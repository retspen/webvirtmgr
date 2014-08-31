import re

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect

from instance.models import Instance
from vrtManager.instance import wvmInstance

from webvirtmgr.settings import WS_PORT


def console(request):
    """
    VNC instance block
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    if request.method == 'GET':
        token = request.GET.get('token', '')

    try:
        temptoken = token.split('-', 1)
        host = int(temptoken[0])
        uuid = temptoken[1]
        instance = Instance.objects.get(compute_id=host, uuid=uuid)
        conn = wvmInstance(instance.compute.hostname,
                           instance.compute.login,
                           instance.compute.password,
                           instance.compute.type,
                           instance.name)
        vnc_websocket_port = conn.get_vnc_websocket_port()
        vnc_passwd = conn.get_vnc_passwd()
    except:
        vnc_websocket_port = None
        vnc_passwd = None

    ws_port = vnc_websocket_port if vnc_websocket_port else WS_PORT
    ws_host = request.get_host()

    if ':' in ws_host:
        ws_host = re.sub(':[0-9]+', '', ws_host)

    response = render_to_response('console.html', locals(), context_instance=RequestContext(request))
    response.set_cookie('token', token)
    return response
