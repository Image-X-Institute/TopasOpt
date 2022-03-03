# Adding new optimisation algorithms - work in progress!

There are many algorithms that could be used for Monte Carlo, and I tried to design this framework in a manner
that enables it to be easily extended. The following docs explain how to easily set up a new optimisation algorithm.
Of course, you are free to simply use whatever you set up internaly, but if you find that it is useful and offers additinoal
functionality, you may wish to consider making a pull request to include it in the main program. In that case, these documents
also explain how we would like you to proceed.


- Inheritance
- RunOptimisation method
- private/ public classses
- example and tutorial
- doc strings
- tests

## Adding new optimisation algorithms

It is also possible to add new optimisation algorithms, by inheriting from the optimisation base class, e.g.

```python
from TopasOpt.Optimisers import TopasOptBaseClass

class NewOptimiser(TopasOptBaseClass):
   # your code here

## Using different optimisation algorithms

The most common optimisation algorithms work on gradients, but when the input is based on monte carlo simulation results, we cannot easily provide derivatives for the objective function, or even assume that it is differentiable.  We believe that in most scenarios, Bayesian optimisation is the ideal approach for this scenario, because it performs well for expensive, noisy, black box objective functions. However, there may be situations where other algorithms perform faster. In particular, if your problem is relatively straight forward it may not be worth the additional overhead of training and understandning Gaussian process models. As such, you can also use some other gradient free optimisation techniques, in particular the Nelder-Mead algorithm and Powell's method. Both of these use the default [scipy implementation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html).
