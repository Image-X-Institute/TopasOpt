# TopasOpt: An open source library for inverse optimisation with Topas Monte Carlo

Other names,,,,

TopasInverseOptimisation

> Brendan Whelan, Paul Keall, Billy W Loo

## Introduction

Monte carlo simulations of radiation transport are ubiquitous across many fields and industries and are considered the most accurate mexhanism of calculating radiation dose. In Medical Physics, Monte Carlo simulations is used for research studies, engineering designs, as a back up dose check, and, increasingly, as a primary clinical dose calculation mechanism. Any Monte carlo simulation is based on a large number of parameters; for instance to specify geometry or phase space parameters. In many cases, these parameters are not well known and must be estimated. In other instances, a parameter may be tuneable and it is desirable to find the optimimum value for that parameter. Despite the ubiquity of Monte Carlo methods, there is currently no simple way to handle these situations. Although it is common to read paper in which some parameter was 'optimized' what this tends to mean in practice that either a grid search was used, or that a few simulations were run and then the best value was guessed. In this work, we aim to overcome this situation by presenting and demonstrating an open source optimization library for Topas Monte Carlo. We comment on why we believe that Bayesian Optimisation is generally an excellent choice for optimisation based on Monte Carlo data, however our framework also allows simple extension to different optimisation algorithms; to this end we also demonstrate the use of the Nelder-Mead optimisation algorithm. 

A number of toolkits exist for performing Monte carlo simulations; of particular note are Fluka, EGS, and Geant4. A number of secondary packages have been built off these primary codes to improve ease of use. One of these is TOPAS: TOol for PArticle Simulation. Topas wraps Geant4 and makes it possible for users to develop complex simulations using only parameters files. {SAY SOMETHING ABOUT TOPAS GROWTH}. As such, an optimisation tool working with topas has the potential to be used by a large and rapidly growing user base.

There have been some previous examples of optimisation based on Monte Carlo simulation. Wang et. al. implemented the Nelder-Mead method in conjunction with {EGS?}, and demonstrated the utility in single channel collimator design. This is however the first open source optimisation library, the first Bayesian optimisation library, and the first library which has been developed such that any existing simulation can be transformed relatively painless and quickly into an optimisation problem. 

## Methods and Materials

### Background: Review of gradient free optimization algorithms

Optimization can be generally described as searching for a particular point in some N-dimensional space. Typically this point is either the minimum or maximum value. There are a great many algorithms for performing optimisation, the strengths and weaknesses of which are highly problem dependent. Therefore, let us define the problem at hand. Monte carlo data is noisy and expensive, and user defined objective functions will in general be 'black box' meaning no knowledge of the form of the objective function can be assumed. Combined,  these aspects mean that optimisation of Monte Carlo data is rather challenging! 

| **Characteristic** | **Explanation**                                              |
| ------------------ | ------------------------------------------------------------ |
| Noisy input data   | The input data is noisy due to the inherently stochastic nature of Monte Carlo. Practically, what this means is that the some point in the objective function space is probed repeatedly, different values will be returned. This hinders reproducibility and convergence of optimization procedures. Noise can be offset by running more histories, but this directly increases the cost of each evaluation. |
| Expensive          | Expense refers to how long it takes to perform each optimisation iteration. Monte Carlo is a computationally expensive and slow technique, taking at least several minutes per iteration. There is a direct trade off between how noisy the data is and how expensive it was to acquire. |
| Black box          | Black box optimisation refers to optimisation in which no knowledge of the objective function is required. There is no assumption that the objective function is smooth and no gradient assessments required. |



The ideal choice of optimisation algorithm for Monte Carlo simualtions is one which performs well subject to these three constraints. Several black box algorithms exist; notable choices are the Nelder-Mead algorithm, evolutionary-type algorithms, and algorithms based on approximation of the true objective function (including Bayesian Optimisation).
Evolutionary algorithms utilise an ensemble concept; they are robust to noise but are not well suited to expensive problems due to the number of redundant assessments of the objective function. Examples of evolutionary algorithms include particle swarm optimisation and the genetic algorithm. The Nelder-Mead is a very well established algorithm based on the concept of a 'simplex' which is an N+1 dimensional shape that 'steps' down the objective function. Its utility in driving Monte Carlo simulations has previously been demonstrated by Wang et al. However, it is not robust to noise, and has a tendency to become stuck in local minima. The third class of algorithms are those in which the true objective function is approximated by some surrogate. These algorithms include 'constrained optimisation by linear approximation' (COBYLA) 

Nelder-Mead: Heuristic

>  **Table: Black box optimization algorithms**. Note that pros and cons are specific to the problem domain being considered. 
>
>  | Class            | Examples                           | Brief explanation                                            | Pros                                                         | Cons                                                         |
>  | ---------------- | ---------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
>  | Heuristic        | Nelder-Mead, simulated annealing   | For a given starting point, use some simple set of rules to choose next points to probe | Simple to implement and interpret.                           | Tendency to get stuck in local minima for complex objectives. |
>  | Surrogate based  | COBYLA, Bayesian Optimisation      | A surrogate is used to approximate the true objective function. At each iteration the surrogate is updated based on the results. | Can handle noise well, don't get stuck in local minima       | Can be complex and difficult to understand. Training of surrogate can be expensive, especially for many (> ~20) parameters. |
>  | Population based | Genetic algorithms, Particle swarm | Uses a population of solutions.                              | Can handle noise, don't get stuck in local minima. Good for problems with many parameters. | Best suited to situations where many assessments of objective function can be made in parallel; as such tend to not be very efficient for expensive objective functions. |
>  |                  |                                    |                                                              |                                                              |                                                              |

