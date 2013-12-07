from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from libvirt import libvirtError
from instance.models import Host, Instance
from webvirtmgr.server import ConnServer
import re


def console(request, host_id, vname):
    """

    VNC vm's block

    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    vnc_port = socket_host = socket_port = None
    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None

    if not conn:
        errors.append(e.message)
    else:
        socket_port = 6080
        socket_host = request.get_host()
        if ':' in socket_host:
            socket_host = re.sub(':[0-9]+', '', socket_host)

        created = None
        try:
            vnc_passwd = conn.get_vnc_password_by_name(vname)
            instance, created = Instance.objects.get_or_create(host=host, vname=vname)
            instance.vnc_passwd = vnc_passwd
        except:
            instance = None

        if created:
            instance.save()

        conn.close()

    response = render_to_response('console.html', {'socket_port': socket_port,
                                                   'socket_host': socket_host,
                                                   'instance': instance,
                                                   'errors': errors
                                                   },
                                  context_instance=RequestContext(request))
    response.set_cookie('token', vname)
    return response
