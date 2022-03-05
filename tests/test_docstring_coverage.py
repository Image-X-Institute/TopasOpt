"""
This uses the 'interrogate' package to check docstring coverage.
The test will fail if there are any missing docstrings!
"""

from interrogate import coverage
from pathlib import Path
import os

def test_TopasOpt_docstrings_coverage():

    desired_coverage = 99
    this_directory = Path(__file__).parent
    TopasOpt_location = str(this_directory.parent / 'TopasOpt')
    assert os.path.isdir(TopasOpt_location)
    cov = coverage.InterrogateCoverage(paths=[TopasOpt_location], excluded=('__init__',))
    results = cov.get_coverage()
    if results.missing > 0:
        print(f'following files are missing docstrings. Run interrogate TopasOpt -vv from command line to see '
              f'a detailed summary')

    assert results.perc_covered >= desired_coverage