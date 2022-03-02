# Development example

This example is aimed at people who want to help develop this library, either by adding new optimisers
or extending existing optimisers!

A major issue with optimising monte carlo sims is that they are very slow. This can make development and testing very 
painful! For this reason, we have included functionality where one can call a 'Topas Emulator'. Basically this
is just a function that does nothing, allowing you to test your optimisation algorithm on [the rosenbrock function](https://en.wikipedia.org/wiki/Rosenbrock_function),
which is a very commonly used function to test optimisers, and has a known global minimum.

This example demonstrates this process.

## Set up base directory

You will want to set up your base directory in a same way that you did in the other examples. The key difference is:

- GenerateTopasScripts code do nothing, and can be almost empty  
- When you instantiate the optimser, you **must** set TopasLocation='testing_mode'.

GenerateTopasScripts:
```python
def GenerateTopasScripts(BaseDirectory, iteration, **variable_dict):
    return ['dummy_script'], ['dummy_script']
```

TopasObjectiveFunction
```python

def TopasObjectiveFunction(ResultsLocation, iteration):
    pass
```


## Limitations

This approach tests a lot of the code, but it doesn't test 
1. The users own code (GenerateTopasScripts and TopasObjectiveFunction), and, perhaps more importantly;
2. it doesn't test the ability of this code to find and correctly use those codes.

This is just a pretty inherent limitation of the way this code is set up unfortunately. 
