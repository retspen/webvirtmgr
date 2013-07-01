# -*- coding: utf-8 -*-

import libvirt
import virtinst.util as util
from network.IPy import IP
import re
import time
from datetime import datetime


class ConnServer(object):
    def __init__(self, host):
        """

        Return connection object.

        """

        self.login = host.login
        self.host = host.ipaddr
        self.passwd = host.passwd
        self.type = host.conn_type
        self.port = host.ssh_port

        if self.type == 'tcp':
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
            self.conn = libvirt.openAuth(uri, auth, 0)
        if self.type == 'ssh':
            uri = 'qemu+ssh://%s@%s:%s/system' % (self.login, self.host, self.port)
            self.conn = libvirt.open(uri)


    def lookupVM(self, vname):
        """

        Return VM object.

        """


        dom = self.conn.lookupByName(vname)
        return dom


    def storagePool(self, storage):
        """

        Return storage object.

        """

        stg = self.conn.storagePoolLookupByName(storage)
        return stg


    def networkPool(self, network):
        """

        Return network object.

        """

        net = self.conn.networkLookupByName(network)
        return net    


    def storageVol(self, volume, storage):
        """

        Return volume object.

        """

        stg = self.storagePool(storage)
        stg_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
        if stg_type == 'dir':
            volume = volume + '.img'
        vl = stg.storageVolLookupByName(volume)
        return vl


    def storageVolPath(self, volume):
        """

        Return volume object by path.

        """

        vl = self.conn.storageVolLookupByPath(volume)
        return vl


    def hard_accel_node(self):
        """

        Check hardware acceleration.

        """

        xml = self.conn.getCapabilities()
        kvm = re.search('kvm', xml)
        if kvm:
            return True
        else:
            return False


    def add_vm(self, name, ram, vcpu, image, net, virtio, passwd, all_storages):
        """
        Create VM function

        """

        iskvm = re.search('kvm', self.conn.getCapabilities())
        if iskvm:
            dom_type = 'kvm'
        else:
            dom_type = 'qemu'

        machine = util.get_xml_path(self.conn.getCapabilities(), "/capabilities/guest/arch/machine/@canonical")
        if not machine:
            machine = 'pc-1.0'

        if re.findall('/usr/libexec/qemu-kvm', self.conn.getCapabilities()):
            emulator = '/usr/libexec/qemu-kvm'
        elif re.findall('/usr/bin/kvm', self.conn.getCapabilities()):
            emulator = '/usr/bin/kvm'
        elif re.findall('/usr/bin/qemu-kvm', self.conn.getCapabilities()):
            emulator = '/usr/bin/qemu-kvm'      
        else:
            emulator = '/usr/bin/qemu-system-x86_64'

        img = ConnServer.storageVolPath(self, image)
        vol = img.name()
        for storage in all_storages:
            stg = self.conn.storagePoolLookupByName(storage)
            if stg.info()[0] != 0:
                stg.refresh(0)
                for img in stg.listVolumes():
                    if img == vol:
                        stg_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
                        if stg_type == 'dir':
                            image_type = 'qcow2'
                        else:
                            image_type = 'raw'

        xml = """<domain type='%s'>
                  <name>%s</name>
                  <memory unit='MiB'>%s</memory>
                  <vcpu>%s</vcpu>
                  <os>
                    <type arch='x86_64' machine='%s'>hvm</type>
                    <boot dev='hd'/>
                    <boot dev='cdrom'/>
                    <bootmenu enable='yes'/>
                  </os>
                  <features>
                    <acpi/>
                    <apic/>
                    <pae/>
                  </features>
                  <clock offset='utc'/>
                  <on_poweroff>destroy</on_poweroff>
                  <on_reboot>restart</on_reboot>
                  <on_crash>restart</on_crash>
                  <devices>
                    <emulator>%s</emulator>
                    <disk type='file' device='disk'>
                      <driver name='qemu' type='%s'/>
                      <source file='%s'/>""" % (dom_type, name, ram, vcpu, machine,
                                                emulator, image_type, image)

        if virtio:
            xml += """<target dev='vda' bus='virtio'/>"""
        else:
            xml += """<target dev='hda' bus='ide'/>"""

        xml += """</disk>
                    <disk type='file' device='cdrom'>
                      <driver name='qemu' type='raw'/>
                      <source file=''/>
                      <target dev='hdc' bus='ide'/>
                      <readonly/>
                    </disk>"""

        if re.findall("br", net):
            xml += """<interface type='bridge'>
                    <source bridge='%s'/>""" % (net)
        else:
            xml += """<interface type='network'>
                    <source network='%s'/>""" % (net)
        if virtio:
            xml += """<model type='virtio'/>"""

        xml += """</interface>
                    <input type='tablet' bus='usb'/>
                    <input type='mouse' bus='ps2'/>
                    <graphics type='vnc' passwd='%s'/>
                    <memballoon model='virtio'/>
                  </devices>
                </domain>""" % (passwd)
        self.conn.defineXML(xml)
        dom = self.lookupVM(name)
        dom.setAutostart(1)


    def vds_get_node(self):
        """

        Get all VM in host server

        """

        vname = {}
        for id in self.conn.listDomainsID():
            id = int(id)
            dom = self.conn.lookupByID(id)
            vname[dom.name()] = dom.info()[0]
        for id in self.conn.listDefinedDomains():
            dom = self.conn.lookupByName(id)
            vname[dom.name()] = dom.info()[0]
        return vname


    def networks_get_node(self):
        """

        Function return host server virtual networks.

        """

        virtnet = {}
        for network in self.conn.listNetworks():
            net = self.conn.networkLookupByName(network)
            status = net.isActive()
            virtnet[network] = status
        for network in self.conn.listDefinedNetworks():
            net = self.conn.networkLookupByName(network)
            status = net.isActive()
            virtnet[network] = status
        return virtnet


    def storages_get_node(self):
        """

        Function return host server storages.

        """

        storages = {}
        for storage in self.conn.listStoragePools():
            stg = self.conn.storagePoolLookupByName(storage)
            status = stg.isActive()
            storages[storage] = status
        for storage in self.conn.listDefinedStoragePools():
            stg = self.conn.storagePoolLookupByName(storage)
            status = stg.isActive()
            storages[storage] = status
        return storages


    def node_get_info(self):
        """

        Function return host server information: hostname, cpu, memory, ...

        """

        info = []
        info.append(self.conn.getHostname())
        info.append(self.conn.getInfo()[0])
        info.append(self.conn.getInfo()[2])
        try:
            info.append(util.get_xml_path(self.conn.getSysinfo(0),
                        "/sysinfo/processor/entry[6]"))
        except:
            info.append('Unknown')
        info.append(self.conn.getLibVersion())
        info.append(self.conn.getURI())
        return info


    def memory_get_usage(self):
        """

        Function return memory usage on node.

        """

        allmem = self.conn.getInfo()[1] * 1048576
        get_freemem = self.conn.getMemoryStats(-1, 0)
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
        cpu = self.conn.getCPUStats(-1, 0)
        if type(cpu) == dict:
            for num in range(2):
                    idle = self.conn.getCPUStats(-1, 0).values()[1]
                    total = sum(self.conn.getCPUStats(-1, 0).values())
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


    def new_volume(self, storage, name, size):
        """

        Add new volume in storage

        """

        stg = self.storagePool(storage)
        size = int(size) * 1073741824
        stg_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
        if stg_type == 'dir':
            name = name + '.img'
            alloc = 0
        else:
            alloc = size
        xml = """
            <volume>
                <name>%s</name>
                <capacity>%s</capacity>
                <allocation>%s</allocation>
                <target>
                    <format type='qcow2'/>
                </target>
            </volume>""" % (name, size, alloc)
        stg.createXML(xml, 0)


    def clone_volume(self, storage, img, new_img):
        """

        Function clone volume

        """

        stg = self.storagePool(storage)
        stg_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
        if stg_type == 'dir':
            new_img = new_img + '.img'
        vol = stg.storageVolLookupByName(img)
        xml = """
            <volume>
                <name>%s</name>
                <capacity>0</capacity>
                <allocation>0</allocation>
                <target>
                    <format type='qcow2'/>
                </target>
            </volume>""" % (new_img)
        stg.createXMLFrom(xml, vol, 0)


    def images_get_storages(self, storages):
        """

        Function return all images on all storages

        """

        disk = []
        for storage in storages:
            stg = self.conn.storagePoolLookupByName(storage)
            if stg.info()[0] != 0:
                stg.refresh(0)
                for img in stg.listVolumes():
                    if re.findall(".iso", img) or re.findall(".ISO", img):
                        pass
                    else:
                        disk.append(img)
        return disk


    def image_get_path(self, vol, storages):
        """

        Function return volume path.

        """

        for storage in storages:
            stg = self.conn.storagePoolLookupByName(storage)
            for img in stg.listVolumes():
                if vol == img:
                    vl = stg.storageVolLookupByName(vol)
                    return vl.path()


    def storage_get_info(self, storage):
        """

        Function return storage info.

        """

        stg = self.storagePool(storage)
        if stg.info()[3] == 0:
            percent = 0
        else:
            percent = (stg.info()[2] * 100) / stg.info()[1]
        info = stg.info()
        info.append(int(percent))
        info.append(stg.isActive())
        xml = stg.XMLDesc(0)
        info.append(util.get_xml_path(xml, "/pool/@type"))
        info.append(util.get_xml_path(xml, "/pool/target/path"))
        info.append(util.get_xml_path(xml, "/pool/source/device/@path"))
        info.append(util.get_xml_path(xml, "/pool/source/format/@type"))
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
                </pool>""" % (target)
        self.conn.storagePoolDefineXML(xml, 0)
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
        volinfo = {}
        for name in stg.listVolumes():
            vol = stg.storageVolLookupByName(name)
            xml = vol.XMLDesc(0)
            size = vol.info()[1]
            format = util.get_xml_path(xml, "/volume/target/format/@type")
            volinfo[name] = size, format
        return volinfo


    def new_network_pool(self, name, forward, gw, netmask, dhcp):
        """

        Function create network pool.

        """

        xml = """
            <network>
                <name>%s</name>""" % (name)

        if forward == "nat" or "route":
            xml += """<forward mode='%s'/>""" % (forward)

        xml += """<bridge stp='on' delay='0' />
                    <ip address='%s' netmask='%s'>""" % (gw, netmask)

        if dhcp[0] == '1':
            xml += """<dhcp>
                        <range start='%s' end='%s' />
                    </dhcp>""" % (dhcp[1], dhcp[2])

        xml += """</ip>
            </network>"""
        self.conn.networkDefineXML(xml)
        net = self.networkPool(name)
        net.create()
        net.setAutostart(1)


    def network_get_info(self, network):
        """

        Function return network info.

        """

        info = []
        net = self.conn.networkLookupByName(network)
        info.append(net.isActive())
        info.append(net.bridgeName())
        return info


    def network_get_subnet(self, network):
        """

        Function return virtual network info: ip, netmask, dhcp, type forward.

        """

        net = self.conn.networkLookupByName(network)
        xml_net = net.XMLDesc(0)
        ipv4 = []

        fw = util.get_xml_path(xml_net, "/network/forward/@mode")
        forwardDev = util.get_xml_path(xml_net, "/network/forward/@dev")

        if fw:
            ipv4.append([fw, forwardDev])
        else:
            ipv4.append(None)

        # Subnet block
        addrStr = util.get_xml_path(xml_net, "/network/ip/@address")
        netmaskStr = util.get_xml_path(xml_net, "/network/ip/@netmask")

        if addrStr and netmaskStr:
            netmask = IP(netmaskStr)
            gateway = IP(addrStr)
            network = IP(gateway.int() & netmask.int())
            ipv4.append(IP(str(network) + "/" + netmaskStr))
        else:
            ipv4.append(None)

        # DHCP block
        dhcpstart = util.get_xml_path(xml_net, "/network/ip/dhcp/range[1]/@start")
        dhcpend = util.get_xml_path(xml_net, "/network/ip/dhcp/range[1]/@end")

        if not dhcpstart or not dhcpend:
            pass
        else:
            ipv4.append([IP(dhcpstart), IP(dhcpend)])
        return ipv4


    def snapshots_get_node(self):
        """

        Function return all snaphots on node.

        """

        vname = {}
        for vm_id in self.conn.listDomainsID():
            vm_id = int(vm_id)
            dom = self.conn.lookupByID(vm_id)
            if dom.snapshotNum(0) != 0:
                vname[dom.name()] = dom.info()[0]
        for vm in self.conn.listDefinedDomains():
            dom = self.conn.lookupByName(vm)
            if dom.snapshotNum(0) != 0:
                vname[dom.name()] = dom.info()[0]
        return vname


    def snapshots_get_vds(self, vname):
        """

        Function return all vds snaphots.

        """

        snapshots = {}
        dom = self.conn.lookupByName(vname)
        all_snapshot = dom.snapshotListNames(0)
        for snapshot in all_snapshot:
            snapshots[snapshot] = (datetime.fromtimestamp(int(snapshot)), dom.info()[0])
        return snapshots


    def snapshot_delete(self, vname, name_snap):
        """

        Function delete vds snaphots.

        """

        dom = self.conn.lookupByName(vname)
        snap = dom.snapshotLookupByName(name_snap, 0)
        snap.delete(0)


    def snapshot_revert(self, vname, name_snap):
        """

        Function revert vds snaphots.

        """

        dom = self.conn.lookupByName(vname)
        snap = dom.snapshotLookupByName(name_snap, 0)
        dom.revertToSnapshot(snap, 0)


    def vnc_get_port(self, vname):
        """

        Function rever vds snaphots.

        """

        dom = self.conn.lookupByName(vname)
        port = util.get_xml_path(dom.XMLDesc(0), "/domain/devices/graphics/@port")
        return port


    def vds_mount_iso(self, vname, image):
        """

        Function mount iso image on vds. Changes on XML config.

        """

        storages = self.storages_get_node()
        dom = self.lookupVM(vname)
        image = image + '.iso'

        for storage in storages:
            stg = self.storagePool(storage)
            for img in stg.listVolumes():
                if image == img:
                    if dom.info()[0] == 1:
                        vol = stg.storageVolLookupByName(image)
                        xml = """<disk type='file' device='cdrom'>
                                    <driver name='qemu' type='raw'/>
                                    <target dev='hdc' bus='ide'/>
                                    <source file='%s'/>
                                    <readonly/>
                                 </disk>""" % vol.path()
                        dom.attachDevice(xml)
                        xmldom = dom.XMLDesc(0)
                        self.conn.defineXML(xmldom)
                    if dom.info()[0] == 5:
                        vol = stg.storageVolLookupByName(image)
                        xml = dom.XMLDesc(0)
                        newxml = "<disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>\n      <source file='%s'/>" % vol.path()
                        xmldom = xml.replace("<disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>", newxml)
                        self.conn.defineXML(xmldom)


    def vds_umount_iso(self, vname, image):
        """

        Function umount iso image on vds. Changes on XML config.

        """

        storages = self.storages_get_node()
        dom = self.lookupVM(vname)
        image = image + '.iso'

        if dom.info()[0] == 1:
            xml = """<disk type='file' device='cdrom'>
                         <driver name="qemu" type='raw'/>
                         <target dev='hdc' bus='ide'/>
                         <readonly/>
                      </disk>"""
            dom.attachDevice(xml)
            xmldom = dom.XMLDesc(0)
            self.conn.defineXML(xmldom)
        if dom.info()[0] == 5:
            for storage in storages:
                stg = self.storagePool(storage)
                for img in stg.listVolumes():
                    if image == img:
                        vol = stg.storageVolLookupByName(image)
                        xml = dom.XMLDesc(0)
                        xmldom = xml.replace("<source file='%s'/>\n" % vol.path(), '')
                        self.conn.defineXML(xmldom)


    def vds_cpu_usage(self, vname):
        """

        Function return vds cpu usage.

        """

        dom = self.lookupVM(vname)
        nbcore = self.conn.getInfo()[2]
        cpu_use_ago = dom.info()[4]
        time.sleep(1)
        cpu_use_now = dom.info()[4]
        diff_usage = cpu_use_now - cpu_use_ago
        cpu_usage = 100 * diff_usage / (1 * nbcore * 10**9L)
        return cpu_usage


    def vds_memory_usage(self, vname):
        """

        Function return vds memory usage.

        """

        dom = self.lookupVM(vname)
        allmem = self.conn.getInfo()[1] * 1048576
        dom_mem = dom.info()[1] * 1024
        percent = (dom_mem * 100) / allmem
        return allmem, percent


    def vds_get_info(self, vname):
        """

        Function return vds info.

        """

        info = []
        dom = self.lookupVM(vname)
        xml = dom.XMLDesc(0)
        info.append(util.get_xml_path(xml, "/domain/vcpu"))
        mem = util.get_xml_path(xml, "/domain/memory")
        mem = int(mem) / 1024
        info.append(int(mem))
        info.append(util.get_xml_path(xml, "/domain/devices/interface/mac/@address"))
        nic = util.get_xml_path(xml, "/domain/devices/interface/source/@network")
        if nic is None:
            nic = util.get_xml_path(xml, "/domain/devices/interface/source/@bridge")
        info.append(nic)
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
            hdd_dev = util.get_xml_path(xml, "/domain/devices/disk[%s]/@device" % (num))
            if hdd_dev == 'disk':
                dev_bus = util.get_xml_path(xml, "/domain/devices/disk[%s]/target/@dev" % (num))
                hdd = util.get_xml_path(xml, "/domain/devices/disk[%s]/source/@file" % (num))
                # If xml create custom
                if not hdd:
                    hdd = util.get_xml_path(xml, "/domain/devices/disk[%s]/source/@dev" % (num))
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
                except:
                    all_hdd_dev[dev_bus] = hdd, 'Not in the pool'
        return all_hdd_dev


    def vds_get_media(self, vname):
        """

        Function return vds media info.

        """

        dom = self.lookupVM(vname)
        xml = dom.XMLDesc(0)
        for num in range(1, 5):
            hdd_dev = util.get_xml_path(xml, "/domain/devices/disk[%s]/@device" % (num))
            if hdd_dev == 'cdrom':
                media = util.get_xml_path(xml, "/domain/devices/disk[%s]/source/@file" % (num))
                if media:
                    vol = self.storageVolPath(media)
                    img = re.sub('.iso', '', vol.name())
                    return img
                else:
                    return None


    def vds_set_vnc_passwd(self, vname, passwd):
        """

        Function set vnc password to vds.

        """

        dom = self.lookupVM(vname)
        xml = dom.XMLDesc(0)
        newxml = "<graphics type='vnc' port='-1' autoport='yes' passwd='%s'/>" % passwd
        xmldom = re.sub('\<graphics.*\>', newxml, xml)
        self.conn.defineXML(xmldom)


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
                        img = re.sub('.iso', '', img)
                        iso.append(img)
        return iso


    def vds_remove_hdd(self, vname):
        """

        Function delete vds hdd.

        """

        dom = self.lookupVM(vname)
        img = util.get_xml_path(dom.XMLDesc(0), "/domain/devices/disk[1]/source/@file")
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
        xml += dom.XMLDesc(0)
        xml += """<active>0</active>\n
                  </domainsnapshot>"""
        dom.snapshotCreateXML(xml, 0)


    def vds_on_cluster(self):
        vname = {}
        host_mem = self.conn.getInfo()[1] * 1048576
        for vm_id in self.conn.listDomainsID():
            vm_id = int(vm_id)
            dom = self.conn.lookupByID(vm_id)
            mem = util.get_xml_path(dom.XMLDesc(0), "/domain/memory")
            mem = int(mem) * 1024
            mem_usage = (mem * 100) / host_mem
            vcpu = util.get_xml_path(dom.XMLDesc(0), "/domain/vcpu")
            vname[dom.name()] = (dom.info()[0], vcpu, mem, mem_usage)
        for vm in self.conn.listDefinedDomains():
            dom = self.conn.lookupByName(vm)
            mem = util.get_xml_path(dom.XMLDesc(0), "/domain/memory")
            mem = int(mem) * 1024
            mem_usage = (mem * 100) / host_mem
            vcpu = util.get_xml_path(dom.XMLDesc(0), "/domain/vcpu")
            vname[dom.name()] = (dom.info()[0], vcpu, mem, mem_usage)
        return vname


    def close(self):
        """

        Close libvirt connection.

        """

        self.conn.close()
