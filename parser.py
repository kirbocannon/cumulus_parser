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
    hosts = [host for host in inventory_hosts]

    args = gen_args()

    if not args.cumulus_crawler:
        print("type --help for help with this command.")
    else:
        if args.cumulus_crawler == 'search':
            if args.mac:
                results = check_mac_address(args.mac, hosts)
                print('\n', tabulate_to_console(results))
            elif args.iface:
                results = check_interface_configuration(args.iface, hosts)
                print(results)
















