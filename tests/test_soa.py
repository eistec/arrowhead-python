"""Test top level soa module"""
import logging
import soa

def test_log_mixin():
    """Test that the LogMixin provides a log object"""
    class TestLog(soa.LogMixin, object): #pylint: disable=too-few-public-methods
        """Test class"""

    class MyLogger(object): #pylint: disable=too-few-public-methods
        """Mock logger object"""

    logger = MyLogger()
    testlog = TestLog(logger=logger)
    assert testlog.log is logger
    testlog2 = TestLog()
    assert isinstance(testlog2.log, logging.Logger)
    assert testlog2.log.name == '.'.join((__name__, 'TestLog'))
