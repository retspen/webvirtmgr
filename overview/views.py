# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from vds.models import Host
from webvirtmgr.server import ConnServer
from libvirt import libvirtError


def cpuusage(request, host_id):
    """
	Return CPU Usage in %
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except libvirtError as e:
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

    errors = []
    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except libvirtError as e:
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

        all_vm = conn.vds_get_node()
        host_info = conn.node_get_info()
        mem_usage = conn.memory_get_usage()
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
