from pathlib import Path
from TopasOpt.utilities import ReadInLogFile
from matplotlib import pyplot as plt
import numpy as np

BaseDirectory = Path(r'/home/brendan/GoliathHome/PhaserSims/topas')  # directory where the opimization sims are stored
n_particles = [10e3, 20e3, 30e3, 40e3, 50e3]

plt.figure()
for n_particle in n_particles:
    # first, attempt to get the noise estimatation data:
    test_sim_name = f'noisy_opt_n_particles_{int(n_particle)}'
    log_location = BaseDirectory / test_sim_name / 'logs' / 'OptimisationLogs.txt'
    Results = ReadInLogFile(log_location)
    objective_value = Results['ObjectiveFunction']
    LowestVal = np.ones(np.size(objective_value)) * objective_value[0]
    for i, val in enumerate(LowestVal):
        if objective_value[i] < LowestVal[i]:
            LowestVal[i:] = objective_value[i]
    iteration = Results['Itteration']
    plt.plot(iteration, LowestVal)
plt.grid()
plt.xlabel('Iteration')
plt.ylabel('objective')
plt.ylim([1, 6])
n_particles = [int(n_particle) for n_particle in n_particles]  # force integers
plt.legend(n_particles, title='n_particles')
plt.show()