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

this_dir = Path(__file__).parent
sys.path.insert(0, str(this_dir.parent))
from TopasOpt import Optimisers as to
from TopasOpt.utilities import ReadInLogFile

# set up file structure (same for all tests)
BaseDirectory = Path('./temp_test').resolve()
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
    Optimiser = to.NelderMeadOptimiser(optimisation_params=optimisation_params, BaseDirectory=BaseDirectory,
                                       SimulationName=SimulationName, OptimisationDirectory=OptimisationDirectory,
                                       TopasLocation='testing_mode', ReadMeText=ReadMeText, Overwrite=True,
                                       KeepAllResults=False, NM_StartingSimplex=.1)
    Optimiser.RunOptimisation()
    # read in the log file:
    ResultsDict = ReadInLogFile(BaseDirectory / SimulationName / 'logs' / 'OptimisationLogs.txt')
    best_solution_number = np.argmin(ResultsDict['ObjectiveFunction'])
    best_x = ResultsDict['x'][best_solution_number]
    best_y = ResultsDict['y'][best_solution_number]
    assert 0.9 <= best_x <= 1.1  # test answer within plus/minus 10% of truth
    assert 0.9 <= best_y <= 1.1  # test answer within plus/minus 10% of truth


def test_Nelder_Mead_UserDefinedSimplex():
    ## Test Nelder Mead:
    starting_sim = [[0.9, 0.9], [0.72, 0.9], [0.9, 0.72]]
    Optimiser = to.NelderMeadOptimiser(optimisation_params=optimisation_params, BaseDirectory=BaseDirectory,
                                       SimulationName=SimulationName, OptimisationDirectory=OptimisationDirectory,
                                       TopasLocation='testing_mode', ReadMeText=ReadMeText, Overwrite=True,
                                       KeepAllResults=False, NM_StartingSimplex=starting_sim)
    Optimiser.RunOptimisation()
    # read in the log file:
    ResultsDict = ReadInLogFile(BaseDirectory / SimulationName / 'logs' / 'OptimisationLogs.txt')
    best_solution_number = np.argmin(ResultsDict['ObjectiveFunction'])
    best_x = ResultsDict['x'][best_solution_number]
    best_y = ResultsDict['y'][best_solution_number]
    assert 0.9 <= best_x <= 1.1  # test answer within plus/minus 10% of truth
    assert 0.9 <= best_y <= 1.1  # test answer within plus/minus 10% of truth


def test_Bayesian():
    ## Test Bayesian
    optimisation_params['Nitterations'] = 50
    optimisation_params['Suggestions'] = np.array([0.7, 0.7])

    Optimiser = to.BayesianOptimiser(optimisation_params=optimisation_params, BaseDirectory=BaseDirectory,
                                     SimulationName=SimulationName, OptimisationDirectory=OptimisationDirectory,
                                     TopasLocation='testing_mode', ReadMeText=ReadMeText, Overwrite=True,
                                     KeepAllResults=False, bayes_length_scales=.2, bayes_KappaDecayIterations=12,
                                     bayes_UCBkappa=6)
    Optimiser.RunOptimisation()
    # read in the log file:
    ResultsDict = ReadInLogFile(BaseDirectory / SimulationName / 'logs' / 'OptimisationLogs.txt')
    best_solution_number = np.argmin(ResultsDict['ObjectiveFunction'])
    best_x = ResultsDict['x'][best_solution_number]
    best_y = ResultsDict['y'][best_solution_number]
    assert 0.9 <= best_x <= 1.1  # test answer within plus/minus 10% of truth
    assert 0.9 <= best_y <= 1.1  # test answer within plus/minus 10% of truth


def test_BayesianRestart():
    optimisation_params['Nitterations'] = optimisation_params['Nitterations'] + 10
    ## Test Bayesian
    Optimiser = to.BayesianOptimiser(optimisation_params=optimisation_params, BaseDirectory=BaseDirectory,
                                     SimulationName=SimulationName, OptimisationDirectory=OptimisationDirectory,
                                     TopasLocation='testing_mode', ReadMeText=ReadMeText, Overwrite=True,
                                     KeepAllResults=False, bayes_length_scales=0.1)
    Optimiser.RestartOptimisation()
    # read in the log file:
    ResultsDict = ReadInLogFile(BaseDirectory / SimulationName / 'logs' / 'OptimisationLogs.txt')
    best_solution_number = np.argmin(ResultsDict['ObjectiveFunction'])
    best_x = ResultsDict['x'][best_solution_number]
    best_y = ResultsDict['y'][best_solution_number]
    assert 0.9 <= best_x <= 1.1  # test answer within plus/minus 10% of truth
    assert 0.9 <= best_y <= 1.1  # test answer within plus/minus 10% of truth


def test_passing_wrong_parameters():
    """
    in this test I want to see what happens when I pass an optimiser parameters it should not be receiving, e.g.
    I pass bayesian specific parameters to the nelder-mead optimiser.
    """
    try:  # Bayesian
        to.BayesianOptimiser(optimisation_params=optimisation_params, BaseDirectory=BaseDirectory,
                             SimulationName=SimulationName, OptimisationDirectory=OptimisationDirectory,
                             TopasLocation='testing_mode', ReadMeText=ReadMeText, Overwrite=True,
                             KeepAllResults=False, bayes_length_scales=.2, bayes_KappaDecayIterations=12,
                             NM_StartingSimplex=0.2)
        assert False  # arriving here counts as failure
    except TypeError:
        # this is exactly what should happen because BayesianOptimiser got passed the wrong parameter
        pass

    try:  # Nelder-Mead
        to.NelderMeadOptimiser(optimisation_params=optimisation_params, BaseDirectory=BaseDirectory,
                               SimulationName=SimulationName, OptimisationDirectory=OptimisationDirectory,
                               TopasLocation='testing_mode', ReadMeText=ReadMeText, Overwrite=True,
                               KeepAllResults=False, bayes_KappaDecayIterations=.1)
        assert False
    except TypeError:
        # this is exactly what should happen
        pass
