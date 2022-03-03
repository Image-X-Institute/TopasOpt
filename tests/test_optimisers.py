"""
This script basically offers an 'itnegration test' for each optimiser.  For each optimiser, it will

- check that it actually runs
- check that the results are within 10% of a known ground truth
- check the the log file can be read back in

The goal is the public methods of each class are being tested. TopasOpt.Optimisers.TopasOptBaseClass is not explicitly tested,
because it does not allow direct user interaction (will throw an error if anyone tries to use it directly)
"""

import os
import sys
import numpy as np
from pathlib import Path

from TopasOpt import Optimisers as to
from TopasOpt.utilities import ReadInLogFile

# set up file structure (same for all tests)
BaseDirectory =  Path('./temp_test').resolve()
if not os.path.isdir(BaseDirectory):
    os.mkdir(BaseDirectory)  # delete this at the end!!
SimulationName = 'development_test'
OptimisationDirectory = Path(__file__).parent

# set up
optimisation_params = {}
optimisation_params['ParameterNames'] = ['x', 'y']
optimisation_params['UpperBounds'] = np.array([1, 1])
optimisation_params['LowerBounds'] = np.array([-1, -1])
optimisation_params['start_point'] = np.array([0, 0])
optimisation_params['Nitterations'] = 100
# optimisation_params['Suggestions'] # you can suggest points to test if you want - we won't here.
ReadMeText = 'This directory only exists for testing; it can be deleted'

def test_Nelder_Mead():
    ## Test Nelder Mead:
    Optimiser = to.NelderMeadOptimiser(optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory,
                                    TopasLocation='testing_mode', ReadMeText=ReadMeText, Overwrite=True,
                                    KeepAllResults=False)
    Optimiser.RunOptimisation()
    best_solution_number = np.argmin(Optimiser.AllObjectiveFunctionValues)
    # read in the log file:
    ResultsDict = ReadInLogFile(BaseDirectory / SimulationName / 'logs' / 'OptimisationLogs.txt')
    OF = ResultsDict['ObjectiveFunction']
    best_x = ResultsDict['x'][best_solution_number]
    best_y = ResultsDict['y'][best_solution_number]
    assert 0.9 <= best_x <= 1.1  # test answer within plus/minus 10% of truth
    assert 0.9 <= best_y <= 1.1  # test answer within plus/minus 10% of truth

def test_Bayesian():
    ## Test Bayesian
    Optimiser = to.BayesianOptimiser(optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory,
                                    TopasLocation='testing_mode', ReadMeText=ReadMeText, Overwrite=True,
                                    KeepAllResults=False)
    Optimiser.RunOptimisation()
    best_solution_number = np.argmin(Optimiser.AllObjectiveFunctionValues)
    # read in the log file:
    ResultsDict = ReadInLogFile(BaseDirectory / SimulationName / 'logs' / 'OptimisationLogs.txt')
    best_x = ResultsDict['x'][best_solution_number]
    best_y = ResultsDict['y'][best_solution_number]
    assert 0.9 <= best_x <= 1.1  # test answer within plus/minus 10% of truth
    assert 0.9 <= best_y <= 1.1  # test answer within plus/minus 10% of truth
