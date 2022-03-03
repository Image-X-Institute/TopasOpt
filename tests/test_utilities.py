"""
Test the classes and functions in utiltiies

I can't test most of them because they involve a plot, which blocks the test runer
Nevertheless, I actually think many of these functions are reasonably well covered by the test_optimsers
integration tests
"""

import sys
from pathlib import Path
sys.path.insert(0, '../TopasOpt')
import numpy as np
from TopasOpt.utilities import WaterTankData, ReadInLogFile, PlotLogFile, compare_multiple_results

def test_WaterTankData():
    """
    Not sure how to test plotting methods without causing a blocking call...
    """
    ResultsLocation = str(Path('../examples/SimpleCollimatorExample_TopasFiles/Results').resolve())
    WT = WaterTankData(ResultsLocation, 'WaterTank.bin')
    
    # Extract some data
    Xpts_prof = WT.x  # profile over entire X range
    Ypts_prof = np.zeros(Xpts_prof.shape)
    Zpts_prof = WT.PhantomSizeZ * np.ones(Xpts_prof.shape)  # at the middle of the water tank
    WT.ProfileDose_X = WT.ExtractDataFromDoseCube(Xpts_prof, Ypts_prof, Zpts_prof)


    
