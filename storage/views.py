# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from vds.models import Host
import libvirt_func
from libvirt import libvirtError
import re


def storage(request, host_id, pool):
    """

    Storage pool block

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = libvirt_func.libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/manage/')
    else:

        storages = libvirt_func.storages_get_node(conn)

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

                    name_have_symbol = re.search('[^a-zA-Z0-9\_\-]+', pool_name)
                    path_have_symbol = re.search('[^a-zA-Z0-9\/]+', pool_source)

                    errors = []

                    if name_have_symbol or path_have_symbol:
                        msg = _("The host name must not contain any special characters")
                        errors.append(msg)
                    if not pool_name:
                        msg = _("No pool name has been entered")
                        errors.append(msg)
                    elif len(pool_name) > 12:
                        msg = _("The host name must not exceed 12")
                        errors.append(msg)
                    if pool_type == 'logical':
                        if not pool_source:
                            msg = _("No device has been entered")
                            errors.append(msg)
                    if pool_type == 'dir':
                        if not pool_target:
                            msg = _("No path has been entered")
                            errors.append(msg)
                    if pool_name in storages.keys():
                        msg = _("Pool name already use")
                        errors.append(msg)
                    if not errors:
                        try:
                            libvirt_func.new_storage_pool(conn, pool_type, pool_name, pool_source, pool_target)
                            stg = conn.storagePoolLookupByName(pool_name)
                            if pool_type == 'logical':
                                stg.build(0)
                            stg.create(0)
                            stg.setAutostart(1)
                            return HttpResponseRedirect('/storage/%s/%s/' % (host_id, pool_name))
                        except libvirtError as error_msg:
                            errors.append(error_msg.message)
        else:
            all_vm = libvirt_func.vds_get_node(conn)
            form_hdd_size = [10, 20, 40, 80, 160, 320, 640]
            stg = conn.storagePoolLookupByName(pool)

            info = libvirt_func.storage_get_info(stg)

            # refresh storage if acitve
            if info[5] == True:
                stg.refresh(0)
                volumes_info = libvirt_func.volumes_get_info(stg)

            if request.method == 'POST':
                errors = []

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
                    name_have_symbol = re.search('[^a-zA-Z0-9\_\-\.]+', name)
                    if img_name in stg.listVolumes():
                        msg = _("Volume name already use")
                        errors.append(msg)
                    if not name:
                        msg = _("No name has been entered")
                        errors.append(msg)
                    elif len(name) > 20:
                        msg = _("The host name must not exceed 20")
                        errors.append(msg)
                    else:
                        if name_have_symbol:
                            msg = _("The host name must not contain any special characters")
                            errors.append(msg)
                    if not errors:
                        libvirt_func.new_volume(stg, name, size)
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
                    name_have_symbol = re.search('[^a-zA-Z0-9\_\-\.]+', clone_name)
                    if full_img_name in stg.listVolumes():
                        msg = _("Volume name already use")
                        errors.append(msg)
                    if not clone_name:
                        msg = _("No name has been entered")
                        errors.append(msg)
                    elif len(clone_name) > 20:
                        msg = _("The host name must not exceed 20 characters")
                        errors.append(msg)
                    else:
                        if name_have_symbol:
                            msg = _("The host name must not contain any special characters")
                            errors.append(msg)
                    if not errors:
                        libvirt_func.clone_volume(stg, img, clone_name)
                        return HttpResponseRedirect('/storage/%s/%s' % (host_id, pool))

        conn.close()

    return render_to_response('storage.html', locals(), context_instance=RequestContext(request))
