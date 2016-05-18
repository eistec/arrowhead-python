import asyncio
import aiocoap.resource as resource
from aiocoap.numbers import media_types_rev
import aiocoap

try:
    import json
except ImportError:
    import simplejson as json

from ..services import service_parse_json
from .directory import ServiceDirectory

_directory = ServiceDirectory('db.json')

class ServiceResource(resource.ObservableResource):
    """/service resource"""
    def __init__(self):
        super().__init__()

        self.notify()

    def notify(self):
        self.updated_state()
    
    def as_json(self, services, request):
        return json.dumps(services).encode('utf-8')

    def as_xml(self, services, request):
        xml_str = str()
        for s in services:
            props = ''.join(('<property><name>%s</name><value>%s</value></property>' % (k, v)) for (k, v) in s.get('properties',  {}).items())
            xml_str += '<service><domain>%s</domain><host>%s</host><name>%s</name><port>%s</port><properties>%s</properties>' % (
                s.get('domain', ''), s.get('host', ''), s.get('name',  ''), s.get('port',  5683), props)
            
        return xml_str.encode('utf-8')

    def as_link(self, services, request):
        link_str = ','.join(('<coap://[%s]:%s%s>' % (s.get('host', ''), s.get('port',  5683), s.get('properties',  {}).get('path', ''))) for s in services)
        return link_str.encode('utf-8')

    @asyncio.coroutine
    def render_get(self, request):
        srv = _directory.service()
        format = media_types_rev['text/plain']
        if request.opt.accept == media_types_rev['application/json']:
            payload = self.as_json(srv, request)
            format = media_types_rev['application/json']
        elif request.opt.accept == media_types_rev['application/link-format']:
            payload = self.as_link(srv, request)
            format = media_types_rev['application/link-format']
        elif request.opt.accept == media_types_rev['application/xml']:
            payload = self.as_xml(srv, request)
            format = media_types_rev['application/xml']
        else:
            # JSON as fallback
            payload = self.as_json(srv, request)
            format = media_types_rev['application/json']
        msg = aiocoap.Message(code=aiocoap.CONTENT, payload=payload)
        msg.opt.content_format = format
        return msg

class PublishResource(resource.Resource):
    @asyncio.coroutine
    def render_post(self, request):
        if request.opt.content_format == media_types_rev['application/json']:
            print('json: %s' % request.payload)
            s = service_parse_json(request.payload.decode('utf-8'))
            print(repr(s))
            _directory.publish(service=s)
            payload = 'POST OK'.encode('ascii')
            code = aiocoap.CONTENT
        else:
            code = aiocoap.UNSUPPORTED_MEDIA_TYPE
            payload = "Unknown Content-Format".encode('ascii')
        return aiocoap.Message(code=code, payload=payload)

class UnpublishResource(resource.Resource):
    @asyncio.coroutine
    def render_post(self, request):
        if request.opt.content_format == aiocoap.numbers.media_types_rev['application/json']:
            print('json: %s' % request.payload)
            d = json.loads(request.payload.decode('utf-8'))
            print(repr(d))
            _directory.unpublish(name=d['name'])
            payload = "POST OK".encode('ascii')
            code = aiocoap.CONTENT
        else:
            code = aiocoap.UNSUPPORTED_MEDIA_TYPE
            payload = "Unknown Content-Format".encode('ascii')
        return aiocoap.Message(code=code, payload=payload)

