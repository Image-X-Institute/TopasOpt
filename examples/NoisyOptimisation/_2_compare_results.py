from pathlib import Path
from TopasOpt.utilities import get_all_files
import numpy as np
from TopasObjectiveFunction import TopasObjectiveFunction
from matplotlib import pyplot as plt

def plot_objective_function_variability(BoxPlotData):
    
    figure, axs = plt.subplots()
    
    axs.boxplot(BoxPlotData, labels=['n=2e4', 'n=4e4', 'n=5e4'],
                               medianprops={'color': 'k'})
    axs.scatter(np.ones(BoxPlotData.shape[0]), BoxPlotData[:, 0])
    axs.scatter(np.ones(BoxPlotData.shape[0])*2, BoxPlotData[:, 1])
    axs.scatter(np.ones(BoxPlotData.shape[0])*3, BoxPlotData[:, 2])
    axs.set_ylabel('OF')
    axs.set_title('Objective function values')
    axs.grid()

# update this to wherever your data from part 1 is stored:
data_dir = Path(r'/home/brendan/RDS/PRJ-Phaser/PhaserSims/topas/noise_sims')
sims_to_investigate = ['n_particles_20000', 'n_particles_40000',  'n_particles_50000']
of_results = [[], [], []]
j = 0
for sim in sims_to_investigate:
    data_loc = data_dir / sim / 'Results'
    results = get_all_files(data_loc, 'bin')
    iteration = 0

    for result in results:
        objective_value = TopasObjectiveFunction(data_loc, iteration)
        of_results[j].append(objective_value)
        iteration += 1
    j += 1

of_results = np.array(of_results)
of_results = of_results.T
plot_objective_function_variability(of_results)