from libvirt import libvirtError

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson

from servers.models import Compute
from vrtManager.conection import wvmConnect
from vrtManager.hostdetails import wvmHostDetails
from webvirtmgr.settings import TIME_JS_REFRESH


def cpuusage(request, host_id):
    """
    Return CPU Usage in %
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmConnect(compute.hostname, compute.login, compute.password, compute.type)
        hostdetail = wvmHostDetails(conn)
    except libvirtError:
        hostdetail = None
    if hostdetail:
        cpu_usage = hostdetail.cpu_get_usage()
        data = simplejson.dumps(cpu_usage)

    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    response.write(data)
    return response

def memusage(request, host_id):
    """
    Return Memory Usage in %
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmConnect(compute.hostname, compute.login, compute.password, compute.type)
        hostdetail = wvmHostDetails(conn)
    except libvirtError:
        hostdetail = None
    if hostdetail:
        mem_usage = hostdetail.memory_get_usage()
        data = simplejson.dumps(mem_usage)

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
    all_vm = hostname = arch = cpus = cpu_model = \
             type_conn = libvirt_ver = all_mem = \
             mem_usage = mem_percent = cpu_usage = None

    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmConnect(compute.hostname, compute.login, compute.password, compute.type)
        hostdetail = wvmHostDetails(conn)
    except libvirtError as e:
        hostdetail = None

    if not hostdetail:
        errors.append(e.message)
    else:
        hostname, host_arch, host_memory, logical_cpu, model_cpu, uri_conn = hostdetail.get_node_info()
        mem_usage = hostdetail.memory_get_usage()
        cpu_usage = hostdetail.cpu_get_usage()

        if request.method == 'POST':
            vname = request.POST.get('vname', '')
            dom = conn.lookupVM(vname)
            if 'start' in request.POST:
                try:
                    dom.create()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'shutdown' in request.POST:
                try:
                    dom.shutdown()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'destroy' in request.POST:
                try:
                    dom.destroy()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'suspend' in request.POST:
                try:
                    dom.suspend()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'resume' in request.POST:
                try:
                    dom.resume()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)

        #hostdetail.close()

    return render_to_response('hostdeatil.html', locals(),
                              context_instance=RequestContext(request))
