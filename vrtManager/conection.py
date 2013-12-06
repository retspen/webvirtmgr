#
# Copyright (C) 2013 Webvirtmgr.
#

import re
import string

import libvirt
import virtinst

from vrtManager.IPy import IP
from datetime import datetime
from xml.etree import ElementTree
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

    def get_instance(self, name):
        return self.wvm.lookupByName(name)

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

    def vnc_get_port(self, vname):
        """
        Function rever vds snaphots.
        """
        dom = self.lookupVM(vname)
        port = get_xml_path(dom.XMLDesc(0), "/domain/devices/graphics/@port")
        return port

    def vds_mount_iso(self, vname, image):
        """
        Function mount iso image on vds. Changes on XML config.
        """
        storages = self.storages_get_node()
        dom = self.lookupVM(vname)

        for storage in storages:
            stg = self.storagePool(storage)
            for img in stg.listVolumes():
                if image == img:
                    if dom.info()[0] == 1:
                        vol = stg.storageVolLookupByName(image)
                        xml = """<disk type='file' device='cdrom'>
                                    <driver name='qemu' type='raw'/>
                                    <target dev='sda' bus='ide'/>
                                    <source file='%s'/>
                                 </disk>""" % vol.path()
                        dom.attachDevice(xml)
                        xmldom = dom.XMLDesc(VIR_DOMAIN_XML_SECURE)
                        self.wvm.defineXML(xmldom)
                    if dom.info()[0] == 5:
                        vol = stg.storageVolLookupByName(image)
                        xml = dom.XMLDesc(VIR_DOMAIN_XML_SECURE)
                        newxml = "<disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>\n      <source file='%s'/>" % vol.path()
                        xmldom = xml.replace(
                            "<disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>", newxml)
                        self.wvm.defineXML(xmldom)

    def vds_umount_iso(self, vname, image):
        """
        Function umount iso image on vds. Changes on XML config.
        """
        dom = self.lookupVM(vname)
        if dom.info()[0] == 1:
            xml = """<disk type='file' device='cdrom'>
                         <driver name="qemu" type='raw'/>
                         <target dev='sda' bus='ide'/>
                         <readonly/>
                      </disk>"""
            dom.attachDevice(xml)
            xmldom = dom.XMLDesc(VIR_DOMAIN_XML_SECURE)
            self.wvm.defineXML(xmldom)
        if dom.info()[0] == 5:
            xml = dom.XMLDesc(VIR_DOMAIN_XML_SECURE)
            xmldom = xml.replace("<source file='%s'/>\n" % image, '')
            self.wvm.defineXML(xmldom)

    def vds_cpu_usage(self, vname):
        """
        Function return vds cpu usage.
        """
        cpu_usage = {}
        dom = self.lookupVM(vname)
        if dom.info()[0] == 1:
            nbcore = self.wvm.getInfo()[2]
            cpu_use_ago = dom.info()[4]
            time.sleep(1)
            cpu_use_now = dom.info()[4]
            diff_usage = cpu_use_now - cpu_use_ago
            cpu_usage['cpu'] = 100 * diff_usage / (1 * nbcore * 10 ** 9L)
        else:
            cpu_usage['cpu'] = 0
        return cpu_usage

    def vds_disk_usage(self, vname):
        """
        Function return vds block IO.
        """
        devices=[]
        dev_usage = []
        dom = self.lookupVM(vname)
        tree = ElementTree.fromstring(dom.XMLDesc(0))

        for source, target in zip(tree.findall("devices/disk/source"), tree.findall("devices/disk/target")):
            if source.get("file").endswith('.img'):
                devices.append([source.get("file"), target.get("dev")])
        for dev in devices:
            rd_use_ago = dom.blockStats(dev[0])[1]
            wr_use_ago = dom.blockStats(dev[0])[3]
            time.sleep(1)
            rd_use_now = dom.blockStats(dev[0])[1]
            wr_use_now = dom.blockStats(dev[0])[3]
            rd_diff_usage = rd_use_now - rd_use_ago
            wr_diff_usage = wr_use_now - wr_use_ago
            dev_usage.append({'dev': dev[1], 'rd': rd_diff_usage, 'wr': wr_diff_usage})
        return dev_usage

    def vds_network_usage(self, vname):
        """
        Function return vds Bandwidth.
        """
        devices=[]
        dev_usage = []
        dom = self.lookupVM(vname)
        tree = ElementTree.fromstring(dom.XMLDesc(0))

        for target in tree.findall("devices/interface/target"):
            devices.append(target.get("dev"))
        for i, dev in enumerate(devices):
            rx_use_ago = dom.interfaceStats(dev)[0]
            tx_use_ago = dom.interfaceStats(dev)[4]
            time.sleep(1)
            rx_use_now = dom.interfaceStats(dev)[0]
            tx_use_now = dom.interfaceStats(dev)[4]
            rx_diff_usage = (rx_use_now - rx_use_ago) * 8
            tx_diff_usage = (tx_use_now - tx_use_ago) * 8
            dev_usage.append({'dev': i, 'rx': rx_diff_usage, 'tx': tx_diff_usage})
        return dev_usage

    def vds_get_info(self, vname):
        """
        Function return vds info.
        """
        info = []
        dom = self.lookupVM(vname)
        xml = dom.XMLDesc(0)
        info.append(get_xml_path(xml, "/domain/vcpu"))
        mem = get_xml_path(xml, "/domain/memory")
        mem = int(mem) / 1024
        info.append(int(mem))

        def get_networks(ctx):
            result = []
            for interface in ctx.xpathEval('/domain/devices/interface'):
                mac = interface.xpathEval('mac/@address')[0].content
                nic = interface.xpathEval('source/@network|source/@bridge')[0].content
                result.append({'mac': mac, 'nic': nic})
            return result

        info.append(get_xml_path(xml, func=get_networks))
        description = get_xml_path(xml, "/domain/description")
        info.append(description)
        return info

    def vds_get_hdd(self, vname):
        """
        Function return vds hdd info.
        """
        all_hdd_dev = {}
        storages = self.storages_get_node()
        dom = self.lookupVM(vname)
        xml = dom.XMLDesc(0)

        for num in range(1, 5):
            hdd_dev = get_xml_path(xml, "/domain/devices/disk[%s]/@device" % (num))
            if hdd_dev == 'disk':
                dev_bus = get_xml_path(xml, "/domain/devices/disk[%s]/target/@dev" % (num))
                hdd = get_xml_path(xml, "/domain/devices/disk[%s]/source/@file" % (num))
                # If xml create custom
                if not hdd:
                    hdd = get_xml_path(xml, "/domain/devices/disk[%s]/source/@dev" % (num))
                try:
                    img = self.storageVolPath(hdd)
                    img_vol = img.name()
                    for storage in storages:
                        stg = self.storagePool(storage)
                        if stg.info()[0] != 0:
                            stg.refresh(0)
                            for img in stg.listVolumes():
                                if img == img_vol:
                                    vol = img
                                    vol_stg = storage
                    all_hdd_dev[dev_bus] = vol, vol_stg
                except Exception:
                    all_hdd_dev[dev_bus] = hdd, 'Not in the pool'
        return all_hdd_dev

    def vds_get_media(self, vname):
        """
        Function return vds media info.
        """
        dom = self.lookupVM(vname)
        xml = dom.XMLDesc(0)
        for num in range(1, 5):
            hdd_dev = get_xml_path(xml, "/domain/devices/disk[%s]/@device" % (num))
            if hdd_dev == 'cdrom':
                media = get_xml_path(xml, "/domain/devices/disk[%s]/source/@file" % (num))
                if media:
                    try:
                        vol = self.storageVolPath(media)
                        return vol.name(), vol.path()
                    except Exception:
                        return media, media
                else:
                    return None, None

    def vds_set_vnc_passwd(self, vname, passwd):
        """
        Function set vnc password to vds.
        """
        dom = self.lookupVM(vname)
        xml = dom.XMLDesc(VIR_DOMAIN_XML_SECURE)
        find_tag = re.findall('<graphics.*/>', xml)
        if find_tag:
            close_tag = '/'
        else:
            close_tag = ''
        newxml = "<graphics type='vnc' passwd='%s'%s>" % (passwd, close_tag)
        xmldom = re.sub('<graphics.*>', newxml, xml)
        self.wvm.defineXML(xmldom)

    def vds_edit(self, vname, description, ram, vcpu):
        """
        Function change ram and cpu on vds.
        """
        dom = self.lookupVM(vname)
        xml = dom.XMLDesc(VIR_DOMAIN_XML_SECURE)
        memory = int(ram) * 1024
        xml_memory = "<memory unit='KiB'>%s</memory>" % memory
        xml_memory_change = re.sub('<memory.*memory>', xml_memory, xml)
        xml_curmemory = "<currentMemory unit='KiB'>%s</currentMemory>" % memory
        xml_curmemory_change = re.sub('<currentMemory.*currentMemory>', xml_curmemory, xml_memory_change)
        xml_vcpu = "<vcpu>%s</vcpu>" % vcpu
        xml_vcpu_change = re.sub('<vcpu.*vcpu>', xml_vcpu, xml_curmemory_change)
        xml_description = "<description>%s</description>" % description
        xml_description_change = re.sub('<description.*description>', xml_description, xml_vcpu_change)
        self.wvm.defineXML(xml_description_change)

    def defineXML(self, xml):
        """
        Funciton define VM config
        """
        self.wvm.defineXML(xml)


    def get_all_media(self):
        """
        Function return all media.
        """
        iso = []
        storages = self.storages_get_node()
        for storage in storages:
            stg = self.storagePool(storage)
            if stg.info()[0] != 0:
                stg.refresh(0)
                for img in stg.listVolumes():
                    if re.findall(".iso", img):
                        iso.append(img)
        return iso

    def vds_remove_hdd(self, vname):
        """
        Function delete vds hdd.
        """
        dom = self.lookupVM(vname)
        img = get_xml_path(dom.XMLDesc(0), "/domain/devices/disk[1]/source/@file")
        vol = self.storageVolPath(img)
        vol.delete(0)

    def vds_create_snapshot(self, vname):
        """
        Function create vds snapshot.
        """
        dom = self.lookupVM(vname)
        xml = """<domainsnapshot>\n
                     <name>%d</name>\n
                     <state>shutoff</state>\n
                     <creationTime>%d</creationTime>\n""" % (time.time(), time.time())
        xml += dom.XMLDesc(VIR_DOMAIN_XML_SECURE)
        xml += """<active>0</active>\n
                  </domainsnapshot>"""
        dom.snapshotCreateXML(xml, 0)

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