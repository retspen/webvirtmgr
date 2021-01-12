FROM ubuntu:14.04
MAINTAINER Jiajun Chen<48853342@qq.com>

RUN apt-get -y update && \
    apt-get -y install git python-pip python-libvirt python-libxml2 supervisor novnc

RUN git clone https://github.com/jxph025319/webvirtmgr.git /opt/webvirtmgr
WORKDIR /opt/webvirtmgr
#RUN git checkout cestc #v4.8.8
RUN pip install -r requirements.txt
ADD local_settings.py /opt/webvirtmgr/webvirtmgr/local/local_settings.py
#RUN sed -i 's/0.0.0.0/172.17.42.1/g' vrtManager/create.py
RUN /usr/bin/python /opt/webvirtmgr/manage.py collectstatic --noinput

ADD supervisor.webvirtmgr.conf /etc/supervisord.d/webvirtmgr.conf
#ADD gunicorn.conf.py /opt/webvirtmgr/conf/gunicorn.conf.py

#ADD bootstrap.sh /opt/webvirtmgr/bootstrap.sh

RUN useradd webvirtmgr -g libvirtd -u 1010 -d /data/vm/ -s /sbin/nologin
RUN chown webvirtmgr:libvirtd -R /webvirtmgr

RUN apt-get -ys clean

WORKDIR /
VOLUME /data/vm

EXPOSE 8080
EXPOSE 6080
CMD ["supervisord", "-n"]
