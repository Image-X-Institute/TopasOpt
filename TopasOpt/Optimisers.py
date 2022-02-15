# -*- coding: iso-8859-1 -*-
import subprocess
import jsonpickle
from matplotlib import pyplot as plt
# matplotlib.use('Agg')  # if having trouble with generating figures through ssh, this resolves...
import shutil
from scipy.optimize import minimize
from scipy import stats
from pathlib import Path
import numpy as np
import sys, os
from bayes_opt import BayesianOptimization
from bayes_opt import UtilityFunction
from bayes_opt.logger import JSONLogger
from bayes_opt.util import load_logs
from bayes_opt.event import Events
from sklearn.gaussian_process.kernels import Matern
import logging
from .utilities import bcolors, FigureSpecs, newJSONLogger
import stat

ch = logging.StreamHandler()
formatter = logging.Formatter('[%(filename)s: line %(lineno)d %(levelname)8s] %(message)s')
ch.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(ch)
logger.setLevel(logging.INFO)  # This toggles all the logging in your app
logger.propagate = False


def import_from_absolute_path(fullpath, global_name=None):
    """
    Dynamic script import using full path.
    This is required to enable mapping to the location of the script generation function and the objective funciton,
    which are not known in advance.
    (credit here)[https://stackoverflow.com/questions/3137731/is-this-correct-way-to-import-python-scripts-residing-in-arbitrary-folders]
    """


    script_dir, filename = os.path.split(fullpath)
    script, ext = os.path.splitext(filename)

    sys.path.insert(0, script_dir)
    try:
        module = __import__(script)
        if global_name is None:
            global_name = script
        globals()[global_name] = module
        sys.modules[global_name] = module
    finally:
        del sys.path[0]

