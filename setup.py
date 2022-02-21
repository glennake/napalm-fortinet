"""setup.py file."""

import uuid

from setuptools import setup, find_packages

try:
    # pip >=20
    from pip._internal.network.session import PipSession
    from pip._internal.req import parse_requirements
except ImportError:
    try:
        # 10.0.0 <= pip <= 19.3.1
        from pip._internal.download import PipSession
        from pip._internal.req import parse_requirements
    except ImportError:
        # pip <= 9.0.3
        from pip.download import PipSession
        from pip.req import parse_requirements

__author__ = "Glenn Akester <glennake@live.co.uk>"

with open("requirements.txt", "r") as fs:
    reqs = [r for r in fs.read().splitlines() if (len(r) > 0 and not r.startswith("#"))]

setup(
    name="napalm-fortinet",
    version="0.1.0",
    packages=find_packages(),
    author="Glenn Akester",
    author_email="glennake@live.co.uk",
    description="Network Automation and Programmability Abstraction Layer (NAPALM) Fortinet Driver",
    long_description="Driver to enable NAPALM network automation support for Fortinet devices.",
    classifiers=[
        "Topic :: Utilities",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
    ],
    url="https://github.com/napalm-automation/napalm-fortinet",
    include_package_data=True,
    zip_safe=False,
    install_requires=reqs,
)
