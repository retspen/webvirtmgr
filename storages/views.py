from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from servers.models import Compute
from storages.forms import AddStgPool, AddImage, CloneImage

from vrtManager.storage import wvmConnect
from vrtManager.storage import wvmStorage

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
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmConnect(compute.hostname, compute.login, compute.password, compute.type)
        storage_pools = conn.get_storages()

        if pool is None:
            if len(storage_pools) > 0:
                return HttpResponseRedirect('/storages/%s/%s/' % (host_id, storage_pools[0]))
        else:
            stgobj = conn.stg_pool(pool)
            stg = wvmStorage(conn, stgobj)
            size, free, usage = stg.get_size()
            percent = (free * 100) / size
            # state = stg.is_active()
            print dir(stgobj)
            # size, free, usage, percent, state, s_type, path = conn.storage_get_info(pool)
            # if state:
            #     stg.refresh(0)
            #     volumes_info = conn.volumes_get_info(pool)
            # else:
            #     volumes_info = None

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
                            conn.new_storage_pool(data['stg_type'], data['name'], data['source'], data['target'])
                            return HttpResponseRedirect('/storage/%s/%s/' % (host_id, data['name']))
                        except libvirtError as error_msg:
                            errors.append(error_msg.message)
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
                        conn.new_volume(pool, data['name'], data['size'], data['format'])
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
                        if 'convert' in data:
                            format = data['format']
                        else:
                            format = None
                        try:
                            conn.clone_volume(pool, data['image'], data['name'], format)
                            return HttpResponseRedirect(request.get_full_path())
                        except libvirtError as error_msg:
                            errors.append(error_msg.message)
        conn.close()
    except libvirtError as err:
        errors.append(e.message)

    return render_to_response('storages.html', locals(),  context_instance=RequestContext(request))