class TopasOptBaseClass:
    """
    There are many overlapping functionalities required by all optimisation algorithms: logging, calculation of objective function,
    generation of models...etc. All of these common methods are contained this base class which other optimisation methods inherit.

    This class is not intended to be used in isolation and won't work if you try.
    """

    def __init__(self, optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory,
                 TargetBeamWidth=7, ReadMeText = None,
                 StartingSimplexRelativeVal=None, length_scales=None,
                 KappaDecayIterations=10, TopasLocation='~/topas/',
                 ShellScriptHeader=None, Overwrite=False, GP_alpha=0.01, KeepAllResults=True):
        """
        :param optimisation_params: Parameters to be optimised. Must match parameters for PhaserBeamLine
        :type optimisation_params: list
        :param BaseDirectory: Place where all the topas simulation results are stored
        :type BaseDirectory: string
        :param SimulationName: Specific folder for this simulation
        :type SimulationName: string
        :param TargetBeamWidth: desired beam width in mm
        :type TargetBeamWidth: double
        :param debug: will try and use a quick phase space. won't produce meaningful results but will be quick. Default is True.
        type debug: Boolean, optional
        param Nthreads: Number of threads to run.
        type Nthreads: double, optional
        :param StartingDoseFile: If supplied, results will be normalised to this. if not, they will be normalised to the
            starting parameters
        :type StartingDoseFile: string, optional
        :param StartingCollimatorThickness: Thickness of collimator used in StartingDoseFile. If StartingDoseFile is supplied
            this MUST be supplied, otherwise not.
        :type StartingCollimatorThickness: double, optional
        :param StartingSimplexRelativeVal: This does nothing here; it is only here to enable complete compatability between
            the Bayesian and Nealder-Mead methods
        :type StartingSimplexRelativeVal: double, optional
        :param MaxItterations: this is defined in optimisation_params['Nitterations']. Note that nealder mead will always
            assess the starting simplex first before checking this (mostly a debugging problem)
        :param KappaDecayIterations: Over the last N iterations, kappa will decay to be almost 0 (highly exploitive). For
            explantion of kappa decay see `here <https://github.com/fmfn/BayesianOptimization/pull/221>`_
        :type KappaDecayIterations: int
        :param OptimisationDirectory: location that TopasObjectiveFunction and GenerateTopasScript are located
        :type OptimisationDirectory: string or Path
        """

        if 'TopasOptBaseClass' in str(self.__class__):
            logger.error('TopasOptBaseClass should not be called directly; it only exists for other optimisers'
                         'to inherit. Quitting')
            sys.exit(1)

        self.ReadMeText = ReadMeText  # this gets written to base directory
        self.ShellScriptHeader = ShellScriptHeader
        self.KeepAllResults = KeepAllResults
        # attempt the absolute imports from the optimisation directory:
        self.BaseDirectory = BaseDirectory
        self.OptimisationDirectory = OptimisationDirectory
        if not os.path.isdir(BaseDirectory):
            logger.error(
                f'{bcolors.FAIL}Input BaseDirectory "{BaseDirectory}" does not exist. Exiting. {bcolors.ENDC}')
            sys.exit()
        self.SimulationName = SimulationName
        self.TargetBeamWidth = TargetBeamWidth
        self.Itteration = 0
        self.ItterationStart = 0
        # the starting values of our optimisation parameters are defined from the default geometry
        self.ParameterNames = optimisation_params['ParameterNames']
        self.StartingValues = optimisation_params['start_point']
        if self.StartingValues is None:
            logger.error('you must define a start point')
            sys.exit()
        else:
            self.x = self.StartingValues
        self.UpperBounds = optimisation_params['UpperBounds']
        self.LowerBounds = optimisation_params['LowerBounds']
        self.MaxItterations = optimisation_params['Nitterations']
        self._CreateVariableDictionary([self.StartingValues])
        self.SuggestionsProbed = 0  # always starts at 0
        self.Overwrite = Overwrite
        self.AllObjectiveFunctionValues = []

        if '~' in TopasLocation:
            TopasLocation = os.path.expanduser(TopasLocation)
        self.TopasLocation = Path(TopasLocation)
        try:
            import_from_absolute_path(Path(self.OptimisationDirectory) / 'GenerateTopasScripts.py')
        except ModuleNotFoundError:
            logger.error(f'could not find required file at {str(Path(self.OptimisationDirectory) / "GenerateTopasScript.py")}.'
                         f'\nQuitting')
            sys.exit(1)
        try:
            import_from_absolute_path(Path(self.OptimisationDirectory) / 'TopasObjectiveFunction.py')
        except ModuleNotFoundError:
            logger.error(f'could not find required file at {str(Path(self.OptimisationDirectory) / "TopasObjectiveFunction.py")}.'
                         f'\nQuitting')
            sys.exit(1)
        self.TopasScriptGenerator = GenerateTopasScripts.GenerateTopasScripts
        self.TopasObjectiveFunction = TopasObjectiveFunction.TopasObjectiveFunction

        # put optimiser specific stuff in blocks like this:
        if 'BayesianOptimiser' in str(self.__class__):
            if StartingSimplexRelativeVal is not None:
                logger.warning(
                    f'You have attempted to use the variable StartingSimplexRelativeVal, but this does nothing'
                    f'in the Bayesian optimiser - it only works with the Nealder-Mead optimiser. Continuing'
                    f' and ignoring this parameter')
            self.BayesOptLogLoc = self.BaseDirectory + '/' + self.SimulationName + '/' + 'logs/bayes_opt_logs.json'
            self._BayesianOptimiser__RestartMode = False  # don't change!
            self._create_p_bounds(optimisation_params)  # Bayesian optimiser wants bounds in a slight differnt format
            self._create_suggested_points_to_probe(optimisation_params)
            self._derive_length_scales(length_scales)

            # Bayesian optimisation settings:
            self.target_prediction_mean = []  # keep track of what the optimiser expects to get
            self.target_prediction_std = []  # keep track of what the optimiser expects to get
            self.GP_alpha = GP_alpha  # this tells the GPM the expected ammount of noise in the objective function
            # see here: https://github.com/fmfn/BayesianOptimization/issues/202
            self.Matern_Nu = 1.5  # see here https://scikit-learn.org/stable/modules/generated/sklearn.gaussian_process.kernels.Matern.html#sklearn.gaussian_process.kernels.Matern
            self.UCBkappa = 5  # higher kappa = more exploration. lower kappa = more exploitation
            self.n_restarts_optimizer = 20  # this controls the gaussian process fitting. 20 seems to be a good number.
            self.KappaDecayIterations = KappaDecayIterations
            self.UCBKappa_final = 0.1
            self.kappa_decay_delay = self.MaxItterations - self.KappaDecayIterations  # this many exploritive iterations will be carried out before kappa begins to decay

            if self.kappa_decay_delay >= self.MaxItterations:
                logger.warning(f'Kappa decay requested, but since kappa_decay_delay ({self.kappa_decay_delay}) is less'
                                   f'than MaxItterations ({self.MaxItterations}), decay will never occur...')
                self.kappa_decay = 1
            else:
                self.kappa_decay = (self.UCBKappa_final/self.UCBkappa) ** (1/(self.MaxItterations - self.kappa_decay_delay))
                # ^^ this is the parameter to ensure we end up with UCBKappa_final on the last iteration

        if 'NealderMeadOptimiser' in str(self.__class__):
            if length_scales is not None:
                logger.warning(
                    f'You have attempted to set length_scales, but this does nothing'
                    f'in the NealderMeadO optimiser - it only works with the Bayesian optimiser. Continuing'
                    f' and ignoring this parameter')

            if 'Suggestions' in optimisation_params.keys():
                logger.warning(
                    f'You have attempted to enter a suggestion, but this does nothing'
                    f'in the NealderMeadO optimiser - it only works with the Bayesian optimiser. Continuing'
                    f' and ignoring this parameter')

            self.StartingSimplexSupplied = False
            self.StartingSimplexRelativeVal = StartingSimplexRelativeVal
            if self.StartingSimplexRelativeVal:  # nb None evaluates as False
                self._GenerateStartingSimplex()

        self._CheckInputData()

    def _CreateVariableDictionary(self, x):
        """
        Use the input information to create a dictionary of geometric inputs. This creates an elegant method to
        create phaser geometries downstream in _GenerateTopasModel

        x is the current list of parameter guesses.
        """

        if np.ndim(x) == 1:
            self.VariableDict = {self.ParameterNames[i]: x[i] for i in range(len(self.ParameterNames))}
        elif np.ndim(x) == 2:
            self.VariableDict = {self.ParameterNames[i]: x[0][i] for i in range(len(self.ParameterNames))}
        else:
            logger.error('seomthing wrong with input parameter format...')
            sys.exit(1)

        for key in self.VariableDict.keys():
            # this just kept happening so put this ugle brutfe forxe method in
            if type(self.VariableDict[key]) is np.ndarray:
                self.VariableDict[key] = self.VariableDict[key][0]
        # finally add in the beamlet size:

    def _EmptySimulationFolder(self):
        """
        If there is already stuff in the simulation folder, ask for user permission to empty and continue
        """
        SimName = str(Path(self.BaseDirectory) / self.SimulationName)
        if os.listdir(SimName) and (not self.Overwrite):
            logger.warning(f'Directory {SimName} is not empty; if you continue it will be emptied.'
                           f'\nType y to continue.'
                           f'\nYou can set Overwrite=True to disable this warning')

        if self.Overwrite:
            UserOverwrite = 'y'
        else:
            UserOverwrite = input()

        if (UserOverwrite.lower() == 'n') or (UserOverwrite.lower() == 'no'):
            logger.warning('Not overwriting and quitting')
            sys.exit(1)
        elif (UserOverwrite.lower() == 'y') or (UserOverwrite.lower() == 'yes'):
            logger.warning('emptying simulation folder')
            for filename in os.listdir(SimName):
                file_path = os.path.join(SimName, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    logger.error(f'Failed to delete {file_path}. Reason: {e}. Quitting')
                    sys.exit(1)

    def _CheckInputData(self):
        """
        check that the user has put in reasonable parameters:

        - Checks if the number of parameters in ParameterNames, StartingValues, UpperBounds, LowerBounds match
        - Checks that StartingValues is actually within the provided bounds
        """

        # do the number of parameters match?
        if not np.size(self.ParameterNames) == np.size(self.StartingValues):
            logger.error(f'{bcolors.FAIL} size of ParameterNames does not match size of StartingValues{bcolors.ENDC}')
            sys.exit(1)
        if not np.size(self.StartingValues) == np.size(self.UpperBounds):
            print(f'{bcolors.FAIL} size of StartingValues does not match size of UpperBounds{bcolors.ENDC}')
            sys.exit(1)
        if not np.size(self.UpperBounds) == np.size(self.LowerBounds):
            print(f'{bcolors.FAIL} size of UpperBounds does not match size of LowerBounds{bcolors.ENDC}')
            sys.exit(1)

        for i, Paramter in enumerate(self.ParameterNames):
            try:
                if self.StartingValues[0][i] < self.LowerBounds[i]:
                    print(f'{bcolors.FAIL}For {Paramter}, Starting value {self.StartingValues[0][i]} is less than '
                          f'Lower bound {self.LowerBounds[i]}{bcolors.ENDC}')
                    sys.exit()
                elif self.StartingValues[0][i] > self.UpperBounds[i]:
                    print(f'{bcolors.FAIL}For {Paramter}, Starting value {self.StartingValues[0][i]} is greater '
                          f'than upper bound {self.UpperBounds[i]}{bcolors.ENDC}')
            except IndexError:
                if self.StartingValues[i] < self.LowerBounds[i]:
                    print(f'{bcolors.FAIL}For {Paramter}, Starting value {self.StartingValues[i]} is less than '
                          f'Lower bound {self.LowerBounds[i]}{bcolors.ENDC}')
                    sys.exit()
                elif self.StartingValues[i] > self.UpperBounds[i]:
                    print(f'{bcolors.FAIL}For {Paramter}, Starting value {self.StartingValues[i]} is greater '
                          f'than upper bound {self.UpperBounds[i]}{bcolors.ENDC}')

        if (self.StartingValues == 0).any():
            Names = np.asarray(self.ParameterNames, dtype=object)
            ind = self.StartingValues == 0
            Names = list(Names[ind])
            logger.error(
                f'{bcolors.FAIL}At the moment no starting values can be zero, because we use the starting values '
                f'to create relative values.\nThis is a fairly inherent limiation of this code, fixable but not '
                f'fixed!The following parameters have starting values of zero:\n{Names}{bcolors.ENDC}')
            sys.exit(1)

        self._CreateVariableDictionary(self.StartingValues)

        # make sure topas binary exists
        if not os.path.isfile(self.TopasLocation / 'bin' / 'topas'):
            logger.error(f'{bcolors.FAIL}could not find topas binary at \n{self.TopasLocation}'
                         f'\nPlease initialise with TopasLocation pointing to the topas installation location.'
                         f'\nQuitting{bcolors.ENDC}')
            sys.exit(1)

    def _GenerateTopasModel(self, x):
        """
        Generates a topas model with the latest parameters as well as a shell script called RunAllFiles.sh to run it.
        """

        self.TopasScripts, self.TopasScriptNames = self.TopasScriptGenerator(self.BaseDirectory, self.Itteration, **self.VariableDict)
        self.ScriptsToRun = []
        for i, script_name in enumerate(self.TopasScriptNames):
            script_name = script_name + '_itt_' + str(self.Itteration) + '.tps'
            self.ScriptsToRun.append(script_name)
            f = open(str(Path(self.BaseDirectory) / self.SimulationName / 'TopasScripts' / script_name), 'w')
            for line in self.TopasScripts[i]:
                f.write(line)
                f.write('\n')

        self._GenerateRunIterationShellScript()

    def _GenerateRunIterationShellScript(self):

        """
        This will generate a bash script called 'RunAllFiles', which, funnily enough, can be used to run all files generated!
        """
        ShellScriptLocation = str(Path(self.BaseDirectory) / self.SimulationName / 'TopasScripts' / 'RunIteration.sh')
        if os.path.isfile(ShellScriptLocation):
            # I don't think I should need to do this; the file should be overwritten if it exists, but this doesn't
            # seem to be working so deleting it.
            os.remove(ShellScriptLocation)
        self.ShellScriptLocation = ShellScriptLocation


        f = open(ShellScriptLocation, 'w+')

        # set up the environment etc.
        if self.ShellScriptHeader is None:
            f.write('# !/bin/bash')
            f.write('\n\n# This script sets up the topas environment then runs all listed files\n\n')
            f.write('\nexport TOPAS_G4_DATA_DIR=~/G4Data\n')
        else:
            f.write(self.ShellScriptHeader)

        # add in all topas scripts which need to be run:
        for script_name in self.ScriptsToRun:
            file_loc = str(Path(self.BaseDirectory) / self.SimulationName / 'TopasScripts' / script_name)
            f.write('echo "Beginning analysis of: ' + script_name + '"')
            f.write('\n')
            f.write('(time ' + str(self.TopasLocation) + '/bin/topas ' + script_name + ') &> ../logs/TopasLogs/' + script_name)
            f.write('\n')
        # change file permissions:
        st = os.stat(ShellScriptLocation)
        os.chmod(ShellScriptLocation, st.st_mode | stat.S_IEXEC)
        f.close()

    def _RunTopasModel(self):
        """
        This invokes a bash subprocess to run the current model
        """
        print(f'{bcolors.OKBLUE}Topas: Running file: \n{self.ShellScriptLocation}')
        ShellScriptPath = str(Path(self.BaseDirectory) / self.SimulationName / 'TopasScripts')
        cmd = subprocess.run(['bash', self.ShellScriptLocation], cwd=ShellScriptPath)
        if cmd.returncode == 0:
            print(f'{bcolors.OKBLUE}Analysis complete{bcolors.ENDC}')
        else:
            logger.error(f'RunIteration.sh failed with exit code {cmd.returncode}.'
                         f'\nSuggestion: look at {Path(self.OptimisationDirectory) / self.SimulationName / "Logs" / "TopasLogs"} '
                         f'\nto figure out what went wrong...'
                         f' Quitting')
            sys.exit(1)

    def _UpdateOptimisationLogs(self, x, OF):
        """
        Just a simple function to keep track of the objective function in the logs folder

        :param x: the current parameter values
        :type x: array
        :param OF: the current objective function value
        """

        LogFile = Path(self.BaseDirectory) / self.SimulationName
        LogFile = LogFile / 'logs'
        LogFile = str(LogFile / 'OptimisationLogs.txt')

        with open(LogFile, 'a') as f:
            Entry = f'Itteration: {self.Itteration}'
            for i, Parameter in enumerate(self.ParameterNames):
                try:
                    Entry = Entry + f', {Parameter}: {x[0][i]: 1.2f}'
                except IndexError:
                    Entry = Entry + f', {Parameter}: {x[i]: 1.2f}'

            try:
                Entry = Entry + f', target_prediction_mean: {self.target_prediction_mean[-1]: 1.2f}'
                Entry = Entry + f', target_prediction_std: {self.target_prediction_std[-1]: 1.2f}'
            except AttributeError:
                # these parameters are only available for bayes optimisation
                pass
            except IndexError:
                # for the first entry
                Entry = Entry + f', target_prediction_mean: NaN'
                Entry = Entry + f', target_prediction_std: NaN'

            Entry = Entry + f', ObjectiveFunction: {OF: 1.2f}\n'
            f.write(Entry)
        print(f'{bcolors.OKGREEN}{Entry}{bcolors.ENDC}')

    def _write_final_log_entry(self, x, OF, Itteration=None):
        """
        This method can optionally be called when the optimiser has finished running.
        It worked similarly to _UpdateOptimisationLogs but it should be passed the best
        parameters and OF value. Optionally, the user can also pass the itteration at which
        these occured (which I recomend, it makes life easier)

        :param x: the best parameter values
        :type x: array
        :param OF: the best objective function value
        :param Itteration: the Itteration these results occured at
        """

        LogFile = Path(self.BaseDirectory) / self.SimulationName
        LogFile = LogFile / 'logs'
        LogFile = str(LogFile / 'OptimisationLogs.txt')

        with open(LogFile, 'a') as f:
            Entry = f'\nBest parameter set: '
            if Itteration is not None:
                Entry = Entry + f'Itteration: {Itteration}.'
            for i, Parameter in enumerate(self.ParameterNames):
                try:
                    Entry = Entry + f', {Parameter}: {x[0][i]: 1.2f}'
                except IndexError:
                    Entry = Entry + f', {Parameter}: {x[i]: 1.2f}'

            Entry = Entry + f', ObjectiveFunction: {OF: 1.2f}\n'
            f.write(Entry)
        print(f'{bcolors.OKGREEN}{Entry}{bcolors.ENDC}')

    def _Plot_Convergence(self):

        ItterationVector = np.arange(self.ItterationStart, self.Itteration + 1)

        # create lowest val at each iteration
        LowestVal = np.ones(np.size(self.AllObjectiveFunctionValues)) * self.AllObjectiveFunctionValues[0]
        for i, val in enumerate(LowestVal):
            if self.AllObjectiveFunctionValues[i] < LowestVal[i]:
                LowestVal[i:] = self.AllObjectiveFunctionValues[i]


        fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(10, 5))
        axs.plot(ItterationVector, LowestVal, '-k', linewidth=2)
        axs.plot(ItterationVector, self.AllObjectiveFunctionValues, 'C6')
        axs.set_xlabel('Itteration number', fontsize=FigureSpecs.LabelFontSize)
        axs.set_ylabel('Objecti'
                          've function', fontsize=FigureSpecs.LabelFontSize)
        axs.grid(True)

        try:
            target_prediction = -1 * np.array(self.target_prediction_mean, )
            axs.plot(ItterationVector, target_prediction, 'C0')
            axs.fill_between(ItterationVector,
                                target_prediction + self.target_prediction_std,
                                target_prediction - self.target_prediction_std, alpha=0.15, color='C0')
            axs.legend(['Best', 'Actual', 'Predicted', r'$\sigma$'])
        except AttributeError:
            # predicted isn't  available for optimisers
            axs.legend(['Best', 'Current'])

        MinValue = np.argmin(self.AllObjectiveFunctionValues)
        axs.plot(ItterationVector[MinValue], self.AllObjectiveFunctionValues[MinValue], 'r-x')
        axs.set_title('Convergence Plot', fontsize=FigureSpecs.TitleFontSize)


        SaveLoc = Path(self.BaseDirectory) / self.SimulationName
        SaveLoc = SaveLoc / 'logs'
        plt.savefig(SaveLoc / 'ConvergencePlot.png')
        plt.close(fig)

    def _CopySelf(self):
        """
        Copies all class attributes to a a (human readable) json file called 'SimulationSettings'.
        This is so you can exactly which settings were used to generate a given simulation
        """

        Filename = Path(self.BaseDirectory) / Path(self.SimulationName) / 'OptimisationSettings.json'

        Attributes = jsonpickle.encode(self, unpicklable=True, max_depth=4)
        f = open(str(Filename), 'w')
        f.write(Attributes)

    def _ReadInLogFile(self, LogFileLoc):
        """
        This function can be used to read in a log file to a dictionary
        """

        if not os.path.isfile(LogFileLoc):
            logger.error(f'File not found:\n{LogFileLoc}\nQuitting')
            sys.exit(1)

        file1 = open(LogFileLoc, 'r')
        Lines = file1.readlines()

        Itteration = []
        OF = []
        LineItteration = 0
        ResultsDict = {}
        for line in Lines:
            try:
                d = {i.split(': ')[0]: i.split(': ')[1] for i in line.split(', ')}
                # remaining keys are the things we want to track
                for key in d.keys():
                    if key == 'Best parameter set':
                        # this is the last line
                        break
                    if LineItteration == 0:
                        ResultsDict[key] = []
                    ResultsDict[key].append(float(d[key]))
                LineItteration += 1
            except IndexError:
                pass

        return ResultsDict

    def _PlotLogFile(self, LogFileLoc):
        """
        This function can be used to plot an existing log file
        need to fix because now itteration and OF are stored in dict
        """
        ResultsDict = self._ReadInLogFile(LogFileLoc)
        fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(15, 5))

        Itteration = ResultsDict.pop('Itteration')
        OF = ResultsDict.pop('ObjectiveFunction')

        axs.plot(Itteration, OF, 'C5',linewidth=2)
        axs.set_xlabel('Itteration number', fontsize=FigureSpecs.LabelFontSize*1.7)
        axs.set_ylabel('Objective Function', fontsize=FigureSpecs.LabelFontSize*1.7)
        axs.grid(True)
        axs.set_title('Convergence Plot', fontsize=FigureSpecs.TitleFontSize*1.5)

        try:
            target_prediction = -1 * np.array(ResultsDict.pop('target_prediction_mean'))
            target_prediction_std = np.array(ResultsDict.pop('target_prediction_std'))
            axs.plot(Itteration, target_prediction, 'C0--',linewidth=2)
            axs.fill_between(Itteration,
                                target_prediction + target_prediction_std,
                                target_prediction - target_prediction_std, alpha=0.3, color='C0')
            axs.legend(['Actual', 'Predicted', r'$\sigma$'], fontsize=FigureSpecs.LabelFontSize*1.5)
        except KeyError:
            # predicted isn't always available
            pass

        ResultsDict.pop('CrossChannelLeakage')
        MinValue = np.argmin(OF)
        axs.plot(Itteration[MinValue], OF[MinValue], 'r-x')
        # axs.set_title('Convergence Plot', fontsize=FigureSpecs.TitleFontSize)
        LegendStrings = ResultsDict.keys()

        if False:
            for i, key in enumerate(ResultsDict.keys()):
                try:
                    ParameterVals = np.array(ResultsDict[key]) / ResultsDict[key][0]
                except:
                    print('hello_')
                axs[1].plot(Itteration, ParameterVals)

            axs[1].legend(LegendStrings)
            axs[1].set_xlabel('Itteration number')
            axs[1].set_ylabel('Parameter value')
            axs[1].grid(True)

            plt.tight_layout()

        else:
            # axs[1].scatter(OF, target_prediction)
            # axs[1].set_xlabel('Actual Objective Function', fontsize=FigureSpecs.LabelFontSize)
            # axs[1].set_ylabel('Predicted Objective Function', fontsize=FigureSpecs.LabelFontSize)
            # NewMinLim = np.min([axs[1].get_ylim(), axs[1].get_xlim()])
            # NewMaxLim = np.max([axs[1].get_ylim(), axs[1].get_xlim()])
            # axs[1].set_ylim([NewMinLim, NewMaxLim])
            # axs[1].set_xlim([NewMinLim, NewMaxLim])
            # axs[1].plot([NewMinLim, NewMaxLim], [NewMinLim, NewMaxLim], 'k--')

            Pearson = stats.pearsonr(OF[1:], target_prediction[1:])
            Spearman = stats.spearmanr(OF[1:], target_prediction[1:])
            print(f'Pearson Correlation: {Pearson}, Spearman Correlation: {Spearman}')
            # plt.text(NewMinLim + abs(NewMinLim * 0.15), NewMaxLim - (abs(NewMaxLim * 0.5)),
            #          f'Spearman: {Spearman[0]: 1.1f}\nPearson: {Pearson[0]: 1.1f}',
            #          fontsize=FigureSpecs.LabelFontSize)

            # axs[1].grid(True)
            # axs[1].set_title('Actual versus predicted correlation', fontsize=FigureSpecs.TitleFontSize)
        plt.tick_params(axis='both', which='major', labelsize=15)
        plt.tight_layout()
        plt.show()

    def _ConvertDictToVariables(self, x_new):
        """
        I'm trying to keep as much of the underlying code base compatible with multiple methods, so convert the x_new
        the bayes code gives me into what the rest of my code expects

        Note the bayes code sends in the dict in alphabetical order; this methods also corrects that such that the initial
        order of variables is maintained
        """
        if not isinstance(x_new, dict):
            # then no conversion needed
            self.x = x_new
            return
        x = []
        for i, paramNames in enumerate(x_new):
            x.append(x_new[self.ParameterNames[i]])
        self.x = np.array(x, ndmin=2)

    def _empty_results_folder(self):
        """
        if KeepAllResults is false, this function is called which removes all existing files
        in the results folder. It is called just before new scripts are run such that the latest results
        will be kept
        """
        ResultsLocation = str(Path(self.BaseDirectory) / self.SimulationName / 'Results')
        for filename in os.listdir(ResultsLocation):
            file_path = os.path.join(ResultsLocation, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                logger.warning(f'Failed to delete {file_path} from results folder. Reason: {e}. continuing...')

    def BlackBoxFunction(self, x_new):
        """
        Called Black Box function in the spirit of bayesian optimisation, this function simply takes the most recent
        parameter guesses, and solves the model.
        """

        self._ConvertDictToVariables(x_new)
        self._CreateVariableDictionary(self.x)
        self._GenerateTopasModel(self.x)
        if not self.KeepAllResults:
            self._empty_results_folder()
        self._RunTopasModel()
        self.OF = self.TopasObjectiveFunction(Path(self.BaseDirectory) / self.SimulationName / 'Results', self.Itteration)
        self.AllObjectiveFunctionValues.append(self.OF)
        self._UpdateOptimisationLogs(self.x, self.OF)
        self._Plot_Convergence()
        self.Itteration = self.Itteration + 1

        if 'BayesianOptimiser' in str(self.__class__):
            # bit of a hack since bayesian optimise will seek maximum
            return -self.OF
        else:
            return self.OF

    def SetUpDirectoryStructure(self):
        """
        Method to set up directory structure. This will attempt to empty the directory if it already exists.
        If Overwrite=False, it will ask first, otherwise just do it.
        Also writes the readme text if that exists, and copies all attributes of self to a json file.
        """

        FullSimName = Path(self.BaseDirectory) / self.SimulationName
        if not os.path.isdir(FullSimName):
            os.mkdir(FullSimName)
        self._EmptySimulationFolder()
        self._CopySelf()
        os.mkdir(Path(FullSimName) / 'logs')
        os.mkdir(Path(FullSimName) / 'logs' / 'TopasLogs')
        if 'BayesianOptimiser' in str(self.__class__):
            os.mkdir(Path(FullSimName) / 'logs' / 'SingleParameterPlots')
        os.mkdir(Path(FullSimName) / 'TopasScripts')
        os.mkdir(Path(FullSimName) / 'Results')

        if self.ReadMeText:
            f = open(FullSimName / 'readme.txt','w')
            f.write(self.ReadMeText)


class NealderMeadOptimiser(TopasOptBaseClass):

    def _GenerateStartingSimplex(self):
        """
        This is copied from the scipy source code (optimize around line 690), with a variable version of nonzdelt
        """

        if not type(self.StartingSimplexRelativeVal) is float:
            logger.error('Starting simplex can only be defined as a relative parameter, e.g. 0.1')
            sys.exit(1)

        N = len(self.StartingValues)
        nonzdelt = self.StartingSimplexRelativeVal
        zdelt = self.StartingSimplexRelativeVal / 200  # based on the scipy code where zdelt - nonzdelt/200
        sim = np.empty((N + 1, N), dtype=self.StartingValues.dtype)
        sim[0] = self.StartingValues
        for k in range(N):
            y = np.array(self.StartingValues, copy=True)
            if y[k] != 0:
                y[k] = (1 + nonzdelt) * y[k]
            else:
                y[k] = zdelt
            sim[k + 1] = y

        self.StartingSimplex = sim
        self.StartingSimplexSupplied = True

    def RunOptimisation(self):
        """
        Use the scipy.optimize.minimize module to perform the optimisation.
        Note that most of the 'action' is happening in BlackBoxFunction, which is repeated called by the optmizer
        """

        self.SetUpDirectoryStructure()
        if self.StartingSimplexSupplied:
            StartingSimplex = self.StartingSimplex
        else:
            StartingSimplex = None

        bnds = tuple(zip(self.LowerBounds, self.UpperBounds))


        self.NelderMeadRes = minimize(self.BlackBoxFunction, self.StartingValues, method='Nelder-Mead', bounds=bnds,
                       options={'xatol': 1e-1, 'fatol': 1e-1, 'disp': True, 'initial_simplex': StartingSimplex,
                                'maxiter': self.MaxItterations, 'maxfev': self.MaxItterations})

        # update final log entry
        best_iteration = np.argmin(self.NelderMeadRes.final_simplex[1])
        best_OF = self.NelderMeadRes.final_simplex[1][best_iteration]
        best_params = self.NelderMeadRes.final_simplex[0][best_iteration]
        self._write_final_log_entry(best_params, best_OF, best_iteration)


class BayesianOptimiser(TopasOptBaseClass):
    """
    Class to perform optimisation using the `Bayesian Optimisation code <https://github.com/fmfn/BayesianOptimization>`_
    This inherits most of its functionality from SphinxOptBaseClass.
    """

    def _derive_length_scales(self, length_scales):
        """
        Figure out what to put in to the gaussian process model kernel for length scales.
        We use the Matern Kernel which is detailed `here <https://scikit-learn.org/stable/modules/generated/sklearn.gaussian_process.kernels.Matern.html#sklearn.gaussian_process.kernels.Matern>`_

        :param length_scales: user input for length scales. Can be one of three things:
            1. **None**: in this case, the default is used: length_scale=1.0
            2. Number > 0 and <1: in this case, the length scales for each parameter are derived as a percentage of range.
                For instance if the user enter 0.1, all length scales will be set to 10% of the range of each variable.
            3. Array: Finally, the user is free to simply specify what length scales to use for each parameter. Make sure
                you enter them in alphabetical order as this is the order used internally by the optimiser.
        """
        ParameterNames = sorted(self.pbounds.keys())
        if length_scales is None:
            length_scales = 0.1
            self.length_scales = []
            for paramter_name in ParameterNames:
                length_scale_temp = (self.pbounds[paramter_name][1] - self.pbounds[paramter_name][0]) * length_scales
                self.length_scales.append(length_scale_temp)
        elif type(length_scales) is float:
            self.length_scales = []
            for paramter_name in ParameterNames:
                length_scale_temp = (self.pbounds[paramter_name][1] - self.pbounds[paramter_name][0]) * length_scales
                self.length_scales.append(length_scale_temp)
        elif type(length_scales) is list or type(length_scales) is np.ndarray:

            if not len(length_scales) == len(ParameterNames):
                logger.error(f'length of length_scales must be single values or match number of parameters; you have'
                             f'{len(ParameterNames)} Parameters, but {len(length_scales)} length_scales. Quitting')
                sys.exit(1)
            self.length_scales = length_scales
        message = f'\nSetting the following length scales. Make sure they are in the right order!!\n'
        for i, paramter_name in enumerate(ParameterNames):
            message = message + paramter_name + f': {self.length_scales[i]}\n'
        logger.info(f'{bcolors.OKGREEN}{message}{bcolors.ENDC}')

    def _create_p_bounds(self, optimisation_params):
        """
        Just reformat the optimisation variables into a format that the Bayesian optimiser wants
        """

        pbounds = {}
        for i, ParamName in enumerate(optimisation_params['ParameterNames']):
            pbounds[ParamName] = (optimisation_params['LowerBounds'][i], optimisation_params['UpperBounds'][i])

        self.pbounds = pbounds

    def _create_suggested_points_to_probe(self, optimisation_params):
        """
        If the user has entered any suggestions, sort them alphabetically and create some variables to keep track of them
        """
        if not 'Suggestions' in optimisation_params.keys():
            # no suggestions made and that's fine
            self.Nsuggestions = None
            return

        else:
            if optimisation_params['Suggestions'].ndim == 1:
                # add an empty dimension to keep the flow going
                optimisation_params['Suggestions'] = np.expand_dims(optimisation_params['Suggestions'], 0)
            if not optimisation_params['Suggestions'].shape[1] == len(optimisation_params['ParameterNames']):
                logger.error(f"wrong dimensionality for suggestions: {optimisation_params['Suggestions'].shape}."
                             f"\nSuggestions shape should be N*{len(optimisation_params['ParameterNames'])}")
                sys.exit(1)
            self.Nsuggestions = optimisation_params['Suggestions'].shape[0]
            self.Suggestions = optimisation_params['Suggestions']
            # put the suggestions into the correct order and store in an array
            self.Suggestions = []
            for n in range(self.Nsuggestions):
                suggestion_dict = {}
                for i, key in enumerate(optimisation_params['ParameterNames']):
                    suggestion_dict[key] = optimisation_params['Suggestions'][n, i]
                self.Suggestions.append(suggestion_dict)

    def _plot_convergence_plot_retrospective(self, optimizer):
        """
        This will read in a log file and produce a version of the convergence plot using the input gaussian process
        model to predict the objective function at each itteration.
        This allows a comparison between the prospective and retrospective performance of the GPM. the plot produced
        in real time (SphinxOptBaseClass._Plot_Convergence) will show the performance of the model in 'real time'.
         this will show the performance
        of the final model.

        :param optimizer: The bayesian optimiser object from RunOptimisation
        """
        LogFile = Path(self.BaseDirectory) / self.SimulationName
        LogFile = LogFile / 'logs'
        LogFile = str(LogFile / 'OptimisationLogs.txt')
        ResultsDict = self._ReadInLogFile(LogFile)

        # we need to format this into a an array based on ParameterNames
        ResultsArray = np.zeros([len(ResultsDict['Itteration']), len(self.ParameterNames)])

        SortedNames = sorted(self.ParameterNames)  # this took me actually hours to figure out.
        for i, parameter in enumerate(SortedNames):
            Values = ResultsDict[parameter]
            ResultsArray[:, i] = Values

        OF = ResultsDict['ObjectiveFunction']
        OF = [-1 * item for item in
              OF]  # it is stored in the log files with the opposite sign of what is used internally
        ItterationVector = ResultsDict['Itteration']
        mean, std = optimizer._gp.predict(ResultsArray, return_std=True)

        fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(5, 5))
        axs.plot(ItterationVector, OF, 'C1-x')
        axs.set_xlabel('Itteration number', fontsize=FigureSpecs.LabelFontSize)
        axs.set_ylabel('Objective function', fontsize=FigureSpecs.LabelFontSize)
        axs.grid(True)
        axs.plot(ItterationVector, mean, 'C0')
        axs.fill_between(ItterationVector, mean + std, mean - std, alpha=0.3, color='C0')
        axs.legend(['Actual', 'Predicted', 'Std.'])
        axs.set_title('Retrospective Model Fit', fontsize=FigureSpecs.TitleFontSize)

        SaveLoc = Path(self.BaseDirectory) / self.SimulationName
        SaveLoc = SaveLoc / 'logs'
        plt.savefig(SaveLoc / 'RetrospectiveModelFit.png')
        plt.close(fig)

    def _plot_predicted_versus_actual_correlation(self):
        """
        Produce a scatter plot of the predicted versus actual objective function values, and print spearman and pearson
        correlation coefficient to it
        """
        fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(5, 5))
        TargetPredictionMean = [-1 * item for item in
                                self.target_prediction_mean]  # need to account for min/max discrepancy
        axs.scatter(self.AllObjectiveFunctionValues, TargetPredictionMean)
        axs.set_xlabel('Actual', fontsize=FigureSpecs.LabelFontSize)
        axs.set_ylabel('Predicted', fontsize=FigureSpecs.LabelFontSize)
        NewMinLim = np.min([axs.get_ylim(), axs.get_xlim()])
        NewMaxLim = np.max([axs.get_ylim(), axs.get_xlim()])
        axs.set_ylim([NewMinLim, NewMaxLim])
        axs.set_xlim([NewMinLim, NewMaxLim])
        axs.plot([NewMinLim, NewMaxLim], [NewMinLim, NewMaxLim], 'r--')

        # Assess and print correlation metrics:
        if len(TargetPredictionMean) > 2:
            Pearson = stats.pearsonr(self.AllObjectiveFunctionValues, TargetPredictionMean)
            Spearman = stats.spearmanr(self.AllObjectiveFunctionValues, TargetPredictionMean)
            plt.text(NewMinLim + abs(NewMinLim * 0.2), NewMaxLim - (abs(NewMaxLim * 0.2)),
                     f'Spearman: {Spearman[0]: 1.1f}\nPearson: {Pearson[0]: 1.1f}',
                     fontsize=FigureSpecs.LabelFontSize)

        axs.grid(True)
        axs.set_title('Actual versus predicted correlation', fontsize=FigureSpecs.TitleFontSize)
        plt.tight_layout()
        SaveLoc = Path(self.BaseDirectory) / self.SimulationName
        SaveLoc = SaveLoc / 'logs'
        plt.savefig(SaveLoc / 'CorrelationPlot.png')
        plt.close(fig)

    def _plot_single_variable_objective(self, optimizer):
        """
        For each variables, produce a plot of the prediced objective function while only that parameter varies
        and the others are held at the current best values.
        This allows one to get an idea of the predicted objective function shape. The accuracy of this prediction
        depends on how well the model is currently fit...
        """

        PlotSavePath = str(Path(self.BaseDirectory) / self.SimulationName / 'logs' / 'SingleParameterPlots')
        if not os.path.isdir(PlotSavePath):
            os.mkdir(PlotSavePath)

        Nsamples = 100
        Params = list(optimizer.max['params'].keys())
        PointsToTest = np.ones([len(Params), Nsamples])  # this will be an array of the best points for each param
        # below we overwrite one row at a time with the parameter being varied
        ConstantValues = np.array(list(optimizer.max['params'].values()))  # current best guess for each param
        for i, const_val in enumerate(ConstantValues):
            PointsToTest[i, :] = PointsToTest[i,:] * const_val


        for i, param in enumerate(Params):

            PointsToTest_temp = PointsToTest.copy()
            PointsToVary = np.linspace(self.pbounds[param][0], self.pbounds[param][1], Nsamples)
            PointsToTest_temp[i, :] = PointsToVary
            mean, std = optimizer._gp.predict(PointsToTest_temp.T, return_std=True)
            mean = -1 * mean
            std = -1 * std
            fig = plt.figure()
            plt.plot(PointsToVary, mean)
            plt.fill_between(PointsToVary, mean + std, mean - std, alpha=0.5, color='C0')
            plt.xlabel(param)
            plt.ylabel('Predicted Objective function value')
            plt.title(f'Single parameter plot for {param}')
            plt.grid()
            SaveName = PlotSavePath + f'/{param}.png'
            plt.savefig(SaveName)
            plt.close(fig)

    def RunOptimisation(self):
        """
        This is the main optimisation loop.
        For explanation of the various parameters and commands, start with the
        """

        # set up directory structure
        if not self.__RestartMode:
            self.SetUpDirectoryStructure()

        # instantiate optimizer:

        self.optimizer = BayesianOptimization(f=None, pbounds=self.pbounds, random_state=1)
        self.optimizer.set_gp_params(normalize_y=True, kernel=Matern(length_scale=self.length_scales, nu=self.Matern_Nu),
                                n_restarts_optimizer=self.n_restarts_optimizer, alpha=self.GP_alpha)  # tuning of the gaussian parameters...
        utility = UtilityFunction(kind="ucb", kappa=self.UCBkappa, xi=0.0, kappa_decay_delay=self.kappa_decay_delay,
                                  kappa_decay=self.kappa_decay)
        logger.warning('setting numpy to ignore underflow errors.')
        np.seterr(under='ignore')

        if self.__RestartMode:
            # then load the previous log files:
            load_logs(self.optimizer, logs=[self.__PreviousBayesOptLogLoc])
            bayes_opt_logger = newJSONLogger(path=self.BayesOptLogLoc)
            self.optimizer.subscribe(Events.OPTIMIZATION_STEP, bayes_opt_logger)
            self.optimizer._gp.fit(self.optimizer._space.params, self.optimizer._space.target)
            self.Itteration = len(self.optimizer.space.target)
            self.ItterationStart = len(self.optimizer.space.target)
            utility._iters_counter = self.ItterationStart
            if self.Itteration >= self.MaxItterations-1:
                logger.error(f'nothing to restart; max iterations is {self.MaxItterations} and have already been completed')
                sys.exit(1)
        else:
            bayes_opt_logger = JSONLogger(path=self.BayesOptLogLoc)
            self.optimizer.subscribe(Events.OPTIMIZATION_STEP, bayes_opt_logger)
            # first guess is nonsense but we need the vectors to be the same length
            self.target_prediction_mean.append(0)
            self.target_prediction_std.append(0)
            target = self.BlackBoxFunction(self.VariableDict)
            self.optimizer.register(self.VariableDict, target=target)

        for point in range(self.Itteration, self.MaxItterations):
            utility.update_params()
            if (self.Nsuggestions is not None) and (self.SuggestionsProbed < self.Nsuggestions):
                # evaluate any suggested solutions first
                next_point_to_probe = self.Suggestions[self.SuggestionsProbed]
                self.SuggestionsProbed += 1
            else:
                next_point_to_probe = self.optimizer.suggest(utility)

            NextPointValues = np.array(list(next_point_to_probe.values()))
            mean, std = self.optimizer._gp.predict(NextPointValues.reshape(1, -1), return_std=True)
            self.target_prediction_mean.append(mean[0])
            self.target_prediction_std.append(std[0])
            target = self.BlackBoxFunction(next_point_to_probe)
            try:
                self.optimizer.register(params=next_point_to_probe, target=target)
            except KeyError:
                try:
                    self.RepeatedPointsProbed = self.RepeatedPointsProbed + 1
                    logger.warning(
                        f'Bayesian algorithm is attempting to probe an existing point: {NextPointValues}. Continuing for now....')
                    if self.RepeatedPointsProbed > 10:
                        logger.error('The same point has been requested more than 10 times; quitting')
                        break
                except AttributeError:
                    self.RepeatedPointsProbed = 1

            self._plot_predicted_versus_actual_correlation()
            self._plot_convergence_plot_retrospective(self.optimizer)
            self._plot_single_variable_objective(self.optimizer)

        # update the logs with the best value:
        best = self.optimizer.max
        best_itteration = np.argmin(abs(self.optimizer.space.target- best['target']))
        self._write_final_log_entry(list(best['params'].values()), best['target'],Itteration=best_itteration)
        # best['target'] = -1 * best['target']  # min/max paradigm...
        # LogFile = Path(self.BaseDirectory) / self.SimulationName
        # LogFile = LogFile / 'logs'
        # LogFile = str(LogFile / 'OptimisationLogs.txt')
        #
        # with open(LogFile, 'a') as f:
        #     Entry = f'\nBest parameter set: {best}'
        #     f.write(Entry)

    def RestartOptimisation(self):
        """
        Sometimes for whatever reason an optimisation is stopped prematurely.
        This function allows you to restart the optimisation by loading the previous log files.
        You just have to change Optimiser.RunOptimisation() to Optimiser.RestartOptimisation()
        in your optimisation script; the code will do the rest automatically.
        """
        self.__RestartMode = True
        self.__PreviousBayesOptLogLoc = self.BayesOptLogLoc
        self.RunOptimisation()
