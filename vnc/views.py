# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from dashboard.models import Host, Vm
from libvirt_func import libvirt_conn


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

            import os
            # Kill only owner proccess
            os.system("kill -9 $(ps aux | grep websockify | grep -v grep | awk '{ print $2 }')")
            os.system('websockify 6080 %s:%s -D' % (host.ipaddr, vnc_port))
        except:
            vm = None

        conn.close()

    return render_to_response('vnc.html', locals(), context_instance=RequestContext(request))
