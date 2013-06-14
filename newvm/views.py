# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from vds.models import Host, Flavor, Vm
import libvirt_func
import virtinst.util as util
from libvirt import libvirtError
import re
from string import letters, digits
from random import choice


def newvm(request, host_id):
    """

    Page add new VM.

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    def add_vm(name, ram, vcpu, image, net, virtio, passwd):
        ram = int(ram) * 1024
        iskvm = re.search('kvm', conn.getCapabilities())
        if iskvm:
            dom_type = 'kvm'
        else:
            dom_type = 'qemu'

        machine = util.get_xml_path(conn.getCapabilities(), "/capabilities/guest/arch/machine/@canonical")
        if not machine:
            machine = 'pc-1.0'

        if re.findall('/usr/libexec/qemu-kvm', conn.getCapabilities()):
            emulator = '/usr/libexec/qemu-kvm'
        elif re.findall('/usr/bin/kvm', conn.getCapabilities()):
            emulator = '/usr/bin/kvm'
        elif re.findall('/usr/bin/qemu-kvm', conn.getCapabilities()):
            emulator = '/usr/bin/qemu-kvm'            
        else:
            emulator = '/usr/bin/qemu-system-x86_64'

        img = conn.storageVolLookupByPath(image)
        vol = img.name()
        for storage in all_storages:
            stg = conn.storagePoolLookupByName(storage)
            if stg.info()[0] != 0:
                stg.refresh(0)
                for img in stg.listVolumes():
                    if img == vol:
                        stg_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
                        if stg_type == 'dir':
                            image_type = 'qcow2'
                        else:
                            image_type = 'raw'

        xml = """<domain type='%s'>
                  <name>%s</name>
                  <memory>%s</memory>
                  <currentMemory>%s</currentMemory>
                  <vcpu>%s</vcpu>
                  <os>
                    <type arch='x86_64' machine='%s'>hvm</type>
                    <boot dev='hd'/>
                    <boot dev='cdrom'/>
                    <bootmenu enable='yes'/>
                  </os>
                  <features>
                    <acpi/>
                    <apic/>
                    <pae/>
                  </features>
                  <clock offset='utc'/>
                  <on_poweroff>destroy</on_poweroff>
                  <on_reboot>restart</on_reboot>
                  <on_crash>restart</on_crash>
                  <devices>
                    <emulator>%s</emulator>
                    <disk type='file' device='disk'>
                      <driver name='qemu' type='%s'/>
                      <source file='%s'/>""" % (dom_type, name, ram, ram, vcpu, machine, emulator, image_type, image)

        if virtio:
            xml += """<target dev='vda' bus='virtio'/>"""
        else:
            xml += """<target dev='hda' bus='ide'/>"""

        xml += """</disk>
                    <disk type='file' device='cdrom'>
                      <driver name='qemu' type='raw'/>
                      <source file=''/>
                      <target dev='hdc' bus='ide'/>
                      <readonly/>
                    </disk>"""

        if re.findall("br", net):
            xml += """<interface type='bridge'>
                    <source bridge='%s'/>""" % (net)
        else:
            xml += """<interface type='network'>
                    <source network='%s'/>""" % (net)
        if virtio:
            xml += """<model type='virtio' />"""

        xml += """</interface>
                    <input type='tablet' bus='usb'/>
                    <input type='mouse' bus='ps2'/>
                    <graphics type='vnc' port='-1' autoport='yes' keymap='en-us' passwd='%s'/>
                    <video>
                      <model type='cirrus' vram='9216' heads='1'/>
                    </video>
                    <memballoon model='virtio'>
                    </memballoon>
                  </devices>
                </domain>""" % (passwd)
        conn.defineXML(xml)
        dom = conn.lookupByName(name)
        dom.setAutostart(1)

    host = Host.objects.get(id=host_id)
    conn = libvirt_func.libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        have_kvm = libvirt_func.hard_accel_node(conn)

        try:
            flavors = Flavor.objects.filter().order_by('id')
        except:
            flavors = 'error'

        errors = []

        all_vm = libvirt_func.vds_get_node(conn)
        all_networks = libvirt_func.networks_get_node(conn)
        all_storages = libvirt_func.storages_get_node(conn)
        all_img = libvirt_func.images_get_storages(conn, all_storages)

        if not all_networks:
            msg = _("You haven't defined any virtual networks")
            errors.append(msg)
        if not all_storages:
            msg = _("You haven't defined have any storage pools")
            errors.append(msg)
        if not have_kvm:
            msg = _("Your CPU doesn't support hardware virtualization")
            errors.append(msg)

        hdd_digits_size = [a for a in range(1, 601)]

        if request.method == 'POST':
            if 'add_flavor' in request.POST:
                name = request.POST.get('name', '')
                vcpu = request.POST.get('vcpu', '')
                ram = request.POST.get('ram', '')
                hdd = request.POST.get('hdd', '')

                for flavor in flavors:
                    if name == flavor.name:
                        msg = _("Name already use")
                        errors.append(msg)
                if not errors:
                    flavor_add = Flavor(name=name, vcpu=vcpu, ram=ram, hdd=hdd)
                    flavor_add.save()
                    return HttpResponseRedirect(request.get_full_path())

            if 'del_flavor' in request.POST:
                flavor_id = request.POST.get('flavor', '')
                flavor_del = Flavor.objects.get(id=flavor_id)
                flavor_del.delete()
                return HttpResponseRedirect(request.get_full_path())

            if 'newvm' in request.POST:
                net = request.POST.get('network', '')
                storage = request.POST.get('storage', '')
                vname = request.POST.get('name', '')
                hdd_size = request.POST.get('hdd_size', '')
                img = request.POST.get('img', '')
                ram = request.POST.get('ram', '')
                vcpu = request.POST.get('vcpu', '')
                virtio = request.POST.get('virtio', '')

                symbol = re.search('[^a-zA-Z0-9\_\-\.]+', vname)

                if vname in all_vm:
                    msg = _("A virtual machine with this name already exists")
                    errors.append(msg)
                if len(vname) > 12:
                    msg = _("The name of the virtual machine must not exceed 12 characters")
                    errors.append(msg)
                if symbol:
                    msg = _("The name of the virtual machine must not contain any special characters")
                    errors.append(msg)
                if not vname:
                    msg = _("Enter the name of the virtual machine")
                    errors.append(msg)
                if not errors:
                    if not hdd_size:
                        if not img:
                            msg = _("First you need to create an image")
                            errors.append(msg)
                        else:
                            image = libvirt_func.image_get_path(conn, img, all_storages)
                    else:
                        try:
                            stg = conn.storagePoolLookupByName(storage)
                            libvirt_func.new_volume(stg, vname, hdd_size)
                        except libvirtError as msg_error:
                            errors.append(msg_error.message)
                    if not errors:
                        if not img:
                            stg_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
                            if stg_type == 'dir':
                                vol = vname + '.img'
                            else:
                                vol = vname
                            vl = stg.storageVolLookupByName(vol)
                        else:
                            vol = img
                            vl = conn.storageVolLookupByPath(image)

                        image = vl.path()
                        vnc_passwd = ''.join([choice(letters + digits) for i in range(12)])

                        try:
                            add_vm(vname, ram, vcpu, image, net, virtio, vnc_passwd)
                        except libvirtError as msg_error:
                            if hdd_size:
                                vl.delete(0)
                            errors.append(msg_error.message)

                        if not errors:
                            new_vm = Vm(host_id=host_id, vname=vname, vnc_passwd=vnc_passwd)
                            new_vm.save()
                            return HttpResponseRedirect('/vds/%s/%s/' % (host_id, vname))

        conn.close()

    return render_to_response('newvm.html', locals(), context_instance=RequestContext(request))
