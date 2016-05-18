have_json = True
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        have_json = False

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
            
    def __repr__(self):
        return "<arrowhead.core.services.Service at %#x: %s %s" % (
                id(self),
                self.name,
                self.type,
                )

if have_json:
    def service_parse_json(jsonstr):
        d = json.loads(jsonstr)
        print(repr(d))
        params = { key: d.get(key, None) for key in ('name', 'type', 'host', 'port', 'domain') }
        params['properties'] = {}
        properties = d.get('properties', [])
        for p in properties:
            print(repr(p))
            try:
                params['properties'][p['name']] = p['value']
            except KeyError:
                continue
        return Service(**params)
