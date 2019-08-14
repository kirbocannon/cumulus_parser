import argparse
import os
import yaml
from utils.logger import logger
from tabulate import tabulate
from cumulus_parser import CumulusDevice
from utils import bcolors
from exceptions import *
from multiprocessing .dummy import Pool as Threadpool

HOSTS_FILENAME = 'hosts.yaml'
VALIDATION_DIR = './templates/validation'
CREDENTIALS_FILENAME = 'credentials.yaml'
VENDOR = 'cumulus'
WAIT_FOR_COMMAND_IN_SECONDS = 4
ADDRESS_FAMILIES = ['ipv4 unicast', 'l2vpn evpn']


INTERFACES_TEST = [{'name': 'lo inet loopback', 'alias': '', 'ip_address': '10.35.0.80/32', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '10.35.0.180', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'eth0', 'alias': 'MGMT-to-CSS1A-106-MGT-01 - 10274', 'ip_address': '10.30.20.80/24', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': 'mgmt', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '10.30.20.1', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp1', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp2', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp3', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp4', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp5', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp6', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp7', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp8', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp9', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp10', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp11', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp12', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp13', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp14', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp15 ', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '10000', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp30', 'alias': 'BLD01-13', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp31', 'alias': 'BLD01-14', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp32', 'alias': 'BLD01-16', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp33', 'alias': 'BLD02-01', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp16', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '10000', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp42', 'alias': 'KFG 52607 Replication', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp48', 'alias': 'Uplink to CSS1A-106-MGMT-01', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'mgmt', 'alias': '', 'ip_address': '127.0.0.1/8', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp46', 'alias': 'Uplink-to-CSS1A-105-EDG-01 - 10019', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp47', 'alias': 'Uplink-to-CSS1A-107-iSC-01 - 10245', 'ip_address': '', 'mtu': '9216', 'link_speed': '10000', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp49', 'alias': 'Uplink-to-CSS1A-105-SPN-01 - 10216', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp50', 'alias': 'Uplink-to-CSS1A-105-SPN-02 - 10217', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp55', 'alias': 'Peerlink - CSS1A-108-LEF-02 - 10232', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'swp56', 'alias': 'Peerlink - CSS1A-108-LEF-02 - 10238', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-native', 'alias': '', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'peerlink', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'peerlink', 'alias': '', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp55 swp56', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'peerlink.4094', 'alias': '', 'ip_address': '169.254.255.1/30', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSS-E004', 'alias': 'CSS1A-ESXI004 - 10059', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp1', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSS-E005', 'alias': 'CSS1A-ESXI005 - 10046', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp2', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSS-E006', 'alias': 'CSS1A-ESXI006 - 10041', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp3', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSS-E007', 'alias': 'CSS1A-ESXI007 - 10039', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp4', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSS-E001', 'alias': 'CSS1A-ESXI001 - 10151', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp5', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSS-E002', 'alias': 'CSS1A-ESXI002 - 10152', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp6', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSS-E003', 'alias': 'CSS1A-ESXI003 - 10058', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp7', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'EHM-E001', 'alias': 'EHM1A-ESXI001 - 10111 ', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp8', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'EHM-E002', 'alias': 'EHM1A-ESXI002 - 10046', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp9', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'EHM-E003', 'alias': 'EHM1A-ESXI003 - 10016', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp10', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'EHM-E004', 'alias': 'EHM1A-ESXI004 - 10056', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp11', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'EDG-E001', 'alias': 'EDG1A-ESXI001 - 10051', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp12', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'EDG-E002', 'alias': 'EDG1A-ESXI002 - 10068', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp13', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'EDG-E003', 'alias': 'EDG1A-ESXI003 - 10055', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp14', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSS-H001', 'alias': 'CSS1A-HYPV001', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp15', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSS-H002', 'alias': 'CSS1A-HYPV002', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp16', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSI-E001', 'alias': 'CSS1A-ESXI001', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp17', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSI-E002', 'alias': 'CSS1A-ESXI002', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp18', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'KFG-H001', 'alias': 'KFG1A-HV001', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp19', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '119', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSS-020', 'alias': 'UNUSED', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp20', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSS-021', 'alias': 'UNUSED', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp21', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSS-022', 'alias': 'UNUSED', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp22', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSS-023', 'alias': 'UNUSED', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp23', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CSS-024', 'alias': 'UNUSED', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp24', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CS-iLF01', 'alias': 'CSS1A-107-iSC-01 - 10245', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp47', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor ', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '201', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CS-EDGSW', 'alias': 'CSS1A-105-EDG-01 - 10019 ', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp46', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': 'balance-xor', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '202', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'CS-MGT', 'alias': 'uplink to MGT-01 and MGT-02 switches', 'ip_address': '', 'mtu': '9216', 'link_speed': '', 'bond_slaves': 'swp48', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '203', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v15', 'alias': 'CSSSF-VLAN15-02-MGMT', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.15 swp31.15 swp32.15 swp33.15 CSS-E004.15 CSS-E005.15 CSS-E006.15 CSS-E007.15 CSS-E001.15 CSS-E002.15 CSS-E003.15 EHM-E001.15 EHM-E002.15 EHM-E003.15 EHM-E004.15 EDG-E001.15 EDG-E002.15 EDG-E003.15 CSS-H001.15 CSS-H002.15 peerlink.15 vni-501', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v205', 'alias': 'CSSSF-DMZ-NET', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.205 swp31.205 swp32.205 swp33.205 EDG-E001.205 EDG-E002.205 EDG-E003.205 peerlink.205 vni-522', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v1251', 'alias': 'CSS-FIREWALL-NET', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CSS-E004.1251 CSS-E005.1251 CSS-E006.1251 CSS-E007.1251 CSS-E001.1251 CSS-E002.1251 CSS-E003.1251 EHM-E001.1251 EHM-E002.1251 EHM-E003.1251 EHM-E004.1251 EDG-E001.1251 EDG-E002.1251 EDG-E003.1251 peerlink.1251 vni-1251', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-kfg-v230', 'alias': 'KFG-VLAN230', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp42 KFG-H001 CS-iLF01.230 peerlink.230 vni-1001', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v1998', 'alias': 'BGP-01-124', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-EDGSW.1998 peerlink.1998 vni-1998', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v1999', 'alias': 'BGP-LaScala', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-EDGSW.1999 peerlink.1999 vni-1999', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v2511', 'alias': 'CS-ESXI-VMOTION', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CSS-E004.2511 CSS-E005.2511 CSS-E006.2511 CSS-E007.2511 CSS-E001.2511 CSS-E002.2511 CSS-E003.2511 EHM-E001.2511 EHM-E002.2511 EHM-E003.2511 EHM-E004.2511 EDG-E001.2511 EDG-E002.2511 EDG-E003.2511 CSS-H001.2511 CSS-H002.2511 CSI-E001.2511 CSI-E002.2511 peerlink.2511 vni-2511', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v2520', 'alias': 'CS-OOB-SWITCH-MGMT', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-MGT.2520 peerlink.2520 vni-2520', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v2521', 'alias': 'CS-iDRAC-MGMT', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-MGT.2521 peerlink.2521 vni-2521', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v2522', 'alias': 'CS-SAN-MGMT', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-MGT.2522 peerlink.2522 vni-2522', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v2577', 'alias': 'CSS-iSCSI-01', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-iLF01.2577 peerlink.2577 vni-2577', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v2578', 'alias': 'CSS-iSCSI-02', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-iLF01.2578 peerlink.2578 vni-2578', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v2579', 'alias': 'CSS-iSCSI-REPL', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-iLF01.2579 peerlink.2579 vni-2579', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v150', 'alias': 'CSSBC-O2-Net', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.150 swp31.150 swp32.150 swp33.150 CSS-E004.150 CSS-E005.150 CSS-E006.150 CSS-E007.150 CSS-E001.150 CSS-E002.150 CSS-E003.150 EHM-E001.150 EHM-E002.150 EHM-E003.150 EHM-E004.150 EDG-E001.150 EDG-E002.150 EDG-E003.150 CSS-H001.150 CSS-H002.150 peerlink.150 vni-600', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v253', 'alias': 'CSSSF-KMS-NET', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CSS-E004.253 CSS-E005.253 CSS-E006.253 CSS-E007.253 CSS-E001.253 CSS-E002.253 CSS-E003.253 EHM-E001.253 EHM-E002.253 EHM-E003.253 EHM-E004.253 EDG-E001.253 EDG-E002.253 EDG-E003.253 CSS-H001.253 CSS-H002.253 peerlink.253 vni-520', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v599', 'alias': 'CSS-SSL-VPN-Clients', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CSS-E004.599 CSS-E005.599 CSS-E006.599 CSS-E007.599 CSS-E001.599 CSS-E002.599 CSS-E003.599 EHM-E001.599 EHM-E002.599 EHM-E003.599 EHM-E004.599 EDG-E001.599 EDG-E002.599 EDG-E003.599 CSS-H001.599 CSS-H002.599 peerlink.599 vni-599', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v201', 'alias': 'CSSBC-KMS-NET', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-MGT.201 peerlink.201 vni-512', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v12', 'alias': 'CSSBC-ESXiMGMT', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.12 swp31.12 swp32.12 swp33.12 peerlink.12 vni-602', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v174', 'alias': 'CSSBC-iSCSI-01', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-iLF01.174 peerlink.174 vni-604', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v175', 'alias': 'CSSBC-iSCSI-02', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-iLF01.175 peerlink.175 vni-605', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-def-v250', 'alias': 'CSSSF-FWAL-NET', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'EDG-E001.250 EDG-E002.250 EDG-E003.250 peerlink.250 vni-250', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-ehm-v100', 'alias': 'CSSSF-VLAN100-EHM-Servers', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.100 swp31.100 swp32.100 swp33.100 EHM-E001.100 EHM-E002.100 EHM-E003.100 EHM-E004.100 CSS-H001.100 CSS-H002.100 peerlink.100 vni-504', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-ehm-v1004', 'alias': 'EHM-VDI-NET', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.1004 swp31.1004 swp32.1004 swp33.1004 CSS-E004.1004 CSS-E005.1004 CSS-E006.1004 CSS-E007.1004 CSS-E001.1004 CSS-E002.1004 CSS-E003.1004 EHM-E001.1004 EHM-E002.1004 EHM-E003.1004 EHM-E004.1004 EDG-E001.1004 EDG-E002.1004 EDG-E003.1004 CSS-H001.1004 CSS-H002.1004 peerlink.1004 vni-514', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-ult-v101', 'alias': 'CSSSF-VLAN101-Ultralevel-Net', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.101 swp31.101 swp32.101 swp33.101 CSS-E004.101 CSS-E005.101 CSS-E006.101 CSS-E007.101 CSS-E001.101 CSS-E002.101 CSS-E003.101 CSS-H001.101 CSS-H002.101 peerlink.101 vni-505', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-ara-v103', 'alias': 'CSSSF-VLAN103-ARAS-NET', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.103 swp31.103 swp32.103 swp33.103 CSS-E004.103 CSS-E005.103 CSS-E006.103 CSS-E007.103 CSS-E001.103 CSS-E002.103 CSS-E003.103 CSS-H001.103 CSS-H002.103 peerlink.103 vni-507', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-ara-v107', 'alias': 'CSSSF-VLAN107-Aras2-Net', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.107 swp31.107 swp32.107 swp33.107 CSS-E004.107 CSS-E005.107 CSS-E006.107 CSS-E007.107 CSS-E001.107 CSS-E002.107 CSS-E003.107 peerlink.107 vni-517', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-ara-v113', 'alias': 'CSSSF-Aras-Physical-Net', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.113 swp31.113 swp32.113 swp33.113 CSS-E004.113 CSS-E005.113 CSS-E006.113 CSS-E007.113 CSS-E001.113 CSS-E002.113 CSS-E003.113 peerlink.113 vni-521', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-ara-v200', 'alias': 'ARA-DMZ-NET', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.200 swp31.200 swp32.200 swp33.200 CSS-E004.200 CSS-E005.200 CSS-E006.200 CSS-E007.200 CSS-E001.200 CSS-E002.200 CSS-E003.200 EHM-E001.200 EHM-E002.200 EHM-E003.200 EHM-E004.200 EDG-E001.200 EDG-E002.200 EDG-E003.200 CSS-H001.200 CSS-H002.200 peerlink.200 vni-511', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-ara-v1003', 'alias': 'ARA-DR-NET', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.1003 swp31.1003 swp32.1003 swp33.1003 CSS-E004.1003 CSS-E005.1003 CSS-E006.1003 CSS-E007.1003 CSS-E001.1003 CSS-E002.1003 CSS-E003.1003 EHM-E001.1003 EHM-E002.1003 EHM-E003.1003 EHM-E004.1003 EDG-E001.1003 EDG-E002.1003 EDG-E003.1003 CSS-H001.1003 CSS-H002.1003 peerlink.1003 vni-513', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-csi-v104', 'alias': 'CSISF-VLAN104-CSCorp-Net', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.104 swp31.104 swp32.104 swp33.104 CSS-E004.104 CSS-E005.104 CSS-E006.104 CSS-E007.104 CSS-E001.104 CSS-E002.104 CSS-E003.104 EHM-E001.104 EHM-E002.104 EHM-E003.104 EHM-E004.104 CSS-H001.104 CSS-H002.104 peerlink.104 vni-508', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-csi-v114', 'alias': 'CSISF-VLAN114-CSCorp-Net', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.114 swp31.114 swp32.114 swp33.114 CSS-E004.114 CSS-E005.114 CSS-E006.114 CSS-E007.114 CSS-E001.114 CSS-E002.114 CSS-E003.114 CSI-E001.114 CSI-E002.114 peerlink.114 vni-525', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-csi-v2704', 'alias': 'CSI-DMZ', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'EDG-E001.2704 EDG-E002.2704 CSS-E001.2704 CSS-E002.2704 CSS-E003.2704 peerlink.2704 vni-2704', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-phn-v1007', 'alias': 'CSSSF-PHCN-Net', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.1007 swp31.1007 swp32.1007 swp33.1007 CSS-E004.1007 CSS-E005.1007 CSS-E006.1007 CSS-E007.1007 CSS-E001.1007 CSS-E002.1007 CSS-E003.1007 CSS-H001.1007 CSS-H002.1007 peerlink.1007 vni-519', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-phn-v1102', 'alias': 'PHCN - SFD-iSCSI1', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-iLF01.1102 peerlink.1102 vni-1102', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-phn-v1103', 'alias': 'PHCN - SFD-iSCSI2', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-iLF01.1103 peerlink.1103 vni-1103', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-phn-v120', 'alias': 'PHN-Legacy-Net', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.120 swp31.120 swp32.120 swp33.120 CSS-E004.120 CSS-E005.120 CSS-E006.120 CSS-E007.120 CSS-E001.120 CSS-E002.120 CSS-E003.120 EHM-E001.120 EHM-E002.120 EHM-E003.120 EHM-E004.120 EDG-E001.120 EDG-E002.120 EDG-E003.120 CSS-H001.120 CSS-H002.120 peerlink.120 vni-620', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-mbs-v1006', 'alias': 'MBS-CLD-PBS-Network', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.1006 swp31.1006 swp32.1006 swp33.1006 CSS-E004.1006 CSS-E005.1006 CSS-E006.1006 CSS-E007.1006 CSS-E001.1006 CSS-E002.1006 CSS-E003.1006 peerlink.1006 vni-524', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-mbs-v1000', 'alias': 'CSSShared-MBS-VL1000-CS-Server-Net', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.1000 swp31.1000 swp32.1000 swp33.1000 CSS-E004.1000 CSS-E005.1000 CSS-E006.1000 CSS-E007.1000 CSS-E001.1000 CSS-E002.1000 CSS-E003.1000 CSS-H001.1000 CSS-H002.1000  peerlink.1000 vni-1000', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-mbs-v1002', 'alias': 'CSSShared-MBS-Site-Interconnect', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.1002 swp31.1002 swp32.1002 swp33.1002 CSS-E004.1002 CSS-E005.1002 CSS-E006.1002 CSS-E007.1002 CSS-E001.1002 CSS-E002.1002 CSS-E003.1002 peerlink.1002 vni-1002', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-mbs-v1', 'alias': 'CSSShared-MBS-VL1-Interconnect', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.1 swp31.1 swp32.1 swp33.1 CSS-E004.1 CSS-E005.1 CSS-E006.1 CSS-E007.1 CSS-E001.1 CSS-E002.1 CSS-E003.1 peerlink.1 vni-1003', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-mbs-v4', 'alias': 'CSSSF-VLAN4-MBS-DMZ-Net', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.4 swp31.4 swp32.4 swp33.4 CSS-E004.4 CSS-E005.4 CSS-E006.4 CSS-E007.4 CSS-E001.4 CSS-E002.4 CSS-E003.4 peerlink.4 vni-1004', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-lit-v2902', 'alias': 'LaScala-SFD-iSCSI1', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-iLF01.2902 peerlink.2902 vni-2902', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-lit-v2903', 'alias': 'LaScala-SFD-iSCSI2', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-iLF01.2903 peerlink.2903 vni-2903', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-lit-v2904', 'alias': 'LaScala-BYR-iSCSI1', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-iLF01.2904 peerlink.2904 vni-2904', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-lit-v2905', 'alias': 'LaScala-BYR-iSCSI2', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CS-iLF01.2905 peerlink.2905 vni-2905', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-dmw-v1200', 'alias': 'DoerenMayhew-RR-Backup', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CSS-H001.1200 CSS-H002.1200 peerlink.1200 vni-1200', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-hss-v1201', 'alias': 'Hutchinson-RR-Backup', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'CSS-H001.1201 CSS-H002.1201 peerlink.1201 vni-1201', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-mbp-v1202', 'alias': 'MBPIA-RR-Backup', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.1202 swp31.1202 swp32.1202 swp33.1202 EDG-E001.1202 EDG-E002.1202 EDG-E003.1202 CSS-H001.1202 CSS-H002.1202 peerlink.1202 vni-1202', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-dcp-v102', 'alias': 'Dencap-Network', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.102 swp31.102 swp32.102 swp33.102 CSS-E004.102 CSS-E005.102 CSS-E006.102 CSS-E007.102 CSS-E001.102 CSS-E002.102 CSS-E003.102 CSS-H001.102 CSS-H002.102 peerlink.102 vni-506', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'br-sqh-v1005', 'alias': 'SQH-DR-NET', 'ip_address': '', 'mtu': '', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': 'swp30.1005 swp31.1005 swp32.1005 swp33.1005 CSS-E004.1005 CSS-E005.1005 CSS-E006.1005 CSS-E007.1005 CSS-E001.1005 CSS-E002.1005 CSS-E003.1005 EHM-E001.1005 EHM-E002.1005 EHM-E003.1005 EHM-E004.1005 EDG-E001.1005 EDG-E002.1005 EDG-E003.1005 CSS-H001.1005 CSS-H002.1005 peerlink.1005 vni-523', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '', 'vxlan_local_tunnel_ip_address': '', 'vxlan_remote_ip_address': ''}, {'name': 'vni-1251', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '1251', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-250', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '250', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-501', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '501', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-504', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '504', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-505 ', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '505', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-506', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '506', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-507', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '507', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-508', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '508', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-511', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '511', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-512', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '512', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-513', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '513', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-514', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '514', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-517', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '517', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-519', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '519', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-520', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '520', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-521', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '521', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-522', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '522', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-523', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '523', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-524', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '524', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-525', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '525', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-599', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '599', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-600', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '600', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-602', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '602', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-604', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '604', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-605', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '605', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-620', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '620', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-1000', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '1000', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-1001', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '1001', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-1002', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '1002', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-1003', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '1003', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-1004', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '1004', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-1102', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '1102', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-1103', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '1103', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-1200', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '1200', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-1201', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '1201', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-1202', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '1202', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-1998', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '1998', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-1999', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '1999', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-2577', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '2577', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-2578', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '2578', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-2579', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '2579', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-2511', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '2511', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-2520', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '2520', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-2521', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '2521', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-2522', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '2522', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-2704', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '2704', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-2902', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '2902', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-2903', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '2903', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-2904', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '2904', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}, {'name': 'vni-2905', 'alias': '', 'ip_address': '', 'mtu': '9148', 'link_speed': '', 'bond_slaves': '', 'bridge_access': '', 'bridge_ports': '', 'bond_mode': '', 'bridge_vids': '', 'bridge_vlan_aware': '', 'clag_id': '', 'vrf': '', 'clagd_anycast_ip_address': '', 'gateway_ip_address': '', 'vxlan_id': '2905', 'vxlan_local_tunnel_ip_address': '10.35.0.80', 'vxlan_remote_ip_address': ''}]


