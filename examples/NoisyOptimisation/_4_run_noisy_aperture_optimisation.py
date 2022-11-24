import numpy as np
from pathlib import Path
from TopasOpt import Optimisers as to
from sklearn.gaussian_process.kernels import Matern, WhiteKernel
import json

BaseDirectory =  '/home/bwhelan/PhaserSims/topas/'

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
# true values are  [1.82, 2.5, 27]
optimisation_params['Nitterations'] = 100
ReadMeText = 'reducing the number of primary particles even further, no noise kernel'

k1 = Matern(length_scale=[3, 0.2, 0.2])
k2 = WhiteKernel()
custom_kernel = k1 + k2
for n_particles in [10e3, 20e3, 30e3, 40e3, 50e3]:
    # write the number of particles to a json file:
    particle_data = {}
    particle_data['n_particles'] = n_particles
    with open('particle_data.json', 'w') as fp:
        json.dump(particle_data, fp)
    # update simulation name:
    SimulationName = f'noisy_opt_n_particles_{int(n_particles)}'
    Optimiser = to.BayesianOptimiser(optimisation_params=optimisation_params, BaseDirectory=BaseDirectory,
                                     SimulationName=SimulationName, OptimisationDirectory=OptimisationDirectory,
                                     TopasLocation='~/topas38', ReadMeText=ReadMeText, Overwrite=True, KeepAllResults=True,
                                     custom_kernel=custom_kernel)
    Optimiser.RunOptimisation()

