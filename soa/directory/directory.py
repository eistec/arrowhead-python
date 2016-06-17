"""Arrowhead service directory implementation

:seealso:
    https://forge.soa4d.org/plugins/mediawiki/wiki/arrowhead-f/index.php/Mandatory_Core_Systems_and_Services
"""
import time
import calendar
import tempfile

import blitzdb

from .. import LogMixin
from ..services import Service as AHService, service_to_dict


def unix_now():
    """Get the current time in UTC as a Unix timestamp

    :returns: Current time in UTC, seconds since 1970-01-01 00:00:00
    :rtype: int
    """
    return calendar.timegm(time.gmtime())

class DirectoryException(Exception):
    """Service directory exception base class"""

class DoesNotExist(DirectoryException):
    """Service not found in directory"""

class Directory(LogMixin, object): # pylint: disable=too-few-public-methods
    """Directory base class"""

    DoesNotExist = DoesNotExist

    config_defaults = {}
    """Default configuration items, override in subclass"""

    def __init__(self, database=None):
        """Constructor

        If a database backend object is not provided, an ephemeral database will
        be created in memory which will be destroyed when the object is deleted.

        :param database: A database file name, or database object
        :type database: string or database
        """
        super().__init__()
        self.log.debug('Using blitzdb v %s', blitzdb.__version__)
        dbsettings = {'serializer_class': 'json'}
        if database is None:
            # TemporaryDirectory will delete the temporary directory when the
            # object is destroyed
            self._tempdir = tempfile.TemporaryDirectory()
            self.log.info("Using temporary database at '%s'", self._tempdir.name)
            self._db = blitzdb.FileBackend(self._tempdir.name, dbsettings)
        elif isinstance(database, str):
            # database is used as a file name
            self.log.info("Using database at '%s'", database)
            self._db = blitzdb.FileBackend(database, dbsettings)
        else:
            # database is used as-is
            self._db = database
        self._config = {}
        self.log.info('Directory initialized')
        self.log.debug('config: %r', [(k, v) for k, v in self._config.items()])
        self._notify_set = set()

    def _get_config_value(self, key):
        """Get a configuration value from the database

        :param key: the key to look up
        :type key: string
        :returns: The configuration value, or a default value if the key was not
            found in the database
        :rtype: varies
        """
        value = self._config.get(key, self.config_defaults[key])
        self.log.debug('Config get: %s => %r', key, value)
        return value

class ServiceDirectory(Directory):
    """Service directory main class"""

    class Service(blitzdb.Document):
        """Service database storage class"""

        class Meta(blitzdb.Document.Meta): # pylint: disable=too-few-public-methods
            """Database backend configuration metadata"""
            primary_key = 'name' #use the name of the service as the primary key

    config_defaults = {
        'lifetime': 30 * 60
        }


    def prune_old_services(self):
        """Delete all service entries that have timed out"""
        now = unix_now()
        services = self._db.filter(self.Service, {'deadline': {'$lt': now}})
        count = len(services)
        services.delete()
        self._db.commit()
        self.log.debug('pruned %u timed out services', count)

    def add_notify_callback(self, callback):
        """Register a callback to be executed whenever the service registry is updated

        This can be used to let users subscribe to events in the registry.
        The service registry will be passed as an argument to the callback.

        :param callback: The callback to register
        :type callback: callable(serviceregistry)
        """
        if callback in self._notify_set:
            return
        self._notify_set.add(callback)

    def del_notify_callback(self, callback):
        """Unregister a callback

        :param callback: The callback to unregister
        :type callback: callable(serviceregistry)
        """
        if callback not in self._notify_set:
            return
        self._notify_set.remove(callback)

    def _call_notify(self):
        """Call all registered callbacks"""
        self.prune_old_services()
        for func in self._notify_set:
            func()

    def publish(self, *, service):
        """Publish a service in the registry

        The service entry will be updated if it already exists, otherwise it
        will be created.

        :param service: The service to update
        :type service: dict
        """
        scopy = service_to_dict(service)
        # Add last updated time stamp and refresh deadline
        now = unix_now()
        lifetime = self._get_config_value('lifetime')
        scopy['updated'] = now
        scopy['deadline'] = now + lifetime
        self.log.debug('publish: %r', scopy)
        old_service = self._db.filter(self.Service, {'name': service.name})
        self.log.debug('remove %r', [s for s in old_service])
        old_service.delete()
        self._db.commit()
        service_entry = self.Service(scopy)
        self._db.save(service_entry)
        self._db.commit()
        self._call_notify()

    def unpublish(self, *, name):
        """De-register a service in the registry

        The service entry will be deleted from the registry if found.

        :param name: The name of the service to delete
        :type name: string
        """
        self.log.debug('unpublish: %s', name)
        service = self._db.filter(self.Service, {'name': name})
        if len(service) == 0:
            raise self.DoesNotExist()
        service.delete()
        self._db.commit()
        self._call_notify()

    def service(self, *, name):
        """Get a named service from the registry

        :param name: The name of the service to look up
        :type name: string

        :returns: A service entry
        :rtype: dict
        """
        self.log.debug('find %s', name)
        try:
            service = self._db.get(self.Service, {'name': name})
        except self.Service.DoesNotExist: #pylint: disable=no-member
            raise self.DoesNotExist('Not found: {}'.format(name))
        sdict = service.attributes.copy()
        # Delete the deadline and updated meta information before returning
        sdict.pop('deadline', None)
        sdict.pop('updated', None)
        return AHService(**sdict)

    def service_list(self, **search):
        """Get a list of services matching the given criteria

        Use an empty criteria to list all services.

        :param search: Search criteria as key: value pairs
        :type search: dict
        """
        self.log.debug('list %r', search)
        now = unix_now()
        # Find all services with deadline >= now
        criteria = {key: value for key, value in search.items()}
        criteria['deadline'] = {'$gte': now}
        service_records = self._db.filter(self.Service, criteria)
        service_dicts = [service.attributes.copy() for service in service_records]
        for srv in service_dicts:
            srv.pop('deadline', None)
            srv.pop('updated', None)
        res = [AHService(**srv) for srv in service_dicts]
        return res

    def types(self):
        """Get a set of all the service types currently registered

        :return: A set of service type names
        :rtype: set
        """
        slist = self.service_list()
        types = {service.type for service in slist}
        self.log.debug('types %r', types)
        return types
