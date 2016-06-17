"""CoAP implementation of the Arrowhead Service Directory based around aiocoap"""

import re
import asyncio

import aiocoap.resource as resource
from aiocoap.numbers import media_types_rev
from aiocoap.numbers.codes import Code
import aiocoap

from .. import LogMixin

from .. import services

__all__ = ['ServiceDirectoryCoAP']

URI_PATH_SEPARATOR = '/'

class RequestDispatcher(object):
    """Helper functions for dispatching requests based on their Accept or
    Content-format header options"""

    default_content_type = None

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

class PathRegex(str):
    """Regular expression match in resource path components"""

class Site(LogMixin, resource.Site):
    """CoAP Site resource with path regex matching"""

    @asyncio.coroutine
    def render(self, request):
        path = tuple(request.opt.uri_path)
        # Only compare against resources with the same number of path components
        matches = [(key, res) for key, res in self._resources.items() if len(key) == len(path)]
        # Filter routes matching the path, one level at a time
        for level in range(len(path)):
            # Try to find exact string matches
            string_matches = [
                (key, res) for key, res in matches \
                if not isinstance(key[level], PathRegex) and \
                key[level] == path[level]
                ]
            if string_matches:
                # string matches have a higher priority than regex matches
                matches = string_matches
                continue
            # Try to find any regex matches
            matches = [
                (key, res) for key, res in matches \
                if isinstance(key[level], PathRegex) and \
                re.fullmatch(key[level], path[level])
                ]
        if len(matches) == 0:
            raise aiocoap.error.NoResource()
        elif len(matches) > 1:
            raise aiocoap.error.RenderableError(
                "Ambiguous matches: {} = {}".format(repr(path), repr(matches)))
        child = matches[0][1]
        return child.render(request)

