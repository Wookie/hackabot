'''
This are all of the model classes used with the storm ORM.
'''

import os
import sys
from datetime import datetime
from storm.locals import *

class LogEntry(object):
    """
    Class that represents a single line in the log table
    """
    __storm_table__ = 'log'
    id = Int(primary=True)
    nick = Unicode()
    chan = Unicode()
    text = Unicode()
    num = Int()
    date = DateTime()
    type = Enum(    map={'msg':'msg', 
                         'action':'action', 
                         'notice':'notice', 
                         'join':'join', 
                         'part':'part', 
                         'quit':'quit', 
                         'stats':'stats', 
                         'topic':'topic'},
                set_map={'msg':'msg',
                         'pubmsg':'msg',
                         'privmsg':'msg',
                         'pubsnd':'msg',
                         'privsnd':'msg',
                         'action':'action', 
                         'notice':'notice', 
                         'privnotice':'notice',
                         'pubnotice':'notice',
                         'join':'join', 
                         'part':'part', 
                         'quit':'quit', 
                         'stats':'stats', 
                         'topic':'topic',
                         'currenttopic':'topic',
                         'topicinfo':'topic'})

    def __init__(self, nick='', chan='', text='', num=0, type='msg', date=datetime.now()):
        self.nick = unicode(nick)
        self.chan = unicode(chan)
        self.text = unicode(text)
        self.num = num
        self.type = type
        self.date = date

class ScoreEntry(object):
    """
    Class that represents a nick's score
    """
    __storm_table__ = 'score'
    name = Unicode(primary=True)
    value = Int()
    nick = Unicode()
    chan = Unicode()
    date = DateTime()

    def __init__(self, name='', value=0, nick='', chan='', date=datetime.now()):
        self.name = unicode(name)
        self.value = value
        self.nick = unicode(nick)
        self.chan = unicode(chan)
        self.date = date

class WTFEntry(object):
    """
    Class that represents a WTF entry
    """
    __storm_table__ = 'wtf'
    id = Int(primary=True)
    acronym_i = Unicode()
    acronym = Unicode()
    text = Unicode()
    nick = Unicode()
    chan = Unicode()
    date = DateTime()
    lastused = Int(default=1)

    def __init__(self, acronym='', definition='', nick='', chan='', date=datetime.now()):
        self.acronym_i = unicode(acronym.lower())
        self.acronym = unicode(acronym)
        self.text = unicode(definition)
        self.nick = unicode(nick)
        self.chan = unicode(chan)
        self.date = date

class TopicEntry(object):
    """
    Class that represents a topic entry
    """
    __storm_table__ = 'topic'
    id = Int(primary=True)
    text = Unicode()
    nick = Unicode()
    chan = Unicode()
    date = DateTime()
    lastused = Int(default=1)

    def __init__(self, text='', nick='', chan='', date=datetime.now()):
        self.text = unicode(text)
        self.nick = unicode(nick)
        self.chan = unicode(chan)
        self.date = date

