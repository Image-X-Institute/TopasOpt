import sys
import os
sys.path.append('../../TopasBayesOpt')
import sys
from pathlib import Path
sys.path.append(str(Path('../../TopasBayesOpt').resolve()))
from WaterTankAnalyser import compare_multiple_results

GroundTruthDir = '../SimpleCollimatorExample_TopasFiles/Results/'
GroundTruthFile = 'WaterTank.bin'


OptimisationDir = '/home/brendan/Dropbox (Sydney Uni)/Projects/PhaserSims/topas/NM_OptimisationTest/Results/'
OptimisationFile = 'WaterTank_itt_40.bin'
OptimisationData = WaterTankData(OptimisationDir, OptimisationFile)



FilesToCompare = ['C:/Users/bwhe3635/Dropbox (Sydney Uni)/Projects/PhaserSims/topas/PhaseSpaceOptimisationTest/Results/WaterTank_itt_99.bin',
                  'C:/Users/bwhe3635/Dropbox (Sydney Uni)/Projects/TopasBayesOpt/examples/SimpleCollimatorExample_TopasFiles/Results/WaterTank.bin']


compare_multiple_results(FilesToCompare, abs_dose=False)









