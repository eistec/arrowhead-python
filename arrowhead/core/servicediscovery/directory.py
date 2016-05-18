from tinydb import TinyDB, where

class ServiceDirectory(object):
    def __init__(self, database):
        if isinstance(database, str):
            # database is used as a file name
            self._db = TinyDB(database)
        else:
            # database is used as-is
            self._db = database
        
    def publish(self, *, service):
        if self._db.contains(where('name') == service.name):
            self._db.update(service.__dict__, where('name') == service.name)
        else:
            self._db.insert(service.__dict__)
    
    def unpublish(self, *, name):
        self._db.remove(where('name') == name)
    
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
