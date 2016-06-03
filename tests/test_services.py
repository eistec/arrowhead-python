"""Unit tests for arrowhead.services"""
import json
import xml.etree.ElementTree as ET

import pytest
from arrowhead import services
from .test_data import EXAMPLE_SERVICES

@pytest.mark.parametrize('testcase', EXAMPLE_SERVICES.items(), ids=(lambda x: str(x[0])))
def test_service_dict(testcase):
    '''Verify that all basic service information gets set by the constructor'''
    # testcase is a tuple (testname, indata)
    indata_dict = testcase[1]['service']
    service = services.service_dict(**indata_dict)
    for attr in indata_dict.keys() - ['properties']:
        assert service[attr] == indata_dict[attr]
    for name, value in indata_dict['properties'].items():
        assert name in service['properties']
        assert value == service['properties'][name]

@pytest.mark.parametrize('testcase', EXAMPLE_SERVICES.items(), ids=(lambda x: str(x[0])))
def test_service_to_json(testcase):
    '''Loading the output from as_json should give the same dict as the input data'''
    # testcase is a tuple (testname, indata)
    indata_dict = testcase[1]['service']
    expected_dict = indata_dict
    service_json = services.service_to_json(indata_dict)
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
    '''as_xml should give an xml representation of the service'''
    # testcase is a tuple (testname, indata)
    indata_dict = testcase[1]['service']
    expected_dict = indata_dict
    service_xml = services.service_to_xml(indata_dict)
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
    '''service_parse_json should create a Service instance from JSON text'''
    # testcase is a tuple (testname, testdata)
    json_input = testcase[1]['as_json']
    expected_dict = testcase[1]['service']
    service = services.service_from_json(json_input)
    for key in expected_dict.keys() - ['properties']:
        assert service[key] == expected_dict[key]
    for name, value in expected_dict['properties'].items():
        assert name in service['properties']
        assert value == service['properties'][name]

@pytest.mark.parametrize('testcase', EXAMPLE_SERVICES.items(), ids=(lambda x: str(x[0])))
def test_service_from_xml(testcase):
    '''service_parse_json should create a Service instance from JSON text'''
    # testcase is a tuple (testname, testdata)
    xml_input = testcase[1]['as_xml']
    expected_dict = testcase[1]['service']
    service = services.service_from_xml(xml_input)
    for key in expected_dict.keys() - ['properties']:
        assert service[key] == expected_dict[key]
    for name, value in expected_dict['properties'].items():
        assert name in service['properties']
        assert value == service['properties'][name]
