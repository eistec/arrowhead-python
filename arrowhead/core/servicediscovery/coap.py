import asyncio
import aiocoap.resource as resource
from aiocoap.numbers import media_types_rev
import aiocoap

try:
    import json
except ImportError:
    import simplejson as json

from .. import services

class ServiceResource(resource.ObservableResource):
    """/service resource"""
    def __init__(self, directory):
        super().__init__()
        self._directory = directory
        self._directory.add_notify_callback(self.notify)
        self.notify()

    def notify(self):
        self.updated_state()

    @asyncio.coroutine
    def render_get(self, request):
        slist = self._directory.service()
        format = media_types_rev['text/plain']
        code = aiocoap.CONTENT
        if request.opt.accept is None or request.opt.accept == media_types_rev['application/json']:
            # JSON by default
            payload = services.servicelist_to_json(slist)
            format = media_types_rev['application/json']
        elif request.opt.accept == media_types_rev['application/link-format']:
            payload = services.servicelist_to_corelf(slist)
            format = media_types_rev['application/link-format']
        elif request.opt.accept == media_types_rev['application/xml']:
            payload = services.servicelist_to_xml(slist)
            format = media_types_rev['application/xml']
        else:
            # Unknown Accept format
            payload = ("Unknown accept option: %u" % (request.opt.accept, ))
            format = media_types_rev['text/plain']
            code = aiocoap.NOT_ACCEPTABLE
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = format
        return msg

class PublishResource(resource.Resource):
    """/publish resource"""
    def __init__(self, directory):
        super().__init__()
        self._directory = directory

    @asyncio.coroutine
    def render_post(self, request):
        if request.opt.content_format == media_types_rev['application/json']:
            print('json: %s' % request.payload)
            try:
                s = services.service_from_json(request.payload.decode('utf-8'))
            except:
                # bad input
                payload = 'Invalid data, expected JSON service'
                code = aiocoap.BAD_REQUEST
            else:
                print(repr(s))
                if not s['name']:
                    # bad input
                    payload = 'Missing service name'
                    code = aiocoap.BAD_REQUEST
                else:
                    if self._directory.service(name=s['name']):
                        code = aiocoap.CHANGED
                    else:
                        code = aiocoap.CREATED
                    self._directory.publish(service=s)
                    payload = 'POST OK'
        else:
            code = aiocoap.UNSUPPORTED_MEDIA_TYPE
            payload = ('Unknown Content-Format option: %u' % (request.opt.content_format, ))
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = media_types_rev['text/plain']
        return msg

class UnpublishResource(resource.Resource):
    """/unpublish resource"""
    def __init__(self, directory):
        super().__init__()
        self._directory = directory

    @asyncio.coroutine
    def render_post(self, request):
        if request.opt.content_format == aiocoap.numbers.media_types_rev['application/json']:
            print('json: %s' % request.payload)
            try:
                d = json.loads(request.payload.decode('utf-8'))
            except:
                # bad input
                payload = 'Invalid data, expected JSON: {"name":"servicename"}'
                code = aiocoap.BAD_REQUEST
            else:
                print(repr(d))
                self._directory.unpublish(name=d['name'])
                payload = 'POST OK'
                code = aiocoap.DELETED
        else:
            code = aiocoap.UNSUPPORTED_MEDIA_TYPE
            payload = 'Unknown Content-Format'
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = media_types_rev['text/plain']
        return msg

    @asyncio.coroutine
    def render_get(self, request):
        payload = 'Unpublish a service, input payload JSON: {"name":"servicename123"}'
        code = aiocoap.METHOD_NOT_ALLOWED
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = media_types_rev['text/plain']
        return msg

class TypeResource(resource.ObservableResource):
    """/service resource"""
    def __init__(self, directory):
        super().__init__()
        self._directory = directory
        self.notify()

    def notify(self):
        self.updated_state()

    @asyncio.coroutine
    def render_get(self, request):
        slist = self._directory.service()
        format = media_types_rev['text/plain']
        code = aiocoap.CONTENT
        if request.opt.accept is None or request.opt.accept == media_types_rev['application/json']:
            # JSON by default
            payload = services.servicelist_to_json(slist)
            format = media_types_rev['application/json']
        elif request.opt.accept == media_types_rev['application/link-format']:
            payload = services.servicelist_to_corelf(slist)
            format = media_types_rev['application/link-format']
        elif request.opt.accept == media_types_rev['application/xml']:
            payload = services.servicelist_to_xml(slist)
            format = media_types_rev['application/xml']
        else:
            # Unknown Accept format
            payload = ("Unknown accept option: %u" % (request.opt.accept, ))
            format = media_types_rev['text/plain']
            code = aiocoap.NOT_ACCEPTABLE
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = format
        return msg
