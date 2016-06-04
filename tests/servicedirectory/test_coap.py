"""Test arrowhead.servicedirectory.coap"""
#pylint: disable=no-member
# pylint doesn't understand mock objects

import random
from unittest import mock
import tempfile
import json
from collections import namedtuple
import xml.etree.ElementTree as ET

import pytest

import link_header
from aiocoap.numbers.codes import Code
import aiocoap

from arrowhead.servicedirectory import directory
from arrowhead.servicedirectory import coap
from arrowhead import services
import arrowhead

from ..test_data import EXAMPLE_SERVICES, BROKEN_SERVICES

URI_PATH_WKC = ('.well-known', 'core')
URI_PATH_PUBLISH = ('servicediscovery', 'publish')
URI_PATH_UNPUBLISH = ('servicediscovery', 'unpublish')
URI_PATH_SERVICE = ('servicediscovery', 'service')
URI_PATH_TYPE = ('servicediscovery', 'type')

EXPECTED_ROOT_RESOURCES = (
    URI_PATH_WKC,
    URI_PATH_SERVICE,
    URI_PATH_TYPE,
    URI_PATH_PUBLISH,
    URI_PATH_UNPUBLISH,
    )

TEST_FORMATS = ['json', 'xml']

def name_to_payload(name, test_format):
    """Convert service name to a payload for use with /unpublish"""
    if test_format == 'json':
        return json.dumps({'name': name}).encode('utf-8')
    elif test_format == 'xml':
        return '<service><name>{}</name></service>'.format(name).encode('utf-8')
    else:
        pytest.fail('Not implemented for test_format={}'.format(test_format))

def service_list_from_payload(payload, test_format):
    """Convert to service list from payload format"""
    if test_format == 'json':
        return [services.service_from_json_dict(x) for x in json.loads(payload)['service']]
    elif test_format == 'xml':
        root = ET.fromstring(payload)
        return [services.service_from_xml(ET.tostring(x)) for x in root]
    else:
        pytest.fail('Not implemented for test_format={}'.format(test_format))

@pytest.yield_fixture
def directory_spy():
    """Create a directory with a spy interface"""
    DirectorySpy = namedtuple( #pylint: disable=invalid-name
        'DirectorySpy', ['spy', 'real'])
    with tempfile.TemporaryDirectory() as db_dir:
        mydir = directory.ServiceDirectory(database=db_dir)
        dir_spy = mock.Mock(wraps=mydir)
        dir_spy.DoesNotExist = mydir.DoesNotExist
        # otherwise: TypeError: catching classes that do not inherit from
        #  BaseException is not allowed
        yield DirectorySpy(dir_spy, mydir)

@pytest.yield_fixture
def coap_server_setup(directory_spy): #pylint: disable=redefined-outer-name
    """Set up a CoAP server with stubbed server context to avoid network use"""
    CoAPTestcase = namedtuple( #pylint: disable=invalid-name
        'CoAPTestcase', ['coap_server', 'directory_spy'])
    with mock.patch('arrowhead.servicedirectory.coap.aiocoap.Context'):
        coap_server = coap.Server(directory=directory_spy.spy)
        directory_spy.spy.reset_mock()
        yield CoAPTestcase(coap_server, directory_spy)

@pytest.yield_fixture
def coap_server_filled(coap_server_setup): #pylint: disable=redefined-outer-name
    """Yield a CoAP Server with some pre-populated services"""
    for testcase in EXAMPLE_SERVICES.values():
        # Put some services in the registry
        coap_server_setup.directory_spy.real.publish(service=testcase['service'])
    yield coap_server_setup

def test_coap_server(directory_spy): #pylint: disable=redefined-outer-name
    """Test initialization of the CoAP Server object"""
    coap_bind = '127.0.0.1'
    coap_port = random.randint(1024, 60000)
    with mock.patch('arrowhead.servicedirectory.coap.aiocoap.Context'):
        coap_server = coap.Server(directory=directory_spy.spy, bind=(coap_bind, coap_port))
        assert isinstance(coap_server, coap.Server)
        assert arrowhead.servicedirectory.coap.aiocoap.Context.create_server_context.call_count == 1
        arrowhead.servicedirectory.coap.\
            aiocoap.Context.create_server_context.\
            assert_called_once_with(mock.ANY, bind=(coap_bind, coap_port))
        for call in directory_spy.spy.method_calls:
            if call[0] not in (
                    'service',
                    'add_notify_callback',
                    'del_notify_callback',
                    'types',
                    'service_list'):
                pytest.fail(
                    'Called directory method {}({}, {}) during instantiation' \
                    .format(call[0], call[1], call[2]))
        assert directory_spy.spy.publish.call_count == 0
        assert directory_spy.spy.unpublish.call_count == 0

