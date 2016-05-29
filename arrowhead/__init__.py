"""This module provides a Python API for interacting with Arrowhead services"""

import logging
from logging import NullHandler

from . import services, log

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(NullHandler())

__version__ = '0.1.0-alpha'

__all__ = ['services', 'logging']
