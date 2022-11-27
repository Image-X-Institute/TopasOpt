# Developer Notes

This is some 'behind the scenes' how to's. Although I grandiosly called it developer notes, in reality it is so that I can remember how to update this repository in the future.

## Additional requirements

To install the required developer libraries

```
pip install dev_requirements.txt
```

## Packaging instructions

nb: this is mostly for me so I can remember how I did this :-P

Packaging for this project has been setup based on [this tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/).
To update the distribution code, use the following commands.
Required depencies are defined in setup.cfg

```bash
# first update version number in TopasOpt.__init__

# delete any existing distribution files
rm -r dist
# build distribution packages
python -m build
# upload built package
python3 -m twine upload --repository testpypi dist/*  # if tests
twine upload dist/*  # for real
```

## Testing framework 

We have some test cases set up which run using [pytest](https://www.google.com/search?channel=fs&client=ubuntu&q=pytest). These are more like 'integration and tests' than unit tests, they mostly test that the code runs without errors and succesfully optimises the rosenbrock function (read more [here](https://acrf-image-x-institute.github.io/TopasOpt/DevelopmentExample.html).)

The tests are automatically run one someone does ```git push```, but if you ever want to run them manually instructions are below:

- To run the tests, just run ```pytest``` from the command line at the repository root
- To assess coverage of tests ```coverage run -m pytest``` then ```coverage report```
- We require >99% of docstrings are present. To get details stats on what doc strings are missing, run ```interrogate ../TopasOpt -vv```

## Building documentation

The documentation is build from the docsrc directory by running ```make github```.

If you want to include a new example in the documents, follow these instructions

- All of your images should be placed in docsrc/_resources/{name-of-example}
- The rest of your example working directory should be in examples/{name-of-example} (the names do not strictly have to match but it's probably a good idea)
- Make sure you use relative links to point to your images, e.g. ../../docrsrc/_resources....
- Inside docsrc, open conf.py, and update the ```example_readmes``` list so that your new example readme is included.
- open worked examples rst and add your new example to the index. 
- Next step the docs are built, your readme will be included in the html

## Adding new optimisation algorithms

This library has been designed to make it easy to add new optimisation algorithms. The basic approach for a new optimiser is below

```python
from TopasOpt.Optimisers import TopasOptBaseClass   # only necesary if you are not adding directly to TopasOpt.Optimisers.py

class NewOptimiser(TopasOptBaseClass):
    # note all __init__ is handled in TopasOptBaseClass. You can see the source code for an example. You don't have to do it
    # exactly like this if you don't want - feel free to add your own __init__ and then use super().__init__ if you want.

    def _some_supporting_method(self):
	# all methods should be private except for RunOptimisation and RestartOptimisation. I prefer soft-private formalism, e.g. 		  # prefix your methods with a single underscore.
        pass
    
    def RunOptimisation(self):  # public method
        self.SetUpDirectoryStructure() # this is needed here for every optimiser
        
        # the function you want to minimise is self.BlackBoxFunction, which your optimiser has inherited from TOpasOptBaseClass
        self.minimise(self.BlackBoxFunction)  # for example
        
    def RestartOptimisation(self):  # this can be another handy public method but is not required or even possible for all optimisers.
        pass

```

If you do implement a handy new algorithm we would love you to consider making a pull request back to the main repository so it can be included in the distributed version. If you do want to do that, a few more requirements:

- Please write a tutorial demonstrating how to use your algorithm, and include it in examples/{your_algorithm}.
- Please see ADD LINK for notes on formatting the readme and updating docsrc/conf.py to ensure the tutorial is included in the html documenation
- Please ensure that your example has good docstring coverage, or it will fail the test framework
- Please add a test of your optimiser to tests/test_optimisers.py - you can see the existing tests to see how to do it. You don't have to do anything else, just adding the test is enough to ensure it will be found by ptest.