@pytest.mark.asyncio
def test_coap_wkc(coap_server_setup): #pylint: disable=redefined-outer-name
    """Test that the CoAP server provides the expected resource links in /.well-known/core"""
    req = aiocoap.Message(code=Code.GET)
    req.opt.uri_path = URI_PATH_WKC
    req.opt.accept = aiocoap.numbers.media_types_rev['application/link-format']
    res = yield from coap_server_setup.coap_server.site.render(req)
    assert isinstance(res, aiocoap.Message)
    links = link_header.parse(res.payload.decode('utf-8'))
    for resource in EXPECTED_ROOT_RESOURCES:
        assert resource in [tuple(link[0][1:].split('/')) for link in links.to_py()]

@pytest.mark.parametrize("test_format", TEST_FORMATS)
@pytest.mark.asyncio
def test_coap_publish(test_format, coap_server_setup): #pylint: disable=redefined-outer-name
    """Test CoAP publish with known good payloads"""
    coap_server = coap_server_setup.coap_server
    dir_spy = coap_server_setup.directory_spy.spy
    service_to_payload = getattr(services, 'service_to_' + test_format)
    content_format = aiocoap.numbers.media_types_rev['application/' + test_format]
    for testcase in EXAMPLE_SERVICES.values():
        # Publish services
        dir_spy.reset_mock()
        payload = testcase['as_' + test_format].encode('utf-8')
        req = aiocoap.Message(code=Code.POST, payload=payload)
        req.opt.content_format = content_format
        req.opt.uri_path = URI_PATH_PUBLISH
        res = yield from coap_server.site.render(req)
        assert isinstance(res, aiocoap.Message)
        assert res.code in (Code.CREATED, )
        assert dir_spy.publish.call_count == 1
        for call in dir_spy.method_calls:
            if call[0] == 'publish':
                assert call == mock.call.publish(service=testcase['service'])

    for testcase in EXAMPLE_SERVICES.values():
        # Update the published service
        dir_spy.reset_mock()
        service = services.service_dict(**testcase['service'])
        service['port'] = int(service['port']) + 111
        payload = service_to_payload(service).encode('utf-8')
        req = aiocoap.Message(code=Code.POST, payload=payload)
        req.opt.content_format = content_format
        req.opt.uri_path = URI_PATH_PUBLISH
        res = yield from coap_server.site.render(req)
        assert isinstance(res, aiocoap.Message)
        assert res.code in (Code.CHANGED, )
        assert dir_spy.publish.call_count == 1
        for call in dir_spy.method_calls:
            if call[0] == 'publish':
                assert call == mock.call.publish(service=service)

@pytest.mark.parametrize("test_format", TEST_FORMATS)
@pytest.mark.asyncio
def test_coap_service(test_format, coap_server_filled): #pylint: disable=redefined-outer-name
    """Test CoAP service query"""
    coap_server = coap_server_filled.coap_server
    content_format = aiocoap.numbers.media_types_rev['application/' + test_format]
    service_from_payload = getattr(services, 'service_from_' + test_format)
    for testcase in EXAMPLE_SERVICES.values():
        name = testcase['service']['name']
        req = aiocoap.Message(code=Code.GET, payload=''.encode('utf-8'))
        req.opt.accept = content_format
        req.opt.uri_path = URI_PATH_SERVICE + (name, )
        res = yield from coap_server.site.render(req)
        assert isinstance(res, aiocoap.Message)
        assert res.code in (Code.CONTENT, )
        output = service_from_payload(res.payload.decode('utf-8'))
        assert output == testcase['service']
    name = 'nonexistant.service._coap._udp'
    req = aiocoap.Message(code=Code.GET, payload=''.encode('utf-8'))
    req.opt.accept = content_format
    req.opt.uri_path = URI_PATH_SERVICE + (name, )
    with pytest.raises(coap.NotFoundError):
        res = yield from coap_server.site.render(req)

@pytest.mark.parametrize("test_format", TEST_FORMATS)
@pytest.mark.asyncio
def test_coap_service_list(test_format, coap_server_filled): #pylint: disable=redefined-outer-name
    """Test CoAP service query"""
    coap_server = coap_server_filled.coap_server
    mydir = coap_server_filled.directory_spy.real
    numitems = len(mydir.service_list())
    content_format = aiocoap.numbers.media_types_rev['application/' + test_format]
    req = aiocoap.Message(code=Code.GET, payload=''.encode('utf-8'))
    req.opt.accept = content_format
    req.opt.uri_path = URI_PATH_SERVICE
    res = yield from coap_server.site.render(req)
    assert isinstance(res, aiocoap.Message)
    assert res.code in (Code.CONTENT, )
    slist = service_list_from_payload(res.payload.decode('utf-8'), test_format)
    sdict = {srv['name']: srv for srv in slist}
    assert len(slist) == numitems
    for service in mydir.service_list():
        assert service['name'] in sdict
        for key in services.service_dict().keys():
            assert sdict[service['name']][key] == service[key]

