import paramiko
import json
import logging.config
import argparse
import os
import yaml
from tabulate import tabulate
from utils import parse_output, \
    bcolors
from paramiko import ssh_exception as pexception
from exceptions import *
from multiprocessing .dummy import Pool as Threadpool

HOSTS_FILENAME = 'hosts.yaml'
VALIDATION_DIR = './templates/validation'
CREDENTIALS_FILENAME = 'credentials.yaml'
PLATFORM = 'cumulus_clos'
VENDOR = 'cumulus'
WAIT_FOR_COMMAND_IN_SECONDS = 4
TEMPLATE_DIR = './templates/'
ADDRESS_FAMILIES = ['ipv4 unicast', 'l2vpn evpn']

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

    return validation_file[hostname]


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

    #results = multithread_command('show bgp summary', hosts)
    results = [{'command': 'show bgp summary', 'output': {'ipv4 unicast': {'as': 65180, 'bestPath': {'multiPathRelax': 'true'}, 'dynamicPeers': 0, 'peerCount': 3, 'peerMemory': 59208, 'peers': {'peerlink.4094': {'hostname': 'CSS1A-106-LEF-02', 'idType': 'interface', 'inq': 0, 'msgRcvd': 2320634, 'msgSent': 2192824, 'outq': 0, 'peerUptime': '08w2d17h', 'peerUptimeEstablishedEpoch': 1560045790, 'peerUptimeMsec': 5075969000, 'prefixReceivedCount': 7, 'remoteAs': 65181, 'state': 'Idle', 'tableVersion': 0, 'version': 4}, 'swp49': {'hostname': 'CSS1A-105-SPN-01', 'idType': 'interface', 'inq': 0, 'msgRcvd': 1969283, 'msgSent': 2192633, 'outq': 0, 'peerUptime': '08w2d18h', 'peerUptimeEstablishedEpoch': 1560045641, 'peerUptimeMsec': 5076118000, 'prefixReceivedCount': 6, 'remoteAs': 65170, 'state': 'Established', 'tableVersion': 0, 'version': 4}, 'swp50': {'hostname': 'CSS1A-105-SPN-02', 'idType': 'interface', 'inq': 0, 'msgRcvd': 2223004, 'msgSent': 2192480, 'outq': 0, 'peerUptime': '08w2d18h', 'peerUptimeEstablishedEpoch': 1560045643, 'peerUptimeMsec': 5076116000, 'prefixReceivedCount': 6, 'remoteAs': 65171, 'state': 'Established', 'tableVersion': 0, 'version': 4}}, 'ribCount': 15, 'ribMemory': 2280, 'routerId': '10.35.0.80', 'tableVersion': 29, 'totalPeers': 3, 'vrfId': 0, 'vrfName': 'default'}, 'ipv6 unicast': {}, 'l2vpn evpn': {'as': 65180, 'bestPath': {'multiPathRelax': 'true'}, 'dynamicPeers': 0, 'peerCount': 3, 'peerMemory': 59208, 'peers': {'peerlink.4094': {'hostname': 'CSS1A-106-LEF-02', 'idType': 'interface', 'inq': 0, 'msgRcvd': 2320634, 'msgSent': 2192824, 'outq': 0, 'peerUptime': '08w2d17h', 'peerUptimeEstablishedEpoch': 1560045789, 'peerUptimeMsec': 5075971000, 'prefixReceivedCount': 1808, 'remoteAs': 65181, 'state': 'Established', 'tableVersion': 0, 'version': 4}, 'swp49': {'hostname': 'CSS1A-105-SPN-01', 'idType': 'interface', 'inq': 0, 'msgRcvd': 1969283, 'msgSent': 2192633, 'outq': 0, 'peerUptime': '08w2d18h', 'peerUptimeEstablishedEpoch': 1560045640, 'peerUptimeMsec': 5076120000, 'prefixReceivedCount': 1808, 'remoteAs': 65170, 'state': 'Established', 'tableVersion': 0, 'version': 4}, 'swp50': {'hostname': 'CSS1A-105-SPN-02', 'idType': 'interface', 'inq': 0, 'msgRcvd': 2223005, 'msgSent': 2192480, 'outq': 0, 'peerUptime': '08w2d18h', 'peerUptimeEstablishedEpoch': 1560045642, 'peerUptimeMsec': 5076118000, 'prefixReceivedCount': 1808, 'remoteAs': 65171, 'state': 'Established', 'tableVersion': 0, 'version': 4}}, 'ribCount': 403, 'ribMemory': 61256, 'routerId': '10.35.0.80', 'tableVersion': 0, 'totalPeers': 3, 'vrfId': 0, 'vrfName': 'default'}}, 'host': '10.30.20.80'},
{'command': 'show bgp summary', 'output': {'ipv4 unicast': {'as': 65181, 'bestPath': {'multiPathRelax': 'true'}, 'dynamicPeers': 0, 'peerCount': 3, 'peerMemory': 59208, 'peers': {'peerlink.4094': {'hostname': 'CSS1A-106-LEF-01', 'idType': 'interface', 'inq': 0, 'msgRcvd': 2192410, 'msgSent': 2320366, 'outq': 0, 'peerUptime': '08w2d17h', 'peerUptimeEstablishedEpoch': 1560045874, 'peerUptimeMsec': 5075885000, 'prefixReceivedCount': 7, 'remoteAs': 65180, 'state': 'idle', 'tableVersion': 0, 'version': 4}, 'swp49': {'hostname': 'CSS1A-105-SPN-01', 'idType': 'interface', 'inq': 0, 'msgRcvd': 1969154, 'msgSent': 2320365, 'outq': 0, 'peerUptime': '08w2d17h', 'peerUptimeEstablishedEpoch': 1560045880, 'peerUptimeMsec': 5075879000, 'prefixReceivedCount': 7, 'remoteAs': 65170, 'state': 'Established', 'tableVersion': 0, 'version': 4}, 'swp50': {'hostname': 'CSS1A-105-SPN-02', 'idType': 'interface', 'inq': 0, 'msgRcvd': 2222788, 'msgSent': 2320219, 'outq': 0, 'peerUptime': '08w2d17h', 'peerUptimeEstablishedEpoch': 1560045883, 'peerUptimeMsec': 5075876000, 'prefixReceivedCount': 7, 'remoteAs': 65171, 'state': 'Established', 'tableVersion': 0, 'version': 4}}, 'ribCount': 15, 'ribMemory': 2280, 'routerId': '10.35.0.81', 'tableVersion': 28, 'totalPeers': 3, 'vrfId': 0, 'vrfName': 'default'}, 'ipv6 unicast': {}, 'l2vpn evpn': {'as': 65181, 'bestPath': {'multiPathRelax': 'true'}, 'dynamicPeers': 0, 'peerCount': 3, 'peerMemory': 59208, 'peers': {'peerlink.4094': {'hostname': 'CSS1A-106-LEF-01', 'idType': 'interface', 'inq': 0, 'msgRcvd': 2192410, 'msgSent': 2320366, 'outq': 0, 'peerUptime': '08w2d17h', 'peerUptimeEstablishedEpoch': 1560045874, 'peerUptimeMsec': 5075886000, 'prefixReceivedCount': 1808, 'remoteAs': 65180, 'state': 'Established', 'tableVersion': 0, 'version': 4}, 'swp49': {'hostname': 'CSS1A-105-SPN-01', 'idType': 'interface', 'inq': 0, 'msgRcvd': 1969154, 'msgSent': 2320365, 'outq': 0, 'peerUptime': '08w2d17h', 'peerUptimeEstablishedEpoch': 1560045880, 'peerUptimeMsec': 5075880000, 'prefixReceivedCount': 1808, 'remoteAs': 65170, 'state': 'Established', 'tableVersion': 0, 'version': 4}, 'swp50': {'hostname': 'CSS1A-105-SPN-02', 'idType': 'interface', 'inq': 0, 'msgRcvd': 2222789, 'msgSent': 2320219, 'outq': 0, 'peerUptime': '08w2d17h', 'peerUptimeEstablishedEpoch': 1560045883, 'peerUptimeMsec': 5075877000, 'prefixReceivedCount': 1808, 'remoteAs': 65171, 'state': 'Established', 'tableVersion': 0, 'version': 4}}, 'ribCount': 403, 'ribMemory': 61256, 'routerId': '10.35.0.81', 'tableVersion': 0, 'totalPeers': 3, 'vrfId': 0, 'vrfName': 'default'}}, 'host': '10.30.20.81'}]

    for result in results:
        hostname = get_hostname_by_ip(result['host'])
        required_peers_dict = {'hostname': hostname,'ipv4 unicast': [], 'l2vpn evpn': []}
        bgp_validators = get_validation_by_hostname(hostname, 'bgp')

        # get validators
        for family in ADDRESS_FAMILIES:
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
                if result['output'][family].get('peers'):
                    for interface, details in result['output'][family]['peers'].items():
                        for required_peer in required_peers_dict[family]:
                            if interface == required_peer['interface'] and \
                                    details['hostname'] == required_peer['peer_hostname']:
                                required_peer['found'] = True
                                if details['state'].upper() == 'ESTABLISHED':
                                    required_peer['established'] = True
                                break

        required_peers.append(required_peers_dict)

    return required_peers


