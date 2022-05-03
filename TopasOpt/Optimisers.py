# -*- coding: iso-8859-1 -*-
"""
This module contains the specific optimisation algorithms for TopasOpt. Most functionality is defined in TopasOptBaseClass,
which other optimisers inherit from.
"""
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
from .utilities import bcolors, FigureSpecs, newJSONLogger, ReadInLogFile, PlotLogFile
import stat
from scipy.optimize import rosen

ch = logging.StreamHandler()
formatter = logging.Formatter('[%(filename)s: line %(lineno)d %(levelname)8s] %(message)s')
ch.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(ch)
logger.setLevel(logging.INFO)  # This toggles all the logging in your app
logger.propagate = False


def _import_from_absolute_path(fullpath, global_name=None):
    """
    Dynamic script import using full path.
    This is required to enable mapping to the location of the script generation function and the objective funciton,
    which are not known in advance.
    `credit here`_<https://stackoverflow.com/questions/3137731/is-this-correct-way-to-import-python-scripts-residing-in-arbitrary-folders>
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
    An important thing to note is that the variables from all optimisers are defined here, which means some of these options
    are specific to a particular optimiser. We may find a more elegant way to handle this in future!

    :param optimisation_params: Parameters to be optimised.
    :type optimisation_params: list or array
    :param BaseDirectory: Place where all the topas simulation results are stored
    :type BaseDirectory: string
    :param SimulationName: Specific folder for this simulation
    :type SimulationName: string
    :param OptimisationDirectory: location that TopasObjectiveFunction and GenerateTopasScript are located
    :type OptimisationDirectory: string or Path
    :param ReadMeText: If supplied, is written to a readme file in BaseDirectory
    :type ReadMeText: string, optional
    :param TopasLocation: location of topas installation. Default is ~/topas if you follow the topas instructions.
    :type TopasLocation: string or pathlib.Path, optional
    :param ShellScriptHeader: Header to place at the start of the bash file that runs the topas model. This header
        should contain all the commands you normally perform to set up your terminal environment.
    :type ShellScriptHeader: string, optional
    :param Overwrite: if True, will automatically overwrite any existing files. If False, will ask first (safer)
    :type Overwrite: bool, optional
    :param KeepAllResults: if True, all results kept, if false, only most recent results are kept. Note that in either
        case the log files contain the info from all cases, it's just a matter of whether you want to store every iteration
        which can take a lot of space
    :type KeepAllResults: bool, optional
    """

    def __init__(self, optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory,
                 ReadMeText=None, G4dataLocation='~/G4Data',
                 TopasLocation='~/topas/',
                 ShellScriptHeader=None, Overwrite=False, KeepAllResults=True):
        """
        init method for all optimisers. input options are in class docstring
        """

        if 'TopasOptBaseClass' in str(self.__class__):
            logger.error('TopasOptBaseClass should not be called directly; it only exists for other optimisers'
                         'to inherit. Quitting')
            sys.exit(1)

        optimisation_params = self._convert_optimisation_params_to_numpy(optimisation_params)
        self.G4dataLocation = G4dataLocation
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
        _LogFileLoc  = Path(self.BaseDirectory) / self.SimulationName
        _LogFileLoc  = _LogFileLoc  / 'logs'
        self._LogFileLoc = str(_LogFileLoc  / 'OptimisationLogs.txt')
        self.Itteration = 0
        self.ItterationStart = 0
        self._optimisation_params = optimisation_params
        # the starting values of our optimisation parameters are defined from the default geometry
        self.ParameterNames = optimisation_params['ParameterNames']
        self.StartingValues = optimisation_params['start_point'].astype(float)
        if self.StartingValues is None:
            logger.error('you must define a start point')
            sys.exit()
        else:
            self.x = self.StartingValues
        self.UpperBounds = optimisation_params['UpperBounds']
        self.LowerBounds = optimisation_params['LowerBounds']
        self.MaxItterations = int(optimisation_params['Nitterations'])
        self._CreateVariableDictionary([self.StartingValues])
        self.SuggestionsProbed = 0  # always starts at 0
        self.Overwrite = Overwrite
        self.AllObjectiveFunctionValues = []

        if '~' in TopasLocation:
            TopasLocation = os.path.expanduser(TopasLocation)
        self.TopasLocation = Path(TopasLocation)
        self._testing_mode = False  # overwrite if True
        if 'testing_mode' in str(self.TopasLocation):
            self._testing_mode = True
            logger.warning(f'Entering test mode because topas location = {self.TopasLocation}')


        # this is where we try to load the user defined model generator and objective function
        try:
            _import_from_absolute_path(Path(self.OptimisationDirectory) / 'GenerateTopasScripts.py')
        except ModuleNotFoundError as e:
            logger.error(f'Failed to import required file at {str(Path(self.OptimisationDirectory) / "GenerateTopasScript.py")}.'
                         f'\nQuitting')
            raise e
        try:
            _import_from_absolute_path(Path(self.OptimisationDirectory) / 'TopasObjectiveFunction.py')
        except ModuleNotFoundError as e:
            logger.error(f'Failed to import required file at {str(Path(self.OptimisationDirectory) / "TopasObjectiveFunction.py")}.'
                         f'\nQuitting')
            raise e
        self.TopasScriptGenerator = GenerateTopasScripts.GenerateTopasScripts
        self.TopasObjectiveFunction = TopasObjectiveFunction.TopasObjectiveFunction
        self._CheckInputData()

    def _convert_optimisation_params_to_numpy(self, optimisation_params):
        """
        This simply checks if any of the supplied parameters are a list instead of an array, and converts them
        if so. will also cast all parameters to floats - if user enntered e.g. 1, python treats it as int
        """
        for param_key in list(optimisation_params.keys()):
            if param_key == 'ParameterNames' or param_key == 'Nitterations':
                continue
            if isinstance(optimisation_params[param_key], list):
                optimisation_params[param_key] = np.array(optimisation_params[param_key])
            if not isinstance(optimisation_params[param_key], np.ndarray):
                logger.error(f'{bcolors.FAIL} optimisation param {param_key} should be a list or an array....')
            optimisation_params[param_key].astype(float)

        return optimisation_params

    def _CreateVariableDictionary(self, x):
        """
        Use the input information to create a dictionary of geometric inputs.
        This is what gets passed to build the topas model
        x is the current list of parameter guesses.
        """

        if np.ndim(x) == 1:
            self.VariableDict = {self.ParameterNames[i]: x[i] for i in range(len(self.ParameterNames))}
        elif np.ndim(x) == 2:
            self.VariableDict = {self.ParameterNames[i]: x[0][i] for i in range(len(self.ParameterNames))}
        else:
            logger.error('seomthing wrong with input parameter format...quitting')
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
                    logger.error(f'Failed to delete {file_path}.')
                    raise e

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
                    sys.exit(1)
                elif self.StartingValues[0][i] > self.UpperBounds[i]:
                    print(f'{bcolors.FAIL}For {Paramter}, Starting value {self.StartingValues[0][i]} is greater '
                          f'than upper bound {self.UpperBounds[i]}{bcolors.ENDC}')
                    sys.exit(1)
            except IndexError:
                if self.StartingValues[i] < self.LowerBounds[i]:
                    print(f'{bcolors.FAIL}For {Paramter}, Starting value {self.StartingValues[i]} is less than '
                          f'Lower bound {self.LowerBounds[i]}{bcolors.ENDC}')
                    sys.exit(1)
                elif self.StartingValues[i] > self.UpperBounds[i]:
                    print(f'{bcolors.FAIL}For {Paramter}, Starting value {self.StartingValues[i]} is greater '
                          f'than upper bound {self.UpperBounds[i]}{bcolors.ENDC}')
                    sys.exit(1)

        self._CreateVariableDictionary(self.StartingValues)

        # make sure topas binary exists
        if not self._testing_mode:
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

    def _setup_topas_emulator(self):
        """
        despite it's fancy sounding name, this isn't really an emulator at all
        What it does is create a bash script that literally does nothing except print hello
        But this allows us to test most of the functionality of this code when we are in testing mode,
        without having to run time consuming topas simulations
        """
        if not os.path.isdir(Path(self.BaseDirectory) / self.SimulationName / 'bin'):
            os.mkdir(Path(self.BaseDirectory) / self.SimulationName / 'bin')

        EmulatorLocation = Path(self.BaseDirectory) / self.SimulationName / 'bin' / 'topas'
        if os.path.isfile(EmulatorLocation):
            # I don't think I should need to do this; the file should be overwritten if it exists, but this doesn't
            # seem to be working so deleting it.
            os.remove(EmulatorLocation)
        self.TopasLocation = EmulatorLocation.parent.parent

        f = open(EmulatorLocation, 'w+')
        f.write('echo "Hello from topas emulator! I dont do anything except print this"')
        # change file permissions:
        st = os.stat(EmulatorLocation)
        os.chmod(EmulatorLocation, st.st_mode | stat.S_IEXEC)
        f.close()

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
            f.write(f'\nexport TOPAS_G4_DATA_DIR={self.G4dataLocation}\n')
        else:
            f.write(self.ShellScriptHeader)

        # add in all topas scripts which need to be run:
        for script_name in self.ScriptsToRun:
            file_loc = str(Path(self.BaseDirectory) / self.SimulationName / 'TopasScripts' / script_name)
            f.write('echo "Beginning analysis of: ' + script_name + '"')
            f.write('\n')
            f.write('(time TOPAS_HEADLESS_MODE=1 ' + str(self.TopasLocation) + '/bin/topas ' + script_name + ') &> ../logs/TopasLogs/' + script_name)
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

        with open(self._LogFileLoc , 'a') as f:
            Entry = f'Itteration: {self.Itteration}'
            for i, Parameter in enumerate(self.ParameterNames):
                try:
                    Entry = Entry + f', {Parameter}: {x[0][i]: 1.2f}'
                except IndexError:
                    Entry = Entry + f', {Parameter}: {x[i]: 1.2f}'

            try:
                Entry = Entry + f', _target_prediction_mean: {self._target_prediction_mean[-1]: 1.2f}'
                Entry = Entry + f', _target_prediction_std: {self._target_prediction_std[-1]: 1.2f}'
            except AttributeError:
                # these parameters are only available for bayes optimisation
                pass
            except IndexError:
                # for the first entry
                Entry = Entry + f', _target_prediction_mean: NaN'
                Entry = Entry + f', _target_prediction_std: NaN'

            Entry = Entry + f', ObjectiveFunction: {OF: 1.2f}\n'
            f.write(Entry)
        print(f'{bcolors.OKGREEN}{Entry}{bcolors.ENDC}')

    def _write_final_log_entry(self):
        """
        This method can optionally be called when an optimiser has finished running.
        It reads in the logs, then prints a message at the end summarising the best found solution.
        """
        ResultsDict = ReadInLogFile(self._LogFileLoc)

        best_iteration = np.argmin(ResultsDict['ObjectiveFunction'])
        best_OF = ResultsDict['ObjectiveFunction'][best_iteration]
        ResultsDict.pop('ObjectiveFunction')
        ResultsDict.pop('Itteration')
        try:
            ResultsDict.pop('_target_prediction_mean')
            ResultsDict.pop('_target_prediction_std')
        except KeyError:
            pass
        # what's left is the results (hopefully no one starts updating the log format!)
        ParameterValues = list(ResultsDict.values())
        best_params = np.array([param_list[best_iteration] for param_list in ParameterValues])
        sort_ind = np.argsort(self.ParameterNames)  # need to sort parameters alphabetically
        best_params = best_params[sort_ind]

        with open(self._LogFileLoc , 'a') as f:
            Entry = f'\nBest parameter set: '

            Entry = Entry + f'Itteration: {best_iteration}.'
            for i, Parameter in enumerate(sorted(self.ParameterNames)):
                Entry = Entry + f', {Parameter}: {best_params[i]: 1.2f}'

            Entry = Entry + f', ObjectiveFunction: {best_OF: 1.2f}\n'
            f.write(Entry)
        print(f'{bcolors.OKGREEN}{Entry}{bcolors.ENDC}')

    def _Plot_Convergence(self):
        """
        just generates the current convergence plot from the log file using the function in utilities
        """

        SaveLoc = Path(self.BaseDirectory) / self.SimulationName
        SaveLoc = SaveLoc / 'logs' / 'ConvergencePlot.png'
        PlotLogFile(self._LogFileLoc, SaveLoc)

    def _CopySelf(self):
        """
        Copies all class attributes to a a (human readable) json file called 'SimulationSettings'.
        This is so you can exactly which settings were used to generate a given simulation
        """

        Filename = Path(self.BaseDirectory) / Path(self.SimulationName) / 'OptimisationSettings.json'

        Attributes = jsonpickle.encode(self, unpicklable=True, max_depth=4)
        f = open(str(Filename), 'w')
        f.write(Attributes)

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

    # public methods
    
    def BlackBoxFunction(self, x_new):
        """
        Called Black Box function in the spirit of bayesian optimisation, this function simply takes the most recent
        parameter guesses, and solves the model.
        """

        if self._testing_mode:
            # this is a special section only intended for development, unit testing, etc.
            # if you are here, it means 'testing_mode' is within your TopasLocation
            self._ConvertDictToVariables(x_new)
            self._CreateVariableDictionary(self.x)
            self._GenerateTopasModel(self.x)
            if not self.KeepAllResults:
                self._empty_results_folder()
            self._RunTopasModel()
            self.OF = self.TopasObjectiveFunction(Path(self.BaseDirectory) / self.SimulationName / 'Results',
                                                  self.Itteration)
            # this is the part where we would normally read in the results and assess the objective function, but
            # since we use TopasEmulator, there are no results. therefore we need to 'insert' them.
            if self.x.shape[0] == 2:
                x = self.x
            elif self.x.shape[0] == 1:
                x = self.x[0]
            else:
                logger.error('how have you managed this.')
                sys.exit(1)
            self.OF = np.min([rosen(x), 100])  # rosenbrock function can get huge, so just cap it at 100.
            self.AllObjectiveFunctionValues.append(self.OF)
            self._UpdateOptimisationLogs(self.x, self.OF)
            self._Plot_Convergence()
            self.Itteration = self.Itteration + 1
        else:
            # this is the normal optimisation
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

        if self._testing_mode:
            self._setup_topas_emulator()


