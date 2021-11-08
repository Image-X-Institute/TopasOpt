import shutil
import sys, os
import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)
logging.Formatter('[%(filename)s: line %(lineno)d %(levelname)8s] %(message)s')


class CreateTopasScript:
    """
    This code will take a single topas script, and create a python function that will write it.
    """

    def __init__(self,OutputDirectory,TopasScriptLocation, RequiredIncludeFiles=None, IncludeFileStorageDirectory=None,
                 ErrorChecking = True):

        self.OutputDirectory = Path(OutputDirectory)
        self.TopasScriptLocation = TopasScriptLocation
        self.RequiredIncludeFiles = RequiredIncludeFiles

        if IncludeFileStorageDirectory is None:
            self.IncludeFileStorageDirectory = Path(OutputDirectory) / 'IncludeFiles'
            if not os.path.isdir(self.IncludeFileStorageDirectory):
                os.mkdir(self.IncludeFileStorageDirectory)
        else:
            self.IncludeFileStorageDirectory = IncludeFileStorageDirectory

        self.ErrorChecking = ErrorChecking
        if self.ErrorChecking:
            self.CheckInputs()
        self.GenerateTopasScriptGenerator()

    def CheckInputs(self):

        if not type(self.TopasScriptLocation) is list:
            self.TopasScriptLocation = [self.TopasScriptLocation]

        for script in self.TopasScriptLocation:
            if not os.path.isfile(script):
                logger.error(f'Could not find TopasScriptLocation at {script}. Quitting')
                sys.exit(1)

        if self.RequiredIncludeFiles is not None:
            if not type(self.RequiredIncludeFiles) == list:
                self.RequiredSupportFiles = list(self.RequiredIncludeFiles)
            for include_file in self.RequiredSupportFiles:
                if not os.path.isfile(include_file):
                    logger.error(f'Expected to find included file: {include_file} but its not there...quitting')
                    sys.exit(1)

        if not os.path.isdir(self.OutputDirectory):
            logger.error(f'Specified output directory does not exist: {self.OutputDirectory}')

        if not os.path.isdir(self.IncludeFileStorageDirectory):
            logger.error(f'IncludeFileStorageDirectory does not exist:\n{self.IncludeFileStorageDirectory}\nQuitting.')
            sys.exit(1)

    def HandleIncludeFiles(self, file, line):
        """
        check the file at self.TopasScriptLocation, and see if it has and include statements.
        If it does...what do we do?

        1. Update the path to be absolute - but this will break if the user chagnes to a different server
        2. Create a directory in the script location called support_files...yes, I think this correct...
        Returns:
        """

        # first, check that this include file exists... the user may have used a relative or an absolute path...
        # see if relative paths points to a file:
        FileLocation, dum = os.path.split(file)
        IncludeFileName = re.findall('(?<==).*$', line)[0] # extract the file name with regular expression
        IncludeFileName = IncludeFileName.replace(' ','')  # replace any spaces with strings
        if os.path.isfile(FileLocation + '/' + IncludeFileName):
            IncludeFileLocation = Path(FileLocation) / IncludeFileName
        elif os.path.isfile(IncludeFileName):  # check for use with absolute paths
            IncludeFileLocation = Path(FileLocation) / IncludeFileName
            dum, IncludeFileName = os.path.split(IncludeFileName)
        else:
            logger.error(f'could not find include file defined on this line:\n{line}\nQuitting')
            sys.exit(1)

        # assuming we found the file, we have to 1) copy it
        shutil.copy2(IncludeFileLocation, str(self.IncludeFileStorageDirectory) + '/' + IncludeFileName)
        # 2) check if it itself contains any include files! This happens recursively (this function calls itself)
        f = open(IncludeFileLocation)
        for i, include_file_line in enumerate(f):
            if 'includeFile'.lower() in include_file_line.lower():
                include_file_line = self.HandleIncludeFiles(file, include_file_line)

                # now we need to update this line in the copied script:
                copied_file_location = str(self.IncludeFileStorageDirectory) + '/' + IncludeFileName
                f2 = open(copied_file_location, 'r')
                old_lines = f2.readlines()
                old_lines[i] = 'includeFile = ' + include_file_line

        # 3) update the line to point to the new storage location.
        line = 'includeFile = ' + str(self.IncludeFileStorageDirectory) + '/' + IncludeFileName
        return line

    def GenerateTopasScriptGenerator(self):
        """
        generate a python script that will itself generate the script at TopasScriptLocation

        Returns:
        """

        outputFile = self.OutputDirectory / 'GenerateTopasScript.py'
        # first read in the text:

        TopasScriptGeneratorReadMe = '    """\n    This file simply returns a list object, where each list entry corresponds to' \
                                     '\n    a line in the topas script.\n    When it is called from an Optimiser object,' \
                                     'it will receive a dictionary that contains the current values of \n    ' \
                                     'the variables you set up in optimisation_params when you initialised the optimiser.\n    """\n'

        TopasScriptGenerator = []
        TopasScriptGenerator.append('def WriteTopasScript(**vars):\n')
        TopasScriptGenerator.append(TopasScriptGeneratorReadMe)

        ScriptNames = []
        ReturnStatementString = '['
        for file in self.TopasScriptLocation:
            dum, ScriptName = os.path.split(file)
            ScriptName, dum = os.path.splitext(ScriptName)
            ScriptName = ''.join(e for e in ScriptName if e.isalnum())  # heal any weird chracters
            ReturnStatementString = ReturnStatementString + ScriptName + ', '
            # setattr(self,ScriptName,[])
            f = open(file)
            TopasScriptGenerator.append('    \n')
            TopasScriptGenerator.append('    ' + ScriptName + ' = []\n')
            for line in f:
                line = line.replace('\n', '')
                if 'includeFile'.lower() in line.lower():
                    line = self.HandleIncludeFiles(file, line)
                if 'OutputFile '.lower() in line.lower():
                    print('hello')


                TopasScriptGenerator.append("    " + ScriptName + ".append('" + line + "')\n")

        ReturnStatementString = ReturnStatementString[:-2]  # remove the last comma
        ReturnStatementString = ReturnStatementString + ']'
        TopasScriptGenerator.append('\n    return ' + ReturnStatementString)
        f2 = open(outputFile, 'w+')
        for line in TopasScriptGenerator:
            f2.writelines(line)

if __name__ == '__main__':
    CreateTopasScript('.', '/home/brendan/topas37/examples/Basic/FlatteningFilter.txt')