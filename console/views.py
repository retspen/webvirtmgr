import re

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect

from instance.models import Instance
from vrtManager.instance import wvmInstance


WS_PORT = 6080


def console(request):
    """
    VNC instance block
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    if request.method == 'GET':
        uuid = request.GET.get('token', '')

    try:
        instance = Instance.objects.get(uuid=uuid)
        conn = wvmInstance(instance.compute.hostname,
                           instance.compute.login,
                           instance.compute.password,
                           instance.compute.type,
                           instance.name)
        vnc_passwd = conn.get_vnc_passwd()
    except:
        vnc_passwd = None

    wsproxy_port = WS_PORT
    wsproxy_host = request.get_host()
    if ':' in wsproxy_host:
        wsproxy_host = re.sub(':[0-9]+', '', wsproxy_host)

    response = render_to_response('console.html', locals(), context_instance=RequestContext(request))
    response.set_cookie('token', uuid)
    return response
