import sys
import os
import topas2numpy as tp
sys.path.append('../../TopasBayesOpt')
from WaterTankAnalyser import WaterTankData
from matplotlib import pyplot as plt

path, file = os.path.split('/home/brendan/python/TopasBayesOpt/examples/SimpleCollimatorExample_TopasFiles/Results/WaterTank.bin')
Dose = WaterTankData(path, file)
Dose.Plot_DosePlanes()
Dose.Plot_Profiles()
Dose.Plot_DepthDose()