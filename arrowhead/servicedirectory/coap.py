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

class RequestDispatcher(object):
    """Helper functions for dispatching requests based on their Accept or
    Content-format header options"""

    @staticmethod
    def dispatch_input(request, handlers, *args, **kwargs):
        """Dispatch handling of the request payload to a handler based on the
        given Content-format option"""
        try:
            input_handler = handlers[request.opt.content_format]
        except KeyError:
            raise UnsupportedMediaTypeError()
        else:
            return input_handler(*args, **kwargs)

    def dispatch_output(self, request, handlers, *args, **kwargs):
        """Dispatch handling of the request payload to a handler based on the
        given Accept option"""
        accept = request.opt.accept
        if accept is None:
            accept = self.default_content_type
        try:
            output_handler = handlers[accept]
        except KeyError:
            raise NotAcceptableError()
        else:
            return output_handler(*args, **kwargs)

class NotAcceptableError(aiocoap.error.RenderableError):
    """Not acceptable, there is no handler registered for the given Accept type"""
    code = Code.NOT_ACCEPTABLE
    message = "NotAcceptable"

class UnsupportedMediaTypeError(aiocoap.error.RenderableError):
    """Unsupported media type, there is no handler registered for the given Content-format"""
    code = Code.UNSUPPORTED_MEDIA_TYPE
    message = "UnsupportedMediaType"

class NotFoundError(aiocoap.error.RenderableError):
    """Not found"""
    code = Code.NOT_FOUND
    message = "NotFound"

class BadRequestError(aiocoap.error.RenderableError):
    """Generic bad request message"""
    code = Code.BAD_REQUEST
    message = "BadRequest"

class ParentSite(LogMixin, resource.Site):
    """CoAP Site resource which sends the request to the closest parent if the
    exact resource specified in the URL was not found"""

    @asyncio.coroutine
    def render(self, request):
        """Dispatch rendering to the best matching resource"""
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


class ServiceResource(RequestDispatcher, LogMixin, resource.ObservableResource):
    """/service resource"""
    service_url = '/service'
    default_content_type = media_types_rev['application/json']
    service_handlers = {
        media_types_rev['application/json']: services.service_to_json,
        media_types_rev['application/link-format']: services.service_to_corelf,
        media_types_rev['application/xml']: services.service_to_xml,
    }
    slist_handlers = {
        media_types_rev['application/json']: services.servicelist_to_json,
        media_types_rev['application/link-format']: services.servicelist_to_corelf,
        media_types_rev['application/xml']: services.servicelist_to_xml,
    }

    def __init__(self, directory, *args, **kwargs):
        """Constructor

        :param directory: Service directory backend
        :type directory: arrowhead.servicedirectory.directory.ServiceDirectory
        """
        super().__init__(*args, **kwargs)
        self._directory = directory
        self._directory.add_notify_callback(self.notify)
        self.notify()

    def notify(self):
        """Send notifications to all registered subscribers"""
        self.log.debug('Notifying subscribers')
        self.updated_state()

    def _render_service(self, request, service):
        payload = self.dispatch_output(request, self.service_handlers, service)
        msg = aiocoap.Message(code=Code.CONTENT, payload=payload.encode('utf-8'))
        msg.opt.content_format = request.opt.accept
        return msg

    def _render_servicelist(self, request, slist):
        payload = self.dispatch_output(request, self.slist_handlers, slist)
        msg = aiocoap.Message(code=Code.CONTENT, payload=payload.encode('utf-8'))
        msg.opt.content_format = request.opt.accept
        if msg.opt.content_format is None:
            msg.opt.content_format = media_types_rev['application/json']
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
            try:
                service = self._directory.service(name=name)
            except self._directory.DoesNotExist:
                # Could not find a service by that name, send response code
                raise NotFoundError()
            return self._render_service(request, service)
        else:
            slist = self._directory.service_list()
            return self._render_servicelist(request, slist)


class PublishResource(RequestDispatcher, LogMixin, resource.Resource):
    """/publish resource"""
    service_input_handlers = {
        media_types_rev['application/json']: services.service_from_json,
        media_types_rev['application/xml']: services.service_from_xml,
    }

    def __init__(self, directory, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        try:
            service = self.dispatch_input(request, self.service_input_handlers, request.payload.decode('utf-8'))
        except services.ServiceError:
            raise BadRequestError()
        if not service['name']:
            # bad input
            raise BadRequestError()

        try:
            self._directory.service(name=service['name'])
        except self._directory.DoesNotExist:
            code = Code.CREATED
        else:
            code = Code.CHANGED

        self._directory.publish(service=service)
        payload = 'POST OK'
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = media_types_rev['text/plain']
        return msg

class UnpublishResource(RequestDispatcher, LogMixin, resource.Resource):
    """/unpublish resource"""

    def __init__(self, directory, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name_input_handlers = {
            media_types_rev['application/json']: self._name_json,
            #media_types_rev['application/xml']: self._name_xml,
        }
        self._directory = directory

    def _name_json(self, payload):
        try:
            data = json.loads(payload.decode('utf-8'))
        except ValueError:
            # bad input
            raise BadRequestError()
        try:
            return data['name']
        except KeyError:
            raise BadRequestError()

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
        name = self.dispatch_input(request, self.name_input_handlers, request.payload)
        self._directory.unpublish(name=name)
        payload = 'POST OK'
        code = Code.DELETED
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = media_types_rev['text/plain']
        return msg

class TypeResource(ServiceResource):
    """/type resource"""
    type_url = '/type'
    tlist_handlers = {
        None: services.typelist_to_json,
        media_types_rev['application/json']: services.typelist_to_json,
        media_types_rev['application/link-format']: services.typelist_to_corelf,
        #media_types_rev['application/xml']: services.typelist_to_xml,
    }

    def _render_typelist(self, request, tlist):
        payload = self.dispatch_output(request, self.tlist_handlers, tlist)
        msg = aiocoap.Message(code=Code.CONTENT, payload=payload.encode('utf-8'))
        msg.opt.content_format = request.opt.accept
        if msg.opt.content_format is None:
            msg.opt.content_format = media_types_rev['application/json']
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
                raise NotFoundError()
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
