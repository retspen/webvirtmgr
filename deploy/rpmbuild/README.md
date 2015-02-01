Installation through RPM
========================

If you want you can install webvirtmgr through a rpm package. Under `deploy/rpmbuild/webvirtmgr.spec` you find the spec file to build the rpm.

Tested on `CentOS 6.5`.

### Build

Using `mock` and `rpmdevtools` to create the rpm (`yum install mock rpm-build rpmdevtools` from `EPEL` ).

##### User

Add new mock user:

```sh
useradd <username>
passwd <username>
usermod -aG mock <username>
```

Or editing existing users:

```sh
usermod -aG mock <username> && newgrp mock
```

##### Get sources from repository

```sh
cd deploy/rpmbuild/
spectool -g webvirtmgr.spec
```

##### Build the sources (src.rpm)

```sh
mock --resultdir=. --root epel-6-x86_64 --buildsrpm --spec webvirtmgr.spec --sources .
```

##### Build rpm

```sh
mock --resultdir=. --root=epel-6-x86_64 --rebuild webvirtmgr-4.8.8-1.el6.src.rpm
```

After this operations you have `webvirtmgr-4.8.8-1.el6.noarch.rpm`. To install it simply run:

```sh
yum localinstall webvirtmgr-4.8.8-1.el6.noarch.rpm
```

### Files

After the rpm installation, you can find the webvirtmgr files under `{python_sitelib}/webvirtmgr`.

Set the correct bind parameter in file `{python_sitelib}/webvirtmgr/conf/gunicorn.conf.py`.

In `CentOS 6.5` the path `{python_sitelib}` is usually `/usr/lib/python2.6/site-packages`.

Upstart file
============

If you want that webvirtmgr starts at boot, under `{python_sitelib}/webvirtmgr/conf/init/webvirtmgr-redhat.conf` there is the configuration file for upstart. The installation through rpm **launch** the app at boot. In fact the rpm installation copy the file `webvirtmgr-redhat.conf` in `/etc/init/`.

If you don't want to start webvirtmgr at boot simply remove the `webvirtmgr-redhat.conf` file in `/etc/init/`.
