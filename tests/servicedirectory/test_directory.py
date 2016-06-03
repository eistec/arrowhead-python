"""Test the arrowhead.servicedirectory.directory module"""
#pylint: disable=no-member
# pylint doesn't understand mock objects

from unittest import mock
import tempfile

import pytest
import blitzdb

from arrowhead.servicedirectory import directory
from arrowhead import services

from ..test_data import EXAMPLE_SERVICES

def test_servicedir_ctor_nowrite():
    """Verify that the constructor does not write to the database"""
    mock_database = mock.create_autospec(blitzdb.FileBackend)
    mydir = directory.ServiceDirectory(database=mock_database)
    assert mock_database.save.call_count == 0
    assert mock_database.commit.call_count == 0
    assert isinstance(mydir, directory.Directory)

def test_servicedir_ctor_dir():
    """Verify that the constructor creates a database in the given directory"""
    db_dir = tempfile.TemporaryDirectory()
    with mock.patch('arrowhead.servicedirectory.directory.blitzdb.FileBackend'):
        mydir = directory.ServiceDirectory(database=db_dir.name)
        directory.blitzdb.FileBackend.assert_called_once_with(db_dir.name, mock.ANY)
        assert isinstance(mydir, directory.Directory)

def test_servicedir_ctor_nodir():
    """Verify that the constructor creates a temporary database if not given a directory"""
    with mock.patch('arrowhead.servicedirectory.directory.blitzdb.FileBackend'):
        mydir = directory.ServiceDirectory(database=None)
        assert directory.blitzdb.FileBackend.call_count == 1
        arg = directory.blitzdb.FileBackend.call_args[0][0]
        assert arg.startswith(tempfile.gettempdir())
        assert isinstance(mydir, directory.Directory)

def test_servicedir_publish():
    """Test ServiceDirectory.publish"""
    mock_database = mock.create_autospec(blitzdb.FileBackend)
    mydir = directory.ServiceDirectory(database=mock_database)
    for service_dict in EXAMPLE_SERVICES.values():
        mock_database.reset_mock()
        service = services.service_dict(**service_dict['service'])
        expected_service_entry = mydir.Service(service)
        mydir.publish(service=service)
        assert mock_database.save.call_count == 1
        assert mock_database.commit.call_count > 1
        service_entry = mock_database.save.call_args[0][0]
        for key in service.keys():
            assert getattr(service_entry, key) == getattr(expected_service_entry, key)

def test_servicedir_unpublish():
    """Test ServiceDirectory.unpublish"""
    db_dir = tempfile.TemporaryDirectory()
    mydir = directory.ServiceDirectory(database=db_dir.name)
    for service_dict in EXAMPLE_SERVICES.values():
        service = services.service_dict(**service_dict['service'])
        with pytest.raises(mydir.DoesNotExist):
            mydir.unpublish(name=service['name'])
        mydir.publish(service=service)
    for service_dict in EXAMPLE_SERVICES.values():
        service = services.service_dict(**service_dict['service'])
        mydir.unpublish(name=service['name'])
        with pytest.raises(mydir.DoesNotExist):
            mydir.unpublish(name=service['name'])

def test_servicedir_service():
    """Test ServiceDirectory.service"""
    db_dir = tempfile.TemporaryDirectory()
    mydir = directory.ServiceDirectory(database=db_dir.name)
    for service_dict in EXAMPLE_SERVICES.values():
        service = services.service_dict(**service_dict['service'])
        with pytest.raises(mydir.DoesNotExist):
            mydir.service(name=service['name'])
        mydir.publish(service=service)
    for service_dict in EXAMPLE_SERVICES.values():
        service = services.service_dict(**service_dict['service'])
        output = mydir.service(name=service['name'])
        for key in service.keys():
            assert output[key] == service[key]
    for service_dict in EXAMPLE_SERVICES.values():
        mydir.unpublish(name=service_dict['service']['name'])
        with pytest.raises(mydir.DoesNotExist):
            mydir.service(name=service_dict['service']['name'])

def test_servicedir_service_list():
    """Test ServiceDirectory.service_list, ServiceDirectory.types"""
    db_dir = tempfile.TemporaryDirectory()
    mydir = directory.ServiceDirectory(database=db_dir.name)
    count = 0
    for service_dict in EXAMPLE_SERVICES.values():
        service = services.service_dict(**service_dict['service'])
        mydir.publish(service=service)
        count += 1
        output = mydir.service_list()
        assert service['name'] in [srv['name'] for srv in output]
        assert len(output) == count
        output = mydir.types()
        assert service['type'] in output
    for service_dict in EXAMPLE_SERVICES.values():
        output = mydir.service_list()
        assert service_dict['service']['name'] in [srv['name'] for srv in output]
        mydir.unpublish(name=service_dict['service']['name'])
        count -= 1
        output = mydir.service_list()
        assert service_dict['service']['name'] not in [srv['name'] for srv in output]
        assert len(output) == count
    assert len(mydir.types()) == 0

def test_servicedir_callbacks():
    """Test ServiceDirectory.add_notify_callback, ServiceDirectory.del_notify_callback"""
    callback = mock.MagicMock()
    db_dir = tempfile.TemporaryDirectory()
    mydir = directory.ServiceDirectory(database=db_dir.name)
    mydir.add_notify_callback(callback)
    mydir.add_notify_callback(callback)
    mydir.add_notify_callback(callback)
    assert callback.call_count == 0
    service = services.service_dict(name='testservice')
    mydir.publish(service=service)
    assert callback.call_count == 1
    mydir.unpublish(name=service['name'])
    assert callback.call_count == 2
    mydir.del_notify_callback(callback)
    mydir.publish(service=service)
    assert callback.call_count == 2
    mydir.del_notify_callback(callback)
    mydir.unpublish(name=service['name'])
    assert callback.call_count == 2
