# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from vds.models import Host, Vm
from libvirt_func import libvirt_conn, vnc_get_port
import os
import re


def vnc(request, host_id, vname):
    """

    VNC vm's block

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        vnc_port = vnc_get_port(conn, vname)
        try:
            vm = Vm.objects.get(host=host_id, vname=vname)

            socket_host = request.META['HTTP_HOST']
            if ':' in socket_host:
                socket_host = re.sub('\:[0-9]+', '', socket_host)

            socket_port = 6080 + int(vnc_port[3:])

            # Kill only owner proccess
            os.system("kill -9 $(ps aux | grep 'websockify %s' | grep -v grep | awk '{ print $2 }')" % socket_port)
            os.system('websockify %s %s:%s -D' % (socket_port, host.ipaddr, vnc_port))
        except:
            vm = None

        conn.close()

    return render_to_response('vnc.html', locals(), context_instance=RequestContext(request))
