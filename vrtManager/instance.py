#
# Copyright (C) 2013 Webvirtmgr.
#
import time
import os.path
try:
    from libvirt import libvirtError, VIR_DOMAIN_XML_SECURE, VIR_MIGRATE_LIVE, VIR_MIGRATE_UNSAFE
except:
    from libvirt import libvirtError, VIR_DOMAIN_XML_SECURE, VIR_MIGRATE_LIVE
from vrtManager import util
from xml.etree import ElementTree
from datetime import datetime
from vrtManager.connection import wvmConnect


class wvmInstances(wvmConnect):
    def get_instance_status(self, name):
        inst = self.get_instance(name)
        return inst.info()[0]

    def get_instance_memory(self, name):
        inst = self.get_instance(name)
        mem = util.get_xml_path(inst.XMLDesc(0), "/domain/currentMemory")
        return int(mem) / 1024

    def get_instance_vcpu(self, name):
        inst = self.get_instance(name)
        cur_vcpu = util.get_xml_path(inst.XMLDesc(0), "/domain/vcpu/@current")
        if cur_vcpu:
            vcpu = cur_vcpu
        else:
            vcpu = util.get_xml_path(inst.XMLDesc(0), "/domain/vcpu")
        return vcpu

    def get_instance_managed_save_image(self, name):
        inst = self.get_instance(name)
        return inst.hasManagedSaveImage(0)

    def get_uuid(self, name):
        inst = self.get_instance(name)
        return inst.UUIDString()

    def start(self, name):
        dom = self.get_instance(name)
        dom.create()

    def shutdown(self, name):
        dom = self.get_instance(name)
        dom.shutdown()

    def force_shutdown(self, name):
        dom = self.get_instance(name)
        dom.destroy()

    def managedsave(self, name):
        dom = self.get_instance(name)
        dom.managedSave(0)

    def managed_save_remove(self, name):
        dom = self.get_instance(name)
        dom.managedSaveRemove(0)

    def suspend(self, name):
        dom = self.get_instance(name)
        dom.suspend()

    def resume(self, name):
        dom = self.get_instance(name)
        dom.resume()

    def moveto(self, conn, name, live, unsafe, undefine):
        flags = 0
        if live and conn.get_status() == 1:
            flags |= VIR_MIGRATE_LIVE
        if unsafe and conn.get_status() == 1:
            flags |= VIR_MIGRATE_UNSAFE
        dom = conn.get_instance(name)
        dom.migrate(self.wvm, flags, name, None, 0)
        if undefine:
            dom.undefine()

    def define_move(self, name):
        dom = self.get_instance(name)
        xml = dom.XMLDesc(VIR_DOMAIN_XML_SECURE)
        self.wvm.defineXML(xml)


