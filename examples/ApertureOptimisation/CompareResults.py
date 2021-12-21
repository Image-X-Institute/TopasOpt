import sys
import os
sys.path.append('../../TopasBayesOpt')
from WaterTankAnalyser import WaterTankData
import numpy as np
from pathlib import Path
from matplotlib import pyplot as plt

GroundTruthDir = '../SimpleCollimatorExample_TopasFiles/Results/'
GroundTruthFile = 'WaterTank.bin'
GroundTruthData = WaterTankData(GroundTruthDir, GroundTruthFile)

OptimisationDir = '/home/brendan/Dropbox (Sydney Uni)/Projects/PhaserSims/topas/NM_OptimisationTest/Results/'
OptimisationFile = 'WaterTank_itt_40.bin'
OptimisationData = WaterTankData(OptimisationDir, OptimisationFile)

# extract profiles:
Xpts_prof = np.linspace(GroundTruthData.x.min(), GroundTruthData.x.max(), 100)  # profile over entire X range
Ypts_prof = np.zeros(Xpts_prof.shape)
Zpts_prof = GroundTruthData.PhantomSizeZ * np.ones(Xpts_prof.shape)  # at the middle of the water tank
GroundTruthProfile = GroundTruthData.ExtractDataFromDoseCube(Xpts_prof, Ypts_prof, Zpts_prof)
GroundTruthProfile = GroundTruthProfile * 100 / GroundTruthProfile.max()  # normalise
OptimisedProfile = OptimisationData.ExtractDataFromDoseCube(Xpts_prof, Ypts_prof, Zpts_prof)
OptimisedProfile = OptimisedProfile * 100 / OptimisedProfile.max()  # normalise

# extract depth dose:
Zpts_dd = GroundTruthData.z
Xpts_dd = np.zeros(Zpts_dd.shape)
Ypts_dd = np.zeros(Zpts_dd.shape)

GroundTruthDD = GroundTruthData.ExtractDataFromDoseCube(Xpts_dd, Ypts_dd, Zpts_dd)
GroundTruthDD = GroundTruthDD * 100 / np.max(GroundTruthDD)  # normalise
OptimisedDD = OptimisationData.ExtractDataFromDoseCube(Xpts_dd, Ypts_dd, Zpts_dd)
OptimisedDD = OptimisedDD * 100 / np.max(OptimisedDD)  # normalise

# plot the differences:
fig, axs = plt.subplots(ncols=2, nrows=1, figsize=[10, 5])
axs[0].plot(Xpts_prof, GroundTruthProfile)
axs[0].plot(Xpts_prof, OptimisedProfile)
axs[0].grid()
axs[0].set_xlabel('X [mm]')
axs[0].set_ylabel('Dose (%)')
axs[0].legend(['Ground Truth', 'Optimised'])

axs[1].plot(Zpts_dd, np.flip(GroundTruthDD))  # nb flip is just to it goes in conventional LR direction
axs[1].plot(Zpts_dd, np.flip(OptimisedDD))
axs[1].set_xlabel('Z [mm]')
axs[1].set_ylabel('Dose [%]')
axs[1].grid()
axs[1].legend(['Ground Truth', 'Optimised'])


plt.show()









