# Setting up the python environment in a command window



Management of virtual environments in python is a detailed and complex topic which is well beyond the scope of these documents. However, we do give a simple example of setting up a virtual environment through the linux command window. There are many ways to do this, this is only one!

This assumes you already have python3 installed, and that the python3 alias will call the version you want to use (e.g. 3.7).  At least on ubunutu, this is true by default.

- Open a new terminal window

- make a new directory called TopasBayesOptVenv

```bash
# python3 -m venv /path/to/new/virtual/environment
# e.g.
python3 -m venv ~/python/TopasBayesOptVenvTest
```

- activate the environment you just created:

```bash
source ~/python/TopasBayesOptVenvTest/bin/activate
```

- If this is the first time you used the environment, you will need to install the TopasBayesOpt package

```bash
python3 -m pip install TopasBayseOpt
```

- The package should install all its dependencies by default, but if you ever have a missing library error you can install it in a similar manner
- Whenever you need to activate this environment, you can use the source command above. You only have to carry out the install step once. 
