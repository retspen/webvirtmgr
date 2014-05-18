# WebVirtMgr Fabric/Fabtools Deployment

## Introduction

This directory includes fabric script that helps you automate WebVirtMgr deployment on your server(s) with one command line.

The fabric deployment script (fabfile.py) depends on:

* [Fabric](http://www.fabfile.org/)
* [Fabtools](http://fabtools.readthedocs.org/en/latest/api/index.html)

## Deployment

This Deployment script has been tested on the following distributions:

* Ubuntu 12.04 and above
* Debian 7.5
* Centos 6.4, 6.5
* Fedora 20, 19

### Steps

Install requirements (mainly Fabric and Fabtools)

```
$ cd deploy/fabric
$ pip install -r fab_requirements.txt
```

Then invoke the deployment task via fabric (**deploy_webvirt**).

Assuming deployment via **username** with **sudo** permission.

```
$ fab -H *host ip* -u *username* -p *password* deploy_webvirt
```

Deployment task will start its routine on the remote server, and will eventually prompt you with database initialization (Admin Information).

It will look something similar to this:

```
[192.168.20.14] out: You just installed Django's auth system, which means you don't have any superusers defined.
[192.168.20.14] out: Would you like to create one now? (yes/no): yes (*type yes*)
[192.168.20.14] out: Username (leave blank to use 'root'): admin (*type username*)
[192.168.20.14] out: Email address: admin@iaas.local (*type email*)
[192.168.20.14] out: Password:  (*type password*)
[192.168.20.14] out: Password (again):  (*type password again*)
[192.168.20.14] out: Superuser created successfully.
[192.168.20.14] out: Installing custom SQL ...
[192.168.20.14] out: Installing indexes ...
[192.168.20.14] out: Installed 6 object(s) from 1 fixture(s)
```

The script will continue with the rest of the steps required to finalize the deployment.

A successful installation will finish with the following message:

```
Done.
Disconnecting from 192.168.20.14... done.
```

Now your installation is Done. You can browse to your WebVirtMgr Host and login via the User name and Password you entered during the setup.

### Notes

#### System Updates

Try to update your system before WebVirtMgr installation.

#### Fedora & Centos *requiretty*

Fedora and Centos add a default restriction **requiretty** in **sudoers** file.

This restriction can cause an error like:

```
[192.168.20.14] out: sudo: sorry, you must have a tty to run sudo
```

In order to overcome this issue, you will need to disable **requiretty** (at least temporarily)

Run:

```
$ visudo
```

and comment out

```
# Defaults      requiretty
```

#### Default Settings

In case you want to modify the default deployment settings, you can edit **settings.py**.

For example you can edit the **SERVER_NAME** that will be inserted in *nginx.conf* Nginx site.

```python
# NGINX server name
SERVER_NAME = "iaas.local"
```

You can also edit any of the templates found in *templates* directory

- **nginx.conf**: webvirtmgr Nginx site.
- **original.nginx.conf**: default Nginx configuration (Applicable only on Fedora)
- **webvirtmgr.ini**: supervisord config file for WebVirtMgr Gunicorn sever.
