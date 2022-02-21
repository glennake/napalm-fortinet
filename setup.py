"""setup.py file."""

import uuid

from setuptools import setup, find_packages

__author__ = "David Barroso <dbarrosop@dravetech.com>"

with open("requirements.txt", "r") as fs:
    reqs = [r for r in fs.read().splitlines() if (len(r) > 0 and not r.startswith("#"))]

setup(
    name="napalm-fortinet",
    version="0.1.0",
    packages=find_packages(),
    author="David Barroso",
    author_email="dbarrosop@dravetech.com",
    description="Network Automation and Programmability Abstraction Layer with Multivendor support",
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
    install_requires=reqs,
)
