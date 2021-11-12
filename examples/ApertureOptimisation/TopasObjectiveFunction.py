import sys
import os
import topas2numpy as tp
sys.path.append('../../TopasBayesOpt')
from WaterTankAnalyser import WaterTankData
from matplotlib import pyplot as plt
import numpy as np
from pathlib import Path


def ReadInTopasResults(ResultsLocation):
    path, file = os.path.split(ResultsLocation)
    Dose = WaterTankData(path, file)  # WaterTank data is built on topas2numpy
    return Dose


def AnalyseTopasResults(TopasResults):
    """
    In this example, for metrics I am going to calculate the RMS error between the desired and actual
    profile and PDD.

    - I will use normalised values to account for the fact that there may be different numbers of particles
    - I will use
    """

    OriginalDataLoc = os.path.realpath('../SimpleCollimatorExample_TopasFiles/Results')
    File = 'WaterTank'
    OriginalResults = WaterTankData(OriginalDataLoc, File)

    # define the points we want to collect our profile at:
    Xpts = np.linspace(OriginalResults.x.min(), OriginalResults.x.max(), 100)  # profile over entire X range
    Ypts = np.zeros(Xpts.shape)
    Zpts = OriginalResults.PhantomSizeZ * np.ones(Xpts.shape)  # at the middle of the water tank

    OriginalProfile = OriginalResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    OriginalProfileNorm = OriginalProfile * 100 / OriginalProfile.max()

    CurrentProfile = TopasResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    CurrentProfileNorm = CurrentProfile * 100 / CurrentProfile.max()

    ProfileDiffere = OriginalProfileNorm - CurrentProfileNorm

    return 1

def CalculateObjectiveFunction(Metrics):
    pass

def TopasObjectiveFunction(ResultsLocation, iteration):

    ResultsFile = ResultsLocation / f'WaterTank_itt_{iteration}.bin'
    TopasResults = ReadInTopasResults(ResultsFile)
    Metrics = AnalyseTopasResults(TopasResults)
    # OF = CalculateObjectiveFunction(Metrics)
    return np.random.randn()

if __name__ == '__main__':
    TopasObjectiveFunction('/home/brendan/Dropbox (Sydney Uni)/Projects/PhaserSims/topas/MVLinac/Dose.bin')