def read_yaml_file(filepath):
    """ Read YAML file """

    with open(filepath, 'r') as stream:
        data = yaml.safe_load(stream)

    return data


def get_inventory():

    if os.path.isfile(HOSTS_FILENAME):
        inventory = read_yaml_file(HOSTS_FILENAME)
    else:
        logger.error(f"Cannot find specified inventory file: {HOSTS_FILENAME}")
        raise InventoryFileNotFound

    return inventory


def get_validation_by_hostname(hostname, check):

    validation_filename = os.path.join(VALIDATION_DIR, check + '.yaml')

    if os.path.isfile(HOSTS_FILENAME):
        validation_file = read_yaml_file(validation_filename)
    else:
        logger.error(f"Cannot find validation file: {validation_filename}")
        raise ValidationFileNotFound

    if validation_file.get(hostname):
        return validation_file[hostname]
    else:
        logger.warning(f"Could not find validation rules for {hostname}")


def get_inventory_by_group(group):

    inventory = get_inventory()

    group_inventory = inventory[group]['hosts']

    for k, v in group_inventory.items():
        for _, i in inventory.items():
            if i.get('hosts'):
                ihosts = i['hosts']
                if ihosts.get(k) and isinstance(ihosts.get(k), dict):
                    if ihosts[k].get('ansible_host'):
                        group_inventory[k] = ihosts[k]['ansible_host']

    return group_inventory


