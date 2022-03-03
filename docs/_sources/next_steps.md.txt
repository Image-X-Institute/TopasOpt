# Next steps (work in progress!)

These instructions assume you have already worked through at least one of the worked examples.
 If you have not, it is strongly recommended that you go back and do so before proceeding. 

## All Optimisiers

### Improving accuracy

If you think you require better accuracy than the first result you get, you have a few options:

- Run more iterations.
- Use these parameters as a starting guess, and run a new optimisation with a reduced search space
- Note that there **will** be noise in the objective function. This is an inherent aspect of the monte carlo method, especially when we are trying to run fast simulations. At some point, this noise will limit the accuracy the optimiser could even theoretically achieve. See assessing and handling noise in the objective function below.

### read in and plot a previous log file

Whenever an optimisation is run, a log file is created at BaseDirectory / SimulationName / logs/ OptimisationLogs.txt.
You can read this file into a dictionary as follows:

```python
from TopasOpt.utilities import ReadInLogFile

LogFileLoc = '/home/brendan/Documents/temp/NMtest/logs/OptimisationLogs.txt'
LogFileDict = ReadInLogFile(LogFileLoc)
```

You are then free to create your own plotting routines to present this data any way
you want, but we do provide a default ploting function:

```python
from TopasOpt.utilities import PlotLogFile

LogFileLoc = '/home/brendan/Documents/temp/NMtest/logs/OptimisationLogs.txt'
PlotLogFile(LogFileLoc)
```

## BayesianOptimiser

The following is a list of things that you can also do with this optimiser (

### Restart an optimisation

 Sometimes an optimisation is terminated prematurely because of time limits on job submissions or because your partner turned your computer off.

In such situations, it is easy to restart the optimisation; you just have to change Optimiser.RunOptimisation() to Optimiser.RestartOptimisation().

This can also be used in situations where you initially thought that 20 iterations would be sufficient but later want to extend this to 40 iterations for instance.

### Load and interact with the gaussian process model

One of the nice things about bayesian optimisation is that at the end of it, there is a model which can be used to predict what the objective function might look like at some particular point. Of course whether or not this is useful depends on how well the model was trained, but assuming you have trained a useful model, you can use the logs from a previous run to read in and interact with the gaussian process model. The below script demonstrates this:

### Setting length scales in the gaussian process model

Length scales are used in the kernel of the gaussian process model. In simple language, the length scales indicate how close together two points should be to expect them to have a fairly similar value. The length scales are integral in getting a good fit of the gaussian process model to 

In this code, the default behaviour is to set the length scales to 10% of the allowed range for each parameter. E.g. if you have a parameter with a lower limit of 1 and an upper limit of 3, the default length scale would be (3-1)*0.1 = 0.2.

This approach works pretty well as the default. However, there may be situations when you wish to apply a little more finesse. In that case, you can also pass an array for length_scales, with one value per parameter, e.g.

```python
Optimiser = to.BayesianOptimiser(optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory, TopasLocation='~/topas37', ReadMeText=ReadMeText, Overwrite=True,length_scales=[par1_scale, par2_scale, par3_scale, etc.])
```

Note that no matter what you pass in as the initial length scales, they will be optimised behind the scenes. If you look at the log file of a completed run, it will tell you at the end what the initial
length scales used were, and what the fitted length scales at the end of the run (e.g. the data driven answer) were. If you plan to run the optimiser again, you will likely get faster convergence if you use the fitted length scales to start off with.


Example of switching between different optimisers is below. For detailed documentation on what options are available for the different optimisers, see the code documentaiton. ADD HYPERLINKS!

```python
Optimiser = to.BayesianOptimiser(optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory)
# OR 
Optimiser = to.NealderMeadOptimiser(optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory)
# OR 
Optimiser = to.PowelOptimiser(optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory)
```


```

The Base class contains all the basic functionality an optimser will need, such as generating models, reading results, etc. This inheritance mechanism makes it fairly quick to set up new algorithms, e.g. the implementation of the Nelder-Mead algorithm requires only 45 lines of code. 

You can look through the source code to see how the different optimisers are implemented.

## Assess noise in the objective function

You can use your GenerateTopasScripts function to create 10 identical scripts, run them all, and then assess the reslts with TopasObjectiveFunction. If the noise in the objective function is higher than the precision you would ultimately like to converge to then you are unlikely to get a great result. E.g. if the noise in the objective function is 20% and you hope to be within 10% of the true optimum you are in trouble. For the Bayesian optimiser, you may be able to handle noise by increasing bayes_GP_alpha.



