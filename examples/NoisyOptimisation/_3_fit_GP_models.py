import numpy as np
from pathlib import Path
from TopasObjectiveFunction import TopasObjectiveFunction
from TopasOpt.utilities import get_all_files
from bayes_opt import BayesianOptimization
from bayes_opt import UtilityFunction
from noise_box_plots import plot_gp_model_versus_data
from sklearn.gaussian_process.kernels import Matern, WhiteKernel

data_dir = Path(r'/home/brendan/Downloads/noise_sims') # where is the previously generated (or downloaded) data
OptimisationDirectory = Path(__file__).parent  # dont change

# set up optimisation params (this is necessary to instantiate the optimizer, we don't actually use them):
optimisation_params = {}
optimisation_params['ParameterNames'] = ['UpStreamApertureRadius', 'DownStreamApertureRadius', 'CollimatorThickness']
optimisation_params['UpperBounds'] = np.array([3, 3, 40])
optimisation_params['LowerBounds'] = np.array([1, 1, 10])
optimisation_params['start_point'] = np.array([1.14, 1.73, 39.9])
optimisation_params['Nitterations'] = 40
k1 = Matern(length_scale=[3, 0.2, 0.2])
k2 = WhiteKernel()
custom_kernel = k1
target_predictions = []
std_predictions = []

# generate pbounds
pbounds = {}
parameter_values = {}
for i, ParamName in enumerate(optimisation_params['ParameterNames']):
    pbounds[ParamName] = (optimisation_params['LowerBounds'][i], optimisation_params['UpperBounds'][i])
    parameter_values[ParamName] = optimisation_params['start_point'][i]


sims_to_investigate = ['n_particles_10000', 'n_particles_20000', 'n_particles_30000', 'n_particles_40000', 'n_particles_50000']
of_results = [[] for _ in range(len(sims_to_investigate))]
j = 0
for sim in sims_to_investigate:
    data_loc = data_dir / sim / 'Results'
    results = get_all_files(data_loc, 'bin')
    iteration = 0
    utility = UtilityFunction(kind="ucb", kappa=2.5, xi=0.0)
    optimizer = BayesianOptimization(f=None,pbounds=pbounds,  verbose=2, random_state=1)
    optimizer.set_gp_params(kernel=custom_kernel)
    for result in results:
        objective_value = TopasObjectiveFunction(data_loc, iteration, take_abs=True)
        # note we added a new parameter so we aren't automatically taking absolute values
        of_results[j].append(objective_value)
        iteration += 1
        optimizer.register(params=parameter_values, target=objective_value)
    # because we are running this in a pretty weird way we have to manually fit the model:
    optimizer._gp.fit(optimizer._space.params, optimizer._space.target)
    # predict objective at this values
    optimal_params = dict(sorted(parameter_values.items()))  # make sure they are in alphabetical order
    param_array = np.fromiter(optimal_params.values(), dtype=float)
    predicted_target, predicted_std = optimizer._gp.predict(param_array.reshape(1, -1), return_std=True)
    target_predictions.append(-1*predicted_target)
    std_predictions.append(predicted_std)
    j = j+1
    del optimizer

of_results = np.array(of_results)
of_results = of_results.T
plot_gp_model_versus_data(of_results,  np.array(target_predictions).squeeze(), np.array(std_predictions).squeeze())
