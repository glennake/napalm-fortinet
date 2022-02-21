# napalm-fortinet

[NAPALM](https://napalm-automation.net/) driver for Fortinet networking
equipment.

## Supported devices

Fortinet FortiOS devices should be supported. The code has been written and tested
against FortiGate firewalls.

Please open a GitHub issue if you find an problems.

## Supported Getters

| Getter                    | Support  |
|---------------------------|----------|
| get_arp_table             |  ❌      |
| get_bgp_config            |  ❌      |
| get_bgp_neighbors         |  ❌      |
| get_bgp_neighbors_detail  |  ❌      |
| get_config                |  ❌      |
| get_environment           |  ❌      |
| get_facts                 |  ✅      |
| get_firewall_policies     |  ❌      |
| get_interfaces            |  ❌      |
| get_interfaces_counters   |  ❌      |
| get_interfaces_ip         |  ❌      |
| get_ipv6_neighbors_table  |  ❌      |
| get_lldp_neighbors        |  ❌      |
| get_lldp_neighbors_detail |  ❌      |
| get_mac_address_table     |  ❌      |
| get_network_instances     |  ❌      |
| get_ntp_peers             |  ❌      |
| get_ntp_servers           |  ❌      |
| get_ntp_stats             |  ❌      |
| get_optics                |  ❌      |
| get_probes_config         |  ❌      |
| get_probes_results        |  ❌      |
| get_route_to              |  ❌      |
| get_snmp_information      |  ❌      |
| get_users                 |  ❌      |
| is_alive                  |  ✅      |
| ping                      |  ❌      |
| traceroute                |  ❌      |

## Usage

Install napalm via pip:
```
$ pip install napalm
```

Install napalm-fortinet via pip:
```
$ pip install git+https://github.com/glennake/napalm-fortinet.git
```

Test functionality:
```
#!/usr/bin/env python3
# Simple napalm-fortinet test

from napalm import get_network_driver

driver = get_network_driver("fortinet")

device = driver(
    "1.2.3.4",
    "admin",
    "password",
    optional_args={"port": 22},
)

device.open()

facts = device.get_facts()

device.close()

print(facts)
```

See the full [NAPALM Docs](https://napalm.readthedocs.io/en/latest/index.html) for more detailed instructions.

## License

Apache License, Version 2.0
