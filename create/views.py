from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from servers.models import Compute
from create.models import Flavor
from instance.models import Instance

from libvirt import libvirtError

from vrtManager.create import wvmCreate
from vrtManager import util
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
        get_images = conn.get_storages_images()
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
            volumes = {}
            form = NewVMForm(request.POST)
            print form.errors
            if form.is_valid():
                data = form.cleaned_data
                if instances:
                    if data['name'] in instances:
                        msg = _("A virtual machine with this name already exists")
                        errors.append(msg)
                if not errors:
                    if not data['hdd_size']:
                        if not data['images']:
                            msg = _("First you need to create or select an image")
                            errors.append(msg)
                        else:
                            for vol in data['images'].split(','):
                                try:
                                    path = conn.get_volume_path(vol)
                                    volumes[path] = conn.get_volume_type(path)
                                except libvirtError as msg_error:
                                    errors.append(msg_error.message)
                    else:
                        try:
                            path = conn.create_volume(data['storage'], data['name'], data['hdd_size'])
                            volumes[path] = conn.get_volume_type(path)
                        except libvirtError as msg_error:
                            errors.append(msg_error.message)
                    if not errors:
                        uuid = util.randomUUID()
                        try:
                            conn.create_instance(data['name'], data['memory'], data['vcpu'], data['host_model'],
                                                 uuid, volumes, data['networks'], data['virtio'])
                            create_instance = Instance(compute_id=host_id, name=data['name'], uuid=uuid)
                            create_instance.save()
                            return HttpResponseRedirect('/instance/%s/%s/' % (host_id, data['name']))
                        except libvirtError as msg_error:
                            if data['hdd_size']:
                                conn.delete_volume(volumes[0])
                            errors.append(msg_error.message)
    conn.close()

    return render_to_response('create.html', locals(), context_instance=RequestContext(request))
