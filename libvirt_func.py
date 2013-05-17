# -*- coding: utf-8 -*-


def libvirt_conn(host):
    """

    Function for connect to libvirt host.
    Create exceptions and return if not connnected.

    """

    import libvirt

    if host.conn_type == 'tcp':
        def creds(credentials, user_data):
            for credential in credentials:
                if credential[0] == libvirt.VIR_CRED_AUTHNAME:
                    credential[4] = host.login
                    if len(credential[4]) == 0:
                        credential[4] = credential[3]
                elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
                    credential[4] = host.passwd
                else:
                    return -1
            return 0

        flags = [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE]
        auth = [flags, creds, None]
        uri = 'qemu+tcp://%s/system' % host.ipaddr
    if host.conn_type == 'ssh':
        uri = 'qemu+ssh://%s@%s:%s/system' % (host.login, host.ipaddr, host.ssh_port)

    try:
        if host.conn_type == 'tcp':
            conn = libvirt.openAuth(uri, auth, 0)
        if host.conn_type == 'ssh':
            conn = libvirt.open(uri)
        return conn
    except libvirt.libvirtError as e:
        return {'error': e.message}


def hard_accel_node(conn):
    """

    Check hardware acceleration.

    """
    import re
    xml = conn.getCapabilities()
    kvm = re.search('kvm', xml)
    if kvm:
        return True
    else:
        return False


def vms_get_node(conn):
    """

    Get all VM in host server

    """

    import libvirt

    try:
        vname = {}
        for id in conn.listDomainsID():
            id = int(id)
            dom = conn.lookupByID(id)
            vname[dom.name()] = dom.info()[0]
        for id in conn.listDefinedDomains():
            dom = conn.lookupByName(id)
            vname[dom.name()] = dom.info()[0]
        return vname
    except libvirt.libvirtError as e:
        add_error(e, 'libvirt')
        return "error"


def networks_get_node(conn):
    """

    Function return host server virtual networks.

    """

    virtnet = {}
    for network in conn.listNetworks():
        net = conn.networkLookupByName(network)
        status = net.isActive()
        virtnet[network] = status
    for network in conn.listDefinedNetworks():
        net = conn.networkLookupByName(network)
        status = net.isActive()
        virtnet[network] = status
    return virtnet


def storages_get_node(conn):
    """

    Function return host server storages.

    """

    storages = {}
    for storage in conn.listStoragePools():
        stg = conn.storagePoolLookupByName(storage)
        status = stg.isActive()
        storages[storage] = status
    for storage in conn.listDefinedStoragePools():
        stg = conn.storagePoolLookupByName(storage)
        status = stg.isActive()
        storages[storage] = status
    return storages


def node_get_info(conn):
    """

    Function return host server information: hostname, cpu, memory, ...

    """

    from libvirt import libvirtError
    import virtinst.util as util
    try:
        info = []
        xml_inf = conn.getSysinfo(0)
        info.append(conn.getHostname())
        info.append(conn.getInfo()[0])
        info.append(conn.getInfo()[2])
        info.append(util.get_xml_path(xml_inf, "/sysinfo/processor/entry[6]"))
        return info
    except libvirtError:
        return "error"


def memory_get_usage(conn):
    """

    Function return memory usage on node.

    """

    from libvirt import libvirtError
    try:
        allmem = conn.getInfo()[1] * 1048576
        get_freemem = conn.getMemoryStats(-1, 0)
        if type(get_freemem) == dict:
            freemem = (get_freemem.values()[0] + get_freemem.values()[2] + get_freemem.values()[3]) * 1024
            percent = (freemem * 100) / allmem
            percent = 100 - percent
            memusage = (allmem - freemem)
        else:
            memusage = None
            percent = None
        return allmem, memusage, percent
    except libvirtError:
        return "error"


def cpu_get_usage(conn):
    """

    Function return cpu usage on node.

    """

    import time
    from libvirt import libvirtError
    try:
        prev_idle = 0
        prev_total = 0
        cpu = conn.getCPUStats(-1, 0)
        if type(cpu) == dict:
            for num in range(2):
                    idle = conn.getCPUStats(-1, 0).values()[1]
                    total = sum(conn.getCPUStats(-1, 0).values())
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
    except libvirtError as e:
        return e.message


def new_volume(storage, name, size):
    """

    Add new volume in storage

    """
    import virtinst.util as util

    size = int(size) * 1073741824
    stg_type = util.get_xml_path(storage.XMLDesc(0), "/pool/@type")
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
    storage.createXML(xml, 0)


def images_get_storages(conn, storages):
    """

    Function return all images on all storages

    """

    import re
    disk = []
    for storage in storages:
        stg = conn.storagePoolLookupByName(storage)
        stg.refresh(0)
        for img in stg.listVolumes():
            if re.findall(".iso", img) or re.findall(".ISO", img):
                pass
            else:
                disk.append(img)
    return disk


def image_get_path(conn, vol, storages):
    """

    Function return volume path.

    """

    for storage in storages:
        stg = conn.storagePoolLookupByName(storage)
        for img in stg.listVolumes():
            if vol == img:
                vl = stg.storageVolLookupByName(vol)
                return vl.path()
