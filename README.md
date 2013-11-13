# WebVirtMgr panel - v3.4.3

### <a href="https://github.com/retspen/webvirtmgr/wiki/Screenshots">Screenshots</a>

Warning: Upgrade from v2 not support!!!

* Move to Django-1.5.x
* Move to Bootstrap-3.0
* Fix many bugs
* Add gentoo init scripts (Thanks: Joachim Langenbach)
* Add function convert images
* Rebuild VNC fanctional
* Fix create or change VNC password if VM created in console

Big Thanks: Alex Kuksenko (<a href="https://github.com/retif">Github</a>)
* Add support for more than one HDD
* Add support for multi networks
* Add support for hardware CPU (host cpu instead of virtual)
* View and Edit XML Virtual Machine
* Add bridge device in Network Pool
* Add create image RAW, QCOW, QCOW2 formats

## 1. Introduction

WebVirtMgr is a libvirt-based Web interface for managing virtual machines. It allows you to create and configure new domains, and adjust a domain's resource allocation. A VNC viewer presents a full graphical console to the guest domain. KVM is currently the only hypervisor supported.

### Technology:

The application logic is written in Python & Django. The LIBVIRT Python bindings are used to interacting with the underlying hypervisor.

### License

WebVirtMgr is licensed under the Apache Licence, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0.html).

## 2. Installation

### Fedora 17 and above

Run:

    $ su -c 'yum -y install git python-pip libvirt-python libxml2-python httpd mod_wsgi python-websockify'
    $ su -c 'python-pip install Django==1.5.4'

### CentOS 6.2, RedHat 6.2 and above

Run:

    $ su -c 'yum -y install http://dl.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm'
    $ su -c 'yum -y install git python-pip libvirt-python libxml2-python httpd mod_wsgi python-websockify'
    $ su -c 'python-pip install Django==1.5.4'

### Ubuntu 12.04 and above

Run:

    $ sudo apt-get install git python-pip python-libvirt python-libxml2 apache2 libapache2-mod-wsgi novnc
    $ sudo ln -s /var/run/apache2 /etc/apache2/run
    $ sudo pip install Django==1.5.4

## 3. Setup

Run: 
    
    $ git clone git://github.com/retspen/webvirtmgr.git -b nestene
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

## 4. Setup Apache

Copy the folder and change owner (Ubuntu: "www-data.", Fedora, Redhat, CentOS: "apache."):

    $ cd ..
    $ sudo cp -r webvirtmgr /var/www/
    $ sudo chown -R apache. /var/www/webvirtmgr

Add file webvirtmgr.conf in conf.d directory (Ubuntu: "/etc/apache2/conf.d" or RedHat,Fedora,CentOS: "/etc/httpd/conf.d"):

Fedora, Redhat, CentOS:

    WSGISocketPrefix run/wsgi
    <VirtualHost *:80>
        ServerAdmin webmaster@dummy-host.example.com
        ServerName dummy-host.example.com

        WSGIDaemonProcess webvirtmgr display-name=%{GROUP} python-path=/var/www/webvirtmgr
        WSGIProcessGroup webvirtmgr
        WSGIScriptAlias / /var/www/webvirtmgr/webvirtmgr/wsgi.py

        Alias /static /var/www/webvirtmgr/static/
        Alias /media /var/www/webvirtmgr/media/

        <Directory /var/www/webvirtmgr/webvirtmgr>
            <Files wsgi.py>
                Order deny,allow
                Allow from all
            </Files>
        </Directory>

        CustomLog logs/webvirtmgr-access_log common
        ErrorLog logs/webvirtmgr-error_log
    </VirtualHost>

Ubuntu:

    WSGISocketPrefix run/wsgi
    <VirtualHost *:80>
        ServerAdmin webmaster@dummy-host.example.com
        ServerName dummy-host.example.com

        WSGIDaemonProcess webvirtmgr display-name=%{GROUP} python-path=/var/www/webvirtmgr
        WSGIProcessGroup webvirtmgr
        WSGIScriptAlias / /var/www/webvirtmgr/webvirtmgr/wsgi.py

        Alias /static /var/www/webvirtmgr/static/
        Alias /media /var/www/webvirtmgr/media/

        <Directory /var/www/webvirtmgr/webvirtmgr>
            <Files wsgi.py>
                Order deny,allow
                Allow from all
            </Files>
        </Directory>

        CustomLog ${APACHE_LOG_DIR}/webvirtmgr-access_log common
        ErrorLog ${APACHE_LOG_DIR}/webvirtmgr-error_log
    </VirtualHost>


Reload apache (Ubuntu: "apache2", Fedora, Redhat, CentOS: "httpd"):

    $ sudo service httpd reload

## 5. Setup Websoket proxy (noVNC)

### CentOS, RedHat, Fedora

Run:

    $ sudo cp /var/www/webvirtmgr/conf/initd/webvirtmgr-novnc-redhat /etc/init.d/webvirtmgr-novnc
    $ sudo service webvirtmgr-novnc start
    $ sudo chkconfig webvirtmgr-novnc on

### Ubuntu

Run: 

    $ sudo service novnc stop
    $ sudo update-rc.d -f novnc remove
    $ sudo cp /var/www/webvirtmgr/conf/initd/webvirtmgr-novnc-ubuntu /etc/init.d/webvirtmgr-novnc
    $ sudo service webvirtmgr-novnc start
    $ sudo update-rc.d webvirtmgr-novnc defaults

## 6. Gunicorn and Supervisor (Only for geeks)

Install gunicorn:

    $ sudo pip install gunicorn

Add line <code>'gunicorn',</code> in file settings.py:

    INSTALLED_APPS = (
    ...
    'gunicorn',
    )

Supervisor settings for webvirtmgr (/etc/supervisor.conf):

    [program:webvirtmgr]
    command=/var/www/webvirtmgr/venv/bin/python /var/www/webvirtmgr/manage.py run_gunicorn -c /var/www/webvirtmgr/conf/gunicorn.conf.py
    directory=/var/www/webvirtmgr
    autostart=true
    autorestart=true
    stdout_logfile=/var/log/supervisor/webvirtmgr.log
    redirect_stderr=true
    
And then install and setup nginx for static files.

## 7. Update

### Read this README.md check settings (maybe something has changed) and then:

    $ cd /path to/webvirtmgr
    $ git pull

## 8. Debug

If have error or not run panel (only for DEBUG or DEVELOP):

    $ ./manage.py runserver 0:8000

Enter in your browser:

    http://x.x.x.x:8000 (x.x.x.x - your server IP address )

Support: <a href="https://github.com/retspen/webvirtmgr/issues">GitHub Issues</a>

Powered by

<img src=http://www.jetbrains.com/img/logos/pycharm_logo.gif>
