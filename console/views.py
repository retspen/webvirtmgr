import re

from libvirt import libvirtError

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext

from instance.models import Instance

def console(request, host_id):
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
        try:
            instance = Instance.objects.get(host=host_id, vname=vname)
            socket_port = 6080
            socket_host = request.get_host()
            if ':' in socket_host:
                socket_host = re.sub(':[0-9]+', '', socket_host)
        except:
            instance = None

        conn.close()

    response = render_to_response('console.html', {'socket_port': socket_port,
                                                   'socket_host': socket_host,
                                                   'instance': instance,
                                                   'errors': errors
                                                   },
                                  context_instance=RequestContext(request))
    response.set_cookie('token', vname)
    return response
