# Aperture Optimisation example



## Creating GenerateTopasScript.py

The first thing we will be needing is a function that generates your topas script.

Create a python file called 'temp_GenerateTopasScript.py' (or whatever you want, the name isn't important). Copy the below code into it (or use an interactive console if you prefer):

```python
import sys

sys.path.append('../../TopasOpt')
from TopasOpt.GenerateTopasScriptGenerator import CreateTopasScript
from pathlib import Path

this_directory = Path(__file__).parent

# nb: the order of input files is important to make sure that a phase space files are correctly classified
CreateTopasScript(this_directory, ['../SimpleCollimatorExample_TopasFiles/SimpleCollimator.tps',
                                   '../SimpleCollimatorExample_TopasFiles/WaterTank.tps'])

```

If it worked, you will now have a python function in your Optimisation Directory called GenerateTopasScript.py.

If you open this script up, you will see that all it has done it copied the contents of the topas file you input into a list, which it returns. At the moment, it's not very useful because every time it's called it will copy out exactly the same script! We will change that a bit later; but first it's a good idea to test this script and see if it actually works. 

To test it, run it directly. This will create two scripts in your working directory called SimpleCollimator.tps and WaterTank.tps. They should be almost identical to the input scripts. The differences are:

- **Include files:**
- **Output files:**
- **Input files**

```
There are three special lines in topas scripts that bear further attention:

- 'includeFile': all include files will be copied into your optimisation folder into a newly created folder called IncludeFiles. The paths in the automatically generated topas scripts will be updated to point to these files. This is to avoid issues with relative paths. This operation is recursive, e.g. all included files are also scanned for their own recursive files.
- 'OutputFile': The output file location will be updated to point to BaseDirectory (which you haven't defined yet but the optimiser will know). In addition the names will be appended with itt_{itterationNumber}. This is so the optimiser can keep track of them
```



In general, you should think of the script created at this point as a first draft. You may have to do some further work on it to get it to do exactly what you want. In this particular case the further steps we will need to take on this script are described below. (You can delete temp_GenerateTopasScript.py now if you want to, it has done its job. )

> A code that takes a code and generates a code that generates a code



## Creating RunOptimisation.py

Create a new file called RunOptimisation_main.py (or whatever you want, the name isn't important). Copy the below code into it:

```python
import sys
import os
import numpy as np
from pathlib import Path

sys.path.append('/mrlSSDfixed/Brendan/Dropbox (Sydney Uni)/Projects/TopasOpt/TopasOpt')
import TopasOpt as to

BaseDirectory = os.path.expanduser("~") + '/Dropbox (Sydney Uni)/Projects/PhaserSims/topas'
SimulationName = 'BayesianOptimisationTest'
OptimisationDirectory = Path(__file__).parent

# set up optimisation params:
optimisation_params = {}
optimisation_params['ParameterNames'] = ['UpStreamApertureRadius', 'DownStreamApertureRadius', 'CollimatorThickness']
optimisation_params['UpperBounds'] = np.array([3, 3, 40])
optimisation_params['LowerBounds'] = np.array([1, 1, 10])
# generate a random starting point between our bounds (it doesn't have to be random, this is just for demonstration purposes)
random_start_point = np.random.default_rng().uniform(optimisation_params['LowerBounds'],
                                                     optimisation_params['UpperBounds'])
optimisation_params['start_point'] = random_start_point
optimisation_params['Nitterations'] = 20
# optimisation_params['Suggestions'] # you can suggest points to test if you want - we won't here.
ReadMeText = 'This is a public service announcement, this is only a test'

Optimiser = to.BayesianOptimiser(optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory,
                                 TopasLocation='~/topas37', ReadMeText=ReadMeText, Overwrite=True, length_scales=0.1)
Optimiser.RunOptimisation()

```

An explanation of what is happening in this script:

- BaseDirectory is where all your different optimisations will be stored.
- SimulationName is the folder which will contain this specific simulation. By default, if this folder already exists the code will crash. You can change this behaviour by setting ```overwrite-True``` in the initialisation of Optimiser.
- optimisation_params is a dictionary. It contains the names of the parameters to be optimised, their starting values, and their allowed bounds. Although only one parameter is called here, you can add as many parameters as you want separated by a comma. 
- ParameterNames is a label for you and the optimiser to keep track of the parameters. You can call your parameters whatever you want. 
- Niterations defines how many iterations the optimiser will carry out. 

## Editing GenerateTopasScript.py

Remember from earlier that GenerateTopasScript.py currently only returns a list that can be used to recreate your existing topas script. 

GenerateTopasScript is going to be called from the optimiser, and when it is called, it is going to be passed a dictionary that contains the variables defined in optimisation_params and their current values. We need to edit GenerateTopasScript so that when these parameters change, the topas parameters change accordingly. Firstly, we need to change three lines:

```python
#change
SimpleCollimator.append('d:Ge/SecondaryCollimator/RMin2      = 1.82 mm')
# to
SimpleCollimator.append('d:Ge/SecondaryCollimator/RMin2      = ' + str(variable_dict['DownStreamApertureRadius']) + ' mm')

# change
SimpleCollimator.append('d:Ge/SecondaryCollimator/RMin1      = 2.5 mm')
# to

# change
SimpleCollimator.append('d:Ge/SecondaryCollimator/RMax2      = 50 mm')
# to
SimpleCollimator.append('d:Ge/SecondaryCollimator/RMax2      = ' + str(variable_dict['CollimatorThickness']) + ' mm')
```

Notice that we have used the variable names that we set up RunOptimisation.py.

We will make a few more changes. The original files used 500000 primary particles which are split 1000 times in the target. The resultant phase space is scored just below the collimator, and recycled 200 times in the water tank simulation. This took around 1 hour to run on 16 multi threaded cores.

We don't actually need especially high quality data to guide the optimser, so I'm going to reduce the number of primary particles by a factor of 10:

```python
# change
SimpleCollimator.append('ic:So/Beam/NumberOfHistoriesInRun = 500000')
# to
SimpleCollimator.append('ic:So/Beam/NumberOfHistoriesInRun = 50000')
```

> **Hint:** Figuring out the optimal trade-off between simulation time and simulation noise is something that can take quite a while to get right! 

## Creating TopasObjectiveFunction.py

Finally, create a file called TopasObjectiveFunction.py. The name of this **does** matter! 

The only things this file **must** do is

1. Contain a function called TopasObjectiveFunction which:
2. Receive two inptuts from the optimiser: the location of the results, and the current iteration
3. Return a value for the objective function to the optimiser. 

A very simple example of a function which meets these requirements is below:

```python
import numpy as np

def TopasObjectiveFunction(ResultsLocation, iteration):
    return np.random.randn()
```

Of course, this is pretty useless as an objective function since it returns a random number that has 
nothing to do with the results! But it illustrates a very useful principle: all this function
has to do is take two parameters and return a number. You can do whatever you want in between.

A more sensible objective function must do a few more things:

- Read in the results,
- Extract some metrics from them
- Calculate an objective value based on those results. The actual objective function we will use in this example is copied below:

```python
import sys
import os
sys.path.append('../../TopasOpt')
from WaterTankAnalyser import WaterTankData
import numpy as np


def ReadInTopasResults(ResultsLocation):
    path, file = os.path.split(ResultsLocation)
    Dose = WaterTankData(path, file)  # WaterTank data is built on topas2numpy
    return Dose

def CalculateObjectiveFunction(TopasResults):
    OriginalDataLoc = os.path.realpath('../SimpleCollimatorExample_TopasFiles/Results')
    File = 'WaterTank'
    OriginalResults = WaterTankData(OriginalDataLoc, File)

    # define the points we want to collect our profile at:
    Xpts = np.linspace(OriginalResults.x.min(), OriginalResults.x.max(), 100)  # profile over entire X range
    Ypts = np.zeros(Xpts.shape)
    Zpts = OriginalResults.PhantomSizeZ * np.ones(Xpts.shape)  # at the middle of the water tank

    OriginalProfile = OriginalResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    OriginalProfileNorm = OriginalProfile * 100 / OriginalProfile.max()
    CurrentProfile = TopasResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    CurrentProfileNorm = CurrentProfile * 100 / CurrentProfile.max()
    ProfileDifference = OriginalProfileNorm - CurrentProfileNorm

    # define the points we want to collect our DD at:
    Zpts = OriginalResults.z
    Xpts = np.zeros(Zpts.shape)
    Ypts = np.zeros(Zpts.shape)

    OriginalDepthDose = OriginalResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    CurrentDepthDose = TopasResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    OriginalDepthDoseNorm = OriginalDepthDose * 100 /np.max(OriginalDepthDose)
    CurrentDepthDoseNorm = CurrentDepthDose * 100 / np.max(CurrentDepthDose)
    DepthDoseDifference = OriginalDepthDoseNorm - CurrentDepthDoseNorm

    ObjectiveFunction = np.mean(abs(ProfileDifference)) + np.mean(abs(DepthDoseDifference))
    return ObjectiveFunction

def TopasObjectiveFunction(ResultsLocation, iteration):

    ResultsFile = ResultsLocation / f'WaterTank_itt_{iteration}.bin'
    TopasResults = ReadInTopasResults(ResultsFile)
    OF = CalculateObjectiveFunction(TopasResults)
    return OF
```



Although this is quite a long code, all it's doing is:

- Reading in the latest results
- Extracting some profiles and depth dose curves
- Calculating an objective function based on a comparison of the original data and the current data

This code is a good template to use for developing your own objective functions. 

The objective function we are using is defined below
$$
OF = mean(abs(CurrentProfile - OriginalProfile)) + mean(abs(CurrentDepthDose - OriginalDepthDose))
$$
Note that both the current and original data are normalised to account for the fact that different numbers of primary particles are being used. 

## Running the example

You now have all the building blocks in place to run this example. To do so, you simply need to run RunOptimisation_main.py:

```bash
# from a command window:
python3 RunOptimisation_main.py 
```



A few notes however:

- Although I have tried to make a relatively light weight example here, it still requires a substantial server to run on. I ran this example on a server with 16 multi-threaded CPUs and it took around 5 minutes per iteration.
- Your command window has to have the appropriate environment set up. Setting up and managing python environments is beyond the scope of this code, but we will provide a detail





