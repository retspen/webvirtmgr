# Applince WebVirtMgr for personal use

## 1. Introduction

WebVirtMgr is a libvirt-based Web interface for managing virtual machines. It allows you to create and configure new domains, and adjust a domain's resource allocation. A VNC viewer over a SSH tunnel presents a full graphical console to the guest domain. KVM is currently the only hypervisor supported

### Technology:

The application logic is written in Python & Django. The LIBVIRT Python bindings are used to interacting with the underlying hypervisor.


## 2. Installation

### Fedora 14 and above

Run:

    # yum install git Django python-virtinst httpd mod_python

### Ubuntu 10.04 and above

Run:

    $ sudo apt-get install git python-django virtinst apache2 libapache2-mod-python

### CentOS, RedHat (6.x)

Run:

    # yum install wget git python-virtinst httpd mod_wsgi
    # wget https://www.djangoproject.com/download/1.3.1/tarball/
    # tar -zxf Django-1.3.1.tar.gz
    # cd Django-1.3.1
    # python setup.py install

## 3. Setup

Run: 

    $ git clone git://github.com/retspen/webvirtmgr.git
    $ cd webvirtmgr
    $ ./manage.py syncdb

Enter the user information:

    You just installed Django's auth system, which means you don't have any superusers defined.
    Would you like to create one now? (yes/no): yes (Put: yes)
    Username (Leave blank to use 'admin'): admin (Put: your username or login)
    E-mail address: username@domain.local (Put: your email)
    Password: xxxxxx (Put: your password)
    Password (again): xxxxxx (Put: confirm password)
    Superuser created successfully.

Run app for test:

    $ ./manage.py runserver x.x.x.x:8080 (x.x.x.x - your IP address server)

## 4. Setup your apache for Django.