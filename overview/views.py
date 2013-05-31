# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from vds.models import Host
import libvirt_func
from libvirt import libvirtError


def overview(request, host_id):
    """

    Overview page.

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = libvirt_func.libvirt_conn(host)

    errors = []

    if type(conn) == dict:
        errors.append(conn.values()[0])
    else:
        have_kvm = libvirt_func.hard_accel_node(conn)
        if not have_kvm:
            msg = _('Your CPU doesn\'t support hardware virtualization')
            errors.append(msg)

        all_vm = libvirt_func.vds_get_node(conn)
        host_info = libvirt_func.node_get_info(conn)
        mem_usage = libvirt_func.memory_get_usage(conn)
        cpu_usage = libvirt_func.cpu_get_usage(conn)
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
