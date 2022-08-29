import sys
from pathlib import Path
from TopasOpt.utilities import compare_multiple_results
from TopasOpt.utilities import WaterTankData
import numpy as np
from matplotlib import pyplot as plt

FilesToCompare = [r'WaterTank.bin',
                  r'/home/brendan/GoliathHome/PhaserSims/topas/electron_beam_test/Results/WaterTank_itt_67']

compare_multiple_results(FilesToCompare)
