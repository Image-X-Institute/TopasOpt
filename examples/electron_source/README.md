# Electron source optimization

this is a simulation of an electron beam hitting two scattering foils:

![](../../docsrc/_resources/electron_source/Diagram.png)

Note that in this example, we are not making any assumptions that the input beam is symmetric, meaning we are optimizing 10 independent parameters.  

## Environment set up

We assume that you have already set up an appropriate environment to run TopasOpt as described in example 1.

## Directory set up

Since we are now running a new optimisation, you have to create a new base directory (you will repeat these basic steps every time you have  an optimisation problem). So, create a new directory called e.g.  electron_source_optimisation.

## Generate sample data

from inside your base directory, download the topas file for this example:

```bash
wget https://raw.githubusercontent.com/ACRF-Image-X-Institute/TopasOpt/ebeam_example/examples/electron_source/electron_beam.tps
```

Following this you will have  a topas script called electron_beam.tps. Run it to generate the starting data:

```bash
~/topas/bin/topas electron_beam.tps
```

This will take a few minutes to run on a high end PC.

## Creating GenerateTopasScript.py

As previously: create a file called e.g. 'temp_make_topas_script_generator.py'. Copy the below code into it and run:

```python
import sys
from TopasOpt.TopasScriptGenerator import generate_topas_script_generator
from pathlib import Path

this_directory = Path(__file__).parent

# nb: the order is important to make sure that a phase space files are correctly classified
generate_topas_script_generator(this_directory, ['electron_beam.tps'])
```

## creating electron_source_main.py

create a file called electron_source_main.py and copy the below into it.

Note that we are optimising 10 independent parameters because we are not assuming the beam is symmetric (and indeed, if you look inside electron_beam.tps, it is not!)

> make sure you point `BaseDirectory` to a location that exists!

```python
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
Optimiser.RunOptimisation()
```

## Editing GenerateTopasScripts.py

We have to update `GenerateTopasScripts.py` so that the parameters we are changing actually get changed in the topas model!!

```bash
# change
SimpleBeam.append('dc:So/Beam/BeamEnergy               = 15.0 MeV')
#to
SimpleBeam.append(f'dc:So/Beam/BeamEnergy               = {variable_dict["BeamEnergy"]} MeV')
# change
SimpleBeam.append('uc:So/Beam/BeamEnergySpread         = 10')
#to
SimpleBeam.append(f'uc:So/Beam/BeamEnergySpread         = {variable_dict["BeamEnergySpread"]}')
SimpleBeam.append('sc:So/Beam/BeamPositionDistribution = "Gaussian" ')
SimpleBeam.append('sc:So/Beam/BeamAngularDistribution  = "Gaussian" ')
SimpleBeam.append('sc:So/Beam/BeamPositionCutoffShape = "Ellipse"')
# change
SimpleBeam.append('dc:So/Beam/BeamPositionCutoffX = 2 mm')
#to
SimpleBeam.append(f'dc:So/Beam/BeamPositionCutoffX = {variable_dict["BeamPositionCutoffX"]} mm')
# change
SimpleBeam.append('dc:So/Beam/BeamPositionCutoffY = 2 mm')
#to
SimpleBeam.append(f'dc:So/Beam/BeamPositionCutoffY = {variable_dict["BeamPositionCutoffY"]} mm')
# change
SimpleBeam.append('dc:So/Beam/BeamPositionSpreadX = 0.3 mm')
#to
SimpleBeam.append(f'dc:So/Beam/BeamPositionSpreadX = {variable_dict["BeamPositionSpreadX"]} mm')
# change
SimpleBeam.append('dc:So/Beam/BeamPositionSpreadY = 0.3 mm')
#to
SimpleBeam.append(f'dc:So/Beam/BeamPositionSpreadY = {variable_dict["BeamPositionSpreadY"]} mm')
# change
SimpleBeam.append('dc:So/Beam/BeamAngularCutoffX = 5 deg')
#to
SimpleBeam.append(f'dc:So/Beam/BeamAngularCutoffX = {variable_dict["BeamAngularCutoffX"]} deg')
# change
SimpleBeam.append('dc:So/Beam/BeamAngularCutoffY = 5 deg')
#to
SimpleBeam.append(f'dc:So/Beam/BeamAngularCutoffY = {variable_dict["BeamAngularCutoffY"]} deg')
# change
SimpleBeam.append('dc:So/Beam/BeamAngularSpreadX = 0.07 deg')
#to
SimpleBeam.append(f'dc:So/Beam/BeamAngularSpreadX = {variable_dict["BeamAngularSpreadX"]} deg')
# change
SimpleBeam.append('dc:So/Beam/BeamAngularSpreadY = 0.07 deg')
#to
SimpleBeam.append(f'dc:So/Beam/BeamAngularSpreadY = {variable_dict["BeamAngularSpreadY"]} deg')
```

