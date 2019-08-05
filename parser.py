import paramiko
import json
import logging.config
import argparse
import os
import yaml
from utils import parse_output
from paramiko import ssh_exception as pexception
from exceptions import *
from multiprocessing .dummy import Pool as Threadpool


HOSTS_FILENAME = 'hosts.yaml'
CREDENTIALS_FILENAME = 'credentials.yaml'
PLATFORM = 'cumulus_clos'
VENDOR = 'cumulus'
WAIT_FOR_COMMAND_IN_SECONDS = 4
TEMPLATE_DIR = './templates/'

# logging
ERROR_FORMAT = "%(levelname)s at %(asctime)s in %(funcName)s in %(filename) at line %(lineno)d: %(message)s"
DEBUG_FORMAT = "%(lineno)d in %(filename)s at %(asctime)s: %(message)s"
LOG_CONFIG = {'version': 1,
              'formatters': {'error': {'format': ERROR_FORMAT},
                            'debug': {'format': DEBUG_FORMAT}},
              'handlers': {'console': {'class': 'logging.StreamHandler',
                                     'formatter':  'debug',
                                     'level': logging.DEBUG},
                          'file': {'class': 'logging.FileHandler',
                                  'filename': 'errors.log',
                                  'formatter': 'error',
                                  'level': logging.ERROR}},
              'root': {'handlers': ('console', 'file'), 'level': 'ERROR'}}

logging.config.dictConfig(LOG_CONFIG)
logger = logging.getLogger(__name__)


def _get_inventory():

    if os.path.isfile(HOSTS_FILENAME):
        inventory = read_yaml_file(HOSTS_FILENAME)
    else:
        logger.error(f"Cannot find specified inventory file: {HOSTS_FILENAME}")
        raise InventoryFileNotFound

    return inventory


def read_yaml_file(filepath):
    """ Read YAML file """

    with open(filepath, 'r') as stream:
        data = yaml.safe_load(stream)

    return data


def get_inventory_by_group(group):
    inventory = _get_inventory()
    group_inventory = inventory[group]['hosts']

    for k, v in group_inventory.items():
        for _, i in inventory.items():
            if i.get('hosts'):
                caw = i['hosts']
                if caw.get(k) and isinstance(caw.get(k), dict):
                    if caw[k].get('ansible_host'):
                        group_inventory[k] = caw[k]['ansible_host']

    return group_inventory


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
        device = CumulusConnection(
            hostname=host,
            username=creds['username'],
            password=creds['password']
        )

        results = device.send_command([command])[0]
        results['host'] = host

        return results

    results = pool.map(_send_multithread_command, host_ips)

    pool.close()
    pool.join()

    return results


def find_hostname_from_ip_address(ip):
    hostname = None

    for k, v in inventory_hosts.items():
        if ip == v:
            hostname = k

    return hostname


def check_interface_configuration(iface, hosts):
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


def check_mac_address(mac, hosts):
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


def gen_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='Arguments', dest='cumulus_crawler')
    subparser_search = subparsers.add_parser('search', help='Search')

    mgroup_search = subparser_search.add_mutually_exclusive_group(required=True)
    mgroup_search.add_argument("-m", "--mac", help="Search MAC address", dest='mac')
    mgroup_search.add_argument("-i", "--iface", help="Search Interface", dest='iface')

    return parser.parse_args()


class CumulusConnection(object):
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.session = None

    def _open_connection(self):

        try:
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(
                               hostname=self.hostname,
                               username=self.username,
                               password=self.password,
                               look_for_keys=False,
                               allow_agent=False, timeout=5)

            #print("SSH connection established to {0}".format(self.hostname))
            logger.info(f"SSH Connection established to {self.hostname}")
            self.session = ssh_client

        except (pexception.BadHostKeyException,
                pexception.AuthenticationException,
                pexception.SSHException,
                pexception.socket.error) as e:
            logger.error(e)

        return

    def _close_connection(self):
        self.session.close()
        self.session = None
        logger.info(f"SSH Connection closed for {self.hostname}")

        return

    def send_command(self, command):
        """Wrapper for self.device.send.command()."""
        output = []
        sb = bool

        if isinstance(command, str):
            if not self.session:
                sb = False
                self._open_connection()

            _, stdout, stderr = self.session.exec_command(command, timeout=10)
            output.append({
                'command': command,
                'output': stdout.read().decode('utf-8')
            })
        elif isinstance(command, list):
            commands = command
            output = self._send_commands(commands)

        if not sb:
            self._close_connection()

        return output

    def _send_commands(self, commands):
        output = []
        self._open_connection()

        for command in commands:
            cmd_output = self._get_func(command)

            output.append({
                'command': command,
                'output': cmd_output
            })

        self._close_connection()

        return output

    def show_version(self, from_json=True):
        command = 'net show version'

        if from_json:
            output = self.send_command(command + ' ' + 'json')[0]['output']
            structured_output = json.loads(output)
        else:
            output = self.send_command(command)[0]['output']
            structured_output = parse_output(
                template_dir=TEMPLATE_DIR,
                command=command,
                platform=PLATFORM,
                data=output)[0]

        return structured_output

    def show_bridge_macs(self, state='dynamic', from_json=False):
        """ Get bridge macs from Device. Currently it seems like json output
        does not return VLAN ID. So default from_json will be set to False here """
        state = state.lower()
        command = f"net show bridge macs {state}"

        if from_json:
            output = self.send_command(command + ' ' + 'json')[0]['output']
            structured_output = json.loads(output)

        else:
            output = self.send_command(command)[0]['output']
            structured_output = parse_output(
                template_dir=TEMPLATE_DIR,
                command=command,
                platform=PLATFORM,
                data=output)

        return structured_output

    def show_interfaces_configuration(self, filter='all'):
        output = self.send_command("cat /etc/network/interfaces")[0]['output']
        filter = filter.lower()
        interfaces = []
        vnis = []
        structured_output = parse_output(
            template_dir=TEMPLATE_DIR,
            command="show interfaces configuration",
            platform=PLATFORM,
            data=output)

        for entry in structured_output:
            iface = {}
            for k, v in entry.items():
                if v:
                    iface[k] = v
            interfaces.append(iface)

            if iface.get('vxlan_id'):
                vnis.append(iface)

        if filter == 'vni':
            interfaces = vnis

        return interfaces

    def _get_func(self, name):
        """ Get Functions Dynamically """
        name = name.lower()
        if 'net' in name:
            name = name.split('net')[1].strip()
        name = name.replace(' ', '_')
        func = getattr(self, name, None)

        if not func:
            self._close_connection()
            logger.error(f"Command {name} is not supported")
            raise CommandNotSupported

        return func()


