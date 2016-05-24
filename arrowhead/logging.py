import logging
class LoggingMixin(object):
    '''Logging mixin object'''
    def __init__(self, loggername, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.log = logging.getLogger(loggername)

