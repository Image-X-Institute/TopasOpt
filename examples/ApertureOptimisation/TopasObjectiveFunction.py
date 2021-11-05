import topas2numpy as tp


def ReadInTopasResults():
    pass

def AnalyseTopasResults():
    pass

def CalculateObjectiveFunction():
    pass

def TopasObjectiveFunction(ResultsLocation):
    TopasResults = ReadInTopasResults(ResultsLocation)
    AnalyseTopasResults(ResultsLocation)
    OF = CalculateObjectiveFunction()
    return OF

