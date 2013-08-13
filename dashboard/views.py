# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from vds.models import Host
from webvirtmgr.server import ConnServer
import re


def SortHosts(hosts):
    """

    Sorts dictionary of hosts by key

    """
    if hosts:
        sorted_hosts = []
        for host in sorted(hosts.iterkeys()):
            sorted_hosts.append((host, hosts[host]))
        return SortedDict(sorted_hosts)


def index(request):
    """

    Index page.

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')
    else:
        return HttpResponseRedirect('/dashboard')


def dashboard(request):
    """

    Dashboard page.

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    def get_hosts_status(hosts):
        all_hosts = {}
        for host in hosts:
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                if host.conn_type == 'ssh':
                    s.connect((host.ipaddr, host.ssh_port))
                else:
                    s.connect((host.ipaddr, 16509))
                s.close()
                status = 1
            except Exception as err:
                status = err
            all_hosts[host.hostname] = (host.id, host.ipaddr, status)
        return all_hosts

    hosts = Host.objects.filter()
    host_info = get_hosts_status(hosts)

    errors = []

    if request.method == 'POST':
        if 'delhost' in request.POST:
            del_host = Host.objects.get(id=request.POST.get('host_id', ''))
            hostname = del_host.hostname
            del_host.delete()
            return HttpResponseRedirect(request.get_full_path())
        if 'addhost' in request.POST:
            hostname = request.POST.get('hostname', '')
            ipaddr = request.POST.get('ipaddr', '')
            con_type = request.POST.get('con_type', '')
            kvm_login = request.POST.get('kvm_login', '')
            ssh_login = request.POST.get('ssh_login', '')
            ssh_port = request.POST.get('ssh_port', '')
            kvm_passwd1 = request.POST.get('kvm_passwd1', '')
            kvm_passwd2 = request.POST.get('kvm_passwd2', '')
            have_simbol = re.search('[^a-zA-Z0-9\_\-\.]+', hostname)
            ip_have_simbol = re.search('[^a-z0-9\.\-]+', ipaddr)
            domain = re.search('[\.]+', ipaddr)
            privat_ip = re.search('^0\.|^255\.', ipaddr)

            if not hostname:
                msg = _('No hostname has been entered')
                errors.append(msg)
            elif len(hostname) > 12:
                msg = _('The host name must not exceed 12 characters')
                errors.append(msg)
            else:
                if have_simbol:
                    msg = _('The host name must not contain any special characters')
                    errors.append(msg)
                else:
                    have_host = Host.objects.filter(hostname=hostname)
                    have_ip = Host.objects.filter(ipaddr=ipaddr)
                    if have_host or have_ip:
                        msg = _('This host is already connected')
                        errors.append(msg)
            if not ipaddr:
                msg = _('No IP address has been entered')
                errors.append(msg)
            elif privat_ip:
                msg = _('Wrong IP address')
                errors.append(msg)
            else:
                if ip_have_simbol or not domain:
                    msg = _('Hostname must contain only numbers, or the domain name separated by "."')
                    errors.append(msg)
            if con_type == 'tcp':
                if not kvm_login:
                    msg = _('No KVM login has been entered')
                    errors.append(msg)
                if not kvm_passwd1:
                    msg = _('No KVM password has been entered')
                    errors.append(msg)
                if not kvm_passwd2:
                    msg = _('No KVM password confirm has been entered')
                    errors.append(msg)
                else:
                    if kvm_passwd1 != kvm_passwd2:
                        msg = _('Your password didn\'t match. Please try again.')
                        errors.append(msg)
            if con_type == 'ssh':
                if not ssh_port.isdigit():
                    msg = _('SSH port mast be digits')
                    errors.append(msg)
                if not ssh_login:
                    msg = _('No SSH login has been entered')
                    errors.append(msg)

            if not errors:
                if con_type == 'tcp':
                    add_host = Host(hostname=hostname, ipaddr=ipaddr, conn_type=con_type,
                                    login=kvm_login, passwd=kvm_passwd1)
                if con_type == 'ssh':
                    add_host = Host(hostname=hostname, ipaddr=ipaddr, conn_type=con_type,
                                    login=ssh_login, ssh_port=ssh_port)
                add_host.save()
                return HttpResponseRedirect(request.get_full_path())

    host_info = SortHosts(host_info)

    return render_to_response('dashboard.html', locals(), context_instance=RequestContext(request))


def clusters(request):
    """

    Infrastructure page.

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    hosts = Host.objects.filter().order_by('id')
    hosts_vms = {}

    for host in hosts:
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            if host.conn_type == 'ssh':
                s.connect((host.ipaddr, host.ssh_port))
            else:
                s.connect((host.ipaddr, 16509))
            s.close()
            status = 1
        except Exception as err:
            status = 2

        if status == 1:
            conn = ConnServer(host)
            host_info = conn.node_get_info()
            host_mem = conn.memory_get_usage()
            hosts_vms[host.id, host.hostname, status, host_info[2], host_mem[0], host_mem[2]] = conn.vds_on_cluster()
        else:
            hosts_vms[host.id, host.hostname, status, None, None, None] = None

    for host in hosts_vms:
        hosts_vms[host] = SortHosts(hosts_vms[host])
    hosts_vms = SortHosts(hosts_vms)

    return render_to_response('clusters.html', locals(), context_instance=RequestContext(request))


def page_setup(request):
    return render_to_response('setup.html', locals(), context_instance=RequestContext(request))
