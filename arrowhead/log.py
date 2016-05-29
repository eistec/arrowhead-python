"""Logging functionality used by other parts of the arrowhead package"""
import logging


class LogMixin(object):
    """Log mixin class

    Inherit from this class to get a self.log logger object for logging runtime
    messages.
    """

    def __init__(self, *args, logger=None, loggername=None, **kwargs):
        """Constructor

        :param args: positional arguments to pass on to other constructors in
            the class hierarchy
        :param logger: Logger object to store in self.log, a new object will be
            created if not provided
        :param loggername: If creating a new logger, use this name,
            default: _modulename.classname_
        :type loggername: str
        :param kwargs: keyword arguments to pass on to other constructors in
            the class hierarchy
        """
        super().__init__(*args, **kwargs)
        if logger is None and not loggername:
            loggername = '.'.join(
                (self.__class__.__module__, self.__class__.__name__))
        self.log = logger or logging.getLogger(loggername)
