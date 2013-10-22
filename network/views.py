from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from instance.models import Host
from network.forms import AddNetPool
from dashboard.views import sort_host
from webvirtmgr.server import ConnServer, network_size
from libvirt import libvirtError


def network(request, host_id, pool):
    """

    Networks block

    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    form = info = ipv4_net = None
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

        all_vm = sort_host(conn.vds_get_node())

        if not pool == 'add':
            info = conn.network_get_info(pool)
            if info[0]:
                ipv4_net = conn.network_get_subnet(pool)
            else:
                ipv4_net = None

        if request.method == 'POST':
            if 'pool_add' in request.POST:
                form = AddNetPool(request.POST)
                if form.is_valid():
                    data = form.cleaned_data
                    if data['name'] in networks.keys():
                        msg = _("Pool name already in use")
                        errors.append(msg)
                    if data['forward'] == 'bridge' and data['bridge_name'] == '':
                        errors.append('Please enter bridge name')
                    try:
                        gateway, netmask, dhcp = network_size(data['subnet'], data['dhcp'])
                    except:
                        msg = _("Input subnet pool error")
                        errors.append(msg)
                    if not errors:
                        try:
                            conn.new_network_pool(data['name'], data['forward'], gateway, netmask, dhcp, data['bridge_name'])
                            return HttpResponseRedirect('/network/%s/%s/' % (host_id, data['name']))
                        except libvirtError as e:
                            errors.append(e.message)
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

    return render_to_response('network.html', {'host_id': host_id,
                                               'errors': errors,
                                               'form': form,
                                               'networks': networks,
                                               'pool': pool,
                                               'all_vm': all_vm,
                                               'info': info,
                                               'ipv4_net': ipv4_net
                                               },
                              context_instance=RequestContext(request))
