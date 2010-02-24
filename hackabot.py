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

import string
import thread
import socket
import time
import sys
import os
import re
from ircbot import SingleServerIRCBot
from irclib import nm_to_n, nm_to_u, nm_to_h, Event
from llbase import llsd

# defaults for config values
DEFAULT_RECONNECT = 60

class Hackabot(SingleServerIRCBot):

    def __init__(self, file):

        # load up the config
        self._load_config(file)
      
        # set up the environment
        self._init_env(file)

        # get the server info
        server_info = [ self._config['server'], self._config['port'] ]

        # add in the server password if there is one specified
        if self._config.has_key('password'):
            server_info.append(self._config['password'])

        # launch the irc bot
        SingleServerIRCBot.__init__(
            self, [server_info],
            self._config['nick'],
            self._config['name'],
            self._config['reconnect'] )

    def _load_config(self, file):
        """
        load up the config file, parse it and set default values
        for any config parameters that are missing but need to
        exists.
        """

        # load up the config
        c = open(file, 'r')
        self._config = llsd.parse_xml(c.read())
        c.close()

        # set reconnect default if it doesn't exist
        if not self._config.has_key('reconnect'):
            self._config['reconnect'] = DEFAULT_RECONNECT

        # set up default python paths
        if not self._config.has_key('pythonpath'):
            self._config['pythonpath'] = []

        # set up default automsg list
        if not self._config.has_key('automsg'):
            self._config['automsg'] = []

        # set up default autojoin list
        if not self._config.has_key('autojoin'):
            self._config['autojoin'] = []

    def _init_env(self, file):
        """
        this sets up environment variables that the command/hook
        scripts/executables can use.
        """

        server = self._config['server']
        root_dir = self._config['directory']
        etc_dir = self._config['etc']
        cmd_dir = self._config['commands']
        socket_file = self._config['socket']

        self.msg("Setting up irc object for %s..." % server)

        # specify the config file hackabot is using
        os.putenv("HACKABOT_CFG", file)

        # the root hackabot dir
        os.putenv("HACKABOT_DIR", root_dir)

        # the hackabot etc dir
        os.putenv("HACKABOT_ETC", os.path.join(root_dir, etc_dir))
        os.putenv("HACKABOT_CMD", os.path.join(root_dir, cmd_dir))
        os.putenv("HACKABOT_SOCK", os.path.join(root_dir, socket_file))

        # if they specify "pythonpath" in the config, then set the PYTHONPATH
        # env variable so that python scripts can import hackabot-local utility
        # classes.
        for ppath in self._config['pythonpath']:
            os.putenv("PYTHONPATH", os.path.join(root_dir, ppath))

    ### irclib event callbacks ###

    def on_nicknameinuse(self, c, event):
        self.connection.nick(self.connection.get_nickname() + "_")

    def on_welcome(self, c, event):

        # snooze a bit
        time.sleep(1)
        self.msg("Connected!")

        # kick off a new thread
        thread.start_new_thread(self.server,tuple())

        # send the automsg messages
        for automsg in self._config['automsg']:
            self.msg('sending msg to %s' % automsg['to'])
            self.privmsg(automsg['to'], automsg['msg'])
        
        # snooze a bit more
        time.sleep(1)

        # join all of the autojoin channels
        for autojoin in self._config['autojoin']:
            self.msg('joining %s' % autojoin['chan'])
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
            self.msg("currenttopic: chan '"+to+"' not known")
        thread.start_new_thread(self.do_hook,(event,to))

    def on_topicinfo(self, c, event):
        to = event.arguments()[0]
        if (self.channels.has_key(to)):
            self.channels[to].topic_nick = event.arguments()[1]
            self.channels[to].topic_time = event.arguments()[2]
        else:
            self.msg("topicinfo: chan '"+to+"' not known")
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
        dir = os.path.join(self._config['directory'], self._config['hooks'], event.eventtype())

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
        cmd = os.path.join(self._config['directory'], self._config['commands'], c.group(1))

        # get the msg
        msg = c.group(2)
       
        # execute the command handler
        return self.do_prog(event, to, cmd, msg)
    
    def do_prog(self, event, to, cmd, msg):

        # make sure we have rights to execute the command handler
        if not os.access(cmd,os.X_OK):
            return
       
        # open a new process with I/O pipes
        write,read = os.popen2(cmd)

        # write the command parameters to the command handler's STDIN
        write.write("type "+event.eventtype()+"\n")
        if isinstance(event.source(), str):
            write.write("nick "+nm_to_n(event.source())+"\n")
            if event.source().find('!') > 0: 
                write.write("user "+ \
                    nm_to_u(event.source())+"\n")
            if event.source().find('@') > 0: 
                write.write("host "+ \
                    nm_to_h(event.source())+"\n")
        if isinstance(to, str):
            write.write("to "+to+"\n")
        if isinstance(msg, str):
            write.write("msg "+msg+"\n")
        write.write("currentnick %s\n" % self.connection.get_nickname())
        write.close()

        # process the output from the command handler
        ret = self.process(read, to, event)
        read.close()

        return ret
    
    def process(self, sockfile, to = None, event = None):
        ret = "ok"
        sendnext = False
        rw = (sockfile.mode != 'r')

        for line in sockfile:
            line = line.rstrip("\n")

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
                self.msg("Exiting!")
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
            
            self.msg("Unknown request: "+line)

        return ret
    
    def server(self):

        # calculate path to command socket
        file = os.path.join(self._config['directory'], self._config['socket'])

        self.msg("Creating control socket: %s" % file)
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
        #what should I do with this:
        listen.close()
    
    def servclient(self, client):
        #self.msg("New control socket connection.")
        self.process(client.makefile('r+'))
        #self.msg("Closing control socket connection.")
        client.close()

    def msg(self, txt):
        print "hackabot:",txt

def main():
    if len(sys.argv) != 2:
        print "Usage:",sys.argv[0],"path/to/config.xml"
        sys.exit(1)

    bot = Hackabot(sys.argv[1])
    bot.start()

if __name__ == "__main__":
    main()
