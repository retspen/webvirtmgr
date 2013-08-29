# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.datastructures import SortedDict
from instance.models import Host
from webvirtmgr.server import ConnServer
from dashboard.forms import HostAddTcpForm, HostAddSshForm


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
        """

        :param hosts:
        :return:
        """
        all_hosts = {}
        for host in hosts:
            try:
                import socket
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                if host.type == 'ssh':
                    s.connect((host.hostname, host.port))
                else:
                    s.connect((host.hostname, 16509))
                s.close()
                status = 1
            except Exception as err:
                status = err
            all_hosts[host.id] = (host.name, host.hostname, status)
        return all_hosts

    hosts = Host.objects.filter()
    hosts_info = get_hosts_status(hosts)

    if request.method == 'POST':
        if 'host_del' in request.POST:
            del_host = Host.objects.get(id=request.POST.get('host_id', ''))
            hostname = del_host.hostname
            del_host.delete()
            return HttpResponseRedirect(request.get_full_path())
        if 'host_tcp_add' in request.POST:
            form = HostAddTcpForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                new_host = Host(name=data['name'], hostname=data['hostname'], type='tcp',
                                login=data['login'], password=data['password1'])
                new_host.save()
                return HttpResponseRedirect(request.get_full_path())
        if 'host_ssh_add' in request.POST:
            form = HostAddSshForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                new_host = Host(name=data['name'], hostname=data['hostname'], type='ssh',
                                port=data['port'], login=login)
                new_host.save()
                return HttpResponseRedirect(request.get_full_path())

    hosts_info = SortHosts(hosts_info)

    return render_to_response('dashboard.html', locals(), context_instance=RequestContext(request))


def infrastructure(request):
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
            if host.type == 'ssh':
                s.connect((host.hostname, host.port))
            else:
                s.connect((host.hostname, 16509))
            s.close()
            status = 1
        except Exception as err:
            status = 2

        if status == 1:
            conn = ConnServer(host)
            host_info = conn.node_get_info()
            host_mem = conn.memory_get_usage()
            hosts_vms[host.id, host.name, status, host_info[2], host_mem[0], host_mem[2]] = conn.vds_on_cluster()
        else:
            hosts_vms[host.id, host.name, status, None, None, None] = None

    for host in hosts_vms:
        hosts_vms[host] = SortHosts(hosts_vms[host])
    hosts_vms = SortHosts(hosts_vms)

    return render_to_response('infrastructure.html', locals(), context_instance=RequestContext(request))


def page_setup(request):
    return render_to_response('setup.html', locals(), context_instance=RequestContext(request))
