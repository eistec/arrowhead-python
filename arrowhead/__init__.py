# Top level Arrowhead package
__version__ = '0.1.0-alpha'

"""Modules for interacting with Arrowhead services

"""

# Set default logging handler to avoid "No handler found" warnings.
import logging
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):

        def emit(self, record):
            pass
logging.getLogger(__name__).addHandler(NullHandler())

__all__ = ['services', 'logging']

from . import services, log
