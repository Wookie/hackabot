'''
This is the base class for a hackabot command.
'''

import re
import sys

# import the other hackabot base class
from action import Action


class Command(Action):
    """
    Base class for all python hackabot commands
    """

    def __init__(self, command):
        super(Command, self).__init__(command)

    def _print_help(self, path):
        """
        This pulls the help block from the top of the command script
        and prints it out.
        """

        # open the script file
        cmdf = open(path, 'r')

        # read in the lines
        lines = cmdf.readlines()

        # close the file
        cmdf.close()

        # scan the lines looking for the help block markers
        in_help = False
        for line in lines:
            if re.match(r'^##HACKABOT_HELP##.*$', line):
                if in_help:
                    return
                else:
                    in_help = True
                    continue
            elif in_help:
                c = re.match(r'^#\s*(.*)', line)
                print >> sys.stdout, 'send %s' % c.group(1)

