#!/usr/bin/env bash

if [ $# -ne 3 ]; then
  echo "need three parameters"
  exit 1
fi
address=$1
passwd=$2
account=$3
id
if [ ! -d "/data/vm/.ssh" ]; then
  /bin/ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa
else
  echo "ssh dir exists!"
fi
if [ ! -f "/data/vm/.ssh/config" ]; then
    touch /data/vm/.ssh/config
    echo -e "StrictHostKeyChecking=no\nUserKnownHostsFile=/dev/null" >> /data/vm/.ssh/config
    chmod 0600 /data/vm/.ssh/config
fi
sshpass -p "$passwd" ssh-copy-id -o StrictHostKeyChecking=no "$account"@"$address" 2>&1
if [ $? -ne 0 ]; then
    echo "ssh key copy error"
    echo "sshpass -p $passwd ssh-copy-id -o StrictHostKeyChecking=no $account@$address"
fi
