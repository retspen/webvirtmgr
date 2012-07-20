# Applince WebVirtMgr for personal use

## 1. Introduction

WebVirtMgr is a libvirt-based Web interface for managing virtual machines. It allows you to create and configure new domains, and adjust a domain's resource allocation. A VNC viewer over a SSH tunnel presents a full graphical console to the guest domain. KVM is currently the only hypervisor supported.

### Technology:

The application logic is written in Python & Django. The LIBVIRT Python bindings are used to interacting with the underlying hypervisor.


## 2. Installation

### Fedora 14 and above

Run:

    $ su -c 'yum install git Django python-virtinst httpd mod_python'

### Ubuntu 10.04 and above

Run:

    $ sudo apt-get install git python-django virtinst apache2 libapache2-mod-python

### CentOS, RedHat (6.x)

Run:

    $ su -c 'rpm -Uvh http://dl.fedoraproject.org/pub/epel/6/i386/epel-release-6-7.noarch.rpm'
    $ su -c 'yum install git python-virtinst httpd mod_wsgi Django'

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

    $ ./manage.py runserver x.x.x.x:8000 (x.x.x.x - your IP address server)
    
Enter in your browser:
    
    http://x.x.x.x:8000 (x.x.x.x - your IP address server)

## 4. Setup apache for Django.

Add virtual host in apache:

    <VirtualHost *:80>
        ServerAdmin webmaster@dummy-host.example.com
        ServerName dummy-host.example.com

        SetHandler python-program
        PythonHandler django.core.handlers.modpython
        SetEnv DJANGO_SETTINGS_MODULE webvirtmgr.settings
        PythonOption django.root /webvirtmgr
        PythonDebug On
        PythonPath "['/var/www'] + sys.path"
        
        ErrorLog logs/webvirtmgr-error_log
        CustomLog logs/webvirtmgr-access_log common
    </VirtualHost>
    
