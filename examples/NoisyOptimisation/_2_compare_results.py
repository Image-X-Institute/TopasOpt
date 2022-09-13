from pathlib import Path
from TopasOpt.utilities import get_all_files
import numpy as np
from TopasObjectiveFunction import TopasObjectiveFunction
from matplotlib import pyplot as plt

def plot_objective_function_variability(BoxPlotData):
    
    figure, axs = plt.subplots()

    try:
        axs.boxplot(BoxPlotData, labels=['n=2e4', 'n=4e4', 'n=5e4', 'n=5e5'],
                                   medianprops={'color': 'k'})
    except ValueError:
        print(f'couldnt label boxplots, label length didnt match data')
        axs.boxplot(BoxPlotData, medianprops={'color': 'k'})

    for i, data in enumerate(BoxPlotData.T):
        axs.scatter(np.ones(BoxPlotData.shape[0])*i+1, data)
    axs.set_ylabel('OF')
    axs.set_title('Objective function values')
    axs.grid()
    plt.show()

# update this to wherever your data from part 1 is stored:
data_dir = Path(r'/home/brendan/Documents/temp/noise_sims')
sims_to_investigate = ['n_particles_20000', 'n_particles_40000',  'n_particles_50000', 'n_particles_500000']
of_results = [[], [], [], []]
j = 0
for sim in sims_to_investigate:
    data_loc = data_dir / sim / 'Results'
    results = get_all_files(data_loc, 'bin')
    iteration = 0

    for result in results:
        objective_value = TopasObjectiveFunction(data_loc, iteration, take_abs=True)
        # note we added a new parameter so we aren't automatically taking absolute values
        of_results[j].append(objective_value)
        iteration += 1
    print(f'mean for {sim}: {np.mean(of_results[j]): 1.10f} ')
    print(f'standard deviation for {sim}: {np.std(of_results[j]): 1.10f} ')
    j += 1

of_results = np.array(of_results)
of_results = of_results.T
plot_objective_function_variability(of_results)