import sys
import os
import topas2numpy as tp
sys.path.append('../../TopasBayesOpt')
from WaterTankAnalyser import WaterTankData
from matplotlib import pyplot as plt


def ReadInTopasResults(ResultsLocation):
    path, file = os.path.split(ResultsLocation)
    Dose = WaterTankData(path, file)
    return Dose


def AnalyseTopasResults(TopasResults):
    pass

def CalculateObjectiveFunction(Metrics):
    pass

def TopasObjectiveFunction(ResultsLocation):
    TopasResults = ReadInTopasResults(ResultsLocation)
    Metrics = AnalyseTopasResults(ResultsLocation)
    OF = CalculateObjectiveFunction(Metrics)
    return OF

if __name__ == '__main__':
    TopasObjectiveFunction('/home/brendan/Dropbox (Sydney Uni)/Projects/PhaserSims/topas/MVLinac/Dose.bin')

