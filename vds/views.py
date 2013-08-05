# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from vds.models import Host, Vm
from dashboard.views import SortHosts
from webvirtmgr.server import ConnServer
from libvirt import libvirtError


def vds(request, host_id, vname):
    """

    VDS block

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    messages = []
    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None

    if not conn:
        errors.append(e.message)
    else:
        all_vm = SortHosts(conn.vds_get_node())
        vcpu, memory, mac, network,description = conn.vds_get_info(vname)
        cpu_usage = conn.vds_cpu_usage(vname)
        memory_usage = conn.vds_memory_usage(vname)[1]
        hdd_image = conn.vds_get_hdd(vname)
        iso_images = sorted(conn.get_all_media())
        media = conn.vds_get_media(vname)
        dom = conn.lookupVM(vname)
        vcpu_range = [str(x) for x in range(1, 9)]
        memory_range = [128, 256, 512, 768, 1024, 2048, 4096, 8192, 16384]

        try:
            vm = Vm.objects.get(vname=vname)
        except:
            vm = None

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
                    msg = _("Create snapshot for instance successful")
                    messages.append(msg)
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'remove_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                try:
                    conn.vds_umount_iso(vname, image)
                    if vm:
                        conn.vds_set_vnc_passwd(vname, vm.vnc_passwd)
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'add_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                try:
                    conn.vds_mount_iso(vname, image)
                    if vm:
                        conn.vds_set_vnc_passwd(vname, vm.vnc_passwd)
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'edit' in request.POST:
	        description = request.POST.get('description', '')
                vcpu = request.POST.get('vcpu', '')
                ram = request.POST.get('ram', '')
                try:
                    conn.vds_edit(vname, description, ram, vcpu)
                    if vm:
                        conn.vds_set_vnc_passwd(vname, vm.vnc_passwd)
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)                
            if 'vnc_pass' in request.POST:
                if request.POST.get('auto_pass', ''):
                    from string import letters, digits
                    from random import choice

                    passwd = ''.join([choice(letters + digits) for i in range(12)])
                else:
                    passwd = request.POST.get('vnc_passwd', '')

                    if not passwd:
                        msg = _("Enter the VNC password or select Generate")
                        errors.append(msg)

                if not errors:
                    try:
                        conn.vds_set_vnc_passwd(vname, passwd)
                        vnc_pass = Vm(host_id=host_id, vname=vname, vnc_passwd=passwd)
                        vnc_pass.save()
                    except libvirtError as msg_error:
                        errors.append(msg_error.message)
                    return HttpResponseRedirect(request.get_full_path())

        conn.close()

    return render_to_response('vds.html', locals(), context_instance=RequestContext(request))