class ServiceDirectoryCoAP(RequestDispatcher, Site):
    """Service Directory resource handler class"""
    service_url = '/service'
    type_url = '/type'

    default_content_type = media_types_rev['application/json']

    service_output_handlers = {
        media_types_rev['application/json']: services.service_to_json,
        media_types_rev['application/link-format']: services.service_to_corelf,
        media_types_rev['application/xml']: services.service_to_xml,
    }

    service_input_handlers = {
        media_types_rev['application/json']: services.service_from_json,
        media_types_rev['application/xml']: services.service_from_xml,
    }

    class Resource(resource.Resource):
        """Generic resource class"""
        def __init__(self, *args, get=None, put=None, post=None, delete=None, **kwargs):
            """Constructor

            :param get: callback for GET requests
            :type get: asyncio.coroutine or None
            :param put: callback for PUT requests
            :type put: asyncio.coroutine or None
            :param post: callback for POST requests
            :type post: asyncio.coroutine or None
            :param delete: callback for DELETE requests
            :type delete: asyncio.coroutine or None
            """
            super().__init__(*args, **kwargs)
            if get is not None:
                self.render_get = get
            if put is not None:
                self.render_put = put
            if post is not None:
                self.render_post = post
            if delete is not None:
                self.render_delete = delete

    class ObservableResource(Resource, resource.ObservableResource):
        """Generic observable resource class"""

    def __init__(self, directory, uri_prefix, *args, **kwargs):
        """Constructor

        :param directory: Service directory backend
        :type directory: soa.directory.directory.ServiceDirectory
        :param uri_prefix: URI prefix for this site
        :type uri_prefix: tuple(strings...)
        """
        super().__init__(*args, **kwargs)
        self.uri_prefix = uri_prefix

        self.slist_handlers = {
            media_types_rev['application/json']: services.servicelist_to_json,
            media_types_rev['application/xml']: services.servicelist_to_xml,
            media_types_rev['application/link-format']: self._slist_to_corelf,
        }

        self.tlist_handlers = {
            media_types_rev['application/json']: services.typelist_to_json,
            #media_types_rev['application/xml']: services.typelist_to_xml,
            media_types_rev['application/link-format']: self._tlist_to_corelf,
        }
        self._create_resources()
        self.log.debug('Resources: %r', self._resources)
        self._directory = directory
        self._directory.add_notify_callback(self.notify)
        self.notify()

    def _create_resources(self):
        """Create all the resources of the service directory REST API"""
        self._servicelist_resource = self.ObservableResource(get=self._render_servicelist)
        self._service_resource = self.ObservableResource(get=self._render_service)
        self._typelist_resource = self.ObservableResource(get=self._render_typelist)
        self._type_resource = self.ObservableResource(get=self._render_type)
        self.add_resource(
            self.uri_prefix + ('service', ), self._servicelist_resource)
        self.add_resource(
            self.uri_prefix + ('service', PathRegex('.*')), self._service_resource)
        self.add_resource(
            self.uri_prefix + ('type', ), self._typelist_resource)
        self.add_resource(
            self.uri_prefix + ('type', PathRegex('.*')), self._type_resource)
        self.add_resource(
            self.uri_prefix + ('publish', ),
            self.Resource(post=self._render_publish))
        self.add_resource(
            self.uri_prefix + ('unpublish', ),
            self.Resource(post=self._render_unpublish))

    def notify(self):
        """Send notifications to all registered subscribers"""
        self.log.debug('Notifying subscribers')
        self._servicelist_resource.updated_state()
        self._service_resource.updated_state()
        self._typelist_resource.updated_state()
        self._type_resource.updated_state()

    def _slist_to_corelf(self, slist):
        """Convert a service list to CoRE Link-format links to other resources"""
        uri_base = '/' + '/'.join(self.uri_prefix) + self.service_url
        return services.servicelist_to_corelf(slist, uri_base)

    def _tlist_to_corelf(self, tlist):
        """Convert a type list to CoRE Link-format links to other resources"""
        uri_base = '/' + '/'.join(self.uri_prefix) + self.type_url
        return services.typelist_to_corelf(tlist, uri_base)

    @asyncio.coroutine
    def _render_service(self, request):
        """GET handler, respond with a single service

        :param request: The inbound CoAP request
        :type request: aiocoap.Message
        """
        name = request.opt.uri_path[-1]
        try:
            service = self._directory.service(name=name)
        except self._directory.DoesNotExist:
            # Could not find a service by that name, send response code
            raise NotFoundError()
        payload = self.dispatch_output(request, self.service_output_handlers, service)
        msg = aiocoap.Message(code=Code.CONTENT, payload=payload.encode('utf-8'))
        msg.opt.content_format = request.opt.accept
        if msg.opt.content_format is None:
            msg.opt.content_format = self.default_content_type
        return msg

    @asyncio.coroutine
    def _render_servicelist(self, request):
        """GET handler, respond with a list of registered services

        :param request: The inbound CoAP request
        :type request: aiocoap.Message
        """
        slist = self._directory.service_list()
        payload = self.dispatch_output(request, self.slist_handlers, slist)
        msg = aiocoap.Message(code=Code.CONTENT, payload=payload.encode('utf-8'))
        msg.opt.content_format = request.opt.accept
        if msg.opt.content_format is None:
            msg.opt.content_format = self.default_content_type
        return msg

    @asyncio.coroutine
    def _render_typelist(self, request):
        """GET handler, respond with a list of registered service types

        :param request: The inbound CoAP request
        :type request: aiocoap.Message
        """
        tlist = self._directory.types()
        payload = self.dispatch_output(request, self.tlist_handlers, tlist)
        msg = aiocoap.Message(code=Code.CONTENT, payload=payload.encode('utf-8'))
        msg.opt.content_format = request.opt.accept
        if msg.opt.content_format is None:
            msg.opt.content_format = media_types_rev['application/json']
        return msg

    @asyncio.coroutine
    def _render_type(self, request):
        """GET handler, respond with a list of registered services of the given type

        :param request: The inbound CoAP request
        :type request: aiocoap.Message
        """
        tname = request.opt.uri_path[-1]
        slist = self._directory.service_list(type=tname)
        payload = self.dispatch_output(request, self.slist_handlers, slist)
        msg = aiocoap.Message(code=Code.CONTENT, payload=payload.encode('utf-8'))
        msg.opt.content_format = request.opt.accept
        if msg.opt.content_format is None:
            msg.opt.content_format = self.default_content_type
        return msg

    @asyncio.coroutine
    def _render_publish(self, request):
        """POST handler

        This method parses the received payload data as a service and updates the
        directory with the new data.

        :param request: The inbound CoAP request
        :type request: aiocoap.Message
        :return: A CoAP response
        :rtype: aiocoap.Message
        """
        self.log.debug('POST %r' % (request.opt.uri_path, ))
        try:
            service = self.dispatch_input(
                request, self.service_input_handlers, request.payload.decode('utf-8'))
        except services.ServiceError:
            raise BadRequestError()
        if not service.name:
            # bad input
            raise BadRequestError()

        try:
            self._directory.service(name=service.name)
        except self._directory.DoesNotExist:
            code = Code.CREATED
        else:
            code = Code.CHANGED

        self._directory.publish(service=service)
        payload = 'POST OK'
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = media_types_rev['text/plain']
        return msg

    @asyncio.coroutine
    def _render_unpublish(self, request):
        """POST handler

        This method parses the received JSON data as a service and tells the
        directory to delete the given service.

        :param request: The inbound CoAP request
        :type request: aiocoap.Message
        :return: A CoAP response
        :rtype: aiocoap.Message
        """
        try:
            service = self.dispatch_input(request, self.service_input_handlers, request.payload)
        except services.ServiceError:
            raise BadRequestError()
        if not service.name:
            # bad input
            raise BadRequestError()
        self._directory.unpublish(name=service.name)
        payload = 'POST OK'
        code = Code.DELETED
        msg = aiocoap.Message(code=code, payload=payload.encode('utf-8'))
        msg.opt.content_format = media_types_rev['text/plain']
        return msg

class Server(object):
    """CoAP server implementation"""

    def __init__(self, *, directory, **kwargs):
        """Constructor

        :param directory: Service directory to use as backend
        :type directory: soa.directory.ServiceDirectory
        """
        super().__init__()
        self._directory = directory
        self.site = ServiceDirectoryCoAP(directory=directory, uri_prefix=('servicediscovery', ))
        self.context = aiocoap.Context.create_server_context(self.site, **kwargs)

        self.site.add_resource(
            ('.well-known', 'core'),
            resource.WKCResource(self.site.get_resources_as_linkheader))
