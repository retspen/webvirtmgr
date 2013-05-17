from django.http import HttpResponseRedirect
from dashboard.models import *


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