def get_hostname_by_ip(ip):
    """ Iterates through the inventory group and gets the first
        hostname which contains a key ansible_host of match IP """

    inventory = get_inventory()
    hostname = None

    for k, v in inventory.items():
        if v.get('hosts'):
            ihosts = v['hosts']
            for k2, v2 in ihosts.items():
                if v2:
                    if v2.get('ansible_host', '') == ip:
                        hostname = k2
                        break

    return hostname


def get_credentials_by_key(key):
    if os.path.isfile(CREDENTIALS_FILENAME):
        credentials = read_yaml_file(CREDENTIALS_FILENAME)
    else:
        logger.error(f"Cannot find specified credentials file: {CREDENTIALS_FILENAME}")
        raise CredentialsFileNotFound

    credentials = credentials[key]

    return {
        'username': credentials['username'],
        'password': credentials['password']
    }


def multithread_command(command, hosts):
    pool = Threadpool(4)
    host_ips = [inventory_hosts[host] for host in hosts]

    def _send_multithread_command(host):
        try:
            device = CumulusDevice(
                hostname=host,
                username=creds['username'],
                password=creds['password']
            )

            result = device.send_command([command])[0]
            result['host'] = host
        except ConnectionError:
            result = None

        return result

    results = pool.map(_send_multithread_command, host_ips)

    pool.close()
    pool.join()

    results = [result for result in results if result]

    return results


