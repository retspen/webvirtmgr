FROM centos:centos7.4.1708
MAINTAINER Jiajun Chen<48853342@qq.com>

RUN yum -y install epel-release vim openssh-clients openssh-server net-tools sshpass && \
    yum -y install python2-pip python-devel libvirt-python libxml2-python git novnc python-websockify numpy supervisor gettext && \
    yum clean all && rm -rf /var/cache/yum
RUN echo cestc01 | passwd --stdin root
RUN git clone -b cestc https://github.com/jxph025319/webvirtmgr.git /opt/webvirtmgr
WORKDIR /opt/webvirtmgr
RUN git checkout v5.0.5
RUN pip install -r requirements.txt
#ADD local_settings.py /opt/webvirtmgr/webvirtmgr/local/local_settings.py
#RUN sed -i 's/0.0.0.0/172.17.42.1/g' vrtManager/create.py
RUN /usr/bin/python /opt/webvirtmgr/manage.py collectstatic --noinput
RUN cp build/webvirtmgr.ini /etc/supervisord.d/webvirtmgr.ini &&  mkdir -p /data/vm/ && \
cp /opt/webvirtmgr/build/local_settings.py /opt/webvirtmgr/webvirtmgr/local/local_settings.py
#ADD gunicorn.conf.py /opt/webvirtmgr/conf/gunicorn.conf.py
#ADD bootstrap.sh /opt/webvirtmgr/bootstrap.sh

#RUN groupadd -g 1010 libvirtd && useradd webvirtmgr -g libvirtd -u 1010 -d /data/vm/ -s /sbin/nologin
RUN groupadd -g 1010 libvirtd && useradd webvirtmgr -g libvirtd -u 1010 -d /data/vm/ && chown webvirtmgr:libvirtd -R /opt/webvirtmgr

WORKDIR /opt
VOLUME /data/vm

EXPOSE 8080
EXPOSE 6080
CMD ["supervisord", "-n"]
