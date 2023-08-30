# TopasOpt

![](docsrc/_resources/interrogate_badge.svg) [![codecov](https://codecov.io/gh/Image-X-Institute/TopasOpt/graph/badge.svg?token=0FSEO19LCD)](https://codecov.io/gh/Image-X-Institute/TopasOpt)![test](https://github.com/ACRF-Image-X-Institute/TopasOpt/actions/workflows/run_tests.yml/badge.svg) ![docs](https://github.com/ACRF-Image-X-Institute/TopasOpt/actions/workflows/build-docs.yml/badge.svg)[![PyPI version](https://badge.fury.io/py/TopasOpt.svg)](https://badge.fury.io/py/TopasOpt)


This code provides a framework for performing optimisation on monte carlo radiation transport 
simulations using [TOPAS](https://www.google.com/search?channel=fs&client=ubuntu&q=topas+MC).

## Install and Requirements

To install: ```pip install TopasOpt```

- You require a working installation of [topas](https://topas.readthedocs.io/en/latest/getting-started/intro.html) to run the code.
- This code will only run on linux or mac (as will topas)
- python3.8 or greater is required.

## Usage and Documentation

Detailed documentation is provided [here](https://image-x-institute.github.io/TopasOpt/)
The source code for the [worked examples](https://image-x-institute.github.io/TopasOpt/worked_examples.html) is inside the examples folder.

## Directory Structure

- **TopasOpt:** source code
- **examples:** source code for the [worked examples](https://image-x-institute.github.io/TopasOpt/worked_examples.html) provided in the docs
- **docsrc:** markdown/rst documentation.
- **tests:** tests which are run through github actions

## Citation

This code is described in [this paper](https://aapm.onlinelibrary.wiley.com/doi/10.1002/mp.16126).
If you use this code in your work, please cite this paper!

```bibtex

@article{whelan_topasopt_2022,
	title = {{TopasOpt}: {An} open-source library for optimization with {Topas} {Monte} {Carlo}},
	shorttitle = {{TopasOpt}},
	journal = {Medical Physics},
	author = {Whelan, Brendan and Loo Jr, Billy W. and Wang, Jinghui and Keall, Paul},
	year = {2022},
	note = {Publisher: Wiley Online Library},
}

```






