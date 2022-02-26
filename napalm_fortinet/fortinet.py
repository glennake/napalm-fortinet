# -*- coding: utf-8 -*-
# Copyright 2022 Glenn Akester. All rights reserved.
#
# The contents of this file are licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

"""
Napalm driver for Fortinet.

Read https://napalm.readthedocs.io for more information.
"""
from __future__ import print_function
from __future__ import unicode_literals

import ipaddress
import re
import socket

from netmiko import ConnectHandler

from napalm.base.base import NetworkDriver

from napalm.base.exceptions import (
    ConnectionClosedException,
    ConnectionException,
    SessionLockedException,
    MergeConfigException,
    ReplaceConfigException,
    CommandErrorException,
)
from paramiko import AgentKey


class FortinetDriver(NetworkDriver):
    """Napalm driver for Fortinet."""

    def __init__(self, hostname, username, password, timeout=60, optional_args=None):
        """Constructor."""
        self.device = None
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout

        if optional_args is None:
            optional_args = {}

        self.transport = optional_args.get("transport", "ssh")

        # Netmiko possible arguments
        netmiko_argument_map = {
            "port": None,
            "secret": "",
            "verbose": False,
            "keepalive": 30,
            "global_delay_factor": 1,
            "use_keys": False,
            "key_file": None,
            "ssh_strict": False,
            "system_host_keys": False,
            "alt_host_keys": False,
            "alt_key_file": "",
            "ssh_config_file": None,
        }

        # Build dict of any optional Netmiko args
        self.netmiko_optional_args = {}
        for k, v in netmiko_argument_map.items():
            try:
                self.netmiko_optional_args[k] = optional_args[k]
            except KeyError:
                pass
        self.global_delay_factor = optional_args.get("global_delay_factor", 1)

        # Set the default port if not set
        default_port = {"ssh": 22}
        self.netmiko_optional_args.setdefault("port", default_port[self.transport])

    def open(self):
        """Open connection to the device."""
        device_type = "fortinet_ssh"
        self.device = self._netmiko_open(
            device_type, netmiko_optional_args=self.netmiko_optional_args
        )

    def close(self):
        """Close connection to the device."""
        self.device.disconnect()

    def _send_command(self, command):
        """Wrapper for self.device.send.command().
        If command is a list will iterate through commands until valid command.
        """
        try:
            if isinstance(command, list):
                for cmd in command:
                    output = self.device.send_command(cmd)
                    if "Invalid input: " not in output:
                        break
            else:
                output = self.device.send_command(command)
            return output
        except (socket.error, EOFError) as e:
            raise ConnectionClosedException(str(e))

    def get_arp_table(self):
        """Get arp table for the device."""
        sys_arp = self._send_command("get system arp")

        arps = []

        for line in sys_arp.splitlines()[1:]:
            line_vals = line.split()
            arp_entry = {
                "age": float(line_vals[1]),
                "interface": str(line_vals[3]),
                "ip": str(line_vals[0]),
                "mac": str(line_vals[2]),
            }
            arps.append(arp_entry)

        return arps

    def get_bgp_config(self, group="", neighbor=""):
        """Get bgp config for the device.
            :param group='':
            :param neighbor='':
        """

        bgp_config = {}
        bgp_config["_"] = {
            "apply_groups": [],
            "description": "",
            "export_policy": "",
            "import_policy": "",
            "local_address": "",
            "local_as": 0,
            "multihop_ttl": 0,
            "multipath": False,
            "neighbors": {},
            "prefix_limit": {
                "inet": {
                    "unicast": {"limit": 0, "teardown": {"threshold": 0, "timeout": 0},}
                }
            },
            "remote_as": 0,
            "remove_private_as": False,
            "type": "",
        }

        show_router_bgp = self._send_command("show full-configuration router bgp")

        re_neighbors = re.search(
            "^    config neighbor\n(?:.*?)\n    end$",
            show_router_bgp,
            re.MULTILINE | re.DOTALL,
        )

        neighbors = re_neighbors.group(0).strip()

        for n in re.finditer(
            '^        edit "?(.*?)"?\n(?:.*?)?\n?        next$',
            neighbors,
            re.MULTILINE | re.DOTALL,
        ):

            neighbor_ip = n.group(1)

            bgp_config["_"]["neighbors"][neighbor_ip] = {
                "authentication_key": "",
                "description": "",
                "export_policy": "",
                "import_policy": "",
                "local_address": "",
                "local_as": 0,
                "nhs": False,
                "prefix_limit": {
                    "inet": {
                        "unicast": {
                            "limit": 0,
                            "teardown": {"threshold": 0, "timeout": 0},
                        }
                    }
                },
                "remote_as": 0,
                "route_reflector_client": False,
            }

        return bgp_config

    def get_bgp_neighbors(self):
        """Get bgp neighbors for the device."""
        pass

    def get_bgp_neighbors_detail(self):
        """Get bgp neighbors with details for the device."""
        pass

    def get_config(self, retrieve="all"):
        """Get config for the device.
            :param retrieve='':
        """
        show_config = self._send_command("show")

        configs = {
            "candidate": "",
            "running": "",
            "startup": "",
        }

        if retrieve in ["candidate", "all"]:
            configs["candidate"] = ""
        if retrieve in ["running", "all"]:
            configs["running"] = show_config
        if retrieve in ["startup", "all"]:
            configs["startup"] = show_config

        return configs

    def get_environment(self):
        """Get environmentals for the device."""
        pass

    def get_facts(self):
        """Get facts for the device."""
        # Default values
        vendor = "Fortinet"
        uptime = -1
        (serial_number, fqdn, os_version, hostname, model, interface_list) = (
            None,
            None,
            None,
            None,
            None,
            [],
        )

        sys_status = self._send_command("get system status")
        sys_perf_uptime = self._send_command(
            "get system performance status | grep Uptime"
        )
        sys_dns_domain = self._send_command("get system dns | grep domain")
        sys_intf_eqeq = self._send_command("get system interface | grep ==")

        uptime_formatted = (
            sys_perf_uptime.replace("Uptime:", "")
            .replace(" days,  ", ":")
            .replace(" hours,  ", ":")
            .replace(" minutes", ":")
            .strip()
        )
        uptime_dict = dict(zip(("d", "h", "m"), uptime_formatted.split(":")))
        uptime = (
            int(uptime_dict["m"]) * 60
            + int(uptime_dict["h"]) * 60 * 60
            + int(uptime_dict["d"]) * 60 * 60 * 24
        )

        for line in sys_status.splitlines():
            if "Version: " in line:
                line_vals = line.split(": ")[1].split(" ")
                model = line_vals[0]
                os_version = line_vals[1].split(",")[0].lstrip("v")
            if "Serial-Number: " in line:
                serial_number = line.split(" ")[1]
            if "Hostname: " in line:
                hostname = line.split(" ")[1]

        domain = sys_dns_domain.strip().split(":")
        if len(domain) > 1 and domain[1]:
            fqdn = hostname + "." + domain[1].lstrip().strip().replace('"', "")
        else:
            fqdn = hostname

        for line in sys_intf_eqeq.splitlines():
            interface_list.append(line.lstrip("== [ ").strip(" ]"))

        facts = {
            "os_version": os_version,
            "uptime": uptime,
            "interface_list": interface_list,
            "vendor": vendor,
            "serial_number": serial_number,
            "model": model,
            "hostname": hostname,
            "fqdn": fqdn,
        }

        return facts

    def get_firewall_policies(self):
        """Get firewall policies for the device."""
        pass

    def get_interfaces_counters(self):
        """Get interface counters for the device."""
        pass

    def get_interfaces_ip(self):
        """Get interface IP addresses for the device."""
        ip_addr_list = self._send_command("diagnose ip address list")
        ipv6_addr_list = self._send_command("diagnose ipv6 address list")

        intfs_ip = {}

        for line in ip_addr_list.splitlines():
            ipv4_vals = line.split(" ")

            intf_name = ipv4_vals[2].split("=")[1]
            if intf_name not in intfs_ip:
                intfs_ip[intf_name] = {}

            if "ipv4" not in intfs_ip[intf_name]:
                intfs_ip[intf_name]["ipv4"] = {}

            ipv4_addr_cidr = ipv4_vals[0].split("->")[1]
            ipv4_network = ipaddress.IPv4Interface(ipv4_addr_cidr)

            ipv4_addr = str(ipv4_network.ip)
            ipv4_prefix = int(ipv4_network.network.prefixlen)

            intfs_ip[intf_name]["ipv4"][ipv4_addr] = {}
            intfs_ip[intf_name]["ipv4"][ipv4_addr]["prefix_length"] = ipv4_prefix

        for line in ipv6_addr_list.splitlines():
            ipv6_vals = line.split(" ")

            intf_name = ipv6_vals[1].split("=")[1]
            if intf_name not in intfs_ip:
                intfs_ip[intf_name] = {}

            if "ipv6" not in intfs_ip[intf_name]:
                intfs_ip[intf_name]["ipv6"] = {}

            ipv6_addr = str(ipv6_vals[5].split("=")[1])
            ipv6_prefix = int(ipv6_vals[4].split("=")[1])

            intfs_ip[intf_name]["ipv6"][ipv6_addr] = {}
            intfs_ip[intf_name]["ipv6"][ipv6_addr]["prefix_length"] = ipv6_prefix

        return intfs_ip

    def get_ipv6_neighbors_table(self):
        """Get IPv6 neighbors for the device."""
        pass

    def get_lldp_neighbors(self):
        """Get LLDP neighbors for the device."""
        pass

    def get_lldp_neighbors_detail(self):
        """Get LLDP neighbors with details for the device."""
        pass

    def get_mac_address_table(self):
        """Get MAC address table for the device."""
        pass

    def get_network_instances(self):
        """Get network instances for the device."""
        pass

    def get_ntp_peers(self):
        """Get NTP peers for the device."""
        pass

    def get_ntp_servers(self):
        """Get NTP servers for the device."""
        pass

    def get_ntp_stats(self):
        """Get NTP statistics for the device."""
        pass

    def get_optics(self):
        """Get optical transceiver state and statistics for the device."""
        pass

    def get_probes_config(self):
        """Get network probes config for the device."""
        pass

    def get_probes_results(self):
        """Get network probs statistics for the device."""
        pass

    def get_route_to(self):
        """Get route for the device."""
        pass

    def get_snmp_information(self):
        """Get SNMP information for the device."""
        pass

    def get_users(self):
        """Get users for the device."""
        pass

    def is_alive(self):
        """Get connection alive status for the device."""
        if self.device is None:
            return {"is_alive": False}
        try:
            # Try sending ASCII null byte to maintain the SSH connection alive
            null = chr(0)
            self.device.write_channel(null)
            return {"is_alive": self.device.remote_conn.transport.is_active()}
        except (socket.error, EOFError, OSError, AttributeError):
            # If unable to send, we can tell for sure that the connection is unusable
            return {"is_alive": False}

    def ping(self):
        """Execute ping from the device."""
        pass

    def traceroute(self):
        """Execute traceroute from the device."""
        pass