def find_hostname_from_ip_address(ip):
    hostname = None

    for k, v in inventory_hosts.items():
        if ip == v:
            hostname = k

    return hostname


def search_interface_configuration(iface, hosts):
    iface = iface.lower()
    interface_search_results = []
    results = multithread_command('show interfaces configuration', hosts)

    for result in results:
        found = False
        iface_config = {}
        hostname = find_hostname_from_ip_address(result['host'])

        for interface in result['output']:
            if interface['name'].lower() == iface:
                found = True
                iface_config.update(interface)

        interface_search_results.append(dict(
            hostname=hostname,
            ip=result['host'],
            configured=found,
            configuration=iface_config
        ))

    return interface_search_results


def search_mac_address(mac, hosts):
    mac = mac.lower()
    mac_search_results = []
    results = multithread_command('show bridge macs', hosts)

    for result in results:
        found = False
        hostname = find_hostname_from_ip_address(result['host'])

        for entry in result['output']:
            if entry['mac'].lower() == mac:
                found = True

        mac_search_results.append(dict(
            hostname=hostname,
            ip=result['host'],
            found=found,
        ))

    return mac_search_results


def check_bgp_neighbors(hosts):
    required_peers = []
    results = multithread_command('show bgp summary', hosts)

    for result in results:
        hostname = get_hostname_by_ip(result['host'])
        required_peers_dict = {'hostname': hostname,'ipv4 unicast': [], 'l2vpn evpn': []}
        bgp_validators = get_validation_by_hostname(hostname, 'bgp')

        # get validators
        for family in ADDRESS_FAMILIES:
            if bgp_validators:
                if bgp_validators.get('bgp_neighbors'):
                    if bgp_validators['bgp_neighbors'].get(family):
                        if bgp_validators['bgp_neighbors'][family].get('peers'):
                            for i, h in bgp_validators['bgp_neighbors'][family]['peers'].items():
                                required_peers_dict[family].append({
                                    'interface': i,
                                    'peer_hostname': h,
                                    'found': False,
                                    'established': False

                            })

        # get current state
        for family in ADDRESS_FAMILIES:
            if result.get('output'):
                if result['output'][family]:
                    if result['output'][family].get('peers'):
                        for interface, details in result['output'][family]['peers'].items():
                            for required_peer in required_peers_dict[family]:
                                if details.get('hostname'):
                                    if interface.upper() == required_peer['interface'].upper() and \
                                            details['hostname'].upper() == required_peer['peer_hostname'].upper():
                                        required_peer['found'] = True
                                        if details['state'].upper() == 'ESTABLISHED':
                                            required_peer['established'] = True
                                        break

        required_peers.append(required_peers_dict)

    return required_peers


