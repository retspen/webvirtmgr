# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from instance.models import Host
from storage.forms import AddStgPool, AddImage, CloneImage
from dashboard.views import SortHosts
from webvirtmgr.server import ConnServer
from libvirt import libvirtError


def storage(request, host_id, pool):
    """

    Storage pool block

    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    def handle_uploaded_file(path, f_name):
        target = path + '/' + str(f_name)
        destination = open(target, 'wb+')
        for chunk in f_name.chunks():
            destination.write(chunk)
        destination.close()

    errors = []
    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None

    if not conn:
        errors.append(e.message)
    else:
        storages = conn.storages_get_node()
        if pool is None:
            if len(storages) == 0:
                return HttpResponseRedirect('/storage/%s/add/' % (host_id))
            else:
                return HttpResponseRedirect('/storage/%s/%s/' % (host_id, storages.keys()[0]))
        if pool == 'add':
            if request.method == 'POST':
                if 'pool_add' in request.POST:
                    form = AddStgPool(request.POST)
                    if form.is_valid():
                        data = form.cleaned_data
                        if data['name'] in storages.keys():
                            msg = _("Pool name already use")
                            errors.append(msg)
                        if not errors:
                            try:
                                conn.new_storage_pool(data['type'], data['name'], data['source'], data['target'])
                                return HttpResponseRedirect('/storage/%s/%s/' % (host_id, data['name']))
                            except libvirtError as error_msg:
                                errors.append(error_msg.message)
        else:
            all_vm = SortHosts(conn.vds_get_node())
            stg = conn.storagePool(pool)
            size, free, usage, percent, state, s_type, path = conn.storage_get_info(pool)

            if state:
                stg.refresh(0)
                volumes_info = conn.volumes_get_info(pool)

            if request.method == 'POST':
                if 'start' in request.POST:
                    try:
                        stg.create(0)
                        return HttpResponseRedirect(request.get_full_path())
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                if 'stop' in request.POST:
                    try:
                        stg.destroy()
                        return HttpResponseRedirect(request.get_full_path())
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                if 'delete' in request.POST:
                    try:
                        stg.undefine()
                        return HttpResponseRedirect('/storage/%s/' % host_id)
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                if 'img_add' in request.POST:
                    form = AddImage(request.POST)
                    if form.is_valid():
                        data = form.cleaned_data
                        img_name = data['name'] + '.img'
                        if img_name in stg.listVolumes():
                            msg = _("Volume name already use")
                            errors.append(msg)
                        if not errors:
                            conn.new_volume(pool, data['name'], data['size'])
                            return HttpResponseRedirect(request.get_full_path())
                if 'img_del' in request.POST:
                    img = request.POST.get('img', '')
                    try:
                        vol = stg.storageVolLookupByName(img)
                        vol.delete(0)
                        return HttpResponseRedirect(request.get_full_path())
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                if 'iso_upload' in request.POST:
                    if str(request.FILES['file']) in stg.listVolumes():
                        msg = _("ISO image already exist")
                        errors.append(msg)
                    else:
                        handle_uploaded_file(path, request.FILES['file'])
                        return HttpResponseRedirect(request.get_full_path())
                if 'img_clone' in request.POST:
                    form = CloneImage(request.POST)
                    if form.is_valid():
                        data = form.cleaned_data
                        img_name = data['name'] + '.img'
                        if img_name in stg.listVolumes():
                            msg = _("Name of volume name already use")
                            errors.append(msg)
                        if not errors:
                            try:
                                conn.clone_volume(pool, data['image'], data['name'])
                                return HttpResponseRedirect(request.get_full_path())
                            except libvirtError as error_msg:
                                errors.append(error_msg.message)
        conn.close()

    return render_to_response('storage.html', locals(), context_instance=RequestContext(request))
