import paramiko
import json
from utils.parse_clitable import parse_output
from utils.logger import logger
from paramiko import ssh_exception as pexception
from exceptions import CommandNotSupported

TEMPLATE_DIR = './templates/'
PLATFORM = 'cumulus_clos'


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

            #print("SSH connection established to {0}".format(self.hostname))
            logger.info(f"SSH Connection established to {self.hostname}")
            self.session = ssh_client

        except (pexception.BadHostKeyException,
                pexception.AuthenticationException,
                pexception.SSHException,
                pexception.socket.error) as e:
            logger.error(f"{e}: Error connecting to {self.hostname}")
            raise ConnectionError

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

            _, stdout, stderr = self.session.exec_command(command, timeout=5)
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

        # print(structured_output)

        #structured_output = INTERFACES_TEST

        for entry in structured_output:
            iface = {}

            # convert bond-slave interfaces to list
            if entry.get('bond_slaves'):
                entry['bond_slaves'] = entry['bond_slaves'].split()

            # convert bridge port members to list
            if entry.get('bridge_ports'):
                entry['bridge_ports'] = entry['bridge_ports'].split()

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
