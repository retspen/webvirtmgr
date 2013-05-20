# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from vds.models import Host
import libvirt_func


def network(request, host_id, pool):
    """

    Networks block

    """

    from libvirt import libvirtError

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = libvirt_func.libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:

        networks = libvirt_func.networks_get_node(conn)

        if pool is None:
            if len(networks) == 0:
                return HttpResponseRedirect('/network/%s/add/' % (host_id))
            else:
                return HttpResponseRedirect('/network/%s/%s/' % (host_id, networks.keys()[0]))

        if pool == 'add':
            if request.method == 'POST':
                if 'addpool' in request.POST:
                    dhcp = []
                    pool_name = request.POST.get('name', '')
                    net_addr = request.POST.get('net_addr', '')
                    forward = request.POST.get('forward', '')
                    dhcp.append(request.POST.get('dhcp', ''))

                    import re
                    errors = []
                    name_have_symbol = re.search('[^a-zA-Z0-9\_\-]+', pool_name)
                    ip_have_symbol = re.search('[^0-9\.\/]+', net_addr)

                    if not pool_name:
                        msg = _("No pool name has been entered")
                        errors.append(msg)
                    elif len(pool_name) > 12:
                        msg = _("The pool name must not exceed 20 characters")
                        errors.append(msg)
                    else:
                        if name_have_symbol:
                            msg = _("The pool name must not contain any special characters")
                            errors.append(msg)
                    if not net_addr:
                        msg = _("No subnet has been entered")
                        errors.append(msg)
                    elif ip_have_symbol:
                        msg = _("The pool name must not contain any special characters")
                        errors.append(msg)
                    if pool_name in networks.keys():
                        msg = _("Pool name already in use")
                        errors.append(msg)
                    try:
                        from virtmgr.IPy import IP

                        netmask = IP(net_addr).strNetmask()
                        ipaddr = IP(net_addr)
                        gateway = ipaddr[0].strNormal()[-1]
                        if gateway == '0':
                            gw = ipaddr[1].strNormal()
                            dhcp_start = ipaddr[2].strNormal()
                            end = ipaddr.len() - 2
                            dhcp_end = ipaddr[end].strNormal()
                        else:
                            gw = ipaddr[0].strNormal()
                            dhcp_start = ipaddr[1].strNormal()
                            end = ipaddr.len() - 2
                            dhcp_end = ipaddr[end].strNormal()
                        dhcp.append(dhcp_start)
                        dhcp.append(dhcp_end)
                    except:
                        msg = _("Input subnet pool error")
                        errors.append(msg)
                    if not errors:
                        try:
                            libvirt_func.new_network_pool(conn, pool_name, forward, gw, netmask, dhcp)
                            net = conn.networkLookupByName(pool_name)
                            net.create()
                            net.setAutostart(1)
                            return HttpResponseRedirect('/network/%s/%s/' % (host_id, pool_name))
                        except libvirtError as error_msg:
                            errors.append(error_msg.message)
        else:
            all_vm = libvirt_func.vds_get_node(conn)
            net = conn.networkLookupByName(pool)

            info = libvirt_func.network_get_info(net)

            if info[0] == True:
                ipv4_net = libvirt_func.network_get_subnet(net)

            if request.method == 'POST':
                if 'start' in request.POST:
                    try:
                        net.create()
                        return HttpResponseRedirect('/network/%s/%s' % (host_id, pool))
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                if 'stop' in request.POST:
                    try:
                        net.destroy()
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                    return HttpResponseRedirect('/network/%s/%s' % (host_id, pool))
                if 'delete' in request.POST:
                    try:
                        net.undefine()
                    except libvirtError as error_msg:
                        errors.append(error_msg.message)
                    return HttpResponseRedirect('/network/%s/' % host_id)

        conn.close()

    return render_to_response('network.html', locals(), context_instance=RequestContext(request))
