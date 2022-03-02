.. Template documentation master file, created by
   sphinx-quickstart on Tue May 12 15:57:47 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Bayesian Optimisation for Topas
===============================

This repository integrates the open source bayesian optimisation code `Bayesian Optimisation <https://github.com/fmfn/BayesianOptimization>`_ with the monte carlo radiation transport code `TopasMC <http://www.topasmc.org/>`_, hence enabling users to apply the power of formal mathematical optimisation with the well established use cases for monte carlo modelling.

To install:

```python
pip install TopasOpt
```

For help getting an appropriate environment set up, see `here <https://acrf-image-x-institute.github.io/TopasOpt/EnvironmentSetup.html>`_

The quickest way to get started is to go through the worked examples.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   /worked_examples
   /next_steps.md
   /convergence_criteria.md
   /designing_objective_functions.md
   /EnvironmentSetup.md
   /code_docs

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