def check_clag(hosts):
    #results = [{'command': 'show clag', 'output': {'clagIntfs': {'CS-EDGSW': {'clagId': 202, 'operstate': 'up', 'peerIf': 'CS-EDGSW', 'status': 'dual'}, 'CS-MGT': {'clagId': 203, 'operstate': 'up', 'peerIf': 'CS-MGT', 'status': 'dual'}, 'CS-iLF01': {'clagId': 201, 'operstate': 'up', 'peerIf': 'CS-iLF01', 'status': 'dual'}, 'KFG-H001': {'clagId': 119, 'operstate': 'up', 'peerIf': 'KFG-H001', 'status': 'dual'}, 'vni-1000': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-1000', 'status': 'dual'}, 'vni-1001': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-1001', 'status': 'dual'}, 'vni-1002': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-1002', 'status': 'dual'}, 'vni-1003': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-1003', 'status': 'dual'}, 'vni-1004': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-1004', 'status': 'dual'}, 'vni-1102': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-1102', 'status': 'dual'}, 'vni-1103': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-1103', 'status': 'dual'}, 'vni-1200': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-1200', 'status': 'dual'}, 'vni-1201': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-1201', 'status': 'dual'}, 'vni-1202': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-1202', 'status': 'dual'}, 'vni-1210': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-1210', 'status': 'dual'}, 'vni-1251': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-1251', 'status': 'dual'}, 'vni-1402': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-1402', 'status': 'dual'}, 'vni-1998': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-1998', 'status': 'dual'}, 'vni-1999': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-1999', 'status': 'dual'}, 'vni-250': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-250', 'status': 'dual'}, 'vni-2511': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-2511', 'status': 'dual'}, 'vni-2520': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-2520', 'status': 'dual'}, 'vni-2521': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-2521', 'status': 'dual'}, 'vni-2522': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-2522', 'status': 'dual'}, 'vni-2577': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-2577', 'status': 'dual'}, 'vni-2578': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-2578', 'status': 'dual'}, 'vni-2579': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-2579', 'status': 'dual'}, 'vni-2702': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-2702', 'status': 'dual'}, 'vni-2704': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-2704', 'status': 'dual'}, 'vni-2902': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-2902', 'status': 'dual'}, 'vni-2903': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-2903', 'status': 'dual'}, 'vni-2904': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-2904', 'status': 'dual'}, 'vni-2905': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-2905', 'status': 'dual'}, 'vni-501': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-501', 'status': 'dual'}, 'vni-504': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-504', 'status': 'dual'}, 'vni-505': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-505', 'status': 'dual'}, 'vni-506': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-506', 'status': 'dual'}, 'vni-507': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-507', 'status': 'dual'}, 'vni-508': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-508', 'status': 'dual'}, 'vni-511': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-511', 'status': 'dual'}, 'vni-512': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-512', 'status': 'dual'}, 'vni-513': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-513', 'status': 'dual'}, 'vni-514': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-514', 'status': 'dual'}, 'vni-517': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-517', 'status': 'dual'}, 'vni-519': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-519', 'status': 'dual'}, 'vni-520': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-520', 'status': 'dual'}, 'vni-521': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-521', 'status': 'dual'}, 'vni-522': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-522', 'status': 'dual'}, 'vni-523': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-523', 'status': 'dual'}, 'vni-524': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-524', 'status': 'dual'}, 'vni-525': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-525', 'status': 'dual'}, 'vni-599': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-599', 'status': 'dual'}, 'vni-600': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-600', 'status': 'dual'}, 'vni-602': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-602', 'status': 'dual'}, 'vni-604': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-604', 'status': 'dual'}, 'vni-605': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-605', 'status': 'dual'}, 'vni-620': {'clagId': 0, 'operstate': 'up', 'peerIf': 'vni-620', 'status': 'dual'}}, 'status': {'backupActive': True, 'backupIp': '10.30.20.81', 'backupReason': '', 'backupVrf': 'mgmt', 'linklocal': False, 'ourId': '98:03:9b:f0:c7:9c', 'ourPriority': 1000, 'ourRole': 'primary', 'peerAlive': False, 'peerId': '98:03:9b:f2:cd:9c', 'peerIf': 'peerlink.4094', 'peerIp': '169.254.255.2', 'peerPriority': 2000, 'peerRole': 'secondary', 'sysMac': '44:38:39:ff:01:30', 'vxlanAnycast': '10.35.0.180'}}, 'host': '10.30.20.80'}]
    #hosts = ['SFD-C319-SPN-SN2700-01', 'SFD-C320-BLF-S4048-01', ]
    results = multithread_command('show clag', hosts)

    down_peers = []
    tr = {
        'hostname': [],
        'status': [],
        'role': [],
        'vxlan anycast ip': [],
        'backup active': [],
        'backup IP': []
    }

    for entry in results:
        hostname = get_hostname_by_ip(entry['host'])
        tr['hostname'].append(hostname)

        ce = {
            'hostname': '',
            'alive': '',
            'role': '',
            'vxlan anycast ip': '',
            'backup active': '',
            'backup IP': ''
        }

        if entry['output']:
            alive = entry['output']['status']['peerAlive']
            role = entry['output']['status']['ourRole']
            vxlan_anycast_ip = entry['output']['status'].get('vxlanAnycast', 'not configured')
            backup_active = entry['output']['status'].get('backupActive', 'not configured')
            backup_ip = vxlan_anycast_ip = entry['output']['status'].get('backupIp', 'not configured')

            ce['hostname'] = hostname
            ce['alive'] = alive
            ce['role'] = role
            ce['vxlan anycast ip'] = vxlan_anycast_ip
            ce['backup active'] = backup_active
            ce['backup IP'] = backup_ip

            tr['role'].append(role)
            tr['vxlan anycast ip'].append(vxlan_anycast_ip)

            if alive:
                tr['status'].append('up')
            else:
                tr['status'].append(bcolors.FAIL + 'down' + bcolors.ENDC)
                down_peers.append(ce)
        else:
            ce['hostname'] = hostname
            ce['alive'] = 'not configured'
            ce['role'] = '-'
            ce['vxlan anycast ip'] = 'not configured'
            ce['backup active'] = 'not configured'
            ce['backup IP'] = 'not configured'
            down_peers.append(ce)

            tr['status'].append('not configured')
            tr['role'].append('-')
            tr['vxlan anycast ip'].append('not configured')
            tr['backup active'].append('not configured')
            tr['backup IP'].append('not configured')


    tabulated_table = tabulate(tr,
                               headers="keys", tablefmt="simple")

    return dict(
        down_peers=down_peers,
        tabulated_table=tabulated_table
    )


