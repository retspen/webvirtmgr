# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from webvirtmgr.virtmgr.models import *


def libvirt_conn(host):
    """
    Function for connect to libvirt host.
    Create exceptions and return if not connnected.

    """

    import libvirt

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

    try:
        conn = libvirt.openAuth(uri, auth, 0)
        return conn
    except libvirt.libvirtError as e:
        return {'error': e.message}


def test_cpu_accel(conn):
    import re
    xml = conn.getCapabilities()
    kvm = re.search('kvm', xml)
    if kvm:
        return True
    else:
        return False


def get_all_vm(conn):
    """

    Get all VM in host

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


def get_all_networks(conn):
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


def get_all_storages(conn):
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


def get_host_info(conn):
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


def get_mem_usage(conn):
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


def get_cpu_usage(conn):
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


def index(request):
    """

    Start page.

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')
    else:
        return HttpResponseRedirect('/dashboard')


def dashboard(request):
    """

    Dashboard page.

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    def get_hosts_status(hosts):
        all_hosts = {}
        for host in hosts:
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.connect((host.ipaddr, 16509))
                s.close()
                status = 1
            except Exception as err:
                status = err
            all_hosts[host.hostname] = (host.id, host.ipaddr, status)
        return all_hosts

    def del_host(host_id):
        hosts = Host.objects.get(id=host_id)
        hosts.delete()

    def add_host(host, ipaddr, login, passwd):
        hosts = Host(hostname=host, ipaddr=ipaddr, login=login, passwd=passwd)
        hosts.save()

    hosts = Host.objects.filter()
    host_info = get_hosts_status(hosts)
    errors = []

    if request.method == 'POST':
        if 'del_host' in request.POST:
            host_id = request.POST.get('host_id', '')
            del_host(host_id)
            return HttpResponseRedirect(request.get_full_path())
        if request.POST.get('add_host', ''):
            name = request.POST.get('hostname', '')
            ipaddr = request.POST.get('ipaddr', '')
            login = request.POST.get('kvm_login', '')
            passwd = request.POST.get('kvm_passwd', '')

            import re
            simbol = re.search('[^a-zA-Z0-9\-\.]+', name)
            ipsimbol = re.search('[^a-z0-9\.\-]+', ipaddr)
            domain = re.search('[\.]+', ipaddr)

            if not name:
                msg = 'No hostname has been entered'
                errors.append(msg)
            elif len(name) > 20:
                msg = 'The host name must not exceed 20 characters'
                errors.append(msg)
            elif simbol:
                msg = 'The host name must not contain any characters'
                errors.append(msg)
            if not ipaddr:
                msg = 'No IP address has been entered'
                errors.append(msg)
            elif ipsimbol or not domain:
                msg = 'Hostname must contain only numbers, or the domain name separated by "."'
                errors.append(msg)
            else:
                have_host = Host.objects.filter(hostname=name)
                have_ip = Host.objects.filter(ipaddr=ipaddr)
                if have_host or have_ip:
                    msg = 'This host is already connected'
                    errors.append(msg)
            if not login:
                msg = 'No KVM login was been entered'
                errors.append(msg)
            if not passwd:
                msg = 'No KVM password was been entered'
                errors.append(msg)
            if not errors:
                add_host(name, ipaddr, login, passwd)
                return HttpResponseRedirect(request.get_full_path())

    return render_to_response('dashboard.html', locals(), context_instance=RequestContext(request))


def clusters(request):
    """

    Infrastructure page.

    """

    def vms_on_host():
        import virtinst.util as util
        import libvirt
        host_mem = conn.getInfo()[1] * 1048576
        try:
            vname = {}
            for id in conn.listDomainsID():
                id = int(id)
                dom = conn.lookupByID(id)
                mem = util.get_xml_path(dom.XMLDesc(0), "/domain/memory")
                mem = int(mem) * 1024
                mem_usage = (mem * 100) / host_mem
                vcpu = util.get_xml_path(dom.XMLDesc(0), "/domain/vcpu")
                vname[dom.name()] = (dom.info()[0], vcpu, mem, mem_usage)
            for id in conn.listDefinedDomains():
                dom = conn.lookupByName(id)
                mem = util.get_xml_path(dom.XMLDesc(0), "/domain/memory")
                mem = int(mem) * 1024
                mem_usage = (mem * 100) / host_mem
                vcpu = util.get_xml_path(dom.XMLDesc(0), "/domain/vcpu")
                vname[dom.name()] = (dom.info()[0], vcpu, mem, mem_usage)
            return vname
        except libvirt.libvirtError as e:
            add_error(e, 'libvirt')
            return "error"

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    hosts = Host.objects.filter().order_by('id')
    hosts_vms = {}

    for host in hosts:
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((host.ipaddr, 16509))
            s.close()
            status = 1
        except Exception as err:
            status = 2

        if status == 1:
            conn = libvirt_conn(host)
            host_info = get_host_info(conn)
            host_mem = get_mem_usage(conn)
            hosts_vms[host.id, host.hostname, status, host_info[2], host_mem[0], host_mem[2]] = vms_on_host()
        else:
            hosts_vms[host.id, host.hostname, status, None, None, None] = None

    return render_to_response('clusters.html', locals(), context_instance=RequestContext(request))


def overview(request, host_id):
    """

    Overview page.

    """

    from libvirt import libvirtError

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = libvirt_conn(host)

    if type(conn) == dict:
        errors = []
        errors.append(conn.values()[0])
    else:
        have_kvm = test_cpu_accel(conn)
        if not have_kvm:
            errors = []
            errors.append('Your CPU doesn\'t support hardware virtualization')

        all_vm = get_all_vm(conn)
        host_info = get_host_info(conn)
        mem_usage = get_mem_usage(conn)
        cpu_usage = get_cpu_usage(conn)
        lib_virt_ver = conn.getLibVersion()
        conn_type = conn.getURI()

        if request.method == 'POST':
            vname = request.POST.get('vname', '')
            dom = conn.lookupByName(vname)
            if 'start' in request.POST:
                try:
                    dom.create()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'shutdown' in request.POST:
                try:
                    dom.shutdown()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'destroy' in request.POST:
                try:
                    dom.destroy()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'suspend' in request.POST:
                try:
                    dom.suspend()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'resume' in request.POST:
                try:
                    dom.resume()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)

        conn.close()

    return render_to_response('overview.html', locals(), context_instance=RequestContext(request))


def newvm(request, host_id):
    """

    New VM's.

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    def find_all_img(storages):
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

    def get_img_path(vol, storages):
        for storage in storages:
            stg = conn.storagePoolLookupByName(storage)
            for img in stg.listVolumes():
                if vol == img:
                    vl = stg.storageVolLookupByName(vol)
                    return vl.path()

    def add_vol(name, size):
        import virtinst.util as util

        stg_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
        if stg_type == 'dir':
            name = name + '.img'
        size = int(size) * 1073741824
        xml = """
            <volume>
                <name>%s</name>
                <capacity>%s</capacity>
                <allocation>0</allocation>
                <target>
                    <format type='qcow2'/>
                </target>
            </volume>""" % (name, size)
        stg.createXML(xml, 0)

    def add_vm(name, ram, vcpu, image, net, passwd):
        import virtinst.util as util
        import re

        ram = int(ram) * 1024
        iskvm = re.search('kvm', conn.getCapabilities())
        if iskvm:
            dom_type = 'kvm'
        else:
            dom_type = 'qemu'

        machine = util.get_xml_path(conn.getCapabilities(), "/capabilities/guest/arch/machine/@canonical")
        if not machine:
            machine = 'pc-1.0'

        if re.findall('/usr/bin/qemu-system-x86_64', conn.getCapabilities()):
            emulator = '/usr/bin/qemu-system-x86_64'
        elif re.findall('/usr/libexec/qemu-kvm', conn.getCapabilities()):
            emulator = '/usr/libexec/qemu-kvm'
        elif re.findall('/usr/bin/kvm', conn.getCapabilities()):
            emulator = '/usr/bin/kvm'
        else:
            emulator = '/usr/bin/qemu-system-x86_64'

        img = conn.storageVolLookupByPath(image)
        vol = img.name()
        for storage in all_storages:
            stg = conn.storagePoolLookupByName(storage)
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
                  <memory>%s</memory>
                  <currentMemory>%s</currentMemory>
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
                      <source file='%s'/>
                      <target dev='hda' bus='ide'/>
                    </disk>
                    <disk type='file' device='cdrom'>
                      <driver name='qemu' type='raw'/>
                      <source file=''/>
                      <target dev='hdc' bus='ide'/>
                      <readonly/>
                    </disk>
                    <controller type='ide' index='0'>
                      <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x1'/>
                    </controller>""" % (dom_type, name, ram, ram, vcpu, machine, emulator, image_type, image)

        if re.findall("br", net):
            xml += """<interface type='bridge'>
                    <source bridge='%s'/>""" % (net)
        else:
            xml += """<interface type='network'>
                    <source network='%s'/>""" % (net)

        xml += """<address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
                    </interface>
                    <input type='tablet' bus='usb'/>
                    <input type='mouse' bus='ps2'/>
                    <graphics type='vnc' port='-1' autoport='yes' keymap='en-us' passwd='%s'/>
                    <video>
                      <model type='cirrus' vram='9216' heads='1'/>
                      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>
                    </video>
                    <memballoon model='virtio'>
                      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
                    </memballoon>
                  </devices>
                </domain>""" % (passwd)
        conn.defineXML(xml)
        dom = conn.lookupByName(name)
        dom.setAutostart(1)

    host = Host.objects.get(id=host_id)
    conn = libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        have_kvm = test_cpu_accel(conn)

        try:
            flavors = Flavor.objects.filter().order_by('id')
        except:
            flavors = 'error'

        errors = []

        all_vm = get_all_vm(conn)
        all_networks = get_all_networks(conn)
        all_storages = get_all_storages(conn)
        all_img = find_all_img(all_storages)

        if not all_networks:
            errors.append('You doesn\'t have any virtual networks')
        if not all_storages:
            errors.append('You doesn\'t have any storages')
        if not have_kvm:
            errors.append('Your CPU doesn\'t support hardware virtualization')

        digits = [a for a in range(1, 601)]

        if not flavors and flavors != 'error':
            add_flavor = Flavor(name='micro', vcpu='1', ram='256', hdd='10')
            add_flavor.save()
            add_flavor = Flavor(name='mini', vcpu='1', ram='512', hdd='20')
            add_flavor.save()
            add_flavor = Flavor(name='small', vcpu='2', ram='1024', hdd='40')
            add_flavor.save()
            add_flavor = Flavor(name='medium', vcpu='2', ram='2048', hdd='80')
            add_flavor.save()
            add_flavor = Flavor(name='large', vcpu='4', ram='4096', hdd='160')
            add_flavor.save()
            add_flavor = Flavor(name='xlarge', vcpu='6', ram='8192', hdd='320')
            add_flavor.save()
            return HttpResponseRedirect(request.get_full_path())

        if request.method == 'POST':
            if 'add_flavor' in request.POST:
                name = request.POST.get('name', '')
                vcpu = request.POST.get('vcpu', '')
                ram = request.POST.get('ram', '')
                hdd = request.POST.get('hdd', '')

                for flavor in flavors:
                    if name == flavor.name:
                        errors.append('Name already use')
                if not errors:
                    flavor_add = Flavor(name=name, vcpu=vcpu, ram=ram, hdd=hdd)
                    flavor_add.save()
                    return HttpResponseRedirect(request.get_full_path())

            if 'del_flavor' in request.POST:
                flavor_id = request.POST.get('flavor', '')
                flavor_del = Flavor.objects.get(id=flavor_id)
                flavor_del.delete()
                return HttpResponseRedirect(request.get_full_path())

            if 'newvm' in request.POST:
                net = request.POST.get('network', '')
                storage = request.POST.get('storage', '')
                vname = request.POST.get('name', '')
                hdd_size = request.POST.get('hdd_size', '')
                img = request.POST.get('img', '')
                ram = request.POST.get('ram', '')
                vcpu = request.POST.get('vcpu', '')

                errors = []

                import re
                simbol = re.search('[^a-zA-Z0-9\_\-\.]+', vname)

                if vname in all_vm:
                    msg = 'This is the name of the virtual machine already exists'
                    errors.append(msg)
                if len(vname) > 12:
                    msg = 'The name of the virtual machine must not exceed 12 characters'
                    errors.append(msg)
                if simbol:
                    msg = 'The name of the virtual machine must not contain any characters'
                    errors.append(msg)
                if not vname:
                    msg = 'Enter the name of the virtual machine'
                    errors.append(msg)
                if not errors:
                    stg = conn.storagePoolLookupByName(storage)

                    if not hdd_size:
                        if not img:
                            msg = 'First you need to create an image'
                            errors.append(msg)
                        else:
                            image = get_img_path(img, all_storages)
                    else:
                        from libvirt import libvirtError
                        try:
                            add_vol(vname, hdd_size)
                        except libvirtError as msg_error:
                            errors.append(msg_error.message)

                    if not errors:
                        if not img:
                            import virtinst.util as util

                            stg_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
                            if stg_type == 'dir':
                                vol = vname + '.img'
                            else:
                                vol = vname
                        else:
                            vol = img
                        vl = stg.storageVolLookupByName(vol)
                        image = vl.path()

                        from string import letters, digits
                        from random import choice

                        vnc_passwd = ''.join([choice(letters + digits) for i in range(12)])

                        new_vm = Vm(host_id=host_id, vname=vname, vnc_passwd=vnc_passwd)
                        new_vm.save()

                        add_vm(vname, ram, vcpu, image, net, vnc_passwd)

                        return HttpResponseRedirect('/vm/%s/%s/' % (host_id, vname))

        conn.close()

    return render_to_response('newvm.html', locals(), context_instance=RequestContext(request))


def storage(request, host_id, pool):
    """

    Storages block

    """

    from libvirt import libvirtError

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    def add_new_pool(type_pool, name, source, target):
        xml = """
                <pool type='%s'>
                <name>%s</name>""" % (type_pool, name)

        if pool_type == 'logical':
            xml += """
                  <source>
                    <device path='%s'/>
                    <name>%s</name>
                    <format type='lvm2'/>
                  </source>""" % (source, name)

        if pool_type == 'logical':
            target = '/dev/' + name

        xml += """
                  <target>
                       <path>%s</path>
                  </target>
                </pool>""" % (target)
        conn.storagePoolDefineXML(xml, 0)

    def add_vol(name, size):
        import virtinst.util as util

        stg_type = util.get_xml_path(stg.XMLDesc(0), "/pool/@type")
        if stg_type == 'dir':
            name = name + '.img'
        size = int(size) * 1073741824
        xml = """
            <volume>
                <name>%s</name>
                <capacity>%s</capacity>
                <allocation>0</allocation>
                <target>
                    <format type='qcow2'/>
                </target>
            </volume>""" % (name, size)
        stg.createXML(xml, 0)

    def clone_vol(img, new_img):
        import virtinst.util as util

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

    def stg_info():
        import virtinst.util as util

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

    def stg_vol():
        import virtinst.util as util

        volinfo = {}
        for name in stg.listVolumes():
            vol = stg.storageVolLookupByName(name)
            xml = vol.XMLDesc(0)
            size = vol.info()[1]
            format = util.get_xml_path(xml, "/volume/target/format/@type")
            volinfo[name] = size, format
        return volinfo

    def all_storages():
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

    host = Host.objects.get(id=host_id)
    conn = libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/manage/')
    else:

        storages = all_storages()

        if pool is None:
            if len(storages) == 0:
                return HttpResponseRedirect('/storage/%s/add/' % (host_id))
            else:
                return HttpResponseRedirect('/storage/%s/%s/' % (host_id, storages.keys()[0]))

        if pool == 'add':
            if request.method == 'POST':
                if 'addpool' in request.POST:
                    pool_name = request.POST.get('name', '')
                    pool_type = request.POST.get('type', '')
                    pool_target = request.POST.get('target', '')
                    pool_source = request.POST.get('source', '')

                    import re
                    errors = []
                    name_have_simbol = re.search('[^a-zA-Z0-9\_\-]+', pool_name)
                    path_have_simbol = re.search('[^a-zA-Z0-9\/]+', pool_source)

                    if name_have_simbol or path_have_simbol:
                        msg = 'The host name must not contain any characters'
                        errors.append(msg)
                    if not pool_name:
                        msg = 'No pool name has been entered'
                        errors.append(msg)
                    elif len(pool_name) > 12:
                        msg = 'The host name must not exceed 12'
                        errors.append(msg)
                    if pool_type == 'logical':
                        if not pool_source:
                            msg = 'No device has been entered'
                            errors.append(msg)
                    if pool_type == 'dir':
                        if not pool_target:
                            msg = 'No path has been entered'
                            errors.append(msg)
                    if pool_name in storages.keys():
                        msg = 'Pool name already use'
                        errors.append(msg)
                    if not errors:
                        try:
                            add_new_pool(pool_type, pool_name, pool_source, pool_target)
                            stg = conn.storagePoolLookupByName(pool_name)
                            if pool_type == 'logical':
                                stg.build(0)
                            stg.create(0)
                            stg.setAutostart(1)
                            return HttpResponseRedirect('/storage/%s/%s/' % (host_id, pool_name))
                        except libvirtError as error_msg:
                            errors.append(error_msg.message)
        else:
            all_vm = get_all_vm(conn)
            form_hdd_size = [10, 20, 40, 80, 160, 320]
            stg = conn.storagePoolLookupByName(pool)

            info = stg_info()

            # refresh storage if acitve
            if info[5] == True:
                stg.refresh(0)
                volumes_info = stg_vol()

            if request.method == 'POST':
                if 'start' in request.POST:
                    try:
                        stg.create(0)
                        msg = 'Start storage pool: %s' % pool
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                    return HttpResponseRedirect('/storage/%s/%s' % (host_id, pool))
                if 'stop' in request.POST:
                    try:
                        stg.destroy()
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                    return HttpResponseRedirect('/storage/%s/%s' % (host_id, pool))
                if 'delete' in request.POST:
                    try:
                        stg.undefine()
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                    return HttpResponseRedirect('/storage/%s/' % host_id)
                if 'addimg' in request.POST:
                    name = request.POST.get('name', '')
                    size = request.POST.get('size', '')
                    img_name = name + '.img'

                    import re
                    errors = []
                    name_have_simbol = re.search('[^a-zA-Z0-9\_\-\.]+', name)
                    if img_name in stg.listVolumes():
                        msg = 'Volume name already use'
                        errors.append(msg)
                    if not name:
                        msg = 'No name has been entered'
                        errors.append(msg)
                    elif len(name) > 20:
                        msg = 'The host name must not exceed 20'
                        errors.append(msg)
                    else:
                        if name_have_simbol:
                            msg = 'The host name must not contain any characters'
                            errors.append(msg)
                    if not errors:
                        add_vol(name, size)
                        return HttpResponseRedirect('/storage/%s/%s' % (host_id, pool))
                if 'delimg' in request.POST:
                    img = request.POST.get('img', '')
                    try:
                        vol = stg.storageVolLookupByName(img)
                        vol.delete(0)
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                    return HttpResponseRedirect('/storage/%s/%s' % (host_id, pool))
                if 'clone' in request.POST:
                    img = request.POST.get('img', '')
                    clone_name = request.POST.get('new_img', '')
                    full_img_name = clone_name + '.img'
                    import re
                    errors = []
                    name_have_simbol = re.search('[^a-zA-Z0-9\_\-\.]+', clone_name)
                    if full_img_name in stg.listVolumes():
                        msg = _('Volume name already use')
                        errors.append(msg)
                    if not clone_name:
                        msg = _('No name has been entered')
                        errors.append(msg)
                    elif len(clone_name) > 20:
                        msg = _('The host name must not exceed 20 characters')
                        errors.append(msg)
                    else:
                        if name_have_simbol:
                            msg = _('The host name must not contain any characters')
                            errors.append(msg)
                    if not errors:
                        clone_vol(img, clone_name)
                        return HttpResponseRedirect('/storage/%s/%s' % (host_id, pool))

        conn.close()

    return render_to_response('storage.html', locals(), context_instance=RequestContext(request))


def network(request, host_id, pool):
    """

    Networks block

    """

    from libvirt import libvirtError

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    def all_networks():
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

    def add_new_pool(name, forward, gw, netmask, dhcp):
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
        conn.networkDefineXML(xml)

    def net_info():
        info = []
        info.append(net.isActive())
        info.append(net.bridgeName())
        return info

    def ipv4_net():
        import virtinst.util as util
        from virtmgr.IPy import IP

        ipv4 = []
        xml_net = net.XMLDesc(0)

        fw = util.get_xml_path(xml_net, "/network/forward/@mode")
        forwardDev = util.get_xml_path(xml_net, "/network/forward/@dev")

        if fw and forwardDev:
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

    host = Host.objects.get(id=host_id)
    conn = libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:

        networks = all_networks()

        if pool is None:
            if len(networks) == 0:
                return HttpResponseRedirect('/network/%s/add/' % (host_id))
            else:
                return HttpResponseRedirect('/network/%s/%s/' % (host_id, networks.keys()[0]))

        if pool == 'add':
            if request.method == 'POST':
                if 'addpool' in request.POST:
                    dhcp = []
                    pool_name = request.POST.get('name', '')
                    net_addr = request.POST.get('net_addr', '')
                    forward = request.POST.get('forward', '')
                    dhcp.append(request.POST.get('dhcp', ''))

                    import re
                    errors = []
                    name_have_simbol = re.search('[^a-zA-Z0-9\_\-]+', pool_name)
                    ip_have_simbol = re.search('[^0-9\.\/]+', net_addr)

                    if not pool_name:
                        msg = 'No pool name has been entered'
                        errors.append(msg)
                    elif len(pool_name) > 12:
                        msg = 'The host name must not exceed 20 characters'
                        errors.append(msg)
                    else:
                        if name_have_simbol:
                            msg = 'The pool name must not contain any characters'
                            errors.append(msg)
                    if not net_addr:
                        msg = 'No subnet has been entered'
                        errors.append(msg)
                    elif ip_have_simbol:
                        msg = 'The pool name must not contain any characters'
                        errors.append(msg)
                    if pool_name in networks.keys():
                        msg = 'Pool name already use'
                        errors.append(msg)
                    try:
                        from virtmgr.IPy import IP

                        netmask = IP(net_addr).strNetmask()
                        ipaddr = IP(net_addr)
                        gateway = ipaddr[0].strNormal()[-1]
                        if gateway == '0':
                            gw = ipaddr[1].strNormal()
                            dhcp_start = ipaddr[2].strNormal()
                            end = ipaddr.len() - 2
                            dhcp_end = ipaddr[end].strNormal()
                        else:
                            gw = ipaddr[0].strNormal()
                            dhcp_start = ipaddr[1].strNormal()
                            end = ipaddr.len() - 2
                            dhcp_end = ipaddr[end].strNormal()
                        dhcp.append(dhcp_start)
                        dhcp.append(dhcp_end)
                    except:
                        msg = 'Input subnet pool error'
                        errors.append(msg)
                    if not errors:
                        try:
                            add_new_pool(pool_name, forward, gw, netmask, dhcp)
                            net = conn.networkLookupByName(pool_name)
                            net.create()
                            net.setAutostart(1)
                            msg = 'Create network pool: %s' % pool_name
                            return HttpResponseRedirect('/network/%s/%s/' % (host_id, pool_name))
                        except libvirtError as error_msg:
                            errors.append(error_msg.message)
        else:
            all_vm = get_all_vm(conn)
            net = conn.networkLookupByName(pool)

            info = net_info()

            if info[0] == True:
                ipv4_net = ipv4_net()

            if request.method == 'POST':
                if 'start' in request.POST:
                    try:
                        net.create()
                        return HttpResponseRedirect('/network/%s/%s' % (host_id, pool))
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                if 'stop' in request.POST:
                    try:
                        net.destroy()
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                    return HttpResponseRedirect('/network/%s/%s' % (host_id, pool))
                if 'delete' in request.POST:
                    try:
                        net.undefine()
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                    return HttpResponseRedirect('/network/%s/' % host_id)

        conn.close()

    return render_to_response('network.html', locals(), context_instance=RequestContext(request))


def vm(request, host_id, vname):
    """

    VM's block

    """

    from libvirt import libvirtError

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    def find_all_iso(storages):
        import re
        iso = []
        for storage in storages:
            stg = conn.storagePoolLookupByName(storage)
            stg.refresh(0)
            for img in stg.listVolumes():
                if re.findall(".iso", img):
                    img = re.sub('.iso', '', img)
                    iso.append(img)
        return iso

    def add_iso(image, storages):
        image = image + '.iso'
        for storage in storages:
            stg = conn.storagePoolLookupByName(storage)
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
                        conn.defineXML(xmldom)
                    if dom.info()[0] == 5:
                        vol = stg.storageVolLookupByName(image)
                        xml = dom.XMLDesc(0)
                        newxml = "<disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>\n      <source file='%s'/>" % vol.path()
                        xmldom = xml.replace("<disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>", newxml)
                        conn.defineXML(xmldom)

    def remove_iso(image, storages):
        image = image + '.iso'
        if dom.info()[0] == 1:
            xml = """<disk type='file' device='cdrom'>
                         <driver name="qemu" type='raw'/>
                         <target dev='hdc' bus='ide'/>
                         <readonly/>
                      </disk>"""
            dom.attachDevice(xml)
            xmldom = dom.XMLDesc(0)
            conn.defineXML(xmldom)
        if dom.info()[0] == 5:
            for storage in storages:
                stg = conn.storagePoolLookupByName(storage)
                for img in stg.listVolumes():
                    if image == img:
                        vol = stg.storageVolLookupByName(image)
                        xml = dom.XMLDesc(0)
                        xmldom = xml.replace("<source file='%s'/>\n" % vol.path(), '')
                        conn.defineXML(xmldom)

    def find_iso(image, storages):
        image = image + '.iso'
        for storage in storages:
            stg = conn.storagePoolLookupByName(storage)
            stg.refresh(0)
            try:
                vol = stg.storageVolLookupByName(image)
            except:
                vol = None
        return vol.name()

    def dom_media():
        import virtinst.util as util
        import re

        xml = dom.XMLDesc(0)
        media = util.get_xml_path(xml, "/domain/devices/disk[2]/source/@file")
        if media:
            vol = conn.storageVolLookupByPath(media)
            img = re.sub('.iso', '', vol.name())
            return img
        else:
            return None

    def dom_uptime():
        if dom.info()[0] == 1:
            nanosec = dom.info()[4]
            minutes = nanosec * 1.66666666666667E-11
            minutes = round(minutes, 0)
            return minutes
        else:
            return 'None'

    def get_dom_info():
        import virtinst.util as util

        info = []

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

    def get_dom_hdd(storages):
        import virtinst.util as util

        xml = dom.XMLDesc(0)
        hdd = util.get_xml_path(xml, "/domain/devices/disk[1]/source/@file")

        # If xml create custom
        if not hdd:
            hdd = util.get_xml_path(xml, "/domain/devices/disk[1]/source/@dev")
        try:
            img = conn.storageVolLookupByPath(hdd)
            img_vol = img.name()

            for storage in storages:
                stg = conn.storagePoolLookupByName(storage)
                stg.refresh(0)
                for img in stg.listVolumes():
                    if img == img_vol:
                        vol = img
                        vol_stg = storage

            return vol, vol_stg
        except:
            return hdd, 'Not in the pool'

    def vm_cpu_usage():
        import time
        try:
            nbcore = conn.getInfo()[2]
            cpu_use_ago = dom.info()[4]
            time.sleep(1)
            cpu_use_now = dom.info()[4]
            diff_usage = cpu_use_now - cpu_use_ago
            cpu_usage = 100 * diff_usage / (1 * nbcore * 10**9L)
            return cpu_usage
        except libvirtError as e:
            return e.message

    def get_mem_usage():
        try:
            allmem = conn.getInfo()[1] * 1048576
            dom_mem = dom.info()[1] * 1024
            percent = (dom_mem * 100) / allmem
            return allmem, percent
        except libvirtError as e:
            return e.message

    def set_vnc_passwd():
        from string import letters, digits
        from random import choice

        passwd = ''.join([choice(letters + digits) for i in range(12)])

        try:
            xml = dom.XMLDesc(0)
            newxml = "<graphics type='vnc' port='-1' autoport='yes' keymap='en-us' passwd='%s'/>" % passwd
            xmldom = xml.replace("<graphics type='vnc' port='-1' autoport='yes' keymap='en-us'/>", newxml)
            conn.defineXML(xmldom)
            vnc_pass = Vm(host_id=host_id, vname=vname, vnc_passwd=passwd)
            vnc_pass.save()
        except libvirtError as e:
            return e.message

    host = Host.objects.get(id=host_id)
    conn = libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        all_vm = get_all_vm(conn)
        dom = conn.lookupByName(vname)

        try:
            vm = Vm.objects.get(vname=vname)
        except:
            vm = None

        dom_info = get_dom_info()
        dom_uptime = dom_uptime()
        cpu_usage = vm_cpu_usage()
        mem_usage = get_mem_usage()

        storages = get_all_storages(conn)
        hdd_image = get_dom_hdd(storages)
        iso_images = find_all_iso(storages)
        media = dom_media()

        errors = []

        if request.method == 'POST':
            if 'start' in request.POST:
                try:
                    dom.create()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'power' in request.POST:
                if 'shutdown' == request.POST.get('power', ''):
                    try:
                        dom.shutdown()
                        return HttpResponseRedirect(request.get_full_path())
                    except libvirtError as msg_error:
                        errors.append(msg_error.message)
                if 'destroy' == request.POST.get('power', ''):
                    try:
                        dom.destroy()
                        return HttpResponseRedirect(request.get_full_path())
                    except libvirtError as msg_error:
                        errors.append(msg_error.message)
            if 'suspend' in request.POST:
                try:
                    dom.suspend()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'resume' in request.POST:
                try:
                    dom.resume()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'delete' in request.POST:
                try:
                    xml = dom.XMLDesc(0)
                    if dom.info()[0] == 1:
                        dom.destroy()
                    dom.undefine()
                    if request.POST.get('image', ''):
                        import virtinst.util as util

                        img = util.get_xml_path(xml, "/domain/devices/disk[1]/source/@file")
                        vol = conn.storageVolLookupByPath(img)
                        vol.delete(0)
                    try:
                        vm = Vm.objects.get(host=host_id, vname=vname)
                        vm.delete()
                    except:
                        pass
                    return HttpResponseRedirect('/overview/%s/' % host_id)
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'snapshot' in request.POST:
                try:
                    import time
                    xml = """<domainsnapshot>\n
                                 <name>%d</name>\n
                                 <state>shutoff</state>\n
                                 <creationTime>%d</creationTime>\n""" % (time.time(), time.time())
                    xml += dom.XMLDesc(0)
                    xml += """<active>0</active>\n
                              </domainsnapshot>"""
                    dom.snapshotCreateXML(xml, 0)
                    messages = []
                    messages.append('Create snapshot for instance successful')
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'remove_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                remove_iso(image, storages)
                return HttpResponseRedirect(request.get_full_path())
            if 'add_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                add_iso(image, storages)
                return HttpResponseRedirect(request.get_full_path())
            if 'vnc_pass' in request.POST:
                set_vnc_passwd()
                return HttpResponseRedirect(request.get_full_path())

        conn.close()

    return render_to_response('vm.html', locals(), context_instance=RequestContext(request))


def vnc(request, host_id, vname):
    """

    VNC vm's block

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    def vnc_port():
        import virtinst.util as util
        dom = conn.lookupByName(vname)
        xml = dom.XMLDesc(0)
        port = util.get_xml_path(xml, "/domain/devices/graphics/@port")
        return port

    host = Host.objects.get(id=host_id)
    conn = libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        vnc_port = vnc_port()
        try:
            vm = Vm.objects.get(host=host_id, vname=vname)

            import os
            # Kill only owner proccess
            os.system("kill -9 $(ps aux | grep websockify | grep -v grep | awk '{ print $2 }')")
            os.system('websockify 6080 %s:%s -D' % (host.ipaddr, vnc_port))
        except:
            vm = None

        conn.close()

    return render_to_response('vnc.html', locals(), context_instance=RequestContext(request))


