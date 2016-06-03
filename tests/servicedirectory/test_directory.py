"""Test the arrowhead.servicedirectory.directory module"""

from unittest import mock
import blitzdb
from arrowhead.servicedirectory import directory
from arrowhead import services

def test_servicedirectory_ctor():
    """Verify that the constructor does not write to the database"""
    mock_database = mock.create_autospec(blitzdb.FileBackend)
    mydir = directory.ServiceDirectory(database=mock_database)
    assert mock_database.save.call_count == 0
    assert mock_database.commit.call_count == 0
    assert isinstance(mydir, directory.Directory)

def test_servicedirectory_publish():
    """Test ServiceDirectory.publish"""
    mock_database = mock.create_autospec(blitzdb.FileBackend)
    mydir = directory.ServiceDirectory(database=mock_database)
    service = services.service_dict(name='testservice')
    expected_service_entry = mydir.Service(service)
    mydir.publish(service=service)
    assert mock_database.save.call_count == 1
    assert mock_database.commit.call_count > 1
    service_entry = mock_database.save.call_args[0][0]
    for key in service.keys():
        assert getattr(service_entry, key) == getattr(expected_service_entry, key)
