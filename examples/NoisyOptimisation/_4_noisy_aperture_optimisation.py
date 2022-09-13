import numpy as np
from pathlib import Path
from TopasOpt import Optimisers as to
from sklearn.gaussian_process.kernels import Matern, WhiteKernel

BaseDirectory =  '/home/brendan/Documents/temp'
SimulationName = 'NMtest'
OptimisationDirectory = Path(__file__).parent


# set up optimisation params:
optimisation_params = {}
optimisation_params['ParameterNames'] = ['UpStreamApertureRadius','DownStreamApertureRadius', 'CollimatorThickness']
optimisation_params['UpperBounds'] = np.array([3, 3, 40])
optimisation_params['LowerBounds'] = np.array([1, 1, 10])
# generate a random starting point between our bounds (it doesn't have to be random, this is just for demonstration purposes)
# random_start_point = np.random.default_rng().uniform(optimisation_params['LowerBounds'], optimisation_params['UpperBounds'])
# optimisation_params['start_point'] = random_start_point
optimisation_params['start_point'] = np.array([1.14, 1.73, 39.9])
# Remember true values are  [1.82, 2.5, 27]
optimisation_params['Nitterations'] = 100
# optimisation_params['Suggestions'] # you can suggest points to test if you want - we won't here.
ReadMeText = 'This is a public service announcement, this is only a test'

k1 = Matern(length_scale=[3, 0.2, 0.2])
k2 = WhiteKernel(noise_level=0.25, noise_level_bounds='fixed')
custom_kernel = k1 + k2


Optimiser = to.BayesianOptimiser(optimisation_params=optimisation_params, BaseDirectory=BaseDirectory,
                                 SimulationName='GeometryOptimisationTest_NM', OptimisationDirectory=OptimisationDirectory,
                                 TopasLocation='~/topas38', ReadMeText=ReadMeText, Overwrite=True, KeepAllResults=True,
                                 custom_kernel=custom_kernel)

Optimiser.RunOptimisation()
