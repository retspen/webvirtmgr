# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from dashboard.models import Host, Flavor, Vm
from libvirt_func import libvirt_conn, hard_accel_node, vds_get_node, networks_get_node, storages_get_node, images_get_storages, image_get_path, new_volume


def newvm(request, host_id):
    """

    Page add new VM.

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    def add_vm(name, ram, vcpu, image, net, passwd):
        import virtinst.util as util
        import re

        ram = int(ram) * 1024
        iskvm = re.search('kvm', conn.getCapabilities())
        if iskvm:
            dom_type = 'kvm'
        else:
            dom_type = 'qemu'

        machine = util.get_xml_path(conn.getCapabilities(), "/capabilities/guest/arch/machine/@canonical")
        if not machine:
            machine = 'pc-1.0'

        if re.findall('/usr/bin/qemu-system-x86_64', conn.getCapabilities()):
            emulator = '/usr/bin/qemu-system-x86_64'
        elif re.findall('/usr/libexec/qemu-kvm', conn.getCapabilities()):
            emulator = '/usr/libexec/qemu-kvm'
        elif re.findall('/usr/bin/kvm', conn.getCapabilities()):
            emulator = '/usr/bin/kvm'
        else:
            emulator = '/usr/bin/qemu-system-x86_64'

        img = conn.storageVolLookupByPath(image)
        vol = img.name()
        for storage in all_storages:
            stg = conn.storagePoolLookupByName(storage)
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
                      <source file='%s'/>
                      <target dev='hda' bus='ide'/>
                    </disk>
                    <disk type='file' device='cdrom'>
                      <driver name='qemu' type='raw'/>
                      <source file=''/>
                      <target dev='hdc' bus='ide'/>
                      <readonly/>
                    </disk>
                    <controller type='ide' index='0'>
                      <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x1'/>
                    </controller>""" % (dom_type, name, ram, ram, vcpu, machine, emulator, image_type, image)

        if re.findall("br", net):
            xml += """<interface type='bridge'>
                    <source bridge='%s'/>""" % (net)
        else:
            xml += """<interface type='network'>
                    <source network='%s'/>""" % (net)

        xml += """<address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
                    </interface>
                    <input type='tablet' bus='usb'/>
                    <input type='mouse' bus='ps2'/>
                    <graphics type='vnc' port='-1' autoport='yes' keymap='en-us' passwd='%s'/>
                    <video>
                      <model type='cirrus' vram='9216' heads='1'/>
                      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>
                    </video>
                    <memballoon model='virtio'>
                      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
                    </memballoon>
                  </devices>
                </domain>""" % (passwd)
        conn.defineXML(xml)
        dom = conn.lookupByName(name)
        dom.setAutostart(1)

    host = Host.objects.get(id=host_id)
    conn = libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        have_kvm = hard_accel_node(conn)

        try:
            flavors = Flavor.objects.filter().order_by('id')
        except:
            flavors = 'error'

        errors = []

        all_vm = vds_get_node(conn)
        all_networks = networks_get_node(conn)
        all_storages = storages_get_node(conn)
        all_img = images_get_storages(conn, all_storages)

        if not all_networks:
            msg = _("You haven't defined any virtual networks")
            errors.append(msg)
        if not all_storages:
            msg = _("You haven't defined have any storage pools")
            errors.append(msg)
        if not have_kvm:
            msg = _("Your CPU doesn't support hardware virtualization")
            errors.append(msg)

        digits = [a for a in range(1, 601)]

        if not flavors and flavors != 'error':
            add_flavor = Flavor(name='micro', vcpu='1', ram='256', hdd='10')
            add_flavor.save()
            add_flavor = Flavor(name='mini', vcpu='1', ram='512', hdd='20')
            add_flavor.save()
            add_flavor = Flavor(name='small', vcpu='2', ram='1024', hdd='40')
            add_flavor.save()
            add_flavor = Flavor(name='medium', vcpu='2', ram='2048', hdd='80')
            add_flavor.save()
            add_flavor = Flavor(name='large', vcpu='4', ram='4096', hdd='160')
            add_flavor.save()
            add_flavor = Flavor(name='xlarge', vcpu='6', ram='8192', hdd='320')
            add_flavor.save()
            return HttpResponseRedirect(request.get_full_path())

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

                errors = []

                import re
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
                    stg = conn.storagePoolLookupByName(storage)

                    if not hdd_size:
                        if not img:
                            msg = _("First you need to create an image")
                            errors.append(msg)
                        else:
                            image = image_get_path(conn, img, all_storages)
                    else:
                        from libvirt import libvirtError
                        try:
                            new_volume(stg, vname, hdd_size)
                        except libvirtError as msg_error:
                            errors.append(msg_error.message)

                    if not errors:
                        if not img:
                            import virtinst.util as util

                            stg_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
                            if stg_type == 'dir':
                                vol = vname + '.img'
                            else:
                                vol = vname
                        else:
                            vol = img
                        vl = stg.storageVolLookupByName(vol)
                        image = vl.path()

                        from string import letters, digits
                        from random import choice

                        vnc_passwd = ''.join([choice(letters + digits) for i in range(12)])

                        new_vm = Vm(host_id=host_id, vname=vname, vnc_passwd=vnc_passwd)
                        new_vm.save()

                        add_vm(vname, ram, vcpu, image, net, vnc_passwd)

                        return HttpResponseRedirect('/vds/%s/%s/' % (host_id, vname))

        conn.close()

    return render_to_response('newvm.html', locals(), context_instance=RequestContext(request))
