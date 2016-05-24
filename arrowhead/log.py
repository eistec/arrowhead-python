import logging
class LogMixin(object):
    '''Log mixin object'''
    def __init__(self, *args, logger=None, loggername=None, **kwargs):
        super().__init__(*args, **kwargs)
        if logger is None and not loggername:
            loggername = '.'.join((self.__class__.__module__, self.__class__.__name__))
        self.log = logger or logging.getLogger(loggername)

