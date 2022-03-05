# TopasOpt

[![Travis](https://img.shields.io/travis/fmfn/BayesianOptimization/master.svg?label=Travis%20CI)](https://travis-ci.org/fmfn/BayesianOptimization)
[![Codecov](https://codecov.io/github/fmfn/BayesianOptimization/badge.svg?branch=master&service=github)](https://codecov.io/github/fmfn/BayesianOptimization?branch=master)
[![Pypi](https://img.shields.io/pypi/v/bayesian-optimization.svg)](https://pypi.python.org/pypi/bayesian-optimization)

![](/home/brendan/python/TopasOpt/docsrc/_resources/interrogate_badge.svg)

This code provides a framework for performing inverse optimisation on monte carlo radiation transport 
simulations using [TOPAS](https://www.google.com/search?channel=fs&client=ubuntu&q=topas+MC).

## Install and Requirements

To install: ```pip install TopasOpt```

- This code will only run on linux (as will topas) (I don't have a mac to check it on but I think it will work)
- You require a working installation of [topas](https://topas.readthedocs.io/en/latest/getting-started/intro.html) to run the code.
- python3.8 or greater is required.

## Usage and Documentation

See the examples folder for worked examples.
Detailed documents are provided [here](https://acrf-image-x-institute.github.io/TopasOpt/index.html)

## Directory Structure

- **TopasOpt:** source code
- **examples:** as the name implies!
- **docs:** html documentation created from docsrc using sphinx
- **docsrc:** markdown/rst documentation.
- **tests:** tests which are run on push







