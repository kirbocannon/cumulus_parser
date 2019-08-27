import os
import pytest
import parser as cp
import test.conf as conf

SH_INT_C_MDP = os.path.join(
    conf.MOCKED_DATA_PATH,
    'show_interfaces_configuration.json')
SH_CLAG = os.path.join(
    conf.MOCKED_DATA_PATH,
    'show_clag.json')
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


@pytest.mark.parametrize('iface, results', [
    (TEST_INTERFACE['name'],
     [{
         'host': 'TEST-HOST',
         'output': conf.get_mock_data(SH_INT_C_MDP)
     }]
     ),
])
def test_search_interface_configuration(iface, results):
    iface = cp.search_interface_configuration(iface, results)[0].get('configuration')
    assert iface == TEST_INTERFACE


@pytest.mark.parametrize('results', [
    (conf.get_mock_data(SH_CLAG)),
])
def test_check_clag(results):
    clags = cp.check_clag(results)['down_peers']
    assert len(clags) == 1


