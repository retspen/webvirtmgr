#
# Copyright (C) 2013 Webvirtmgr.
#
import virtinst
from vrtManager import util
from vrtManager.conection import wvmConnect


class wvmStorage(wvmConnect):
    def __init__(self, host, login, passwd, conn, pool):
        wvmConnect.__init__(self, host, login, passwd, conn)
        self.pool = self.wvm.storagePoolLookupByName(pool)

    def get_name(self):
        return self.pool.name()

    def get_size(self):
        return [self.pool.info()[1], self.pool.info()[2], self.pool.info()[3]]

    def _XMLDesc(self, flags):
        return self.pool.XMLDesc(flags)

    def _createXML(self, xml, flags):
        self.pool.createXML(xml, flags)

    def _createXMLFrom(self, xml, vol, flags):
        self.pool.createXMLFrom(xml, vol, flags)

    def _define(self, xml):
        return self.wvm.storagePoolDefineXML(xml, 0)

    def is_active(self):
        return self.pool.isActive()

    def get_uuid(self):
        return self.pool.UUIDString()

    def start(self):
        self.pool.create(0)

    def stop(self):
        self.pool.destroy()

    def delete(self):
        self.pool.undefine()

    def get_autostart(self):
        return self.pool.autostart()

    def set_autostart(self, value):
        self.pool.setAutostart(value)

    def get_type(self):
        return util.get_xml_path(self._XMLDesc(0), "/pool/@type")

    def get_target_path(self):
        return util.get_xml_path(self._XMLDesc(0), "/pool/target/path")

    def get_allocation(self):
        return long(util.get_xml_path(self._XMLDesc(0), "/pool/allocation"))

    def get_available(self):
        return long(util.get_xml_path(self._XMLDesc(0), "/pool/available"))

    def get_capacity(self):
        return long(util.get_xml_path(self._XMLDesc(0), "/pool/capacity"))

    def get_pretty_allocation(self):
        return util.pretty_bytes(self.get_allocation())

    def get_pretty_available(self):
        return util.pretty_bytes(self.get_available())

    def get_pretty_capacity(self):
        return util.pretty_bytes(self.get_capacity())

    def get_volumes(self):
        return self.pool.listVolumes()

    def get_volume(self, name):
        return self.pool.storageVolLookupByName(name)

    def get_volume_size(self, name):
        vol = self.get_volume(name)
        return vol.info()[1]

    def _vol_XMLDesc(self, name):
        vol = self.get_volume(name)
        return vol.XMLDesc(0)

    def del_volume(self, name):
        vol = self.pool.storageVolLookupByName(name)
        vol.delete(0)

    def get_volume_type(self, name):
        vol_xml = self._vol_XMLDesc(name)
        return util.get_xml_path(vol_xml, "/volume/target/format/@type")

    def refresh(self):
        self.pool.refresh(0)

    def update_volumes(self):
        try:
            self.refresh()
        except Exception:
            pass
        vols = self.get_volumes()
        vol_list = {}

        for volname in vols:
            vol_list[volname] = self.get_volume_size(volname), self.get_volume_type(volname)
        return vol_list

    def create_volume(self, name, size, format='qcow2'):
        size = int(size) * 1073741824
        storage_type = self.get_type()
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
        self._createXML(xml, 0)

    def clone_volume(self, name, clone, format=None):
        storage_type = self.get_type()
        if storage_type == 'dir':
            clone += '.img'
        vol = self.get_volume(name)
        if not format:
            format = self.get_volume_type(name)
        xml = """
            <volume>
                <name>%s</name>
                <capacity>0</capacity>
                <allocation>0</allocation>
                <target>
                    <format type='%s'/>
                </target>
            </volume>""" % (clone, format)
        self._createXMLFrom(xml, vol, 0)
