# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from instance.models import Host
from dashboard.views import SortHosts
from webvirtmgr.server import ConnServer
from libvirt import libvirtError
from webvirtmgr.settings import TIME_JS_REFRESH


def cpuusage(request, host_id):
    """
    Return CPU Usage in %
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except:
        conn = None
    if conn:
        cpu_usage = conn.cpu_get_usage()
    return HttpResponse(cpu_usage)


def memusage(request, host_id):
    """
    Return Memory Usage in %
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except:
        conn = None
    if conn:
        mem_usage = conn.memory_get_usage()
    return HttpResponse(mem_usage[2])


def overview(request, host_id):
    """

    Overview page.

    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    time_refresh = TIME_JS_REFRESH
    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None

    if not conn:
        errors.append(e.message)
    else:
        have_kvm = conn.hard_accel_node()
        if not have_kvm:
            msg = _('Your CPU doesn\'t support hardware virtualization')
            errors.append(msg)

        all_vm = SortHosts(conn.vds_get_node())
        hostname, arch, cpus, cpu_model, type_conn, libvirt_ver = conn.node_get_info()
        all_mem, mem_usage, mem_perc = conn.memory_get_usage()
        cpu_usage = conn.cpu_get_usage()

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

        conn.close()

    return render_to_response('overview.html', locals(), context_instance=RequestContext(request))
