"""Functions for serialization/deserialization of Arrowhead services"""
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        HAVE_JSON = False
else:
    HAVE_JSON = True

try:
    import xml.etree.ElementTree as ET
except ImportError:
    HAVE_XML = False
else:
    HAVE_XML = True

try:
    import link_header
except ImportError:
    HAVE_LINK_HEADER = False
else:
    HAVE_LINK_HEADER = True

SERVICE_ATTRIBUTES = ("name", "type", "host", "port", "domain")

__all__ = [
    'ServiceError',
    'service_dict',
    'service_from_json',
    'service_from_json_dict',
    'service_from_xml',
    'service_to_corelf',
    'service_to_json',
    'service_to_json_dict',
    'service_to_xml',
    'servicelist_to_corelf',
    'servicelist_to_json',
    'servicelist_to_xml']


class ServiceError(Exception):
    """Exception raised by run time errors in this module"""


def service_dict(**kwargs):
    """Create a new service dict"""
    res = {key: kwargs.get(key, None) for key in SERVICE_ATTRIBUTES}
    res['properties'] = kwargs.get('properties', {})
    return res

if HAVE_JSON:
    def service_from_json_dict(js_dict):
        """Create a service dict from a dict of the JSON representation

        This is suitable for passing already parsed JSON dicts to.

        :param js_dict: JSON dict
        :type js_dict: dict
        """
        attrs = {key: js_dict.get(key, None) for key in SERVICE_ATTRIBUTES}
        props = {}
        js_props = js_dict.get('properties', {'property': []})['property']
        for jprop in js_props:
            try:
                props[jprop['name']] = jprop['value']
            except KeyError:
                continue
        return service_dict(properties=props, **attrs)

    def service_from_json(jsonstr):
        """Create a service dict from a JSON string representation of the service

        The JSON string can be obtained from :meth:`arrowhead.services.service_to_json`

        :param jsonstr: JSON string representation of a service
        :type jsonstr: string
        """
        return service_from_json_dict(json.loads(jsonstr))

    def service_to_json_dict(service):
        """Convert a service dict to a JSON representation dict"""
        props = [{'name': name, 'value': value}
                 for name, value in service['properties'].items()]
        res = {key: service.get(key, None) for key in SERVICE_ATTRIBUTES}
        res['properties'] = {"property": props}
        return res

    def service_to_json(service):
        """Convert a JSON service dict to JSON text

        :param service: Service to convert
        :type service: dict
        :returns: The service encoded as an JSON string
        :rtype: string
        """
        return json.dumps(service_to_json_dict(service))


def service_to_xml(service):
    """Convert a service dict to an XML representation

    :param service: Service to convert
    :type service: dict
    :returns: The service encoded as an XML string
    :rtype: string
    """
    # note: Does not use any xml functions, hence unaffected by HAVE_XML
    props = ''.join(
        ('<property><name>%s</name><value>%s</value></property>' % (k, v))
        for (k, v) in service['properties'].items())
    xml_str = (
        '<service>'
        '<domain>%s</domain>'
        '<host>%s</host>'
        '<name>%s</name>'
        '<port>%u</port>'
        '<properties>%s</properties>'
        '</service>') % (service['domain'],
                         service['host'],
                         service['name'],
                         service['port'],
                         props)
    return xml_str

if HAVE_XML:
    def service_from_xml(xmlstr):
        """Convert XML representation of service to service dict"""
        res = service_dict()
        root = ET.fromstring(xmlstr)
        for node in root:
            if node.tag in res and res[node.tag]:
                # disallow multiple occurrences of the same tag
                raise ServiceError(
                    "Multiple occurrence of tag <%s>" %
                    node.tag, res[node.tag], node.text)
            if node.tag in SERVICE_ATTRIBUTES:
                res[node.tag] = node.text.strip()
                # ignoring any XML attributes or child nodes
            elif node.tag == 'properties':
                props = {}
                for child_node in node:
                    if child_node.tag != 'property':
                        # ignoring any unknown tags
                        continue
                    name = None
                    value = None
                    for child_prop in child_node:
                        if child_prop.tag == 'name':
                            if name is not None:
                                raise ServiceError(
                                    "Multiple occurrence of property tag <%s>" %
                                    child_prop.tag, child_prop.tag, child_prop.text)
                            name = child_prop.text.strip()
                        elif child_prop.tag == 'value':
                            if value is not None:
                                raise ServiceError(
                                    "Multiple occurrence of property tag <%s>" %
                                    child_prop.tag, child_prop.tag, child_prop.text)
                            value = child_prop.text.strip()
                        # ignoring any unknown tags
                    if not name:
                        raise ServiceError(
                            "Missing property name (value=%s)" % value)
                    if name in props:
                        raise ServiceError(
                            "Multiple occurrence of property '%s'" %
                            name, name, value, props[name])
                    props[name] = value
                res['properties'] = props
            # ignoring any unknown tags
        return res


def service_to_corelf(service):
    """Convert a service dict to CoRE Link-format (:rfc:`6690`)

    :param service: Service to convert
    :type service: dict
    """
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


if HAVE_JSON:
    def servicelist_to_json(slist):
        """Convert a list of service dicts to a JSON string

        :param slist: List of services to convert
        :type slist: iterable
        :returns: The service list encoded as a JSON string
        :rtype: string
        """
        return json.dumps({'service': [service_to_json_dict(s) for s in slist]})


def servicelist_to_xml(slist):
    """Convert a list of service dicts to an XML string

    :param slist: List of services to convert
    :type slist: iterable
    :returns: The service list encoded as an XML string
    :rtype: string
    """

    return '<serviceList>' + \
        ''.join([service_to_xml(s) for s in slist]) + '</serviceList>'


if HAVE_LINK_HEADER:
    def servicelist_to_corelf(slist, uri_base):
        """Convert a list of services to a CoRE Link-format (:rfc:`6690`) string

        :param slist: List of services to convert
        :type slist: iterable
        :param uri_base: Base URI for the links
        :type uri_base: string
        :returns: The service list encoded as an application/link-format string
        :rtype: string
        """
        return link_header.format_links(
            [link_header.Link('{0}/{1}'.format(uri_base, s['name'])) for s in slist])

if HAVE_JSON:
    def typelist_to_json(tlist):
        """Convert a list of service dicts to a JSON string

        :param tlist: List of service types to convert
        :type tlist: iterable
        :returns: The service list encoded as a JSON string
        :rtype: string
        """
        return json.dumps({'serviceType': list(tlist)})


if HAVE_LINK_HEADER:
    def typelist_to_corelf(tlist, uri_base):
        """Convert a list of services to a CoRE Link-format (:rfc:`6690`) string

        :param tlist: List of service types to convert
        :type tlist: iterable
        :param uri_base: Base URI for the links
        :type uri_base: string
        :returns: The service list encoded as an application/link-format string
        :rtype: string
        """
        return link_header.format_links(
            [link_header.Link('{0}/{1}'.format(uri_base, t)) for t in tlist])
