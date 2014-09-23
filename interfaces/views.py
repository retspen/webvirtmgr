from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext

from servers.models import Compute
from interfaces.forms import AddInterface

from vrtManager.interface import wvmInterface, wvmInterfaces

from libvirt import libvirtError


def interfaces(request, host_id):
    """
    Interfaces block

    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')

    errors = []
    ifaces_all = []
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmInterfaces(compute.hostname,
                             compute.login,
                             compute.password,
                             compute.type)
        ifaces = conn.get_ifaces()
        try:
            netdevs = conn.get_net_device()
        except:
            netdevs = ['eth0', 'eth1']

        for iface in ifaces:
            ifaces_all.append(conn.get_iface_info(iface))

        if request.method == 'POST':
            if 'create' in request.POST:
                form = AddInterface(request.POST)
                if form.is_valid():
                    data = form.cleaned_data
                    conn.create_iface(data['name'], data['itype'], data['start_mode'], data['netdev'],
                                      data['ipv4_type'], data['ipv4_addr'], data['ipv4_gw'],
                                      data['ipv6_type'], data['ipv6_addr'], data['ipv6_gw'],
                                      data['stp'], data['delay'])
                    return HttpResponseRedirect(request.get_full_path())
        conn.close()
    except libvirtError as err:
        errors.append(err)

    return render_to_response('interfaces.html', locals(), context_instance=RequestContext(request))


def interface(request, host_id, iface):
    """
    Interface block

    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')

    errors = []
    ifaces_all = []
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmInterface(compute.hostname,
                            compute.login,
                            compute.password,
                            compute.type,
                            iface)
        start_mode = conn.get_start_mode()
        state = conn.is_active()
        mac = conn.get_mac()
        itype = conn.get_type()
        ipv4 = conn.get_ipv4()
        ipv4_type = conn.get_ipv4_type()
        ipv6 = conn.get_ipv6()
        ipv6_type = conn.get_ipv6_type()
        bridge = conn.get_bridge()

        if request.method == 'POST':
            if 'stop' in request.POST:
                conn.stop_iface()
                return HttpResponseRedirect(request.get_full_path())
            if 'start' in request.POST:
                conn.start_iface()
                return HttpResponseRedirect(request.get_full_path())
            if 'delete' in request.POST:
                conn.delete_iface()
                return HttpResponseRedirect('/interfaces/%s' % host_id)
        conn.close()
    except libvirtError as err:
        errors.append(err)

    return render_to_response('interface.html', locals(), context_instance=RequestContext(request))
