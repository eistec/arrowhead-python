import time
import calendar
from tinydb import TinyDB, where
from ..logging import LoggingMixin

class ServiceDirectory(LoggingMixin, object):
    def __init__(self, database, loggername='directory'):
        super().__init__(loggername=loggername)
        if isinstance(database, str):
            # database is used as a file name
            self._db = TinyDB(database)
        else:
            # database is used as-is
            self._db = database
        self._notify_set = set()

    def add_notify_callback(self, callback):
        if callback in self._notify_set:
            return
        self._notify_set.add(callback)

    def del_notify_callback(self, callback):
        if callback not in self._notify_set:
            return
        self._notify_set.remove(callback)

    def _call_notify(self):
        for cb in self._notify_set:
            cb()

    def publish(self, *, service):
        s = service.copy()
        s['updated'] = calendar.timegm(time.gmtime())
        self.log.info('publish: %r' % (s, ))
        print('publish: %r' % (s, ))
        if self._db.contains(where('name') == s['name']):
            self._db.update(s, where('name') == s['name'])
        else:
            self._db.insert(s)
        self._call_notify()

    def unpublish(self, *, name):
        self._db.remove(where('name') == name)
        self._call_notify()

    def service(self, *, name=None):
        if name is not None:
            return self._db.search(where('name') == name)
        else:
            return self._db.all()

    def types(self, *, type=None):
        if type is not None:
            return self._db.search(where('type') == type)
        else:
            return [ v['type'] for v in self._db.all() ]
