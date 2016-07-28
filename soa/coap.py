"""SOA CoAP client functions"""

import asyncio
import json

import aiocoap

from . import services

from . import LogMixin

class CoAPObserver(LogMixin, object):
    """CoAP resource observer"""

    def __init__(self, *args, uri, observation_handler,
                 accept=aiocoap.numbers.media_types_rev['application/json'], **kwargs):
        """Constructor"""
        super().__init__(*args, **kwargs)
        self.uri = uri
        self.requester = None
        self.context = None
        self.accept = accept
        self.observation_handler = observation_handler

    @asyncio.coroutine
    def start_observe(self):
        """Begin observing the resource given in self.uri"""
        self.context = yield from aiocoap.Context.create_client_context()
        request = aiocoap.Message(code=aiocoap.numbers.codes.Code.GET)
        request.set_request_uri(self.uri)
        request.opt.accept = aiocoap.numbers.media_types_rev['application/json']
        # Tell the server we want to observe the resource
        request.opt.observe = 0
        observation_is_over = asyncio.Future()
        self.requester = self.context.request(request)
        self.requester.observation.register_errback(observation_is_over.set_result)
        self.requester.observation.register_callback(self.observation_handler)
        self.log.info("Begin observation on '{}'".format(self.uri))
        self.log.debug("options: {}".format(repr(request.opt)))
        try:
            response = yield from self.requester.response
        except aiocoap.error.Error as exc:
            self.log.warning('CoAP exception: %r', exc)
            if not self.requester.observation.cancelled:
                self.log.warning('Cancelling observation %r', self.requester.observation)
                self.requester.observation.cancel()
        # Pass the initial GET response to the observation handler as well
        yield from self.observation_handler(response)
        # The observation_is_over Future is only completed if the observation
        # stops for whatever reason
        exit_reason = yield from observation_is_over
        # The below two lines are probably not necessary
        if not self.requester.observation.cancelled:
            self.requester.observation.cancel()
        self.log.info("Observation is over ({}): {!r}, {!r}".format(
            self.uri, exit_reason, self.requester.observation))

class ServiceDirectoryBrowser(LogMixin, object):
    """Client for the Arrowhead service directory"""

    def __init__(self, *args, uri, notify=None, **kwargs):
        """Constructor"""
        super().__init__(*args, **kwargs)
        self.services = {}
        self.notify = notify
        self.uri = uri
        self.observer = None

    @asyncio.coroutine
    def browse_handler(self, response):
        """Handler for incoming responses to an active directory observation"""
        if not response.code.is_successful():
            self.log.info('Error in observe response: %s: (%s)', self.uri, response.code)
            raise RuntimeError('Error in observe response: {}: ({})'.format(
                self.uri, response.code))
        if response.opt.content_format != aiocoap.numbers.media_types_rev['application/json']:
            raise RuntimeError('Unknown content format: {}'.format(response.opt.content_format))
        try:
            slist = json.loads(response.payload.decode('utf-8'))
        except ValueError as exc:
            raise RuntimeError('ValueError while parsing JSON service list: {}'.format(str(exc)))
        self.log.debug('slist: %r', slist)
        for json_dict in slist['service']:
            srv = services.Service.from_json_dict(json_dict)
            name = srv.name
            self.services[name] = srv
        if self.notify is not None:
            self.notify(self)

    @asyncio.coroutine
    def start_observe(self):
        """Timed polling"""
        if False:
            # This would be correct if Block2 was working properly for observe in aiocoap
            if self.observer is None:
                self.observer = CoAPObserver(
                    uri=self.uri, observation_handler=self.browse_handler,
                    accept=aiocoap.numbers.media_types_rev['application/json'])
            yield from self.observer.start_observe()
        self.log.warning('Using polling because of missing Block2 Observation handler')
        self.context = yield from aiocoap.Context.create_client_context()
        self.log.info("Begin poll on '%s'", self.uri)
        while True:
            request = aiocoap.Message(code=aiocoap.numbers.codes.Code.GET)
            request.set_request_uri(self.uri)
            request.opt.accept = aiocoap.numbers.media_types_rev['application/json']
            requester = self.context.request(request)
            self.log.debug("poll: %r, options: %r", request, request.opt)
            try:
                response = yield from asyncio.wait_for(requester.response, timeout=60.0)
            except asyncio.TimeoutError:
                # timed out waiting for server to respond
                self.log.warning('Request timed out (60 s), retrying...')
                continue
            except ConnectionError as exc:
                # connection refused etc.
                self.log.warning('Connection error: %r, retrying in 15 s...', exc)
                self.log.debug('Context: %r', self.context)
                self.log.debug('Requester: %r', requester)
                del self.context
                self.context = yield from aiocoap.Context.create_client_context()
                yield from asyncio.sleep(15.0)
                continue
            # Pass the poll response to the observation handler
            yield from self.browse_handler(response)
            self.log.debug('ServiceRegistry: Sleeping')
            yield from asyncio.sleep(30.0) # magic number, wait 30 seconds before polling again
            self.log.debug('ServiceRegistry: Awake')
