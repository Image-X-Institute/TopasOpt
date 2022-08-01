# TopasOpt

![](docsrc/_resources/interrogate_badge.svg) [![codecov](https://codecov.io/gh/ACRF-Image-X-Institute/TopasOpt/branch/master/graph/badge.svg?token=0FSEO19LCD)](https://codecov.io/gh/ACRF-Image-X-Institute/TopasOpt)![test](https://github.com/ACRF-Image-X-Institute/TopasOpt/actions/workflows/run_tests.yml/badge.svg) ![docs](https://github.com/ACRF-Image-X-Institute/TopasOpt/actions/workflows/build-docs.yml/badge.svg)


This code provides a framework for performing optimisation on monte carlo radiation transport 
simulations using [TOPAS](https://www.google.com/search?channel=fs&client=ubuntu&q=topas+MC).

## Install and Requirements

To install: ```pip install TopasOpt```

- You require a working installation of [topas](https://topas.readthedocs.io/en/latest/getting-started/intro.html) to run the code.
- This code will only run on linux or mac (as will topas)
- python3.8 or greater is required.

## Usage and Documentation

Detailed documentation is provided [here](https://acrf-image-x-institute.github.io/TopasOpt/index.html)
The source code for the [worked examples](https://acrf-image-x-institute.github.io/TopasOpt/worked_examples.html) is inside the examples folder.

## Directory Structure

- **TopasOpt:** source code
- **examples:** source code for the [worked examples](https://acrf-image-x-institute.github.io/TopasOpt/worked_examples.html) provided in the docs
- **docsrc:** markdown/rst documentation.
- **tests:** tests which are run through github actions







