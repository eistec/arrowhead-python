__all__ = ['Resource', 'ParentSite', 'ServiceResource', 'PublishResource', 'UnpublishResource']

import asyncio
import aiocoap.resource as resource
from aiocoap.numbers import media_types_rev
import aiocoap
from ..log import LogMixin

try:
    import json
except ImportError:
    import simplejson as json

from .. import services

uri_path_separator = '/'

class ObservableResource(LogMixin, resource.ObservableResource):
    pass

class Resource(LogMixin, resource.Resource):
    pass

class ParentSite(LogMixin, resource.Site):
    '''CoAP Site resource which sends the request to the closest parent if the
    exact resource specified in the URL was not found'''

    @asyncio.coroutine
    def render(self, request):
        path = tuple(request.opt.uri_path)
        for i in range(len(path), 0, -1):
            key = request.opt.uri_path[:i]
            try:
                child = self._resources[key]
            except KeyError:
                continue
            request.prepath = key
            request.postpath = request.opt.uri_path[i:]
            self.log.debug('prepath: %r postpath: %r' % (request.prepath, request.postpath))
            self.log.debug('Request: %r' % (request, ))
            self.log.debug('options: %r' % (request.opt, ))
            return child.render(request)
        raise aiocoap.error.NoResource()

class ServiceResource(ObservableResource):
    """/service resource"""
    service_url = '/service'
    def __init__(self, directory):
        super().__init__()
        self._directory = directory
        self._directory.add_notify_callback(self.notify)
        self.notify()

    def notify(self):
        self.log.debug('Notifying subscribers')
        self.updated_state()

    def _render_service(self, request, service):
        code = aiocoap.CONTENT
        if request.opt.accept is None or request.opt.accept == media_types_rev['application/json']:
            # JSON by default
            payload = services.service_to_json(service)
            format = media_types_rev['application/json']
        elif request.opt.accept == media_types_rev['application/link-format']:
            payload = services.service_to_corelf(service)
            format = media_types_rev['application/link-format']
        elif request.opt.accept == media_types_rev['application/xml']:
            payload = services.service_to_xml(service)
            format = media_types_rev['application/xml']
        else:
            # Unknown Accept format
            payload = ("Unknown accept option: %u" % (request.opt.accept, ))
            format = media_types_rev['text/plain']
            code = aiocoap.NOT_ACCEPTABLE
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = format
        return msg

    def _render_servicelist(self, request, slist):
        code = aiocoap.CONTENT
        if request.opt.accept is None or request.opt.accept == media_types_rev['application/json']:
            # JSON by default
            payload = services.servicelist_to_json(slist)
            format = media_types_rev['application/json']
        elif request.opt.accept == media_types_rev['application/link-format']:
            uri_base_str = '/' + '/'.join(request.prepath[:-1]) + self.service_url
            payload = services.servicelist_to_corelf(slist, uri_base_str)
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

    @asyncio.coroutine
    def render_get(self, request):
        name = '/'.join(request.postpath)
        self.log.debug('GET service %s' % (name, ))
        if name:
            service = self._directory.service(name=name)
            if service is None:
                # Could not find a service by that name, send response code
                return aiocoap.Message(code=aiocoap.NOT_FOUND, payload='')
            return self._render_service(request, service)
        else:
            slist = self._directory.service()
            return self._render_servicelist(request, slist)

class PublishResource(Resource):
    """/publish resource"""
    def __init__(self, directory):
        super().__init__()
        self._directory = directory

    @asyncio.coroutine
    def render_post(self, request):
        self.log.debug('POST %r' % (request.opt.uri_path, ))
        if request.opt.content_format == media_types_rev['application/json']:
            self.log.debug('POST JSON: %r' % request.payload)
            try:
                s = services.service_from_json(request.payload.decode('utf-8'))
            except:
                # bad input
                payload = 'Invalid data, expected JSON service'
                code = aiocoap.BAD_REQUEST
            else:
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

class UnpublishResource(Resource):
    """/unpublish resource"""
    def __init__(self, directory):
        super().__init__()
        self._directory = directory

    @asyncio.coroutine
    def render_post(self, request):
        if request.opt.content_format == aiocoap.numbers.media_types_rev['application/json']:
            self.log.debug('POST JSON: %r' % request.payload)
            try:
                d = json.loads(request.payload.decode('utf-8'))
            except:
                # bad input
                payload = 'Invalid data, expected JSON: {"name":"servicename"}'
                code = aiocoap.BAD_REQUEST
            else:
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

class TypeResource(ServiceResource):
    """/type resource"""
    type_url = '/type'
    def _render_typelist(self, request, tlist):
        code = aiocoap.CONTENT
        if request.opt.accept is None or request.opt.accept == media_types_rev['application/json']:
            # JSON by default
            payload = json.dumps({'serviceType': tlist})
            format = media_types_rev['application/json']
        elif request.opt.accept == media_types_rev['application/link-format']:
            uri_base_str = '/' + '/'.join(request.prepath[:-1]) + self.type_url
            payload = ','.join(['<%s/%s>' % (uri_base_str, t) for t in tlist])
            format = media_types_rev['application/link-format']
        else:
            # Unknown Accept format
            payload = ("Unknown accept option: %u" % (request.opt.accept, ))
            format = media_types_rev['text/plain']
            code = aiocoap.NOT_ACCEPTABLE
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = format
        return msg

    @asyncio.coroutine
    def render_get(self, request):
        name = '/'.join(request.postpath)
        if name:
            slist = self._directory.types(type=name)
            if not slist:
                # Could not find a service by that name, send response code
                return aiocoap.Message(code=aiocoap.NOT_FOUND, payload='')
            return self._render_servicelist(request, slist)
        else:
            tlist = self._directory.types()
            return self._render_typelist(request, tlist)
