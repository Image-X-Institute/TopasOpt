# How to know if the optimization has worked

Just because your optimisation RUNS, doesn't mean that it actually found the minimum. Here is some advice on assessing the quality of the optimisation. After some discussions with a colleague I felt inspired to write this brief notes. 

**1. Use the Bayesian Optimiser**

Although this code supports multiple optimisers, the Bayesian optimiser gives excellent feedback about whether or not it actually worked, which is simply lacking in most other approaches. For this reason: I heavily recommend using the Bayesian approach

**2. Make sure that your Topas simulation is robust before you start**

If the simulation is no good, the optimisation will be no good. Of critical importance: is the noise level in the simulations acceptable for your use case? See [handling noisy data](https://image-x-institute.github.io/TopasOpt/NoisyOptimisation.html) for instructions on assessing noise in the simulations. You can and should spend a lot of time on the Topas simulation side, tuning the noise versus run time and implementing appropriate variance reduction. 

**3. is your objective function appropriate**

See [designing objective functions](https://image-x-institute.github.io/TopasOpt/next_steps.html#designing-objective-functions). If the objective function:

- does not in fact capture your objective
- has multiple global minima of similar magnitude
- is too noisy (see above)

you are unlikely to get a high quality optimisation

**4. Look at the default plots**

Since you are using the Bayesian Optimiser, you will get several default plots in the logs folder.

- `ConvergencePlot` - do the predicted values correlate with the observed values? if not, then for some reason, the Gaussian process model is not modelling the objective
- `Retrospective Model Fit` - this shows the predicted objective, for points which have already been observed. This one SHOULD correlate very well - it's not hard to predict something that already happened!
- `SingleParameterPlots` - have you observed a minimum within your bounds? if not: the bounds may need to be adjusted. How does the modelled uncertainty look? if it's high, you probably need to run more iterations.

If you've done all this and you still think the optimisation doesn't work, then please raise an issue!

**5. KISS: keep it simple stupid**

Basically what we are doing here is a parameter search. The bigger the search space, the harder it is to find the solution. so:

- limit the dimensionality: if you throw more than ~10 parameters in, you're going to have a hard time. If you have a lot of parameters, consider whether you can split the problem into stages, rather than optimizing every parameter at the same time.
- limit the search region: bound your parameter space as tightly as possible
- build up the problem complexity: verify you can get this working for simple cases, then build up complexity.