## Create TopasObjectiveFunction.py

Create a file called TopasObjectiveFunction.py and copy the below into it.

We are using an almost identical objective function as in the [bremstrahlung source optimization](https://acrf-image-x-institute.github.io/TopasOpt/PhaseSpaceOptimisation.html), except that we take a profile at a shallower depth in water. This is simply because electrons have a more rapid fall off in dose than photons, so better SNR is obtained with a shallower profile.  

```python
import os
from TopasOpt.utilities import WaterTankData
import numpy as np
from pathlib import Path

def CalculateObjectiveFunction(TopasResults, GroundTruthResults):
    """
    In this example, for metrics I am going to calculate the RMS error between the desired and actual
    profile and PDD. I will use normalised values to account for the fact that there may be different numbers of
    particles used between the different simulations
    """

    # define the points we want to collect our profile at:
    Xpts = np.linspace(GroundTruthResults.x.min(), GroundTruthResults.x.max(), 100)  # profile over entire X range
    Ypts = np.zeros(Xpts.shape)
    Zpts = 25 * np.ones(Xpts.shape)  # at the middle of the water tank

    OriginalProfile = GroundTruthResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    OriginalProfileNorm = OriginalProfile * 100 / OriginalProfile.max()
    CurrentProfile = TopasResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    CurrentProfileNorm = CurrentProfile * 100 / CurrentProfile.max()
    ProfileDifference = OriginalProfileNorm - CurrentProfileNorm

    # define the points we want to collect our DD at:
    Zpts = GroundTruthResults.z
    Xpts = np.zeros(Zpts.shape)
    Ypts = np.zeros(Zpts.shape)

    OriginalDepthDose = GroundTruthResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    CurrentDepthDose = TopasResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    OriginalDepthDoseNorm = OriginalDepthDose * 100 /np.max(OriginalDepthDose)
    CurrentDepthDoseNorm = CurrentDepthDose * 100 / np.max(CurrentDepthDose)
    DepthDoseDifference = OriginalDepthDoseNorm - CurrentDepthDoseNorm

    ObjectiveFunction = np.mean(abs(ProfileDifference)) + np.mean(abs(DepthDoseDifference))
    return np.log(ObjectiveFunction)


def TopasObjectiveFunction(ResultsLocation, iteration):
    ResultsFile = ResultsLocation / f'WaterTank_itt_{iteration}.bin'
    path, file = os.path.split(ResultsFile)
    CurrentResults = WaterTankData(path, file)

    GroundTruthDataPath = str(Path(__file__).parent)
    # this assumes that you stored the base files in the same directory as this file, updated if needed
    GroundTruthDataFile = 'WaterTank.bin'
    GroundTruthResults = WaterTankData(GroundTruthDataPath, GroundTruthDataFile)

    OF = CalculateObjectiveFunction(CurrentResults, GroundTruthResults)
    return OF
```



## Results

| Parameter           | Ground truth | Optimizer |
| ------------------- | ------------ | --------- |
| BeamEnergy          | 15           | 15.02     |
| BeamEnergySpread    | 10           | 7.52      |
| BeamPositionSpreadX | 0.3          | 0.74      |
| BeamPositionSpreadY | 0.6          | 0.3       |
| BeamPositionCutoffX | 2            | **2.5**   |
| BeamPositionCutoffY | 1            | 3         |
| BeamAngularSpreadX  | 1            | 1         |
| BeamAngularSpreadY  | .07          | 0.28      |
| BeamAngularCutoffX  | 5            | 4.11      |
| BeamAngularCutoffY  | 2            | **2.43**  |

![](../../docsrc/_resources/electron_source/compare_results.png)

# other stuff

- tibaray scanning magnets
- target heating 



- 
