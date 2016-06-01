"""Unit tests for arrowhead.services"""
try:
    import json
except ImportError:
    import simplejson as json
import xml.etree.ElementTree as ET

import pytest
from arrowhead import services

EXAMPLE_SERVICES = {
    'SingleService1': {
        'service': {
            "name": "orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.",
            "type": "_orch-s-ws-https._tcp",
            "domain": "arces.unibo.it.",
            "host": "bedework.arces.unibo.it.",
            "port": 8181,
            "properties": {
                "version": "1.0",
                "path": "/orchestration/store/"
            }
        },
        'as_json': '''
            {
                "name": "orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.",
                "type": "_orch-s-ws-https._tcp",
                "domain": "arces.unibo.it.",
                "host": "bedework.arces.unibo.it.",
                "port": 8181,
                "properties": {
                    "property": [
                        {
                            "name": "version",
                            "value": "1.0"
                        },
                        {
                            "name": "path",
                            "value": "/orchestration/store/"
                        }
                    ]
                }
            }''',
        'as_xml': '''
            <service>
                <domain>arces.unibo.it.</domain>
                <host>bedework.arces.unibo.it.</host>
                <name>orchestration-store._orch-s-ws-https._tcp.srv.arces.unibo.it.</name>
                <port>8181</port>
                <properties>
                    <property>
                        <name>version</name>
                        <value>1.0</value>
                    </property>
                    <property>
                        <name>path</name>
                        <value>/orchestration/store/</value>
                    </property>
                </properties>
                <type>_orch-s-ws-https._tcp</type>
            </service>
        '''
    },
    'SingleService2': {
        'service': {
            "name": "anotherprinterservice._printer-s-ws-https._tcp.srv.arces.unibo.it.",
            "type": "_printer-s-ws-https._tcp",
            "domain": "168.56.101.",
            "host": "192.168.56.101.",
            "port": 8055,
            "properties": {
                "version": "1.0",
                "path": "/printer/something"
            }
        },
        'as_json': '''
            {
                "name": "anotherprinterservice._printer-s-ws-https._tcp.srv.arces.unibo.it.",
                "type": "_printer-s-ws-https._tcp",
                "domain": "168.56.101.",
                "host": "192.168.56.101.",
                "port": 8055,
                "properties": {
                    "property": [
                        {
                            "name": "version",
                            "value": "1.0"
                        },
                        {
                            "name": "path",
                            "value": "/printer/something"
                        }
                    ]
                }
            }
        ''',
        'as_xml': '''
            <service>
                <domain>168.56.101.</domain>
                <host>192.168.56.101.</host>
                <name>anotherprinterservice._printer-s-ws-https._tcp.srv.arces.unibo.it.</name>
                <port>8055</port>
                <properties>
                    <property>
                        <name>version</name>
                        <value>1.0</value>
                    </property>
                    <property>
                        <name>path</name>
                        <value>/printer/something</value>
                    </property>
                </properties>
                <type>_printer-s-ws-https._tcp</type>
            </service>
        '''
    }
}

@pytest.mark.parametrize('testcase', EXAMPLE_SERVICES.items(), ids=(lambda x: str(x[0])))
def test_service_dict(testcase):
    '''Verify that all basic service information gets set by the constructor'''
    # testcase is a tuple (testname, indata)
    indata_dict = testcase[1]['service']
    s = services.service_dict(**indata_dict)
    for attr in indata_dict.keys() - ['properties']:
        assert s[attr] == indata_dict[attr]
    for name, value in indata_dict['properties'].items():
        assert name in s['properties']
        assert value == s['properties'][name]

@pytest.mark.parametrize('testcase', EXAMPLE_SERVICES.items(), ids=(lambda x: str(x[0])))
def test_service_to_json(testcase):
    '''Loading the output from as_json should give the same dict as the input data'''
    # testcase is a tuple (testname, indata)
    indata_dict = testcase[1]['service']
    s = services.service_dict(**indata_dict)
    js = services.service_to_json(s)
    sd = json.loads(js)
    assert set(sd.keys()) == set(indata_dict.keys())
    for key in sd.keys() - ['properties']:
        assert indata_dict[key] == sd[key]
    props = {}
    for prop in sd['properties']['property']:
        assert prop['name'] not in props
        props[prop['name']] = prop['value']
    for name, value in indata_dict['properties'].items():
        assert name in props
        assert props[name] == value

@pytest.mark.parametrize('testcase', EXAMPLE_SERVICES.items(), ids=(lambda x: str(x[0])))
def test_service_to_xml(testcase):
    '''as_xml should give an xml representation of the service'''
    # testcase is a tuple (testname, indata)
    indata_dict = testcase[1]['service']
    s = services.service_dict(**indata_dict)
    sx = services.service_to_xml(s)
    root = ET.fromstring(sx)
    assert root.tag == 'service'
    s = {}
    for child in root:
        assert not child.attrib
        assert not child.tail or child.tail.isspace()
        assert child.tag not in s
        if child.tag == 'properties':
            props = {}
            for c in child:
                assert c.tag == 'property'
                name = None
                value = None
                for pc in c:
                    assert not list(pc)
                    assert not pc.tail or pc.tail.isspace()
                    assert pc.text.strip()
                    if pc.tag == 'name':
                        assert name is None
                        name = pc.text.strip()
                    elif pc.tag == 'value':
                        assert value is None
                        value = pc.text.strip()
                    else:
                        assert 0
                assert name not in props
                props[name] = value
            s['properties'] = props
            continue
        assert child.text.strip()
        assert child.text.strip() == str(indata_dict[child.tag])
        s[child.tag] = child.text.strip()
        assert not list(child)
    # Check that there is no garbage text around
    assert not root.text or root.text.isspace()
    assert not root.tail or root.tail.isspace()

@pytest.mark.parametrize('testcase', EXAMPLE_SERVICES.items(), ids=(lambda x: str(x[0])))
def test_service_from_json(testcase):
    '''service_parse_json should create a Service instance from JSON text'''
    # testcase is a tuple (testname, testdata)
    json_input = testcase[1]['as_json']
    expected_dict = testcase[1]['service']
    s = services.service_from_json(json_input)
    for key in expected_dict.keys() - ['properties']:
        assert s[key] == expected_dict[key]
    for name, value in expected_dict['properties'].items():
        assert name in s['properties']
        assert value == s['properties'][name]

@pytest.mark.parametrize('testcase', EXAMPLE_SERVICES.items(), ids=(lambda x: str(x[0])))
def test_service_from_xml(testcase):
    '''service_parse_json should create a Service instance from JSON text'''
    # testcase is a tuple (testname, testdata)
    xml_input = testcase[1]['as_xml']
    expected_dict = testcase[1]['service']
    s = services.service_from_xml(xml_input)
    for key in expected_dict.keys() - ['properties']:
        assert str(s[key]) == str(expected_dict[key])
    for name, value in expected_dict['properties'].items():
        assert name in s['properties']
        assert str(value) == str(s['properties'][name])

