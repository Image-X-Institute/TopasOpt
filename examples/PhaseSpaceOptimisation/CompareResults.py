import sys
from pathlib import Path
sys.path.append(str(Path('../../TopasOpt').resolve()))
from TopasOpt.WaterTankAnalyser import compare_multiple_results

FilesToCompare = ['C:/Users/bwhe3635/Dropbox (Sydney Uni)/Projects/PhaserSims/topas/PhaseSpaceOptimisationTest/Results/WaterTank_itt_95.bin',
                  'C:/Users/bwhe3635/Dropbox (Sydney Uni)/Projects/TopasOpt/examples/SimpleCollimatorExample_TopasFiles/Results/WaterTank.bin']


compare_multiple_results(FilesToCompare, abs_dose=False)







