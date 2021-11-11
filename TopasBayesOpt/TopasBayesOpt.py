# -*- coding: iso-8859-1 -*-
import subprocess
import jsonpickle
from matplotlib import pyplot as plt
# matplotlib.use('Agg')  # having trouble with generating figures through ssh, hopefiully this resolves...
from matplotlib import rcParams
import shutil
import glob
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
from bayes_opt import SequentialDomainReductionTransformer
from sklearn.gaussian_process.kernels import Matern
import logging
from utilities import bcolors

# formatter = logging.Formatter('[%(filename)s: line %(lineno)d %(levelname)8s] %(message)s')
# ch = logging.StreamHandler()
# ch.setFormatter(formatter)
# logger = logging.getLogger(__name__).addHandler(ch)
# logger.setLevel(logging.INFO)

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
    import os
    import sys

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
    We provide two different method's for performing optimisation: Downhill Simplex, and Bayesian with Gausian Processes.

    However, there are many overlapping functinoalities between these two methods: logging, calculation of objective function,
    generation of models...etc.
    To avoid duplication and ensure consistency between the two methods, we store all of these methods in a base class
    which the two different optimisation methods inherit.
    This class also contains various methods for plotting the results of log files output by the optimisers, which can
    be useful for analysis and debugging
    """

    def __init__(self):
        self.Overwrite = True
        self.BeamletWidthPrecision = 0.25  # in mm. Results are rounded to the nearerst BeamletWidthPrecision,
        # AND, differences smaller than this are ignored.
        self.Nparticles = 10000000  # primary particles in topas sim
        self.CrossChannelLeakageLimit = 5  # Defined as NeighborDose * 100 /MainDose
        self.AllObjectiveFunctionValues = []
        self.CopyResultsToRemoteServer = True  # will try to to copy the results to the paths below (first one that works)
        self.RemoteServerPaths = ['/rds/PRJ-Phaser/PhaserSims/topas/', '/home/brendan/RDS/PRJ-Phaser/PhaserSims/topas/',
                                  '/mrlSSDfixed/Brendan/RDS/PRJ-Phaser/PhaserSims/topas/']
        self.BadSolutionOF = 70  # this is the max value returned by the OF. To help the bayesian optimiser, it should be
        # on the same order of magntiude as the expected minimum OF.

    def CreateVariableDictionary(self, x):
        """
        Use the input information to create a dictionary of geometric inputs. This creates an elegant method to
        create phaser geometries downstream in GenerateTopasModel

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

    def EmptySimulationFolder(self):
        """
        If there is already stuff in the simulation folder, ask for user permission to empty and continue
        """
        SimName = str(Path(self.BaseDirectory) / self.SimulationName)
        if os.listdir(SimName):
            logger.warning(f'Directory {SimName} is not empty; if you continue it will be emptied.')

            try:
                if self.Overwrite:
                    UserOverwrite = 'y'
                else:
                    UserOverwrite = input()
            except AttributeError:
                print(f'\nPlease enter y/n:')
                UserOverwrite = input()
            if (UserOverwrite.lower() == 'n') or (UserOverwrite.lower() == 'no'):
                logger.warning('quitting')
                sys.exit()
            elif (UserOverwrite.lower() == 'y') or (UserOverwrite.lower() == 'yes'):
                print('emptying simulation folder')
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

    def CheckInputData(self):
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

        MinTargThicknessValues = []  # keep track of this below
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

            if 'targ_Thicknesses' in Paramter:
                # need to make sure we have at least one layer with a non zero minimum
                MinTargThicknessValues.append(self.LowerBounds[i])

        if MinTargThicknessValues:  # check list is not empty
            if (np.array(MinTargThicknessValues) == 0).all():
                logger.error('At least one target layer must have a non zero minimum; '
                             '\nrunning simulations with no target makes no sense and wont work. Quitting')
                sys.exit(1)

        if (self.StartingValues == 0).any():
            Names = np.asarray(self.ParameterNames, dtype=object)
            ind = self.StartingValues == 0
            Names = list(Names[ind])
            logger.error(
                f'{bcolors.FAIL}At the moment no starting values can be zero, because we use the starting values '
                f'to create relative values.\nThis is a fairly inherent limiation of this code, fixable but not '
                f'fixed!The following parameters have starting values of zero:\n{Names}{bcolors.ENDC}')
            sys.exit(1)

        self.CreateVariableDictionary(self.StartingValues)
        NewVariableDict = self.targ_Thicknesses_toList()  # converts targ_Thicknesses terms to list if they exist

    def GenerateTopasModel(self, x):
        """
        Generates a topas model with the latest parameters as well as a shell script called RunAllFiles.sh to run it.
        """

        # if RunAllFiles exists, delete it
        ShellScriptLocation = str(Path(self.BaseDirectory) / self.SimulationName / 'RunAllFiles.sh')
        if os.path.isfile(ShellScriptLocation):
            # I don't think I should need to do this; the file should be overwritten if it exists, but this doesn't
            # seem to be working so deleting it.
            os.remove(ShellScriptLocation)
        self.ShellScriptLocation = ShellScriptLocation
        ParameterString = f'run_{self.Itteration}'
        # for i, Paramter in enumerate(self.ParameterNames):
        #     ParameterString = ParameterString + f'_{Paramter}_{x[0][i]:1.1f}'

        if self.debug:
            UsePhaseSpaceSource = False
            Nparticles = 10000
        else:
            UsePhaseSpaceSource = True
            Nparticles = self.Nparticles

        self.TopasScripts = self.TopasScriptGenerator(self.BaseDirectory, self.Itteration, **self.VariableDict)
        print('hello')

    def RunTopasModel(self):
        """
        This invokes a bash subprocess to run the current model
        """
        print(f'{bcolors.OKBLUE}Topas: Running file: \n{self.ShellScriptLocation}')
        ShellScriptPath = str(Path(self.BaseDirectory) / self.SimulationName)
        cmd = subprocess.run(['bash', self.ShellScriptLocation], cwd=ShellScriptPath)
        print(f'{bcolors.OKBLUE}Analysis complete{bcolors.ENDC}')

        # update the definition of current model
        self.CurrentWTdata = self.TopasScript.WT_PhaseSpaceName_current

    def ReadTopasResults(self):
        """
        Read in topas results and extract quantities of interest

        Returns two parameters:
        BeamletWidth (double, mm)
        MaxDose (double, AU)
        """

        DataLocation = str(Path(self.BaseDirectory) / self.SimulationName / 'Results')

        # use similar triangles to derive desired beamlet width at surface
        TargToIso = self.PhaserGeom.VirtSourceToIso - self.PhaserGeom.SourceToTarget
        TargToSurface = TargToIso - self.TopasScript.WT_PhantomSize
        desiredBWsurface = (self.TargetBeamWidth * TargToSurface) / TargToIso
        Dose = WaterTankData(DataLocation, self.CurrentWTdata,
                             AbsDepthDose=True, MirrorData=False,
                             DesiredBeamletWidthAtSurface=desiredBWsurface,
                             FourierFilterIsoPlanData=False)
        # store the relevant quantities:
        self.BeamletWidth = Dose.BeamletWidthsManual[0]
        # round beamlet width to beamlet width precision:
        self.CrossChannelLeakage = Dose.CrossChannelLeakageRatio[0] * 100  # convert to %
        print(f'cross channel leakage is {self.CrossChannelLeakage}')
        self.MaxDoseGauss = Dose.MaxDoseAtIsoplaneGauss[0]
        self.MaxDose = Dose.DosePerCoulomb[0]/1e3  # starts in Gy/C so this makes is Gy/mC or kGy/C
        self.DmaxToD100 = Dose.DmaxToD100[0]
        self.RelOutOfFieldSurfDose = Dose.RelOutOfFieldSurfDose[0]

    def UpdateOptimisationLogs(self, x, OF):
        """
        Just a simple function to keep track of the objective function in the logs folder
        """

        LogFile = Path(self.BaseDirectory) / self.SimulationName
        LogFile = LogFile / 'logs'
        LogFile = str(LogFile / 'OptimisationLogs.txt')

        with open(LogFile, 'a') as f:
            Entry = f'Itteration: {self.Itteration}'
            for i, Parameter in enumerate(self.ParameterNames):
                Entry = Entry + f', {Parameter}: {x[0][i]: 1.2f}'
            Entry = Entry + f', BeamletWidth: {self.BeamletWidth: 1.2f}'
            Entry = Entry + f', Dose: {self.MaxDose: 1.2f}'
            Entry = Entry + f', CrossChannelLeakage: {self.CrossChannelLeakage: 1.2f}'
            Entry = Entry + f', Dmax/D100: {self.DmaxToD100: 1.2f}'
            Entry = Entry + f', OutOfFieldSurface: {self.RelOutOfFieldSurfDose: 1.2f}'
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
            if self.BoundaryViolation:
                Entry = Entry + '^^ BOUNDS VIOLATION DETECTED!\n'
            if self.WallThicknessError:
                Entry = Entry + '^^ WALL THICKNESS VIOLATION DETECTED!\n'
            f.write(Entry)
        print(f'{bcolors.OKGREEN}{Entry}{bcolors.ENDC}')

    def PlotResults(self):

        ItterationVector = np.arange(self.ItterationStart, self.Itteration + 1)

        fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(10, 5))
        axs[0].plot(ItterationVector, self.AllObjectiveFunctionValues, 'C1')
        axs[0].set_xlabel('Itteration number', fontsize=FigureSpecs.LabelFontSize)
        axs[0].set_ylabel('Objecti'
                          've function', fontsize=FigureSpecs.LabelFontSize)
        axs[0].grid(True)

        try:
            target_prediction = -1 * np.array(self.target_prediction_mean, )
            axs[0].plot(ItterationVector, target_prediction, 'C0')
            axs[0].fill_between(ItterationVector,
                                target_prediction + self.target_prediction_std,
                                target_prediction - self.target_prediction_std, alpha=0.15, color='C0')
            axs[0].legend(['Actual', 'Predicted', r'$\sigma$'])
        except AttributeError:
            # predicted isn't always available
            pass

        MinValue = np.argmin(self.AllObjectiveFunctionValues)
        axs[0].plot(ItterationVector[MinValue], self.AllObjectiveFunctionValues[MinValue], 'r-x')
        axs[0].set_title('Convergence Plot', fontsize=FigureSpecs.TitleFontSize)

        LegendStrings = []
        for i, ParameterVals in enumerate(self.AllParameterValues.T):
            LegendStrings.append(f'{self.ParameterNames[i]}: InitVal = {self.StartingValues[i]}')
            try:
                ParameterVals = ParameterVals / ParameterVals[0]
            except FloatingPointError:
                logger.error(f'got that weird error...ParameterVals were {ParameterVals}.\nnot normalising parameters...')
            axs[1].plot(ItterationVector, ParameterVals)

        axs[1].legend(LegendStrings)

        axs[1].plot(ItterationVector[MinValue], ParameterVals[MinValue], 'r-x')
        axs[1].set_xlabel('Itteration number', fontsize=FigureSpecs.LabelFontSize)
        axs[1].set_ylabel('Relative parameter values', fontsize=FigureSpecs.LabelFontSize)
        axs[1].grid(True)
        axs[1].set_title('Parameter values', fontsize=FigureSpecs.TitleFontSize)

        SaveLoc = Path(self.BaseDirectory) / self.SimulationName
        SaveLoc = SaveLoc / 'logs'
        plt.savefig(SaveLoc / 'Results.png')
        plt.close(fig)

    def CalculateObjectiveFunction(self):
        """
        Calculate and log the objective function for the current itteration
        """

        w1 = 22  # max dose weight
        w2 = 50  # Beamlet width weight
        w3 = 1e-2  # Collimator Thickness - note collimator thickness is in mm. So this returns 2.5 for a 250 mm collimator
        w4 = 5  # minimise out of field surface dose (electron scatter)
        w5 = 5  # CrossChannelLeakageTerm
        w6 = 20  # electron contamination dose

        self.CalculateBoundaryViolationTerm()
        if self.WallThicknessError or (self.BoundaryViolationTerm > 0) or (self.CrossChannelLeakage > 30):
            # just return a constant high value (set in self.BadSolutionOF) for these really bad solutions.
            # Otherwise the OF can get very spiky and discontinuous.
            self.OF = self.BadSolutionOF
            self.AllObjectiveFunctionValues.append(self.OF)
            self.AllParameterValues = np.vstack([self.AllParameterValues, self.x])
            self.UpdateOptimisationLogs(self.x, self.BadSolutionOF)
            self.PlotResults()
            self.Itteration = self.Itteration + 1
            return
        if abs(self.TargetBeamWidth - self.BeamletWidth) < self.BeamletWidthPrecision:
            DeltaBeamletWidth = 0
        else:
            DeltaBeamletWidth = abs(self.TargetBeamWidth - self.BeamletWidth)

        if self.CrossChannelLeakage > self.CrossChannelLeakageLimit:
            self.CrossChannelLeakageTerm = self.CrossChannelLeakage
        else:
            self.CrossChannelLeakageTerm = 0

        if self.DmaxToD100 < 2.5:
            self.eContaminationTerm = 0
        else:
            self.eContaminationTerm = self.DmaxToD100

        if self.RelOutOfFieldSurfDose < 1:
            # ~1% seems to be the value at least to the eye where there is no electron contamination to speak of
            self.RelOutOfFieldSurfDose = 0

        if 'coll_CollimatorThickness' in self.VariableDict.keys():
            collimatorThickness = self.VariableDict['coll_CollimatorThickness']
        else:
            collimatorThickness = 0

        OF = (-w1 * self.MaxDose) + (DeltaBeamletWidth * w2) + (w3 *collimatorThickness) \
             + (w4 * self.RelOutOfFieldSurfDose) + (w5 * self.CrossChannelLeakageTerm) + (w6 * self.eContaminationTerm)
        if OF > self.BadSolutionOF:
            OF = self.BadSolutionOF

        self.AllObjectiveFunctionValues.append(OF)
        try:
            self.AllParameterValues = np.vstack([self.AllParameterValues, self.x])
        except AttributeError:
            self.AllParameterValues = self.x
        self.UpdateOptimisationLogs(self.x, OF)
        self.PlotResults()
        self.Itteration = self.Itteration + 1
        self.OF = OF

    def CalculateBoundaryViolationTerm(self):
        """
        Depending on the optimiser chosen, the limits may or may not be enforced by the optimiser.
        If they are enforced, this function always returns 0.
        If thay are not and the bounds are violated, returns a positive value proportional to the extent of the violation
        if outside the bounds.
        I've normalised parameter values to their starting values, such that a 10% violation in variable 1 is penalised
        the same way as variable 2. Note that this value is also multiplied by a weight in CalculateObjectiveFunction;
        by using a high weight, we should ensure that violations do not occur
        """
        self.BoundaryViolation = False
        try:
            test = self.StartingValues[0][1]
            StartingValues = self.StartingValues[0]
        except IndexError:
            StartingValues = self.StartingValues

        self.BoundaryViolationTerm = int(0)
        RelativeParameters = np.divide(self.x[0], StartingValues)
        RelativeUpperLimit = np.divide(self.UpperBounds, StartingValues)
        RelativeLowerLimit = np.divide(self.LowerBounds, StartingValues)
        for i, ParameterName in enumerate(self.ParameterNames):

            index = self.ParameterNames.index(ParameterName)
            ParameterUpperLimit = RelativeUpperLimit[index]
            ParameterLowerLimit = RelativeLowerLimit[index]
            self.BoundaryViolationTerm = self.BoundaryViolationTerm + \
                                         (min(0, ParameterUpperLimit - RelativeParameters[index]) ** 2) + \
                                         np.sqrt(abs(min(0, RelativeParameters[index] - ParameterLowerLimit)))

            if self.x[0][i] < self.LowerBounds[i]:
                print(f'{bcolors.WARNING}For {ParameterName}, Value {self.x[0][i]} is less than '
                      f'Lower bound {self.LowerBounds[i]}{bcolors.ENDC}')
            elif self.x[0][i] > self.UpperBounds[i]:
                print(f'{bcolors.WARNING}For {ParameterName}, Starting value {self.x[0][i]} is greater '
                      f'than upper bound {self.UpperBounds[i]}{bcolors.ENDC}')

        if self.BoundaryViolationTerm > 0:
            self.BoundaryViolation = True
            print('Boundary violation detected')

    def CopySelf(self):
        """
        Copies all class attributes to a a (human readable) json file called 'SimulationSettings'.
        This is so you can exactly which settings were used to generate a given simulation
        """

        Filename = Path(self.BaseDirectory) / Path(self.SimulationName) / 'OptimisationSettings.json'

        Attributes = jsonpickle.encode(self, unpicklable=False, max_depth=3)
        f = open(str(Filename), 'w')
        f.write(Attributes)

    def targ_Thicknesses_toList(self):
        """
        Because the target thicknesses are entered into PhaserBeamLine as a list instead of floats,
        we need to do some clever wrangling to convert them into an appropriate format before we create that
        instance
        """
        NewVariableDict = {}
        targ_Thicknesses_list = []
        SortedKeys = sorted(self.VariableDict.keys())  # this ensures any targ_Thicknesses terms are ordred correctly
        for key in self.VariableDict.keys():
            if 'targ_Thicknesses' in key:
                targ_Thicknesses_list.append(self.VariableDict[key])
            else:
                # no change needed
                NewVariableDict[key] = self.VariableDict[key]
        if targ_Thicknesses_list:  # not empty evaluates as true
            NewVariableDict['coll_targ_Thicknesses'] = targ_Thicknesses_list

        return NewVariableDict

    def GetAllbinFiles(self, AnalysisPath):
        """
        quick script to just collect all the files in the Analysis path
        """

        if not os.path.isdir(AnalysisPath):
            logger.error(f'invalid path supplied; {AnalysisPath} does not exist')
        AllCSVFiles = glob.glob(AnalysisPath + '/*.bin')
        File = []
        for file in AllCSVFiles:
            head, tail = os.path.split(file)
            File.append(tail)
        if not File:
            logger.error(f'no bin files in {AnalysisPath}')
            sys.exit()
        return File

    def RewindResults(self):
        """
        This function allows you to read in previously calculated water tank files and calculate the objective function
        it can be useful for fine tuning and optimising the objective function but is not part of the normal optimisation
        workflow.
        You should check to actual objective function matches the one below since they are independant

        It requires manual input below to specifiy where the files are. And it won't work
        for cases where there is a wall thickness violation or boundary violation. it's basically fiddly and ugly :-)
        """
        self.BaseDirectory = '/project/Phaser/PhaserSims/topas/'
        self.SimulationName = 'BayesianOptimisation_Hard'
        AnalysisPath = self.BaseDirectory + self.SimulationName + '/Results'
        # self.StartingDoseFile='/home/brendan/Dropbox (Sydney Uni)/Projects/PhaserSims/topas/PaulGeom_BSI_2_6_5/Results/WT_xAng_0.00_yAng_0.00_BSI_2.0.bin',
        # self.ReadTopasResults(StartingDoseFile=self.StartingDoseFile)
        # self.StartingValuesProvided = True
        FilesToAnalyse = self.GetAllbinFiles(AnalysisPath)
        FilesToAnalyse = ['WT_xAng_0.00_yAng_0.00_run_78.bin']

        FilesToAnalyse.sort()
        self.TargetBeamWidth = 7
        self.Itteration = 0

        w1 = 30  # max dose weight
        w2 = 50  # Beamlet width weight
        w3 = 1  # Collimator Thickness
        w4 = 5  # minimise out of field surface dose (electron scatter)
        w5 = 5  # CrossChannelLeakageTerm
        w6 = 20  # electron contamination dose

        for file in FilesToAnalyse:
            self.CurrentWTdata = file
            self.ReadTopasResults()
            if abs(self.TargetBeamWidth - self.BeamletWidth) < self.BeamletWidthPrecision:
                DeltaBeamletWidth = 0
            else:
                DeltaBeamletWidth = abs(self.TargetBeamWidth - self.BeamletWidth)

            if self.CrossChannelLeakage > self.CrossChannelLeakageLimit:
                self.OutOfFieldDoseTerm = self.CrossChannelLeakage
            else:
                self.OutOfFieldDoseTerm = 0
            print(f'Out of field dose term is {w5 * self.OutOfFieldDoseTerm}')

            OF = (-w1 * self.MaxDose) + (DeltaBeamletWidth * w2) + (w3 * self.RelativeCollimatorThickness) \
                 + (w5 * self.OutOfFieldDoseTerm)

    def CopyResultsToServer(self):
        """
        Will attempt to copy the results to RDS.
        """
        ResultsCopied = False
        if not self.CopyResultsToRemoteServer:
            return

        try:
            for ServerPath in self.RemoteServerPaths:
                # loop over all; use the first one that works
                if os.path.isdir(ServerPath):
                    BashCommand = 'cp -r ' + "'" + self.BaseDirectory + '/' + self.SimulationName + "' " + "'" + ServerPath + "'"
                    subprocess.run(BashCommand, shell=True)
                    ResultsCopied = True
                if ResultsCopied:
                    break
        except:
            pass

        if not ResultsCopied:
            logger.warning('failed to upload results to remote server.')

    def ReadInLogFile(self, LogFileLoc):
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

    def PlotLogFile(self, LogFileLoc):
        """
        This function can be used to plot an existing log file
        need to fix because now itteration and OF are stored in dict
        """
        ResultsDict = self.ReadInLogFile(LogFileLoc)
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

    def PlotLogFileScatter(self, LogFileLoc, RemoveOutliers=True):
        """
        Create a scatter plot of bayesian prediction versus actual value of objective function from log file.
        Unlike the in-optimiser function, in this case we can assess and remove outliers before assessing correlation

        :param LogFileLoc: Path location of the log flie to plot
        :param RemoveOutliers: If True, will remove outliers based on the Zscore of the OF (Zscore>2 used at time of writing).
        """
        ResultsDict = self.ReadInLogFile(LogFileLoc)
        OF = np.array(ResultsDict.pop('ObjectiveFunction'))
        prediction = -1 * np.array(ResultsDict.pop('target_prediction_mean'))
        OF = np.delete(OF, [0])
        try:
            prediction = np.delete(prediction, [0])
        except KeyError:
            logger.error('Log file does not contain target_prediction_mean')
            return

        if RemoveOutliers:
            # remove datapoints in objective function
            Zscore = (OF - np.mean(OF)) / np.std(OF)
            ind = Zscore > 2
            OF = np.delete(OF, ind)
            prediction = np.delete(prediction, ind)

        fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(5, 5))
        axs.scatter(OF, prediction)
        axs.set_xlabel('Actual', fontsize=FigureSpecs.LabelFontSize)
        axs.set_ylabel('Predicted', fontsize=FigureSpecs.LabelFontSize)
        NewMinLim = np.min([axs.get_ylim(), axs.get_xlim()])
        NewMaxLim = np.max([axs.get_ylim(), axs.get_xlim()])
        axs.set_ylim([NewMinLim, NewMaxLim])
        axs.set_xlim([NewMinLim, NewMaxLim])
        axs.plot([NewMinLim, NewMaxLim], [NewMinLim, NewMaxLim], 'r--')

        # Assess and print correlation metrics:
        if len(prediction) > 2:
            Pearson = stats.pearsonr(OF, prediction)
            Spearman = stats.spearmanr(OF, prediction)
            plt.text(NewMinLim + abs(NewMinLim * 0.2), NewMaxLim - (abs(NewMaxLim * 0.2)),
                     f'Spearman: {Spearman[0]: 1.1f}\nPearson: {Pearson[0]: 1.1f}',
                     fontsize=FigureSpecs.LabelFontSize)

        axs.grid(True)
        axs.set_title('Actual versus predicted correlation', fontsize=FigureSpecs.TitleFontSize)
        plt.tight_layout()
        plt.show()

    def PlotLogFile_BayesianClusters(self, LogFileLoc, ClusterThreshold=10):
        """
        Read in a log file from the Bayesian optimiser, group points together according to the ClusterThreshold,
        and plot the actual versus predicted objective function.
        I'm going to code it to start with two points: the best it found and the worst point. In principle, this points
        variable could be an input, or even something automatically determined by a clustering algorithm. this is the
        quick(ish) and dirty version!

        :param LogFileLoc: the path to the log dile
        :type LogFileLoc: string
        :param ClusterThreshold: percentage that points should be within each other to count as clustered
        :type ClusterThreshold: double
        """

        ResultsDict = self.ReadInLogFile(LogFileLoc)
        OF = np.array(ResultsDict.pop('ObjectiveFunction'))
        # remove stuff we don't want: whats left should be our variables (unfortunately not robust to changes in log file format)
        Itteration = np.array(ResultsDict.pop('Itteration'))
        Dose = np.array(ResultsDict.pop('Dose'))
        CrossChannelLeakage = np.array(ResultsDict.pop('CrossChannelLeakage'))
        BeamletWidth = np.array(ResultsDict.pop('BeamletWidth'))
        try:
            prediction = -1 * np.array(ResultsDict.pop('target_prediction_mean'))
            prediction_std = -1 * np.array(ResultsDict.pop('target_prediction_std'))
        except KeyError:
            logger.error('Log file does not contain target_prediction_mean')
            return

        # identify points:
        ind_best = np.argmin(OF)
        ind_worst = np.argmax(OF)
        print(
            f'Reading in log file: The following parameters have been identified as the variables: {ResultsDict.keys()}')
        OptimisationVariables = np.array(list(ResultsDict.values()))
        BestPoint = OptimisationVariables[:, ind_best]
        WorstPoint = OptimisationVariables[:, ind_worst]

        BestPointThresholdUpper = (1 + ClusterThreshold / 100) * BestPoint
        BestPointThresholdLower = (1 - ClusterThreshold / 100) * BestPoint
        WorstPointThresholdUpper = (1 + ClusterThreshold / 100) * WorstPoint
        WorstPointThresholdLower = (1 - ClusterThreshold / 100) * WorstPoint

        ind_bestCluster = np.zeros(OptimisationVariables.shape)
        ind_worstCluster = np.zeros(OptimisationVariables.shape)
        for i in range(OptimisationVariables.shape[0]):
            # get the points within +/- ClusterThreshold in a loop
            ind_bestCluster[i, :] = np.logical_and(OptimisationVariables[i, :] < BestPointThresholdUpper[i],
                                                   OptimisationVariables[i, :] > BestPointThresholdLower[i])
            ind_worstCluster[i, :] = np.logical_and(OptimisationVariables[i, :] < WorstPointThresholdUpper[i],
                                                    OptimisationVariables[i, :] > WorstPointThresholdLower[i])
        ind_bestCluster = np.sum(ind_bestCluster, axis=0) == OptimisationVariables.shape[0]
        ind_worstCluster = np.sum(ind_worstCluster, axis=0) == OptimisationVariables.shape[0]

        fig, axs = plt.subplots(nrows=1, ncols=2, figsize=(10, 5))
        axs[0].plot(Itteration[ind_bestCluster], OF[ind_bestCluster], '-x', color='C1')
        axs[0].plot(Itteration[ind_bestCluster], prediction[ind_bestCluster], '-x', color='C0')
        axs[0].fill_between(Itteration[ind_bestCluster],
                            prediction[ind_bestCluster] + prediction_std[ind_bestCluster],
                            prediction[ind_bestCluster] - prediction_std[ind_bestCluster], alpha=0.15, color='C0')
        axs[0].legend(['Actual', 'Predicted', r'$\sigma$'])
        axs[0].set_title('Best points cluster')
        axs[0].legend(['Real', 'Predicted'])

        axs[1].plot(Itteration[ind_worstCluster], OF[ind_worstCluster], '-x')
        axs[1].plot(Itteration[ind_worstCluster], prediction[ind_worstCluster], '-x')
        axs[1].fill_between(Itteration[ind_worstCluster],
                            prediction[ind_worstCluster] + prediction_std[ind_worstCluster],
                            prediction[ind_worstCluster] - prediction_std[ind_worstCluster], alpha=0.15, color='C0')
        axs[1].legend(['Actual', 'Predicted', r'$\sigma$'])
        axs[1].set_title('Worst points cluster')
        axs[1].legend(['Real', 'Predicted'])
        plt.show()


