"""CoAP implementation of the Arrowhead Service Directory based around aiocoap"""

import asyncio
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        HAVE_JSON = False
else:
    HAVE_JSON = True

import aiocoap.resource as resource
from aiocoap.numbers import media_types_rev
from aiocoap.numbers.codes import Code
import aiocoap

from .. import LogMixin

from .. import services

__all__ = [
    'ParentSite',
    'ServiceResource',
    'TypeResource',
    'PublishResource',
    'UnpublishResource']

URI_PATH_SEPARATOR = '/'


class ParentSite(LogMixin, resource.Site):
    """CoAP Site resource which sends the request to the closest parent if the
    exact resource specified in the URL was not found"""

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
            self.log.debug(
                'prepath: %r postpath: %r' %
                (request.prepath, request.postpath))
            self.log.debug('Request: %r' % (request, ))
            self.log.debug('options: %r' % (request.opt, ))
            return child.render(request)
        raise aiocoap.error.NoResource()


class ServiceResource(LogMixin, resource.ObservableResource):
    """/service resource"""
    service_url = '/service'

    def __init__(self, directory):
        super().__init__()
        self._directory = directory
        self._directory.add_notify_callback(self.notify)
        self.notify()

    def notify(self):
        """Send notifications to all registered subscribers"""
        self.log.debug('Notifying subscribers')
        self.updated_state()

    @staticmethod
    def _render_service(request, service):
        code = Code.CONTENT
        if request.opt.accept is None or request.opt.accept == media_types_rev[
                'application/json']:
            # JSON by default
            payload = services.service_to_json(service)
            content_format = media_types_rev['application/json']
        elif request.opt.accept == media_types_rev['application/link-format']:
            payload = services.service_to_corelf(service)
            content_format = media_types_rev['application/link-format']
        elif request.opt.accept == media_types_rev['application/xml']:
            payload = services.service_to_xml(service)
            content_format = media_types_rev['application/xml']
        else:
            # Unknown Accept format
            payload = ("Unknown accept option: %u" % (request.opt.accept, ))
            content_format = media_types_rev['text/plain']
            code = Code.NOT_ACCEPTABLE
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = content_format
        return msg

    def _render_servicelist(self, request, slist):
        code = Code.CONTENT
        if request.opt.accept is None or request.opt.accept == media_types_rev[
                'application/json']:
            # JSON by default
            payload = services.servicelist_to_json(slist)
            content_format = media_types_rev['application/json']
        elif request.opt.accept == media_types_rev['application/link-format']:
            uri_base_str = '/' + \
                '/'.join(request.prepath[:-1]) + self.service_url
            payload = services.servicelist_to_corelf(slist, uri_base_str)
            content_format = media_types_rev['application/link-format']
        elif request.opt.accept == media_types_rev['application/xml']:
            payload = services.servicelist_to_xml(slist)
            content_format = media_types_rev['application/xml']
        else:
            # Unknown Accept format
            payload = ("Unknown accept option: %u" % (request.opt.accept, ))
            content_format = media_types_rev['text/plain']
            code = Code.NOT_ACCEPTABLE
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = content_format
        return msg

    @asyncio.coroutine
    def render_get(self, request):
        """GET handler, respond with either a service list or a single service

        :param request: The inbound CoAP request
        :type request: aiocoap.Message
        """
        name = '/'.join(request.postpath)
        self.log.debug('GET service %s' % (name, ))
        if name:
            service = self._directory.service(name=name)
            if service is None:
                # Could not find a service by that name, send response code
                return aiocoap.Message(code=Code.NOT_FOUND, payload='')
            return self._render_service(request, service)
        else:
            slist = self._directory.service_list()
            return self._render_servicelist(request, slist)


class PublishResource(LogMixin, resource.Resource):
    """/publish resource"""

    def __init__(self, directory):
        super().__init__()
        self._directory = directory

    @asyncio.coroutine
    def render_post(self, request):
        """POST handler

        This method parses the received JSON data as a service and updates the
        directory with the new data.

        :param request: The inbound CoAP request
        :type request: aiocoap.Message
        :return: A CoAP response
        :rtype: aiocoap.Message
        """
        self.log.debug('POST %r' % (request.opt.uri_path, ))
        if request.opt.content_format == media_types_rev['application/json']:
            self.log.debug('POST JSON: %r' % request.payload)
            try:
                service = services.service_from_json(request.payload.decode('utf-8'))
            except ValueError:
                # bad input
                payload = 'Invalid data, expected JSON service'
                code = Code.BAD_REQUEST
            else:
                if not service['name']:
                    # bad input
                    payload = 'Missing service name'
                    code = Code.BAD_REQUEST
                else:
                    try:
                        self._directory.service(name=service['name'])
                    except self._directory.DoesNotExist:
                        code = Code.CREATED
                    else:
                        code = Code.CHANGED

                    self._directory.publish(service=service)
                    payload = 'POST OK'
        else:
            code = Code.UNSUPPORTED_MEDIA_TYPE
            payload = (
                'Unknown Content-Format option: %s' %
                (request.opt.content_format, ))
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = media_types_rev['text/plain']
        return msg


