import asyncio
import aiocoap.resource as resource
import aiocoap

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

    @asyncio.coroutine
    def render_get(self, request):
        payload = repr(_directory.services()).encode('ascii')
        return aiocoap.Message(code=aiocoap.CONTENT, payload=payload)

class RegisterResource(resource.Resource):
    @asyncio.coroutine
    def render_post(self, request):
        if request.opt.content_format == aiocoap.numbers.media_types_rev['application/json']:
            print('json: %s' % request.payload)
            s = service_parse_json(request.payload.decode("utf-8"))
            print(repr(s))
            _directory.register(service=s)
            payload = "POST OK".encode('ascii')
            code = aiocoap.CONTENT
        else:
            code = aiocoap.UNSUPPORTED_MEDIA_TYPE
            payload = "Unknown Content-Format".encode('ascii')
        return aiocoap.Message(code=code, payload=payload)

    @asyncio.coroutine
    def render_delete(self, request):
        
