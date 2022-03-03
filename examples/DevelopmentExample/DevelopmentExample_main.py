import sys
import numpy as np
from pathlib import Path
from TopasOpt import Optimisers as to

BaseDirectory =  '/home/brendan/Documents/temp'
SimulationName = 'development_test'
OptimisationDirectory = Path(__file__).parent


# set up optimisation params for rosen function:
optimisation_params = {}
optimisation_params['ParameterNames'] = ['x', 'y']
optimisation_params['UpperBounds'] = np.array([1, 1])
optimisation_params['LowerBounds'] = np.array([-1, -1])
optimisation_params['start_point'] = np.array([0, 0])
# Remember true values are  [1.82, 2.5, 27]
optimisation_params['Nitterations'] = 100
# optimisation_params['Suggestions'] # you can suggest points to test if you want - we won't here.
ReadMeText = 'This is an example in which the rosen function is minimised, and demonstrates how this library' \
             'can be tested without actually calling topas'

# Optimiser = to.BayesianOptimiser(optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory,
#                                  TopasLocation='~/topas37', ReadMeText=ReadMeText, Overwrite=True, length_scales=0.1)

# Optimiser = to.NealderMeadOptimiser(optimisation_params, BaseDirectory, 'NM_OptimisationTest', OptimisationDirectory,
#                                   TopasLocation='~/topas37', ReadMeText=ReadMeText, Overwrite=True, StartingSimplexRelativeVal=.4)

Optimiser = to.NelderMeadOptimiser(optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory,
                                TopasLocation='testing_mode', ReadMeText=ReadMeText, Overwrite=True, KeepAllResults=False)
Optimiser.RunOptimisation()
