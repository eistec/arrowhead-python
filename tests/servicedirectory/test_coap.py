"""Test arrowhead.servicedirectory.coap"""
#pylint: disable=no-member
# pylint doesn't understand mock objects

import random
from unittest import mock
import tempfile
import json

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

def test_coap_server():
    """Test initialization of the CoAP Server object"""
    db_dir = tempfile.TemporaryDirectory()
    mydir = directory.ServiceDirectory(database=db_dir.name)
    coap_bind = '127.0.0.1'
    coap_port = random.randint(1024, 60000)
    with mock.patch('arrowhead.servicedirectory.coap.aiocoap.Context'):
        coap_server = coap.Server(directory=mydir, bind=(coap_bind, coap_port))
        assert arrowhead.servicedirectory.coap.aiocoap.Context.create_server_context.call_count == 1
        arrowhead.servicedirectory.coap.\
            aiocoap.Context.create_server_context.\
            assert_called_once_with(mock.ANY, bind=(coap_bind, coap_port))
        req = aiocoap.Message(code=Code.GET)
        req.opt.uri_path = URI_PATH_WKC
        req.opt.accept = aiocoap.numbers.media_types_rev['application/link-format']
        res = yield from coap_server.site.render(req)
        assert isinstance(res, aiocoap.Message)
        links = link_header.parse(res.payload.decode('utf-8'))
        for resource in EXPECTED_ROOT_RESOURCES:
            assert resource in [tuple(link[0][1:].split('/')) for link in links.to_py()]

def test_coap_pub_unp_json():
    """Test CoAP publish, unpublish with JSON content"""
    db_dir = tempfile.TemporaryDirectory()
    mydir = directory.ServiceDirectory(database=db_dir.name)
    with mock.patch('arrowhead.servicedirectory.coap.aiocoap.Context'):
        coap_server = coap.Server(directory=mydir)
        count = 0
        for testcase in EXAMPLE_SERVICES.values():
            # Publish services
            service = services.service_dict(**testcase['service'])
            payload = testcase['as_json'].encode('utf-8')
            req = aiocoap.Message(code=Code.POST, payload=payload)
            req.opt.content_format = aiocoap.numbers.media_types_rev['application/json']
            req.opt.uri_path = URI_PATH_PUBLISH
            res = yield from coap_server.site.render(req)
            assert res.code in (Code.CREATED, )
            count += 1
            output = mydir.service_list()
            assert service['name'] in [srv['name'] for srv in output]
            assert len(output) == count
        for service_dict in EXAMPLE_SERVICES.values():
            output = mydir.service_list()
            assert service_dict['service']['name'] in [srv['name'] for srv in output]
        for testcase in EXAMPLE_SERVICES.values():
            # Update the published service
            service = services.service_dict(**testcase['service'])
            service['port'] = int(service['port']) + 111
            payload = services.service_to_json(service).encode('utf-8')
            req = aiocoap.Message(code=Code.POST, payload=payload)
            req.opt.content_format = aiocoap.numbers.media_types_rev['application/json']
            req.opt.uri_path = URI_PATH_PUBLISH
            res = yield from coap_server.site.render(req)
            assert res.code in (Code.CHANGED, )
            output = mydir.service_list()
            assert service['name'] in [srv['name'] for srv in output]
            for srv in output:
                if srv['name'] == service['name']:
                    assert srv['port'] == service['port']
            assert len(output) == count
        for testcase in EXAMPLE_SERVICES.values():
            # Unpublish the services
            name = testcase['service']['name']
            payload = json.dumps({'name': name}).encode('utf-8')
            req = aiocoap.Message(code=Code.POST, payload=payload)
            req.opt.content_format = aiocoap.numbers.media_types_rev['application/json']
            req.opt.uri_path = URI_PATH_UNPUBLISH
            res = yield from coap_server.site.render(req)
            count -= 1
            assert res.code in (Code.DELETED, )
            output = mydir.service_list()
            assert name not in [srv['name'] for srv in output]
            assert len(output) == count

def test_coap_publish_bad_type():
    """Test CoAP publish with unknown content formats"""
    db_dir = tempfile.TemporaryDirectory()
    mydir = directory.ServiceDirectory(database=db_dir.name)
    with mock.patch('arrowhead.servicedirectory.coap.aiocoap.Context'):
        coap_server = coap.Server(directory=mydir)
        testcase = EXAMPLE_SERVICES[next(iter(EXAMPLE_SERVICES))]
        payload = testcase['as_json'].encode('utf-8')
        req = aiocoap.Message(code=Code.POST, payload=payload)
        req.opt.uri_path = URI_PATH_PUBLISH
        res = yield from coap_server.site.render(req)
        assert res.code in (Code.UNSUPPORTED_MEDIA_TYPE, )
        req = aiocoap.Message(code=Code.POST, payload=payload)
        req.opt.uri_path = URI_PATH_PUBLISH
        req.opt.content_format = 30
        res = yield from coap_server.site.render(req)
        assert res.code in (Code.UNSUPPORTED_MEDIA_TYPE, )
        output = mydir.service_list()
        assert len(output) == 0

def test_coap_publish_wrong_format():
    """Test CoAP publish with wrong content format"""
    db_dir = tempfile.TemporaryDirectory()
    mydir = directory.ServiceDirectory(database=db_dir.name)
    with mock.patch('arrowhead.servicedirectory.coap.aiocoap.Context'):
        coap_server = coap.Server(directory=mydir)
        testcase = EXAMPLE_SERVICES[next(iter(EXAMPLE_SERVICES))]
        payload = testcase['as_xml'].encode('utf-8')
        req = aiocoap.Message(code=Code.POST, payload=payload)
        req.opt.uri_path = URI_PATH_PUBLISH
        req.opt.content_format = aiocoap.numbers.media_types_rev['application/json']
        res = yield from coap_server.site.render(req)
        assert res.code in (Code.BAD_REQUEST, )
        output = mydir.service_list()
        assert len(output) == 0

def test_coap_publish_neg():
    """Test CoAP publish broken services"""
    db_dir = tempfile.TemporaryDirectory()
    mydir = directory.ServiceDirectory(database=db_dir.name)
    with mock.patch('arrowhead.servicedirectory.coap.aiocoap.Context'):
        coap_server = coap.Server(directory=mydir)
        for testcase in BROKEN_SERVICES.values():
            payload = testcase['as_json'].encode('utf-8')
            req = aiocoap.Message(code=Code.POST, payload=payload)
            req.opt.uri_path = URI_PATH_PUBLISH
            req.opt.content_format = aiocoap.numbers.media_types_rev['application/json']
            res = yield from coap_server.site.render(req)
            assert res.code in (Code.BAD_REQUEST, )
            output = mydir.service_list()
            assert len(output) == 0
