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

    def is_alive(self):
        """ Returns a flag with the state of the connection."""
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
            +int(uptime_dict["m"]) * 60
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
