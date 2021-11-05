import sys, os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
logging.Formatter('[%(filename)s: line %(lineno)d %(levelname)8s] %(message)s')


class CreateTopasScript:
    """
    This code will take a single topas script, and create a python function that will write it.
    """

    def __init__(self,OutputDirectory,TopasScriptLocation, RequiredIncludeFiles=None, IncludeFilePath=None):

        self.OutputDirectory = Path(OutputDirectory)
        self.TopasScriptLocation = TopasScriptLocation
        self.RequiredIncludeFiles = RequiredIncludeFiles
        self.FindIncludeFiles()
        self.CheckInputs()

        self.GenerateTopasScriptGenerator()

    def CheckInputs(self):

        if not os.path.isfile(self.TopasScriptLocation):
            logger.error(f'Could not find TopasScriptLocation at {self.TopasScriptLocation}')

        if self.RequiredIncludeFiles is not None:
            if not type(self.RequiredIncludeFiles) == list:
                self.RequiredSupportFiles = list(self.RequiredIncludeFiles)
            for include_file in self.RequiredSupportFiles:
                if not os.path.isfile(include_file):
                    logger.error(f'Expected to find included file {include_file} at {include_file}'
                                 f' but its not there...quitting')
                    sys.exit(1)

        if not os.path.isdir(self.OutputDirectory):
            logger.error(f'Specified output directory does not exist: {self.OutputDirectory}')

    def FindIncludeFiles(self):
        """
        check the file at self.TopasScriptLocation, and see if it has and include statements.
        If it does...what do we do?

        1. Update the path to be absolute - but this will break if the user chagnes to a different server
        2. Create a directory in the script location called support_files...yes, I think this correct...
        Returns:
        """
        pass

    def GenerateTopasScriptGenerator(self):
        """
        generate a python script that will itself generate the script at TopasScriptLocation

        Returns:
        """

        outputFile = self.OutputDirectory / 'GenerateTopasScript.py'
        # first read in the text:
        f = open(self.TopasScriptLocation)
        TopasScriptGeneratorReadMe = '    """\n    This file simply returns a list object, where each list entry corresponds to' \
                                     '\n    a line in the topas script.\n    When it is called from an Optimiser object,' \
                                     'it will receive a dictionary that contains the current values of \n    ' \
                                     'the variables you set up in optimisation_params when you initialised the optimiser.\n    """\n\n'

        TopasScriptGenerator = []
        TopasScriptGenerator.append('def WriteTopasScript(**vars):\n')
        TopasScriptGenerator.append(TopasScriptGeneratorReadMe)
        TopasScriptGenerator.append('    TopasScript = []\n')
        for line in f:
            line = line.replace('\n', '')
            TopasScriptGenerator.append("    TopasScript.append('" + line + "')\n")
        TopasScriptGenerator.append('\n    return TopasScript')

        f2 = open(outputFile, 'w+')
        for line in TopasScriptGenerator:
            f2.writelines(line)


    def CopyIncludeFiles(self):

        pass

if __name__ == '__main__':
    CreateTopasScript('.', '/home/brendan/topas37/examples/Basic/FlatteningFilter.txt')