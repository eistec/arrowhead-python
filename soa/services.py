"""Functions for serialization/deserialization of Arrowhead services"""
from types import SimpleNamespace

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

import attr

SERVICE_ATTRIBUTES = ("name", "type", "host", "port", "domain")

__all__ = [
    'Service',
    'ServiceError',
    'service_to_xml',
    'servicelist_to_xml',
    'service_to_corelf',
    ]

if HAVE_JSON:
    __all__.extend([
        'service_from_json',
        'service_from_json_dict',
        'service_to_json',
        'service_to_json_dict',
        'servicelist_to_json',
        'typelist_to_json',
    ])

if HAVE_XML:
    __all__.extend([
        'service_from_xml',
    ])

if HAVE_LINK_HEADER:
    __all__.extend([
        'servicelist_to_corelf',
        'typelist_to_corelf',
    ])


@attr.s # pylint: disable=too-few-public-methods
class Service(object):
    """Service description class

    This class contains the same fields as are available in the service registry
    """
    name = attr.ib(default=None)
    type = attr.ib(default=None)
    host = attr.ib(default=None, hash=False)
    port = attr.ib(default=None, hash=False)
    domain = attr.ib(default=None, hash=False)
    properties = attr.ib(
        default={}, hash=False,
        convert=lambda prop_dict: SimpleNamespace(**prop_dict))


class ServiceError(RuntimeError):
    """Exception raised by run time errors in this module"""


def service_to_dict(service):
    """Copy the values of a Service into a new dict"""
    srv_dict = attr.asdict(service)
    props = srv_dict['properties']
    srv_dict['properties'] = {key: getattr(props, key) for key in props.__dict__.keys()}
    return srv_dict

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
        return Service(properties=props, **attrs)

    def service_from_json(payload):
        """Create a service dict from a JSON string representation of the service

        The JSON string can be obtained from :meth:`soa.services.service_to_json`

        :param payload: JSON string representation of a service
        :type payload: string or bytes
        """
        try:
            if not isinstance(payload, str):
                jsonstr = payload.decode('utf-8')
            else:
                jsonstr = payload
            return service_from_json_dict(json.loads(jsonstr))
        except ValueError as exc:
            raise ServiceError(
                'ValueError while parsing JSON service: {}'.format(str(exc)))

    def service_to_json_dict(service):
        """Convert a Service to a JSON representation dict"""
        props = [{'name': key, 'value': value} \
            for key, value in service.properties.__dict__.items()]
        res = {key: getattr(service, key) for key in SERVICE_ATTRIBUTES}
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
        for (k, v) in service.properties.__dict__.items())
    xml_str = (
        '<service>'
        '<name>%s</name>'
        '<type>%s</type>'
        '<domain>%s</domain>'
        '<host>%s</host>'
        '<port>%s</port>'
        '<properties>%s</properties>'
        '</service>') % (service.name,
                         service.type,
                         service.domain,
                         service.host,
                         service.port,
                         props)
    return xml_str

if HAVE_XML:
    def _service_parse_xml_props(node):
        """Parse the ``<properties>`` XML tag

        :param node: XML ``<properties>`` node
        :type node: xml.etree.ElementTree.Element
        :returns: Parsed properties as key=>value pairs
        :rtype: dict
        """
        props = {}
        for child_node in node:
            if child_node.tag != 'property':
                # ignoring any unknown tags
                continue
            values = {'name': None, 'value': None}
            for child_prop in child_node:
                if child_prop.tag not in values:
                    raise ServiceError(
                        "Unknown property tag <%s>" %
                        child_prop.tag)
                if values[child_prop.tag] is not None:
                    raise ServiceError(
                        "Multiple occurrence of property tag <%s>: '%s', '%s'" %
                        child_prop.tag, values[child_prop.tag], child_prop.text)
                values[child_prop.tag] = child_prop.text and child_prop.text.strip() or ''

            for key, value in values.items():
                if value is None:
                    raise ServiceError(
                        "Missing property %s" % (key, ))
            if values['name'] in props:
                raise ServiceError(
                    "Multiple occurrence of property '{}': '{}', '{}'".format(
                        values['name'], props[values['name']], values['value']))
            props[values['name']] = values['value']
        return props

    def service_from_xml(xmlstr):
        """Convert XML representation of service to service dict"""
        res = Service()
        try:
            root = ET.fromstring(xmlstr)
        except ET.ParseError:
            raise ServiceError('Invalid XML service')
        if root.tag != 'service':
            raise ServiceError('Missing <service> tag')
        for node in root:
            if node.tag == 'properties':
                if len(res.properties.__dict__) > 0:
                    raise ServiceError(
                        "Multiple occurrence of tag <%s>" %
                        node.tag, getattr(res, node.tag), node.text)

                props = _service_parse_xml_props(node)
                res.properties.__dict__.update(props)
            elif node.tag not in SERVICE_ATTRIBUTES:
                raise ServiceError(
                    "Unknown service tag <%s>" %
                    node.tag)
            elif getattr(res, node.tag) is not None:
                # disallow multiple occurrences of the same tag
                raise ServiceError(
                    "Multiple occurrence of tag <%s>" %
                    node.tag, getattr(res, node.tag), node.text)
            else:
                val = node.text and node.text.strip() or ''
                if node.tag == 'port':
                    val = int(val)
                setattr(res, node.tag, val)
                if list(node):
                    raise ServiceError(
                        "Nested service tag <{0}>{1}</{0}>".format(
                            node.tag, repr(list(node))))
        return res


def service_to_corelf(service):
    """Convert a service dict to CoRE Link-format (:rfc:`6690`)

    :param service: Service to convert
    :type service: dict
    """
    host = str(service.host)
    if ':' in host:
        # assume IPv6 address, wrap in brackets for URL construction
        host = '[%s]' % host
    port = str(service.port)
    if port:
        port = ':' + port
    path = getattr(service.properties, 'path', '/')
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
            [link_header.Link('{0}/{1}'.format(uri_base, srv.name)) for srv in slist])

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
