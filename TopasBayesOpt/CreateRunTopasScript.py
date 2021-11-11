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

    def HandleIncludeFileLine(self, OriginalFileLocation, line):
        """
        check the OriginalFileLocation at self.TopasScriptLocation, and see if it has and include statements.
        If it does...what do we do?

        1. Update the path to be absolute - but this will break if the user chagnes to a different server
        2. Create a directory in the script location called support_files...yes, I think this correct...
        Returns:
        """
        # first, check that this include file exists... the user may have used a relative or an absolute path...
        # see if relative paths points to a OriginalFileLocation:
        FileLocation, dum = os.path.split(OriginalFileLocation)
        IncludeFileName = re.findall('(?<==).*$', line)[0] # extract the file name with regular expression
        IncludeFileName = IncludeFileName.replace(' ','')  # replace any spaces with strings
        if os.path.isfile(FileLocation + '/' + IncludeFileName):
            IncludeFileLocation = Path(FileLocation) / IncludeFileName
        elif os.path.isfile(IncludeFileName):  # check for use with absolute paths
            IncludeFileLocation = Path(FileLocation) / IncludeFileName
            dum, IncludeFileName = os.path.split(IncludeFileName)
        else:
            logger.error(f'could not find include file defined on this line:\n{line}'
                         f'\nSearched locations:'
                         f'\n{FileLocation + "/" + IncludeFileName}'
                         f'\n{IncludeFileName}'
                         f'\nQuitting')
            sys.exit(1)

        # assuming we found the file, we have to 1) copy it
        shutil.copy2(IncludeFileLocation, str(self.IncludeFileStorageDirectory) + '/' + IncludeFileName)
        # 2) check if it itself contains any include files! This happens recursively (this function calls itself)
        f = open(IncludeFileLocation)
        for i, include_file_line in enumerate(f):
            if 'includeFile'.lower() in include_file_line.lower():
                include_OriginalFileLocation_line = self.HandleIncludeFileLine(OriginalFileLocation, include_file_line)

                # now we need to update this line in the copied script:
                copied_file_location = str(self.IncludeFileStorageDirectory) + '/' + IncludeFileName
                f2 = open(copied_file_location, 'r')
                old_lines = f2.readlines()
                old_lines[i] = 'includeFile = ' + include_file_line

        # 3) update the line to point to the new storage location.
        line = 'includeFile = ' + str(self.IncludeFileStorageDirectory) + '/' + IncludeFileName

        return line

    def HandleOutputFileLine(self, line):
        """
        If a file is being output, change the location it is being output to
        BaseDirectory / Results.
        Change the name of the output to reflect the iteration number.

        Args:
            line: the OutputFile line from the original

        Returns:
            line: the line adapted to output a file name to BaseDirectory / Results, and with the relevat iteration
                  appended

        """
        line1, line2 = line.split("=", 1)  # delete everything after the first =
        dum, OriginalFileName = line2.split("/", 1)
        OriginalFileName = OriginalFileName.replace('"', '')
        OriginalFileName = OriginalFileName.replace("'", '')
        line1 = line1.replace('"', '')
        line1 = line1.replace("'", '')
        new_line = line1 + ' =  ../Results/' + OriginalFileName + "_itt_\' + " + 'str(iteration)' + ')'

        return new_line, OriginalFileName

    def HandlePhaseSpaceSource(self, line, OutputPhaseSpaceFilesNames):
        """
        Handle lines where a phase space source is used

        For phase space sources, there are two scenarios:
        1. A static phase space source is used; in this case we just want to update

        Args:
            line:
            OutputPhaseSpaceFilesNames:

        Returns:

        """
        # check whether this is a dynamic or static phase space source
        UseStaticPhaseSpace = True
        for OutputPhaseSpace in OutputPhaseSpaceFilesNames:
            if OutputPhaseSpace in line:
                UseStaticPhaseSpace = False

        line1, line2 = line.split("=", 1)  # delete everything after the first =
        dum, OriginalFileName = line2.split("/", 1)
        OriginalFileName = OriginalFileName.replace('"', '')
        OriginalFileName = OriginalFileName.replace("'", '')
        line1 = line1.replace('"', '')
        line1 = line1.replace("'", '')
        if not UseStaticPhaseSpace:
            # dynamically allocated phase space name
            # new_line = line1 + ' = "\' + str(Path(BaseDirectory) / "Results" / "' + OriginalFileName + '") + "_itt" + ' + 'str(iteration)' + ' + \'"\')'
            new_line = line1 + ' =  ../Results/' + OriginalFileName + "_itt_\' + " + 'str(iteration)' + ')'
        else:
            # in this case we want to convert a relative path to an absolute path.
            # do we also want to copy the file to the IncludeDirectory? probably not, it could be huge...
            logger.warning('not coded yet :-P')  #ToDo
            pass

        return new_line

    def GenerateTopasScriptGenerator(self):
        """
        generate a python script that will itself generate the script at TopasScriptLocation

        Returns:
        """
        outputFile = self.OutputDirectory / 'GenerateTopasScripts.py'
        # first read in the text:

        TopasScriptGeneratorReadMe = '    """\n    This file simply returns a list object, where each list entry corresponds to' \
                                     '\n    a line in the topas script.\n    When it is called from an Optimiser object,' \
                                     'it will receive a dictionary that contains the current values of \n    ' \
                                     'the variables you set up in optimisation_params when you initialised the optimiser.\n    """\n'

        TopasScriptGenerator = []
        TopasScriptGenerator.append('from pathlib import Path\n')
        TopasScriptGenerator.append('\n')
        TopasScriptGenerator.append('def GenerateTopasScripts(BaseDirectory, iteration, **vars):\n')
        TopasScriptGenerator.append(TopasScriptGeneratorReadMe)

        ScriptNames = []
        ReturnStatementString = '['
        OutputPhaseSpaceFilesNames = []  # need to keep track of these to see if they match the input of another file
        for file in self.TopasScriptLocation:
            dum, ScriptName = os.path.split(file)
            ScriptName, dum = os.path.splitext(ScriptName)
            ScriptName = ''.join(e for e in ScriptName if e.isalnum())  # heal any weird chracters
            ReturnStatementString = ReturnStatementString + ScriptName + ', '
            f = open(file)
            TopasScriptGenerator.append('    \n')
            TopasScriptGenerator.append('    ' + ScriptName + ' = []\n')

            for line in f:
                line = line.replace('\n', '')  # remove new line characters
                CommentLine = False
                if (not line == '') and line.lstrip()[0] == '#':
                    CommentLine = True

                if not CommentLine:  # avoid doing anything silly to commented lines
                    line = line.split('#', 1)
                    line = line[0]  # i'm going to remove inline comments, easier and safer.
                    if 'includeFile'.lower() in line.lower():
                        line = self.HandleIncludeFileLine(file, line)
                    if 'OutputFile '.lower() in line.lower():
                        line, OriginalFileName = self.HandleOutputFileLine(line)
                        TopasScriptGenerator.append("    " + ScriptName + ".append('" + line + "\n")
                        OutputPhaseSpaceFilesNames.append(OriginalFileName)
                        continue  # need a slightly different line in this case from the default
                    if 'PhaseSpaceFileName'.lower() in line.lower():  # could put a more sophisticated test here...
                        line = self.HandlePhaseSpaceSource(line, OutputPhaseSpaceFilesNames)
                        TopasScriptGenerator.append("    " + ScriptName + ".append('" + line + "\n")
                        continue  # need a slightly different line in this case from the default

                TopasScriptGenerator.append("    " + ScriptName + ".append('" + line + "')\n")

        ReturnStatementString = ReturnStatementString[:-2]  # remove the last comma
        ReturnStatementString = ReturnStatementString + ']'
        TopasScriptGenerator.append('\n    return ' + ReturnStatementString)
        f2 = open(outputFile, 'w+')
        for line in TopasScriptGenerator:
            f2.writelines(line)

