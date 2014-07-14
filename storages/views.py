from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from servers.models import Compute
from storages.forms import AddStgPool, AddImage, CloneImage

from vrtManager.storage import wvmStorage, wvmStorages

from libvirt import libvirtError


def storages(request, host_id):
    """
    Storage pool block
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmStorages(compute.hostname,
                           compute.login,
                           compute.password,
                           compute.type)
        storages = conn.get_storages_info()
        secrets = conn.get_secrets()

        if request.method == 'POST':
            if 'create' in request.POST:
                form = AddStgPool(request.POST)
                if form.is_valid():
                    data = form.cleaned_data
                    if data['name'] in storages:
                        msg = _("Pool name already use")
                        errors.append(msg)
                    if data['stg_type'] == 'rbd':
                        if not data['secret']:
                            msg = _("You need create secret for pool")
                            errors.append(msg)
                        if not data['ceph_pool'] and not data['ceph_host'] and not data['ceph_user']:
                            msg = _("You need input all fields for creating ceph pool")
                            errors.append(msg)
                    if not errors:
                        if data['stg_type'] == 'rbd':
                            conn.create_storage_ceph(data['stg_type'], data['name'],
                                                     data['ceph_pool'], data['ceph_host'],
                                                     data['ceph_user'], data['secret'])
                        else:
                            conn.create_storage(data['stg_type'], data['name'], data['source'], data['target'])
                        return HttpResponseRedirect('/storage/%s/%s/' % (host_id, data['name']))
        conn.close()
    except libvirtError as err:
        errors.append(err)

    return render_to_response('storages.html', locals(), context_instance=RequestContext(request))


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
    compute = Compute.objects.get(id=host_id)
    meta_prealloc = False

    try:
        conn = wvmStorage(compute.hostname,
                          compute.login,
                          compute.password,
                          compute.type,
                          pool)

        storages = conn.get_storages()
        state = conn.is_active()
        size, free = conn.get_size()
        used = (size - free)
        if state:
            percent = (used * 100) / size
        else:
            percent = 0
        status = conn.get_status()
        path = conn.get_target_path()
        type = conn.get_type()
        autostart = conn.get_autostart()

        if state:
            conn.refresh()
            volumes = conn.update_volumes()
        else:
            volumes = None
    except libvirtError as err:
        errors.append(err)

    if request.method == 'POST':
        if 'start' in request.POST:
            try:
                conn.start()
                return HttpResponseRedirect(request.get_full_path())
            except libvirtError as error_msg:
                errors.append(error_msg.message)
        if 'stop' in request.POST:
            try:
                conn.stop()
                return HttpResponseRedirect(request.get_full_path())
            except libvirtError as error_msg:
                errors.append(error_msg.message)
        if 'delete' in request.POST:
            try:
                conn.delete()
                return HttpResponseRedirect('/storages/%s/' % host_id)
            except libvirtError as error_msg:
                errors.append(error_msg.message)
        if 'set_autostart' in request.POST:
            try:
                conn.set_autostart(1)
                return HttpResponseRedirect(request.get_full_path())
            except libvirtError as error_msg:
                errors.append(error_msg.message)
        if 'unset_autostart' in request.POST:
            try:
                conn.set_autostart(0)
                return HttpResponseRedirect(request.get_full_path())
            except libvirtError as error_msg:
                errors.append(error_msg.message)
        if 'add_volume' in request.POST:
            form = AddImage(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                if data['meta_prealloc'] and data['format'] == 'qcow2':
                    meta_prealloc = True
                try:
                    conn.create_volume(data['name'], data['size'], data['format'], meta_prealloc)
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as err:
                    errors.append(err)
        if 'del_volume' in request.POST:
            volname = request.POST.get('volname', '')
            try:
                vol = conn.get_volume(volname)
                vol.delete(0)
                return HttpResponseRedirect(request.get_full_path())
            except libvirtError as error_msg:
                errors.append(error_msg.message)
        if 'iso_upload' in request.POST:
            if str(request.FILES['file']) in conn.update_volumes():
                msg = _("ISO image already exist")
                errors.append(msg)
            else:
                handle_uploaded_file(path, request.FILES['file'])
                return HttpResponseRedirect(request.get_full_path())
        if 'cln_volume' in request.POST:
            form = CloneImage(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                img_name = data['name'] + '.img'
                meta_prealloc = 0
                if img_name in conn.update_volumes():
                    msg = _("Name of volume name already use")
                    errors.append(msg)
                if not errors:
                    if data['convert']:
                        format = data['format']
                        if data['meta_prealloc'] and data['format'] == 'qcow2':
                            meta_prealloc = True
                    else:
                        format = None
                    try:
                        conn.clone_volume(data['image'], data['name'], format, meta_prealloc)
                        return HttpResponseRedirect(request.get_full_path())
                    except libvirtError as err:
                        errors.append(err)
    conn.close()

    return render_to_response('storage.html', locals(), context_instance=RequestContext(request))
