#
# Dockerfile to launch WebVirtMgr, see:
# https://github.com/retspen/webvirtmgr
#
# Build with:
# docker build --no-cache=true --rm=true -t webvirtmgr .
#
# Customize:
# * Replace 'authorized_keys' with your key(s) so you can login and inspect the container.
#
# Default credentials (in initial_data.json): L: admin P: admin
#

FROM centos:6

ENV VERSION 0.1

MAINTAINER nuno.tavares@synrix.com

RUN yum clean all && \
    yum -y update && \
    yum -y install http://dl.fedoraproject.org/pub/epel/6/i386/epel-release-6-8.noarch.rpm && \
    yum -y install git python-pip libvirt-python libxml2-python python-websockify \
        supervisor nginx

#
# For debugging
#
RUN yum clean all && \
    yum -y install telnet openssh-server sudo && \
    service sshd start && \
    service sshd stop

RUN mkdir /var/www && \
    cd /var/www && \
    git clone git://github.com/retspen/webvirtmgr.git webvirtmgr

COPY initial_data.json /var/www/webvirtmgr

RUN cd /var/www/webvirtmgr && \
    pip install -r requirements.txt && \
    cd /var/www/webvirtmgr && \
    ./manage.py syncdb --noinput && \
    ./manage.py loaddata ./initial_data.json && \
    ./manage.py collectstatic --noinput && \
    chown -R nginx:nginx /var/www/webvirtmgr



#
# Installation instructions from:
# https://github.com/retspen/webvirtmgr/wiki/Setup-SSH-Authorization
#
RUN mkdir -p /var/lib/nginx/.ssh && \
    chmod 700 /var/lib/nginx/.ssh && \
    ssh-keygen -t rsa -C "webvirtmgr@portavita.nl" -P '' -f /var/lib/nginx/.ssh/id_rsa && \
    touch /var/lib/nginx/.ssh/config && \
    echo -e "StrictHostKeyChecking=no\nUserKnownHostsFile=/dev/null" >> /var/lib/nginx/.ssh/config && \
    mkdir -p /root/.ssh && \
    chmod 700 /root/.ssh && \
    chown nginx:nginx -R /var/lib/nginx && \
    sed -i 's,^user nginx;,user nginx;\ndaemon off;,' /etc/nginx/nginx.conf && \
    rm -f /etc/nginx/conf.d/default.conf

COPY authorized_keys /root/.ssh/authorized_keys

COPY nginx_conf.d_webvirtmgr.conf /etc/nginx/conf.d/webvirtmgr.conf



COPY supervisor.d_webvirtmgr.ini /etc/supervisord.conf

EXPOSE 22 80

ENTRYPOINT ["/usr/bin/supervisord"]
