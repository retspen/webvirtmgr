#
# Copyright (C) 2013 Webvirtmgr.
#

from vrtManager import util
from vrtManager.IPy import IP

def network_size(net, dhcp=None):
    """

    Func return gateway, mask and dhcp pool.

    """
    mask = IP(net).strNetmask()
    addr = IP(net)
    if addr[0].strNormal()[-1] == '0':
        gateway = addr[1].strNormal()
        dhcp_pool = [addr[2].strNormal(), addr[addr.len() - 2].strNormal()]
    else:
        gateway = addr[0].strNormal()
        dhcp_pool = [addr[1].strNormal(), addr[addr.len() - 2].strNormal()]
    if dhcp:
        return gateway, mask, dhcp_pool
    else:
        return gateway, mask, No

class vmmNetwork(vmmLibvirtObject):
    def __init__(self, conn, net, uuid, active):
        vmmLibvirtObject.__init__(self, conn)
        self.net = net
        self.uuid = uuid
        self.active = active

    # Required class methods
    def get_name(self):
        return self.net.name()
    def _XMLDesc(self, flags):
        return self.net.XMLDesc(flags)
    def _define(self, xml):
        return self.conn.vmm.networkDefineXML(xml)

    def set_active(self, state):
        self.active = state

    def is_active(self):
        return self.active

    def get_label(self):
        return self.get_name()

    def get_uuid(self):
        return self.uuid

    def get_bridge_device(self):
        try:
            return self.net.bridgeName()
        except:
            return ""

    def start(self):
        self.net.create()

    def stop(self):
        self.net.destroy()

    def delete(self):
        self.net.undefine()
        del(self.net)
        self.net = None

    def set_autostart(self, value):
        self.net.setAutostart(value)

    def get_autostart(self):
        return self.net.autostart()

    def get_ipv4_network(self):
        xml = self.get_xml()
        if util.xpath(xml, "/network/ip") is None:
            return None
        addrStr = util.xpath(xml, "/network/ip/@address")
        netmaskStr = util.xpath(xml, "/network/ip/@netmask")
        prefix = util.xpath(xml, "/network/ip/@prefix")

        if prefix:
            prefix = int(prefix)
            binstr = ((prefix * "1") + ((32 - prefix) * "0"))
            netmaskStr = str(IP(int(binstr, base=2)))

        if netmaskStr:
            netmask = IP(netmaskStr)
            gateway = IP(addrStr)
            network = IP(gateway.int() & netmask.int())
            ret = IP(str(network) + "/" + netmaskStr)
        else:
            ret = IP(str(addrStr))

        return ret

    def get_ipv4_forward(self):
        xml = self.get_xml()
        fw = util.xpath(xml, "/network/forward/@mode")
        forwardDev = util.xpath(xml, "/network/forward/@dev")
        return [fw, forwardDev]

    def get_ipv4_dhcp_range(self):
        xml = self.get_xml()
        dhcpstart = util.xpath(xml, "/network/ip/dhcp/range[1]/@start")
        dhcpend = util.xpath(xml, "/network/ip/dhcp/range[1]/@end")
        if not dhcpstart or not dhcpend:
            return None

        return [IP(dhcpstart), IP(dhcpend)]

    def pretty_forward_mode(self):
        forward, forwardDev = self.get_ipv4_forward()
        return vmmNetwork.pretty_desc(forward, forwardDev)

    def can_pxe(self):
        xml = self.get_xml()
        forward = self.get_ipv4_forward()[0]
        if forward and forward != "nat":
            return True
        return bool(util.xpath(xml, "/network/ip/dhcp/bootp/@file"))