@pytest.mark.parametrize("test_format", TEST_FORMATS)
@pytest.mark.asyncio
def test_coap_unpublish(test_format, coap_server_filled): #pylint: disable=redefined-outer-name
    """Test CoAP unpublish"""
    coap_server = coap_server_filled.coap_server
    dir_spy = coap_server_filled.directory_spy.spy
    content_format = aiocoap.numbers.media_types_rev['application/' + test_format]

    for testcase in EXAMPLE_SERVICES.values():
        # Unpublish the services
        dir_spy.reset_mock()
        name = testcase['service']['name']
        payload = name_to_payload(name, test_format)
        req = aiocoap.Message(code=Code.POST, payload=payload)
        req.opt.content_format = content_format
        req.opt.uri_path = URI_PATH_UNPUBLISH
        res = yield from coap_server.site.render(req)
        assert isinstance(res, aiocoap.Message)
        assert res.code in (Code.DELETED, )
        assert dir_spy.unpublish.call_count == 1
        for call in dir_spy.method_calls:
            if call[0] == 'unpublish':
                assert call == mock.call.unpublish(name=name)

@pytest.mark.asyncio
def test_coap_publish_bad_type(coap_server_setup): #pylint: disable=redefined-outer-name
    """Test CoAP publish with unknown content formats"""
    coap_server = coap_server_setup.coap_server
    dir_spy = coap_server_setup.directory_spy.spy
    dir_spy.reset_mock()

    testcase = EXAMPLE_SERVICES[next(iter(EXAMPLE_SERVICES))]
    payload = testcase['as_json'].encode('utf-8')

    # missing Content-format option
    req = aiocoap.Message(code=Code.POST, payload=payload)
    req.opt.uri_path = URI_PATH_PUBLISH
    res = yield from coap_server.site.render(req)
    assert isinstance(res, aiocoap.Message)
    assert res.code in (Code.UNSUPPORTED_MEDIA_TYPE, )

    # wrong Content-format option
    req = aiocoap.Message(code=Code.POST, payload=payload)
    req.opt.uri_path = URI_PATH_PUBLISH
    req.opt.content_format = 30
    res = yield from coap_server.site.render(req)
    assert isinstance(res, aiocoap.Message)
    assert res.code in (Code.UNSUPPORTED_MEDIA_TYPE, )
    assert len(dir_spy.method_calls) == 0

@pytest.mark.asyncio
def test_coap_publish_wrong_format(coap_server_setup): #pylint: disable=redefined-outer-name
    """Test CoAP publish with wrong content format"""
    coap_server = coap_server_setup.coap_server
    dir_spy = coap_server_setup.directory_spy.spy
    dir_spy.reset_mock()

    testcase = EXAMPLE_SERVICES[next(iter(EXAMPLE_SERVICES))]
    payload = testcase['as_xml'].encode('utf-8')
    req = aiocoap.Message(code=Code.POST, payload=payload)
    req.opt.uri_path = URI_PATH_PUBLISH
    req.opt.content_format = aiocoap.numbers.media_types_rev['application/json']
    res = yield from coap_server.site.render(req)
    assert isinstance(res, aiocoap.Message)
    assert res.code in (Code.BAD_REQUEST, )
    assert len(dir_spy.method_calls) == 0

@pytest.mark.parametrize("test_format", TEST_FORMATS)
@pytest.mark.asyncio
def test_coap_publish_neg(test_format, coap_server_setup): #pylint: disable=redefined-outer-name
    """Test CoAP publish broken services"""
    coap_server = coap_server_setup.coap_server
    dir_spy = coap_server_setup.directory_spy.spy

    for testcase in BROKEN_SERVICES.values():
        dir_spy.reset_mock()
        payload = testcase['as_' + test_format].encode('utf-8')
        req = aiocoap.Message(code=Code.POST, payload=payload)
        req.opt.uri_path = URI_PATH_PUBLISH
        req.opt.content_format = aiocoap.numbers.media_types_rev['application/' + test_format]
        res = yield from coap_server.site.render(req)
        assert isinstance(res, aiocoap.Message)
        assert res.code in (Code.BAD_REQUEST, )
        assert len(dir_spy.method_calls) == 0

@pytest.mark.asyncio
def test_coap_service_default(coap_server_filled): #pylint: disable=redefined-outer-name
    """Test that /service gives a proper response without Accept headers"""
    test_format = 'json'
    coap_server = coap_server_filled.coap_server
    mydir = coap_server_filled.directory_spy.real
    numitems = len(mydir.service_list())
    #content_format = aiocoap.numbers.media_types_rev['application/' + test_format]
    req = aiocoap.Message(code=Code.GET, payload=''.encode('utf-8'))
    #req.opt.accept = content_format
    req.opt.uri_path = URI_PATH_SERVICE
    res = yield from coap_server.site.render(req)
    assert isinstance(res, aiocoap.Message)
    assert res.code in (Code.CONTENT, )
    slist = service_list_from_payload(res.payload.decode('utf-8'), test_format)
    sdict = {srv['name']: srv for srv in slist}
    assert len(slist) == numitems
    for service in mydir.service_list():
        assert service['name'] in sdict
        for key in services.service_dict().keys():
            assert sdict[service['name']][key] == service[key]
