
class Service(object):
    def __init__(self, *, name, type, host, port, domain=None, properties=None):
        self.name = name
        self.type = type
        self.host = host
        self.port = port
        self.domain = domain
        if properties is not None:
            self.properties = properties
        else:
            self.properties = dict()
