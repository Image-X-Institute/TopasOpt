# Handling noisy data

In Monte Carlo modelling, we constantly have to trade off how long our simulations run for and how noisy they are. This is particularly important for TopasOpt, where total run time = time_per_sim * n_iterations.

In general, the easiest way to handle noise is to make sure it is low enough that you don't care about it. However, there will certainly be situations where this approach results in unacceptably long run times. Therefore, in this example we will look at working with noisy data using Bayesian Optimization.

This tutorial is split into the following sections:

- generating data with different levels of noise
- modelling noisy data with gaussian process models
- re-running TopasOpt with a custom kernel



## Setup example

As always; start by setting up a new folder that will hold all the codes to run the example. 

This example is based on the same base code as the [geometry example](https://acrf-image-x-institute.github.io/TopasOpt/ApertureOptimisation.html). You should complete that example first. All of the source codes for the steps below can be found [here](https://github.com/ACRF-Image-X-Institute/TopasOpt/tree/master/examples/NoisyOptimisation)

## Generating simulations with different level of noise

In order to assess how statistical noise manifests in our objective function, we can generate N identical simulations, assess the objective function for each one, and quantify the variance. We can use our the `GenerateTopasScripts.py` function we [previously developed](https://acrf-image-x-institute.github.io/TopasOpt/ApertureOptimisation.html) to do this, so copy that one into your example directory. we will make some modifications so that we can also vary the number of primary particles. 

add the following lines inside the GenerateTopasScripts function:

```python
try:
    with open('particle_data.json', 'r') as fp:
        particle_data = json.load(fp)
        n_particles = particle_data['n_particles']
    except FileNotFoundError:
        raise FileNotFoundError('could not locate particle_data.json. Please create    									this file and place e.g. the following in it:'
                                '\n`{"n_particles": 50000}`')
```

This line of code will attempt to read in the number of particles from a file called particle_data.json, which we will create later.

Also change 

```python
#change:
SimpleCollimator.append('ic:So/Beam/NumberOfHistoriesInRun = 5000')
# to
SimpleCollimator.append(f'ic:So/Beam/NumberOfHistoriesInRun = {int(n_particles)}')
```

Next, create a new file called (for instance) `generate_identical_sims.py` and copy the below code into it:

```python
from GenerateTopasScripts import GenerateTopasScripts
import os
from pathlib import Path
from TopasOpt.utilities import generate_run_all_scripts_shell_script
import json


basedirectory = Path(os.path.expanduser('~')) / 'Documents' / 'temp' / 'noise_sims'
if not basedirectory.is_dir():
    basedirectory.mkdir()

n_sims_to_generate = range(10)
n_particles_to_investigate = [10000, 20000, 30000, 40000, 50000]

variable_dict = {'UpStreamApertureRadius': 1.82,
                 'DownStreamApertureRadius': 2.5,
                 'CollimatorThickness': 27}

for n_particles in n_particles_to_investigate:
    particle_data = {}
    particle_data['n_particles'] = n_particles
    with open('particle_data.json', 'w') as fp:
        json.dump(particle_data, fp)  # GenerateTopasScripts will read this
    sim_directory = basedirectory / f'n_particles_{n_particles}'
    if not sim_directory.is_dir():
        sim_directory.mkdir()
    if not (sim_directory / 'Results').is_dir():
        (sim_directory / 'Results').mkdir()
    if not (sim_directory / 'logs').is_dir():
        (sim_directory / 'logs').mkdir()
    if not (sim_directory / 'scripts').is_dir():
        (sim_directory / 'scripts').mkdir()
    sim_num = 0
    variable_dict['n_primaries'] = n_particles
    ScriptsToRun = []
    for n_sim in n_sims_to_generate:
        [SimpleCollimator, WaterTank], [sim1_name, sim2_name] = GenerateTopasScripts('gah', n_sim, **variable_dict)
        sim_num += 1
        sim1 = sim_directory / 'scripts' / (sim1_name + '_' + str(sim_num) + '.tps')
        sim2 = sim_directory / 'scripts' / (sim2_name + '_' + str(sim_num) + '.tps')
        ScriptsToRun.append(sim1)
        ScriptsToRun.append(sim2)
        # write the first simulation
        f = open(sim1, 'w')
        for line in SimpleCollimator:
            f.write(line)
            f.write('\n')
        # write the second simulation
        f = open(sim2, 'w')
        for line in WaterTank:
            f.write(line)
            f.write('\n')
    # once all sims are generated, write a 'RunAllFiles.sh' script:
    generate_run_all_scripts_shell_script((sim_directory / 'scripts'), ScriptsToRun)
```

As the name implies, this script will generate N identical simulations. In addition, we are looping over the n_particles parameter so we can also assess the effect of this on noise.

>  you may have to update the `basedirectory` parameter for your system.

Running this script will generate a series of folders called n_particles_{some_number}. Inside each folder is a directory called scripts, which contains a shell file called `RunAllFiles.sh`. As the name implies, this will run all scripts in the folder. You could also create a bash script to run all of these sequentially, e.g:

```bash
#!/bin/bash
cd n_particles_20000/scripts/
./RunAllFiles.sh
cd ../..
cd n_particles_40000/scripts/
./RunAllFiles.sh
cd ../..
cd n_particles_50000/scripts
./RunAllFiles.sh
cd ../..
cd n_particles_500000/scripts
./RunAllFiles.sh
cd ../..
```

You can go ahead and generate results if you want, but it is somewhat time consuming, so if you want you can just [download the pre-run results](https://cloudstor.aarnet.edu.au/plus/s/7X2fwap7iIvC71O) and continue...

## Assessing noise in the objective function

Now that we have the results (either because you generated them yourself or you downloaded the data) we can assess how the effect the objective function. Create a new script called e.g. `quantify_noise.py` and copy the below into it:

```python
from pathlib import Path
from TopasOpt.utilities import get_all_files
import numpy as np
from TopasObjectiveFunction import TopasObjectiveFunction
from matplotlib import pyplot as plt

def plot_objective_function_variability(BoxPlotData, labels=None):
    
    figure, axs = plt.subplots()

    try:
        axs.boxplot(BoxPlotData, labels=labels,
                                   medianprops={'color': 'k'})
    except:
        print(f'couldnt label boxplots, label length probably didnt match data')
        axs.boxplot(BoxPlotData, medianprops={'color': 'k'})

    for i, data in enumerate(BoxPlotData.T):
        axs.scatter(np.ones(BoxPlotData.shape[0])*i+1, data)
    axs.set_ylabel('OF')
    axs.set_title('Objective function values')
    axs.grid()
    plt.show()

# update this to wherever your data is stored:
data_dir = Path(r'/home/brendan/RDS/PRJ-Phaser/PhaserSims/topas/noise_sims')
sims_to_investigate = ['n_particles_10000',
                       'n_particles_20000',
                       'n_particles_30000',
                       'n_particles_40000',
                       'n_particles_50000']
plot_labels = [sim.split('_')[0] + '_' + sim.split('_')[2] for sim in sims_to_investigate]
of_results = [[] for _ in range(len(sims_to_investigate))]
j = 0
for sim in sims_to_investigate:
    data_loc = data_dir / sim / 'Results'
    results = get_all_files(data_loc, 'bin')
    iteration = 0
    for result in results:
        objective_value = TopasObjectiveFunction(data_loc, iteration)
        of_results[j].append(objective_value)
        iteration += 1
    print(f'mean for {sim}: {np.mean(of_results[j]): 1.10f} ')
    print(f'standard deviation for {sim}: {np.std(of_results[j]): 1.10f} ')
    j += 1

of_results = np.array(of_results)
of_results = of_results.T
plot_objective_function_variability(of_results, labels=plot_labels)
```

This script will attempt to call TopasObjectiveFunction repeatedly, so copy the [TopasObjectiveFunction from the geometry optimisation example](https://github.com/ACRF-Image-X-Institute/TopasOpt/tree/master/examples/ApertureOptimisation) into your working directory. As discussed in the notes for that example, you need to update this function such that it points to wherever your ground truth results are stored:

```python
# change
GroundTruthDataPath = str(Path(__file__).parent / 'SimpleCollimatorExample_TopasFiles' / 'Results')
# to wherever your ground truth results are
```

Remember you can also [download the ground truth results](https://cloudstor.aarnet.edu.au/plus/s/Wm9vndV47u941JU)



Ok, now we can run `quantify_noise.py`, which will produce the following results:


![](../../docsrc/_resources/noise_example/noise_quant.png)



From this, we observe the following two facts:

1. Noise in the objective function decreases with increasing number of particles. This is not surprising!
2. Mean value of the objective function increases as noise increases. This perhaps is more surprising, and goes back to the fact that we are taking absolute differences in the objective function, therefore any noise manifests as an increased value of the objective function.

## Modelling noise using Gaussian Processes

OK; so we know that as we reduce the number of particles, the noise in the objective function increases, as does it's average value. If we can **model** this appropriately, we should still be able to perform decent optimisation even with noisy data. 

Our Bayesian Optimizer uses a [gaussian process model](https://scikit-learn.org/stable/modules/gaussian_process.html) behind the scenes to construct its prior for the objective function. This model can be used to predict both a mean value and a confience interval at all points in the objective space. Increased noise in the objective function can be modelled as decreased confidence (larger confidence interval) in the predictions. 


## Passing the newly constructed kernel to TopasOpt

- change GenerateTopasScripts.py back to n_particles = 20000
- add new parameter to main script where we pass custom kernel

## Comparison with Nelder-Mead

As a comparitor, lets see how Nelder-Mead does on the same problem. Instantiate like this:
