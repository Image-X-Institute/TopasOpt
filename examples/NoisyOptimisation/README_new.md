# Handling noisy data

In Monte Carlo modelling, we constantly have to trade off how long our simulations run for and how noisy they are.
Obviously this is particularly important for TopasOpt, where total run time = time_per_sim * n_iterations.

In general, the easiest way to handle noise is to make sure it is low enough that you don't care about it. However, 
there will certainly be situations where this approach results in unaccetably long run times. Therefore, in this example
we will look at working with noisy data using Bayesian Optimization. Essentially the goal is to include the noise in
our predictions, so our model doesn't get 'over confident' about some spurious results. 

This tutorial is split into the following sectoins:

- generating noisy data
- modelling noisy data with gaussian process models
- re-running TopasOpt with a custom kernel

## Generate N identical simulations

- add parameter to GenerateTopasScripts allowing us to vary N_particles

## Passing the newly constructed kernel to TopasOpt

- change GenerateTopasScripts.py back to n_particles = 20000
- add new parameter to main script where we pass custom kernel

## Comparison with Nelder-Mead

As a comparitor, lets see how Nelder-Mead does on the same problem. Instantiate like this: