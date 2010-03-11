'''
This is the base class for a hackabot command.  It handles automatically
loading the hackabot configuration, parsing the inputs from hackabot,
and helps with establishing database connections.
'''

import MySQLdb
import os
import re
import sqlite3
import string
import sys

# import the other hackabot utility classes
from acl import Acl
from log import Log
from config import Config


class Command(object):
    """
    Base class for all python hackabot commands
    """

    def __init__(self, command):
        # this gets a handle to the logging facility
        self._log = Log()

        # this loads up the config specified in env vars
        self._config = Config()

        # this loads up the acl specified in env vars
        self._acl = Acl()

        # load the database config
        self._db = self._config['database']
        self._db_config = self._config['databases'][self._db]

        # parse the input from hackabot
        self._event_type = None
        self._nick = None
        self._user = None
        self._host = None
        self._msg = None
        self._to = None
        for line in sys.stdin.readlines():
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

        self._log.debug('>>> event type: %s' % self._event_type)
        self._log.debug('>>> nick: %s' % self._nick)
        self._log.debug('>>> user: %s' % self._user)
        self._log.debug('>>> host: %s' % self._host)
        self._log.debug('>>> msg: %s' % self._msg)
        self._log.debug('>>> to: %s' % self._to)
        self._log.debug('>>> currentnick: %s' % self._current_nick)

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

    def _get_database_connection(self):
        """
        this attempts to connect to the hackabot database
        """
        if self._db.lower() == 'mysql':
            return MySQLdb.connect(host = self._db_config['host'], \
                                   db = self._db_config['name'], \
                                   user = self._db_config['user'], \
                                   passwd = self._db_config['password'])
            
        elif self._db.lower() == 'sqlite':
            db = os.path.join(self._config['directory'], self._db_config['file'])
            return sqlite3.connect(db)
        else:
            return None

    def main(self):
        """
        this is the function that handles the command...the base class
        doesn't do anything.
        """
        pass