class NelderMeadOptimiser(TopasOptBaseClass):
    """
    Implementation of Nelder-Mead based on scipy. Other options are defined in TopasOptBaseClass

    :param NM_StartingSimplex: This is a Nelder-Mead specific parameter which controls the size of the
        starting simplex. A value of .1 will create a starting simplex that is spans 10% of the starting values,
        which is the default behavior. Alternatively one can specify the starting simplex, e.g. for a 2D function
        starting_sim = [[0.9, 0.9], [0.72, 0.9], [0.9, 0.72]]
    :type NM_StartingSimplex: None or float or array-like, optional
    """

    def __init__(self, NM_StartingSimplex=None, **kwds):
        """
        init function for NelderMeadOptimiser
        """
        self.NM_StartingSimplex = NM_StartingSimplex
        super().__init__(**kwds)
        if self.NM_StartingSimplex:  # nb None evaluates as False
            self.StartingSimplexSupplied = True
            self._GenerateStartingSimplex()

    def _GenerateStartingSimplex(self):
        """
        Enbles the user to enter their own starting simplex, or optionally scale the starting simplex by some fraction.
        This is copied from the scipy source code (optimize around line 690), with a variable version of nonzdelt
        The default is 0.1
        """

        if isinstance(self.NM_StartingSimplex, float):
            # then we generate a simplex based on the starting values
            N = len(self.StartingValues)
            nonzdelt = self.NM_StartingSimplex
            zdelt = self.NM_StartingSimplex / 200  # based on the scipy code where zdelt - nonzdelt/200
            sim = np.empty((N + 1, N), dtype=self.StartingValues.dtype)
            sim[0] = self.StartingValues
            for k in range(N):
                y = np.array(self.StartingValues, copy=True)
                if y[k] != 0:
                    store_yk_temp = y[k]  # yuck, surely someone can do better than this
                    y[k] = (1 + nonzdelt) * y[k]
                    if y[k] > self.UpperBounds[k]:
                        y[k] = (1 - nonzdelt) * store_yk_temp
                    if y[k]  < self.LowerBounds[k]:
                        logger.warning('unable to generate starting simplex within bounds. Simplex will be clipped to bounds.'
                                       'To avoid this behavior, consider changing the starting point, bounds, or value of'
                                       'NM_StartingSimplex')
                else:
                    y[k] = zdelt
                sim[k + 1] = y
        elif isinstance(self.NM_StartingSimplex, np.ndarray)or isinstance(self.NM_StartingSimplex, list):
            sim = self.NM_StartingSimplex
            # then we assume the user entered their own simplex. No additional error handling is included because
            # scipy do their own
        else:
            logger.error('Starting simplex can only be defined as a relative parameter, e.g. 0.1, or as an array of size'
                         '[N+1, N]. Quitting')
            sys.exit(1)

        self.StartingSimplex = sim

    def RunOptimisation(self):
        """
        Use the scipy.optimize.minimize module to perform the optimisation.
        Note that most of the 'action' is happening in BlackBoxFunction, which is repeated called by the optimiser
        """

        self.SetUpDirectoryStructure()
        if self.StartingSimplexSupplied:
            StartingSimplex = self.StartingSimplex
        else:
            StartingSimplex = None

        bnds = tuple(zip(self.LowerBounds, self.UpperBounds))

        self.NelderMeadRes = minimize(self.BlackBoxFunction, self.StartingValues, method='Nelder-Mead', bounds=bnds,
                       options={'disp': True, 'initial_simplex': StartingSimplex,
                                'maxiter': self.MaxItterations, 'maxfev': self.MaxItterations})
        self._write_final_log_entry()


