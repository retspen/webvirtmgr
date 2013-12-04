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

    def _define(self, xml):
        return self.wvm.storagePoolDefineXML(xml, 0)

    def get_autostart(self):
        return self.pool.UUID()

    def is_active(self):
        return self.pool.isActive()

    def get_uuid(self):
        return self.pool.UUID()

    def start(self):
        self.pool.create(0)

    def stop(self):
        self.pool.destroy()

    def delete(self):
        self.pool.undefine()

    def set_autostart(self, value):
        self.pool.setAutostart(value)

    def get_autostart(self):
        return self.pool.autostart()

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

    def refresh(self):
        self.pool.refresh(0)

    def update_volumes(self):
        vols = self.get_volumes()
        vol_list = {}

        for volname in vols:
            vol = self.get_volume(self, volname)
            vol_xml = vol.XMLDesc(0)
            vol_type = util.get_xml_path(vol_xml, "/volume/target/format/@type")
            vol_list[volname] = vol.info()[1], vol_type
        return vol_list