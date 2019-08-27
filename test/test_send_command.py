import os
import json
import pytest
import parser as cp

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
MOCKED_DATA_PATH = os.path.join(TEST_DIR, 'mocked_data')
SH_INT_C_MDP = os.path.join(
    MOCKED_DATA_PATH,
    'show_interfaces_configuration.json')

# @pytest.fixture
# def cumulus_device():
#     from cumulus_parser import CumulusDevice
#
#     return CumulusDevice(
#                 hostname='TEST-HOST',
#                 username='TEST-USERNAME',
#                 password='TEST-PASSWORD'
#             )


def get_mock_data(mock_data_path):
    with open(mock_data_path, 'r') as f:
        data = json.loads(f.read())

    return json.dumps(data)


@pytest.mark.parametrize('iface, results', [
    ('vni-2905',
     [{
         'command': '',
         'host': 'TEST-HOST',
         'output': get_mock_data(SH_INT_C_MDP)
     }]),
])
def test_search_interface_configuration(iface, results):
    #print(iface)

    # hostname = hostname,
    # ip = result['host'],
    # configured = found,
    # configuration = iface_config


    assert cp.search_interface_configuration(iface, results) == 'blah'

