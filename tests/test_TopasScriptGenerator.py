"""
This tests topas script generator
This is actually a very difficult code to test automatically, since what it does
is take generate a code which, when run will generate a script that would be sent to Topas.

I'm not sure how to really test this functionality automatically, but what we can test easily is
that it runs without error, and that is what we do.
"""
import sys
from pathlib import Path
this_dir = Path(__file__).parent
sys.path.insert(0, str(this_dir.parent))
from TopasOpt.TopasScriptGenerator import generate_topas_script_generator
from pathlib import Path

def test_topas_script_generator():
    this_directory = Path(__file__).parent

    # we will use the files from our examples directory as a test
    Input_files = [this_directory.parent / 'docsrc' / '_resources' / 'SimpleCollimator.tps',
                   this_directory.parent / 'docsrc' / '_resources' / 'WaterTank.tps']


    generate_topas_script_generator(this_directory, Input_files)
