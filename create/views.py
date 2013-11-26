from string import letters, digits
from random import choice

from libvirt import libvirtError

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from servers.models import Compute
from create.models import Flavor
from instances.models import Instance

from create.forms import FlavorAddForm, NewVMForm


def create(request, host_id):
    """

    Page add new VM.

    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    form = None
    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None

    if not conn:
        errors.append(e.message)
    else:
        flavors = Flavor.objects.filter().order_by('id')
        all_vm = sort_host(conn.vds_get_node())
        all_networks = conn.networks_get_node()
        all_storages = conn.storages_get_node()
        all_img = conn.images_get_storages(all_storages)

        if not all_storages:
            msg = _("You haven't defined have any storage pools")
            errors.append(msg)
        if not all_networks:
            msg = _("You haven't defined have any network pools")
            errors.append(msg)

        if request.method == 'POST':
            if 'flavor_add' in request.POST:
                form = FlavorAddForm(request.POST)
                if form.is_valid():
                    data = form.cleaned_data
                    new_flavor = Flavor(name=data['name'], vcpu=data['vcpu'],
                                        ram=data['ram'], hdd=data['hdd'])
                    new_flavor.save()
                    return HttpResponseRedirect(request.get_full_path())
            if 'flavor_del' in request.POST:
                flavor_id = request.POST.get('flavor', '')
                del_flavor = Flavor.objects.get(id=flavor_id)
                del_flavor.delete()
                return HttpResponseRedirect(request.get_full_path())
            if 'instance_add' in request.POST:
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
                                passwd = ''.join([choice(letters + digits) for i in range(12)])
                                conn.add_vm(data['name'], data['ram'], data['vcpu'], data['host_model'], images,
                                            data['networks'], data['virtio'], all_storages, passwd)
                                vnc_pass = Instance(host_id=host_id, vname=data['name'], vnc_passwd=passwd)
                                vnc_pass.save()
                                return HttpResponseRedirect('/instance/%s/%s/' % (host_id, data['name']))
                            except libvirtError as msg_error:
                                if data['hdd_size']:
                                    volumes[0].delete(0)
                                errors.append(msg_error.message)
        conn.close()

    return render_to_response('newvm.html', {'host_id': host_id,
                                             'errors': errors,
                                             'form': form,
                                             'flavors': flavors,
                                             'all_vm': all_vm,
                                             'all_img': all_img,
                                             'all_storages': all_storages,
                                             'all_networks': all_networks
                                             },
                              context_instance=RequestContext(request))
