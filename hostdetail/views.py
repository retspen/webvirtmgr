from libvirt import libvirtError

from django.shortcuts import render_to_response
from django.http import HttpResponse
from django.template import RequestContext
from django.utils import simplejson

from servers.models import Compute
from vrtManager.hostdetails import wvmHostDetails
from webvirtmgr.settings import TIME_JS_REFRESH


def cpuusage(request, host_id):
    """
    Return CPU Usage in %
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    data = {}
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmHostDetails(compute.hostname, compute.login, compute.password, compute.type)
        cpu_usage = conn.cpu_get_usage()
        data = simplejson.dumps(cpu_usage)
        conn.close()
    except libvirtError:
        pass
    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    response.write(data)
    return response

def memusage(request, host_id):
    """
    Return Memory Usage in % and numeric
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    data = {}
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmHostDetails(compute.hostname, compute.login, compute.password, compute.type)
        mem_usage = conn.memory_get_usage()
        data = simplejson.dumps(mem_usage)
        conn.close()
    except libvirtError:
        pass
    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    response.write(data)
    return response

def overview(request, host_id):
    """
    Overview page.
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    time_refresh = TIME_JS_REFRESH

    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmHostDetails(compute.hostname, compute.login, compute.password, compute.type)
        hostname, host_arch, host_memory, logical_cpu, model_cpu, uri_conn = conn.get_node_info()
        hypervisor = conn.hypervisor_type()
        mem_usage = conn.memory_get_usage()
        conn.close()
    except libvirtError as err:
        errors.append(err.message)

    return render_to_response('hostdeatil.html', locals(), context_instance=RequestContext(request))
