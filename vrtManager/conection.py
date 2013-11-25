#
# Copyright (C) 2013 Webvirtmgr.
#

import re
import time
import libvirt
import string
from vrtManager.IPy import IP
from datetime import datetime
from xml.etree import ElementTree
from libvirt import VIR_DOMAIN_XML_SECURE

CONN_SSH = 0
CONN_TCP = 1

class wvmConnect(object):
    def __init__(self, host, login, passwd, conn):
        self.login = login
        self.host = host
        self.passwd = passwd
        self.conn = conn

    def open(self):
        """

        Return connection object.

        """
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
            self.wvm = libvirt.openAuth(uri, auth, 0)

        if self.conn == CONN_SSH:
            
            uri = 'qemu+ssh://%s@%s/system' % (self.login, self.host)
            self.wvm = libvirt.open(uri)
        
        return self.wvm

    def get_machine_capable(conn):
         """Return machine capabilities."""

        machine = get_xml_path(conn.getCapabilities(), "/capabilities/guest/arch/machine/@canonical")
        if not machine:
            machine = 'pc-1.0'
        return machine


    def is_kvm_capable(conn):
        """Return KVM capabilities."""

        kvm = re.search('kvm', conn.getCapabilities())
        if kvm:
            return True
        return False

    def get_emulator_capable(conn):
        """Return emulator capabilities."""

        if re.findall('/usr/libexec/qemu-kvm', conn.getCapabilities()):
            return '/usr/libexec/qemu-kvm'
        elif re.findall('/usr/bin/kvm', conn.getCapabilities()):
            return '/usr/bin/kvm'
        elif re.findall('/usr/bin/qemu-kvm', conn.getCapabilities()):
            return '/usr/bin/qemu-kvm'
        else:
            return '/usr/bin/qemu-system-x86_64'

    def lookupVM(self, vname):
        """

        Return VM object.

        """
        try:
            dom = self.open.lookupByName(vname)
        except Exception:
            dom = None
        return dom

    def storagePool(self, storage):
        """

        Return storage object.

        """
        try:
            stg = self.open.storagePoolLookupByName(storage)
        except Exception:
            stg = None
        return stg

    def networkPool(self, network):
        """

        Return network object.

        """
        try:
            net = self.open.networkLookupByName(network)
        except Exception:
            net = None
        return net

    def storageVol(self, volume, storage):
        """

        Return volume object.

        """
        stg = self.storagePool(storage)
        stg_type = get_xml_path(stg.XMLDesc(0), "/pool/@type")
        if stg_type == 'dir':
            volume += '.img'
        stg_volume = stg.storageVolLookupByName(volume)
        return stg_volume

    def storageVolPath(self, volume):
        """

        Return volume object by path.

        """
        stg_volume = self.open.storageVolLookupByPath(volume)
        return stg_volume

    def hard_accel_node(self):
        """

        Check hardware acceleration.

        """
        xml = self.open.getCapabilities()
        kvm = re.search('kvm', xml)
        if kvm:
            return True
        else:
            return False

    def get_vol_image_type(self, storages, vol):
        for storage in storages:
            stg = self.storagePool(storage)
            stg_type = get_xml_path(stg.XMLDesc(0), "/pool/@type")
            if stg_type == 'logical':
                image_type = 'raw'
            if stg_type == 'dir':
                if stg.info()[0] != 0:
                    stg.refresh(0)
                    for img in stg.listVolumes():
                        if img == vol:
                            vol = stg.storageVolLookupByName(img)
                            image_type = get_xml_path(vol.XMLDesc(0), "/volume/target/format/@type")
        return image_type


    def vds_get_node(self):
        """

        Get all VM in host server

        """
        vname = {}
        for vm_id in self.open.listDomainsID():
            vm_id = int(vm_id)
            dom = self.open.lookupByID(vm_id)
            vname[dom.name()] = dom.info()[0]
        for name in self.open.listDefinedDomains():
            dom = self.lookupVM(name)
            vname[dom.name()] = dom.info()[0]
        return vname

    def networks_get_node(self):
        """

        Function return host server virtual networks.

        """
        virtnet = {}
        for network in self.open.listNetworks():
            net = self.open.networkLookupByName(network)
            status = net.isActive()
            virtnet[network] = status
        for network in self.open.listDefinedNetworks():
            net = self.networkPool(network)
            status = net.isActive()
            virtnet[network] = status
        return virtnet

    def storages_get_node(self):
        """

        Function return host server storages.

        """
        storages = {}
        for storage in self.open.listStoragePools():
            stg = self.open.storagePoolLookupByName(storage)
            status = stg.isActive()
            storages[storage] = status
        for storage in self.open.listDefinedStoragePools():
            stg = self.storagePool(storage)
            status = stg.isActive()
            storages[storage] = status
        return storages

    def node_get_info(self):
        """

        Function return host server information: hostname, cpu, memory, ...

        """
        info = []
        info.append(self.open.getHostname())
        info.append(self.open.getInfo()[0])
        info.append(self.open.getInfo()[2])
        try:
            info.append(get_xml_path(self.open.getSysinfo(0),
                                     "/sysinfo/processor/entry[6]"))
        except Exception:
            info.append('Unknown')
        info.append(self.open.getURI())
        info.append(self.open.getLibVersion())
        return info

    def memory_get_usage(self):
        """

        Function return memory usage on node.

        """
        allmem = self.open.getInfo()[1] * 1048576
        get_freemem = self.open.getMemoryStats(-1, 0)
        if type(get_freemem) == dict:
            freemem = (get_freemem.values()[0] + \
                       get_freemem.values()[2] + \
                       get_freemem.values()[3]) * 1024
            percent = (freemem * 100) / allmem
            percent = 100 - percent
            memusage = (allmem - freemem)
        else:
            memusage = None
            percent = None
        return allmem, memusage, percent

    def cpu_get_usage(self):
        """

        Function return cpu usage on node.

        """
        prev_idle = 0
        prev_total = 0
        cpu = self.open.getCPUStats(-1, 0)
        if type(cpu) == dict:
            for num in range(2):
                idle = self.open.getCPUStats(-1, 0).values()[1]
                total = sum(self.open.getCPUStats(-1, 0).values())
                diff_idle = idle - prev_idle
                diff_total = total - prev_total
                diff_usage = (1000 * (diff_total - diff_idle) / diff_total + 5) / 10
                prev_total = total
                prev_idle = idle
                if num == 0:
                    time.sleep(1)
                else:
                    if diff_usage < 0:
                        diff_usage = 0
        else:
            diff_usage = None
        return diff_usage

    def new_volume(self, storage, name, size, format='qcow2'):
        """

        Add new volume in storage

        """
        stg = self.storagePool(storage)
        size = int(size) * 1073741824
        stg_type = get_xml_path(stg.XMLDesc(0), "/pool/@type")
        if stg_type == 'dir':
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

    def clone_volume(self, storage, img, new_img, format=None):
        """

        Function clone volume

        """
        stg = self.storagePool(storage)
        stg_type = get_xml_path(stg.XMLDesc(0), "/pool/@type")
        if stg_type == 'dir':
            new_img += '.img'
        vol = stg.storageVolLookupByName(img)
        if not format:
            xml = vol.XMLDesc(0)
            format = get_xml_path(xml, "/volume/target/format/@type")
        xml = """
            <volume>
                <name>%s</name>
                <capacity>0</capacity>
                <allocation>0</allocation>
                <target>
                    <format type='%s'/>
                </target>
            </volume>""" % (new_img, format)
        stg.createXMLFrom(xml, vol, 0)

    def images_get_storages(self, storages):
        """

        Function return all images on all storages

        """
        disk = []
        for storage in storages:
            stg = self.storagePool(storage)
            stg_type = get_xml_path(stg.XMLDesc(0), "/pool/@type")
            if stg.info()[0] != 0:
                stg.refresh(0)
                for img in stg.listVolumes():
                    if stg_type == 'dir':
                        if re.findall(".img", img):
                            disk.append(img)
                    if stg_type == 'logical':
                        disk.append(img)
        return disk

    def image_get_path(self, vol, storages):
        """

        Function return volume path.

        """
        for storage in storages:
            stg = self.storagePool(storage)
            for img in stg.listVolumes():
                if vol == img:
                    stg_volume = stg.storageVolLookupByName(vol)
                    return stg_volume.path()

    def storage_get_info(self, storage):
        """

        Function return storage info.

        """
        stg = self.storagePool(storage)
        if stg:
            if stg.info()[3] == 0:
                percent = 0
            else:
                percent = (stg.info()[2] * 100) / stg.info()[1]
            info = stg.info()[1:4]
            info.append(int(percent))
            info.append(stg.isActive())
            xml = stg.XMLDesc(0)
            info.append(get_xml_path(xml, "/pool/@type"))
            info.append(get_xml_path(xml, "/pool/target/path"))
        else:
            info = [None] * 7
        return info

    def new_storage_pool(self, type_pool, name, source, target):
        """

        Function create storage pool.

        """
        xml = """
                <pool type='%s'>
                <name>%s</name>""" % (type_pool, name)

        if type_pool == 'logical':
            xml += """
                  <source>
                    <device path='%s'/>
                    <name>%s</name>
                    <format type='lvm2'/>
                  </source>""" % (source, name)

        if type_pool == 'logical':
            target = '/dev/' + name

        xml += """
                  <target>
                       <path>%s</path>
                  </target>
                </pool>""" % target
        self.open.storagePoolDefineXML(xml, 0)
        stg = self.storagePool(name)
        if type_pool == 'logical':
            stg.build(0)
        stg.create(0)
        stg.setAutostart(1)

    def volumes_get_info(self, storage):
        """

        Function return volume info.

        """
        stg = self.storagePool(storage)
        stg_type = get_xml_path(stg.XMLDesc(0), "/pool/@type")
        volume_info = {}
        for name in stg.listVolumes():
            if stg_type == 'dir':
                if re.findall(".img", name) or re.findall(".iso", name):
                    vol = stg.storageVolLookupByName(name)
                    xml = vol.XMLDesc(0)
                    volume_format = get_xml_path(xml, "/volume/target/format/@type")
                    volume_info[name] = vol.info()[1], volume_format
            if stg_type == 'logical':
                vol = stg.storageVolLookupByName(name)
                xml = vol.XMLDesc(0)
                volume_format = get_xml_path(xml, "/volume/target/format/@type")
                volume_info[name] = vol.info()[1], volume_format
        return volume_info

    def new_network_pool(self, name, forward, gateway, mask, dhcp, bridge_name):
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
            xml += """name='%s'""" % bridge_name
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

        self.open.networkDefineXML(xml)
        net = self.networkPool(name)
        net.create()
        net.setAutostart(1)

    def network_get_info(self, network):
        """

        Function return network info.

        """
        info = []
        net = self.networkPool(network)
        if net:
            info.append(net.isActive())
            info.append(net.bridgeName())
        else:
            info = [None] * 2
        return info

    def network_get_subnet(self, network):
        """

        Function return virtual network info: ip, netmask, dhcp, type forward.

        """
        net = self.networkPool(network)
        xml_net = net.XMLDesc(0)
        ipv4 = []

        fw_type = get_xml_path(xml_net, "/network/forward/@mode")
        fw_dev = get_xml_path(xml_net, "/network/forward/@dev")

        if fw_type:
            ipv4.append([fw_type, fw_dev])
        else:
            ipv4.append(None)

        # Subnet block
        addr_str = get_xml_path(xml_net, "/network/ip/@address")
        mask_str = get_xml_path(xml_net, "/network/ip/@netmask")

        if addr_str and mask_str:
            netmask = IP(mask_str)
            gateway = IP(addr_str)
            network = IP(gateway.int() & netmask.int())
            ipv4.append(IP(str(network) + "/" + mask_str))
        else:
            ipv4.append(None)

        # DHCP block
        dhcp_start = get_xml_path(xml_net, "/network/ip/dhcp/range[1]/@start")
        dhcp_end = get_xml_path(xml_net, "/network/ip/dhcp/range[1]/@end")

        if not dhcp_start or not dhcp_end:
            pass
        else:
            ipv4.append([IP(dhcp_start), IP(dhcp_end)])
        return ipv4

    def snapshots_get_node(self):
        """

        Function return all snaphots on node.

        """
        vname = {}
        for vm_id in self.open.listDomainsID():
            vm_id = int(vm_id)
            dom = self.open.lookupByID(vm_id)
            if dom.snapshotNum(0) != 0:
                vname[dom.name()] = dom.info()[0]
        for name in self.open.listDefinedDomains():
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
                        self.open.defineXML(xmldom)
                    if dom.info()[0] == 5:
                        vol = stg.storageVolLookupByName(image)
                        xml = dom.XMLDesc(VIR_DOMAIN_XML_SECURE)
                        newxml = "<disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>\n      <source file='%s'/>" % vol.path()
                        xmldom = xml.replace(
                            "<disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>", newxml)
                        self.open.defineXML(xmldom)

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
            self.open.defineXML(xmldom)
        if dom.info()[0] == 5:
            xml = dom.XMLDesc(VIR_DOMAIN_XML_SECURE)
            xmldom = xml.replace("<source file='%s'/>\n" % image, '')
            self.open.defineXML(xmldom)

    def vds_cpu_usage(self, vname):
        """

        Function return vds cpu usage.

        """
        cpu_usage = {}
        dom = self.lookupVM(vname)
        if dom.info()[0] == 1:
            nbcore = self.open.getInfo()[2]
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
        self.open.defineXML(xmldom)

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
        self.open.defineXML(xml_description_change)

    def defineXML(self, xml):
        """

        Funciton define VM config

        """
        self.open.defineXML(xml)


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
        host_mem = self.open.getInfo()[1] * 1048576
        for vm_id in self.open.listDomainsID():
            vm_id = int(vm_id)
            dom = self.open.lookupByID(vm_id)
            mem = get_xml_path(dom.XMLDesc(0), "/domain/memory")
            mem = int(mem) * 1024
            mem_usage = (mem * 100) / host_mem
            vcpu = get_xml_path(dom.XMLDesc(0), "/domain/vcpu")
            vname[dom.name()] = (dom.info()[0], vcpu, mem, mem_usage)
        for name in self.open.listDefinedDomains():
            dom = self.lookupVM(name)
            mem = get_xml_path(dom.XMLDesc(0), "/domain/memory")
            mem = int(mem) * 1024
            mem_usage = (mem * 100) / host_mem
            vcpu = get_xml_path(dom.XMLDesc(0), "/domain/vcpu")
            vname[dom.name()] = (dom.info()[0], vcpu, mem, mem_usage)
        return vname

    def close(self):
        """

        Close libvirt connection.

        """
        self.open.close()
