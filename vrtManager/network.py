#
# Copyright (C) 2013 Webvirtmgr.
#
from vrtManager import util
from vrtManager.IPy import IP
from vrtManager.connection import wvmConnect


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
        return gateway, mask, None


class wvmNetworks(wvmConnect):
    def get_networks_info(self):
        get_networks = self.get_networks()
        networks = []
        for network in get_networks:
            net = self.get_network(network)
            net_status = net.isActive()
            net_bridge = net.bridgeName()
            net_forwd = util.get_xml_path(net.XMLDesc(0), "/network/forward/@mode")
            networks.append({'name': network, 'status': net_status,
                             'device': net_bridge, 'forward': net_forwd})
        return networks

    def define_network(self, xml):
        self.wvm.networkDefineXML(xml)

    def create_network(self, name, forward, gateway, mask, dhcp, bridge, openvswitch, fixed=False):
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
        if openvswitch is True:
            xml += """<virtualport type='openvswitch'/>"""
        if forward != 'bridge':
            xml += """
                        <ip address='%s' netmask='%s'>""" % (gateway, mask)
            if dhcp:
                xml += """<dhcp>
                            <range start='%s' end='%s' />""" % (dhcp[0], dhcp[1])
                if fixed:
                    fist_oct = int(dhcp[0].strip().split('.')[3])
                    last_oct = int(dhcp[1].strip().split('.')[3])
                    for ip in range(fist_oct, last_oct + 1):
                        xml += """<host mac='%s' ip='%s.%s' />""" % (util.randomMAC(), gateway[:-2], ip)
                xml += """</dhcp>"""

            xml += """</ip>"""
        xml += """</network>"""
        self.define_network(xml)
        net = self.get_network(name)
        net.create()
        net.setAutostart(1)


class wvmNetwork(wvmConnect):
    def __init__(self, host, login, passwd, conn, net):
        wvmConnect.__init__(self, host, login, passwd, conn)
        self.net = self.get_network(net)

    def get_name(self):
        return self.net.name()

    def _XMLDesc(self, flags):
        return self.net.XMLDesc(flags)

    def get_autostart(self):
        return self.net.autostart()

    def set_autostart(self, value):
        self.net.setAutostart(value)

    def is_active(self):
        return self.net.isActive()

    def get_uuid(self):
        return self.net.UUIDString()

    def get_bridge_device(self):
        try:
            return self.net.bridgeName()
        except:
            return None

    def start(self):
        self.net.create()

    def stop(self):
        self.net.destroy()

    def delete(self):
        self.net.undefine()

    def get_ipv4_network(self):
        xml = self._XMLDesc(0)
        if util.get_xml_path(xml, "/network/ip") is None:
            return None
        addrStr = util.get_xml_path(xml, "/network/ip/@address")
        netmaskStr = util.get_xml_path(xml, "/network/ip/@netmask")
        prefix = util.get_xml_path(xml, "/network/ip/@prefix")

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
        xml = self._XMLDesc(0)
        fw = util.get_xml_path(xml, "/network/forward/@mode")
        forwardDev = util.get_xml_path(xml, "/network/forward/@dev")
        return [fw, forwardDev]

    def get_ipv4_dhcp_range(self):
        xml = self._XMLDesc(0)
        dhcpstart = util.get_xml_path(xml, "/network/ip/dhcp/range[1]/@start")
        dhcpend = util.get_xml_path(xml, "/network/ip/dhcp/range[1]/@end")
        if not dhcpstart or not dhcpend:
            return None

        return [IP(dhcpstart), IP(dhcpend)]

    def get_ipv4_dhcp_range_start(self):
        dhcp = self.get_ipv4_dhcp_range()
        if not dhcp:
            return None

        return dhcp[0]

    def get_ipv4_dhcp_range_end(self):
        dhcp = self.get_ipv4_dhcp_range()
        if not dhcp:
            return None

        return dhcp[1]

    def can_pxe(self):
        xml = self.get_xml()
        forward = self.get_ipv4_forward()[0]
        if forward and forward != "nat":
            return True
        return bool(util.get_xml_path(xml, "/network/ip/dhcp/bootp/@file"))

    def get_mac_ipaddr(self):
        def network(ctx):
            result = []
            for net in ctx.xpathEval('/network/ip/dhcp/host'):
                host = net.xpathEval('@ip')[0].content
                mac = net.xpathEval('@mac')[0].content
                result.append({'host': host, 'mac': mac})
            return result

        return util.get_xml_path(self._XMLDesc(0), func=network)
