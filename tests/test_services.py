"""Unit tests for arrowhead.services"""
import json
import xml.etree.ElementTree as ET

import pytest
import link_header
from arrowhead import services
from .test_data import EXAMPLE_SERVICES, BROKEN_XML



@pytest.mark.parametrize('testcase', EXAMPLE_SERVICES.items(), ids=(lambda x: str(x[0])))
def test_Service(testcase):
    """Test the Service constructor"""
    indata_dict = testcase[1]['service']
    service = services.Service(**indata_dict)
    for attr in indata_dict.keys() - ['properties']:
        assert getattr(service, attr) == indata_dict[attr]
    for name, value in indata_dict['properties'].items():
        assert getattr(service.properties, name) == value

def test_Service_eq():
    """Test Service comparison operations"""
    for lhs_case in EXAMPLE_SERVICES.values():
        lhs_dict = lhs_case['service']
        lhs_service = services.Service(**lhs_dict)
        for rhs_case in EXAMPLE_SERVICES.values():
            rhs_service = services.Service(**rhs_case['service'])
            equal = True
            for attr in lhs_dict.keys() - ['properties']:
                if not getattr(rhs_service, attr) == lhs_dict[attr]:
                    equal = False
            for prop in lhs_dict['properties'].keys():
                if not getattr(rhs_service.properties, prop) == lhs_dict['properties'][prop]:
                    equal = False
            if equal:
                assert lhs_service == rhs_service
                assert not lhs_service != rhs_service
            else:
                assert not lhs_service == rhs_service
                assert lhs_service != rhs_service

@pytest.mark.parametrize('testcase', EXAMPLE_SERVICES.items(), ids=(lambda x: str(x[0])))
def test_service_to_json(testcase):
    '''Loading the output from service_to_json should give the same dict as the input data'''
    # testcase is a tuple (testname, indata)
    indata_dict = testcase[1]['service']
    expected_dict = indata_dict
    service_input = services.Service(**indata_dict)
    service_json = services.service_to_json(service_input)
    service = json.loads(service_json)
    assert set(service.keys()) == set(expected_dict.keys())
    for key in service.keys() - ['properties']:
        assert expected_dict[key] == service[key]
    props = {}
    for prop in service['properties']['property']:
        assert prop['name'] not in props
        props[prop['name']] = prop['value']
    for name, value in expected_dict['properties'].items():
        assert name in props
        assert props[name] == value

@pytest.mark.parametrize('testcase', EXAMPLE_SERVICES.items(), ids=(lambda x: str(x[0])))
def test_service_to_xml(testcase):
    '''service_to_xml should give an xml representation of the service'''
    # testcase is a tuple (testname, indata)
    indata_dict = testcase[1]['service']
    expected_dict = indata_dict
    service_input = services.Service(**indata_dict)
    service_xml = services.service_to_xml(service_input)
    root = ET.fromstring(service_xml)
    assert root.tag == 'service'
    service = {}
    for node in root:
        assert not node.attrib
        assert not node.tail or node.tail.isspace()
        assert node.tag not in service
        if node.tag == 'properties':
            props = {}
            for child in node:
                assert child.tag == 'property'
                name = None
                value = None
                for prop in child:
                    assert not list(prop)
                    assert not prop.tail or prop.tail.isspace()
                    assert prop.text.strip()
                    assert prop.tag in ('name', 'value')
                    if prop.tag == 'name':
                        assert name is None
                        name = prop.text.strip()
                    elif prop.tag == 'value':
                        assert value is None
                        value = prop.text.strip()

                assert name not in props
                props[name] = value
            service['properties'] = props
            continue
        assert node.text.strip()
        assert node.text.strip() == str(indata_dict[node.tag])
        service[node.tag] = node.text.strip()
        if node.tag == 'port':
            service[node.tag] = int(service[node.tag])
        assert not list(node)
    # Check that there is no garbage text around
    assert not root.text or root.text.isspace()
    assert not root.tail or root.tail.isspace()
    for key in expected_dict.keys() - ['properties']:
        assert service[key] == expected_dict[key]
    for name, value in expected_dict['properties'].items():
        assert name in service['properties']
        assert value == service['properties'][name]

@pytest.mark.parametrize('testcase', EXAMPLE_SERVICES.items(), ids=(lambda x: str(x[0])))
def test_service_from_json(testcase):
    '''service_from_json should create a service dict from JSON text'''
    # testcase is a tuple (testname, testdata)
    json_input = testcase[1]['as_json']
    expected_dict = testcase[1]['service']
    service = services.service_from_json(json_input)
    for key in expected_dict.keys() - ['properties']:
        assert getattr(service, key) == expected_dict[key]
    for name, value in expected_dict['properties'].items():
        assert getattr(service.properties, name) == value

@pytest.mark.parametrize('testcase', EXAMPLE_SERVICES.items(), ids=(lambda x: str(x[0])))
def test_service_from_xml(testcase):
    '''service_from_xml should create a service dict from XML text'''
    # testcase is a tuple (testname, testdata)
    xml_input = testcase[1]['as_xml']
    expected_dict = testcase[1]['service']
    service = services.service_from_xml(xml_input)
    for key in expected_dict.keys() - ['properties']:
        assert getattr(service, key) == expected_dict[key]
    for name, value in expected_dict['properties'].items():
        assert getattr(service.properties, name) == value

@pytest.mark.parametrize('testcase', BROKEN_XML.items(), ids=(lambda x: str(x[0])))
def test_service_from_xml_neg(testcase):
    '''service_from_xml should raise exceptions on broken XML'''
    xml_input = testcase[1]
    with pytest.raises(services.ServiceError):
        service = services.service_from_xml(xml_input)
        assert isinstance(service, services.Service)

def test_servicelist_to_corelf():
    '''service_to_corelf should give a Link object'''
    slist = [services.Service(**case['service']) for case in EXAMPLE_SERVICES.values()]
    links = link_header.parse(str(services.servicelist_to_corelf(slist, '/uri/base')))
    uris = {('uri', 'base') + (srv.name, ) for srv in slist}
    for link in links.links:
        assert tuple(link.href.strip('/').split('/')) in uris
        uris.remove(tuple(link.href.strip('/').split('/')))
    assert len(uris) == 0
