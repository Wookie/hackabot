'''
This is the base class for a hackabot action.  Both commands and hooks
are types of actions.  This base class handles automatically
loading the hackabot configuration, parsing the inputs from hackabot,
and helps with establishing database connections.
'''

import os
import re
import socket
import sys
import fcntl

# remote debugging facility
from rdebug import *

# import the storm ORM
from storm.locals import *

# import the other hackabot utility classes
from acl import Acl
from log import Log
from config import Config

class Action(object):
    """
    Base class for all python hackabot actions
    """

    def __init__(self, action):

        # turn on the debug signal
        #listen()

        # store our action
        self._action = action

        # this gets a handle to the logging facility
        self._log = Log()

        # this loads up the config specified in env vars
        self._config = Config()

        # this loads up the acl specified in env vars
        self._acl = Acl()

        # get the root dir
        self._root_dir = os.getenv('HACKABOT_DIR')

        # load the database config
        self._db = self._config['database']
        self._db_config = self._config['databases'][self._db]

        # initialize members
        self._event_type = None
        self._nick = None
        self._user = None
        self._host = None
        self._msg = None
        self._to = None
        self._current_nick = None

        # make stdin non-blocking
        fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        # read in the input from hackabot
        buf = ""
        while True:
            try:
                b = sys.stdin.read()
                if b == "":
                    break
                buf += b
            except:
                break

        # parse the input from hackabot
        lines = buf.split('\n')
        for line in lines:
            line = line.rstrip("\n")
            if re.match(r'type\s+(\S+)', line):
                c = re.match(r'type\s+(\S+)', line)
                self._event_type = c.group(1)
            elif re.match(r'nick\s+(\S+)', line):
                c = re.match(r'nick\s+(\S+)', line)
                self._nick = c.group(1)
            elif re.match(r'user\s+(\S+)', line):
                c = re.match(r'user\s+(\S+)', line)
                self._user = c.group(1)
            elif re.match(r'host\s+(\S+)', line):
                c = re.match(r'host\s+(\S+)', line)
                self._host = c.group(1)
            elif re.match(r'msg\s*(.*)', line):
                c = re.match(r'msg\s*(.*)', line)
                self._msg = c.group(1)
            elif re.match(r'to\s+(\S+)', line):
                c = re.match(r'to\s+(\S+)', line)
                self._to = c.group(1)
            elif re.match(r'currentnick\s+(\S+)', line):
                c = re.match(r'currentnick\s+(\S+)', line)
                self._current_nick = c.group(1)

        # log
        self._log.debug('A>> event type: %s' % self._event_type)
        self._log.debug('A>> nick: %s' % self._nick)
        self._log.debug('A>> user: %s' % self._user)
        self._log.debug('A>> host: %s' % self._host)
        self._log.debug('A>> msg: %s' % self._msg)
        self._log.debug('A>> to: %s' % self._to)
        self._log.debug('A>> currentnick: %s' % self._current_nick)

    def __del__(self):
        """
        make sure that our pipes are closed
        """
        sys.stdin.close()
        sys.stdout.close()
        sys.stderr.close()

    def _get_log(self):
        return self._log

    def _get_acl(self):
        return self._acl

    def _get_config(self):
        return self._config

    def _get_full_path(self, path):
        if os.path.isabs(path):
            return path

        return os.path.join(self._root_dir, path)

    def _get_database_connection(self):
        """
        this attempts to connect to the hackabot database
        """
        if self._db.lower() == 'mysql':
            # build the mysql uri 
            uri = 'mysql://%s:%s@%s/%s' % (self._db_config['user'], 
                                           self._db_config['password'],
                                           self._db_config['host'],
                                           self._db_config['name'])
            
        elif self._db.lower() == 'sqlite':
            # get the db file path
            db_file = self._db_config['file']
            if not db_file.startswith('/'):
                db_file = os.path.join(self._config['directory'], db_file)
            
            # build the sqlite uri
            uri = 'sqlite:%s' % db_file
        else:
            return None

        # return a storm Store instance
        return Store(create_database(uri))

#    def _set_proc_name(self, name):
#        sys.argv[0] = name
#        libc = cdll.LoadLibrary('libc.so.6')
#        buff = create_string_buffer(len(name) + 1)
#        buff.value = name
#        libc.prctl(15, byref(buff), 0, 0, 0)

