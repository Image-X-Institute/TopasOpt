import sys
sys.path.append('../../TopasBayesOpt')
from TopasBayesOpt.CreateRunTopasScript import CreateTopasScript
from pathlib import Path

this_directory = Path(__file__).parent
topas_script = CreateTopasScript(this_directory, ['/home/brendan/python/TopasBayesOpt/examples/SimpleCollimatorExample_TopasFiles/SimpleCollimator.tps',
                                                  '/home/brendan/python/TopasBayesOpt/examples/SimpleCollimatorExample_TopasFiles/WaterTank.tps'])

