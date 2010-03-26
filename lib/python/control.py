'''
This contains the base class and specialized classes for working with the
control socket communication channel provided by hackabot.  Hackabot opens a
control socket that allows actions (e.g. hooks, commands) to query and control
hackabot.
'''

import os
import re
import socket
import sys

from acl import Acl
from log import Log
from config import Config

class ControlCommand(object):
    """
    Base class for all control socket commands/queries.
    """

    def __init__(self, control_command):

        # store our control command name
        self._control_command = control_command

        # set up our logging facility
        self._log = Log()

        # get the config
        self._config = Config()

        # get the acls too
        self._acl = Acl()

        # initialize a connect to the control socket
        self._init_control_socket()

    def __del__(self):
        # make sure we clean up our socket connection
        self._s.close()
        self._sf.close()

    def _init_control_socket(self):
        sock_file = os.getenv('HACKABOT_SOCK')
        if sock_file is None:
            self._log.warn('Could not get command socket filename')

        self._s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._s.connect(sock_file)

    def _send(self, line):
        self._s.send(line)

    def _get_result(self):
        # we must close the write side of the socket to force all of the
        # data to be written and to unblock the read on the other side
        self._s.shutdown(socket.SHUT_WR)

        # create a file-like object from the socket
        self._sf = self._s.makefile('r', 0)

        # now we can read all of the available data in the response
        return self._sf.readlines()

class ChannelNames(ControlCommand):
    """
    Class that queries for and wraps the nicks of all users in a channel.
    """

    def __init__(self, chan):

        # init the base class 
        super(ChannelNames, self).__init__('ChannelNames')

        # store the chan
        self._chan = chan

        # init the values that would be filled
        self._names = []

        # query for the names
        self._init_names()

    def _init_names(self):

        # send the names command
        self._send('names %s\n' % self._chan)

        # get the result
        result = self._get_result()

        # parse the results
        if len(result) > 0:
            parts = result[0].split()
            self._names = parts[2:]

    def __getitem__(self, index):
        return self._names[index]

    def __setitem__(self, index, value):
        raise Exception('channel names are read-only')

    def __iter__(self):
        return self._names.__iter__()

    def __len__(self):
        return self._names.__len__()

    def next(self):
        return self._names.next()

class ChannelTopicInfo(ControlCommand):
    """
    Class that queries for the nick of who last set the topic and when they
    set it.
    """

    def __init__(self, chan):

        # init the base class
        super(ChannelTopicInfo, self).__init__('ChannelTopicInfo')

        # store the chan
        self._chan = chan

        # init the values that will be filled in
        self._nick = 'Nobody'
        self._date = 'Never'

        # query for the topic info
        self._init_topic_info()

    def _init_topic_info(self):

        # send the topicinfo command
        self._send('topicinfo %s\n' % self._chan)

        # get the result
        result = self._get_result()

        # parse the result
        if len(result) > 0:
            self._log.debug('ChannelTopicInfo line: %s' % result[0])
            if re.match(r'^topicinfo\s+%s\s+(\S+)\s+(\d+)$' % self._chan, result[0]):
                c = re.match(r'^topicinfo\s+%s\s+(\S+)\s+(\d+)$' % self._chan, result[0])
                self._nick = c.group(1)
                self._date = c.group(2)
                self._log.debug('TopicInfo -- nick: %s, date: %s' % (self._nick, self._date))

class ChannelTopic(ControlCommand):
    """
    Class that queries for the current topic
    """

    def __init__(self, chan):

        # init the base class
        super(ChannelTopic, self).__init__('ChannelTopic')

        # store the chan
        self._chan = chan

        # init the topic to something sane
        self._topic = ''

        # query for the topic info
        self._init_topic()

    def _init_topic(self):

        # send the topicinfo command
        self._send('currenttopic %s\n' % self._chan)

        # get the result
        result = self._get_result()

        # parse the result
        if len(result) > 0:
            self._log.debug('ChannelTopic line: %s' % result[0])
            if re.match(r'^currenttopic\s+%s\s*(\S*)$' % self._chan, result[0]):
                c = re.match(r'^currenttopic\s+%s\s*(\S*)$' % self._chan, result[0])
                self._topic = c.group(1)
                self._log.debug('CurrentTopic -- topic: %s' % self._topic)


