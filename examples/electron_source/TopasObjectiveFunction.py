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

    # define the points we want to collect our X profile at:
    Xpts = np.linspace(GroundTruthResults.x.min(), GroundTruthResults.x.max(), 100)  # profile over entire X range
    Ypts = np.zeros(Xpts.shape)	
    Zpts = 25 * np.ones(Xpts.shape)  # at the middle of the water tank

    OriginalProfileX = GroundTruthResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    OriginalProfileNormX = OriginalProfileX * 100 / OriginalProfileX.max()
    CurrentProfileX = TopasResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    CurrentProfileNormX = CurrentProfileX * 100 / CurrentProfileX.max()
    ProfileDifferenceX = OriginalProfileNormX - CurrentProfileNormX

    # define the points we want to collect our Y profile at:
    Ypts = np.linspace(GroundTruthResults.x.min(), GroundTruthResults.x.max(), 100)  # profile over entire Y range
    Xpts = np.zeros(Xpts.shape)
    Zpts = 25 * np.ones(Xpts.shape)  # at the middle of the water tank

    OriginalProfileY = GroundTruthResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    OriginalProfileNormY = OriginalProfileY * 100 / OriginalProfileY.max()
    CurrentProfileY = TopasResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    CurrentProfileNormY = CurrentProfileY * 100 / CurrentProfileY.max()
    ProfileDifferenceY = OriginalProfileNormY - CurrentProfileNormY

    # define the points we want to collect our DD at:
    Zpts = GroundTruthResults.z
    Xpts = np.zeros(Zpts.shape)
    Ypts = np.zeros(Zpts.shape)

    OriginalDepthDose = GroundTruthResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    CurrentDepthDose = TopasResults.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)
    OriginalDepthDoseNorm = OriginalDepthDose * 100 /np.max(OriginalDepthDose)
    CurrentDepthDoseNorm = CurrentDepthDose * 100 / np.max(CurrentDepthDose)
    DepthDoseDifference = OriginalDepthDoseNorm - CurrentDepthDoseNorm

    ObjectiveFunction = np.mean(abs(ProfileDifferenceX)) + np.mean(abs(ProfileDifferenceY)) + np.mean(abs(DepthDoseDifference))
    return ObjectiveFunction


def TopasObjectiveFunction(ResultsLocation, iteration):
    ResultsFile = ResultsLocation / f'WaterTank_itt_{iteration}.bin'
    path, file = os.path.split(ResultsFile)
    CurrentResults = WaterTankData(path, file)

    GroundTruthDataPath = str(Path(__file__).parent)
    # this assumes that you stored the base files in the same directory as this file, updated if needed
    GroundTruthDataFile = 'WaterTank.bin'
    GroundTruthResults = WaterTankData(GroundTruthDataPath, GroundTruthDataFile)

    OF = CalculateObjectiveFunction(CurrentResults, GroundTruthResults)
    return OF

