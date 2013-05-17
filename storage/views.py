# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from dashboard.models import Host
from libvirt_func import libvirt_conn


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
                    name_have_symbol = re.search('[^a-zA-Z0-9\_\-]+', pool_name)
                    path_have_symbol = re.search('[^a-zA-Z0-9\/]+', pool_source)

                    if name_have_symbol or path_have_symbol:
                        msg = 'The host name must not contain any special characters'
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
                    name_have_symbol = re.search('[^a-zA-Z0-9\_\-\.]+', name)
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
                        if name_have_symbol:
                            msg = 'The host name must not contain any special characters'
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
                    name_have_symbol = re.search('[^a-zA-Z0-9\_\-\.]+', clone_name)
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
                        if name_have_symbol:
                            msg = _('The host name must not contain any special characters')
                            errors.append(msg)
                    if not errors:
                        clone_vol(img, clone_name)
                        return HttpResponseRedirect('/storage/%s/%s' % (host_id, pool))

        conn.close()

    return render_to_response('storage.html', locals(), context_instance=RequestContext(request))
