FROM whharbor.centos.org/centos/bash:v1
MAINTAINER Jiajun Chen<48853342@qq.com>

RUN yum -y install epel-release vim && \
    yum -y install python2-pip python-devel libvirt-python libxml2-python git novnc python-websockify numpy supervisor && \
    yum clean all && rm -rf /var/cache/yum

RUN git clone -b cestc https://github.com/jxph025319/webvirtmgr.git /opt/webvirtmgr
WORKDIR /opt/webvirtmgr
#RUN git checkout cestc #v4.8.8
RUN pip install -r requirements.txt
#ADD local_settings.py /opt/webvirtmgr/webvirtmgr/local/local_settings.py
#RUN sed -i 's/0.0.0.0/172.17.42.1/g' vrtManager/create.py
RUN /usr/bin/python /opt/webvirtmgr/manage.py collectstatic --noinput
RUN cp build/webvirtmgr.ini /etc/supervisord.d/webvirtmgr.ini &&  mkdir -p /data/vm/ && \
cp /opt/webvirtmgr/build/local_settings.py /opt/webvirtmgr/webvirtmgr/local/local_settings.py
#ADD gunicorn.conf.py /opt/webvirtmgr/conf/gunicorn.conf.py
#ADD bootstrap.sh /opt/webvirtmgr/bootstrap.sh

#RUN groupadd -g 1010 libvirtd && useradd webvirtmgr -g libvirtd -u 1010 -d /data/vm/ -s /sbin/nologin
RUN groupadd -g 1010 libvirtd && useradd webvirtmgr -g libvirtd -u 1010 -d /data/vm/
RUN chown webvirtmgr:libvirtd -R /opt/webvirtmgr

WORKDIR /
VOLUME /data/vm

EXPOSE 8080
EXPOSE 6080
CMD ["supervisord", "-n"]

#  docker build --no-cache -t whharbor.cestc.cn/centos/webvirtmgr:v1 .
#docker run -d --name webvirtmgr_dev -h webvirtmgr_dev -v /usr/share/zoneinfo/Asia/Shanghai:/etc/localtime  --privileged=true -v /data/vm1:/data/vm -p 2100:22 -p 8180:8080 -p 6180:6080 -m 4g whharbor.cestc.cn/centos/webvirtmgr:v1
#docker run -d --name webvirtmgr_dev -h webvirtmgr_dev -v /usr/share/zoneinfo/Asia/Shanghai:/etc/localtime  --privileged=true -v /data/vm1:/data/vm -p 2100:22 -p 8180:8080 -p 6180:6080 -m 4g whharbor.cestc.cn/centos/webvirtmgr:v1 /usr/sbin/init