class NealderMeadOptimiser(TopasOptBaseClass):
    """
    the purpose of this code is to run a optimsiation of the central channel for the sphinx collimator.
    The goal is to maximise the dose/dose rate while maintaining TargetBeamWidth. This is a work in progress.

    .. figure:: ../doc_source/_static/07012021_BeamletWidths.png
        :align: center
        :alt: FreeCAD setup
        :scale: 100%
        :figclass: align-center
    """

    def __init__(self, optimisation_params, BaseDirectory, SimulationName, TargetBeamWidth=7, debug=True, Nthreads=-6,
                 StartingSimplexRelativeVal=None, length_scales=None):
        """
        Set up the parameters to be optimised and bounds.

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
        :param StartingSimplexRelativeVal: If supplied, will construct the starting simplex around the starting values
            using this number. By default, scipy uses 0.05, which creates a simplex 0.05 around the starting values.
            If this seems to small (e.g. your answer is likely to be further away from the starting point than that),
            you can increase this number here.
        :type StartingSimplexRelativeVal: double, optional
        :param MaxItterations: this is defined in optimisation_params['Nitterations']. Note that nealder mead will always
            assess the starting simplex first before checking this (mostly a debugging problem)
        """

        if length_scales is not None:
            logger.warning(
                f'You have attempted to use the variable length_scales, but this does nothing'
                f'in the NealderMeadO optimiser - it only works with the Bayesian optimiser. Continuing'
                f' and ignoring this parameter')

        self.Nthreads = Nthreads
        # set up folder structure:
        self.BaseDirectory = BaseDirectory
        if not os.path.isdir(BaseDirectory):
            print(f'{bcolors.FAIL}Input BaseDirectory "{BaseDirectory}" does not exist. Exiting. {bcolors.ENDC}')
            sys.exit()
        self.SimulationName = SimulationName
        SimName = Path(self.BaseDirectory) / self.SimulationName

        self.TargetBeamWidth = TargetBeamWidth
        self.Itteration = 0
        self.MaxItterations = optimisation_params['Nitterations']
        # the starting values of our optimisation parameters are defined from the default geometry
        self.ParameterNames = optimisation_params['ParameterNames']
        self.StartingValues = optimisation_params['start_point']
        self.UpperBounds = optimisation_params['UpperBounds']
        self.LowerBounds = optimisation_params['LowerBounds']
        self.CheckInputData()
        self.CreateVariableDictionary(self.StartingValues)  # puts the above two parameters into a dictionary.
        self.StartingSimplexSupplied = False
        self.StartingSimplexRelativeVal = StartingSimplexRelativeVal
        if self.StartingSimplexRelativeVal:  # nb None evaluates as False
            self.GenerateStartingSimplex()
        self.WallThicknessError = False  # we assume the user inputs a valid set of starting parameters.

        self.debug = debug
        super().__init__()  # get anything we need from base class
        if not os.path.isdir(SimName):
            os.mkdir(SimName)
        self.EmptySimulationFolder()
        self.CopySelf()

    def GenerateStartingSimplex(self):
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

    def setX(self, x_new):
        """
        set's and run's the model with the latest state update
        """

        self.x = np.array(x_new, ndmin=2)
        self.CreateVariableDictionary(self.x)
        self.GenerateTopasModel(self.x)
        if (not self.WallThicknessError):
            '''
            Since this code takes bounds, if the use entered these sensibly, this shouldn't occur...
            '''
            self.RunTopasModel()
            self.ReadTopasResults()
        # Now assess the objective function:
        self.CalculateObjectiveFunction()

        return self.OF

    def RunOptimisation(self):
        """
        Use the scipy.optimize.minimize module to perform the optimisation.
        Note that most of the 'action' is happening in setX, which is repeated called by the optmizer
        """
        if self.StartingSimplexSupplied:
            StartingSimplex = self.StartingSimplex
        else:
            StartingSimplex = None

        bnds = tuple(zip(self.LowerBounds, self.UpperBounds))
        res = minimize(self.setX, self.StartingValues, method='Nelder-Mead', bounds=bnds,
                       options={'xatol': 1e-1, 'fatol': 1e-1, 'disp': True, 'initial_simplex': StartingSimplex,
                                'maxiter': self.MaxItterations, 'maxfev': self.MaxItterations})


