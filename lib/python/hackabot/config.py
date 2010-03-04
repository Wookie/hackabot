'''
This is a wrapper class around the hackabot config file.  It handles loading
the config and setting up default values so that both hackabot and commands
alike see the config in the same way
'''
import sys
from llbase import llsd


class Config(object):
    """
    Config wrapper
    """

    # default config values
    DEFAULT_RECONNECT = 60
    DEFAULT_PYTHONPATH = []
    DEFAULT_AUTOMSG = []
    DEFAULT_AUTOJOIN = []
    DEFAULT_CMDCONFIG = {}

    def __init__(self, config_file = None):

        # figure out the path to the config file
        if config_file:
            self._config_file = config_file
        else:
            # get the path to the config
            self._config_file = os.getenv('HACKABOT_CFG')
        
        if self._config_file == None:
            print >> sys.stderr, 'Could not load hackabot config file'

        # load the configuration
        c = open(config, 'r')
        self._config = llsd.parse_xml(c.read())
        c.close()

    def _set_defaults(self):
        """
        This sets sane defaults for values that must be defined.
        """
        # set reconnect default if it doesn't exist
        if not self._config.has_key('reconnect'):
            self._config['reconnect'] = Config.DEFAULT_RECONNECT

        # set up default python paths
        if not self._config.has_key('pythonpath'):
            self._config['pythonpath'] = Config.DEFAULT_PYTHONPATH

        # set up default automsg list
        if not self._config.has_key('automsg'):
            self._config['automsg'] = Config.DEFAULT_AUTOMSG

        # set up default autojoin list
        if not self._config.has_key('autojoin'):
            self._config['autojoin'] = Config.DEFAULT_AUTOJOIN

        # set up the default cmdconfig map
        if not self._config.has_key('cmdconfig'):
            self._config['cmdconfig'] = Config.DEFAULT_CMDCONFIG

    def __get__(self, key):
        if self._config.has_key(key):
            return self._config[key]

        return None

    def __set__(self, key, value):
        self._config[key] = value