def cumulus_interface_to_ansible_vars(interfaces):
    """ This takes in json/dict data and converts it to yaml
        For use with Ansible vars """

    ansible_structure = {
        'switchports': {},
        'bridges': {},
        'bonds': {},
        'vlans': {},
        'vnis': {}
    }

    # classify interfaces into their respective types
    # then create yaml structure
    for interface in interfaces:
        if interface.get('bridge_ports'):
            name = interface.pop('name')
            ansible_structure['bridges'][name] = interface
            for port in interface['bridge_ports']:
                if port.lower().startswith('vni-'):
                    vni = int(port.split('vni-')[1])
                    break
            # find vlan iterating through ports for <interface>.<vlan>
            for port in interface['bridge_ports']:
                if '.' in port:
                    vlan = int(port.split('.')[1])
                    ansible_structure['bridges'][name]['vlan_id'] = vlan
                    ansible_structure['vlans'].update({vlan: {'vni': vni}})
                    break
            interface['bridge_ports'] = \
                [port.split('.')[0] for port in interface['bridge_ports']]
        elif interface.get('bond_mode') or interface.get('bond_slaves'):
            name = interface.pop('name')
            ansible_structure['bonds'][name] = interface
        elif interface.get('vxlan_id'):
            name = interface.pop('name')
            ansible_structure['vnis'][name] = interface
        else:
            name = interface.pop('name')
            ansible_structure['switchports'][name] = interface

    return ansible_structure


