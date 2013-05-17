# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from dashboard.models import Host
from libvirt_func import libvirt_conn, hard_accel_node, node_get_info, vm_get_node, cpu_get_usage, memory_get_usage


def overview(request, host_id):
    """

    Overview page.

    """

    from libvirt import libvirtError

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = libvirt_conn(host)

    if type(conn) == dict:
        errors = []
        errors.append(conn.values()[0])
    else:
        have_kvm = hard_accel_node(conn)
        if not have_kvm:
            errors = []
            msg = _('Your CPU doesn\'t support hardware virtualization')
            errors.append(msg)

        all_vm = vm_get_node(conn)
        host_info = node_get_info(conn)
        mem_usage = memory_get_usage(conn)
        cpu_usage = cpu_get_usage(conn)
        lib_virt_ver = conn.getLibVersion()
        conn_type = conn.getURI()

        if request.method == 'POST':
            vname = request.POST.get('vname', '')
            dom = conn.lookupByName(vname)
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
