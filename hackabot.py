#!/usr/bin/env python
#
# The Python rewrite of the ever famous Hackabot 
#
# This code is under the GPL 2.0 and all that good jazz.

"""Hackabot baby!

This is the Python rewrite of Hackabot, aka manatee. This is the result of

several rewrites of the original Perl version trying to either use multiple
processes or threads. In short, Perl frickin sucks at sharing data between
threads. Hopefully python will prove itself to be much better.
"""

import logging
import os
import re
import socket
import string
import subprocess
import sys
import thread
import time
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_u, nm_to_h, Event
from llbase import llsd
from optparse import OptionParser

# HACK: this includes the hackabot/lib/python dir in the python search paths
app_bin_dir = os.path.dirname( os.path.realpath( __file__ ) )
app_lib_dir = os.path.join( app_bin_dir, 'lib/python' )
sys.path.insert(0, app_lib_dir)

# import the hackabot helper classes
from log import Log
from config import Config
from acl import Acl

# this is the directory name that holds the hackabot config files
# hackabot will first search the local directory for a directory
# with the name, then it will check for the environment variable,
# then it will look for a dot directory in the current user's home 
# directory and lastly it will search the /etc directory for a 
# directory with the given name.
HACKABOT_CONF_DIR = 'hackabot'

# this it the environment variable that hackabot will check as well
HACKABOT_CONF_DIR_ENV_VAR = 'HACKABOT_CONF_DIR'

# this is the name of the hackabot config file
HACKABOT_CONF_FILE = 'config.llsd.xml'

# this is the name of the hackabot ACL file
HACKABOT_ACL_FILE = 'acl.llsd.xml'

# this is the name of the hackabot logging config file
HACKABOT_LOG_FILE = 'logging.conf'

