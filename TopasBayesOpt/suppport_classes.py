
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