def tabulate_to_console(results):
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

    return tabulated_results


def gen_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='Arguments', dest='cumulus_crawler')
    subparser_search = subparsers.add_parser('search', help='Search')
    subparser_check = subparsers.add_parser('check', help='Check Status, such as BGP')
    mgroup_search = subparser_search.add_mutually_exclusive_group(required=True)
    #mgroup_check = subparser_check.add_mutually_exclusive_group(required=True)
    mgroup_search.add_argument("-m", "--mac", help="Search MAC address", dest='mac')
    mgroup_search.add_argument("-i", "--iface", help="Search Interface", dest='iface')
    subparser_check.add_argument("-b", "--bgp", help="Check BGP", dest='bgp', action='store_true')
    subparser_check.add_argument("-v", "--verbose", help="Verbose output", dest='verbose', action='store_true')

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
        """ Get's interface configuration from /etc/network/interfaces file.
            Not all interface configurations are supported at this time. """
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

    def show_bgp_summary(self):
        """ Currently only supports JSON output
            Currently no VRF support """
        command = "net show bgp summary"
        output = self.send_command(command + ' ' + 'json')[0]['output']
        structured_output = json.loads(output)

        return structured_output

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
    hosts = [host for host in inventory_hosts]

    args = gen_args()

    if not args.cumulus_crawler:
        print("type --help for help with this command.")
    else:
        if args.cumulus_crawler == 'search':
            if args.mac:
                results = search_mac_address(args.mac, hosts)
                print('\n')
                print(tabulate_to_console(results))
            elif args.iface:
                results = search_interface_configuration(args.iface, hosts)
                print(results)
        elif args.cumulus_crawler == 'check':
            if args.bgp:
                results = check_bgp_neighbors(['CSS1A-106-LEF-01', 'CSS1A-106-LEF-02'])
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
                    for peer in down_peers:
                        if not peer['found']:
                            reason = "is not configured"
                        elif not peer['established']:
                            reason = "peering is not established"
                        print("\n", f"{bcolors.FAIL} --> {peer['hostname']}'s required peer "
                        f"on interface {peer['interface']} "
                        f"to {peer['peer_hostname']} failed check because \n {' ' * 4} {reason}! {bcolors.ENDC}", "\n")





























