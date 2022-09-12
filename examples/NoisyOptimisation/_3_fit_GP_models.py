import numpy as np
from pathlib import Path
from TopasObjectiveFunction import TopasObjectiveFunction
from TopasOpt.utilities import get_all_files
from bayes_opt import BayesianOptimization
from bayes_opt import UtilityFunction
from matplotlib import pyplot as plt

def plot_retrospective_fit(of_results, optimizer, title=None):
    """
    plot a list of results versus GP fit
    """
    # generate array of (identical) points to predict:
    sorted_values = {key: value for key, value in sorted(parameter_values.items())}
    # note bayesian optimisation code sorts alphabetically for some reason
    point = [list(sorted_values.values())]
    point_array = np.repeat(point, of_results.__len__(), axis=0)
    # generate the optimizer predictions:
    target_prediction, target_prediction_std = optimizer._gp.predict(point_array, return_std=True)

    # plot the results
    run_number = np.linspace(0, of_results.__len__() - 1, of_results.__len__())

    fig, axs = plt.subplots(nrows=1, ncols=1, figsize=(10, 5))
    axs.plot(run_number, of_results, 'C6')
    axs.plot(run_number, target_prediction, 'C0')
    axs.fill_between(run_number,
                     target_prediction + target_prediction_std,
                     target_prediction - target_prediction_std, alpha=0.15, color='C0')

    axs.legend(['Actual', 'Predicted', r'$\sigma$'])
    axs.set_xlabel('Run number')
    axs.set_ylabel('Objective function')
    axs.grid(True)
    if title:
        axs.set_title(title)

BaseDirectory = '/home/brendan/Documents/temp'
SimulationName = 'NMtest'
OptimisationDirectory = Path(__file__).parent

# set up optimisation params:
optimisation_params = {}
optimisation_params['ParameterNames'] = ['UpStreamApertureRadius', 'DownStreamApertureRadius', 'CollimatorThickness']
optimisation_params['UpperBounds'] = np.array([3, 3, 40])
optimisation_params['LowerBounds'] = np.array([1, 1, 10])
# generate a random starting point between our bounds (it doesn't have to be random, this is just for demonstration purposes)
# random_start_point = np.random.default_rng().uniform(optimisation_params['LowerBounds'], optimisation_params['UpperBounds'])
# optimisation_params['start_point'] = random_start_point
optimisation_params['start_point'] = np.array([1.14, 1.73, 39.9])
# Remember true values are  [1.82, 2.5, 27]
optimisation_params['Nitterations'] = 40
# optimisation_params['Suggestions'] # you can suggest points to test if you want - we won't here.
ReadMeText = 'This is a public service announcement, this is only a test'

# generate pbounds
pbounds = {}
for i, ParamName in enumerate(optimisation_params['ParameterNames']):
    pbounds[ParamName] = (optimisation_params['LowerBounds'][i], optimisation_params['UpperBounds'][i])

data_dir = Path(r'X:\PRJ-Phaser\PhaserSims\topas\noise_sims')
sims_to_investigate = ['n_particles_20000', 'n_particles_40000',  'n_particles_50000', 'n_particles_500000']
of_results = [[], [], [], []]
j = 0
for sim in sims_to_investigate:
    data_loc = data_dir / sim / 'Results'
    results = get_all_files(data_loc, 'bin')
    iteration = 0
    utility = UtilityFunction(kind="ucb", kappa=2.5, xi=0.0)
    optimizer = BayesianOptimization(
        f=None,
        pbounds=pbounds,
        verbose=2,
        random_state=1,
    )

    parameter_values = {'UpStreamApertureRadius': 1.82,
                     'DownStreamApertureRadius': 2.5,
                     'CollimatorThickness': 27}

    for result in results:
        objective_value = TopasObjectiveFunction(data_loc, iteration, take_abs=True)
        next_point = optimizer.suggest(utility)
        optimizer.register(params=parameter_values, target=objective_value)
        # note we added a new parameter so we aren't automatically taking absolute values
        of_results[j].append(objective_value)
        iteration += 1
    plot_retrospective_fit(of_results[j], optimizer,title=sim)









