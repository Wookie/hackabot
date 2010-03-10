'''
singleton wrapper around logging.
'''
import os
import logging
import logging.config
import logging.handlers

class Log(object):

    class __impl:
        '''
        singleton implementation
        '''
    
        def __init__(self, logging_config_file = None):

            # figure out the path to the config file
            if config_file:
                self._config_file = logging_config_file
            else:
                # get the path to the config file
                self._config_file = os.getenv('HACKABOT_LOGGING_CFG')

            if self._config_file = None:
                print >> sys.stderr, 'Could not load the hackabot logging config file'

            # set up the logging facility
            logging.config.fileConfig(self._config_file)

            # get our logging wrapper
            self._logger = logging.getLogger()

        def debug(self, msg):
            self._logger.debug(msg)

        def info(self, msg):
            self._logger.info(msg)

        def warn(self, msg):
            self._logger.warn(msg)

        def error(self, msg):
            self._logger.error(msg)

        def critical(self, msg):
            self._logger.critical(msg)


    # storage for the instance reference
    __instance = None


    def __init__(self, logging_config_file = None):
        '''
        create the singleton instance if needed
        '''

        # check to see if we already have an instance
        if Log.__instance is None:
            # create and remember the instance
            Log.__instance = Log.__impl(logging_config_file)

        # store the instance reference as the only member in the handle
        self.__dict__['_Log__instance'] = Log.__instance

    def __getattr__(self, attr):
        '''
        delegate access to implementation
        '''
        return getattr(self.__instance, attr)

    def __setattr__(self, attr, value):
        '''
        delegate access to the implementation
        '''
        return setattr(self.__instance, attr, value)

