"""Test that the soa.services module can import without some library modules present"""
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

# This test will break comparison between Service objects that are created from
# factories instantiated during fixture creation and Service objects that are
# created from factories instantiated afterwards.
@pytest.mark.skip(reason="This test breaks the other services tests")
@pytest.mark.parametrize('testcase', TEST_SETUP.items(), ids=(lambda x: str(x[0])))
def test_have_json(testcase):
    """Verify that the soa.services module imports without the json module present"""

    # Note that using reload() below will cause inconsistencies between the
    # collection stage (and fixture instantiation), and the execute stage
    services = importlib.import_module('soa.services')
    importlib.reload(services)

    assert getattr(services, testcase[1]['indicator'])
    for func in testcase[1]['missing_functions']:
        assert func in services.__dict__
    del services
    with mock.patch.dict('sys.modules', {name: None for name in testcase[1]['deleted_modules']}):
        services = importlib.import_module('soa.services')
        importlib.reload(services)
        assert not getattr(services, testcase[1]['indicator'])
        for func in testcase[1]['missing_functions']:
            assert func not in services.__all__
