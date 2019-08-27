import os
from config import *
from utils.io import read_yaml_file
from utils.logger import logger
from exceptions import InventoryFileNotFound, \
    ValidationFileNotFound


def find_hostname_from_ip_address(ip):
    hostname = None

    for k, v in INVENTORY_HOSTS.items():
        if ip == v:
            hostname = k

    return hostname


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


def get_inventory():

    if os.path.isfile(HOSTS_FILENAME):
        inventory = read_yaml_file(HOSTS_FILENAME)
    else:
        logger.error(f"Cannot find specified inventory file: {HOSTS_FILENAME}")
        raise InventoryFileNotFound

    return inventory


INVENTORY_HOSTS = get_inventory_by_group(VENDOR)
