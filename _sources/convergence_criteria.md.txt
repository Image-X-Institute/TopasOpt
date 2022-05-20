# Convergence criteria

At the moment, this code is primarily set up to terminate based on number of iterations, e.g. if you figure you have 24 hours of computing time available, figure out how many iterations you can run for.

It is of course possible in principle to use different convergence criteria - e.g.

- if the solution hasn't been improved on for N iterations, stop
- if the solution is x times better than the starting solution, stop

At the moment, these aren't coded properly, but should be considered in future versions!
