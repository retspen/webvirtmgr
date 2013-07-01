# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from vds.models import Host, Vm
from webvirtmgr.server import ConnServer
from libvirt import libvirtError


def vds(request, host_id, vname):
    """

    VDS block

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = ConnServer(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        all_vm = conn.vds_get_node()
        dom_info = conn.vds_get_info(vname)
        cpu_usage = conn.vds_cpu_usage(vname)
        mem_usage = conn.vds_memory_usage(vname)
        hdd_image = conn.vds_get_hdd(vname)
        iso_images = sorted(conn.get_all_media())
        media = conn.vds_get_media(vname)        
        dom = conn.lookupVM(vname)

        try:
            vm = Vm.objects.get(vname=vname)
        except:
            vm = None

        errors = []

        if request.method == 'POST':
            if 'start' in request.POST:
                try:
                    dom.create()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'power' in request.POST:
                if 'shutdown' == request.POST.get('power', ''):
                    try:
                        dom.shutdown()
                        return HttpResponseRedirect(request.get_full_path())
                    except libvirtError as msg_error:
                        errors.append(msg_error.message)
                if 'destroy' == request.POST.get('power', ''):
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
            if 'delete' in request.POST:
                try:
                    if dom.info()[0] == 1:
                        dom.destroy()
                    if request.POST.get('image', ''):
                        conn.vds_remove_hdd(vname)
                    try:
                        vm = Vm.objects.get(host=host_id, vname=vname)
                        vm.delete()
                    except:
                        pass
                    dom.undefine()
                    return HttpResponseRedirect('/overview/%s/' % host_id)
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'snapshot' in request.POST:
                try:
                    conn.vds_create_snapshot(vname)
                    messages = []
                    msg = _("Create snapshot for instance successful")
                    messages.append(msg)
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'remove_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                try:
                    conn.vds_umount_iso(vname, image)
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'add_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                try:
                    conn.vds_mount_iso(vname, image)
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'vnc_pass' in request.POST:
                from string import letters, digits
                from random import choice

                passwd = ''.join([choice(letters + digits) for i in range(12)])
                try:
                    conn.vds_set_vnc_passwd(vname, passwd)
                    vnc_pass = Vm(host_id=host_id, vname=vname, vnc_passwd=passwd)
                    vnc_pass.save()
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
                return HttpResponseRedirect(request.get_full_path())

        conn.close()

    return render_to_response('vds.html', locals(), context_instance=RequestContext(request))
