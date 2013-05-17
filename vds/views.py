# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from dashboard.models import Host
from libvirt_func import libvirt_conn, vds_get_node


def vds(request, host_id, vname):
    """

    VM's block

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

    def add_iso(image, storages):
        image = image + '.iso'
        for storage in storages:
            stg = conn.storagePoolLookupByName(storage)
            for img in stg.listVolumes():
                if image == img:
                    if dom.info()[0] == 1:
                        vol = stg.storageVolLookupByName(image)
                        xml = """<disk type='file' device='cdrom'>
                                    <driver name='qemu' type='raw'/>
                                    <target dev='hdc' bus='ide'/>
                                    <source file='%s'/>
                                    <readonly/>
                                 </disk>""" % vol.path()
                        dom.attachDevice(xml)
                        xmldom = dom.XMLDesc(0)
                        conn.defineXML(xmldom)
                    if dom.info()[0] == 5:
                        vol = stg.storageVolLookupByName(image)
                        xml = dom.XMLDesc(0)
                        newxml = "<disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>\n      <source file='%s'/>" % vol.path()
                        xmldom = xml.replace("<disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>", newxml)
                        conn.defineXML(xmldom)

    def remove_iso(image, storages):
        image = image + '.iso'
        if dom.info()[0] == 1:
            xml = """<disk type='file' device='cdrom'>
                         <driver name="qemu" type='raw'/>
                         <target dev='hdc' bus='ide'/>
                         <readonly/>
                      </disk>"""
            dom.attachDevice(xml)
            xmldom = dom.XMLDesc(0)
            conn.defineXML(xmldom)
        if dom.info()[0] == 5:
            for storage in storages:
                stg = conn.storagePoolLookupByName(storage)
                for img in stg.listVolumes():
                    if image == img:
                        vol = stg.storageVolLookupByName(image)
                        xml = dom.XMLDesc(0)
                        xmldom = xml.replace("<source file='%s'/>\n" % vol.path(), '')
                        conn.defineXML(xmldom)

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

    def dom_media():
        import virtinst.util as util
        import re

        xml = dom.XMLDesc(0)
        media = util.get_xml_path(xml, "/domain/devices/disk[2]/source/@file")
        if media:
            vol = conn.storageVolLookupByPath(media)
            img = re.sub('.iso', '', vol.name())
            return img
        else:
            return None

    def dom_uptime():
        if dom.info()[0] == 1:
            nanosec = dom.info()[4]
            minutes = nanosec * 1.66666666666667E-11
            minutes = round(minutes, 0)
            return minutes
        else:
            return 'None'

    def get_dom_info():
        import virtinst.util as util

        info = []

        xml = dom.XMLDesc(0)
        info.append(util.get_xml_path(xml, "/domain/vcpu"))
        mem = util.get_xml_path(xml, "/domain/memory")
        mem = int(mem) / 1024
        info.append(int(mem))
        info.append(util.get_xml_path(xml, "/domain/devices/interface/mac/@address"))
        nic = util.get_xml_path(xml, "/domain/devices/interface/source/@network")
        if nic is None:
            nic = util.get_xml_path(xml, "/domain/devices/interface/source/@bridge")
        info.append(nic)
        return info

    def get_dom_hdd(storages):
        import virtinst.util as util

        xml = dom.XMLDesc(0)
        hdd = util.get_xml_path(xml, "/domain/devices/disk[1]/source/@file")

        # If xml create custom
        if not hdd:
            hdd = util.get_xml_path(xml, "/domain/devices/disk[1]/source/@dev")
        try:
            img = conn.storageVolLookupByPath(hdd)
            img_vol = img.name()

            for storage in storages:
                stg = conn.storagePoolLookupByName(storage)
                stg.refresh(0)
                for img in stg.listVolumes():
                    if img == img_vol:
                        vol = img
                        vol_stg = storage

            return vol, vol_stg
        except:
            return hdd, 'Not in the pool'

    def vm_cpu_usage():
        import time
        try:
            nbcore = conn.getInfo()[2]
            cpu_use_ago = dom.info()[4]
            time.sleep(1)
            cpu_use_now = dom.info()[4]
            diff_usage = cpu_use_now - cpu_use_ago
            cpu_usage = 100 * diff_usage / (1 * nbcore * 10**9L)
            return cpu_usage
        except libvirtError as e:
            return e.message

    def get_mem_usage():
        try:
            allmem = conn.getInfo()[1] * 1048576
            dom_mem = dom.info()[1] * 1024
            percent = (dom_mem * 100) / allmem
            return allmem, percent
        except libvirtError as e:
            return e.message

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
    conn = libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        all_vm = vds_get_node(conn)
        dom = conn.lookupByName(vname)

        try:
            vm = Vm.objects.get(vname=vname)
        except:
            vm = None

        dom_info = get_dom_info()
        dom_uptime = dom_uptime()
        cpu_usage = vm_cpu_usage()
        mem_usage = get_mem_usage()

        storages = get_all_storages(conn)
        hdd_image = get_dom_hdd(storages)
        iso_images = sorted(find_all_iso(storages))
        media = dom_media()

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
                remove_iso(image, storages)
                return HttpResponseRedirect(request.get_full_path())
            if 'add_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                add_iso(image, storages)
                return HttpResponseRedirect(request.get_full_path())
            if 'vnc_pass' in request.POST:
                set_vnc_passwd()
                return HttpResponseRedirect(request.get_full_path())

        conn.close()

    return render_to_response('vm.html', locals(), context_instance=RequestContext(request))