class wvmInstance(wvmConnect):
    def __init__(self, host, login, passwd, conn, vname):
        wvmConnect.__init__(self, host, login, passwd, conn)
        self.instance = self.get_instance(vname)

    def start(self):
        self.instance.create()

    def shutdown(self):
        self.instance.shutdown()

    def force_shutdown(self):
        self.instance.destroy()

    def managedsave(self):
        self.instance.managedSave(0)

    def managed_save_remove(self):
        self.instance.managedSaveRemove(0)

    def suspend(self):
        self.instance.suspend()

    def resume(self):
        self.instance.resume()

    def delete(self):
        self.instance.undefine()

    def _XMLDesc(self, flag):
        return self.instance.XMLDesc(flag)

    def _defineXML(self, xml):
        self.wvm.defineXML(xml)

    def get_status(self):
        return self.instance.info()[0]

    def get_autostart(self):
        return self.instance.autostart()

    def set_autostart(self, flag):
        return self.instance.setAutostart(flag)

    def get_uuid(self):
        return self.instance.UUIDString()

    def get_vcpu(self):
        vcpu = util.get_xml_path(self._XMLDesc(0), "/domain/vcpu")
        return int(vcpu)

    def get_cur_vcpu(self):
        cur_vcpu = util.get_xml_path(self._XMLDesc(0), "/domain/vcpu/@current")
        if cur_vcpu:
            return int(cur_vcpu)

    def get_memory(self):
        mem = util.get_xml_path(self._XMLDesc(0), "/domain/memory")
        return int(mem) / 1024

    def get_cur_memory(self):
        mem = util.get_xml_path(self._XMLDesc(0), "/domain/currentMemory")
        return int(mem) / 1024

    def get_description(self):
        return util.get_xml_path(self._XMLDesc(0), "/domain/description")

    def get_max_memory(self):
        return self.wvm.getInfo()[1] * 1048576

    def get_max_cpus(self):
        """Get number of physical CPUs."""
        hostinfo = self.wvm.getInfo()
        pcpus = hostinfo[4] * hostinfo[5] * hostinfo[6] * hostinfo[7]
        range_pcpus = xrange(1, int(pcpus + 1))
        return range_pcpus

    def get_net_device(self):
        def get_mac_ipaddr(net, mac_host):
            def fixed(ctx):
                for net in ctx.xpathEval('/network/ip/dhcp/host'):
                    mac = net.xpathEval('@mac')[0].content
                    host = net.xpathEval('@ip')[0].content
                    if mac == mac_host:
                        return host
                return None

            return util.get_xml_path(net.XMLDesc(0), func=fixed)

        def networks(ctx):
            result = []
            for net in ctx.xpathEval('/domain/devices/interface'):
                mac_host = net.xpathEval('mac/@address')[0].content
                nic_host = net.xpathEval('source/@network|source/@bridge|source/@dev')[0].content
                try:
                    net = self.get_network(nic_host)
                    ip = get_mac_ipaddr(net, mac_host)
                except:
                    ip = None
                result.append({'mac': mac_host, 'nic': nic_host, 'ip': ip})
            return result

        return util.get_xml_path(self._XMLDesc(0), func=networks)

    def get_disk_device(self):
        def disks(ctx):
            result = []
            dev = None
            volume = None
            storage = None
            src_fl = None
            disk_format = None
            for disk in ctx.xpathEval('/domain/devices/disk'):
                device = disk.xpathEval('@device')[0].content
                if device == 'disk':
                    try:
                        dev = disk.xpathEval('target/@dev')[0].content
                        src_fl = disk.xpathEval('source/@file|source/@dev|source/@name|source/@volume')[0].content
                        disk_format = disk.xpathEval('driver/@type')[0].content
                        try:
                            vol = self.get_volume_by_path(src_fl)
                            volume = vol.name()
                            stg = vol.storagePoolLookupByVolume()
                            storage = stg.name()
                        except libvirtError:
                            volume = src_fl
                    except:
                        pass
                    finally:
                        result.append(
                            {'dev': dev, 'image': volume, 'storage': storage, 'path': src_fl, 'format': disk_format})
            return result

        return util.get_xml_path(self._XMLDesc(0), func=disks)

    def get_media_device(self):
        def disks(ctx):
            result = []
            dev = None
            volume = None
            storage = None
            src_fl = None
            for media in ctx.xpathEval('/domain/devices/disk'):
                device = media.xpathEval('@device')[0].content
                if device == 'cdrom':
                    try:
                        dev = media.xpathEval('target/@dev')[0].content
                        try:
                            src_fl = media.xpathEval('source/@file')[0].content
                            vol = self.get_volume_by_path(src_fl)
                            volume = vol.name()
                            stg = vol.storagePoolLookupByVolume()
                            storage = stg.name()
                        except:
                            src_fl = None
                            volume = src_fl
                    except:
                        pass
                    finally:
                        result.append({'dev': dev, 'image': volume, 'storage': storage, 'path': src_fl})
            return result

        return util.get_xml_path(self._XMLDesc(0), func=disks)

    def mount_iso(self, dev, image):
        def attach_iso(dev, disk, vol):
            if disk.get('device') == 'cdrom':
                for elm in disk:
                    if elm.tag == 'target':
                        if elm.get('dev') == dev:
                            src_media = ElementTree.Element('source')
                            src_media.set('file', vol.path())
                            disk.insert(2, src_media)
                            return True

        storages = self.get_storages()
        for storage in storages:
            stg = self.get_storage(storage)
            if stg.info()[0] != 0:
                for img in stg.listVolumes():
                    if image == img:
                        vol = stg.storageVolLookupByName(image)
        tree = ElementTree.fromstring(self._XMLDesc(0))
        for disk in tree.findall('devices/disk'):
            if attach_iso(dev, disk, vol):
                break
        if self.get_status() == 1:
            xml = ElementTree.tostring(disk)
            self.instance.attachDevice(xml)
            xmldom = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        if self.get_status() == 5:
            xmldom = ElementTree.tostring(tree)
        self._defineXML(xmldom)

    def umount_iso(self, dev, image):
        tree = ElementTree.fromstring(self._XMLDesc(0))
        for disk in tree.findall('devices/disk'):
            if disk.get('device') == 'cdrom':
                for elm in disk:
                    if elm.tag == 'source':
                        if elm.get('file') == image:
                            src_media = elm
                    if elm.tag == 'target':
                        if elm.get('dev') == dev:
                            disk.remove(src_media)
        if self.get_status() == 1:
            xml_disk = ElementTree.tostring(disk)
            self.instance.attachDevice(xml_disk)
            xmldom = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        if self.get_status() == 5:
            xmldom = ElementTree.tostring(tree)
        self._defineXML(xmldom)

    def cpu_usage(self):
        cpu_usage = {}
        if self.get_status() == 1:
            nbcore = self.wvm.getInfo()[2]
            cpu_use_ago = self.instance.info()[4]
            time.sleep(1)
            cpu_use_now = self.instance.info()[4]
            diff_usage = cpu_use_now - cpu_use_ago
            cpu_usage['cpu'] = 100 * diff_usage / (1 * nbcore * 10 ** 9L)
        else:
            cpu_usage['cpu'] = 0
        return cpu_usage

    def disk_usage(self):
        devices = []
        dev_usage = []
        tree = ElementTree.fromstring(self._XMLDesc(0))
        for disk in tree.findall('devices/disk'):
            if disk.get('device') == 'disk':
                dev_file = None
                dev_bus = None
                network_disk = True
                for elm in disk:
                    if elm.tag == 'source':
                        if elm.get('protocol'):
                            dev_file = elm.get('protocol')
                            network_disk = True
                        if elm.get('file'):
                            dev_file = elm.get('file')
                        if elm.get('dev'):
                            dev_file = elm.get('dev')
                    if elm.tag == 'target':
                        dev_bus = elm.get('dev')
                if (dev_file and dev_bus) is not None:
                    if network_disk:
                        dev_file = dev_bus
                    devices.append([dev_file, dev_bus])
        for dev in devices:
            rd_use_ago = self.instance.blockStats(dev[0])[1]
            wr_use_ago = self.instance.blockStats(dev[0])[3]
            time.sleep(1)
            rd_use_now = self.instance.blockStats(dev[0])[1]
            wr_use_now = self.instance.blockStats(dev[0])[3]
            rd_diff_usage = rd_use_now - rd_use_ago
            wr_diff_usage = wr_use_now - wr_use_ago
            dev_usage.append({'dev': dev[1], 'rd': rd_diff_usage, 'wr': wr_diff_usage})
        return dev_usage

    def net_usage(self):
        devices = []
        dev_usage = []
        tree = ElementTree.fromstring(self._XMLDesc(0))
        for target in tree.findall("devices/interface/target"):
            devices.append(target.get("dev"))
        for i, dev in enumerate(devices):
            rx_use_ago = self.instance.interfaceStats(dev)[0]
            tx_use_ago = self.instance.interfaceStats(dev)[4]
            time.sleep(1)
            rx_use_now = self.instance.interfaceStats(dev)[0]
            tx_use_now = self.instance.interfaceStats(dev)[4]
            rx_diff_usage = (rx_use_now - rx_use_ago) * 8
            tx_diff_usage = (tx_use_now - tx_use_ago) * 8
            dev_usage.append({'dev': i, 'rx': rx_diff_usage, 'tx': tx_diff_usage})
        return dev_usage

    def get_telnet_port(self):
        telnet_port = None
        service_port = None
        tree = ElementTree.fromstring(self._XMLDesc(0))
        for console in tree.findall('devices/console'):
            if console.get('type') == 'tcp':
                for elm in console:
                    if elm.tag == 'source':
                        if elm.get('service'):
                            service_port = elm.get('service')
                    if elm.tag == 'protocol':
                        if elm.get('type') == 'telnet':
                            if service_port is not None:
                                telnet_port = service_port
        return telnet_port

    def get_vnc_port(self):
        vnc_port = util.get_xml_path(self._XMLDesc(0),
                                     "/domain/devices/graphics[@type='vnc']/@port")
        return vnc_port

    def get_vnc_websocket_port(self):
        vnc_websocket_port = util.get_xml_path(self._XMLDesc(0),
                                               "/domain/devices/graphics[@type='vnc']/@websocket")
        return vnc_websocket_port

    def get_vnc_passwd(self):
        return util.get_xml_path(self._XMLDesc(VIR_DOMAIN_XML_SECURE),
                                 "/domain/devices/graphics/@passwd")

    def set_vnc_passwd(self, passwd):
        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        root = ElementTree.fromstring(xml)
        try:
            graphics_vnc = root.find("devices/graphics[@type='vnc']")
        except SyntaxError:
            # Little fix for old version ElementTree
            graphics_vnc = root.find("devices/graphics")
        if passwd:
            graphics_vnc.set('passwd', passwd)
        else:
            try:
                graphics_vnc.attrib.pop('passwd')
            except:
                pass
        newxml = ElementTree.tostring(root)
        self._defineXML(newxml)

    def set_vnc_keymap(self, keymap):
        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        root = ElementTree.fromstring(xml)
        try:
            graphics_vnc = root.find("devices/graphics[@type='vnc']")
        except SyntaxError:
            # Little fix for old version ElementTree
            graphics_vnc = root.find("devices/graphics")
        if keymap:
            graphics_vnc.set('keymap', keymap)
        else:
            try:
                graphics_vnc.attrib.pop('keymap')
            except:
                pass
        newxml = ElementTree.tostring(root)
        self._defineXML(newxml)

    def get_vnc_keymap(self):
        return util.get_xml_path(self._XMLDesc(VIR_DOMAIN_XML_SECURE),
                                 "/domain/devices/graphics/@keymap") or ''

    def change_settings(self, description, cur_memory, memory, cur_vcpu, vcpu):
        """
        Function change ram and cpu on vds.
        """
        memory = int(memory) * 1024
        cur_memory = int(cur_memory) * 1024

        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        tree = ElementTree.fromstring(xml)

        set_mem = tree.find('memory')
        set_mem.text = str(memory)
        set_cur_mem = tree.find('currentMemory')
        set_cur_mem.text = str(cur_memory)
        set_desc = tree.find('description')
        set_vcpu = tree.find('vcpu')
        set_vcpu.text = vcpu
        set_vcpu.set('current', cur_vcpu)

        if not set_desc:
            tree_desc = ElementTree.Element('description')
            tree_desc.text = description
            tree.insert(2, tree_desc)
        else:
            set_desc.text = description

        new_xml = ElementTree.tostring(tree)
        self._defineXML(new_xml)

    def get_iso_media(self):
        iso = []
        storages = self.get_storages()
        for storage in storages:
            stg = self.get_storage(storage)
            if stg.info()[0] != 0:
                try:
                    stg.refresh(0)
                except:
                    pass
                for img in stg.listVolumes():
                    if img.endswith('.iso'):
                        iso.append(img)
        return iso

    def delete_disk(self):
        disks = self.get_disk_device()
        for disk in disks:
            vol = self.get_volume_by_path(disk.get('path'))
            vol.delete(0)

    def _snapshotCreateXML(self, xml, flag):
        self.instance.snapshotCreateXML(xml, flag)

    def create_snapshot(self, name):
        xml = """<domainsnapshot>
                     <name>%s</name>
                     <state>shutoff</state>
                     <creationTime>%d</creationTime>""" % (name, time.time())
        xml += self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        xml += """<active>0</active>
                  </domainsnapshot>"""
        self._snapshotCreateXML(xml, 0)

    def get_snapshot(self):
        snapshots = []
        snapshot_list = self.instance.snapshotListNames(0)
        for snapshot in snapshot_list:
            snap = self.instance.snapshotLookupByName(snapshot, 0)
            snap_time_create = util.get_xml_path(snap.getXMLDesc(0), "/domainsnapshot/creationTime")
            snapshots.append({'date': datetime.fromtimestamp(int(snap_time_create)), 'name': snapshot})
        return snapshots

    def snapshot_delete(self, snapshot):
        snap = self.instance.snapshotLookupByName(snapshot, 0)
        snap.delete(0)

    def snapshot_revert(self, snapshot):
        snap = self.instance.snapshotLookupByName(snapshot, 0)
        self.instance.revertToSnapshot(snap, 0)

    def get_managed_save_image(self):
        return self.instance.hasManagedSaveImage(0)

    def clone_instance(self, clone_data):
        clone_dev_path = []

        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        tree = ElementTree.fromstring(xml)
        name = tree.find('name')
        name.text = clone_data['name']
        uuid = tree.find('uuid')
        tree.remove(uuid)

        for num, net in enumerate(tree.findall('devices/interface')):
            elm = net.find('mac')
            elm.set('address', clone_data['net-' + str(num)])

        for disk in tree.findall('devices/disk'):
            if disk.get('device') == 'disk':
                elm = disk.find('target')
                device_name = elm.get('dev')
                if device_name:
                    target_file = clone_data['disk-' + device_name]
                    try:
                        meta_prealloc = clone_data['meta-' + device_name]
                    except:
                        meta_prealloc = False
                    elm.set('dev', device_name)

                elm = disk.find('source')
                source_file = elm.get('file')
                if source_file:
                    clone_dev_path.append(source_file)
                    clone_path = os.path.join(os.path.dirname(source_file),
                                              target_file)
                    elm.set('file', clone_path)

                    vol = self.get_volume_by_path(source_file)
                    vol_format = util.get_xml_path(vol.XMLDesc(0),
                                                   "/volume/target/format/@type")

                    if vol_format == 'qcow2' and meta_prealloc:
                        meta_prealloc = True
                    vol_clone_xml = """
                                    <volume>
                                        <name>%s</name>
                                        <capacity>0</capacity>
                                        <allocation>0</allocation>
                                        <target>
                                            <format type='%s'/>
                                        </target>
                                    </volume>""" % (target_file, vol_format)
                    stg = vol.storagePoolLookupByVolume()
                    stg.createXMLFrom(vol_clone_xml, vol, meta_prealloc)

        self._defineXML(ElementTree.tostring(tree))
