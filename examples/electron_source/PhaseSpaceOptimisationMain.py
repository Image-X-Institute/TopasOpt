import sys
import os
import numpy as np
from pathlib import Path
sys.path.append('../../../TopasOpt')
from TopasOpt import Optimisers as to

BaseDirectory = os.path.expanduser("~") + '/Dropbox (Sydney Uni)/Projects/PhaserSims/topas'
SimulationName = 'PhaseSpaceOptimisationTest_NM'
OptimisationDirectory = Path(__file__).parent  # this points to whatever directory this file is in, don't change it.

# set up optimisation params:
optimisation_params = {}
optimisation_params['ParameterNames'] = ['BeamEnergy', 'BeamEnergySpread', 'BeamPositionCutoff', 'BeamPositionSpread', 'BeamAngularSpread',
                                         'BeamAngularCutoff']
optimisation_params['UpperBounds'] = np.array([18, 30, 3, 1, 1, 10])
optimisation_params['LowerBounds'] = np.array([14, 0, 1, 0.1, .01, 1])
# generate a random starting point between our bounds (it doesn't have to be random, this is just for demonstration purposes)
random_start_point = np.random.default_rng().uniform(optimisation_params['LowerBounds'], optimisation_params['UpperBounds'])
optimisation_params['start_point'] = random_start_point
optimisation_params['start_point'] = np.array([16, 15, 2.71, 0.98, 0.1, 2.7])  # keeping original random values for reproducability
optimisation_params['Nitterations'] = 100
# optimisation_params['Suggestions'] # you can suggest points to test if you want - we won't here.
ReadMeText = 'This is a public service announcement, this is only a test'

Optimiser = to.BayesianOptimiser(optimisation_params=optimisation_params, BaseDirectory=BaseDirectory,
                                 SimulationName='PhaseSpaceOptimisationTest', OptimisationDirectory=OptimisationDirectory,
                                  TopasLocation='~/topas37', ReadMeText=ReadMeText, Overwrite=True, bayes_length_scales=0.1)


# Optimiser = to.NelderMeadOptimiser(optimisation_params=optimisation_params, BaseDirectory=BaseDirectory,
#                                    SimulationName='PhaseSpaceOptimisationTest_NM', OptimisationDirectory=OptimisationDirectory,
#                                    TopasLocation='~/topas37', ReadMeText=ReadMeText, Overwrite=True, NM_StartingSimplex=.2)

Optimiser.RunOptimisation()
