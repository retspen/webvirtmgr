# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from vds.models import Host
from webvirtmgr.server import ConnServer
from libvirt import libvirtError


def overview(request, host_id):
    """

    Overview page.

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = ConnServer(host)

    errors = []

    if type(conn) == dict:
        errors.append(conn.values()[0])
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
