# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from dashboard.models import *


def index(request):
    """

    Index page.

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')
    else:
        return HttpResponseRedirect('/dashboard')


def page_setup(request):
    return render_to_response('setup.html', locals(), context_instance=RequestContext(request))


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
                s.connect((host.ipaddr, 16509))
                s.close()
                status = 1
            except Exception as err:
                status = err
            all_hosts[host.hostname] = (host.id, host.ipaddr, status)
        return all_hosts

    def del_host(host_id):
        hosts = Host.objects.get(id=host_id)
        hosts.delete()

    def add_host(host, ipaddr, login, passwd):
        hosts = Host(hostname=host, ipaddr=ipaddr, login=login, passwd=passwd)
        hosts.save()

    hosts = Host.objects.filter()
    host_info = get_hosts_status(hosts)
    errors = []

    if request.method == 'POST':
        if 'delhost' in request.POST:
            del_host = Host.objects.get(id=request.POST.get('srv_id', ''))
            hostname = del_host.hostname
            del_host.is_deleted = True
            del_host.save()
            msg = _('Delete host: %s') % hostname
            add_log(msg, request.user.id)
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

            import re
            errors = []
            have_simbol = re.search('[^a-zA-Z0-9\_\-\.]+', hostname)
            ip_have_simbol = re.search('[^a-z0-9\.\-]+', ipaddr)
            domain = re.search('[\.]+', ipaddr)
            privat_ip = re.search('^0\.|^127\.|^255\.', ipaddr)

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
                    have_host = Host.objects.filter(hostname=hostname, is_deleted=0)
                    have_ip = Host.objects.filter(ipaddr=ipaddr, is_deleted=0)
                    if have_host or have_ip:
                        msg = _('This host is already connected')
                        errors.append(msg)
            if not ipaddr:
                msg = _('No IP address has been entered')
                errors.append(msg)
            elif privat_ip:
                msg = _('IP address can not be a private address space')
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
                msg = _('Add host: %s') % hostname
                add_log(msg, request.user.id)
                return HttpResponseRedirect(request.get_full_path())

    if request.method == 'POST':
        if 'del_host' in request.POST:
            host_id = request.POST.get('host_id', '')
            del_host(host_id)
            return HttpResponseRedirect(request.get_full_path())
        if request.POST.get('add_host', ''):
            name = request.POST.get('hostname', '')
            ipaddr = request.POST.get('ipaddr', '')
            login = request.POST.get('kvm_login', '')
            passwd = request.POST.get('kvm_passwd', '')

            import re
            symbol = re.search('[^a-zA-Z0-9\-\.]+', name)
            ipsymbol = re.search('[^a-z0-9\.\-]+', ipaddr)
            domain = re.search('[\.]+', ipaddr)

            if not name:
                msg = 'No hostname has been entered'
                errors.append(msg)
            elif len(name) > 20:
                msg = 'The host name must not exceed 20 characters'
                errors.append(msg)
            elif symbol:
                msg = 'The host name must not contain any special characters'
                errors.append(msg)
            if not ipaddr:
                msg = 'No IP address has been entered'
                errors.append(msg)
            elif ipaddr == '127.0.0.1':
                msg = 'Are you sure? This IP is not serious'
                errors.append(msg)
            elif ipsymbol or not domain:
                msg = 'Hostname must contain only numbers, or the domain name separated by "."'
                errors.append(msg)
            else:
                have_host = Host.objects.filter(hostname=name)
                have_ip = Host.objects.filter(ipaddr=ipaddr)
                if have_host or have_ip:
                    msg = 'This host is already connected'
                    errors.append(msg)
            if not login:
                msg = 'No KVM login was been entered'
                errors.append(msg)
            if not passwd:
                msg = 'No KVM password was been entered'
                errors.append(msg)
            if not errors:
                add_host(name, ipaddr, login, passwd)
                return HttpResponseRedirect(request.get_full_path())

    return render_to_response('dashboard.html', locals(), context_instance=RequestContext(request))
