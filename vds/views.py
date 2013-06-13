# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from vds.models import Host, Vm
import libvirt_func
from libvirt import libvirtError


def vds(request, host_id, vname):
    """

    VDS block

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = libvirt_func.libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        all_vm = libvirt_func.vds_get_node(conn)
        dom = conn.lookupByName(vname)

        try:
            vm = Vm.objects.get(vname=vname)
        except:
            vm = None

        dom_info = libvirt_func.vds_get_info(dom)
        cpu_usage = libvirt_func.vds_cpu_usage(conn, dom)
        mem_usage = libvirt_func.vds_memory_usage(conn, dom)

        storages = libvirt_func.storages_get_node(conn)
        hdd_image = libvirt_func.vds_get_hdd(conn, dom, storages)
        iso_images = sorted(libvirt_func.get_all_media(conn, storages))
        media = libvirt_func.vds_get_media(conn, dom)

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
                        libvirt_func.vds_remove_hdd(conn, dom)
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
                    libvirt_func.vds_create_snapshot(dom)
                    messages = []
                    msg = _("Create snapshot for instance successful")
                    messages.append(msg)
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'remove_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                try:
                    libvirt_func.vds_umount_iso(conn, dom, image, storages)
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'add_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                try:
                    libvirt_func.vds_mount_iso(conn, dom, image, storages)
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'vnc_pass' in request.POST:
                from string import letters, digits
                from random import choice

                passwd = ''.join([choice(letters + digits) for i in range(12)])
                try:
                    libvirt_func.vds_set_vnc_passwd(conn, dom, passwd)
                    vnc_pass = Vm(host_id=host_id, vname=vname, vnc_passwd=passwd)
                    vnc_pass.save()
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
                return HttpResponseRedirect(request.get_full_path())

        conn.close()

    return render_to_response('vds.html', locals(), context_instance=RequestContext(request))
