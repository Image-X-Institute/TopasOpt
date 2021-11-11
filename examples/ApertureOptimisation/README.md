# Aperture Optimisation example



## Creating GenerateTopasScript.py

The first thing we will be needing is a function that generates your topas script.

Create a python file called 'temp_GenerateTopasScript.py' (or whatever you want, the name isn't important). Copy the below code into it (or use an interactive console if you prefer):

```python
import sys
sys.path.append('../../TopasBayesOpt')
from TopasBayesOpt.CreateRunTopasScript import CreateTopasScript
from pathlib import Path

this_directory = Path(__file__).parent
topas_script = CreateTopasScript(this_directory, '/home/brendan/topas37/examples/Basic/FlatteningFilter.txt')
```

Replace the second line with the equivalent path in your topas installation, and run the file. If it works, you will now have a python function in your Optimisation Directory called GenerateTopasScript.py.

If you open this script up, you will see that all it has done it copied the contents of the topas file you input into a list, which it returns. At the moment, it's not very useful because every time it's called it will copy out exactly the same script! We will change that a bit later; first we need to define what our optimisation variables will be, which brings us to our next file.

You can delete temp_GenerateTopasScript.py now if you want to, it has done its job. 

> A code that takes a code and generates a code that generates a code

````python
# code to test GeneraetTopasScript

if __name__ == '__main__':
    Scripts = GenerateTopasScripts('.',1)
    for i, script in enumerate(Scripts):
        filename = 'test_script' + str(i) + '.tps'
        f = open(filename, 'w')
        for line in script:
            f.write(line)
            f.write('\n')

````

There are three special lines in topas scripts that bear further attention:

- 'includeFile': all include files will be copied into your optimisation folder into a newly created folder called IncludeFiles. The paths in the automatically generated topas scripts will be updated to point to these files. This is to avoid issues with relative paths. This operation is recursive, e.g. all included files are also scanned for their own recursive files.
- 'OutputFile': The output file location will be updated to point to BaseDirectory (which you haven't defined yet but the optimiser will know). In addition the names will be appended with itt_{itterationNumber}. This is so the optimiser can keep track of them

## Creating RunOptimisation.py

Create a new file called RunOptimisation.py (or whatever you want, the name isn't important). Copy the below code into it:

```python
# main script for running the optimisation

import sys
import os
import numpy as np
sys.path.append('../../TopasBayesOpt')
from TopasBayesOpt import TopasBayesOpt as tpb


BaseDirectory = os.path.expanduser("~") + '/Dropbox (Sydney Uni)/Projects/PhaserSims/topas'
SimulationName = 'BayesianOptimisationTest'

# set up optimisation params:
optimisation_params = {}
optimisation_params['ParameterNames'] = ['UpStreamAperture']
optimisation_params['start_point'] = np.array([1])
optimisation_params['UpperBounds'] = np.array([2])
optimisation_params['LowerBounds'] = np.array([0.5])
optimisation_params['Niterations'] = 40

Optimiser = tpb.BayesianOptimiser(optimisation_params, BaseDirectory, SimulationName)
Optimiser.RunOptimisation()
```

An explanation of what is happening in this script:

- BaseDirectory is where all your different optimisations will be stored.
- SimulationName is the folder which will contain this specific simulation. By default, if this folder already exists the code will crash. You can change this behaviour by setting ```overwrite-True``` in the initialisation of Optimiser.
- optimisation_params is a dictionary. It contains the names of the parameters to be optimised, their starting values, and their allowed bounds. Although only one parameter is called here, you can add as many parameters as you want separated by a comma. 
- ParameterNames is a label for you and the optimiser to keep track of the parameters. You can call it whatever you want.
- Niterations defines how many iterations the optimiser will carry out. 

## updating GenerateTopasScript.py

Remember from earlier that GenerateTopasScript.py currently only returns a list that can be used to recreate your existing topas script. 

GenerateTopasScript is going to be called from the optimiser, and when it is called, it is going to be passed a dictionary that contains the variables defined in optimisation_params and their current values. We need to edit GenerateTopasScript so that when these parameters change, the topas parameters change accordingly.

- You can also edit any other things of this script. For instance, for this example we are don't really care about the results, we just want to make sure we can get the infrastructure up and running. Therefore, you could create a variable Nparticles, set it to 10, and then change LINE to:.

## Creating TopasObjectiveFunction.py

Finally, create a file called TopasObjectiveFunction.py. The name of this **does** matter! 

The only things this file **must** do is

1. Receive the location of the latest results from the optimiser
2. Return a value for the objective function to the optimiser. 

Between these two things, you can do whatever you want. However, what we will be doing in this example, and what is in general a good template to follow, is:

- reads the latest results
- analyse the results
- turns that analysis into an objective function value

Below is TopasObjectiveFunction.py we will be using in  this example

```python
print('hello')
```