class UnpublishResource(LogMixin, resource.Resource):
    """/unpublish resource"""

    def __init__(self, directory):
        super().__init__()
        self._directory = directory

    def _unpublish_json(self, request):
        self.log.debug('POST JSON: %r' % request.payload)
        try:
            data = json.loads(request.payload.decode('utf-8'))
        except ValueError:
            # bad input
            payload = 'Invalid data, expected JSON: {"name":"servicename"}'
            code = Code.BAD_REQUEST
        else:
            self._directory.unpublish(name=data['name'])
            payload = 'POST OK'
            code = Code.DELETED
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = media_types_rev['text/plain']
        return msg

    @asyncio.coroutine
    def render_post(self, request):
        """POST handler

        This method parses the received JSON data as a service and tells the
        directory to delete the given service.

        :param request: The inbound CoAP request
        :type request: aiocoap.Message
        :return: A CoAP response
        :rtype: aiocoap.Message
        """
        content_handlers = {
            media_types_rev['application/json']: self._unpublish_json
            }

        try:
            handler = content_handlers[request.opt.content_format]
        except KeyError:
            code = Code.UNSUPPORTED_MEDIA_TYPE
            payload = (
                'Unknown Content-Format option: %s' %
                (request.opt.content_format, ))
            msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
            msg.opt.content_format = media_types_rev['text/plain']
            return msg
        else:
            return handler(request)

    @asyncio.coroutine
    @staticmethod
    def render_get(request): # pylint: disable=unused-argument
        """GET handler, show usage help

        :param request: The inbound CoAP request
        :type request: aiocoap.Message
        :return: A CoAP response
        :rtype: aiocoap.Message
        """
        payload = 'Unpublish a service, input payload JSON: {"name":"servicename123"}'
        code = Code.METHOD_NOT_ALLOWED
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = media_types_rev['text/plain']
        return msg


class TypeResource(ServiceResource):
    """/type resource"""
    type_url = '/type'

    def _render_typelist(self, request, tlist):
        code = Code.CONTENT
        if request.opt.accept is None or request.opt.accept == media_types_rev[
                'application/json']:
            # JSON by default
            payload = services.typelist_to_json(tlist)
            content_format = media_types_rev['application/json']
        elif request.opt.accept == media_types_rev['application/link-format']:
            uri_base_str = '/' + '/'.join(request.prepath[:-1]) + self.type_url
            payload = services.typelist_to_corelf(tlist, uri_base_str)
            content_format = media_types_rev['application/link-format']
        else:
            # Unknown Accept format
            payload = ("Unknown accept option: %u" % (request.opt.accept, ))
            content_format = media_types_rev['text/plain']
            code = Code.NOT_ACCEPTABLE
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = content_format
        return msg

    @asyncio.coroutine
    def render_get(self, request):
        """GET handler, return a list of types

        :param request: The inbound CoAP request
        :type request: aiocoap.Message
        :return: A CoAP response
        :rtype: aiocoap.Message
        """
        name = '/'.join(request.postpath)
        if name:
            slist = self._directory.service_list(type=name)
            if not slist:
                # Could not find a service by that name, send response code
                return aiocoap.Message(code=Code.NOT_FOUND, payload='')
            return self._render_servicelist(request, slist)
        else:
            tlist = self._directory.types()
            return self._render_typelist(request, tlist)


class Server(ParentSite):
    """CoAP server implementation"""

    def __init__(self, *, directory, **kwargs):
        """Constructor

        :param directory: Service directory to use as backend
        :type directory: arrowhead.servicedirectory.ServiceDirectory
        """
        super().__init__()
        self._directory = directory
        self.site = ParentSite()
        self.context = aiocoap.Context.create_server_context(self.site, **kwargs)

        self.site.add_resource(
            ('.well-known', 'core'),
            resource.WKCResource(self.site.get_resources_as_linkheader))

        self.site.add_resource(
            ('servicediscovery', 'service'),
            ServiceResource(directory=directory))
        self.site.add_resource(
            ('servicediscovery', 'publish'),
            PublishResource(directory=directory))
        self.site.add_resource(
            ('servicediscovery', 'unpublish'),
            UnpublishResource(directory=directory))
        self.site.add_resource(
            ('servicediscovery', 'type'),
            TypeResource(directory=directory))
