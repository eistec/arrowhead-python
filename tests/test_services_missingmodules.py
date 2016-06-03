"""Test that the arrowhead.services module can import without some library modules present"""
import importlib
from unittest import mock
import pytest

TEST_SETUP = {
    'without json': {
        'missing_functions': (
            'service_from_json',
            'service_from_json_dict',
            'service_to_json',
            'service_to_json_dict',
            'servicelist_to_json',
            'typelist_to_json',
            ),
        'indicator': 'HAVE_JSON',
        'deleted_modules': ('json', 'simplejson'),
    },
    'without xml': {
        'missing_functions': (
            'service_from_xml',
            #'service_to_xml',
            #'servicelist_to_xml',
            #'typelist_to_xml', # not using xml for this
            ),
        'indicator': 'HAVE_XML',
        'deleted_modules': ('xml', ),
    },
    'without link_header': {
        'missing_functions': (
            #'service_to_corelf', # not using link_header
            'servicelist_to_corelf',
            'typelist_to_corelf',
            ),
        'indicator': 'HAVE_LINK_HEADER',
        'deleted_modules': ('link_header', ),
    },
}

@pytest.mark.parametrize('testcase', TEST_SETUP.items(), ids=(lambda x: str(x[0])))
def test_have_json(testcase):
    """Verify that the arrowhead.services module imports without the json module present"""
    services = importlib.import_module('arrowhead.services')
    importlib.reload(services)

    assert getattr(services, testcase[1]['indicator'])
    for func in testcase[1]['missing_functions']:
        assert func in services.__dict__
    del services
    with mock.patch.dict('sys.modules', {name: None for name in testcase[1]['deleted_modules']}):
        services = importlib.import_module('arrowhead.services')
        importlib.reload(services)
        assert not getattr(services, testcase[1]['indicator'])
        for func in testcase[1]['missing_functions']:
            assert func not in services.__all__
