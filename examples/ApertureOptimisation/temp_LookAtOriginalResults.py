import sys
import os
sys.path.append('../../TopasBayesOpt')
from WaterTankAnalyser import WaterTankData
from matplotlib import pyplot as plt

path, file = os.path.split('/home/brendan/Dropbox (Sydney Uni)/Projects/PhaserSims/topas/BayesianOptimisationTest/Results/WaterTank_itt_7.bin')
Dose = WaterTankData(path, file)
Dose.Plot_DosePlanes()
Dose.Plot_Profiles()
Dose.Plot_DepthDose()