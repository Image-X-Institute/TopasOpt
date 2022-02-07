import sys
sys.path.append('../../TopasOpt')
from TopasOpt.GenerateTopasScriptGenerator import CreateTopasScriptGenerator
from pathlib import Path

this_directory = Path(__file__).parent

# nb: the order is important to make sure that a phase space files are correctly classified
GenerateTopasScriptGenerator(this_directory, ['../SimpleCollimatorExample_TopasFiles/SimpleCollimator.tps',
                                                  '../SimpleCollimatorExample_TopasFiles/WaterTank.tps'])

