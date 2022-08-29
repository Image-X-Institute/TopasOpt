import sys
import os
import numpy as np
from pathlib import Path
sys.path.append('../../../TopasOpt')
from TopasOpt import Optimisers as to

BaseDirectory = os.path.expanduser("~") + '/PhaserSims/topas/'
SimulationName = 'electron_beam_test'
OptimisationDirectory = Path(__file__).parent  # this points to whatever directory this file is in, don't change it.

# set up optimisation params:
optimisation_params = {}
optimisation_params['ParameterNames'] = ['BeamEnergy', 'BeamEnergySpread', 'BeamPositionCutoffX','BeamPositionCutoffY', 'BeamPositionSpreadX',
                                            'BeamPositionSpreadY', 'BeamAngularSpreadX', 'BeamAngularSpreadY',  'BeamAngularCutoffX', 'BeamAngularCutoffY']
optimisation_params['UpperBounds'] = np.array([18, 30, 3, 3,   1,   1,     1,    1, 10, 10])
optimisation_params['LowerBounds'] = np.array([14, 0,  1, 1, 0.1, 0.1,  0.01, 0.01, 1,  1 ])
# generate a random starting point between our bounds (it doesn't have to be random, this is just for demonstration purposes)
random_start_point = np.random.default_rng().uniform(optimisation_params['LowerBounds'], optimisation_params['UpperBounds'])
optimisation_params['start_point'] = random_start_point
# using previously randomly generated start point for reproducability 
optimisation_params['start_point'] = [14, 12.9,  2.1,  1.6,  0.2, 0.18,  0.39 ,  0.62,  3.5,  3.8]

optimisation_params['Nitterations'] = 200
# optimisation_params['Suggestions'] # you can suggest points to test if you want - we won't here.
ReadMeText = 'This is a public service announcement, this is only a test'

Optimiser = to.BayesianOptimiser(optimisation_params=optimisation_params, BaseDirectory=BaseDirectory,
                                 SimulationName=SimulationName, OptimisationDirectory=OptimisationDirectory,
                                  TopasLocation='~/topas38', ReadMeText=ReadMeText, Overwrite=True, bayes_length_scales=0.1)


# Optimiser = to.NelderMeadOptimiser(optimisation_params=optimisation_params, BaseDirectory=BaseDirectory,
#                                    SimulationName='PhaseSpaceOptimisationTest_NM', OptimisationDirectory=OptimisationDirectory,
#                                    TopasLocation='~/topas37', ReadMeText=ReadMeText, Overwrite=True, NM_StartingSimplex=.2)

Optimiser.RunOptimisation()
