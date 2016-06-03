"""Test arrowhead.servicedirectory.coap"""
#pylint: disable=no-member
# pylint doesn't understand mock objects

import random
from unittest import mock
import tempfile

import pytest

import aiocoap
import link_header
from aiocoap.numbers.codes import Code

from arrowhead.servicedirectory import directory
from arrowhead.servicedirectory import coap
import arrowhead

from ..test_data import EXAMPLE_SERVICES

EXPECTED_ROOT_RESOURCES = (
    ('.well-known', 'core'),
    ('servicediscovery', 'service'),
    ('servicediscovery', 'type'),
    ('servicediscovery', 'publish'),
    ('servicediscovery', 'unpublish'),
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
        arrowhead.servicedirectory.coap.aiocoap.Context.create_server_context.assert_called_once_with(mock.ANY, bind=(coap_bind, coap_port))
        req = aiocoap.Message(code=Code.GET)
        req.opt.uri_path = ('.well-known', 'core')
        req.opt.accept = aiocoap.numbers.media_types_rev['application/link-format']
        res = yield from coap_server.site.render(req)
        assert isinstance(res, aiocoap.Message)
        links = link_header.parse(res.payload.decode('utf-8'))
        for resource in EXPECTED_ROOT_RESOURCES:
            assert resource in [tuple(link[0][1:].split('/')) for link in links.to_py()]
