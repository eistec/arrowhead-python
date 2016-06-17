"""HTTP REST implementation of Arrowhead service registry based around aiohttp"""
import fnmatch
import asyncio
from aiohttp import web

from .. import LogMixin

from .. import services


class Server(LogMixin, web.Application):
    """HTTP server implementation"""

    def __init__(self, *args, directory, **kwargs):
        """Constructor

        :param directory: Service directory to use as backend
        :type directory: soa.directory.ServiceDirectory
        """
        super().__init__(*args, **kwargs)
        self._directory = directory

        self._service_list_res = self.router.add_resource('/servicediscovery/service')
        self._service_list_res.add_route('GET', self.service_list_get)
        self._service_res = self.router.add_resource('/servicediscovery/service/{name}')
        self._service_res.add_route('GET', self.service_get)
        self._type_list_res = self.router.add_resource('/servicediscovery/type')
        self._type_list_res.add_route('GET', self.type_list_get)
        self._type_res = self.router.add_resource('/servicediscovery/type/{name}')
        self._type_res.add_route('GET', self.type_get)
        self._publish_res = self.router.add_resource('/servicediscovery/publish')
        self._publish_res.add_route('POST', self.publish_post)
        self._unpublish_res = self.router.add_resource('/servicediscovery/unpublish')
        self._unpublish_res.add_route('POST', self.unpublish_post)
        self.log.debug('HTTP directory starting')

    def parse_accept(self, request, content_types):
        """Parse the incoming Accept: headers for content types matching the
        available handlers

        Currently this method does not care about the quality Accept parameter
        (e.g. 'text/plain;q=0.5')

        :param request: the incoming HTTP request
        :type request: aiohttp.Request
        :param content_types: list of content types that can be produced
        :type content_types: list(string)
        :returns: The first matching item, or None if the incoming request has
            no Accept headers.
        :rtype: string
        :raises aiohttp.web.HTTPNotAcceptable: if incoming Accept headers can
            not be matched against any of the available produced types.
        """

        client_acceptables = [
            accept.split(';')[0] for accept in
            ','.join(request.headers.getall('ACCEPT', [])).split(',')]

        self.log.info('acceptables: %r', client_acceptables)
        if len(client_acceptables) == 0 or (
                len(client_acceptables) == 1 and len(client_acceptables[0]) == 0):
            return None
        for accept in client_acceptables:
            for content_type in content_types:
                if fnmatch.fnmatch(content_type, accept):
                    return content_type
        raise web.HTTPNotAcceptable()

    def dispatch_request(self, request, content_handlers, *args, **kwargs):
        """Handle request by dispatching to a suitable handler based on client
        provided Accept: headers

        The content_handlers parameter is a dictionary with content-type as keys
        and callables as values. Any extra arguments will be passed on to the
        chosen callable.

        :param request: the request to handle
        :type request: aiohttp.Request
        :param content_handlers: Content-type => handler mappings
        :type content_handlers: dict('content_type': callable)
        :param args: Extra positional arguments to pass on to content handler
        :param kwargs: Extra keyword arguments to pass on to content handler
        :returns: A HTTP response
        :rtype: aiohttp.web.Response
        """
        content_type = self.parse_accept(request, content_handlers.keys())
        if content_type is None:
            # Missing Accept: header, pick arbitrary handler
            self.log.info('Request is missing Accept headers')
            content_type = list(content_handlers.keys())[0]
        self.log.debug('Content-type: %s', content_type)
        handler = content_handlers[content_type]
        payload = handler(*args, **kwargs)
        charset = 'utf-8'
        return web.Response(
            body=payload.encode(charset), content_type=content_type,
            charset=charset)

    @asyncio.coroutine
    def service_list_get(self, request):
        """Generate a service list response

        :param request: incoming HTTP request
        :type request: aiohttp.Request
        :returns: A HTTP response
        :rtype: aiohttp.web.Response
        """
        content_handlers = {
            'application/json': services.servicelist_to_json,
            'application/xml': services.servicelist_to_xml,
        }
        slist = self._directory.service_list()
        return self.dispatch_request(request, content_handlers, slist)

    @asyncio.coroutine
    def service_get(self, request):
        """Generate a service response

        :param request: incoming HTTP request
        :type request: aiohttp.Request
        :returns: A HTTP response
        :rtype: aiohttp.web.Response
        """
        content_handlers = {
            'application/json': services.service_to_json,
            'application/xml': services.service_to_xml,
        }
        name = request.match_info.get('name', '(null)')
        service = self._directory.service(name=name)
        return self.dispatch_request(request, content_handlers, service)

    @asyncio.coroutine
    def type_list_get(self, request):
        """Generate a service type list response

        :param request: incoming HTTP request
        :type request: aiohttp.Request
        :returns: A HTTP response
        :rtype: aiohttp.web.Response
        """
        content_handlers = {
            'application/json': services.typelist_to_json,
            #'application/xml': services.service_to_xml,
        }
        tlist = self._directory.types()
        return self.dispatch_request(request, content_handlers, tlist)

    @asyncio.coroutine
    def type_get(self, request):
        """Generate a service list response for the given service type

        :param request: incoming HTTP request
        :type request: aiohttp.Request
        :returns: A HTTP response
        :rtype: aiohttp.web.Response
        """
        content_handlers = {
            'application/json': services.servicelist_to_json,
            'application/xml': services.servicelist_to_xml,
        }
        name = request.match_info.get('name', '(null)')
        slist = self._directory.service_list(type=name)
        if not slist:
            raise web.HTTPNotFound()
        return self.dispatch_request(request, content_handlers, slist)

    @asyncio.coroutine
    def publish_post(self, request):
        """Register a service in the service directory

        :param request: incoming HTTP request
        :type request: aiohttp.Request
        :returns: A HTTP response
        :rtype: aiohttp.web.Response
        """
        content_handlers = {
            'application/json': services.service_from_json,
            'application/xml': services.service_from_xml,
        }
        try:
            handler = content_handlers[request.content_type]
        except KeyError:
            self.log.info('Unhandled Content-Type: %s', request.content_type)
            raise web.HTTPUnsupportedMediaType(
                reason='Unhandled Content-Type: %s' % request.content_type)

        try:
            text = yield from request.text()
            self.log.debug('Service text: %s', text)
            service = handler(text)
        except ValueError:
            # bad input
            raise web.HTTPBadRequest(reason='Invalid data, expected service')

        if not service['name']:
            # bad input
            raise web.HTTPBadRequest(reason='Missing service name')
        else:
            try:
                self._directory.service(name=service['name'])
            except self._directory.DoesNotExist:
                code = web.HTTPCreated.status_code
            else:
                code = web.HTTPOk.status_code

            self._directory.publish(service=service)
            payload = 'Publish OK'
            return web.Response(
                body=payload.encode('utf-8'), status=code,
                content_type='text/plain', charset='utf-8')

    @asyncio.coroutine
    def unpublish_post(self, request):
        """De-register a service in the service directory

        :param request: incoming HTTP request
        :type request: aiohttp.Request
        :returns: A HTTP response
        :rtype: aiohttp.web.Response
        """
        content_handlers = {
            'application/json': services.service_from_json,
            'application/xml': services.service_from_xml,
        }
        try:
            handler = content_handlers[request.content_type]
        except KeyError:
            self.log.info('Unhandled Content-Type: %s', request.content_type)
            raise web.HTTPUnsupportedMediaType(
                reason='Unhandled Content-Type: %s' % request.content_type)

        try:
            text = yield from request.text()
            self.log.debug('Service text: %s', text)
            service = handler(text)
        except ValueError:
            # bad input
            raise web.HTTPBadRequest(reason='Invalid data, expected service')

        name = service['name']
        if not name:
            # bad input
            raise web.HTTPBadRequest(reason='Missing service name')

        try:
            self._directory.unpublish(name=name)
        except self._directory.DoesNotExist:
            self.log.info('Service %s is not published', name)
            raise web.HTTPBadRequest(reason='Service %s is not published' % (name, ))
        self.log.info('Unpublish %s OK', name)
        payload = 'Unpublish OK'
        code = web.HTTPOk.status_code
        return web.Response(
            body=payload.encode('utf-8'), status=code,
            content_type='text/plain', charset='utf-8')

    def copy(self):
        """Disable copying"""
        raise NotImplementedError
