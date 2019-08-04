import paramiko
import json
import time
import logging
import os
import yaml
from textfsm import clitable
from paramiko import ssh_exception as pexception
from exceptions import *
from multiprocessing .dummy import Pool as Threadpool


HOSTS_FILENAME = 'hosts.yaml'
CREDENTIALS_FILENAME = 'credentials.yaml'
PLATFORM = 'cumulus_clos'
VENDOR = 'cumulus'
WAIT_FOR_COMMAND_IN_SECONDS = 4
TEMPLATE_DIR = './templates/'


class CumulusDevice(object):
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

            print("SSH connection established to {0}".format(self.hostname))
            self.session = ssh_client

        except (pexception.BadHostKeyException,
                pexception.AuthenticationException,
                pexception.SSHException,
                pexception.socket.error) as e:
            print(e)

        return

    def _close_connection(self):
        self.session.close()
        self.session = None
        print('session closed')

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

    @staticmethod
    def _clitable_to_dict(cli_table):
        """Convert TextFSM cli_table object to list of dictionaries."""
        objs = []
        for row in cli_table:
            temp_dict = {}
            for index, element in enumerate(row):
                temp_dict[cli_table.header[index].lower()] = element
            objs.append(temp_dict)

        return objs

    def parse_output(self, platform=None, command=None, data=None):
        """Return the structured data based on the output from a network device."""
        cli_table = clitable.CliTable('index', TEMPLATE_DIR)

        attrs = dict(
            Command=command,
            Platform=platform
        )
        try:
            cli_table.ParseCmd(data, attrs)
            structured_data = self._clitable_to_dict(cli_table)
        except clitable.CliTableError as e:
            raise CannotParseOutputWithTextFSM

        return structured_data

    def show_version(self, from_json=True):
        command = 'net show version'

        if from_json:
            output = self.send_command(command + ' ' + 'json')[0]['output']
            structured_output = json.loads(output)
        else:
            output = self.send_command(command)[0]['output']
            structured_output = self.parse_output(
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
            structured_output = self.parse_output(
                command=command,
                platform=PLATFORM,
                data=output)

        return structured_output

    def show_interfaces_configuration(self, filter='all'):
        #output = self.send_command("cat /etc/network/interfaces")[0]['output']
        filter = filter.lower()
        output = INTERFACES
        interfaces = []
        vnis = []
        structured_output = self.parse_output(
            command="show interfaces configuration",
            platform=PLATFORM,
            data=output)

        for entry in structured_output:
            interface = {}
            for k, v in entry.items():
                if v:
                    interface[k] = v
            interfaces.append(interface)

            if interface.get('vxlan_id'):
                vnis.append(interface)

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

        return func()


def _get_inventory():

    if os.path.isfile(HOSTS_FILENAME):
        inventory = read_yaml_file(HOSTS_FILENAME)
    else:
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
        raise CredentialsFileNotFound

    credentials = credentials[key]

    return {
        'username': credentials['username'],
        'password': credentials['password']
    }


def multithread_command(command, hosts):
    pool = Threadpool(4)
    host_ips = [inventory_hosts[host] for host in hosts]

    def _sc(host):
        device = CumulusDevice(
            hostname=host,
            username=creds['username'],
            password=creds['password']
        )

        results = device.send_command([command])[0]
        results['host'] = host

        return results

    results = pool.map(_sc, host_ips)

    pool.close()
    pool.join()

    return results


if __name__ == '__main__':
    # get host inventory
    inventory_hosts = get_inventory_by_group(VENDOR)
    creds = get_credentials_by_key(VENDOR)

    h = ["CSS1A-106-LEF-01", "CSS1A-106-LEF-02" ]

    multithread_command('show interfaces configuration', h)




    # device = CumulusDevice(
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











