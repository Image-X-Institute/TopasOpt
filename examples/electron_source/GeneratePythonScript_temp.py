import sys
sys.path.append('../../TopasOpt')
from TopasOpt.TopasScriptGenerator import generate_topas_script_generator
from pathlib import Path

this_directory = Path(__file__).parent

# nb: the order is important to make sure that a phase space files are correctly classified
generate_topas_script_generator(this_directory, ['SimpleBeam.tps'])

