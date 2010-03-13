'''
This is the base class for a hackabot hook.
'''

# import the base class
from action import Action


class Hook(Action):
    """
    Base class for all python hackabot hooks
    """

    def __init__(self, hook):
        super(Hook, self).__init__(hook)

