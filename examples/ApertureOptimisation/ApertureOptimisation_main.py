import sys
import os
import numpy as np
from pathlib import Path
sys.path.append('../../TopasBayesOpt')
from TopasBayesOpt import TopasBayesOpt as to


BaseDirectory = os.path.expanduser("~") + '/Dropbox (Sydney Uni)/Projects/PhaserSims/topas'
SimulationName = 'BayesianOptimisationTest'
OptimisationDirectory = Path(__file__).parent

# set up optimisation params:
optimisation_params = {}
optimisation_params['ParameterNames'] = ['SomeVariable']
optimisation_params['start_point'] = np.array([1])
optimisation_params['UpperBounds'] = np.array([2])
optimisation_params['LowerBounds'] = np.array([0.5])
optimisation_params['Nitterations'] = 10
# optimisation_params['Suggestions'] = np.array([[1.1],[1.2]])
ReadMeText = 'This is a public service announcement, this is only a test'

ShellScriptHeader = '# !/bin/bash\n\n# This script sets up the topas environment then runs all listed files' \
                    '\n\n# ensure that any errors cause the script to stop executing:' \
                    '\nset - e\n\n' \
                    'export TOPAS_G4_DATA_DIR=~/G4Data' \
                    '\nmodule unload gcc >/dev/null 2>&1  # will fail on non artemis systems, output is surpressed' \
                    '\nmodule load gcc/9.1.0 >/dev/null 2>&1\n\n'

Optimiser = to.BayesianOptimiser(optimisation_params, BaseDirectory, SimulationName, OptimisationDirectory,
                                 TopasLocation='~/topas37', ReadMeText=ReadMeText, ShellScriptHeader=ShellScriptHeader,
                                 Overwrite=True)
Optimiser.RunOptimisation()