have_json = True
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        have_json = False

have_xml = True
try:
    import xml.etree.ElementTree as ET
except ImportError:
    have_xml = False

service_attributes = ("name", "type", "host", "port", "domain")

class ServiceError(Exception):
    pass

def service_dict(**kwargs):
    '''Create a new service dict'''
    print(kwargs)
    res = { key: kwargs.get(key, None) for key in service_attributes }
    res['properties'] = kwargs.get('properties', {})
    return res

if have_json:
    def service_from_json_dict(js_dict):
        d = js_dict
        attrs = { key: d.get(key, None) for key in service_attributes }
        props = {}
        jp = d.get('properties', {'property': []})['property']
        for p in jp:
            try:
                props[p['name']] = p['value']
            except KeyError:
                continue
        return service_dict(properties=props, **attrs)

    def service_from_json(jsonstr):
        return service_from_json_dict(json.loads(jsonstr))

    def service_to_json_dict(service):
        '''Convert a service dict to a JSON representation dict'''
        props = [ { 'name': name, 'value': value } for name, value in service['properties'].items() ]
        res = {key: service.get(key, None) for key in service_attributes}
        res['properties'] = {"property": props}
        return res

    def service_to_json(service):
        '''Convert a JSON service dict to JSON text'''
        return json.dumps(service_to_json_dict(service))

def service_to_xml(service):
    '''Convert a service dict to an XML representation'''
    # note: Does not use any xml functions, hence unaffected by have_xml
    props = ''.join(('<property><name>%s</name><value>%s</value></property>' % (k, v)) for (k, v) in service['properties'].items())
    xml_str = (
        '<service>'
            '<domain>%s</domain>'
            '<host>%s</host>'
            '<name>%s</name>'
            '<port>%u</port>'
            '<properties>%s</properties>'
        '</service>') % (
            service['domain'], service['host'], service['name'], service['port'], props)
    return xml_str

if have_xml:
    def service_from_xml(xmlstr):
        res = service_dict()
        root = ET.fromstring(xmlstr)
        for child in root:
            if child.tag in res:
                # disallow multiple occurrences of the same tag
                raise ServiceError("Multiple occurrence of tag <%s>" % child.tag, child.tag, child.text)
            if child.tag in service_attributes:
                res[child.tag] = child.text.strip()
                # ignoring any XML attributes or child nodes
            elif child.tag == 'properties':
                props = {}
                for c in child:
                    if c.tag != 'property':
                        # ignoring any unknown tags
                        continue
                    name = None
                    value = None
                    for pc in c:
                        if pc.tag == 'name':
                            if name is not None:
                                raise ServiceError("Multiple occurrence of property tag <%s>" % pc.tag, pc.tag, pc.text)
                            name = pc.text.strip()
                        elif pc.tag == 'value':
                            if value is not None:
                                raise ServiceError("Multiple occurrence of property tag <%s>" % pc.tag, pc.tag, pc.text)
                            value = pc.text.strip()
                        # ignoring any unknown tags
                    if not name:
                        raise ServiceError("Missing property name (value=%s)" % value)
                    if name in props:
                        raise ServiceError("Multiple occurrence of property '%s'" % name, name, value, props[name])
                    props[name] = value
                res['properties'] = props
            # ignoring any unknown tags
        return res

def service_to_corelf(service):
    '''Convert a service dict to CoRE Link-format'''
    host = str(service['host'])
    if ':' in host:
        # assume IPv6 address, wrap in brackets for URL construction
        host = '[%s]' % host
    port = str(service['port'])
    if port:
        port = ':' + port
    path = service['properties'].get('path', '/')
    if path and path[0] != '/':
        path = '/' + path
    link_str = '<coap://%s%s%s>' % (host, port, path)
    return link_str

def servicelist_to_json(slist):
    return json.dumps({'service': [service_to_json_dict(s) for s in slist]})

def servicelist_to_xml(slist):
    return '<serviceList>' + ''.join([service_to_xml(s) for s in slist]) + '</serviceList>'

def servicelist_to_corelf(slist):
    '''Return a core link-format string for the given services'''
    return ','.join([service_to_corelf(s) for s in slist])
