# napalm-fortinet

[NAPALM](https://napalm-automation.net/) driver for Fortinet networking
equipment.

Supported devices
=================

Fortinet FortiOS devices should be supported. The code has been written and tested
against FortiGate firewalls.

Please open a GitHub issue if you find an problems.

Development status
==================

The driver is functional and can be used to poll status information:

* WIP

How to use
==========

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

import json
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

License
=======

Apache License, Version 2.0
