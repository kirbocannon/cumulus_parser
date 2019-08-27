import os
import json
import pytest
import parser as cp

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
MOCKED_DATA_PATH = os.path.join(TEST_DIR, 'mocked_data')
SH_INT_C_MDP = os.path.join(
    MOCKED_DATA_PATH,
    'show_interfaces_configuration.json')
TEST_INTERFACE = {
        "name": "vni-2905",
        "alias": "",
        "ip_address": "",
        "mtu": "9148",
        "link_speed": "",
        "bond_slaves": "",
        "bridge_access": "",
        "bridge_ports": "",
        "bond_mode": "",
        "bridge_vids": "",
        "bridge_vlan_aware": "",
        "clag_id": "",
        "vrf": "",
        "clagd_anycast_ip_address": "",
        "gateway_ip_address": "",
        "vxlan_id": "2905",
        "vxlan_local_tunnel_ip_address": "10.35.0.80",
        "vxlan_remote_ip_address": ""
    }


def get_mock_data(mock_data_path):
    with open(mock_data_path, 'r') as f:
        data = json.loads(f.read())

    return data


@pytest.mark.parametrize('iface, results', [
    (TEST_INTERFACE['name'],
     [{
         'command': '',
         'host': 'TEST-HOST',
         'output': get_mock_data(SH_INT_C_MDP)
     }]
     ),
])
def test_search_interface_configuration(iface, results):
    iface = cp.search_interface_configuration(iface, results)[0].get('configuration') or ''
    assert iface == TEST_INTERFACE





