import time
import calendar
from tinydb import TinyDB, where
from ..log import LogMixin

def unix_now():
    return calendar.timegm(time.gmtime())

class ServiceDirectory(LogMixin, object):
    config_defaults = {
        'ttl': 30 * 60
    }
    def __init__(self, database):
        super().__init__()
        if isinstance(database, str):
            # database is used as a file name
            self.log.debug("loading database from '%s'", database)
            self._db = TinyDB(database)
        else:
            # database is used as-is
            self._db = database
        self.log.info('Directory initialized, tables: %r', self._db.tables())
        self.log.debug('config: %r', self._get_config_table().all())
        self._notify_set = set()

    def _get_config_value(self, key):
        return self._get_config_table().get(where('key') == key) or self.config_defaults[key]

    def prune_old_services(self):
        table = self._get_service_table()
        now = unix_now()
        if table.contains(where('deadline') < now):
            ids = table.remove(where('deadline') < now)
            self.log.debug('pruned %u timed out services', len(ids))

    def add_notify_callback(self, callback):
        if callback in self._notify_set:
            return
        self._notify_set.add(callback)

    def del_notify_callback(self, callback):
        if callback not in self._notify_set:
            return
        self._notify_set.remove(callback)

    def _call_notify(self):
        self.prune_old_services()
        for cb in self._notify_set:
            cb()

    def _get_service_table(self):
        return self._db.table('services')

    def _get_config_table(self):
        return self._db.table('config')

    def publish(self, *, service):
        s = service.copy()
        now = unix_now()
        ttl = self._get_config_value('ttl')
        s['updated'] = now
        s['deadline'] = now + ttl
        self.log.debug('publish: %r' % (s, ))
        table = self._get_service_table()
        if table.contains(where('name') == s['name']):
            table.update(s, where('name') == s['name'])
        else:
            table.insert(s)
        self._call_notify()

    def unpublish(self, *, name):
        self.log.debug('unpublish: %s' % (name, ))
        self._get_service_table().remove(where('name') == name)
        self._call_notify()

    def service(self, *, name=None):
        table = self._get_service_table()
        if name is not None:
            return table.get(where('name') == name)
        else:
            now = unix_now()
            return table.search(where('deadline') >= now)

    def types(self, *, type=None):
        table = self._get_service_table()
        now = unix_now()
        if type is not None:
            return table.search((where('type') == type) & (where('deadline') >= now))
        else:
            return [v['type'] for v in table.search(where('deadline') >= now)]
