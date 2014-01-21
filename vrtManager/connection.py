#
# Copyright (C) 2013 Webvirtmgr.
#
import libvirt
from datetime import datetime
from vrtManager import util

from libvirt import VIR_DOMAIN_XML_SECURE, libvirtError

CONN_SSH = 2
CONN_TCP = 1
SSH_PORT = 22
TCP_PORT = 16509

class wvmConnect(object):
    def __init__(self, host, login, passwd, conn):
        self.login = login
        self.host = host
        self.passwd = passwd
        self.conn = conn

        if self.conn == CONN_TCP:
            def creds(credentials, user_data):
                for credential in credentials:
                    if credential[0] == libvirt.VIR_CRED_AUTHNAME:
                        credential[4] = self.login
                        if len(credential[4]) == 0:
                            credential[4] = credential[3]
                    elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
                        credential[4] = self.passwd
                    else:
                        return -1
                return 0

            flags = [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE]
            auth = [flags, creds, None]
            uri = 'qemu+tcp://%s/system' % self.host
            try:
                self.wvm = libvirt.openAuth(uri, auth, 0)
            except libvirtError:
                raise libvirtError('Connection Failed')

        if self.conn == CONN_SSH:
            uri = 'qemu+ssh://%s@%s/system' % (self.login, self.host)
            try:
                self.wvm = libvirt.open(uri)
            except libvirtError as err:
                raise err.message

    def get_cap_xml(self):
        """Return xml capabilities"""
        return self.wvm.getCapabilities()

    def is_kvm_supported(self):
        """Return KVM capabilities."""
        return util.is_kvm_available(self.get_cap_xml())

    def get_storages(self):
        storages = []
        for pool in self.wvm.listStoragePools():
            storages.append(pool)
        for pool in self.wvm.listDefinedStoragePools():
            storages.append(pool)
        return storages

    def get_networks(self):
        virtnet = []
        for net in self.wvm.listNetworks():
            virtnet.append(net)
        for net in self.wvm.listDefinedNetworks():
            virtnet.append(net)
        return virtnet

    def get_storage(self, name):
        return self.wvm.storagePoolLookupByName(name)

    def get_volume_by_path(self, path):
        return self.wvm.storageVolLookupByPath(path)

    def get_network(self, net):
        return self.wvm.networkLookupByName(net)

    def get_instance(self, name):
        return self.wvm.lookupByName(name)

    def get_instances(self):
        instances = []
        for inst_id in self.wvm.listDomainsID():
            dom = self.wvm.lookupByID(int(inst_id))
            instances.append(dom.name())
        for name in self.wvm.listDefinedDomains():
            instances.append(name)
        return instances

    def get_snapshots(self):
        instance = []
        for snap_id in self.wvm.listDomainsID():
            dom = self.wvm.lookupByID(int(snap_id))
            if dom.snapshotNum(0) != 0:
                instance.append(dom.name())
        for name in self.wvm.listDefinedDomains():
            dom = self.wvm.lookupByName(name)
            if dom.snapshotNum(0) != 0:
                instance.append(dom.name())
        return instance

    def get_snapshot(self, name):
        """
        Function return all vds snaphots.
        """
        snapshots = {}
        dom = self.get_instance(name)
        snapshot_list = dom.snapshotListNames(0)
        for snapshot in snapshot_list:
            snapshots[snapshot] = (datetime.fromtimestamp(int(snapshot)), dom.info()[0])
        return snapshots

    def snapshot_delete(self, name, snapshot):
        """
        Function delete vds snaphots.
        """
        dom = self.get_instance(name)
        snap = dom.snapshotLookupByName(snapshot, 0)
        snap.delete(0)

    def snapshot_revert(self, name, snapshot):
        """
        Function revert vds snaphots.
        """
        dom = self.get_instance(name)
        snap = dom.snapshotLookupByName(snapshot, 0)
        dom.revertToSnapshot(snap, 0)

    def get_host_instances(self):
        vname = {}
        memory = self.wvm.getInfo()[1] * 1048576
        for name in self.get_instances():
            dom = self.get_instance(name)
            mem = util.get_xml_path(dom.XMLDesc(0), "/domain/currentMemory")
            mem = int(mem) * 1024
            mem_usage = (mem * 100) / memory
            cur_vcpu = util.get_xml_path(dom.XMLDesc(0), "/domain/vcpu/@current")
            if cur_vcpu:
                vcpu = cur_vcpu
            else:
                vcpu = util.get_xml_path(dom.XMLDesc(0), "/domain/vcpu")
            vname[dom.name()] = (dom.info()[0], vcpu, mem, mem_usage)
        return vname

    def close(self):
        """Close connection"""
        self.wvm.close()