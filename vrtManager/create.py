#
# Copyright (C) 2013 Webvirtmgr.
#
import virtinst
import string
from vrtManager import util
from vrtManager.connection import wvmConnect


class wvmCreate(wvmConnect):
    def get_storages_images(self):
        """
        Function return all images on all storages
        """
        images = []
        storages = self.get_storages()
        for storage in storages:
            stg = self.get_storage(storage)
            try:
                stg.refresh(0)
            except:
                pass
            for img in stg.listVolumes():
                if img.endswith('.iso'):
                    pass
                else:
                    images.append(img)
        return images

    def get_guest_cap(self):
        """Get guest capabilities"""
        return virtinst.CapabilitiesParser.guest_lookup(self.wvm)

    def create_volume(self, storage, name, size, format='qcow2'):
        size = int(size) * 1073741824
        stg = self.get_storage(storage)
        storage_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
        if storage_type == 'dir':
            name += '.img'
            alloc = 0
        else:
            alloc = size
        xml = """
            <volume>
                <name>%s</name>
                <capacity>%s</capacity>
                <allocation>%s</allocation>
                <target>
                    <format type='%s'/>
                </target>
            </volume>""" % (name, size, alloc, format)
        stg.createXML(xml, 0)
        try:
            stg.refresh(0)
        except:
            pass
        vol = stg.storageVolLookupByName(name)
        return vol.path()

    def get_volume_type(self, path):
        vol = self.get_volume_by_path(path)
        return util.get_xml_path(vol.XMLDesc(0), "/volume/target/format/@type")

    def get_volume_path(self, volume):
        storages = self.get_storages()
        for storage in storages:
            stg = self.get_storage(storage)
            if stg.info()[0] != 0:
                stg.refresh(0)
                for img in stg.listVolumes():
                    if img == volume:
                        vol = stg.storageVolLookupByName(img)
                        return vol.path()

    def _defineXML(self, xml):
        self.wvm.defineXML(xml)

    def create_instance(self, name, memory, vcpu, host_model, uuid, images, networks, virtio):
        """
        Create VM function
        """
        memory = int(memory) * 1024

        if self.is_kvm_supported():
            hypervisor_type = 'kvm'
        else:
            hypervisor_type = 'qemu'

        xml = """
                <domain type='%s'>
                  <name>%s</name>
                  <description>None</description>
                  <uuid>%s</uuid>
                  <memory unit='KiB'>%s</memory>
                  <vcpu>%s</vcpu>""" % (hypervisor_type, name, uuid, memory, vcpu)
        if host_model:
            xml += """<cpu mode='host-model'/>"""
        xml += """<os>
                    <type arch='%s'>%s</type>
                    <boot dev='hd'/>
                    <boot dev='cdrom'/>
                    <bootmenu enable='yes'/>
                  </os>""" % (self.get_guest_cap()[0].arch,
                              self.get_guest_cap()[0].os_type)
        xml += """<features>
                    <acpi/><apic/><pae/>
                  </features>
                  <clock offset="utc"/>
                  <on_poweroff>destroy</on_poweroff>
                  <on_reboot>restart</on_reboot>
                  <on_crash>restart</on_crash>
                  <devices>"""

        disk_letters = list(string.lowercase)
        for image, type in images.items():
            xml += """  <disk type='file' device='disk'>
                          <driver name='qemu' type='%s'/>
                          <source file='%s'/>""" % (type, image)
            if virtio:
                xml += """<target dev='vd%s' bus='virtio'/>""" % (disk_letters.pop(0),)
            else:
                xml += """<target dev='sd%s' bus='ide'/>""" % (disk_letters.pop(0),)
            xml += """</disk>"""

        xml += """  <disk type='file' device='cdrom'>
                      <driver name='qemu' type='raw'/>
                      <source file=''/>
                      <target dev='hda' bus='ide'/>
                      <readonly/>
                      <address type='drive' controller='0' bus='1' target='0' unit='1'/>
                    </disk>"""
        for net in networks.split(','):
            xml += """
                    <interface type='network'>
                        <source network='%s'/>""" % net
            if virtio:
                xml += """<model type='virtio'/>"""
            xml += """</interface>"""

        xml += """  <input type='mouse' bus='ps2'/>
                    <input type='tablet' bus='usb'/>
                    <graphics type='vnc' port='-1' autoport='yes' listen='0.0.0.0'>
                      <listen type='address' address='0.0.0.0'/>
                    </graphics>
                    <console type='pty'/>
                    <video>
                      <model type='cirrus'/>
                    </video>
                    <memballoon model='virtio'/>
                  </devices>
                </domain>"""
        self._defineXML(xml)
