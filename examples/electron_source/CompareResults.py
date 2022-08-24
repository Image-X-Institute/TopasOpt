import sys
from pathlib import Path
sys.path.append(str(Path('../../TopasOpt').resolve()))
from TopasOpt.utilities import compare_multiple_results
from TopasOpt.utilities import WaterTankData
import numpy as np
from matplotlib

FilesToCompare = [r'WaterTank.bin',
                  r'Z:\PhaserSims\topas\electron_beam_test\Results\WaterTank_itt_164']

for file in FilesToCompare:
    WT = WaterTankData(file)
    Xpts = np.linspace(WT.x.min(), WT.x.max(), 100)  # profile over entire X range
    Ypts = np.zeros(Xpts.shape)
    Zpts = 25 * np.ones(Xpts.shape)  # at the middle of the water tank

    Profile = WT.ExtractDataFromDoseCube(Xpts, Ypts, Zpts)

