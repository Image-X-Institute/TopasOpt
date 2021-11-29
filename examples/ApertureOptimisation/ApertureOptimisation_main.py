import sys
import os
import numpy as np
from pathlib import Path
sys.path.append('../../TopasBayesOpt')
from TopasBayesOpt import TopasBayesOpt as to


BaseDirectory = os.path.expanduser("~") + '/Dropbox (Sydney Uni)/Projects/PhaserSims/topas'
SimulationName = 'BayesianOptimisationTest'
OptimisationDirectory = Path(__file__).parent

# set up optimisation params:
optimisation_params = {}
optimisation_params['ParameterNames'] = ['AppertureSize']
optimisation_params['UpperBounds'] = np.array([10])
optimisation_params['LowerBounds'] = np.array([0.5])
# generate a random starting point between our bounds (it doesn't have to be random, this is just for demonstration purposes)
random_start_point = np.random.default_rng().uniform(optimisation_params['LowerBounds'], optimisation_params['UpperBounds'])[0]
optimisation_params['start_point'] = np.array([random_start_point])
optimisation_params['Nitterations'] = 20
# optimisation_params['Suggestions'] = np.array([[1.1],[1.2]])  # you can suggest points to test if you want
ReadMeText = 'This is a public service announcement, this is only a test'

Optimiser = to.BayesianOptimiser(optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory,
                                 TopasLocation='~/topas37', ReadMeText=ReadMeText, Overwrite=True)
Optimiser.RunOptimisation()