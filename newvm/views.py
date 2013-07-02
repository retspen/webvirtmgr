# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from vds.models import Host, Flavor, Vm
from webvirtmgr.server import ConnServer
from libvirt import libvirtError
import re
from string import letters, digits
from random import choice


def newvm(request, host_id):
    """

    Page add new VM.

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None

    if not conn:
        errors.append(e.message)
    else:
        try:
            flavors = Flavor.objects.filter().order_by('id')
        except:
            flavors = 'error'

        all_vm = conn.vds_get_node()
        all_networks = conn.networks_get_node()
        all_storages = conn.storages_get_node()
        all_img = conn.images_get_storages(all_storages)

        if not all_networks:
            msg = _("You haven't defined any virtual networks")
            errors.append(msg)
        if not all_storages:
            msg = _("You haven't defined have any storage pools")
            errors.append(msg)

        hdd_digits_size = [a for a in range(1, 601)]

        if request.method == 'POST':
            if 'add_flavor' in request.POST:
                name = request.POST.get('name', '')
                vcpu = request.POST.get('vcpu', '')
                ram = request.POST.get('ram', '')
                hdd = request.POST.get('hdd', '')

                for flavor in flavors:
                    if name == flavor.name:
                        msg = _("Name already use")
                        errors.append(msg)
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
                virtio = request.POST.get('virtio', '')

                symbol = re.search('[^a-zA-Z0-9\_\-\.]+', vname)

                if vname in all_vm:
                    msg = _("A virtual machine with this name already exists")
                    errors.append(msg)
                if len(vname) > 12:
                    msg = _("The name of the virtual machine must not exceed 12 characters")
                    errors.append(msg)
                if symbol:
                    msg = _("The name of the virtual machine must not contain any special characters")
                    errors.append(msg)
                if not vname:
                    msg = _("Enter the name of the virtual machine")
                    errors.append(msg)

                if not errors:
                    if not hdd_size:
                        if not img:
                            msg = _("First you need to create an image")
                            errors.append(msg)
                        else:
                            image = conn.image_get_path(img, all_storages)
                    else:
                        try:
                            conn.new_volume(storage, vname, hdd_size)
                        except libvirtError as msg_error:
                            errors.append(msg_error.message)
                    if not errors:
                        if not img:
                            vl = conn.storageVol(vname, storage)
                        else:
                            vl = conn.storageVolPath(image)

                        image = vl.path()

                        try:
                            conn.add_vm(vname, ram, vcpu, image, net, virtio, all_storages)
                            return HttpResponseRedirect('/vds/%s/%s/' % (host_id, vname))
                        except libvirtError as msg_error:
                            if hdd_size:
                                vl.delete(0)
                            errors.append(msg_error.message)
        conn.close()

    return render_to_response('newvm.html', locals(), context_instance=RequestContext(request))
