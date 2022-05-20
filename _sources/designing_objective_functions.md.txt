# Designing objective functions

The optimisers implemented in this library are so called 'black box' optimisers, which means they don't know anything about the objective function or make any assumptions about it's shape. This means that you can literally make your objective function anything you want, the only requirement is that it returns a number to the optimiser.

Having said this, having a well crafted objective function can absolutely be the difference between success and failure. The below are some things you may want to consider when you are writing your objective function.

## Competing objectives

Let's take a trivial example: say you are building a table; you want to minimise the mass, but maximise the strength. Clearly these objectives will 'fight' each other.

In this library, we do 'single criteria optimisation', which means the objective function can only return one number. That means you have to encapsulate both priorities in the objective function. A simple way to do this is below:

```python
objective_function = -weight_strength*strength + weight_mass*mass
```

(Note that we want strength to be high - since we are **minimising** this function, we use -strength).

Clearly, the 'best' solution that will be found in this case depends on how you weight these objectives. This can take some trial and error and experience to get right.

A more elegant, but more complicated way to handle these situations is via [multi-objective or pareto optimisation](https://en.wikipedia.org/wiki/Multi-objective_optimization). We do not currently have an implementation of this for this library although pull requests are welcome!

## Hard boundaries

Let's continue using our table from above. Although we have initially stated that we want maximum strength, this is probably not really true - we just want the strength to be above some threshold. This is another very common situation, and in code looks like below :

```python
if strength_sufficient:
	objective_function = 0 
else:
	objective_function = large_number  # penalise the case where our condition is not met
```

The problem with this form is that it results in a discontinuity in the objective function. Although the optimisation will still run, it may not bconverge as fast as it could. In such cases it is better to "smooth" the discontinuity using a [sigmoid function](https://en.wikipedia.org/wiki/Sigmoid_function). Having said this, in my experience with the Bayesian optimiser it didn't actually make much difference - but at the very least a smooth objective function gives reviewers less to complain about ;-)

## Log of objective function

It is pretty common that large swarthes of the objective space are 'bad' i.e. have a high objective function. In some cases, it is desirable to flatten out these bad regions so the optimisation algorithm doesn't get 'distracted' by high gradient errors in 'bad regions'. For instance, maybe your objective function ranges between 0 and 100, but you are really interested in the spaces between 0 and 1. The optimiser may find a very steep gradient that goes from 20 to 2, which to it may seem more interesting than a shallow gradient in a different region that may go from 2 to 1.2. 

In such situations, you may wish to take the log of the objective function. This has the effect of surpressing the differences in high value  (bad)regions and enhancing the differences in the low value (good) regions.

## Handling constraints

At the moment, this code handles boundaries (0<=x<=1) but not constraints (x<=2*y). Nevertheless, it is very common that the allowed values for one variable are dependant on the values of another variable. 

I hope that in the future we will be able to handle these cases in the problem set up, but for now, I recomend just returning a high number. Although this does contradict my earlier advice to try and ensure the objective function is smooth, it is less important to ensure this in 'bad' regions, since a good algorithm will not pay too much attention to these regions anyway.

## Convergence criteria

At the moment, this code is primarily set up to terminate based on number of iterations, e.g. if you figure you have 24 hours of computing time available, figure out how many iterations you can run for. It is of course possible in principle to use different convergence criteria - e.g.

- if the solution hasn't been improved on for N iterations, stop
- if the solution is x times better than the starting solution, stop

At the moment, these aren't coded , but will be considered in future versions!
