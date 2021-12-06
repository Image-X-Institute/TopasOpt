import sys
import os
sys.path.append('../../TopasBayesOpt')
from WaterTankAnalyser import WaterTankData
import numpy as np


def ReadInTopasResults(ResultsLocation):
    path, file = os.path.split(ResultsLocation)
    Dose = WaterTankData(path, file)  # WaterTank data is built on topas2numpy
    return Dose

def CalculateObjectiveFunction(TopasResults):
    """
    In this example, for metrics I am going to calculate the RMS error between the desired and actual
    profile and PDD.

    - I will use normalised values to account for the fact that there may be different numbers of particles
    - I will use
    """

    OriginalDataLoc = os.path.realpath('../SimpleCollimatorExample_TopasFiles/Results')
    File = 'WaterTank'
    OriginalResults = WaterTankData(OriginalDataLoc, File)

    OriginalDoseCube = OriginalResults.DoseCube
    CurrentDoseCube = TopasResults.DoseCube * 10  # Im going to explot the fact that i know how how many particles have been run in each case


    ObjectiveFunction = np.mean(np.abs(OriginalDoseCube - CurrentDoseCube))  # match to every point
    return ObjectiveFunction

def TopasObjectiveFunction(ResultsLocation, iteration):

    ResultsFile = ResultsLocation / f'WaterTank_itt_{iteration}.bin'
    TopasResults = ReadInTopasResults(ResultsFile)
    OF = CalculateObjectiveFunction(TopasResults)
    return OF

