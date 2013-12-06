from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from servers.models import Compute
from create.models import Flavor

from libvirt import libvirtError

from vrtManager.create import wvmCreate
from create.forms import FlavorAddForm, NewVMForm


def create(request, host_id):
    """
    Create new instance.
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    compute = Compute.objects.get(id=host_id)
    flavors = Flavor.objects.filter().order_by('id')

    try:
        conn = wvmCreate(compute.hostname,
                         compute.login,
                         compute.password,
                         compute.type)

        storages = conn.get_storages()
        networks = conn.get_networks()
        instances = conn.get_instances()
        get_images = conn.get_storages_images(storages)
    except libvirtError as err:
        errors.append(err.message)

    if not storages:
        msg = _("You haven't defined have any storage pools")
        errors.append(msg)
    if not networks:
        msg = _("You haven't defined have any network pools")
        errors.append(msg)

    if request.method == 'POST':
        if 'create_flavor' in request.POST:
            form = FlavorAddForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                create_flavor = Flavor(label=data['label'],
                                       vcpu=data['vcpu'],
                                       memory=data['memory'],
                                       disk=data['disk'])
                create_flavor.save()
                return HttpResponseRedirect(request.get_full_path())
        if 'delete_flavor' in request.POST:
            flavor_id = request.POST.get('flavor', '')
            delete_flavor = Flavor.objects.get(id=flavor_id)
            delete_flavor.delete()
            return HttpResponseRedirect(request.get_full_path())
        if 'create' in request.POST:
            form = NewVMForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                if all_vm:
                    if data['name'] in all_vm:
                        msg = _("A virtual machine with this name already exists")
                        errors.append(msg)
                if not errors:
                    if not data['hdd_size']:
                        if not data['images']:
                            msg = _("First you need to create or select an image")
                            errors.append(msg)
                        else:
                            vol_paths = []
                            for vol in data['images'].split(','):
                                vol_paths.append(conn.image_get_path(vol, all_storages))
                    else:
                        try:
                            conn.new_volume(data['storage'], data['name'], data['hdd_size'])
                        except libvirtError as msg_error:
                            errors.append(msg_error.message)
                    if not errors:
                        volumes = []
                        if not data['images']:
                            volumes.append(conn.storageVol(data['name'], data['storage']))
                        else:
                            for vol_path in vol_paths:
                                volumes.append(conn.storageVolPath(vol_path))

                        images = []
                        for vol in volumes:
                            images.append(vol.path())

                        try:
                            conn.add_vm(data['name'], data['ram'], data['vcpu'], data['host_model'], images,
                                        data['networks'], data['virtio'], all_storages, passwd)
                            return HttpResponseRedirect('/instance/%s/%s/' % (host_id, data['name']))
                        except libvirtError as msg_error:
                            if data['hdd_size']:
                                volumes[0].delete(0)
                            errors.append(msg_error.message)
        conn.close()

    return render_to_response('create.html', locals(), context_instance=RequestContext(request))
