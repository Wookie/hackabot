'''
This is a wrapper class around the hackabot acl file.
'''
import os
import sys
from llbase import llsd
from log import Log

class Acl(object):
    """
    Acl wrapper
    """

    # if for some reason the acl file fails to load, we
    # lock hackabot down hard by denying all access and 
    # sending a response msg that says the acl file failed
    # to load 
    DEFAULT_RULE = { 'action': 'deny', 'msg': 'acl file failed to load' }

    def __init__(self, acl_file = None):

        # get a handle to the log
        self._log = Log()

        # figure out the path to the acl file
        if acl_file:
            self._acl_file = acl_file
        else:
            # get the path to the acl
            self._acl_file = os.getenv('HACKABOT_ACL')
        
        if self._acl_file == None:
            self._log.critical('Could not load hackabot acl file')

        # load the acl's
        c = open(self._acl_file, 'r')
        fname = c.name
        self._acl = llsd.parse_xml(c.read())
        c.close()

        self._rules = {}
        if self._acl:
            # process the acl file
            self._process_acls(self._acl, fname) 
        else:
            self._log.warn('Acl file failed to load, no access is granted')
            self._apply_rule(Acl.DEFAULT_RULE, 'default', 1)

    def _process_acls(self, acl, filename):

        if not acl.has_key('rules'):
            self._log.warn('Acl file %s does not have any rules defined in it' % acl_file.name)

        rule_number = 1
        for rule in acl['rules']:

            if isinstance(rule, dict):
                # it is a rule definition
                self._apply_rule(rule, filename, rule_number)
                rule_number += 1

            elif isinstance(rule, str):
                # if it isn't an absolute path, join it with the conf dir
                if not os.path.isabs(rule):
                    rule = os.path.join(self.get_config_dir(), rule)

                # recursively apply acl rules
                acl_file = open(rule, 'r')
                tmp_acl = llsd.parse_xml(acl_file.read())
                self._process_acls(tmp_acl, acl_file.name)
                acl_file.close()

            else:
                self._log('Unknown rule type: %s' % type(rule))

    def _apply_rule(self, rule, filename, number):
        # get the pieces of the rule
        channel = None
        command = None
        person = None
        access = None
        action = None
        msg = None

        if rule.has_key('channel'):
            if isinstance(rule['channel'], list):
                channel = rule['channel']
            else:
                channel = [ rule['channel'] ]
        else:
            channel = [ '*' ]
        if rule.has_key('command'):
            if isinstance(rule['command'], list):
                command = rule['command']
            else:
                command = [ rule['command'] ]
        else:
            command = [ '*' ]
        if rule.has_key('person'):
            if isinstance(rule['person'], list):
                person = rule['person']
            else:
                person = [ rule['person'] ]
        else:
            person = [ '*' ]

        if rule.has_key('access'):
            access = rule['access']
        else:
            access = '*'
        if rule.has_key('action'):
            action = rule['action']
        if rule.has_key('msg'):
            msg = rule['msg']
        else:
            msg = ''

        if action is None:
            self._log.warn('rule %d from file %s does not have an action' % (number, filename))

        # generate the rules
        for ch in channel:
            for co in command:
                for p in person:
                    key = '%s-%s-%s-%s' % (ch, co, p, access)
                    self._rules[key] = { 'action': action, 'msg': msg }

    def check_action(self, channel = '*', command = '*', person = '*', access = '*'):
        """
        This function is tricky because we want to try all combinations frrom least
        specific to most specific. while updating the current action and msg until
        we fail to find a match.
        """

        # if you consider each bit in a 4-bit number as being either 0 for '*'
        # or 1 for the specified value, then the following order specifies from
        # most general to most specific.
        order = [ 0, 1, 2, 4, 8, 3, 5, 9, 6, 10, 12, 7, 11, 13, 14, 15 ]

        # assume the action is denied 
        action = 'deny'
        msg = ''

        # if they specify a parameter we have to check both '*' and the specified
        # parameter to make sure we cover all possibilities.  if they don't specify
        # a parameter we only check '*' for it.
        if channel != '*':
            channel = [ '*', channel ]
        else:
            channel = [ channel ]
        if command != '*':
            command = [ '*', command ]
        else:
            command = [ command ]
        if person != '*':
            person = [ '*', person ]
        else:
            person = [ person ]
        if access != '*':
            access = [ '*', access ]
        else:
            access = [ access ]

        # now check all possibilities from most general to most specific
        for o in order:

            # calculate the index for each parameter
            channel_idx = ((o & 0x8) >> 3)
            command_idx = ((o & 0x4) >> 2)
            person_idx = ((o & 0x2) >> 1)
            access_idx = (o & 0x1)

            # skip the combos that aren't possible
            if channel_idx == len(channel):
                continue
            if command_idx == len(command):
                continue
            if person_idx == len(person):
                continue
            if access_idx == len(access):
                continue

            # generate the combo key
            key = '%s-%s-%s-%s' % (channel[channel_idx], command[command_idx],
                                   person[person_idx], access[access_idx])

            if self._rules.has_key(key):
                action = self._rules[key]['action']
                msg = self._rules[key]['msg']
                self._log.info('%s => action: %s -- msg: %s' % (key, action, msg))
        
        return (action, msg)

    def dump_rules(self):
        for rule in self._rules:
            self._log.debug('%s' % rule)

    def has_key(self, key):
        return self._config.has_key(key)

    def get_acl_filename(self):
        return self._acl_file

    def get_config_dir(self):
        return os.path.dirname(self._acl_file)

    def __getitem__(self, key):
        if self._acl.has_key(key):
            return self._acl[key]
        return None


