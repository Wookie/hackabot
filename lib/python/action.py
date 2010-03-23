'''
This is the base class for a hackabot action.  Both commands and hooks
are types of actions.  This base class handles automatically
loading the hackabot configuration, parsing the inputs from hackabot,
and helps with establishing database connections.
'''

import MySQLdb
import os
import re
import socket
import sqlite3
import sys

# import the other hackabot utility classes
from acl import Acl
from log import Log
from config import Config


class Action(object):
    """
    Base class for all python hackabot actions
    """

    def __init__(self, action):

        # store our action
        self._action = action

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

    def _get_database_connection(self):
        """
        this attempts to connect to the hackabot database
        """
        if self._db.lower() == 'mysql':
            # connect to the mysql database
            return MySQLdb.connect(host = self._db_config['host'], \
                                   db = self._db_config['name'], \
                                   user = self._db_config['user'], \
                                   passwd = self._db_config['password'])
            
        elif self._db.lower() == 'sqlite':
            # get the db file path
            db_file = self._db_config['file']
            if not db_file.startswith('/'):
                db_file = os.path.join(self._config['directory'], db_file)
            
            # connect to the db
            conn = sqlite3.connect(db_file)

            # use a dict structure for each row
            conn.row_factory = sqlite3.Row

            return conn
        else:
            return None

    def _get_control_socket_connection(self):
        sock_file = os.getenv('HACKABOT_SOCK')
        if sock_file is None:
            self._log.warn('Could not get command socket filename')

        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(sock_file)

        return s

    def _get_channel_names(self, chan):

        # get the socket connection
        sock = self._get_control_socket_connection()

        # send it the channel name
        sock.send('names %s\n' % chan)

        # shutdown the write side so that all of the data is sent
        sock.shutdown(socket.SHUT_WR)

        # create a file-like object from the socket
        sf = sock.makefile('r', 0)

        # read in the response
        line = sf.readline()
        parts = line.split()
        names = parts[2:]

        # close the socket
        sock.close()
        sf.close()
        
        self._log.debug('names for chan %s: %s' % (parts[1], ' '.join(names)))

        return names

        