class Hackabot(SingleServerIRCBot):

    def __init__(self, options):

        # this is the calculated config directory
        self._config_dir = os.path.realpath(options.config_dir)

        # set up the logger
        self._log_file = os.path.join(self._config_dir, HACKABOT_LOG_FILE)
        self._log = Log(self._log_file)

        # load up the config
        self._config_file = os.path.join(self._config_dir, HACKABOT_CONF_FILE)
        self._config = Config(self._config_file)

        # load up the acl
        self._acl_file = os.path.join(self._config_dir, HACKABOT_ACL_FILE)
        self._acl = Acl(self._acl_file)
      
        # get the server info
        server_info = [ self._config['server'], self._config['port'] ]

        # add in the server password if there is one specified
        if self._config.has_key('password'):
            server_info.append(self._config['password'])

        # figure out what directory we live in 
        self._root_dir = self._config['directory']
        if self._root_dir == '':
            self._root_dir = os.path.dirname(os.path.realpath(__file__))
        
        # calculate absolute paths to essential files/dirs
        self._socket_file = self._get_full_path(self._root_dir, self._config['socket'])
        self._commands_dir = self._get_full_path(self._root_dir, self._config['commands'])
        self._hooks_dir = self._get_full_path(self._root_dir, self._config['hooks'])
 
        # set up the environment
        self._init_env()

        # launch the irc bot
        SingleServerIRCBot.__init__(
            self, [server_info],
            self._config['nick'],
            self._config['name'],
            self._config['reconnect'] )

    def _get_full_path(self, root_dir, path):
        """
        this function looks to see if path starts with a /
        if it does, then it just assumes path is an absolute
        path and returns it.  if it doesn't start with a /
        then it joins it with the root_dir and returns that.
        """

        if os.path.isabs(path):
            return path

        return os.path.join(root_dir, path)

    def _init_env(self):
        """
        this sets up environment variables that the command/hook
        scripts/executables can use.
        """
        
        self._log.info("Setting up irc object for %s..." % self._config['server'])

        # specify the config file hackabot is using
        os.putenv("HACKABOT_CFG", self._config_file)

        # specify the log config file that hackabot is using
        os.putenv('HACKABOT_LOG', self._log_file)

        # specify the acl file that hackabot is using
        os.putenv('HACKABOT_ACL', self._acl_file)

        # the root hackabot dir
        os.putenv("HACKABOT_DIR", self._root_dir)

        # specify the hackabot commands dir
        os.putenv("HACKABOT_CMD", self._commands_dir) 

        # the hackabot etc dir
        os.putenv("HACKABOT_ETC", self._config_dir)

        # specify the command socket 
        os.putenv("HACKABOT_SOCK", self._socket_file)

        # if they specify "pythonpath" in the config, then set the PYTHONPATH
        # env variable so that python scripts can import hackabot-local utility
        # cLasses.
        python_path = os.getenv('PYTHONPATH')
        for ppath in self._config['pythonpath']:
            ppath = self._get_full_path(self._root_dir, ppath)
            python_path = ppath + ':' + python_path
            sys.path.insert(0, ppath)

        # set the new python path
        os.putenv("PYTHONPATH", python_path)

    ### irclib event callbacks ###

    def on_nicknameinuse(self, c, event):
        self.connection.nick(self.connection.get_nickname() + "_")

    def on_welcome(self, c, event):

        # snooze a bit
        time.sleep(1)
        self._log.info("Connected!")

        # kick off a new thread
        thread.start_new_thread(self.server,tuple())

        # send the automsg messages
        for automsg in self._config['automsg']:
            self._log.info('sending msg to %s' % automsg['to'])
            self.privmsg(automsg['to'], automsg['msg'])
        
        # snooze a bit more
        time.sleep(1)

        # join all of the autojoin channels
        for autojoin in self._config['autojoin']:
            self._log.info('joining %s' % autojoin['chan'])
            if autojoin.has_key('password'):
                self.connection.join(autojoin['chan'], autojoin['password'])
            else:
                self.connection.join(autojoin['chan'])

            if autojoin.has_key('msg'):
                self.privmsg(autojoin['chan'], autojoin['msg'])
                
    def on_privmsg(self, c, event):
        to = nm_to_n(event.source())
        thread.start_new_thread(self.do_msg,(event,to))

    def on_pubmsg(self, c, event):
        to = event.target()
        thread.start_new_thread(self.do_msg,(event,to))

    def on_action(self, c, event):
        to = event.target()
        thread.start_new_thread(self.do_hook,(event,to))

    def on_pubnotice(self, c, event):
        to = event.target()
        thread.start_new_thread(self.do_hook,(event,to))

    def on_privnotice(self, c, event):
        to = event.target()
        thread.start_new_thread(self.do_hook,(event,to))

    def on_join(self, c, event):
        to = event.target()
        thread.start_new_thread(self.do_hook,(event,to))

    def on_part(self, c, event):
        to = event.target()
        thread.start_new_thread(self.do_hook,(event,to))

    def on_topic(self, c, event):
        # quick hack so topic changes are handeled by currenttopic/topicinfo all the time
        self.connection.topic(event.target())

    def on_currenttopic(self, c, event):
        to = event.arguments()[0]
        if (self.channels.has_key(to)):
            self.channels[to].topic = event.arguments()[1]
        else:
            self._log.info("currenttopic: chan '"+to+"' not known")
        thread.start_new_thread(self.do_hook,(event,to))

    def on_topicinfo(self, c, event):
        to = event.arguments()[0]
        if (self.channels.has_key(to)):
            self.channels[to].topic_nick = event.arguments()[1]
            self.channels[to].topic_time = event.arguments()[2]
        else:
            self._log.info("topicinfo: chan '"+to+"' not known")
        thread.start_new_thread(self.do_hook,(event,to))

    def on_quit(self, c, event):
        to = event.target()
        thread.start_new_thread(self.do_hook,(event,to))

    def privmsg(self, to, txt):
        self.connection.privmsg(to, txt)
    
        nickmask = self.connection.nickname \
            + "!" + self.connection.username \
            + "@" + self.connection.localhost

        if re.match(r'#',to):
            self.do_hook(Event("pubsnd", nickmask, to, [txt]),to)
        else:
            self.do_hook(Event("privsnd", nickmask, to, [txt]),to)

    def action(self, to, txt):
        self.connection.action(to, txt)
    
        nickmask = self.connection.nickname \
            + "!" + self.connection.username \
            + "@" + self.connection.localhost

        self.do_hook(Event("action", nickmask, to, [txt]),to)

    def notice(self, to, txt):
        self.connection.notice(to, txt)
    
        nickmask = self.connection.nickname \
            + "!" + self.connection.username \
            + "@" + self.connection.localhost

        if re.match(r'#',to):
            self.do_hook(Event("pubnotice", nickmask, to, [txt]),to)
        else:
            self.do_hook(Event("privnotice", nickmask, to, [txt]),to)

    def do_msg(self, event, to):
        nick = nm_to_n(event.source())
        r = self.do_hook(event, to)
        if r != "noall" and r != "nocmd":
            self.do_cmd(event, to)

    def do_hook(self, event, to):
        ret = "ok"

        # calculate the hook directory path
        dir = os.path.join(self._hooks_dir, event.eventtype())

        # make sure we have read access to the dir
        if not os.access(dir,os.R_OK):
            return ret

        # get the list of files in the hook dir
        hooks = os.listdir(dir)
        hooks.sort()
        for hook in hooks:
            if re.match(r'\.', hook):
                continue

            if event.eventtype() == "currenttopic":
                to = event.arguments()[0]
                arg = event.arguments()[1]
                event._source = None
            elif event.eventtype() == "topicinfo":
                to = event.arguments()[0]
                arg = event.arguments()[1]+" "+event.arguments()[2]
                event._source = None
            elif len(event.arguments()) > 0:
                arg = event.arguments()[0]
            else:
                arg = None

            r = self.do_prog(event, to, os.path.join(dir, hook), arg)
            if r == "noall" or r == "nohook":
                ret = r
                break
            elif r == "nocmd":
                ret = r
        return ret

    def do_cmd(self, event, to):
        c = re.match(r'!([^\s/]+)\s*(.*)', event.arguments()[0])
        if (not c):
            return

        # calculate the path to the command script
        cmd = os.path.join(self._commands_dir, c.group(1))
        self._log.info('executing %s' % cmd)

        # get the msg
        msg = c.group(2)
       
        # execute the command handler
        return self.do_prog(event, to, cmd, msg)
    
    def do_prog(self, event, to, cmd, msg):
        self._log.debug('event: %s' % str(event))
        self._log.debug('to: %s' % to)
        self._log.debug('cmd: %s' % cmd)
        self._log.debug('msg: %s' % msg)

        # make sure we have rights to execute the command handler
        if not os.access(cmd,os.X_OK):
            return
       
        # open a new process with I/O pipes
        #write,read = os.popen2(cmd)
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, 
                             stdout=subprocess.PIPE, close_fds = True)
       
        (child_stdin, child_stdout) = (p.stdin, p.stdout)
        
        # write the command parameters to the command handler's STDIN
        self._log.debug('feeding msg details to %s' % cmd)
        print >> child_stdin, 'type %s' % event.eventtype()
        if isinstance(event.source(), str):
            print >> child_stdin, 'nick %s' % nm_to_n(event.source())
            if event.source().find('!') > 0:
                print >> child_stdin, 'user %s' % nm_to_u(event.source())
            if event.source().find('@') > 0:
                print >> child_stdin, 'host %s' % nm_to_u(event.source())
        if isinstance(to, str):
            print >> child_stdin, 'to %s' % to
        if isinstance(msg, str):
            print >> child_stdin, 'msg %s' % msg
        print >> child_stdin, 'currentnick %s' % self.connection.get_nickname()

        # process the output from the command handler
        self._log.debug('processing response from %s' % cmd)
        ret = self.process(child_stdout, to, event)
        child_stdout.close()

        return ret
    
    def process(self, sockfile, to = None, event = None):
        ret = "ok"
        sendnext = False
        rw = (sockfile.mode != 'r')
        self._log.debug('pipe in rw mode: %s' % rw)

        for line in sockfile:
            line = line.rstrip("\n")
            self._log.info(line)

            if to and sendnext:
                self.privmsg(to, line)
                continue

            c = re.match(r'sendnext', line)
            if to and c:
                sendnext = True
                continue

            c = re.match(r'send\s+(.+)',line)
            if to and c:
                self.privmsg(to, c.group(1))
                continue

            c = re.match(r'notice\s+(.+)',line)
            if to and c:
                self.notice(to, c.group(1))
                continue

            c = re.match(r'(me|action)\s+(.+)',line)
            if to and c:
                self.action(to, c.group(2))
                continue

            c = re.match(r'to\s+(\S+)',line)
            if c:
                to = c.group(1)
                continue

            c = re.match(r'nick\s+(\S+)',line)
            if c:
                self.connection.nick(c.group(1))
                continue

            c = re.match(r'topic\s+(.+)',line)
            if c:
                self.connection.topic(to, c.group(1))
                continue

            c = re.match(r'join\s+(\S+)',line)
            if c:
                self.connection.join(c.group(1))
                continue

            c = re.match(r'part\s+(\S+)',line)
            if c:
                self.connection.part(c.group(1))
                continue

            c = re.match(r'quit\s*(.*)',line)
            if c:
                self._log.info("Exiting!")
                self.disconnect(c.group(1))
                self.connection.execute_delayed(1,sys.exit)
                continue

            c = re.match(r'currenttopic\s+(#\S+)',line)
            if rw and c:
                chan = c.group(1)
                if self.channels.has_key(chan):
                    if hasattr(self.channels[chan], 'topic'):
                        topic = " "+self.channels[chan].topic
                    else:
                        topic = ""
                else:
                    topic = ""
                sockfile.write("currenttopic "+chan+topic+"\n")
                sockfile.flush()
                continue

            c = re.match(r'topicinfo\s+(#\S+)',line)
            if rw and c:
                chan = c.group(1)
                if self.channels.has_key(chan):
                    if hasattr(self.channels[chan], 'topic_nick') and \
                        hasattr(self.channels[chan], 'topic_time'):
                        topic = " "+self.channels[chan].topic_nick \
                            +" "+self.channels[chan].topic_time
                    else:
                        topic = ""
                else:
                    topic = ""
                sockfile.write("topicinfo "+chan+topic+"\n")
                sockfile.flush()
                continue

            c = re.match(r'names\s+(#\S+)',line)
            if rw and c:
                chan = c.group(1)
                if self.channels.has_key(chan):
                    list = self.channels[chan].users()
                    names = " "+string.join(list," ")
                else:
                    names = ""
                sockfile.write("names "+chan+names+"\n")
                sockfile.flush()
                continue

            if rw and re.match(r'channels',line):
                list = self.channels.keys()
                names = " "+string.join(list," ")
                sockfile.write("channels"+names+"\n")
                sockfile.flush()
                continue

            if rw and re.match(r'currentnick',line):
                sockfile.write("currentnick %s\n" %
                    self.connection.get_nickname())
                sockfile.flush()
                continue

            if event and re.match(r'msg\s*(.*)',line) and ( \
                    event.eventtype() == "pubmsg" or \
                    event.eventtype() == "privmsg" or \
                    event.eventtype() == "pubsnd" or \
                    event.eventtype() == "privsnd" or \
                    event.eventtype() == "pubnotice" or \
                    event.eventtype() == "privnotice" or \
                    event.eventtype() == "action"):
                c = re.match(r'msg\s*(.*)',line)
                event._arguments[0] = c.group(1)
                continue

            if re.match(r'nocmd',line):
                ret = "nocmd"
                continue

            if re.match(r'nohook',line):
                ret = "nohook"
                continue

            if re.match(r'noall',line):
                ret = "noall"
                continue
            
            self._log.info("Unknown request: "+line)

        return ret
    
    def server(self):

        # calculate path to command socket
        file = self._socket_file

        self._log.info("Creating control socket: %s" % file)
        listen = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    
        # Ignore an unlink error since it might not exist
        try:
            os.unlink(file)
        except OSError:
            pass

        listen.bind(file)
        listen.listen(5)

        while True:
            client,c = listen.accept()
            thread.start_new_thread(self.servclient,(client,))
        listen.close()
    
    def servclient(self, client):
        self._log.debug("New control socket connection.")
        self.process(client.makefile('r+'))
        self._log.debug("Closing control socket connection.")
        client.close()

    def msg(self, txt):
        print "hackabot:",txt


