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

@pytest.yield_fixture
def temp_dir():
    """Create a service directory object with a temporary storage"""
    with tempfile.TemporaryDirectory() as db_dir:
        mydir = directory.ServiceDirectory(database=db_dir)
        yield mydir

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
        service = services.Service(**service_dict['service'])
        expected_service_entry = mydir.Service(service_dict['service'])
        mydir.publish(service=service)
        assert mock_database.save.call_count == 1
        assert mock_database.commit.call_count >= 1
        # some white box testing here: examine what was passed to the database's
        # save method
        service_entry = mock_database.save.call_args[0][0]
        for key in service_dict['service'].keys():
            assert getattr(service_entry, key) == getattr(expected_service_entry, key)

def test_servicedir_unpublish(temp_dir): #pylint: disable=redefined-outer-name
    """Test ServiceDirectory.unpublish"""
    for service_dict in EXAMPLE_SERVICES.values():
        service = services.Service(**service_dict['service'])
        with pytest.raises(temp_dir.DoesNotExist):
            temp_dir.unpublish(name=service.name)
        temp_dir.publish(service=service)
    for service_dict in EXAMPLE_SERVICES.values():
        service = services.Service(**service_dict['service'])
        temp_dir.unpublish(name=service.name)
        with pytest.raises(temp_dir.DoesNotExist):
            temp_dir.unpublish(name=service.name)

def test_servicedir_service(temp_dir): #pylint: disable=redefined-outer-name
    """Test ServiceDirectory.service"""
    for service_dict in EXAMPLE_SERVICES.values():
        service = services.Service(**service_dict['service'])
        with pytest.raises(temp_dir.DoesNotExist):
            temp_dir.service(name=service.name)
        temp_dir.publish(service=service)
    for service_dict in EXAMPLE_SERVICES.values():
        service = services.Service(**service_dict['service'])
        output = temp_dir.service(name=service.name)
        assert output == service

    for service_dict in EXAMPLE_SERVICES.values():
        temp_dir.unpublish(name=service_dict['service']['name'])
        with pytest.raises(temp_dir.DoesNotExist):
            temp_dir.service(name=service_dict['service']['name'])

def test_servicedir_service_list(temp_dir): #pylint: disable=redefined-outer-name
    """Test ServiceDirectory.service_list, ServiceDirectory.types"""
    count = 0
    for service_dict in EXAMPLE_SERVICES.values():
        service = services.Service(**service_dict['service'])
        temp_dir.publish(service=service)
        count += 1
        output = temp_dir.service_list()
        assert service.name in [srv.name for srv in output]
        assert len(output) == count
        output = temp_dir.types()
        assert service.type in output
    for service_dict in EXAMPLE_SERVICES.values():
        service = services.Service(**service_dict['service'])
        output = temp_dir.service_list(type=service.type)
        assert not [srv for srv in output if srv.type != service.type]
    for service_dict in EXAMPLE_SERVICES.values():
        output = temp_dir.service_list()
        assert service_dict['service']['name'] in [srv.name for srv in output]
        temp_dir.unpublish(name=service_dict['service']['name'])
        count -= 1
        output = temp_dir.service_list()
        assert service_dict['service']['name'] not in [srv.name for srv in output]
        assert len(output) == count
    assert len(temp_dir.types()) == 0

def test_servicedir_callbacks(temp_dir): #pylint: disable=redefined-outer-name
    """Test ServiceDirectory.add_notify_callback, ServiceDirectory.del_notify_callback"""
    callback = mock.MagicMock()
    temp_dir.add_notify_callback(callback)
    temp_dir.add_notify_callback(callback)
    temp_dir.add_notify_callback(callback)
    assert callback.call_count == 0
    service = services.Service(name='testservice')
    temp_dir.publish(service=service)
    assert callback.call_count == 1
    temp_dir.unpublish(name=service.name)
    assert callback.call_count == 2
    temp_dir.del_notify_callback(callback)
    temp_dir.publish(service=service)
    assert callback.call_count == 2
    temp_dir.del_notify_callback(callback)
    temp_dir.unpublish(name=service.name)
    assert callback.call_count == 2
