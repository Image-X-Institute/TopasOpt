import sys
import os
import numpy as np
from pathlib import Path
sys.path.append('/mrlSSDfixed/Brendan/Dropbox (Sydney Uni)/Projects/TopasBayesOpt/TopasBayesOpt')
import TopasBayesOpt as to
# sys.path.append('../../TopasBayesOpt')
# from TopasBayesOpt import TopasBayesOpt as to

BaseDirectory = os.path.expanduser("~") + '/Dropbox (Sydney Uni)/Projects/PhaserSims/topas'
SimulationName = 'PhaseSpaceOptimisationTest'
OptimisationDirectory = Path(__file__).parent

# set up optimisation params:
optimisation_params = {}
optimisation_params['ParameterNames'] = ['BeamEnergy', 'BeamPositionCutoff', 'BeamPositionSpread', 'BeamAngularSpread',
                                         'BeamAngularCutoff']
optimisation_params['UpperBounds'] = np.array([12, 3, 0.5, 0.15, 10])
optimisation_params['LowerBounds'] = np.array([8,  1, 0.1, .01, 1])
# generate a random starting point between our bounds (it doesn't have to be random, this is just for demonstration purposes)
random_start_point = np.random.default_rng().uniform(optimisation_params['LowerBounds'], optimisation_params['UpperBounds'])
optimisation_params['start_point'] = random_start_point
optimisation_params['Nitterations'] = 100
# optimisation_params['Suggestions'] # you can suggest points to test if you want - we won't here.
ReadMeText = 'This is a public service announcement, this is only a test'

Optimiser = to.BayesianOptimiser(optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory,
                                 TopasLocation='~/topas37', ReadMeText=ReadMeText, Overwrite=True, length_scales=0.1)
Optimiser.RunOptimisation()
