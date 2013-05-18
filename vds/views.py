# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from dashboard.models import Host, Vm
import libvirt_func


def vds(request, host_id, vname):
    """

    VDS block

    """

    from libvirt import libvirtError

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    def find_all_iso(storages):
        import re
        iso = []
        for storage in storages:
            stg = conn.storagePoolLookupByName(storage)
            stg.refresh(0)
            for img in stg.listVolumes():
                if re.findall(".iso", img):
                    img = re.sub('.iso', '', img)
                    iso.append(img)
        return iso


    def find_iso(image, storages):
        image = image + '.iso'
        for storage in storages:
            stg = conn.storagePoolLookupByName(storage)
            stg.refresh(0)
            try:
                vol = stg.storageVolLookupByName(image)
            except:
                vol = None
        return vol.name()


    def set_vnc_passwd():
        from string import letters, digits
        from random import choice

        passwd = ''.join([choice(letters + digits) for i in range(12)])

        try:
            xml = dom.XMLDesc(0)
            newxml = "<graphics type='vnc' port='-1' autoport='yes' keymap='en-us' passwd='%s'/>" % passwd
            xmldom = xml.replace("<graphics type='vnc' port='-1' autoport='yes' keymap='en-us'/>", newxml)
            conn.defineXML(xmldom)
            vnc_pass = Vm(host_id=host_id, vname=vname, vnc_passwd=passwd)
            vnc_pass.save()
        except libvirtError as e:
            return e.message

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
        dom_uptime = libvirt_func.vds_get_uptime(dom)
        cpu_usage = libvirt_func.vds_cpu_usage(conn, dom)
        mem_usage = libvirt_func.vds_memory_usage(conn, dom)

        storages = libvirt_func.storages_get_node(conn)
        hdd_image = libvirt_func.vds_get_hdd(conn, dom, storages)
        iso_images = sorted(find_all_iso(storages))
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
                    xml = dom.XMLDesc(0)
                    if dom.info()[0] == 1:
                        dom.destroy()
                    dom.undefine()
                    if request.POST.get('image', ''):
                        import virtinst.util as util

                        img = util.get_xml_path(xml, "/domain/devices/disk[1]/source/@file")
                        vol = conn.storageVolLookupByPath(img)
                        vol.delete(0)
                    try:
                        vm = Vm.objects.get(host=host_id, vname=vname)
                        vm.delete()
                    except:
                        pass
                    return HttpResponseRedirect('/overview/%s/' % host_id)
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'snapshot' in request.POST:
                try:
                    import time
                    xml = """<domainsnapshot>\n
                                 <name>%d</name>\n
                                 <state>shutoff</state>\n
                                 <creationTime>%d</creationTime>\n""" % (time.time(), time.time())
                    xml += dom.XMLDesc(0)
                    xml += """<active>0</active>\n
                              </domainsnapshot>"""
                    dom.snapshotCreateXML(xml, 0)
                    messages = []
                    messages.append('Create snapshot for instance successful')
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'remove_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                libvirt_func.vds_umount_iso(conn, dom, image, storages)
                return HttpResponseRedirect(request.get_full_path())
            if 'add_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                libvirt_func.vds_mount_iso(conn, dom, image, storages)
                return HttpResponseRedirect(request.get_full_path())
            if 'vnc_pass' in request.POST:
                set_vnc_passwd()
                return HttpResponseRedirect(request.get_full_path())

        conn.close()

    return render_to_response('vm.html', locals(), context_instance=RequestContext(request))
