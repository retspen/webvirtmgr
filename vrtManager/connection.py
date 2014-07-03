#
# Copyright (C) 2013 Webvirtmgr.
#
import libvirt
from vrtManager import util

from libvirt import libvirtError

CONN_TLS = 3
CONN_SSH = 2
CONN_TCP = 1
TLS_PORT = 16514
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

        if self.conn == CONN_TLS:
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
            uri = 'qemu+tls://%s@%s/system' % (self.login, self.host)
            try:
                self.wvm = libvirt.openAuth(uri, auth, 0)
            except libvirtError:
                raise libvirtError('Connection Failed')

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

    def get_ifaces(self):
        interface = []
        for inface in self.wvm.listInterfaces():
            interface.append(inface)
        for inface in self.wvm.listDefinedInterfaces():
            interface.append(inface)
        return interface

    def get_iface(self, name):
        return self.wvm.interfaceLookupByName(name)

    def get_secrets(self):
        return self.wvm.listSecrets()

    def get_secret(self, uuid):
        return self.wvm.secretLookupByUUIDString(uuid)

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

    def get_net_device(self):
        netdevice = []
        for dev in self.wvm.listAllDevices(0):
            xml = dev.XMLDesc(0)
            dev_type = util.get_xml_path(xml, '/device/capability/@type')
            if dev_type == 'net':
                netdevice.append(util.get_xml_path(xml, '/device/capability/interface'))
        return netdevice

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
