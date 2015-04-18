#
# Copyright (C) 2013 Webvirtmgr.
#
import string
from lxml import etree
from lxml.builder import E
from vrtManager import util
from vrtManager.connection import wvmConnect

from webvirtmgr.settings import QEMU_CONSOLE_DEFAULT_TYPE


def get_rbd_storage_data(stg):
    xml = stg.XMLDesc(0)
    ceph_user = util.get_xml_path(xml, "/pool/source/auth/@username")
    ceph_host = util.get_xml_path(xml, "/pool/source/host/@name")
    secrt_uuid = util.get_xml_path(xml, "/pool/source/auth/secret/@uuid")
    return ceph_user, secrt_uuid, ceph_host


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

    def get_os_type(self):
        """Get guest capabilities"""
        return util.get_xml_path(self.get_cap_xml(), "/capabilities/guest/os_type")

    def get_host_arch(self):
        """Get guest capabilities"""
        return util.get_xml_path(self.get_cap_xml(), "/capabilities/host/cpu/arch")

    def create_volume(self, storage, name, size, format='qcow2', metadata=False):
        size = int(size) * 1073741824
        stg = self.get_storage(storage)
        storage_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
        if storage_type == 'dir':
            name += '.img'
            alloc = 0
        else:
            alloc = size
            metadata = False
        xml = """
            <volume>
                <name>%s</name>
                <capacity>%s</capacity>
                <allocation>%s</allocation>
                <target>
                    <format type='%s'/>
                </target>
            </volume>""" % (name, size, alloc, format)
        stg.createXML(xml, metadata)
        try:
            stg.refresh(0)
        except:
            pass
        vol = stg.storageVolLookupByName(name)
        return vol.path()

    def get_volume_type(self, path):
        vol = self.get_volume_by_path(path)
        vol_type = util.get_xml_path(vol.XMLDesc(0), "/volume/target/format/@type")
        if vol_type == 'unknown':
            return 'raw'
        if vol_type:
            return vol_type
        else:
            return 'raw'

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

    def get_storage_by_vol_path(self, vol_path):
        vol = self.get_volume_by_path(vol_path)
        return vol.storagePoolLookupByVolume()

    def clone_from_template(self, clone, template, **kwargs):
        vol = self.get_volume_by_path(template)
        stg = vol.storagePoolLookupByVolume()
        storage_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
        format = util.get_xml_path(vol.XMLDesc(0), "/volume/target/format/@type")
        metadata = kwargs.get('metadata', False)
        capacity = 0
        capacity_unit = util.get_xml_path(vol.XMLDesc(0), "/volume/capacity/@unit")
        meta_base = kwargs.get('meta_base', False)
        if storage_type == 'dir':
            clone += '.img'
        else:
            metadata = False
            meta_base = False
        if format != 'qcow2':
            meta_base = False
        v_tree = E.volume(E.name(clone))
        v_tree.append(E.allocation('0'))
        target = E.target(E.format(type=format))
        if meta_base:
            v_tree.append(E.backingStore(
                E.path(vol.path()),
                E.format(type=format)))
            capacity = util.get_xml_path(vol.XMLDesc(0), "/volume/capacity")
        v_tree.append(E.capacity(str(capacity), unit=capacity_unit))
        v_tree.append(target)
        xml = etree.tostring(v_tree)
        stg.createXML(xml, metadata)
        clone_vol = stg.storageVolLookupByName(clone)
        return clone_vol.path()

    def _defineXML(self, xml):
        self.wvm.defineXML(xml)

    def delete_volume(self, path):
        vol = self.get_volume_by_path(path)
        vol.delete()

    def create_instance(self, name, memory, vcpu, host_model, uuid, images, networks, virtio, mac=None):
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
                  </os>""" % (self.get_host_arch(), self.get_os_type())
        xml += """<features>
                    <acpi/><apic/><pae/>
                  </features>
                  <clock offset="utc"/>
                  <on_poweroff>destroy</on_poweroff>
                  <on_reboot>restart</on_reboot>
                  <on_crash>restart</on_crash>
                  <devices>"""

        disk_letters = list(string.lowercase)
        for image, img_type in images.items():
            stg = self.get_storage_by_vol_path(image)
            stg_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")

            if stg_type == 'rbd':
                ceph_user, secrt_uuid, ceph_host = get_rbd_storage_data(stg)
                xml += """<disk type='network' device='disk'>
                            <driver name='qemu' type='%s'/>
                            <auth username='%s'>
                                <secret type='ceph' uuid='%s'/>
                            </auth>
                            <source protocol='rbd' name='%s'>
                                <host name='%s' port='6789'/>
                            </source>""" % (img_type, ceph_user, secrt_uuid, image, ceph_host)
            else:
                xml += """<disk type='file' device='disk'>
                            <driver name='qemu' type='%s'/>
                            <source file='%s'/>""" % (img_type, image)

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
            xml += """<interface type='network'>"""
            if mac:
                xml += """<mac address='%s'/>""" % mac
            xml += """<source network='%s'/>""" % net
            if virtio:
                xml += """<model type='virtio'/>"""
            xml += """</interface>"""

        xml += """  <input type='mouse' bus='ps2'/>
                    <input type='tablet' bus='usb'/>
                    <graphics type='%s' port='-1' autoport='yes' listen='0.0.0.0'>
                      <listen type='address' address='0.0.0.0'/>
                    </graphics>
                    <console type='pty'/>
                    <video>
                      <model type='cirrus'/>
                    </video>
                    <memballoon model='virtio'/>
                  </devices>
                </domain>""" % QEMU_CONSOLE_DEFAULT_TYPE
        self._defineXML(xml)
