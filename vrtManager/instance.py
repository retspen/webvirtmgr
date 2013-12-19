#
# Copyright (C) 2013 Webvirtmgr.
#
import time
import re
from libvirt import VIR_DOMAIN_XML_SECURE
from vrtManager import util
from xml.etree import ElementTree
from vrtManager.connection import wvmConnect


class wvmInstances(wvmConnect):
    def get_instance_status(self, name):
        inst = self.get_instance(name)
        return inst.info()[0]

    def start(self, name):
        dom = self.get_instance(name)
        dom.create()

    def shutdown(self, name):
        dom = self.get_instance(name)
        dom.shutdown()

    def force_shutdown(self, name):
        dom = self.get_instance(name)
        dom.destroy()

    def suspend(self, name):
        dom = self.get_instance(name)
        dom.suspend()

    def resume(self, name):
        dom = self.get_instance(name)
        dom.resume()


class wvmInstance(wvmConnect):
    def __init__(self, host, login, passwd, conn, vname):
        wvmConnect.__init__(self, host, login, passwd, conn)
        self.instance = self.wvm.lookupByName(vname)

    def start(self):
        self.instance.create()

    def shutdown(self):
        self.instance.shutdown()

    def force_shutdown(self):
        self.instance.destroy()

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
        return util.get_xml_path(self._XMLDesc(0), "/domain/vcpu")

    def get_memory(self):
        mem = util.get_xml_path(self._XMLDesc(0), "/domain/memory")
        return int(mem) / 1024

    def get_description(self):
        return util.get_xml_path(self._XMLDesc(0), "/domain/description")

    def get_max_cpus(self):
        """Get number of physical CPUs."""
        hostinfo = self.wvm.getInfo()
        pcpus = hostinfo[4] * hostinfo[5] * hostinfo[6] * hostinfo[7]
        range_pcpus = xrange(1, int(pcpus + 1))
        return range_pcpus

    def get_net_device(self):
        def networks(ctx):
            result = []
            for interface in ctx.xpathEval('/domain/devices/interface'):
                mac = interface.xpathEval('mac/@address')[0].content
                nic = interface.xpathEval('source/@network|source/@bridge|source/@dev')[0].content
                result.append({'mac': mac, 'nic': nic})
            return result
        return util.get_xml_path(self._XMLDesc(0), func=networks)

    def get_disk_device(self):
        def disks(ctx):
            result = []
            for interface in ctx.xpathEval('/domain/devices/disk'):
                device = interface.xpathEval('@device')[0].content
                if device == 'disk':
                    dev = interface.xpathEval('target/@dev')[0].content
                    file = interface.xpathEval('source/@file|source/@dev')[0].content
                    vol = self.get_volume_by_path(file)
                    stg = vol.storagePoolLookupByVolume()
                    result.append({'dev': dev, 'image': vol.name(), 'storage': stg.name(), 'path': file})
            return result
        return util.get_xml_path(self._XMLDesc(0), func=disks)

    def get_media_device(self):
        def disks(ctx):
            result = []
            for interface in ctx.xpathEval('/domain/devices/disk'):
                device = interface.xpathEval('@device')[0].content
                if device == 'cdrom':
                    try:
                        dev = interface.xpathEval('target/@dev')[0].content
                        file = interface.xpathEval('source/@file')[0].content
                        vol = self.get_volume_by_path(file)
                        stg = vol.storagePoolLookupByVolume()
                        result.append({'dev': dev, 'image': vol.name(), 'storage': stg.name(), 'path': file})
                    except:
                        pass
            return result
        return util.get_xml_path(self._XMLDesc(0), func=disks)

    def get_vnc(self):
        vnc = util.get_xml_path(self._XMLDesc(0),
                                "/domain/devices/graphics/@port")
        return vnc

    def mount_iso(self, image):
        storages = self.get_storages()
        for storage in storages:
            stg = self.get_storage(storage)
            for img in stg.listVolumes():
                if image == img:
                    vol = stg.storageVolLookupByName(image)
                    if self.get_status() == 1:
                        xml = """<disk type='file' device='cdrom'>
                                    <driver name='qemu' type='raw'/>
                                    <target dev='hda' bus='ide'/>
                                    <source file='%s'/>
                                 </disk>""" % vol.path()
                        self.instance.attachDevice(xml)
                        xmldom = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
                        self._defineXML(xmldom)
                    if self.get_status() == 5:
                        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
                        newxml = """<disk type='file' device='cdrom'>
                                      <driver name='qemu' type='raw'/>
                                      <target dev='hda' bus='ide'/>
                                      <source file='%s'/>""" % vol.path()
                        xml_string = "<disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>"
                        xmldom = xml.replace(xml_string, newxml)
                        self._defineXML(xmldom)

    def umount_iso(self, image):
        if self.get_status() == 1:
            xml = """<disk type='file' device='cdrom'>
                         <driver name="qemu" type='raw'/>
                         <target dev='hda' bus='ide'/>
                         <readonly/>
                      </disk>"""
            self.instance.attachDevice(xml)
            xmldom = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
            self._defineXML(xmldom)
        if self.get_status() == 5:
            xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
            xmldom = xml.replace("<source file='%s'/>\n" % image, '')
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
        devices=[]
        dev_usage = []
        tree = ElementTree.fromstring(self._XMLDesc(0))
        for source, target in zip(tree.findall("devices/disk/source"),
                                  tree.findall("devices/disk/target")):
            if source.get("file").endswith('.img'):
                devices.append([source.get("file"), target.get("dev")])
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
        devices=[]
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

    def get_vnc_passwd(self):
        return util.get_xml_path(self._XMLDesc(VIR_DOMAIN_XML_SECURE),
                                 "/domain/devices/graphics/@passwd")

    def set_vnc_passwd(self, passwd):
        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        find_tag = re.findall('<graphics.*/>', xml)
        if find_tag:
            close_tag = '/'
        else:
            close_tag = ''
        newxml = "<graphics type='vnc' passwd='%s'%s>" % (passwd, close_tag)
        xmldom = re.sub('<graphics.*>', newxml, xml)
        self._defineXML(xmldom)

    def change_settings(self, description, memory, vcpu):
        """
        Function change ram and cpu on vds.
        """
        xml = self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        memory = int(memory) * 1024
        xml_memory = "<memory unit='KiB'>%s</memory>" % memory
        xml_memory_change = re.sub('<memory.*memory>', xml_memory, xml)
        xml_curmemory = "<currentMemory unit='KiB'>%s</currentMemory>" % memory
        xml_curmemory_change = re.sub('<currentMemory.*currentMemory>', xml_curmemory, xml_memory_change)
        xml_vcpu = "<vcpu>%s</vcpu>" % vcpu
        xml_vcpu_change = re.sub('<vcpu.*vcpu>', xml_vcpu, xml_curmemory_change)
        xml_description = "<description>%s</description>" % description
        xml_description_change = re.sub('<description.*description>', xml_description, xml_vcpu_change)
        self._defineXML(xml_description_change)

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

    def create_snapshot(self):
        xml = """<domainsnapshot>\n
                     <name>%d</name>\n
                     <state>shutoff</state>\n
                     <creationTime>%d</creationTime>\n""" % (time.time(), time.time())
        xml += self._XMLDesc(VIR_DOMAIN_XML_SECURE)
        xml += """<active>0</active>\n
                  </domainsnapshot>"""
        self._snapshotCreateXML(xml, 0)
