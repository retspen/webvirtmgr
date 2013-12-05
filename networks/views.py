from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from servers.models import Compute
from networks.forms import AddNetPool

from vrtManager.network import wvmNetwork

from libvirt import libvirtError


def networks(request, host_id):
    return render_to_response('networks.html', locals(), context_instance=RequestContext(request))

def network(request, host_id, pool):
    """
    Networks block
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmNetwork(compute.hostname, compute.login, compute.password, compute.type, pool)
        networks = conn.get_networks()
        state = conn.is_active()
        device = conn.get_bridge_device()
        autostart = conn.get_autostart()
        ipv4_forward = conn.get_ipv4_forward()
        ipv4_dhcp_range = conn.get_ipv4_dhcp_range()
        ipv4_network = conn.get_ipv4_network()

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
                    return HttpResponseRedirect('/networks/%s/' % host_id)
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
        conn.close()
    except libvirtError as err:
        errors.append(err.message)

    return render_to_response('network.html', locals(), context_instance=RequestContext(request))
