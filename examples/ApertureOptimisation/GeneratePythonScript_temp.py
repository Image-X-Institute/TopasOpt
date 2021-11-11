import sys
sys.path.append('../../TopasBayesOpt')
from TopasBayesOpt.CreateRunTopasScript import CreateTopasScript
from pathlib import Path

this_directory = Path(__file__).parent

# nb: the order is important to make sure that a phase space files are correctly classified
CreateTopasScript(this_directory, ['/home/brendan/python/TopasBayesOpt/examples/SimpleCollimatorExample_TopasFiles/SimpleCollimator.tps',
                                                  '/home/brendan/python/TopasBayesOpt/examples/SimpleCollimatorExample_TopasFiles/WaterTank.tps'])