Powells method: good if function is quadratic near extrema. But since we can't assume this for black box optimisation I won't include it. I'm not really sure I can group Genetic and particle swarm together like this although to me it makes sense. 

> Note: In general, none of these algorithms guarantee that the globally optimal solution is found. I think that such a guarantee is not possible with black box optimisation. 

Broadly speaking, in such problem classes heuristic approaches must be applied. What t

### TopasBayesOpt:  Goals and Architecture

- Enable any parameter from any topas project to be optimised
- Enable simple extension to other optimisation algorithms 

Several steps are common to any optimisation algorithm. These are a) Generate a model for a given set of parameters, b) Run the model, and c) Extract results and assess the objective function. The next step is to somehow decide on the next set of parameters to assess, and it is this step which is algorithm specfic. The TopasBayesOpt code is object orientated, and each optimisation alfogorithm is a separate class which inherits shared functionality a base class. Using this mechanism, a minimal implementation of the Nelder-Mead algorithm can be achieved using only five lines of code. 

**The base directory**

The basic starting point for a new optimisation is a folder which will contain the user defined scripts which define the optimiser to use, the model to generate, and the objective function. This folder is termed the 'base directory'. 

| Script in base directory  | Explanation                                                  |
| ------------------------- | ------------------------------------------------------------ |
| RunOptimisation_main.py   | This script is executed to run the optimisation. It defines the directory to write results, the optimisation variable names starting values and bounds, and the options used to initialised the optimiser. |
| GenerateTopasScripts.py   | This script accepts an dictionary of optimisation parameters from the optimiser, and outputs topas parameter files with the current value of the optimisation parameters. A first draft of this function can be generated by  passing the starting topas parameter files to the TopasOpt module 'CreateTopasScript'. However, some manual editing by the user is required to correctly incorporate the optimisation variables. |
| TopasObjectiveFunction.py | This function must do two things: 1) Receive two inputs from the optimiser: the location of the results, and the current iteration, and 2) Return a value for the objective function to the optimiser. What happens in between is entirely up to the user; as such the user has ultimate flexibility in defining an objective function. A standard approach would be to read in the latest results, extract relevant metrics from them, and calculate some objective function from these metrics. Concrete examples of objective functions are provided in the examples section below. |

**Conversion of topas parameter files to a python function**

A requirement of all optimization approaches is to generate a model for a given set of parameters. This is not straightforward for topas, which uses 'parameter files' to define a model. A python module was therefore developed which takes a set of parameter files and generates a python function which in turn writes the initial parameter files. TopasOpt will look for this function in the directory TopasOpt is initialised from, and pass a dictionary containing the user defined optimisation parameters to it on each iteration. The end user is required to manually edit TopasScriptGenerator such that the resultant scripts use the current value of each paramter. Typically this involves editing one line per optimization parameter. An example is below:

```python
# 1. change
SimpleCollimator.append('d:Ge/SecondaryCollimator/RMin2      = 1.82 mm')
# to
SimpleCollimator.append('d:Ge/SecondaryCollimator/RMin2      = ' + str(variable_dict['DownStreamApertureRadius']) + ' mm')
```

The module which converts Topas parameter files into a python function handles several situations automatically:

- Any output phase space file names are automatically appended with iteration number so that the optimiser can keep track of different results
- Any relative paths are updated automatically
- Include statements (which include other parameter files) are recursively searched 
- Multiple Parameter files can be written each iteration; the code will determine situations in which the output of one simulation is used an input for another simulation. 

The major (known) limitation to this process is that  any variables to be optimised must be defined and used in the input parameter files as oposed to parameter files which are 'included' in the input files. In general, this process should be considered as one which creates a good first draft of the generator function, but which will still require at least some user tweaking to finalise.

**Reading in the results and defining an objective function** 

As described in TABLE, at each iteration the objective function will be queried. Typically, within this call the user will want to read in the latests resuts and calculate some objective function based on these. Reading topas phase space files in python can be handled through the [topas2numpy module](https://github.com/davidchall/topas2numpy). Some simple code is included in this package which extends this functionality slightly to enable easy extraction of profiles from volumetric data, but in general it is the users task to define exactly what processing steps should be applied to the topas data and what metrics are extracted from them. 

There is no requirement on the form of the objective function in this package and no assessment of gradients is required. In general, convergence will be quicker for smooth objective functions, but this is not a requirement. 

**Running the parameter files for each iteration**

For each iteration, a shell script to run the topas files is created and automatically run through the python 'subprocess' module which runs this script from a terminal. The user can define a header to include in this shell script, such that it automatically performs any necessary environmental set up and takes into account custom topas installation locations etc.

**The output directory**

Within RunOptimisation_main.py, the user must define a location to write results to. The resultant folder is structured as follows:

| Item in results directory | Explanation                                                  |
| ------------------------- | ------------------------------------------------------------ |
| logs (directory)          | At a minimum contains a convergence plot and a log file sumarising the value of each parameters and the objective function for every iteration. Other logs/plots are included on a per-optimiser basis. |
| Results (directory)       | Contains all output files from the topas simulations. Alternatively, the user can request that only the most recent result file is stored to save space. |
| TopasScripts (directory)  | Contains every topas script run, appended with the relevant iteration. |
| OptimisationSettings.json | All settings are saved to a json file such that the exact settings used to generate the results can easily be recovered. |
| Readme.txt (optional)     | The user may specify some read me text when the optimiser is intialised which explains the purpose of the optimisation. If this was done, the readme text is written to this file. |

### Examples

Two examples are supplied. Detailed step by step tutorials to recreate these examples are included in the code repository. 

### Example 1: Optimisation of geometric parameters



### Example 2: Optimisation of phase space parameters

## Results

## Discussion

- Multi Objective Optimisation
