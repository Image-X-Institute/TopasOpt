import os
from TopasOpt.utilities import WaterTankData
import numpy as np
from pathlib import Path

def CalculateObjectiveFunction(TopasResults, GroundTruthResults):
    """
    In this example, for metrics I am going to calculate the RMS error between the desired and actual
    profile and PDD. I will use normalised values to account for the fact that there may be different numbers of
    particles used between the different simulations
    """

    # define the points we want to collect our profile at:
    Xpts = np.linspace(GroundTruthResults.x.min(), GroundTruthResults.x.max(), 100)  # profile over entire X range
    Ypts = np.zeros(Xpts.shape)
    Zpts = GroundTruthResults.PhantomSizeZ * np.ones(Xpts.shape)  # at the middle of the water tank

    OriginalProfile = GroundTruthResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    OriginalProfileNorm = OriginalProfile * 100 / OriginalProfile.max()
    CurrentProfile = TopasResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    CurrentProfileNorm = CurrentProfile * 100 / CurrentProfile.max()
    ProfileDifference = OriginalProfileNorm - CurrentProfileNorm

    # define the points we want to collect our DD at:
    Zpts = GroundTruthResults.z
    Xpts = np.zeros(Zpts.shape)
    Ypts = np.zeros(Zpts.shape)

    OriginalDepthDose = GroundTruthResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    CurrentDepthDose = TopasResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    OriginalDepthDoseNorm = OriginalDepthDose * 100 /np.max(OriginalDepthDose)
    CurrentDepthDoseNorm = CurrentDepthDose * 100 / np.max(CurrentDepthDose)
    DepthDoseDifference = OriginalDepthDoseNorm - CurrentDepthDoseNorm

    ObjectiveFunction = np.mean(abs(ProfileDifference)) + np.mean(abs(DepthDoseDifference))
    return np.log(ObjectiveFunction)


def TopasObjectiveFunction(ResultsLocation, iteration):
    ResultsFile = ResultsLocation / f'WaterTank_itt_{iteration}.bin'
    path, file = os.path.split(ResultsFile)
    CurrentResults = WaterTankData(path, file)

    GroundTruthDataPath = str(Path(__file__).parent / 'SimpleCollimatorExample_TopasFiles' / 'Results')
    # this assumes that you stored the base files in the same directory as this file, updated if needed
    GroundTruthDataFile = 'WaterTank.bin'
    GroundTruthResults = WaterTankData(GroundTruthDataPath, GroundTruthDataFile)

    OF = CalculateObjectiveFunction(CurrentResults, GroundTruthResults)
    return OF

