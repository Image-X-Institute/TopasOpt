"""
This tests topas script generator
This is actually a very difficult code to test automatically, since what it does
is take generate a code which, when run will generate a script that would be sent to Topas.

I'm not sure how to really test this functionality automatically, but what we can test easily is
that it runs without error, and outputs the expected files, and that is what we do.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path('../').resolve()))
from TopasOpt.TopasScriptGenerator import generate_topas_script_generator
from pathlib import Path

def test_topas_script_generator():
    this_directory = Path(__file__).parent

    # we will use the files from our examples directory as a test
    Input_files = [Path('../examples/SimpleCollimatorExample_TopasFiles/SimpleCollimator.tps').resolve(),
                   Path('../examples/SimpleCollimatorExample_TopasFiles/WaterTank.tps').resolve()]

    generate_topas_script_generator(this_directory, Input_files)