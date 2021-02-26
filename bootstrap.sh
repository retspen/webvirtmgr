#!/bin/sh

if [ ! -f "/data/vm/webvirtmgr.sqlite3" ]; then

#chown webvirtmgr /var/run/libvirt/libvirt-sock
#/usr/bin/python /opt/webvirtmgr/manage.py syncdb --noinput
/usr/bin/python /opt/webvirtmgr/manage.py makemigrations && /usr/bin/python /opt/webvirtmgr/manage.py migrate
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@localhost', 'Cestc_01')" | /usr/bin/python /opt/webvirtmgr/manage.py shell
chown -R webvirtmgr:libvirtd /data/vm
su - webvirtmgr -c "ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa && touch ~/.ssh/config && echo -e "StrictHostKeyChecking=no\nUserKnownHostsFile=/dev/null" >> ~/.ssh/config && chmod 0600 ~/.ssh/config"

fi

