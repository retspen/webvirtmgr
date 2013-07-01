# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from vds.models import Host, Vm
from webvirtmgr.server import ConnServer
import re


def vnc(request, host_id, vname):
    """

    VNC vm's block

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = ConnServer(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        vnc_port = conn.vnc_get_port(vname)
        try:
            vm = Vm.objects.get(host=host_id, vname=vname)
            socket_port = 6080
            socket_host = request.META['HTTP_HOST']
            if ':' in socket_host:
                socket_host = re.sub('\:[0-9]+', '', socket_host)
        except:
            vm = None

        conn.close()

    response = render_to_response('vnc.html', locals(), context_instance=RequestContext(request))
    response.set_cookie('token', vname)
    return response
