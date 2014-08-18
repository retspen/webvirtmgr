"""
=================
WebVirtMgr panel
=================

Introduction
------------

WebVirtMgr is a libvirt-based Web interface for managing virtual machines. It allows you to create and configure new domains, and adjust a domain's resource allocation. A VNC viewer presents a full graphical console to the guest domain. KVM is currently the only hypervisor supported.

Technology:
***********

The application logic is written in Python & Django. The LIBVIRT Python bindings are used to interacting with the underlying hypervisor.

Installation (Only web panel)
-----------------------------

`Install WebVirtMgr <https://github.com/retspen/webvirtmgr/wiki/Install-WebVirtMgr>`_


Setup host server (Server for VM's)
-----------------------------------

`Setup Host Server <https://github.com/retspen/webvirtmgr/wiki/Setup-Host-Server>`_

Links
------
- `Website <https://github.com/retspen/webvirtmgr>`_
- `Screenshots <https://github.com/retspen/webvirtmgr/wiki/Screenshots>`_
- `Wiki <https://github.com/retspen/webvirtmgr/wiki>`_
"""

import os
from setuptools import setup, find_packages


__version__ = "4.8.7"


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    # package name in pypi
    name='webvirtmgr',
    # extract version from module.
    version=__version__,
    description="WebVirtMgr panel for manage virtual machine",
    long_description=__doc__,
    classifiers=[],
    keywords='',
    author='Anatoliy Guskov',
    author_email='anatoliy.guskov@gmail.com',
    url='http://github.com/retspen/webvirtmgr',
    license='Apache Licence, Version 2.0.',
    # include all packages in the egg, except the test package.
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    # for avoiding conflict have one namespace for all webvirtmgr related eggs.
    namespace_packages=[],
    # include non python files
    include_package_data=True,
    zip_safe=False,
    # specify dependencies
    install_requires=[
        'setuptools',
        'django>=1.5.5',
        'gunicorn>=18.0',
        'lockfile>=0.9',
    ],
    # mark test target to require extras.
    extras_require={
        'ldap': ["django-auth-ldap>=1.2.0"]
    },
    scripts=[
        'manage.py',
    ],
)
