# WebVirtMgr panel - v3

Warning: Upgrade from v2 not support!!!

* Move to Django-1.5.x
* Move to Bootstrap-3.0
* Fix many bugs
* Add gentoo init scripts (Thanks: Joachim Langenbach)

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
    $ su -c 'python-pip install Django==1.5.2'

### CentOS 6.2, RedHat 6.2 and above

Run:

    $ su -c 'yum -y install http://dl.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm'
    $ su -c 'yum -y install git python-pip libvirt-python libxml2-python httpd mod_wsgi python-websockify'
    $ su -c 'python-pip install Django==1.5.2'

### Ubuntu 12.04 and above

Run:

    $ sudo apt-get install git python-pip python-libvirt python-libxml2 apache2 libapache2-mod-wsgi novnc
    $ sudo pip install Django==1.5.2

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

## 4. Setup Web (Autostart panel)

Add file webvirtmgr.conf in conf.d directory (Ubuntu: "/etc/apache2/conf.d" or RedHat,Fedora,CentOS: "/etc/httpd/conf.d"):

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

Copy the folder and change owner (Ubuntu: "www-data:www-data", Fedora, Redhat, CentOS: "apache:apache"):

    $ sudo cp -r webvirtmgr /var/www/
    $ sudo chown -R www-data:www-data /var/www/webvirtmgr

Reload apache:
    
    $ sudo service apache2 reload

## 5. Setup Websoket proxy (noVNC)

### CentOS, RedHat, Fedora

Run:

    $ sudo cp conf/initd/webvirtmgr-novnc-redhat /etc/init.d/webvirtmgr-novnc
    $ sudo service webvirtmgr-novnc start
    $ sudo chkconfig webvirtmgr-novnc on

### Ubuntu

Run: 

    $ sudo service novnc stop
    $ sudo update-rc.d -f novnc remove
    $ sudo cp conf/initd/webvirtmgr-novnc-ubuntu /etc/init.d/webvirtmgr-novnc
    $ sudo service webvirtmgr-novnc start
    $ sudo update-rc.d webvirtmgr-novnc defaults

## 6. Gunicorn and Runit (Only for geeks)

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

Support: support@webvirtmgr.net or <a href="https://github.com/retspen/webvirtmgr/issues">GitHub Issues</a>

Powered by

<img src=http://www.jetbrains.com/img/logos/pycharm_logo.gif>
