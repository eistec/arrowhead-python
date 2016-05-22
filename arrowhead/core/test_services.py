import pytest
from arrowhead.core import services
try:
    import json
except ImportError:
    import simplejson as json

class TestService(object):
    example_services = {
        'SingleService1': {
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
        },
        'SingleService2': {
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
    }

    @pytest.mark.parametrize('testcase', example_services.items(), ids=(lambda x: str(x[0])))
    def test_attrs(self, testcase):
        '''Verify that all basic service information gets set by the constructor'''
        # testcase is a tuple (testname, indata)
        indata_dict = testcase[1]
        s = services.Service(**indata_dict)
        for attr in indata_dict.keys() - ['properties']:
            assert getattr(s, attr) == indata_dict[attr]

    @pytest.mark.parametrize('testcase', example_services.items(), ids=(lambda x: str(x[0])))
    def test_properties(self, testcase):
        '''self.properties should be a dict with key->value pairs of the given properties'''
        # testcase is a tuple (testname, indata)
        indata_dict = testcase[1]
        s = services.Service(**indata_dict)
        for prop in indata_dict['properties']['property']:
            assert prop['name'] in s.properties
            assert prop['value'] == s.properties[prop['name']]

    @pytest.mark.parametrize('testcase', example_services.items(), ids=(lambda x: str(x[0])))
    def test_as_dict(self, testcase):
        '''as_dict should give the same dictionary as the examples'''
        # testcase is a tuple (testname, indata)
        indata_dict = testcase[1]
        s = services.Service(**indata_dict)
        sd = s.as_dict()
        assert set(sd.keys()) == set(indata_dict.keys())
        for key in (sd.keys() - ['properties']):
            assert indata_dict[key] == sd[key]

    @pytest.mark.parametrize('testcase', example_services.items(), ids=(lambda x: str(x[0])))
    def test_as_json(self, testcase):
        '''The output from as_json should give the same dict as the input data'''
        # testcase is a tuple (testname, indata)
        indata_dict = testcase[1]
        s = services.Service(**indata_dict)
        js = s.as_json()
        sd = json.loads(js)
        assert set(sd.keys()) == set(indata_dict.keys())
        for key in (sd.keys() - ['properties']):
            assert indata_dict[key] == sd[key]

    @pytest.mark.parametrize('testcase', example_services.items(), ids=(lambda x: str(x[0])))
    def test_as_xml(self, testcase):
        '''as_xml should give the same output as running json.dumps on the input data'''
        # testcase is a tuple (testname, indata)
        indata_dict = testcase[1]
        s = services.Service(**indata_dict)
        js = s.as_xml()
        raise NotImplementedError('TODO: Add XML handling')

test_json_inputs = {
    'SingleServiceJSON':
        { 'as_json': '''{
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
}''',
    'as_dict': {
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
    }
}

@pytest.mark.parametrize('testcase', test_json_inputs.items(), ids=(lambda x: str(x[0])))
def test_service_parse_json(testcase):
    '''service_parse_json should create a Service instance from JSON text'''
    # testcase is a tuple (testname, testdata)
    json_input = testcase[1]['as_json']
    expected_dict = testcase[1]['as_dict']
    s = services.service_parse_json(json_input)
    assert isinstance(s, services.Service)
    for attr in expected_dict.keys() - ['properties']:
        assert getattr(s, attr) == expected_dict[attr]
    for prop in expected_dict['properties']['property']:
        assert prop['name'] in s.properties
        assert prop['value'] == s.properties[prop['name']]

