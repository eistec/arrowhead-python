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

from aiocoap.numbers import media_types_rev
import attr

SERVICE_ATTRIBUTES = ("name", "type", "host", "port", "domain")

__all__ = [
    'Service',
    'ServiceError',
    'servicelist_to_xml',
    'servicelist_to_json',
    'typelist_to_json',
    'servicelist_to_corelf',
    'typelist_to_corelf',
    ]


class ServiceError(RuntimeError):
    """Exception raised by run time errors in this module"""

class UnknownContentError(ServiceError):
    """Exception raised by run time errors in this module"""


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

    # Mapping content types in CoAP to translator function name prefix
    media_type_to_name = {
        media_types_rev['application/json']: 'json',
        media_types_rev['application/xml']: 'xml',
    }

    @classmethod
    def from_message(cls, message):
        """Create a Service object from a CoAP Message"""
        # Dispatch handling of the request payload to a handler based on the
        # given Content-format option
        try:
            input_handler = getattr(
                cls, 'from_' + cls.media_type_to_name[message.opt.content_format])
        except LookupError:
            raise UnknownContentError(
                "No translator for media type {}".format(message.opt.content_format))
        else:
            return input_handler(message.payload)

    @classmethod
    def from_json_dict(cls, js_dict):
        """Create a Service object from a dict of the JSON representation

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
        return cls(properties=props, **attrs)

    @classmethod
    def from_json(cls, payload):
        """Create a Service object from a JSON string representation of the service

        The JSON string can be obtained from :meth:`soa.services.service_to_json`

        :param payload: JSON string representation of a service
        :type payload: string or bytes
        """
        try:
            try:
                jsonstr = payload.decode('utf-8')
            except AttributeError:
                jsonstr = payload
            return cls.from_json_dict(json.loads(jsonstr))
        except ValueError as exc:
            raise ServiceError(
                'ValueError while parsing JSON service: {}'.format(str(exc)))

    def to_bytes(self, media_type):
        """Serialize a Service to the given content type"""

        # Dispatch handling of the request payload to a handler based on the
        # given Content-format option
        try:
            output_handler = getattr(self, 'to_' + self.media_type_to_name[media_type])
        except LookupError:
            raise UnknownContentError("No translator for media type {}".format(media_type))
        buf = output_handler()
        try:
            # encode from str to bytes object
            buf = buf.encode('utf-8')
        except AttributeError:
            # buf is already encoded or not a str
            pass
        return buf


    def to_dict(self):
        """Copy the values of a Service into a new dict"""
        srv_dict = attr.asdict(self)
        # convert SimpleNamespace to dict
        props = srv_dict['properties']
        srv_dict['properties'] = {key: getattr(props, key) for key in props.__dict__.keys()}
        return srv_dict

    def to_json_dict(self):
        """Convert a Service to a JSON representation dict

        Kludge which will go away if the SD JSON interface spec is improved"""
        srv_dict = attr.asdict(self)
        # convert SimpleNamespace to dict
        props = srv_dict['properties']
        srv_dict['properties'] = {
            "property": [{'name': key, 'value': getattr(props, key)} \
            for key in props.__dict__.keys()]}
        return srv_dict

    def to_json(self):
        """Convert a JSON service dict to JSON text

        :param self: Service to convert
        :type self: Service
        :returns: The service encoded as an JSON string
        :rtype: string
        """
        return json.dumps(self.to_json_dict())

    def to_xml(self):
        """Convert a service dict to an XML representation

        :param self: Service to convert
        :type self: Service
        :returns: The service encoded as an XML string
        :rtype: string
        """
        # note: Does not use any xml functions, hence unaffected by HAVE_XML
        props = ''.join(
            ('<property><name>%s</name><value>%s</value></property>' %
             (key, getattr(self.properties, key)))
            for key in self.properties.__dict__.keys())
        xml_str = (
            '<service>'
            '<name>%s</name>'
            '<type>%s</type>'
            '<domain>%s</domain>'
            '<host>%s</host>'
            '<port>%s</port>'
            '<properties>%s</properties>'
            '</service>') % (self.name,
                             self.type,
                             self.domain,
                             self.host,
                             self.port,
                             props)
        return xml_str

    @staticmethod
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

    @classmethod
    def from_xml(cls, xmlstr):
        """Convert XML representation of service to service dict"""
        res = cls()
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

                props = cls._service_parse_xml_props(node)
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


    def to_corelf(self):
        """Convert a service dict to CoRE Link-format (:rfc:`6690`)

        :param self: Service to convert
        :type self: Service
        """
        host = str(self.host)
        if ':' in host:
            # assume IPv6 address, wrap in brackets for URL construction
            host = '[%s]' % host
        port = str(self.port)
        if port:
            port = ':' + port
        path = getattr(self.properties, 'path', '/')
        if path and path[0] != '/':
            path = '/' + path
        link_str = '<coap://%s%s%s>' % (host, port, path)
        return link_str


def servicelist_to_json(slist):
    """Convert a list of service dicts to a JSON string

    :param slist: List of services to convert
    :type slist: iterable
    :returns: The service list encoded as a JSON string
    :rtype: string
    """
    return json.dumps({'service': [srv.to_json_dict() for srv in slist]})


def servicelist_to_xml(slist):
    """Convert a list of service dicts to an XML string

    :param slist: List of services to convert
    :type slist: iterable
    :returns: The service list encoded as an XML string
    :rtype: string
    """

    return '<serviceList>' + \
        ''.join([srv.to_xml() for srv in slist]) + '</serviceList>'


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

def typelist_to_json(tlist):
    """Convert a list of service dicts to a JSON string

    :param tlist: List of service types to convert
    :type tlist: iterable
    :returns: The service list encoded as a JSON string
    :rtype: string
    """
    return json.dumps({'serviceType': list(tlist)})

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
