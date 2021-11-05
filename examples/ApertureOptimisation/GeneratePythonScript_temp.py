import sys
sys.path.append('../../TopasBayesOpt')
from TopasBayesOpt.CreateRunTopasScript import CreateTopasScript
from pathlib import Path

this_directory = Path(__file__).parent
topas_script = CreateTopasScript(this_directory, '/home/brendan/topas37/examples/Basic/FlatteningFilter.txt')