def find_config_root(app_conf_dir, APP_CONF_DIR_ENV_VAR):

    # 1. Look in current working directory
    if os.path.isdir(app_conf_dir):
        return abspath(app_conf_dir)

    # 2. Look for env var
    if os.environ.has_key(APP_CONF_DIR_ENV_VAR) and \
           os.path.isdir(os.environ[APP_CONF_DIR_ENV_VAR]):
        return os.environ[APP_CONF_DIR_ENV_VAR]

    # 3. Look in user home dir as a dot directory
    user_home = os.path.expanduser('~')
    home_conf_dir = os.path.join(user_home, '.' + app_conf_dir)
    if os.path.isdir(home_conf_dir):
        return home_conf_dir

    # 4. Fall back to /etc, or die.
    etc_conf_dir = os.path.join('/etc', app_conf_dir)
    if os.path.isdir(etc_conf_dir):
        return etc_conf_dir

    return None


def main():

    # create the option parser
    parser = OptionParser()
    parser.add_option( "-D", "--no-daemon", action='store_true', dest="no_daemon",  
                       help="force hackabot to not become a daemon")
    parser.add_option( "-c", "--config-dir", default=None, dest="config_dir",
                       help="specify the directory that contains the hackabot configs")

    # parse the args and get the results
    (options, args) = parser.parse_args()

    # if they didn't specify the config dir, try to search for it
    if options.config_dir is None:
        options.config_dir = find_config_root(HACKABOT_CONF_DIR, HACKABOT_CONF_DIR_ENV_VAR)
        if not options.config_dir:
            parser.error('Could not find hackabot config dir')

    # create the instance of the bot
    bot = Hackabot(options)

    # start it
    bot.start()

    return 0


if __name__ == "__main__":
    ret = main()
    sys.exit(ret)

