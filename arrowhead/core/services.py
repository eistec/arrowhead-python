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
            try:
                props = {}
                for it in properties['property']:
                    try:
                        props[it['name']] = it['value']
                    except KeyError:
                        pass
                self.properties = props
            except KeyError:
                self.properties = { key: value for key, value in properties.items()}
        else:
            self.properties = {}
            
    def __repr__(self):
        return "<arrowhead.core.services.Service at %#x: %s (%s)" % (
                id(self),
                self.name,
                self.type,
                )
                
    def as_dict(self):
        """Get Service values as a dictionary"""
        res = {key: self.__dict__[key] for key in ("name", "type", "host", "port", "domain")}
        props = [ { 'name': name, 'value': value } for name, value in self.properties.items() ]
        res['properties'] = {"property": props}
        
        return res

    def as_json(self):
        d = self.as_dict()
        return json.dumps(d)

    def as_xml(self):
        props = ''.join(('<property><name>%s</name><value>%s</value></property>' % (k, v)) for (k, v) in self.properties.items())
        xml_str = (
            '<service>'
                '<domain>%s</domain>'
                '<host>%s</host>'
                '<name>%s</name>'
                '<port>%u</port>'
                '<properties>%s</properties>'
            '</service>') % (
                self.domain, self.host, self.name, self.port, props)
        return xml_str

    def as_link(self, services, request):
        link_str = ','.join(('<coap://[%s]:%s%s>' % (s.get('host', ''), s.get('port',  5683), s.get('properties',  {}).get('path', ''))) for s in services)
        return link_str.encode('utf-8')


if have_json:
    def service_parse_json(jsonstr):
        d = json.loads(jsonstr)
        print(repr(d))
        params = { key: d.get(key, None) for key in ('name', 'type', 'host', 'port', 'domain') }
        params['properties'] = {}
        properties = d.get('properties', {'property': []})['property']
        for p in properties:
            print(repr(p))
            try:
                params['properties'][p['name']] = p['value']
            except KeyError:
                continue
        return Service(**params)
