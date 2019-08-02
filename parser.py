import paramiko
import json
import time
import logging
import os
import yaml
from textfsm import clitable
from paramiko import ssh_exception as pexception
from exceptions import InventoryFileNotFound, \
    CannotParseOutputWithTextFSM
from multiprocessing .dummy import Pool as Threadpool


HOSTS_FILENAME = 'hosts.yaml'
POOL = Threadpool(4)
WAIT_FOR_COMMAND_IN_SECONDS = 4
TEMPLATE_DIR = './templates/'


class CumulusDevice(object):
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.username = username
        self.password = password

    def _open_connection(self):
        ssh_client = None

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

        except (pexception.BadHostKeyException,
                pexception.AuthenticationException,
                pexception.SSHException,
                pexception.socket.error) as e:
                    print(e)

        return ssh_client

    def _close_connection(self, client):
        return client.close()

    def send_command(self, command):
        """Wrapper for self.device.send.command().
        If command is a list will iterate through commands until valid command.
        """

        ssh_client = self._open_connection()
        _, stdout, stderr = ssh_client.exec_command(command, timeout=10)
        output = stdout.read().decode('utf-8')
        _ = self._close_connection(ssh_client)

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

    def show_version(self):
        output = self.send_command('net show version')
        structured_output = device.parse_output(
            command="net show version",
            platform="cumulus_clos",
            data=output)

        return structured_output

    def show_bridge_macs(self, state='dynamic'):
        state = state.lower()
        command = f"net show bridge macs {state}"
        output = self.send_command(command)
        structured_output = device.parse_output(
            command=command,
            platform="cumulus_clos",
            data=output)

        return structured_output


def get_inventory():

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
    inventory = get_inventory()
    group_inventory = inventory[group]['hosts']

    for k, v in group_inventory.items():
        for _, i in inventory.items():
            if i.get('hosts'):
                caw = i['hosts']
                if caw.get(k) and isinstance(caw.get(k), dict):
                    if caw[k].get('ansible_host'):
                        group_inventory[k] = caw[k]['ansible_host']

    return group_inventory


if __name__ == '__main__':
    # get host inventory
    hosts = get_inventory_by_group('cumulus')

    device = CumulusDevice(
        hostname="10.30.20.82",
        username="cumulus",
        password="T0dayweride!"
    )

    show_version = device.show_version()
    print(show_version)

    # macs = device.show_bridge_macs()
    # for mac in macs:
    #     print(mac)
    # print(len(macs))











