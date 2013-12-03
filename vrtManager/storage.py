#
# Copyright (C) 2013 Webvirtmgr.
#
import virtinst
from vrtManager import util
from vrtManager.conection import wvmConnect


class wvmStorage(object):
    def __init__(self, conn, pool):
        self.pool = pool
        self.conn = conn

    def get_name(self):
        return self.pool.name()

    def get_size(self):
        return [self.pool.info()[1], self.pool.info()[2], self.pool.info()[3]]

    def _XMLDesc(self, flags):
        return self.pool.XMLDesc(flags)

    def _define(self, xml):
        return self.conn.vmm.storagePoolDefineXML(xml, 0)

    def set_active(self, state):
        self.active = state
        self.refresh_xml()

    def is_active(self):
        return self.active

    def can_change_alloc(self):
        typ = self.get_type()
        return (typ in [virtinst.Storage.StoragePool.TYPE_LOGICAL])

    def get_uuid(self):
        return self.uuid

    def start(self):
        self.pool.create(0)
        self.idle_add(self.refresh_xml)

    def stop(self):
        self.pool.destroy()
        self.idle_add(self.refresh_xml)

    def delete(self, nodelete=True):
        if nodelete:
            self.pool.undefine()
        else:
            self.pool.delete(0)
        del(self.pool)

    def set_autostart(self, value):
        self.pool.setAutostart(value)

    def get_autostart(self):
        return self.pool.autostart()

    def get_target_path(self):
        return util.get_xml_path(self.get_xml(), "/pool/target/path")

    def get_allocation(self):
        return long(util.get_xml_path(self.get_xml(), "/pool/allocation"))

    def get_available(self):
        return long(util.get_xml_path(self.get_xml(), "/pool/available"))

    def get_capacity(self):
        return long(util.get_xml_path(self.get_xml(), "/pool/capacity"))

    def get_pretty_allocation(self):
        return util.pretty_bytes(self.get_allocation())

    def get_pretty_available(self):
        return util.pretty_bytes(self.get_available())

    def get_pretty_capacity(self):
        return util.pretty_bytes(self.get_capacity())

    def get_type(self):
        return util.xpath(self.get_xml(), "/pool/@type")

    def get_volumes(self):
        self.update_volumes()
        return self._volumes

    def get_volume(self, uuid):
        return self._volumes[uuid]

    def refresh(self):
        if not self.active:
            return

        def cb():
            self.refresh_xml()
            self.update_volumes(refresh=True)
            self.emit("refreshed")

        self.pool.refresh(0)
        self.idle_add(cb)

    def update_volumes(self, refresh=False):
        if not self.is_active():
            self._volumes = {}
            return

        vols = self.pool.listVolumes()
        new_vol_list = {}

        for volname in vols:
            if volname in self._volumes:
                new_vol_list[volname] = self._volumes[volname]
                if refresh:
                    new_vol_list[volname].refresh_xml()
            else:
                new_vol_list[volname] = vmmStorageVolume(self.conn,
                                    self.pool.storageVolLookupByName(volname),
                                    volname)
        self._volumes = new_vol_list