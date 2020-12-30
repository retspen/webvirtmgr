#!/bin/sh

if [ ! -f "/data/vm/webvirtmgr.sqlite3" ]; then

chown webvirtmgr /var/run/libvirt/libvirt-sock
/usr/bin/python /webvirtmgr/manage.py syncdb --noinput
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@localhost', '1234')" | /usr/bin/python /webvirtmgr/manage.py shell

fi

