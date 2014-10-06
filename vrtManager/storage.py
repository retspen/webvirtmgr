#
# Copyright (C) 2013 Webvirtmgr.
#
from vrtManager import util
from vrtManager.connection import wvmConnect


class wvmStorages(wvmConnect):
    def get_storages_info(self):
        get_storages = self.get_storages()
        storages = []
        for pool in get_storages:
            stg = self.get_storage(pool)
            stg_status = stg.isActive()
            stg_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
            if stg_status:
                stg_vol = len(stg.listVolumes())
            else:
                stg_vol = None
            stg_size = stg.info()[1]
            storages.append({'name': pool, 'status': stg_status,
                             'type': stg_type, 'volumes': stg_vol,
                             'size': stg_size})
        return storages

    def define_storage(self, xml, flag):
        self.wvm.storagePoolDefineXML(xml, flag)

    def create_storage(self, stg_type, name, source, target):
        xml = """
                <pool type='%s'>
                <name>%s</name>""" % (stg_type, name)
        if stg_type == 'logical':
            xml += """
                  <source>
                    <device path='%s'/>
                    <name>%s</name>
                    <format type='lvm2'/>
                  </source>""" % (source, name)
        if stg_type == 'logical':
            target = '/dev/' + name
        xml += """
                  <target>
                       <path>%s</path>
                  </target>
                </pool>""" % target
        self.define_storage(xml, 0)
        stg = self.get_storage(name)
        if stg_type == 'logical':
            stg.build(0)
        stg.create(0)
        stg.setAutostart(1)

    def create_storage_ceph(self, stg_type, name, ceph_pool, ceph_host, ceph_user, secret):
        xml = """
                <pool type='%s'>
                <name>%s</name>
                <source>
                    <name>%s</name>
                    <host name='%s' port='6789'/>
                    <auth username='%s' type='ceph'>
                        <secret uuid='%s'/>
                    </auth>
                </source>
                </pool>""" % (stg_type, name, ceph_pool, ceph_host, ceph_user, secret)
        self.define_storage(xml, 0)
        stg = self.get_storage(name)
        stg.create(0)
        stg.setAutostart(1)

    def create_storage_netfs(self, stg_type, name, netfs_host, source, source_format, target):
        xml = """
                <pool type='%s'>
                <name>%s</name>
                <source>
                    <host name='%s'/>
                    <dir path='%s'/>
                    <format type='%s'/>
                </source>
                <target>
                    <path>%s</path>
                </target>
                </pool>""" % (stg_type, name, netfs_host, source, source_format, target)
        self.define_storage(xml, 0)
        stg = self.get_storage(name)
        stg.create(0)
        stg.setAutostart(1)


class wvmStorage(wvmConnect):
    def __init__(self, host, login, passwd, conn, pool):
        wvmConnect.__init__(self, host, login, passwd, conn)
        self.pool = self.get_storage(pool)

    def get_name(self):
        return self.pool.name()

    def get_status(self):
        status = ['Not running', 'Initializing pool, not available', 'Running normally', 'Running degraded']
        try:
            return status[self.pool.info()[0]]
        except ValueError:
            return 'Unknown'

    def get_size(self):
        return [self.pool.info()[1], self.pool.info()[3]]

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
        vol_list = []

        for volname in vols:
            vol_list.append(
                {'name': volname,
                 'size': self.get_volume_size(volname),
                 'type': self.get_volume_type(volname)}
            )
        return vol_list

    def create_volume(self, name, size, vol_fmt='qcow2', metadata=False):
        size = int(size) * 1073741824
        storage_type = self.get_type()
        alloc = size
        if vol_fmt == 'unknown':
            vol_fmt = 'raw'
        if storage_type == 'dir':
            name += '.img'
            alloc = 0
        xml = """
            <volume>
                <name>%s</name>
                <capacity>%s</capacity>
                <allocation>%s</allocation>
                <target>
                    <format type='%s'/>
                </target>
            </volume>""" % (name, size, alloc, vol_fmt)
        self._createXML(xml, metadata)

    def clone_volume(self, name, clone, vol_fmt=None, metadata=False):
        storage_type = self.get_type()
        if storage_type == 'dir':
            clone += '.img'
        vol = self.get_volume(name)
        if not vol_fmt:
            vol_fmt = self.get_volume_type(name)
        xml = """
            <volume>
                <name>%s</name>
                <capacity>0</capacity>
                <allocation>0</allocation>
                <target>
                    <format type='%s'/>
                </target>
            </volume>""" % (clone, vol_fmt)
        self._createXMLFrom(xml, vol, metadata)
