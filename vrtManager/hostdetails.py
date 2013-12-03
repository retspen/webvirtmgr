#
# Copyright (C) 2013 Webvirtmgr.
#
import time
import virtinst
from vrtManager.conection import wvmConnect
from vrtManager.util import get_xml_path


class wvmHostDetails(wvmConnect):
    def memory_get_usage(self):
        """
        Function return memory usage on node.
        """
        get_all_mem = self.wvm.getInfo()[1] * 1048576
        get_freemem = self.wvm.getMemoryStats(-1, 0)
        if type(get_freemem) == dict:
            free = (get_freemem.values()[0] + \
                    get_freemem.values()[2] + \
                    get_freemem.values()[3]) * 1024
            percent = (100 - ((free * 100) / get_all_mem))
            usage = (get_all_mem - free)
            mem_usage = {'usage': usage, 'percent': percent}
        else:
            mem_usage = {'usage': None, 'percent': None}
        return mem_usage

    def cpu_get_usage(self):
        """
        Function return cpu usage on node.
        """
        prev_idle = 0
        prev_total = 0
        cpu = self.wvm.getCPUStats(-1, 0)
        if type(cpu) == dict:
            for num in range(2):
                idle = self.wvm.getCPUStats(-1, 0).values()[1]
                total = sum(self.wvm.getCPUStats(-1, 0).values())
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
            return {'usage': None}
        return {'usage': diff_usage}

    def get_node_info(self):
        """
        Function return host server information: hostname, cpu, memory, ...
        """
        info = []
        info.append(self.wvm.getHostname())
        info.append(self.wvm.getInfo()[0])
        info.append(self.wvm.getInfo()[1] * 1048576)
        info.append(self.wvm.getInfo()[2])
        try:
            info.append(get_xml_path(self.wvm.getSysinfo(0),
                                     "/sysinfo/processor/entry[6]"))
        except Exception:
            info.append('Unknown')
        info.append(self.wvm.getURI())
        return info

    def get_guest_cap(self):
        """Get guest capabilities"""
        return virtinst.CapabilitiesParser.guest_lookup(self.wvm)

    def hypervisor_type(self):
        """Return hypervisor type"""
        return self.get_guest_cap()[1].hypervisor_type
