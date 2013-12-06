#
# Copyright (C) 2013 Webvirtmgr.
#
import time
from vrtManager import util
from xml.etree import ElementTree
from vrtManager.conection import wvmConnect


class wvmInstances(wvmConnect):
    def get_instance(self, name):
        return self.wvm.lookupByName(name)

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

    def suspend(self, name):
        self.instance.suspend()

    def resume(self, name):
        self.instance.resume()

    def delete(self, name):
        self.instance.undefine()

    def get_status(self):
        return self.instance.info()[0]

    def get_vcpu(self):
        return util.get_xml_path(self._XMLDesc(0), "/domain/vcpu")

    def get_memory(self):
        mem = util.get_xml_path(self._XMLDesc(0), "/domain/memory")
        return int(mem) / 1024

    def get_net_device(self):
        def networks(ctx):
            result = []
            for interface in ctx.xpathEval('/domain/devices/interface'):
                mac = interface.xpathEval('mac/@address')[0].content
                nic = interface.xpathEval('source/@network|source/@bridge')[0].content
                result.append({'mac': mac, 'nic': nic})
            return result
        return util.get_xml_path(self._XMLDesc(0), func=networks)

    def get_disk_device(self):
        def disks(ctx):
            result = []
            for interface in ctx.xpathEval('/domain/devices/disk'):
                device = interface.xpathEval('@device')[0].content
                if device == 'disk':
                    dev = interface.xpathEval('targe/@dev')[0].content
                    file = interface.xpathEval('source/@file')[0].content
                    result.append({'dev': dev, 'disk': file})
            return result
        return util.get_xml_path(self._XMLDesc(0), func=disks)

    def get_media_device(self):
        def disks(ctx):
            result = []
            for interface in ctx.xpathEval('/domain/devices/disk'):
                device = interface.xpathEval('@device')[0].content
                if device == 'cdrom':
                    dev = interface.xpathEval('targe/@dev')[0].content
                    file = interface.xpathEval('source/@file')[0].content
                    result.append({'dev': dev, 'disk': file})
            return result
        return util.get_xml_path(self._XMLDesc(0), func=disks)

    def _XMLDesc(self, flag):
        return self.instance.XMLDesc(flag)

    def get_vnc(self):
        vnc = util.get_xml_path(self._XMLDesc(0),
                                "/domain/devices/graphics/@port")
        return vnc

    def mount_iso(self, image):
        storages = self.storages_get_node()
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
                        newxml = """<disk type='file' device='cdrom'>
                                    <driver name='qemu' type='raw'/>
                                    <source file='%s'/>""" % vol.path()
                        xmldom = xml.replace("""<disk type='file' device='cdrom'>
                                                <driver name='qemu' type='raw'/>""", newxml)
                        self.wvm.defineXML(xmldom)

    def umount_iso(self, image):
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
        tree = ElementTree.fromstring(dom.XMLDesc(0))
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

    def _defineXML(self, xml):
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
