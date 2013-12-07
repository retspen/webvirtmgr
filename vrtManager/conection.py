#
# Copyright (C) 2013 Webvirtmgr.
#

import re
import string

import libvirt
import virtinst

from libvirt import VIR_DOMAIN_XML_SECURE, libvirtError

CONN_SSH = 2
CONN_TCP = 1

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
                raise libvirtError('Connetion Failed')

        if self.conn == CONN_SSH:
            uri = 'qemu+ssh://%s@%s/system' % (self.login, self.host)
            try:
                self.wvm = libvirt.open(uri)
            except libvirtError as err:
                raise err.message

    def get_cap_xml(self):
        """Return xml capabilities"""
        return self.wvm.getCapabilities()

    def get_cap(self):
        """Return parse capabilities"""
        return virtinst.CapabilitiesParser.parse(self.get_cap_xml())

    def is_kvm_supported(self):
        """Return KVM capabilities."""
        return self.get_cap().is_kvm_available()

    def get_storages(self):
        """
        Function return host server storages.
        """
        storages = []
        for pool in self.wvm.listStoragePools():
            storages.append(pool)
        for pool in self.wvm.listDefinedStoragePools():
            storages.append(pool)
        return storages

    def get_networks(self):
        """
        Function return host server virtual networks.
        """
        virtnet = []
        for net in self.wvm.listNetworks():
            virtnet.append(net)
        for net in self.wvm.listDefinedNetworks():
            virtnet.append(net)
        return virtnet

    def define_storage(self, xml, flag):
        self.wvm.storagePoolDefineXML(xml, flag)

    def get_storage(self, name):
        return self.wvm.storagePoolLookupByName(name)

    def get_volume_by_path(self, path):
        return self.wvm.storageVolLookupByPath(path)

    def create_storage(self, type, name, source, target):
        """
        Function create storage pool.
        """
        xml = """
                <pool type='%s'>
                <name>%s</name>""" % (type, name)
        if type == 'logical':
            xml += """
                  <source>
                    <device path='%s'/>
                    <name>%s</name>
                    <format type='lvm2'/>
                  </source>""" % (source, name)
        if type == 'logical':
            target = '/dev/' + name
        xml += """
                  <target>
                       <path>%s</path>
                  </target>
                </pool>""" % target
        self.define_storage(xml, 0)
        stg = self.get_storage(name)
        if type == 'logical':
            stg.build(0)
        stg.create(0)
        stg.setAutostart(1)

    def get_network(self, net):
        return self.wvm.networkLookupByName(net)

    def define_network(self, xml):
        self.wvm.networkDefineXML(xml)

    def create_network(self, name, forward, gateway, mask, dhcp, bridge):
        """
        Function create network pool.
        """
        xml = """
            <network>
                <name>%s</name>""" % name
        if forward in ['nat', 'route', 'bridge']:
            xml += """<forward mode='%s'/>""" % forward
        xml += """<bridge """
        if forward in ['nat', 'route', 'none']:
            xml += """stp='on' delay='0'"""
        if forward == 'bridge':
            xml += """name='%s'""" % bridge
        xml += """/>"""
        if forward != 'bridge':
            xml += """
                        <ip address='%s' netmask='%s'>""" % (gateway, mask)
            if dhcp:
                xml += """<dhcp>
                            <range start='%s' end='%s' />
                        </dhcp>""" % (dhcp[0], dhcp[1])

            xml += """</ip>"""
        xml += """</network>"""
        self.define_network(xml)
        net = self.get_network(name)
        net.create()
        net.setAutostart(1)

    def get_instances(self):
        """
        Get all instance in host server
        """
        instances = []
        for inst_id in self.wvm.listDomainsID():
            dom = self.wvm.lookupByID(int(inst_id))
            instances.append(dom.name())
        for name in self.wvm.listDefinedDomains():
            instances.append(name)
        return instances

    def snapshots_get_node(self):
        """
        Function return all snaphots on node.
        """
        vname = {}
        for vm_id in self.wvm.listDomainsID():
            vm_id = int(vm_id)
            dom = self.wvm.lookupByID(vm_id)
            if dom.snapshotNum(0) != 0:
                vname[dom.name()] = dom.info()[0]
        for name in self.wvm.listDefinedDomains():
            dom = self.lookupVM(name)
            if dom.snapshotNum(0) != 0:
                vname[dom.name()] = dom.info()[0]
        return vname

    def snapshots_get_vds(self, vname):
        """
        Function return all vds snaphots.
        """
        snapshots = {}
        dom = self.lookupVM(vname)
        all_snapshot = dom.snapshotListNames(0)
        for snapshot in all_snapshot:
            snapshots[snapshot] = (datetime.fromtimestamp(int(snapshot)), dom.info()[0])
        return snapshots

    def snapshot_delete(self, vname, name_snap):
        """
        Function delete vds snaphots.
        """
        dom = self.lookupVM(vname)
        snap = dom.snapshotLookupByName(name_snap, 0)
        snap.delete(0)

    def snapshot_revert(self, vname, name_snap):
        """
        Function revert vds snaphots.
        """
        dom = self.lookupVM(vname)
        snap = dom.snapshotLookupByName(name_snap, 0)
        dom.revertToSnapshot(snap, 0)


    def vds_on_cluster(self):
        """
        Function show all host and vds
        """
        vname = {}
        host_mem = self.wvm.getInfo()[1] * 1048576
        for vm_id in self.wvm.listDomainsID():
            vm_id = int(vm_id)
            dom = self.wvm.lookupByID(vm_id)
            mem = get_xml_path(dom.XMLDesc(0), "/domain/memory")
            mem = int(mem) * 1024
            mem_usage = (mem * 100) / host_mem
            vcpu = get_xml_path(dom.XMLDesc(0), "/domain/vcpu")
            vname[dom.name()] = (dom.info()[0], vcpu, mem, mem_usage)
        for name in self.wvm.listDefinedDomains():
            dom = self.lookupVM(name)
            mem = get_xml_path(dom.XMLDesc(0), "/domain/memory")
            mem = int(mem) * 1024
            mem_usage = (mem * 100) / host_mem
            vcpu = get_xml_path(dom.XMLDesc(0), "/domain/vcpu")
            vname[dom.name()] = (dom.info()[0], vcpu, mem, mem_usage)
        return vname

    def close(self):
        """Close connection"""
        self.wvm.close()