class BayesianOptimiser(TopasOptBaseClass):
    """
    Class to perform optimisation using the `Bayesian Optimisation code <https://github.com/fmfn/BayesianOptimization>`_
    Specific options are described below, the rest are described in TopasOptBaseClass

    :param bayes_length_scales: Bayes-specific parameter to defined the length scales used in the gaussian process
        model. If supplied to non-Bayes optimisers it does nothing (and hopefully you will be warned accordingly).
        This can be supplied as one of three things: **None**: in this case, the default is used: length_scale=1.0
        **Number > 0 and <1**: in this case, the length scales for each parameter are derived as a percentage of range.
        For instance if the user enter 0.1, all length scales will be set to 10% of the range of each variable -
        this is the default behavior. **Array**: Finally, the user is free to simply specify what length scales to use for each parameter. Make sure
        you enter them in alphabetical order as this is the order used internally by the optimiser.
    :type bayes_length_scales: None, float, or array (optional)
    :param bayes_UCBkappa: Bayes-specific parameter . kappa value in UCB  function. A higher value=more exploration. see
        `this notebook <https://github.com/fmfn/BayesianOptimization/blob/master/examples/exploitation_vs_exploration.ipynb>`_
        for explanation
    :type bayes_UCBkappa: float, optional
    :param bayes_KappaDecayIterations: Bayes-specific parameter. Over the last N iterations, kappa will decay to be
        almost 0 (highly exploitive). For explantion of kappa decay see `here <https://github.com/fmfn/BayesianOptimization/pull/221>`_
    :type bayes_KappaDecayIterations: int, optional
    :param bayes_GP_alpha: Bayes-specific parameter. This parameter handles the smoothness of the gaussian process model.
        for a noisy objective function, increasing this value can minimise overfitting errors.
    :type bayes_GP_alpha: float, optional
    """

    def __init__(self, bayes_length_scales=None, bayes_UCBkappa=5,
                 bayes_KappaDecayIterations=10, bayes_GP_alpha=0.01, **kwds):
        """
        init function for Bayesian optimiser
        """
        self.bayes_length_scales = bayes_length_scales
        self.bayes_UCBkappa = bayes_UCBkappa
        self.bayes_KappaDecayIterations = bayes_KappaDecayIterations
        self.bayes_GP_alpha = bayes_GP_alpha
        super().__init__(**kwds)

        self.BayesOptLogLoc = Path(self.BaseDirectory) / self.SimulationName / 'logs/bayes_opt_logs.json'
        self._BayesianOptimiser__RestartMode = False  # don't change!
        self._create_p_bounds(self._optimisation_params)  # Bayesian optimiser wants bounds in a slight differnt format
        self._create_suggested_points_to_probe(self._optimisation_params)
        self._derive_bayes_length_scales(bayes_length_scales)

        # Bayesian optimisation settings:
        self._target_prediction_mean = []  # keep track of what the optimiser expects to get
        self._target_prediction_std = []  # keep track of what the optimiser expects to get
        # see here: https://github.com/fmfn/BayesianOptimization/issues/202
        self.Matern_Nu = 1.5  # see here https://scikit-learn.org/stable/modules/generated/sklearn.gaussian_process.kernels.Matern.html#sklearn.gaussian_process.kernels.Matern
        self.UCBkappa = bayes_UCBkappa  # higher kappa = more exploration. lower kappa = more exploitation
        self.n_restarts_optimizer = 20  # this controls the gaussian process fitting. 20 seems to be a good number.
        self.bayes_KappaDecayIterations = bayes_KappaDecayIterations
        self.UCBKappa_final = 0.1
        self.kappa_decay_delay = self.MaxItterations - self.bayes_KappaDecayIterations  # this many exploritive iterations will be carried out before kappa begins to decay

        if self.kappa_decay_delay >= self.MaxItterations:
            logger.warning(f'Kappa decay requested, but since kappa_decay_delay ({self.kappa_decay_delay}) is less'
                           f'than MaxItterations ({self.MaxItterations}), decay will never occur...')
            self.kappa_decay = 1
        else:
            self.kappa_decay = (self.UCBKappa_final / self.UCBkappa) ** (
                        1 / (self.MaxItterations - self.kappa_decay_delay))
            # ^^ this is the parameter to ensure we end up with UCBKappa_final on the last iteration


    def _derive_bayes_length_scales(self, bayes_length_scales):
        """
        Figure out what to put in to the gaussian process model kernel for length scales.
        We use the Matern Kernel which is detailed `here <https://scikit-learn.org/stable/modules/generated/sklearn.gaussian_process.kernels.Matern.html#sklearn.gaussian_process.kernels.Matern>`_

        :param bayes_length_scales: user input for length scales. Can be one of three things:
            1. **None**: in this case, the default is used: length_scale=1.0
            2. Number > 0 and <1: in this case, the length scales for each parameter are derived as a percentage of range.
                For instance if the user enter 0.1, all length scales will be set to 10% of the range of each variable.
            3. Array: Finally, the user is free to simply specify what length scales to use for each parameter. Make sure
                you enter them in alphabetical order as this is the order used internally by the optimiser.
        """
        ParameterNames = sorted(self.pbounds.keys())
        if bayes_length_scales is None:
            bayes_length_scales = 0.1
            self.bayes_length_scales = []
            for paramter_name in ParameterNames:
                length_scale_temp = (self.pbounds[paramter_name][1] - self.pbounds[paramter_name][0]) * bayes_length_scales
                self.bayes_length_scales.append(length_scale_temp)
        elif type(bayes_length_scales) is float:
            self.bayes_length_scales = []
            for paramter_name in ParameterNames:
                length_scale_temp = (self.pbounds[paramter_name][1] - self.pbounds[paramter_name][0]) * bayes_length_scales
                self.bayes_length_scales.append(length_scale_temp)
        elif type(bayes_length_scales) is list or type(bayes_length_scales) is np.ndarray:

            if not len(bayes_length_scales) == len(ParameterNames):
                logger.error(f'length of bayes_length_scales must be single values or match number of parameters; you have'
                             f'{len(ParameterNames)} Parameters, but {len(bayes_length_scales)} bayes_length_scales. Quitting')
                sys.exit(1)
            self.bayes_length_scales = bayes_length_scales

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

        ResultsDict = ReadInLogFile(self._LogFileLoc)

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
                                self._target_prediction_mean]  # need to account for min/max discrepancy
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

    def _update_logs_with_length_scales(self):
        """
        writes the original and optimised length scales to the end of a log file
        """
        start_length = self.optimizer._gp.kernel.length_scale
        final_length = self.optimizer._gp.kernel_.length_scale
        keys = sorted(self.pbounds)
        start_length = dict(zip(keys, start_length))
        final_length = dict(zip(keys, final_length))
        Entry = f'\nStarting length scales were {start_length}'
        Entry = Entry + f'\nOptimised length scales were {final_length}'

        with open(self._LogFileLoc , 'a') as f:
            f.write(Entry)

    def RunOptimisation(self):
        """
        This is the main optimisation loop.
        For explanation of the various parameters and commands, start with the
        """

        # set up directory structure
        if not self.__RestartMode:
            self.SetUpDirectoryStructure()
        else:
            self._setup_topas_emulator()

        # instantiate optimizer:

        self.optimizer = BayesianOptimization(f=None, pbounds=self.pbounds, random_state=1)
        self.optimizer.set_gp_params(normalize_y=True, kernel=Matern(length_scale=self.bayes_length_scales, nu=self.Matern_Nu),
                                n_restarts_optimizer=self.n_restarts_optimizer, alpha=self.bayes_GP_alpha)  # tuning of the gaussian parameters...
        utility = UtilityFunction(kind="ucb", kappa=self.UCBkappa, xi=0.0, kappa_decay_delay=self.kappa_decay_delay,
                                  kappa_decay=self.kappa_decay)
        logger.warning('setting numpy to ignore underflow errors.')
        np.seterr(under='ignore')

        if self.__RestartMode:
            # then load the previous log files:
            load_logs(self.optimizer, logs=[self.BayesOptLogLoc])
            bayes_opt_logger = newJSONLogger(path=str(self.BayesOptLogLoc))
            self.optimizer.subscribe(Events.OPTIMIZATION_STEP, bayes_opt_logger)
            self.optimizer._gp.fit(self.optimizer._space.params, self.optimizer._space.target)
            self.Itteration = len(self.optimizer.space.target)
            self.ItterationStart = len(self.optimizer.space.target)
            utility._iters_counter = self.ItterationStart
            if self.Itteration >= self.MaxItterations-1:
                logger.error(f'nothing to restart; max iterations is {self.MaxItterations} and have already been completed')
                sys.exit(1)
        else:
            bayes_opt_logger = JSONLogger(path=str(self.BayesOptLogLoc))
            self.optimizer.subscribe(Events.OPTIMIZATION_STEP, bayes_opt_logger)
            # first guess is nonsense but we need the vectors to be the same length
            self._target_prediction_mean.append(0)
            self._target_prediction_std.append(0)
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
            self._target_prediction_mean.append(mean[0])
            self._target_prediction_std.append(std[0])
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
        self._write_final_log_entry()
        # update logs with length scales:
        self._update_logs_with_length_scales()

    def RestartOptimisation(self):
        """
        Sometimes for whatever reason an optimisation is stopped prematurely.
        This function allows you to restart the optimisation by loading the previous log files.
        You just have to change Optimiser.RunOptimisation() to Optimiser.RestartOptimisation()
        in your optimisation script; the code will do the rest automatically.
        """
        self.__RestartMode = True


        # delete the end of run info from the log file
        with open(self._LogFileLoc, "r") as f:
            lines = f.readlines()
        with open(self._LogFileLoc, "w") as f:
            for line in lines:
                if line[0:10] == 'Itteration':
                    f.write(line)

        self.RunOptimisation()