class BayesianOptimiser(TopasOptBaseClass):
    """
    Class to perform optimisation using the `Bayesian Optimisation code <https://github.com/fmfn/BayesianOptimization>`_
    This inherits most of its functionality from SphinxOptBaseClass
    """

    def __init__(self, optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory,
                 TargetBeamWidth=7, debug=True, Nthreads=-6,
                 StartingSimplexRelativeVal=None, length_scales=None,
                 UseKappaDecay=False, UseBoundsTransformer=False):
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
        :param UseKappaDecay: if True, can implement kappt to start decaying, and hence the algorithm becoming more
            explotive, after kappa_decay_delay iterations. UCBKappa_final determines the last value of Kappa.
        :type UseKappaDecay: Boolean
        :param UseBoundsTransformer: if True, use bounds transformation as described
            `here <https://github.com/fmfn/BayesianOptimization/blob/master/examples/domain_reduction.ipynb>`_
        :type UseBoundsTransformer: Boolean
        :param OptimisationDirectory: location that TopasObjectiveFunction and GenerateTopasScript are located
        :type OptimisationDirectory: string or Path
        """

        # attempt the absolute imports from the optimisation directory:
        #ToDo:: this should be moved to BaseClass as it is shared functionality
        try:
            import_from_absolute_path(Path(OptimisationDirectory) / 'GenerateTopasScripts.py')
        except ModuleNotFoundError:
            logger.error(f'could not find required file at {str(Path(OptimisationDirectory) / "GenerateTopasScript.py")}.'
                         f'\nQuitting')
            sys.exit(1)
        try:
            import_from_absolute_path(Path(OptimisationDirectory) / 'TopasObjectiveFunction.py')
        except ModuleNotFoundError:
            logger.error(f'could not find required file at {str(Path(OptimisationDirectory) / "TopasObjectiveFunction.py")}.'
                         f'\nQuitting')
            sys.exit(1)
        self.TopasScriptGenerator = GenerateTopasScripts.GenerateTopasScripts
        self.TopasObjectiveFunction = TopasObjectiveFunction.TopasObjectiveFunction

        if StartingSimplexRelativeVal is not None:
            logger.warning(
                f'You have attempted to use the variable StartingSimplexRelativeVal, but this does nothing'
                f'in the Bayesian optimiser - it only works with the Nealder-Mead optimiser. Continuing'
                f' and ignoring this parameter')

        self.__RestartMode = False  # don't change!
        self.Nthreads = Nthreads
        self.name = 'topas_interface'
        self.BaseDirectory = BaseDirectory
        self.OptimisationDirectory = OptimisationDirectory
        if not os.path.isdir(BaseDirectory):
            logger.error(
                f'{bcolors.FAIL}Input BaseDirectory "{BaseDirectory}" does not exist. Exiting. {bcolors.ENDC}')
            sys.exit()
        self.SimulationName = SimulationName
        self.__BayesOptLogLoc = self.BaseDirectory + '/' + self.SimulationName + '/' + 'logs/bayes_opt_logs.json'
        SimName = Path(self.BaseDirectory) / self.SimulationName
        self.TargetBeamWidth = TargetBeamWidth
        self.Itteration = 0
        self.ItterationStart = 0
        # the starting values of our optimisation parameters are defined from the default geometry
        self.ParameterNames = optimisation_params[
            'ParameterNames']
        self.StartingValues = optimisation_params['start_point']
        if self.StartingValues is None:
            logger.error('you must define a start point')
            sys.exit()
        else:
            self.x = self.StartingValues
        self.UpperBounds = optimisation_params['UpperBounds']
        self.LowerBounds = optimisation_params['LowerBounds']
        self.MaxItterations = optimisation_params['Nitterations']
        self.CreateVariableDictionary([self.StartingValues])
        self.CreatePbounds(optimisation_params)  # Bayesian optimiser wants bounds in a slight differnt format
        self.CreateSuggestedPointsToProbe(optimisation_params)
        self.DeriveLengthScales(length_scales)
        self.WallThicknessError = False  # we assume the user inputs a valid set of starting parameters.
        self.target_prediction_mean = []  # keep track of what the optimiser expects to get
        self.target_prediction_std = []  # keep track of what the optimiser expects to get
        self.SuggestionsProbed = 0  # always starts at 0
        self.debug = debug
        # Bayesian optimisation settings:
        self.GP_alpha = .1  # this tells the GPM the expected ammount of noise in the objective function
        # see here: https://github.com/fmfn/BayesianOptimization/issues/202
        self.Matern_Nu = 1.5  # see here https://scikit-learn.org/stable/modules/generated/sklearn.gaussian_process.kernels.Matern.html#sklearn.gaussian_process.kernels.Matern
        self.UCBkappa = 5  # higher kappa = more exploration. lower kappa = more exploitation
        self.n_restarts_optimizer = 20  # this controls the gaussian process fitting. 20 seems to be a good number.
        self.UseKappaDecay = UseKappaDecay
        if self.UseKappaDecay:
            # we use kappa decay such the algorithm becomes more exploritive
            # https://github.com/fmfn/BayesianOptimization/pull/221
            self.UCBKappa_final = 0.1
            self.kappa_decay_delay = 180  # this many exploritive iterations will be carried out before kappa begins to decay
            if self.kappa_decay_delay > self.MaxItterations:
                logger.warning(f'Kappa decay requested, but since kappa_decay_delay ({self.kappa_decay_delay}) is less'
                               f'than MaxItterations ({self.MaxItterations}), decay will never occur...')
            self.kappa_decay = (self.UCBKappa_final/self.UCBkappa) ** (1/(self.MaxItterations - self.kappa_decay_delay))
            # ^^ this is the parameter to ensure we end up with UCBKappa_final on the last iteration
        else:
            self.kappa_decay = 1
            self.kappa_decay_delay = 0
        self.UseBoundsTransformer = UseBoundsTransformer
        if self.UseBoundsTransformer:
            self.BoundsTransformer = SequentialDomainReductionTransformer()
            self.BoundsTransformer_delay = 180
        else:
            self.BoundsTransformer = None

        super().__init__()  # get anything we need from base class
        self.CheckInputData()
        if not os.path.isdir(SimName):
            os.mkdir(SimName)
        # setup the devices name (input controls)
        self.pvs = np.array(optimisation_params['ParameterNames'])
        self.CopySelf()

    def DeriveLengthScales(self, length_scales):
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
            self.length_scales = 1.0
            logger.info(f'{bcolors.OKGREEN}Length scales unset, using defaults{bcolors.ENDC}')
            return
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

    def CreatePbounds(self, optimisation_params):
        """
        Just reformat the optimisation variables into a format that the Bayesian optimiser wants
        """

        pbounds = {}
        for i, ParamName in enumerate(optimisation_params['ParameterNames']):
            pbounds[ParamName] = (optimisation_params['LowerBounds'][i], optimisation_params['UpperBounds'][i])

        self.pbounds = pbounds

    def CreateSuggestedPointsToProbe(self, optimisation_params):
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

    def ConvertDictToVariables(self, x_new):
        """
        I'm trying to keep as much of the underlying code base compatible with multiple methods, so convert the x_new
        the bayes code gives me into what the rest of my code expects

        Note the bayes code sends in the dict in alphabetical order; this methods also corrects that such that the initial
        order of variables is maintained
        """
        x = []
        for i, paramNames in enumerate(x_new):
            x.append(x_new[self.ParameterNames[i]])
        self.x = np.array(x, ndmin=2)

    def BlackBoxFunction(self, x_new):
        """
        Called Black Box function in the spirit of bayesian optimisation, this function simply takes the most recent
        parameter guesses, and solves the model.
        """

        self.ConvertDictToVariables(x_new)
        self.CreateVariableDictionary(self.x)
        self.GenerateTopasModel(self.x)
        if not self.WallThicknessError:
            '''
            Since this code takes bounds, if the use entered these sensibly, this shouldn't occur...
            '''
            self.RunTopasModel()
            self.ReadTopasResults()
        # Now assess the objective function:
        self.CalculateObjectiveFunction()

        return -self.OF

    def PlotResultsRetrospective(self, optimizer):
        """
        This will read in a log file and produce a version of the convergence plot using the input gaussian process
        model to predict the objective function at each itteration.
        This allows a comparison between the prospective and retrospective performance of the GPM. the plot produced
        in real time (SphinxOptBaseClass.PlotResults) will show the performance of the model in 'real time'.
         this will show the performance
        of the final model.

        :param optimizer: The bayesian optimiser object from RunOptimisation
        """
        LogFile = Path(self.BaseDirectory) / self.SimulationName
        LogFile = LogFile / 'logs'
        LogFile = str(LogFile / 'OptimisationLogs.txt')
        ResultsDict = self.ReadInLogFile(LogFile)

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

    def PlotPredictedVersusActualCorrelation(self):
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

    def PlotSingleVariableObjective(self, optimizer):
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
            plt.figure()
            plt.plot(PointsToVary, mean)
            plt.fill_between(PointsToVary, mean + std, mean - std, alpha=0.5, color='C0')
            plt.xlabel(param)
            plt.ylabel('Predicted Objective function value')
            plt.title(f'Single parameter plot for {param}')
            plt.grid()
            SaveName = PlotSavePath + f'/{param}.png'
            plt.savefig(SaveName)

    def RunOptimisation(self):
        """
        This is the main optimisation loop.
        For explanation of the various parameters and commands, start with the
        """
        FullSimName = Path(self.BaseDirectory) / self.SimulationName
        if not os.path.isdir(FullSimName):
            os.mkdir(FullSimName)
        self.EmptySimulationFolder()
        os.mkdir(self.BaseDirectory + '/' + self.SimulationName + '/' + 'logs')
        # instantiate optimizer:

        optimizer = BayesianOptimization(f=None, pbounds=self.pbounds, random_state=1, bounds_transformer=self.BoundsTransformer)
        optimizer.set_gp_params(normalize_y=True, kernel=Matern(length_scale=self.length_scales, nu=self.Matern_Nu),
                                n_restarts_optimizer=self.n_restarts_optimizer, alpha=self.GP_alpha)  # tuning of the gaussian parameters...
        utility = UtilityFunction(kind="ucb", kappa=self.UCBkappa, xi=0.0, kappa_decay_delay=self.kappa_decay_delay,
                                  kappa_decay=self.kappa_decay)
        bayes_opt_logger = JSONLogger(path=self.__BayesOptLogLoc)
        optimizer.subscribe(Events.OPTIMIZATION_STEP, bayes_opt_logger)
        if self.__RestartMode:
            # then load the previous log files:
            logger.warning('setting numpy to ignore underflow errors.')
            np.seterr(under='ignore')
            load_logs(optimizer, logs=[self.__PreviousBayesOptLogLoc])
            Filename = Path(self.BaseDirectory) / Path(self.SimulationName) / 'gah.json'
            Attributes = jsonpickle.encode(optimizer, unpicklable=False, max_depth=5)
            f = open(str(Filename), 'w')
            f.write(Attributes)
            optimizer._gp.fit(optimizer._space.params, optimizer._space.target)
            self.Itteration = len(optimizer.space.target)
            self.ItterationStart = len(optimizer.space.target)
            utility._iters_counter = self.ItterationStart
            if self.Itteration >= self.MaxItterations:
                logger.error(f'nothing to restart; max iterations is {self.MaxItterations} and have already been completed')
                sys.exit(1)
        else:
            # first guess is nonsense but we need the vectors to be the same length
            self.target_prediction_mean.append(0)
            self.target_prediction_std.append(0)
            target = self.BlackBoxFunction(self.VariableDict)
            optimizer.register(self.VariableDict, target=target)

        for point in range(self.Itteration,self.MaxItterations):
            utility.update_params()
            if self.UseBoundsTransformer:
                if point > (self.BoundsTransformer_delay):
                    optimizer.set_bounds(optimizer._bounds_transformer.transform(optimizer._space))
            if (self.Nsuggestions is not None) and (self.SuggestionsProbed < self.Nsuggestions):
                # evaluate any suggested solutions first
                next_point_to_probe = self.Suggestions[self.SuggestionsProbed]
                self.SuggestionsProbed += 1
            else:
                next_point_to_probe = optimizer.suggest(utility)

            NextPointValues = np.array(list(next_point_to_probe.values()))
            mean, std = optimizer._gp.predict(NextPointValues.reshape(1, -1), return_std=True)
            self.target_prediction_mean.append(mean[0])
            self.target_prediction_std.append(std[0])
            target = self.BlackBoxFunction(next_point_to_probe)
            try:
                optimizer.register(params=next_point_to_probe, target=target)
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

            self.PlotPredictedVersusActualCorrelation()
            self.PlotResultsRetrospective(optimizer)
            self.PlotSingleVariableObjective(optimizer)

        # update the logs with the best value:
        best = optimizer.max
        best['target'] = -1 * best['target']  # min/max paradigm...
        LogFile = Path(self.BaseDirectory) / self.SimulationName
        LogFile = LogFile / 'logs'
        LogFile = str(LogFile / 'OptimisationLogs.txt')

        with open(LogFile, 'a') as f:
            Entry = f'\nBest parameter set: {best}'
            f.write(Entry)

    def RestartOptimisation(self):
        """
        Sometimes for whatever reason an optimisation is stopped prematurely.
        This function allows you to restart the optimisation by loading the previous log files.
        You just have to change Optimiser.RunOptimisation() to Optimiser.RestartOptimisation(PreviousSimulationLocation)
        in your optimisation script; the code will do the rest automatically. The restarted siulations will be at
        OriginalSimulationName_restart

        Note this will only work once. If you have to restart a third time, you have to do some copying and pasting
        to make sure there is one previous log file at bayes_opt_logs.json that represents all iterations to date.
        """
        self.__RestartMode = True
        self.SimulationName = self.SimulationName + '_restart'
        self.__PreviousBayesOptLogLoc = self.__BayesOptLogLoc
        self.__BayesOptLogLoc = self.BaseDirectory + '/' + self.SimulationName + '/' + 'logs/bayes_opt_logs2.json'

        self.RunOptimisation()

    def debug_LoadPreviousLogFile(self, LogFileLocation):
        """
        This will load a previously generated .json log file, read the results into a model,
        and return the model. You can then play around with the model and for examples see
        it's predictions at various parameter combos.
        This is useful for debugging only. You need to make sure the optimiser set up matches that
        in RunOptimisation

        Example use::

            import sys,os
            import numpy as np
            sys.path.append('.')
            from TopasSphinxOptimiser import NealderMeadOptimiser, BayesianOptimiser

            # 5 mm beamlets:
            BaseDirectory = "/home/brendan/Dropbox (Sydney Uni)/Projects/PhaserSims/topas/"
            SimulationName = 'temp'
            # set up optimisation params:
            optimisation_params = {}
            optimisation_params['ParameterNames'] = ['coll_UpStreamHoleSize', 'BeamletSizeAtIso', 'coll_CollimatorThickness',
                                                    'CollimatorToIso','VirtSourceToIso', 'coll_TargetOffset','targ_Thicknesses_1','targ_Thicknesses_2',
                                                    'coll_filt_Thickness']
            optimisation_params['start_point'] = np.array([1.7,   2, 257, 500, 1200, 25,  1, 1, 2])
            optimisation_params['UpperBounds'] = np.array([2.5,   4, 300, 600, 1400, 50,  5, 2, 4])
            optimisation_params['LowerBounds'] = np.array([1.5,   1, 100, 400, 1000, 0,    0, 1, 2])
            # optimisation_params['Suggestions'] = np.array([1.99, 1.12, 246.52, 400, 1000, 0,  3.07, 1.72])
            optimisation_params['Nitterations'] = 200
            Optimiser = BayesianOptimiser(optimisation_params, BaseDirectory, SimulationName, debug=False, Nthreads=0, TargetBeamWidth=5, length_scales=0.1)

            LogFileLoc = '/home/brendan/Dropbox (Sydney Uni)/Projects/PhaserSims/topas/Paper_7mm_final/logs/bayes_opt_logs.json'
            bayes_opt_object, utility = Optimiser.debug_LoadPreviousLogFile(LogFileLoc)
            bayes_opt_object._gp.fit(bayes_opt_object._space.params, bayes_opt_object._space.target)

            # next_point_to_probe = bayes_opt_object.suggest(utility)
            # NextPointValues = np.array(list(next_point_to_probe.values()))
            # mean, std = bayes_opt_object._gp.predict(NextPointValues.reshape(1, -1), return_std=True)
        """

        new_optimizer = BayesianOptimization(f=None, pbounds=self.pbounds, random_state=1)
        new_optimizer.set_gp_params(normalize_y=True, kernel=Matern(length_scale=self.length_scales, nu=self.Matern_Nu),
                                n_restarts_optimizer=20, alpha=self.GP_alpha)  # tuning of the gaussian parameters...
        utility = UtilityFunction(kind="ucb", kappa=self.UCBkappa,
                                  xi=0.0)  # kappa determines explore/Exploitation ratio, see here:
        # load logs:
        load_logs(new_optimizer, logs=[LogFileLocation])
        new_optimizer._gp.fit(new_optimizer._space.params, new_optimizer._space.target)
        return new_optimizer, utility