def gen_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='Arguments', dest='cumulus_crawler')
    subparser_search = subparsers.add_parser('search', help='Search')
    subparser_check = subparsers.add_parser('check', help='Check Status, such as BGP')
    mgroup_search = subparser_search.add_mutually_exclusive_group(required=True)
    #mgroup_check = subparser_check.add_mutually_exclusive_group(required=True)
    mgroup_search.add_argument("-m", "--mac", help="Search MAC address", dest='mac')
    mgroup_search.add_argument("-i", "--iface", help="Search Interface", dest='iface')
    subparser_check.add_argument("-b", "--bgp", help="Check BGP", dest='check_bgp', action='store_true')
    subparser_check.add_argument("-c", "--clag", help="Check CLAG", dest='check_clag', action='store_true')
    subparser_check.add_argument("-v", "--verbose", help="Verbose output", dest='verbose', action='store_true')

    return parser.parse_args()


if __name__ == '__main__':
    # get host inventory
    inventory_hosts = get_inventory_by_group(VENDOR)
    creds = get_credentials_by_key(VENDOR)
    hosts = [host for host in inventory_hosts][0:1]

    # device = CumulusDevice(
    #     hostname=inventory_hosts['CSS1A-106-LEF-01'],
    #     #hostname=inventory_hosts['CSS1A-106-LEF-01'],
    #     username=creds['username'],
    #     password=creds['password']
    # )

    # interfaces = device.show_interfaces_configuration()
    # print(yaml.dump(cumulus_interface_to_ansible_vars(interfaces), indent=2))
    #device.show_interfaces_status()

    # r = search_mac_address('5c:f9:dd:ef:ab:82', hosts)
    # print(r)
    #

    args = gen_args()

    if not args.cumulus_crawler:
        print("type --help for help with this command.")
    else:
        if args.cumulus_crawler == 'search':
            if args.mac:
                results = search_mac_address(args.mac, hosts)
                print('\n')
                tabulated_results = {}

                for entry in results:
                    for k, v in entry.items():
                        k = k.upper()
                        if not tabulated_results.get(k):
                            tabulated_results[k] = []
                        tabulated_results[k].append(v)

                if tabulated_results:
                    if tabulated_results.get('FOUND'):
                        found_with_bcolor = []
                        for i in tabulated_results['FOUND']:
                            if i:
                                found_with_bcolor.append(bcolors.OKBLUE +
                                                         "Yes" + bcolors.ENDC)
                            else:
                                found_with_bcolor.append(bcolors.FAIL +
                                                         "No" + bcolors.ENDC)

                        tabulated_results['FOUND'] = found_with_bcolor

                    tabulated_results = tabulate(tabulated_results,
                                                 headers="keys", tablefmt="fancy_grid")
                    print(tabulated_results)

            elif args.iface:
                results = search_interface_configuration(args.iface, hosts)
                print(results)
        elif args.cumulus_crawler == 'check':
            if args.check_bgp:
                #results = check_bgp_neighbors(['CSS1A-109-LEF-03', 'CSS1A-109-LEF-04'])
                results = check_bgp_neighbors(inventory_hosts)
                down_peers = []
                tabulated_results = None
                tr = {
                    'hostname': [],
                    'address family': [],
                    'interface': [],
                    'peer hostname': [],
                    'configured': [],
                    'status': []
                }

                for entry in results:
                    hostname = entry['hostname']

                    for family in ADDRESS_FAMILIES:
                        for peer in entry[family]:
                            peer['hostname'] = hostname
                            tr['hostname'].append(hostname)
                            tr['address family'].append(family)
                            tr['interface'].append(peer['interface'])
                            tr['peer hostname'].append(peer['peer_hostname'])

                            if peer['found']:
                                tr['configured'].append('yes')
                            else:
                                down_peers.append(peer)
                                tr['configured'].append(bcolors.FAIL + 'no' + bcolors.ENDC)

                            if peer['established']:
                                tr['status'].append('Established')
                            else:
                                down_peers.append(peer)
                                tr['status'].append(bcolors.FAIL + 'Not Established' + bcolors.ENDC)

                tabulated_table = tabulate(tr,
                                             headers="keys", tablefmt="simple")

                if args.verbose:
                    print('\n', tabulated_table)
                    print('\n')
                else:
                    if not down_peers:
                        print("\n", f"{bcolors.OKBLUE} --> All BGP neighbors established! {bcolors.ENDC} \n")
                    else:
                        for peer in down_peers:
                            if not peer['found']:
                                reason = "is not configured"
                            elif not peer['established']:
                                reason = "peering is not established"
                            print("\n", f"{bcolors.FAIL} --> {peer['hostname']}'s required peer "
                            f"on interface {peer['interface']} "
                            f"to {peer['peer_hostname']} failed check because \n {' ' * 4} {reason}. {bcolors.ENDC}", "\n")

            elif args.check_clag:
                clag_status = check_clag(inventory_hosts)

                if args.verbose:
                    print("\n", clag_status['tabulated_table'])
                else:
                    if clag_status['down_peers']:
                        for dp in clag_status['down_peers']:
                            print("\n", f"{bcolors.FAIL} --> {dp['hostname']} failed check because system clag (mlag) is down. "
                                  f"The VXLAN Anycast IP is: {dp['vxlan anycast ip']} {bcolors.ENDC}", "\n")
                        print("\n")




            else:
                print("Please enter argument. Use -h for help.")