def snapshot(request, host_id):
    """

    Snapshot block

    """

    from libvirt import libvirtError

    def get_vm_snapshots():
        try:
            vname = {}
            for id in conn.listDomainsID():
                id = int(id)
                dom = conn.lookupByID(id)
                if dom.snapshotNum(0) != 0:
                    vname[dom.name()] = dom.info()[0]
            for id in conn.listDefinedDomains():
                dom = conn.lookupByName(id)
                if dom.snapshotNum(0) != 0:
                    vname[dom.name()] = dom.info()[0]
            return vname
        except libvirtError as e:
            return e.message

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        all_vm = get_all_vm(conn)
        all_vm_snap = get_vm_snapshots()

        conn.close()

    if all_vm_snap:
        return HttpResponseRedirect('/snapshot/%s/%s/' % (host_id, all_vm_snap.keys()[0]))

    return render_to_response('snapshot.html', locals(), context_instance=RequestContext(request))


def dom_snapshot(request, host_id, vname):
    """

    Snapshot block

    """

    from libvirt import libvirtError

    def get_vm_snapshots():
        try:
            vname = {}
            for id in conn.listDomainsID():
                id = int(id)
                dom = conn.lookupByID(id)
                if dom.snapshotNum(0) != 0:
                    vname[dom.name()] = dom.info()[0]
            for id in conn.listDefinedDomains():
                dom = conn.lookupByName(id)
                if dom.snapshotNum(0) != 0:
                    vname[dom.name()] = dom.info()[0]
            return vname
        except libvirtError as e:
            return e.message

    def get_snapshots():
        from datetime import datetime
        try:
            snapshots = {}
            all_snapshot = dom.snapshotListNames(0)
            for snapshot in all_snapshot:
                snapshots[snapshot] = (datetime.fromtimestamp(int(snapshot)), dom.info()[0])
            return snapshots
        except libvirtError as e:
            return e.message

    def del_snapshot(name_snap):
        try:
            snap = dom.snapshotLookupByName(name_snap,0)
            snap.delete(0)
        except libvirtError as e:
            return e.message

    def revert_snapshot(name_snap):
        try:
            snap = dom.snapshotLookupByName(name_snap,0)
            dom.revertToSnapshot(snap,0)
        except libvirtError as e:
            return e.message

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        dom = conn.lookupByName(vname)
        all_vm = get_all_vm(conn)
        all_vm_snap = get_vm_snapshots()
        vm_snapshot = get_snapshots()

        if request.method == 'POST':
            if 'delete' in request.POST:
                name = request.POST.get('name', '')
                del_snapshot(name)
                return HttpResponseRedirect('/snapshot/%s/%s/' % (host_id, vname))
            if 'revert' in request.POST:
                name = request.POST.get('name', '')
                revert_snapshot(name)
                message = _('Successful revert snapshot: ')
                message = message + name

    return render_to_response('snapshot.html', locals(), context_instance=RequestContext(request))


def page_setup(request):
    return render_to_response('setup.html', locals(), context_instance=RequestContext(request))
