"""
Supporting classes and functions
"""
from bayes_opt.logger import JSONLogger


class bcolors:
    """
    This is just here to enable me to print pretty colors to the linux terminal
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class FigureSpecs:
    """
    Thought this might be the easiest way to ensure universal parameters accross all figures
    """
    LabelFontSize = 14
    TitleFontSize = 16
    Font = 'serif'
    AxisFontSize = 14


class newJSONLogger(JSONLogger):
    """
    To avoid the annoying behaviour where the bayesian logs get deleted on restart.
    Thanks to: https://github.com/fmfn/BayesianOptimization/issues/159
    """
    def __init__(self, path):
        self._path = None
        super(JSONLogger, self).__init__()
        self._path = path if path[-5:] == ".json" else path + ".json"


def import_from_absolute_path(fullpath, global_name=None):
    """
    Dynamic script import using full path.
    This is required to enable mapping to the location of the script generation function and the objective funciton,
    which are not known in advance.
    (credit here)[https://stackoverflow.com/questions/3137731/is-this-correct-way-to-import-python-scripts-residing-in-arbitrary-folders]
    """
    import os
    import sys

    script_dir, filename = os.path.split(fullpath)
    script, ext = os.path.splitext(filename)

    sys.path.insert(0, script_dir)
    try:
        module = __import__(script)
        if global_name is None:
            global_name = script
        globals()[global_name] = module
        sys.modules[global_name] = module
    finally:
        del sys.path[0]


