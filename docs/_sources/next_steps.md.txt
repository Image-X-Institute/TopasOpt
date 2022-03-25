# Next steps (work in progress!)

These instructions assume you have already worked through at least one of the worked examples.
 If you have not, it is strongly recommended that you go back and do so before proceeding. 

## Designing objective functions

The optimisers implemented in this library are so called 'black box' optimisers, which means they don't know anything about the objective function or make any assumptions about it's shape. This means that you can literally make your objective function anything you want, the only requirement is that it returns a number to the optimiser.

Having said this, having a well crafted objective function can absolutely be the difference between success and failure. The below are some things you may want to consider when you are writing your objective function.

### Competing objectives

Let's take a trivial example: say you are building a table; you want to minimise the mass, but maximise the strength. Clearly these objectives will 'fight' each other.

In this library, we do 'single criteria optimisation', which means the objective function can only return one number. That means you have to encapsulate both priorities in the objective function. A simple way to do this is below:

```python
objective_function = -weight_strength*strength + weight_mass*mass
```

(Note that we want strength to be high - since we are **minimising** this function, we use -strength).

Clearly, the 'best' solution that will be found in this case depends on how you weight these objectives. This can take some trial and error and experience to get right.

A more elegant, but more complicated way to handle these situations is via [multi-objective or pareto optimisation](https://en.wikipedia.org/wiki/Multi-objective_optimization). We do not currently have an implementation of this for this library although pull requests are welcome!

### Hard boundaries

Let's continue using our table from above. Although we have initially stated that we want maximum strength, this is probably not really true - we just want the strength to be above some threshold. This is another very common situation, and in code looks like below :

```python
if strength_sufficient:
	objective_function = 0 
else:
	objective_function = large_number  # penalise the case where our condition is not met
```

The problem with this form is that it results in a discontinuity in the objective function. Although the optimisation will still run, it may not bconverge as fast as it could. In such cases it is better to "smooth" the discontinuity using a [sigmoid function](https://en.wikipedia.org/wiki/Sigmoid_function). Having said this, in my experience with the Bayesian optimiser it didn't actually make much difference - but at the very least a smooth objective function gives reviewers less to complain about ;-)

### Log of objective function

It is pretty common that large swarthes of the objective space are 'bad' i.e. have a high objective function. In some cases, it is desirable to flatten out these bad regions so the optimisation algorithm doesn't get 'distracted' by high gradient errors in 'bad regions'. For instance, maybe your objective function ranges between 0 and 100, but you are really interested in the spaces between 0 and 1. The optimiser may find a very steep gradient that goes from 20 to 2, which to it may seem more interesting than a shallow gradient in a different region that may go from 2 to 1.2. 

In such situations, you may wish to take the log of the objective function. This has the effect of surpressing the differences in high value  (bad)regions and enhancing the differences in the low value (good) regions. Note however that this will also emphasise low level noise in your objective function!

### Handling constraints

At the moment, this code handles boundaries (0<=x<=1) but not constraints (x<=2*y). Nevertheless, it is very common that the allowed values for one variable are dependant on the values of another variable. 

I hope that in the future we will be able to handle these cases in the problem set up, but for now, I recomend just returning a high number. Although this does contradict my earlier advice to try and ensure the objective function is smooth, it is less important to ensure this in 'bad' regions, since a good algorithm will not pay too much attention to these regions anyway.

## Convergence criteria

At the moment, this code is primarily set up to terminate based on number of iterations, e.g. if you figure you have 24 hours of computing time available, figure out how many iterations you can run for. It is of course possible in principle to use different convergence criteria - e.g.

- if the solution hasn't been improved on for N iterations, stop
- if the solution is x times better than the starting solution, stop

At the moment, these aren't coded , but will be considered in future versions!

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
```

## NelderMeadOptimiser

## Choose the starting simplex

The NelderMead method is based on the concept of a simplex, which is a shape with [n+1] vertices, where n is the number of parameters. For instance, in a one dimension, the simplex has two vertices. The algorithm works by changing the position of these vertices according to a set of rules - expand, contract, reflect, or shrink.

Clearly, the position of the starting simplex will be of crucial importance in the convergence of this algorithm. Like a lot of things in optimisation, sometimes there can be more art than science in choosing the starting simplex well! In general, choosing it to span a larger space will result in more exploraratory behavior, while a smaller space will be quicker to converge but more likely to get stuck in a local minima (these are only rules of thumb!!). We provide three ways to choose the starting simplex, using the parameter ```NM_StartingSimplex```:

- None: this will follow the default scipy, which will construct the starting simplex by expanding your starting position by 5%. So for example, in 1D, if your starting point is 1, your starting simplex would be [1, 1.05]
- Float: this just replaces the 5% with another number, e.g. NM_StartingSimplex=.1, you will get [1, 1.1] in the example above.
- List/array of size [n, n+1]: This allows you complete control over the starting simplex, e.g. for a two dimensional problem: NM_StartingSimplex = [[0.9, 0.9], [0.72, 0.9], [0.9, 0.72]]
