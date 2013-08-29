# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from instance.models import Host
from network.forms import AddNetPool
from dashboard.views import SortHosts
from webvirtmgr.server import ConnServer, network_size
from libvirt import libvirtError


def network(request, host_id, pool):
    """

    Networks block

    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None

    if not conn:
        errors.append(e.message)
    else:
        networks = conn.networks_get_node()

        if pool is None:
            if len(networks) == 0:
                return HttpResponseRedirect('/network/%s/add/' % (host_id))
            else:
                return HttpResponseRedirect('/network/%s/%s/' % (host_id, networks.keys()[0]))

        if pool == 'add':
            if request.method == 'POST':
                if 'pool_add' in request.POST:
                    form = AddNetPool(request.POST)
                    if form.is_valid():
                        errors = []
                        data = form.cleaned_data
                        if data['name'] in networks.keys():
                            msg = _("Pool name already in use")
                            errors.append(msg)
                        try:
                            gateway, netmask, dhcp = network_size(data['subnet'], data['dhcp'])
                        except:
                            msg = _("Input subnet pool error")
                            errors.append(msg)
                        if not errors:
                            try:
                                conn.new_network_pool(data['name'], data['forward'], gateway, netmask, dhcp)
                                return HttpResponseRedirect('/network/%s/%s/' % (host_id, data['name']))
                            except libvirtError as e:
                                errors.append(e.message)
        else:
            all_vm = SortHosts(conn.vds_get_node())
            info = conn.network_get_info(pool)
            if info[0]:
                ipv4_net = conn.network_get_subnet(pool)
            if request.method == 'POST':
                net = conn.networkPool(pool)
                if 'start' in request.POST:
                    try:
                        net.create()
                        return HttpResponseRedirect(request.get_full_path())
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                if 'stop' in request.POST:
                    try:
                        net.destroy()
                        return HttpResponseRedirect(request.get_full_path())
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                if 'delete' in request.POST:
                    try:
                        net.undefine()
                        return HttpResponseRedirect('/network/%s/' % host_id)
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
        conn.close()

    return render_to_response('network.html', locals(), context_instance=RequestContext(request))