if __name__ == '__main__':
    # get host inventory
    inventory_hosts = get_inventory_by_group(VENDOR)
    creds = get_credentials_by_key(VENDOR)

    #hosts = ["CSS1A-106-LEF-01", "CSS1A-106-LEF-02"]
    hosts = [host for host in inventory_hosts][0:5]
    #hosts = [host for host in inventory_hosts]
    # print(hosts)
    #
    #
    # # results = check_interface_configuration('vni-1251', hosts)
    # # print(results)
    #
    # results = check_mac_address("00:50:56:9e:2b:c4", hosts)
    # print(results)

    args = gen_args()

    if not args.cumulus_crawler:
        print("type --help for help with this command.")
    else:
        if args.cumulus_crawler == 'search':
            if args.mac:
                results = check_mac_address(args.mac, hosts)
                for result in results:
                    print(f"{result['hostname']} - Mac Found: {result['found']}")
            elif args.iface:
                results = check_interface_configuration(args.iface, hosts)
                print(results)





    #results = multithread_command('show interfaces configuration', hosts)

    # results = [{'command': 'show interfaces configuration', 'output': [{'name': 'lo inet loopback', 'ip_address': '10.35.0.80/32', 'clagd_anycast_ip_address': '10.35.0.180'}, {'name': 'eth0', 'alias': 'MGMT-to-CSS1A-106-MGT-01 - 10274', 'ip_address': '10.30.20.80/24', 'vrf': 'mgmt', 'gateway_ip_address': '10.30.20.1'}, {'name': 'swp1', 'mtu': '9216'}, {'name': 'swp2', 'mtu': '9216'}, {'name': 'swp3', 'mtu': '9216'}, {'name': 'swp4', 'mtu': '9216'}, {'name': 'swp5', 'mtu': '9216'}, {'name': 'swp6', 'mtu': '9216'}, {'name': 'swp7', 'mtu': '9216'}, {'name': 'swp8', 'mtu': '9216'}, {'name': 'swp9', 'mtu': '9216'}, {'name': 'swp10', 'mtu': '9216'}, {'name': 'swp11', 'mtu': '9216'}, {'name': 'swp12', 'mtu': '9216'}, {'name': 'swp13', 'mtu': '9216'}, {'name': 'swp14', 'mtu': '9216'}, {'name': 'swp15 ', 'mtu': '9216'}, {'name': 'swp30', 'alias': 'BLD01-13', 'mtu': '9216'}, {'name': 'swp31', 'alias': 'BLD01-14', 'mtu': '9216'}, {'name': 'swp32', 'alias': 'BLD01-16', 'mtu': '9216'}, {'name': 'swp33', 'alias': 'BLD02-01', 'mtu': '9216'}, {'name': 'swp16', 'mtu': '9216'}, {'name': 'swp42', 'alias': 'KFG 52607 Replication', 'mtu': '9216'}, {'name': 'swp48', 'alias': 'Uplink to CSS1A-106-MGMT-01', 'mtu': '9216'}, {'name': 'mgmt', 'ip_address': '127.0.0.1/8'}, {'name': 'swp46', 'alias': 'Uplink-to-CSS1A-105-EDG-01 - 10019', 'mtu': '9216'}, {'name': 'swp47', 'alias': 'Uplink-to-CSS1A-107-iSC-01 - 10245', 'mtu': '9216'}, {'name': 'swp49', 'alias': 'Uplink-to-CSS1A-105-SPN-01 - 10216', 'mtu': '9216'}, {'name': 'swp50', 'alias': 'Uplink-to-CSS1A-105-SPN-02 - 10217', 'mtu': '9216'}, {'name': 'swp55', 'alias': 'Peerlink - CSS1A-108-LEF-02 - 10232', 'mtu': '9216'}, {'name': 'swp56', 'alias': 'Peerlink - CSS1A-108-LEF-02 - 10238', 'mtu': '9216'}, {'name': 'br-native', 'bridge_ports': 'peerlink'}, {'name': 'peerlink', 'mtu': '9216', 'bond_slaves': 'swp55 swp56'}, {'name': 'peerlink.4094', 'ip_address': '169.254.255.1/30'}, {'name': 'CSS-E004', 'alias': 'CSS1A-ESXI004 - 10059', 'mtu': '9216', 'bond_slaves': 'swp1'}, {'name': 'CSS-E005', 'alias': 'CSS1A-ESXI005 - 10046', 'mtu': '9216', 'bond_slaves': 'swp2'}, {'name': 'CSS-E006', 'alias': 'CSS1A-ESXI006 - 10041', 'mtu': '9216', 'bond_slaves': 'swp3'}, {'name': 'CSS-E007', 'alias': 'CSS1A-ESXI007 - 10039', 'mtu': '9216', 'bond_slaves': 'swp4'}, {'name': 'CSS-E001', 'alias': 'CSS1A-ESXI001 - 10151', 'mtu': '9216', 'bond_slaves': 'swp5'}, {'name': 'CSS-E002', 'alias': 'CSS1A-ESXI002 - 10152', 'mtu': '9216', 'bond_slaves': 'swp6'}, {'name': 'CSS-E003', 'alias': 'CSS1A-ESXI003 - 10058', 'mtu': '9216', 'bond_slaves': 'swp7'}, {'name': 'EHM-E001', 'alias': 'EHM1A-ESXI001 - 10111 ', 'mtu': '9216', 'bond_slaves': 'swp8'}, {'name': 'EHM-E002', 'alias': 'EHM1A-ESXI002 - 10046', 'mtu': '9216', 'bond_slaves': 'swp9'}, {'name': 'EHM-E003', 'alias': 'EHM1A-ESXI003 - 10016', 'mtu': '9216', 'bond_slaves': 'swp10'}, {'name': 'EHM-E004', 'alias': 'EHM1A-ESXI004 - 10056', 'mtu': '9216', 'bond_slaves': 'swp11'}, {'name': 'EDG-E001', 'alias': 'EDG1A-ESXI001 - 10051', 'mtu': '9216', 'bond_slaves': 'swp12'}, {'name': 'EDG-E002', 'alias': 'EDG1A-ESXI002 - 10068', 'mtu': '9216', 'bond_slaves': 'swp13'}, {'name': 'EDG-E003', 'alias': 'EDG1A-ESXI003 - 10055', 'mtu': '9216', 'bond_slaves': 'swp14'}, {'name': 'CSS-H001', 'alias': 'CSS1A-HYPV001', 'mtu': '9216', 'bond_slaves': 'swp15'}, {'name': 'CSS-H002', 'alias': 'CSS1A-HYPV002', 'mtu': '9216', 'bond_slaves': 'swp16'}, {'name': 'CSI-E001', 'alias': 'CSS1A-ESXI001', 'mtu': '9216', 'bond_slaves': 'swp17'}, {'name': 'CSI-E002', 'alias': 'CSS1A-ESXI002', 'mtu': '9216', 'bond_slaves': 'swp18'}, {'name': 'KFG-H001', 'alias': 'KFG1A-HV001', 'mtu': '9216', 'bond_slaves': 'swp19', 'clag_id': '119'}, {'name': 'CSS-020', 'alias': 'UNUSED', 'mtu': '9216', 'bond_slaves': 'swp20'}, {'name': 'CSS-021', 'alias': 'UNUSED', 'mtu': '9216', 'bond_slaves': 'swp21'}, {'name': 'CSS-022', 'alias': 'UNUSED', 'mtu': '9216', 'bond_slaves': 'swp22'}, {'name': 'CSS-023', 'alias': 'UNUSED', 'mtu': '9216', 'bond_slaves': 'swp23'}, {'name': 'CSS-024', 'alias': 'UNUSED', 'mtu': '9216', 'bond_slaves': 'swp24'}, {'name': 'CS-iLF01', 'alias': 'CSS1A-107-iSC-01 - 10245', 'mtu': '9216', 'bond_slaves': 'swp47', 'clag_id': '201'}, {'name': 'CS-EDGSW', 'alias': 'CSS1A-105-EDG-01 - 10019 ', 'mtu': '9216', 'bond_slaves': 'swp46', 'clag_id': '202'}, {'name': 'CS-MGT', 'alias': 'uplink to MGT-01 and MGT-02 switches', 'mtu': '9216', 'bond_slaves': 'swp48', 'clag_id': '203'}, {'name': 'br-def-v15', 'alias': 'CSSSF-VLAN15-02-MGMT', 'bridge_ports': 'swp30.15 swp31.15 swp32.15 swp33.15 CSS-E004.15 CSS-E005.15 CSS-E006.15 CSS-E007.15 CSS-E001.15 CSS-E002.15 CSS-E003.15 EHM-E001.15 EHM-E002.15 EHM-E003.15 EHM-E004.15 EDG-E001.15 EDG-E002.15 EDG-E003.15 CSS-H001.15 CSS-H002.15 peerlink.15 vni-501'}, {'name': 'br-def-v205', 'alias': 'CSSSF-DMZ-NET', 'bridge_ports': 'swp30.205 swp31.205 swp32.205 swp33.205 EDG-E001.205 EDG-E002.205 EDG-E003.205 peerlink.205 vni-522'}, {'name': 'br-def-v1251', 'alias': 'CSS-FIREWALL-NET', 'bridge_ports': 'CSS-E004.1251 CSS-E005.1251 CSS-E006.1251 CSS-E007.1251 CSS-E001.1251 CSS-E002.1251 CSS-E003.1251 EHM-E001.1251 EHM-E002.1251 EHM-E003.1251 EHM-E004.1251 EDG-E001.1251 EDG-E002.1251 EDG-E003.1251 peerlink.1251 vni-1251'}, {'name': 'br-kfg-v230', 'alias': 'KFG-VLAN230', 'bridge_ports': 'swp42 KFG-H001 CS-iLF01.230 peerlink.230 vni-1001'}, {'name': 'br-def-v1998', 'alias': 'BGP-01-124', 'bridge_ports': 'CS-EDGSW.1998 peerlink.1998 vni-1998'}, {'name': 'br-def-v1999', 'alias': 'BGP-LaScala', 'bridge_ports': 'CS-EDGSW.1999 peerlink.1999 vni-1999'}, {'name': 'br-def-v2511', 'alias': 'CS-ESXI-VMOTION', 'bridge_ports': 'CSS-E004.2511 CSS-E005.2511 CSS-E006.2511 CSS-E007.2511 CSS-E001.2511 CSS-E002.2511 CSS-E003.2511 EHM-E001.2511 EHM-E002.2511 EHM-E003.2511 EHM-E004.2511 EDG-E001.2511 EDG-E002.2511 EDG-E003.2511 CSS-H001.2511 CSS-H002.2511 CSI-E001.2511 CSI-E002.2511 peerlink.2511 vni-2511'}, {'name': 'br-def-v2520', 'alias': 'CS-OOB-SWITCH-MGMT', 'bridge_ports': 'CS-MGT.2520 peerlink.2520 vni-2520'}, {'name': 'br-def-v2521', 'alias': 'CS-iDRAC-MGMT', 'bridge_ports': 'CS-MGT.2521 peerlink.2521 vni-2521'}, {'name': 'br-def-v2522', 'alias': 'CS-SAN-MGMT', 'bridge_ports': 'CS-MGT.2522 peerlink.2522 vni-2522'}, {'name': 'br-def-v2577', 'alias': 'CSS-iSCSI-01', 'bridge_ports': 'CS-iLF01.2577 peerlink.2577 vni-2577'}, {'name': 'br-def-v2578', 'alias': 'CSS-iSCSI-02', 'bridge_ports': 'CS-iLF01.2578 peerlink.2578 vni-2578'}, {'name': 'br-def-v2579', 'alias': 'CSS-iSCSI-REPL', 'bridge_ports': 'CS-iLF01.2579 peerlink.2579 vni-2579'}, {'name': 'br-def-v150', 'alias': 'CSSBC-O2-Net', 'bridge_ports': 'swp30.150 swp31.150 swp32.150 swp33.150 CSS-E004.150 CSS-E005.150 CSS-E006.150 CSS-E007.150 CSS-E001.150 CSS-E002.150 CSS-E003.150 EHM-E001.150 EHM-E002.150 EHM-E003.150 EHM-E004.150 EDG-E001.150 EDG-E002.150 EDG-E003.150 CSS-H001.150 CSS-H002.150 peerlink.150 vni-600'}, {'name': 'br-def-v253', 'alias': 'CSSSF-KMS-NET', 'bridge_ports': 'CSS-E004.253 CSS-E005.253 CSS-E006.253 CSS-E007.253 CSS-E001.253 CSS-E002.253 CSS-E003.253 EHM-E001.253 EHM-E002.253 EHM-E003.253 EHM-E004.253 EDG-E001.253 EDG-E002.253 EDG-E003.253 CSS-H001.253 CSS-H002.253 peerlink.253 vni-520'}, {'name': 'br-def-v599', 'alias': 'CSS-SSL-VPN-Clients', 'bridge_ports': 'CSS-E004.599 CSS-E005.599 CSS-E006.599 CSS-E007.599 CSS-E001.599 CSS-E002.599 CSS-E003.599 EHM-E001.599 EHM-E002.599 EHM-E003.599 EHM-E004.599 EDG-E001.599 EDG-E002.599 EDG-E003.599 CSS-H001.599 CSS-H002.599 peerlink.599 vni-599'}, {'name': 'br-def-v201', 'alias': 'CSSBC-KMS-NET', 'bridge_ports': 'CS-MGT.201 peerlink.201 vni-512'}, {'name': 'br-def-v12', 'alias': 'CSSBC-ESXiMGMT', 'bridge_ports': 'swp30.12 swp31.12 swp32.12 swp33.12 peerlink.12 vni-602'}, {'name': 'br-def-v174', 'alias': 'CSSBC-iSCSI-01', 'bridge_ports': 'CS-iLF01.174 peerlink.174 vni-604'}, {'name': 'br-def-v175', 'alias': 'CSSBC-iSCSI-02', 'bridge_ports': 'CS-iLF01.175 peerlink.175 vni-605'}, {'name': 'br-def-v250', 'alias': 'CSSSF-FWAL-NET', 'bridge_ports': 'EDG-E001.250 EDG-E002.250 EDG-E003.250 peerlink.250 vni-250'}, {'name': 'br-ehm-v100', 'alias': 'CSSSF-VLAN100-EHM-Servers', 'bridge_ports': 'swp30.100 swp31.100 swp32.100 swp33.100 EHM-E001.100 EHM-E002.100 EHM-E003.100 EHM-E004.100 CSS-H001.100 CSS-H002.100 peerlink.100 vni-504'}, {'name': 'br-ehm-v1004', 'alias': 'EHM-VDI-NET', 'bridge_ports': 'swp30.1004 swp31.1004 swp32.1004 swp33.1004 CSS-E004.1004 CSS-E005.1004 CSS-E006.1004 CSS-E007.1004 CSS-E001.1004 CSS-E002.1004 CSS-E003.1004 EHM-E001.1004 EHM-E002.1004 EHM-E003.1004 EHM-E004.1004 EDG-E001.1004 EDG-E002.1004 EDG-E003.1004 CSS-H001.1004 CSS-H002.1004 peerlink.1004 vni-514'}, {'name': 'br-ult-v101', 'alias': 'CSSSF-VLAN101-Ultralevel-Net', 'bridge_ports': 'swp30.101 swp31.101 swp32.101 swp33.101 CSS-E004.101 CSS-E005.101 CSS-E006.101 CSS-E007.101 CSS-E001.101 CSS-E002.101 CSS-E003.101 CSS-H001.101 CSS-H002.101 peerlink.101 vni-505'}, {'name': 'br-ara-v103', 'alias': 'CSSSF-VLAN103-ARAS-NET', 'bridge_ports': 'swp30.103 swp31.103 swp32.103 swp33.103 CSS-E004.103 CSS-E005.103 CSS-E006.103 CSS-E007.103 CSS-E001.103 CSS-E002.103 CSS-E003.103 CSS-H001.103 CSS-H002.103 peerlink.103 vni-507'}, {'name': 'br-ara-v107', 'alias': 'CSSSF-VLAN107-Aras2-Net', 'bridge_ports': 'swp30.107 swp31.107 swp32.107 swp33.107 CSS-E004.107 CSS-E005.107 CSS-E006.107 CSS-E007.107 CSS-E001.107 CSS-E002.107 CSS-E003.107 peerlink.107 vni-517'}, {'name': 'br-ara-v113', 'alias': 'CSSSF-Aras-Physical-Net', 'bridge_ports': 'swp30.113 swp31.113 swp32.113 swp33.113 CSS-E004.113 CSS-E005.113 CSS-E006.113 CSS-E007.113 CSS-E001.113 CSS-E002.113 CSS-E003.113 peerlink.113 vni-521'}, {'name': 'br-ara-v200', 'alias': 'ARA-DMZ-NET', 'bridge_ports': 'swp30.200 swp31.200 swp32.200 swp33.200 CSS-E004.200 CSS-E005.200 CSS-E006.200 CSS-E007.200 CSS-E001.200 CSS-E002.200 CSS-E003.200 EHM-E001.200 EHM-E002.200 EHM-E003.200 EHM-E004.200 EDG-E001.200 EDG-E002.200 EDG-E003.200 CSS-H001.200 CSS-H002.200 peerlink.200 vni-511'}, {'name': 'br-ara-v1003', 'alias': 'ARA-DR-NET', 'bridge_ports': 'swp30.1003 swp31.1003 swp32.1003 swp33.1003 CSS-E004.1003 CSS-E005.1003 CSS-E006.1003 CSS-E007.1003 CSS-E001.1003 CSS-E002.1003 CSS-E003.1003 EHM-E001.1003 EHM-E002.1003 EHM-E003.1003 EHM-E004.1003 EDG-E001.1003 EDG-E002.1003 EDG-E003.1003 CSS-H001.1003 CSS-H002.1003 peerlink.1003 vni-513'}, {'name': 'br-csi-v104', 'alias': 'CSISF-VLAN104-CSCorp-Net', 'bridge_ports': 'swp30.104 swp31.104 swp32.104 swp33.104 CSS-E004.104 CSS-E005.104 CSS-E006.104 CSS-E007.104 CSS-E001.104 CSS-E002.104 CSS-E003.104 EHM-E001.104 EHM-E002.104 EHM-E003.104 EHM-E004.104 CSS-H001.104 CSS-H002.104 peerlink.104 vni-508'}, {'name': 'br-csi-v114', 'alias': 'CSISF-VLAN114-CSCorp-Net', 'bridge_ports': 'swp30.114 swp31.114 swp32.114 swp33.114 CSS-E004.114 CSS-E005.114 CSS-E006.114 CSS-E007.114 CSS-E001.114 CSS-E002.114 CSS-E003.114 CSI-E001.114 CSI-E002.114 peerlink.114 vni-525'}, {'name': 'br-csi-v2704', 'alias': 'CSI-DMZ', 'bridge_ports': 'EDG-E001.2704 EDG-E002.2704 CSS-E001.2704 CSS-E002.2704 CSS-E003.2704 peerlink.2704 vni-2704'}, {'name': 'br-phn-v1007', 'alias': 'CSSSF-PHCN-Net', 'bridge_ports': 'swp30.1007 swp31.1007 swp32.1007 swp33.1007 CSS-E004.1007 CSS-E005.1007 CSS-E006.1007 CSS-E007.1007 CSS-E001.1007 CSS-E002.1007 CSS-E003.1007 CSS-H001.1007 CSS-H002.1007 peerlink.1007 vni-519'}, {'name': 'br-phn-v1102', 'alias': 'PHCN - SFD-iSCSI1', 'bridge_ports': 'CS-iLF01.1102 peerlink.1102 vni-1102'}, {'name': 'br-phn-v1103', 'alias': 'PHCN - SFD-iSCSI2', 'bridge_ports': 'CS-iLF01.1103 peerlink.1103 vni-1103'}, {'name': 'br-phn-v120', 'alias': 'PHN-Legacy-Net', 'bridge_ports': 'swp30.120 swp31.120 swp32.120 swp33.120 CSS-E004.120 CSS-E005.120 CSS-E006.120 CSS-E007.120 CSS-E001.120 CSS-E002.120 CSS-E003.120 EHM-E001.120 EHM-E002.120 EHM-E003.120 EHM-E004.120 EDG-E001.120 EDG-E002.120 EDG-E003.120 CSS-H001.120 CSS-H002.120 peerlink.120 vni-620'}, {'name': 'br-mbs-v1006', 'alias': 'MBS-CLD-PBS-Network', 'bridge_ports': 'swp30.1006 swp31.1006 swp32.1006 swp33.1006 CSS-E004.1006 CSS-E005.1006 CSS-E006.1006 CSS-E007.1006 CSS-E001.1006 CSS-E002.1006 CSS-E003.1006 peerlink.1006 vni-524'}, {'name': 'br-mbs-v1000', 'alias': 'CSSShared-MBS-VL1000-CS-Server-Net', 'bridge_ports': 'swp30.1000 swp31.1000 swp32.1000 swp33.1000 CSS-E004.1000 CSS-E005.1000 CSS-E006.1000 CSS-E007.1000 CSS-E001.1000 CSS-E002.1000 CSS-E003.1000 CSS-H001.1000 CSS-H002.1000  peerlink.1000 vni-1000'}, {'name': 'br-mbs-v1002', 'alias': 'CSSShared-MBS-Site-Interconnect', 'bridge_ports': 'swp30.1002 swp31.1002 swp32.1002 swp33.1002 CSS-E004.1002 CSS-E005.1002 CSS-E006.1002 CSS-E007.1002 CSS-E001.1002 CSS-E002.1002 CSS-E003.1002 peerlink.1002 vni-1002'}, {'name': 'br-mbs-v1', 'alias': 'CSSShared-MBS-VL1-Interconnect', 'bridge_ports': 'swp30.1 swp31.1 swp32.1 swp33.1 CSS-E004.1 CSS-E005.1 CSS-E006.1 CSS-E007.1 CSS-E001.1 CSS-E002.1 CSS-E003.1 peerlink.1 vni-1003'}, {'name': 'br-mbs-v4', 'alias': 'CSSSF-VLAN4-MBS-DMZ-Net', 'bridge_ports': 'swp30.4 swp31.4 swp32.4 swp33.4 CSS-E004.4 CSS-E005.4 CSS-E006.4 CSS-E007.4 CSS-E001.4 CSS-E002.4 CSS-E003.4 peerlink.4 vni-1004'}, {'name': 'br-lit-v2902', 'alias': 'LaScala-SFD-iSCSI1', 'bridge_ports': 'CS-iLF01.2902 peerlink.2902 vni-2902'}, {'name': 'br-lit-v2903', 'alias': 'LaScala-SFD-iSCSI2', 'bridge_ports': 'CS-iLF01.2903 peerlink.2903 vni-2903'}, {'name': 'br-lit-v2904', 'alias': 'LaScala-BYR-iSCSI1', 'bridge_ports': 'CS-iLF01.2904 peerlink.2904 vni-2904'}, {'name': 'br-lit-v2905', 'alias': 'LaScala-BYR-iSCSI2', 'bridge_ports': 'CS-iLF01.2905 peerlink.2905 vni-2905'}, {'name': 'br-dmw-v1200', 'alias': 'DoerenMayhew-RR-Backup', 'bridge_ports': 'CSS-H001.1200 CSS-H002.1200 peerlink.1200 vni-1200'}, {'name': 'br-hss-v1201', 'alias': 'Hutchinson-RR-Backup', 'bridge_ports': 'CSS-H001.1201 CSS-H002.1201 peerlink.1201 vni-1201'}, {'name': 'br-mbp-v1202', 'alias': 'MBPIA-RR-Backup', 'bridge_ports': 'swp30.1202 swp31.1202 swp32.1202 swp33.1202 EDG-E001.1202 EDG-E002.1202 EDG-E003.1202 CSS-H001.1202 CSS-H002.1202 peerlink.1202 vni-1202'}, {'name': 'br-dcp-v102', 'alias': 'Dencap-Network', 'bridge_ports': 'swp30.102 swp31.102 swp32.102 swp33.102 CSS-E004.102 CSS-E005.102 CSS-E006.102 CSS-E007.102 CSS-E001.102 CSS-E002.102 CSS-E003.102 CSS-H001.102 CSS-H002.102 peerlink.102 vni-506'}, {'name': 'br-sqh-v1005', 'alias': 'SQH-DR-NET', 'bridge_ports': 'swp30.1005 swp31.1005 swp32.1005 swp33.1005 CSS-E004.1005 CSS-E005.1005 CSS-E006.1005 CSS-E007.1005 CSS-E001.1005 CSS-E002.1005 CSS-E003.1005 EHM-E001.1005 EHM-E002.1005 EHM-E003.1005 EHM-E004.1005 EDG-E001.1005 EDG-E002.1005 EDG-E003.1005 CSS-H001.1005 CSS-H002.1005 peerlink.1005 vni-523'}, {'name': 'vni-1251', 'mtu': '9148', 'vxlan_id': '2905', 'vxlan_local_tunnel_ip_address': '10.35.0.80'}], 'host': '10.30.20.80'}, {'command': 'show interfaces configuration', 'output': [{'name': 'lo inet loopback', 'ip_address': '10.35.0.81/32', 'clagd_anycast_ip_address': '10.35.0.180'}, {'name': 'eth0', 'alias': 'MGMT-to-CSS1A-106-MGT-01 - 10270', 'ip_address': '10.30.20.81/24', 'vrf': 'mgmt', 'gateway_ip_address': '10.30.20.1'}, {'name': 'swp1', 'mtu': '9216'}, {'name': 'swp2', 'mtu': '9216'}, {'name': 'swp3', 'mtu': '9216'}, {'name': 'swp4', 'mtu': '9216'}, {'name': 'swp5', 'mtu': '9216'}, {'name': 'swp6', 'mtu': '9216'}, {'name': 'swp7', 'mtu': '9216'}, {'name': 'swp8', 'mtu': '9216'}, {'name': 'swp9', 'mtu': '9216'}, {'name': 'swp10', 'mtu': '9216'}, {'name': 'swp11', 'mtu': '9216'}, {'name': 'swp12', 'mtu': '9216'}, {'name': 'swp13', 'mtu': '9216'}, {'name': 'swp14', 'mtu': '9216'}, {'name': 'swp15', 'mtu': '9216'}, {'name': 'swp16', 'mtu': '9216'}, {'name': 'swp30', 'alias': 'BLD01-13', 'mtu': '9216'}, {'name': 'swp31', 'alias': 'BLD01-14', 'mtu': '9216'}, {'name': 'swp32', 'alias': 'BLD01-16', 'mtu': '9216'}, {'name': 'swp33', 'alias': 'BLD02-01', 'mtu': '9216'}, {'name': 'swp42', 'alias': 'KFG 52608 Replication', 'mtu': '9216'}, {'name': 'swp46', 'alias': 'Uplink-to-CSS1A-105-EDG-02 - 10020', 'mtu': '9216'}, {'name': 'swp47', 'alias': 'Uplink-to-CSS1A-107-iSC-02 - 10247', 'mtu': '9216'}, {'name': 'swp48', 'alias': 'Uplink to MGMT-SWITCH', 'mtu': '9216'}, {'name': 'swp49', 'alias': 'Uplink to CSS1A-105-SPN-01 - 10218', 'mtu': '9216'}, {'name': 'swp50', 'alias': 'Uplink to CSS1A-105-SPN-02 - 10224', 'mtu': '9216'}, {'name': 'swp55', 'alias': 'Peerlink - CSS1A-108-LEF-01 - 10232', 'mtu': '9216'}, {'name': 'swp56', 'alias': 'Peerlink - CSS1A-108-LEF-01 - 10238', 'mtu': '9216'}, {'name': 'br-native', 'bridge_ports': 'peerlink'}, {'name': 'mgmt', 'ip_address': '127.0.0.1/8'}, {'name': 'peerlink', 'mtu': '9216', 'bond_slaves': 'swp55 swp56'}, {'name': 'peerlink.4094', 'ip_address': '169.254.255.2/30'}, {'name': 'CSS-E004', 'alias': 'CSS1A-ESXI004 - 10023', 'mtu': '9216', 'bond_slaves': 'swp1'}, {'name': 'CSS-E005', 'alias': 'CSS1A-ESXI005 - 10024', 'mtu': '9216', 'bond_slaves': 'swp2'}, {'name': 'CSS-E006', 'alias': 'CSS1A-ESXI006 - 10060', 'mtu': '9216', 'bond_slaves': 'swp3'}, {'name': 'CSS-E007', 'alias': 'CSS1A-ESXI007 - 10038', 'mtu': '9216', 'bond_slaves': 'swp4'}, {'name': 'CSS-E001', 'alias': 'CSS1A-ESXI001 - 10150', 'mtu': '9216', 'bond_slaves': 'swp5'}, {'name': 'CSS-E002', 'alias': 'CSS1A-ESXI002 - 10108', 'mtu': '9216', 'bond_slaves': 'swp6'}, {'name': 'CSS-E003', 'alias': 'CSS1A-ESXI003 - 10052', 'mtu': '9216', 'bond_slaves': 'swp7'}, {'name': 'EHM-E001', 'alias': 'EHM1A-ESXI001 - 10112', 'mtu': '9216', 'bond_slaves': 'swp8'}, {'name': 'EHM-E002', 'alias': 'EHM1A-ESXI002 - 10064', 'mtu': '9216', 'bond_slaves': 'swp9'}, {'name': 'EHM-E003', 'alias': 'EHM1A-ESXI003 - 10044', 'mtu': '9216', 'bond_slaves': 'swp10'}, {'name': 'EHM-E004', 'alias': 'EHM1A-ESXI004 - 10062', 'mtu': '9216', 'bond_slaves': 'swp11'}, {'name': 'EDG-E001', 'alias': 'EDG1A-ESXI001 - 10077', 'mtu': '9216', 'bond_slaves': 'swp12'}, {'name': 'EDG-E002', 'alias': 'EDG1A-ESXI002 - 10071', 'mtu': '9216', 'bond_slaves': 'swp13'}, {'name': 'EDG-E003', 'alias': 'EDG1A-ESXI003 - 10061', 'mtu': '9216', 'bond_slaves': 'swp14'}, {'name': 'CSS-H001', 'alias': 'CSS1A-HYPV001', 'mtu': '9216', 'bond_slaves': 'swp15'}, {'name': 'CSS-H002', 'alias': 'CSS1A-HYPV002', 'mtu': '9216', 'bond_slaves': 'swp16'}, {'name': 'CSI-E001', 'alias': 'CSS1A-ESXI001', 'mtu': '9216', 'bond_slaves': 'swp17'}, {'name': 'CSI-E002', 'alias': 'CSS1A-ESXI002', 'mtu': '9216', 'bond_slaves': 'swp18'}, {'name': 'KFG-H001', 'alias': 'KFG1A-HV001', 'mtu': '9216', 'bond_slaves': 'swp19', 'clag_id': '119'}, {'name': 'CSS-020', 'alias': 'UNUSED', 'mtu': '9216', 'bond_slaves': 'swp20'}, {'name': 'CSS-021', 'alias': 'UNUSED', 'mtu': '9216', 'bond_slaves': 'swp21'}, {'name': 'CSS-022', 'alias': 'UNUSED', 'mtu': '9216', 'bond_slaves': 'swp22'}, {'name': 'CSS-023', 'alias': 'UNUSED', 'mtu': '9216', 'bond_slaves': 'swp23'}, {'name': 'CSS-024', 'alias': 'UNUSED', 'mtu': '9216', 'bond_slaves': 'swp24'}, {'name': 'CS-iLF01', 'alias': 'CSS1A-107-iSC-02 - 10247', 'mtu': '9216', 'bond_slaves': 'swp47', 'clag_id': '201'}, {'name': 'CS-EDGSW', 'alias': 'CSS1A-105-EDG-02 - 10020', 'mtu': '9216', 'bond_slaves': 'swp46', 'clag_id': '202'}, {'name': 'CS-MGT', 'alias': 'uplink to MGT-01 and MGT-02 switches', 'mtu': '9216', 'bond_slaves': 'swp48', 'clag_id': '203'}, {'name': 'br-def-v15', 'alias': 'CSSSF-VLAN15-02-MGMT', 'bridge_ports': 'swp30.15 swp31.15 swp32.15 swp33.15 CSS-E004.15 CSS-E005.15 CSS-E006.15 CSS-E007.15 CSS-E001.15 CSS-E002.15 CSS-E003.15 EHM-E001.15 EHM-E002.15 EHM-E003.15 EHM-E004.15 EDG-E001.15 EDG-E002.15 EDG-E003.15 CSS-H001.15 CSS-H002.15 peerlink.15 vni-501'}, {'name': 'br-def-v205', 'alias': 'CSSSF-DMZ-NET', 'bridge_ports': 'swp30.205 swp31.205 swp32.205 swp33.205 EDG-E001.205 EDG-E002.205 EDG-E003.205 peerlink.205 vni-522'}, {'name': 'br-def-v1251', 'alias': 'CSS-FIREWALL-NET', 'bridge_ports': 'CSS-E004.1251 CSS-E005.1251 CSS-E006.1251 CSS-E007.1251 CSS-E001.1251 CSS-E002.1251 CSS-E003.1251 EHM-E001.1251 EHM-E002.1251 EHM-E003.1251 EHM-E004.1251 EDG-E001.1251 EDG-E002.1251 EDG-E003.1251 peerlink.1251 vni-1251'}, {'name': 'br-kfg-v230', 'alias': 'KFG-VLAN230', 'bridge_ports': 'swp42 KFG-H001 CS-iLF01.230 peerlink.230 vni-1001'}, {'name': 'br-def-v1998', 'alias': 'BGP-01-124', 'bridge_ports': 'CS-EDGSW.1998 peerlink.1998 vni-1998'}, {'name': 'br-def-v1999', 'alias': 'BGP-LaScala', 'bridge_ports': 'CS-EDGSW.1999 peerlink.1999 vni-1999'}, {'name': 'br-def-v2511', 'alias': 'CS-ESXI-VMOTION', 'bridge_ports': 'CSS-E004.2511 CSS-E005.2511 CSS-E006.2511 CSS-E007.2511 CSS-E001.2511 CSS-E002.2511 CSS-E003.2511 EHM-E001.2511 EHM-E002.2511 EHM-E003.2511 EHM-E004.2511 EDG-E001.2511 EDG-E002.2511 EDG-E003.2511 CSS-H001.2511 CSS-H002.2511 CSI-E001.2511 CSI-E002.2511 peerlink.2511 vni-2511'}, {'name': 'br-def-v2520', 'alias': 'CS-OOB-SWITCH-MGMT', 'bridge_ports': 'CS-MGT.2520 peerlink.2520 vni-2520'}, {'name': 'br-def-v2521', 'alias': 'CS-iDRAC-MGMT', 'bridge_ports': 'CS-MGT.2521 peerlink.2521 vni-2521'}, {'name': 'br-def-v2522', 'alias': 'CS-SAN-MGMT', 'bridge_ports': 'CS-MGT.2522 peerlink.2522 vni-2522'}, {'name': 'br-def-v2577', 'alias': 'CSS-iSCSI-01', 'bridge_ports': 'CS-iLF01.2577 peerlink.2577 vni-2577'}, {'name': 'br-def-v2578', 'alias': 'CSS-iSCSI-02', 'bridge_ports': 'CS-iLF01.2578 peerlink.2578 vni-2578'}, {'name': 'br-def-v2579', 'alias': 'CSS-iSCSI-REPL', 'bridge_ports': 'CS-iLF01.2579 peerlink.2579 vni-2579'}, {'name': 'br-def-v150', 'alias': 'CSSBC-O2-Net', 'bridge_ports': 'swp30.150 swp31.150 swp32.150 swp33.150 CSS-E004.150 CSS-E005.150 CSS-E006.150 CSS-E007.150 CSS-E001.150 CSS-E002.150 CSS-E003.150 EHM-E001.150 EHM-E002.150 EHM-E003.150 EHM-E004.150 EDG-E001.150 EDG-E002.150 EDG-E003.150 CSS-H001.150 CSS-H002.150 peerlink.150 vni-600'}, {'name': 'br-def-v253', 'alias': 'CSSSF-KMS-NET', 'bridge_ports': 'CSS-E004.253 CSS-E005.253 CSS-E006.253 CSS-E007.253 CSS-E001.253 CSS-E002.253 CSS-E003.253 EHM-E001.253 EHM-E002.253 EHM-E003.253 EHM-E004.253 EDG-E001.253 EDG-E002.253 EDG-E003.253 CSS-H001.253 CSS-H002.253 peerlink.253 vni-520'}, {'name': 'br-def-v599', 'alias': 'CSS-SSL-VPN-Clients', 'bridge_ports': 'CSS-E004.599 CSS-E005.599 CSS-E006.599 CSS-E007.599 CSS-E001.599 CSS-E002.599 CSS-E003.599 EHM-E001.599 EHM-E002.599 EHM-E003.599 EHM-E004.599 EDG-E001.599 EDG-E002.599 EDG-E003.599 CSS-H001.599 CSS-H002.599 peerlink.599 vni-599'}, {'name': 'br-def-v201', 'alias': 'CSSBC-KMS-NET', 'bridge_ports': 'CS-MGT.201 peerlink.201 vni-512'}, {'name': 'br-def-v12', 'alias': 'CSSBC-ESXiMGMT', 'bridge_ports': 'swp30.12 swp31.12 swp32.12 swp33.12 peerlink.12 vni-602'}, {'name': 'br-def-v174', 'alias': 'CSSBC-iSCSI-01', 'bridge_ports': 'CS-iLF01.174 peerlink.174 vni-604'}, {'name': 'br-def-v175', 'alias': 'CSSBC-iSCSI-02', 'bridge_ports': 'CS-iLF01.175 peerlink.175 vni-605'}, {'name': 'br-def-v250', 'alias': 'CSSSF-FWAL-NET', 'bridge_ports': 'EDG-E001.250 EDG-E002.250 EDG-E003.250 peerlink.250 vni-250'}, {'name': 'br-ehm-v100', 'alias': 'CSSSF-VLAN100-EHM-Servers', 'bridge_ports': 'swp30.100 swp31.100 swp32.100 swp33.100 EHM-E001.100 EHM-E002.100 EHM-E003.100 EHM-E004.100 CSS-H001.100 CSS-H002.100 peerlink.100 vni-504'}, {'name': 'br-ehm-v1004', 'alias': 'EHM-VDI-NET', 'bridge_ports': 'swp30.1004 swp31.1004 swp32.1004 swp33.1004 CSS-E004.1004 CSS-E005.1004 CSS-E006.1004 CSS-E007.1004 CSS-E001.1004 CSS-E002.1004 CSS-E003.1004 EHM-E001.1004 EHM-E002.1004 EHM-E003.1004 EHM-E004.1004 EDG-E001.1004 EDG-E002.1004 EDG-E003.1004 CSS-H001.1004 CSS-H002.1004 peerlink.1004 vni-514'}, {'name': 'br-ult-v101', 'alias': 'CSSSF-VLAN101-Ultralevel-Net', 'bridge_ports': 'swp30.101 swp31.101 swp32.101 swp33.101 CSS-E004.101 CSS-E005.101 CSS-E006.101 CSS-E007.101 CSS-E001.101 CSS-E002.101 CSS-E003.101 CSS-H001.101 CSS-H002.101 peerlink.101 vni-505'}, {'name': 'br-ara-v103', 'alias': 'CSSSF-VLAN103-ARAS-NET', 'bridge_ports': 'swp30.103 swp31.103 swp32.103 swp33.103 CSS-E004.103 CSS-E005.103 CSS-E006.103 CSS-E007.103 CSS-E001.103 CSS-E002.103 CSS-E003.103 CSS-H001.103 CSS-H002.103 peerlink.103 vni-507'}, {'name': 'br-ara-v107', 'alias': 'CSSSF-VLAN107-Aras2-Net', 'bridge_ports': 'swp30.107 swp31.107 swp32.107 swp33.107 CSS-E004.107 CSS-E005.107 CSS-E006.107 CSS-E007.107 CSS-E001.107 CSS-E002.107 CSS-E003.107 peerlink.107 vni-517'}, {'name': 'br-ara-v113', 'alias': 'CSSSF-Aras-Physical-Net', 'bridge_ports': 'swp30.113 swp31.113 swp32.113 swp33.113 CSS-E004.113 CSS-E005.113 CSS-E006.113 CSS-E007.113 CSS-E001.113 CSS-E002.113 CSS-E003.113 peerlink.113 vni-521'}, {'name': 'br-ara-v200', 'alias': 'ARA-DMZ-NET', 'bridge_ports': 'swp30.200 swp31.200 swp32.200 swp33.200 CSS-E004.200 CSS-E005.200 CSS-E006.200 CSS-E007.200 CSS-E001.200 CSS-E002.200 CSS-E003.200 EHM-E001.200 EHM-E002.200 EHM-E003.200 EHM-E004.200 EDG-E001.200 EDG-E002.200 EDG-E003.200 CSS-H001.200 CSS-H002.200 peerlink.200 vni-511'}, {'name': 'br-ara-v1003', 'alias': 'ARA-DR-NET', 'bridge_ports': 'swp30.1003 swp31.1003 swp32.1003 swp33.1003 CSS-E004.1003 CSS-E005.1003 CSS-E006.1003 CSS-E007.1003 CSS-E001.1003 CSS-E002.1003 CSS-E003.1003 EHM-E001.1003 EHM-E002.1003 EHM-E003.1003 EHM-E004.1003 EDG-E001.1003 EDG-E002.1003 EDG-E003.1003 CSS-H001.1003 CSS-H002.1003 peerlink.1003 vni-513'}, {'name': 'br-csi-v104', 'alias': 'CSSSF-VLAN104-CSCorp-Net', 'bridge_ports': 'swp30.104 swp31.104 swp32.104 swp33.104 CSS-E004.104 CSS-E005.104 CSS-E006.104 CSS-E007.104 CSS-E001.104 CSS-E002.104 CSS-E003.104 EHM-E001.104 EHM-E002.104 EHM-E003.104 EHM-E004.104 CSS-H001.104 CSS-H002.104 peerlink.104 vni-508'}, {'name': 'br-csi-v114', 'alias': 'CSSSF-VLAN114-CSCorp-Net', 'bridge_ports': 'swp30.114 swp31.114 swp32.114 swp33.114 CSS-E004.114 CSS-E005.114 CSS-E006.114 CSS-E007.114 CSS-E001.114 CSS-E002.114 CSS-E003.114 CSI-E001.114 CSI-E002.114 peerlink.114 vni-525'}, {'name': 'br-csi-v2704', 'alias': 'CSI-DMZ', 'bridge_ports': 'EDG-E001.2704 EDG-E002.2704 CSS-E001.2704 CSS-E002.2704 CSS-E003.2704 peerlink.2704 vni-2704'}, {'name': 'br-phc-v1007', 'alias': 'CSSSF-PHCN-Net', 'bridge_ports': 'swp30.1007 swp31.1007 swp32.1007 swp33.1007 CSS-E004.1007 CSS-E005.1007 CSS-E006.1007 CSS-E007.1007 CSS-E001.1007 CSS-E002.1007 CSS-E003.1007 CSS-H001.1007 CSS-H002.1007 peerlink.1007 vni-519'}, {'name': 'br-phc-v1102', 'alias': 'PHCN - SFD-iSCSI1', 'bridge_ports': 'CS-iLF01.1102 peerlink.1102 vni-1102'}, {'name': 'br-phn-v1103', 'alias': 'PHCN - SFD-iSCSI2', 'bridge_ports': 'CS-iLF01.1103 peerlink.1103 vni-1103'}, {'name': 'br-phn-v120', 'alias': 'PHN-Legacy-Net', 'bridge_ports': 'swp30.120 swp31.120 swp32.120 swp33.120 CSS-E004.120 CSS-E005.120 CSS-E006.120 CSS-E007.120 CSS-E001.120 CSS-E002.120 CSS-E003.120 EHM-E001.120 EHM-E002.120 EHM-E003.120 EHM-E004.120 EDG-E001.120 EDG-E002.120 EDG-E003.120 CSS-H001.120 CSS-H002.120 peerlink.120 vni-620'}, {'name': 'br-mbs-v1006', 'alias': 'MBS-CLD-PBS-Network', 'bridge_ports': 'swp30.1006 swp31.1006 swp32.1006 swp33.1006 CSS-E004.1006 CSS-E005.1006 CSS-E006.1006 CSS-E007.1006 CSS-E001.1006 CSS-E002.1006 CSS-E003.1006 peerlink.1006 vni-524'}, {'name': 'br-mbs-v1000', 'alias': 'CSSShared-MBS-VL1000-CS-Server-Net', 'bridge_ports': 'swp30.1000 swp31.1000 swp32.1000 swp33.1000 CSS-E004.1000 CSS-E005.1000 CSS-E006.1000 CSS-E007.1000 CSS-E001.1000 CSS-E002.1000 CSS-E003.1000 CSS-H001.1000 CSS-H002.1000 peerlink.1000 vni-1000'}, {'name': 'br-mbs-v1002', 'alias': 'CSSShared-MBS-Site-Interconnect', 'bridge_ports': 'swp30.1002 swp31.1002 swp32.1002 swp33.1002 CSS-E004.1002 CSS-E005.1002 CSS-E006.1002 CSS-E007.1002 CSS-E001.1002 CSS-E002.1002 CSS-E003.1002 peerlink.1002 vni-1002'}, {'name': 'br-mbs-v1', 'alias': 'CSSShared-MBS-VL1-Interconnect', 'bridge_ports': 'swp30.1 swp31.1 swp32.1 swp33.1 CSS-E004.1 CSS-E005.1 CSS-E006.1 CSS-E007.1 CSS-E001.1 CSS-E002.1 CSS-E003.1 peerlink.1 vni-1003'}, {'name': 'br-mbs-v4', 'alias': 'CSSSF-VLAN4-MBS-DMZ-Net', 'bridge_ports': 'swp30.4 swp31.4 swp32.4 swp33.4 CSS-E004.4 CSS-E005.4 CSS-E006.4 CSS-E007.4 CSS-E001.4 CSS-E002.4 CSS-E003.4 peerlink.4 vni-1004'}, {'name': 'br-lit-v2902', 'alias': 'LaScala-SFD-iSCSI1', 'bridge_ports': 'CS-iLF01.2902 peerlink.2902 vni-2902'}, {'name': 'br-lit-v2903', 'alias': 'LaScala-SFD-iSCSI2', 'bridge_ports': 'CS-iLF01.2903 peerlink.2903 vni-2903'}, {'name': 'br-lit-v2904', 'alias': 'LaScala-BYR-iSCSI1', 'bridge_ports': 'CS-iLF01.2904 peerlink.2904 vni-2904'}, {'name': 'br-lit-v2905', 'alias': 'LaScala-BYR-iSCSI2', 'bridge_ports': 'CS-iLF01.2905 peerlink.2905 vni-2905'}, {'name': 'br-dmw-v1200', 'alias': 'DoerenMayhew-RR-Backup', 'bridge_ports': 'CSS-H001.1200 CSS-H002.1200 peerlink.1200 vni-1200'}, {'name': 'br-hss-v1201', 'alias': 'Hutchinson-RR-Backup', 'bridge_ports': 'CSS-H001.1201 CSS-H002.1201 peerlink.1201 vni-1201'}, {'name': 'br-mbp-v1202', 'alias': 'MBPIA-RR-Backup', 'bridge_ports': 'swp30.1202 swp31.1202 swp32.1202 swp33.1202 EDG-E001.1202 EDG-E002.1202 EDG-E003.1202 CSS-H001.1202 CSS-H002.1202 peerlink.1202 vni-1202'}, {'name': 'br-dcp-v102', 'alias': 'Dencap-Network', 'bridge_ports': 'swp30.102 swp31.102 swp32.102 swp33.102 CSS-E004.102 CSS-E005.102 CSS-E006.102 CSS-E007.102 CSS-E001.102 CSS-E002.102 CSS-E003.102 CSS-H001.102 CSS-H002.102 peerlink.102 vni-506'}, {'name': 'br-sqh-v1005', 'alias': 'SQH-DR-NET', 'bridge_ports': 'swp30.1005 swp31.1005 swp32.1005 swp33.1005 CSS-E004.1005 CSS-E005.1005 CSS-E006.1005 CSS-E007.1005 CSS-E001.1005 CSS-E002.1005 CSS-E003.1005 EHM-E001.1005 EHM-E002.1005 EHM-E003.1005 EHM-E004.1005 EDG-E001.1005 EDG-E002.1005 EDG-E003.1005 CSS-H001.1005 CSS-H002.1005 peerlink.1005 vni-523'}, {'name': 'vni-1251', 'mtu': '9148', 'vxlan_id': '2905', 'vxlan_local_tunnel_ip_address': '10.35.0.81'}], 'host': '10.30.20.81'}]
    #
    # interface_search_results = []
    #
    # for result in results:
    #     found = False
    #     hostname = find_hostname_from_ip_address(result['host'])
    #     for interface in result['output']:
    #         if interface['name'] == 'vni-1251':
    #             found = True
    #             print(f"--- {hostname} ({result['host']}) ---")
    #             print(json.dumps(interface, indent=4))
    #     interface_search_results.append(dict(
    #         hostname=hostname,
    #         ip=result['host'],
    #         found=found
    #     ))
    #
    # print(interface_search_results)





    # device = CumulusConnection(
    #     #hostname=hosts['CSS1A-109-LEF-03'],
    #     hostname=hosts['CSS1A-106-LEF-01'],
    #     #hostname=hosts['CSS1A-105-TBL-01'],
    #     username=creds['username'],
    #     password=creds['password']
    # )
    #






    # blah = device.show_interfaces_configuration()
    # for i in blah:
    #     #print(json.dumps(i, indent=4))
    #     print(i)

    # caw = device.show_bridge_macs()
    # for i in caw:
    #     print(i)
    #
    # print(len(caw))

    # show_version = device.show_version()
    # print(json.dumps(show_version, indent=4))


    #
    # show_version = device.show_version()
    # print(json.dumps(show_version, indent=4))

    #l = device.send_command("cat /etc/network/interfaces")

    #for b in l:
    #    print(b)

    # macs = device.show_bridge_macs()
    # for mac in macs:
    #     print(mac)
    # print(len(macs))











