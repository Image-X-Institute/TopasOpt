"""
Convert topas parameter files into a python function that recreates the input files.
"""
import shutil
import sys, os
import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)
logging.Formatter('[%(filename)s: line %(lineno)d %(levelname)8s] %(message)s')


class generate_topas_script_generator:
    """
    This code will take a list topas scripts, and create a python function that returns a list for each script.
    Each list element contains one line of the topas script, which can be used to automatically regenerate that script.
    This class will also attempt to handle input/output lines in the topas language such as include lines and input
    and output of phase space lines.

    :param OutputDirectory: location to write the returned python function to
    :type OutputDirectory: string or pathlib.Path
    :param TopasScriptLocation: location of all topas scripts which need to be recreated. Note that you do not need
        to enter 'include' files, as these are found automatically. You only need to enter files which will be
        changing on each iteration. The order of the files must match the order in which they will be run so the
        code can correctly detect dynamic input/output files.
    :type TopasScriptLocation: string or pathlib.Path
    :param IncludeFileStorageDirectory: Any included files will be copied here. This is to try and ensure the topas
        scripts are portable. If no path is entered then they will be written to OutputDirectory / IncludeFiles
    :type IncludeFileStorageDirectory: None or string or pathlib.Path (optional)
    :param ErrorChecking: if True (recommended), will attempt to perform some checks on the input data.
    :type ErrorChecking: bool, optional
    """

    def __init__(self,OutputDirectory, TopasScriptLocation, IncludeFileStorageDirectory=None,
                 ErrorChecking=True):
        """
        init method TopasScriptGenerator. input options are in class docstring
        """

        self.OutputDirectory = Path(OutputDirectory)
        self.TopasScriptLocation = TopasScriptLocation


        if IncludeFileStorageDirectory is None:
            self.IncludeFileStorageDirectory = Path(OutputDirectory) / 'IncludeFiles'

        else:
            self.IncludeFileStorageDirectory = IncludeFileStorageDirectory

        self.ErrorChecking = ErrorChecking
        if self.ErrorChecking:
            self._check_inputs()
        self._generate_topas_script_generator()

    def _check_inputs(self):
        """
        Perform checks of input data.
        these tests should be updated as uncaught errors arise!
        """

        if not type(self.TopasScriptLocation) is list:
            self.TopasScriptLocation = [self.TopasScriptLocation]

        for script in self.TopasScriptLocation:
            if not os.path.isfile(script):
                logger.error(f'Could not find TopasScriptLocation at {script}. Quitting')
                sys.exit(1)

        if not os.path.isdir(self.OutputDirectory):
            logger.error(f'Specified output directory does not exist: {self.OutputDirectory}')

    def _handle_include_files(self, OriginalFileLocation, line):
        """
        This function is called when an includeFile statement is found in the input topas script.
        The include file will be copied to  IncludeFileStorageDirectory, and the line updated with an
        absolute path to that location

        Returns: line, the updated includeFile line
        """
        # first, check that this include file exists... the user may have used a relative or an absolute path...
        # see if relative paths points to a OriginalFileLocation:
        if not os.path.isdir(self.IncludeFileStorageDirectory):
            os.mkdir(self.IncludeFileStorageDirectory)
        FileLocation, dum = os.path.split(OriginalFileLocation)
        IncludeFileNames = re.findall('(?<==).*$', line)[0] # extract the file name with regular expression
        IncludeFileNames = IncludeFileNames.split('#')[0]  # ignore anything after a comment symbol
        IncludeFileNames = IncludeFileNames.split(' ')
        line = 'includeFile = '
        for IncludeFileName in IncludeFileNames:  # have to handle the potential for multiple include files on one line
            if IncludeFileName == '' or IncludeFileName == '\n':
                continue
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
                    if not include_file_line.lstrip()[0] == '#':  # ignore comments
                        # extract everything on the RHS of the equals sign:
                        RHS = include_file_line.lstrip().split('=')[1]
                        RHS = RHS.split('#')[0]  #remove anything after a comment symbol
                        AllIncludeFiles = RHS.split(' ')
                        new_include_file_line = 'includeFile = '
                        for j, file in enumerate(AllIncludeFiles):
                            if file == '' or file =='\n':
                                continue
                            temp_include_file_line = 'includeFile = ' + file
                            include_OriginalFileLocation_line = self._handle_include_files(IncludeFileLocation, temp_include_file_line)
                            new_include_file_line = new_include_file_line + os.path.split(self.IncludeFileStorageDirectory)[1] + '/' + file + ' '
                        if AllIncludeFiles[-1] == '\n':
                            new_include_file_line = new_include_file_line + '\n'
                        # now we need to update this line in the copied script:
                        copied_file_location = str(self.IncludeFileStorageDirectory) + '/' + IncludeFileName
                        f2 = open(copied_file_location, 'r')
                        old_lines = f2.readlines()
                        new_lines = old_lines.copy()
                        new_lines[i] = new_include_file_line
                        f2 = open(copied_file_location, 'w')
                        f2.writelines(new_lines)

            # 3) update the line to point to the new storage location.
            line = line + ' ' + os.path.split(self.IncludeFileStorageDirectory)[1] + '/' + IncludeFileName

        return line

    def _handle_output_file_line(self, line):
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
        if '/' in line2:
            dum, OriginalFileName = line2.split("/", 1)
        else:
            OriginalFileName = line2
        OriginalFileName = OriginalFileName.replace('"', '')
        OriginalFileName = OriginalFileName.replace("'", '')
        OriginalFileName = OriginalFileName.replace(' ','')
        line1 = line1.replace('"', '')
        line1 = line1.replace("'", '')
        new_line = line1 + ' =  "../Results/' + OriginalFileName + "_itt_\' + " + 'str(iteration)' + ' + \'"\')'

        return new_line, OriginalFileName

    def _handle_phase_space_source(self,OriginalFileLocation, line, OutputPhaseSpaceFilesNames):
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
        OriginalFileLocation = Path(OriginalFileLocation)
        for OutputPhaseSpace in OutputPhaseSpaceFilesNames:
            if OutputPhaseSpace in line:
                UseStaticPhaseSpace = False

        line1, line2 = line.split("=", 1)  # delete everything after the first =
        OriginalFileName = line2.split('/')[-1]
        OriginalFileName = OriginalFileName.replace('"', '')
        OriginalFileName = OriginalFileName.replace("'", '')
        OriginalFileName = OriginalFileName.replace(" ", '')
        line1 = line1.replace('"', '')
        line1 = line1.replace("'", '')
        if not UseStaticPhaseSpace:
            # dynamically allocated phase space name
            # new_line = line1 + ' = "\' + str(Path(BaseDirectory) / "Results" / "' + OriginalFileName + '") + "_itt" + ' + 'str(iteration)' + ' + \'"\')'
            new_line = line1 + ' =  "../Results/' + OriginalFileName + "_itt_\' + " + 'str(iteration)' + ' + \'"\')'
        else:
            # in this case we want to convert a relative path to an absolute path.
            # do we also want to copy the file to the IncludeDirectory? probably not, it could be huge...
            new_line = line1 + ' = ' + str(OriginalFileLocation.parent / OriginalFileName) + "')"

        return new_line

    def _generate_topas_script_generator(self):
        """
        generate a python script that will itself generate the script at TopasScriptLocation
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
        TopasScriptGenerator.append('def GenerateTopasScripts(BaseDirectory, iteration, **variable_dict):\n')
        TopasScriptGenerator.append(TopasScriptGeneratorReadMe)

        ScriptNames = []
        ReturnStatementString = '['
        OutputPhaseSpaceFilesNames = []  # need to keep track of these to see if they match the input of another file
        ScriptNames = []
        for file in self.TopasScriptLocation:
            dum, ScriptName = os.path.split(file)
            ScriptName, dum = os.path.splitext(ScriptName)
            ScriptName = ''.join(e for e in ScriptName if e.isalnum())  # heal any weird chracters
            ReturnStatementString = ReturnStatementString + ScriptName + ', '
            ScriptNames.append(ScriptName)
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
                        line = self._handle_include_files(file, line)
                    if 'OutputFile '.lower() in line.lower():
                        line, OriginalFileName = self._handle_output_file_line(line)
                        TopasScriptGenerator.append("    " + ScriptName + ".append('" + line + "\n")
                        OutputPhaseSpaceFilesNames.append(OriginalFileName)
                        continue  # need a slightly different line in this case from the default
                    if 'PhaseSpaceFileName'.lower() in line.lower():  # could put a more sophisticated test here...
                        line = self._handle_phase_space_source(file, line, OutputPhaseSpaceFilesNames)
                        TopasScriptGenerator.append("    " + ScriptName + ".append('" + line + "\n")
                        continue  # need a slightly different line in this case from the default

                TopasScriptGenerator.append("    " + ScriptName + ".append('" + line + "')\n")

        ReturnStatementString = ReturnStatementString[:-2]  # remove the last comma
        ReturnStatementString = ReturnStatementString + ']'
        ReturnStatementString = ReturnStatementString + ', ' + str(ScriptNames)
        TopasScriptGenerator.append('\n    return ' + ReturnStatementString)

        TopasScriptGenerator.append('\n\nif __name__ == "__main__":\n')
        TopasScriptGenerator.append('    Scripts, ScriptNames = GenerateTopasScripts(".", 1)\n')
        TopasScriptGenerator.append('    for i, script in enumerate(Scripts):\n')
        TopasScriptGenerator.append('        filename = ScriptNames[i] + ".tps"\n')
        TopasScriptGenerator.append('        f = open(filename, "w")\n')
        TopasScriptGenerator.append('        for line in script:\n')
        TopasScriptGenerator.append('            f.write(line)\n')
        TopasScriptGenerator.append('            f.write("\\n")\n')
        f2 = open(outputFile, "w+")
        for line in TopasScriptGenerator:
            f2.writelines(line)
