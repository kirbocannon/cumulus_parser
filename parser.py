import argparse
from tabulate import tabulate
from cumulus_parser import CumulusDevice
from inventory.management import *
from utils import bcolors, logger
from exceptions import *
from multiprocessing .dummy import Pool as Threadpool


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
    host_ips = [INVENTORY_HOSTS[host] for host in hosts]

    def _send_multithread_command(host):
        try:
            device = CumulusDevice(
                hostname=host,
                username=creds['username'],
                password=creds['password']
            )

            result = device.send_command([command])[0]
            result['host'] = host
            result['hostname'] = find_hostname_from_ip_address(host)
        except ConnectionError:
            result = None

        return result

    results = pool.map(_send_multithread_command, host_ips)

    pool.close()
    pool.join()

    results = [result for result in results if result]

    return results


def search_interface_configuration(iface, results):
    iface = iface.lower()
    interface_search_results = []

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
    #hosts = ['SFD-C319-SPN-SN2700-01', 'SFD-C320-BLF-S4048-01']
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

    cit = {
        'hostname': [],
        'interface': [],
        'peerIf': [],
        'clagId': [],
        'operstate': [],
        'status': []
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
            #print(json.dumps(entry['output']['clagIntfs'], indent=4))
            alive = entry['output']['status']['peerAlive']
            role = entry['output']['status']['ourRole']
            vxlan_anycast_ip = entry['output']['status'].get('vxlanAnycast', 'not configured')
            backup_active = entry['output']['status'].get('backupActive', 'not configured')
            backup_ip = entry['output']['status'].get('backupIp', 'not configured')
            clag_interfaces = entry['output']['clagIntfs']

            ce['hostname'] = hostname
            ce['alive'] = alive
            ce['role'] = role
            ce['vxlan anycast ip'] = vxlan_anycast_ip
            ce['backup active'] = backup_active
            ce['backup IP'] = backup_ip

            tr['role'].append(role)
            tr['vxlan anycast ip'].append(vxlan_anycast_ip)
            tr['backup active'].append(backup_active)
            tr['backup IP'].append(backup_ip)

            if alive:
                tr['status'].append('up')
            else:
                tr['status'].append(bcolors.FAIL + 'down' + bcolors.ENDC)
                down_peers.append(ce)

            # get individual clag interfaces
            for k, v in clag_interfaces.items():
                cit['hostname'].append(hostname)
                cit['interface'].append(k),
                cit['clagId'].append(v.get('clagId'))
                cit['operstate'].append(v.get('operstate'))
                cit['peerIf'].append(v.get('peerIf'))
                cit['status'].append(v.get('status'))

        else:
            ce['hostname'] = hostname
            ce['alive'] = 'not configured'
            ce['role'] = '-'
            ce['vxlan anycast ip'] = 'not configured'
            ce['backup active'] = '-'
            ce['backup IP'] = '-'
            down_peers.append(ce)

            tr['status'].append('not configured')
            tr['role'].append('-')
            tr['vxlan anycast ip'].append('not configured')
            tr['backup active'].append('-')
            tr['backup IP'].append('-')

    overall_mlag_status_table = tabulate(tr,
                               headers="keys", tablefmt="simple")
    overall_clag_interfaces_table = tabulate(cit,
                               headers="keys", tablefmt="simple")

    return dict(
        down_peers=down_peers,
        overall_mlag_status_table=overall_mlag_status_table,
        overall_clag_interfaces_table=overall_clag_interfaces_table
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


    creds = get_credentials_by_key(VENDOR)
    hosts = [host for host in INVENTORY_HOSTS][0:1]

    # device = CumulusDevice(
    #     hostname=INVENTORY_HOSTS['CSS1A-106-LEF-01'],
    #     #hostname=INVENTORY_HOSTS['CSS1A-106-LEF-01'],
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
                results = search_interface_configuration(
                    args.iface,
                    multithread_command('show interfaces configuration',
                                        hosts))
                print(results)
        elif args.cumulus_crawler == 'check':
            if args.check_bgp:
                #results = check_bgp_neighbors(['CSS1A-109-LEF-03', 'CSS1A-109-LEF-04'])
                results = check_bgp_neighbors(INVENTORY_HOSTS)
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
                clag_status = check_clag(INVENTORY_HOSTS)

                if args.verbose:
                    print(f"\n{clag_status['overall_clag_interfaces_table']}")
                    print("\nSwitch CLAG Status: ")
                    print(f"\n{clag_status['overall_mlag_status_table']}", "\n")
                else:
                    if clag_status['down_peers']:
                        for dp in clag_status['down_peers']:
                            print("\n", f"{bcolors.FAIL} --> {dp['hostname']} failed check because system clag (mlag) is down. "
                                  f"The VXLAN Anycast IP is: {dp['vxlan anycast ip']} {bcolors.ENDC}", "\n")
                        print("\n")


                 

            else:
                print("Please enter argument. Use -h for help.")