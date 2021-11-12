import sys
import os
import numpy as np
from pathlib import Path
sys.path.append('../../TopasBayesOpt')
from TopasBayesOpt import TopasBayesOpt as tpbo


BaseDirectory = os.path.expanduser("~") + '/Dropbox (Sydney Uni)/Projects/PhaserSims/topas'
SimulationName = 'BayesianOptimisationTest'
OptimisationDirectory = Path(__file__).parent

# set up optimisation params:
optimisation_params = {}
optimisation_params['ParameterNames'] = ['SomeVariable']
optimisation_params['start_point'] = np.array([1])
optimisation_params['UpperBounds'] = np.array([2])
optimisation_params['LowerBounds'] = np.array([0.5])
optimisation_params['Nitterations'] = 5
optimisation_params['Suggestions'] = np.array([[1.1],[1.2]])

Optimiser = tpbo.BayesianOptimiser(optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory)
Optimiser.RunOptimisation()