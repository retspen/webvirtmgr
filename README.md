# WebVirtMgr panel - v2.2.1

* Created WebVirtMgr noVNC server (support open many vnc connection - item 6)
* Package novnc not need - $ apt-get autoremove novnc (Ubuntu)

## 1. Introduction

WebVirtMgr is a libvirt-based Web interface for managing virtual machines. It allows you to create and configure new domains, and adjust a domain's resource allocation. A VNC viewer presents a full graphical console to the guest domain. KVM is currently the only hypervisor supported.

### Technology:

The application logic is written in Python & Django. The LIBVIRT Python bindings are used to interacting with the underlying hypervisor.

### License

WebVirtMgr is licensed under the Apache Licence, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0.html).

## 2. Installation

### Fedora 17 and above

Run:

    $ su -c 'yum -y install git python-pip python-virtinst httpd mod_python mod_wsgi numpy python-websockify'
    $ su -c 'python-pip install Django==1.4.5'

### CentOS 6.2, RedHat 6.2 and above

Run:

    $ su -c 'yum -y install http://dl.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm'
    $ su -c 'yum -y install git python-pip python-virtinst httpd mod_python mod_wsgi numpy python-websockify'
    $ su -c 'python-pip install Django==1.4.5'

### Ubuntu 12.04 and above

Run:

    $ sudo apt-get install git python-pip virtinst apache2 libapache2-mod-python libapache2-mod-wsgi python-novnc python-numpy
    $ sudo pip install Django==1.4.5

## 3. Setup

Run: 
    
    $ git clone git://github.com/retspen/webvirtmgr.git
    $ cd webvirtmgr
    $ ./manage.py syncdb
    
Or install <a href="https://github.com/euforia/webvirtmgr">RPM</a> (CentOS, RHEL, Fedora, Oracle Linux 6)  

Enter the user information:

    You just installed Django's auth system, which means you don't have any superusers defined.
    Would you like to create one now? (yes/no): yes (Put: yes)
    Username (Leave blank to use 'admin'): admin (Put: your username or login)
    E-mail address: username@domain.local (Put: your email)
    Password: xxxxxx (Put: your password)
    Password (again): xxxxxx (Put: confirm password)
    Superuser created successfully.

Add pre-installed flavors:
    
    $ ./manage.py loaddata conf/flavor.json

Run app for test:

    $ ./manage.py runserver 0:8000
    
Enter in your browser:
    
    http://x.x.x.x:8000 (x.x.x.x - your server IP address )

## 4. Setup Web (Choose only one method: Virtual Host or WSGI)

###1. Virtual Host 

Add file webvirtmgr.conf in conf.d directory (Ubuntu: "/etc/apache2/conf.d" or RedHat,Fedora,CentOS: "/etc/httpd/conf.d"):

    <VirtualHost *:80>
        ServerAdmin webmaster@dummy-host.example.com
        ServerName dummy-host.example.com

        SetHandler python-program
        PythonHandler django.core.handlers.modpython
        SetEnv DJANGO_SETTINGS_MODULE webvirtmgr.settings
        PythonOption django.root /webvirtmgr
        PythonDebug On
        PythonPath "['/var/www/webvirtmgr'] + sys.path"
        
        ErrorLog ${APACHE_LOG_DIR}/webvirtmgr-error_log
        CustomLog ${APACHE_LOG_DIR}/webvirtmgr-access_log common
    </VirtualHost>

Copy the folder and change owner (Ubuntu: "www-data:www-data", Fedora, Redhat, CentOS: "apache:apache"):

    $ sudo cp -r webvirtmgr /var/www/
    $ sudo chown -R www-data:www-data /var/www/webvirtmgr

Reload apache:
    
    $ sudo service apache2 reload
    
###2. WSGI

Add file webvirtmgr.conf in conf.d directory (Ubuntu: "/etc/apache2/conf.d" or RedHat,Fedora,CentOS: "/etc/httpd/conf.d"):

    WSGIScriptAlias / /var/www/webvirtmgr/webvirtmgr/wsgi.py
    WSGIPythonPath /var/www/webvirtmgr/

    Alias /static /var/www/webvirtmgr/static/
    Alias /media /var/www/webvirtmgr/media/

    <Directory /var/www/webvirtmgr/webvirtmgr>
        <Files wsgi.py>
            Order deny,allow
            Allow from all
        </Files>
    </Directory>

Reload apache:
    
    $ sudo service apache2 reload

## 5. Setup Websoket proxy (noVNC)

### CentOS, RedHat

Run:

    $ sudo cp conf/initd/webvirtmgr-novnc-redhat /etc/init.d/webvirtmgr-novnc
    $ sudo service webvirtmgr-novnc start

### Ubuntu

Run: 

    $ sudo cp conf/initd/webvirtmgr-novnc-ubuntu /etc/init.d/webvirtmgr-novnc
    $ sudo service webvirtmgr-novnc start

## 6. Gunicorn and Runit (Only for geeks)

Install gunicorn:

    $ sudo pip install gunicorn

Add line <code>'gunicorn',</code> in file settings.py:

    INSTALLED_APPS = (
    ...
    'gunicorn',
    )

Runit script for webvirtmgr (/etc/sv/webvirtmgr/run):

    #!/bin/bash

    GUNICORN=/usr/local/bin/gunicorn
    ROOT=/var/www/webvirtmgr
    PID=/var/run/gunicorn.pid

    APP=webvirtmgr.wsgi:application

    if [ -f $PID ]; then
       rm $PID
    fi

    cd $ROOT
    exec $GUNICORN -c $ROOT/conf/gunicorn.conf.py --pid $PID $APP
    
And then install and setup nginx.

## 7. Update

### Read this README.md check settings (maybe something has changed) and then:

    $ cd /path to/webvirtmgr
    $ git pull

Support: support@webvirtmgr.net or <a href="https://github.com/retspen/webvirtmgr/issues">GitHub Issues</a>
