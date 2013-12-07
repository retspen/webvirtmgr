from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson

from instance.models import Instance
from servers.models import Compute

from vrtManager import util
from vrtManager.instance import wvmInstances, wvmInstance

from libvirt import libvirtError, VIR_DOMAIN_XML_SECURE
from webvirtmgr.settings import TIME_JS_REFRESH


def diskusage(request, host_id, vname):
    """
    VM disk IO
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except:
        conn = None

    if conn:
        blk_usage = conn.vds_disk_usage(vname)
        data = simplejson.dumps(blk_usage)
    else:
        data = None

    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    response.write(data)
    return response


def netusage(request, host_id, vname):
    """
    VM net bandwidth
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except:
        conn = None

    if conn:
        net_usage = conn.vds_network_usage(vname)
        data = simplejson.dumps(net_usage)
    else:
        data = None

    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    response.write(data)
    return response


def cpuusage(request, host_id, vname):
    """
    VM cpu usage
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except:
        conn = None

    if conn:
        cpu_usage = conn.vds_cpu_usage(vname)
        data = simplejson.dumps(cpu_usage)
    else:
        data = None

    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    response.write(data)
    return response


def instances(request, host_id):
    """
    Instances block
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    instances = {}
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmInstances(compute.hostname,
                            compute.login,
                            compute.password,
                            compute.type)
        get_instances = conn.get_instances()

        for instance in get_instances:
            try:
                instance_uuid = Instance.objects.get(compute_id=host_id, name=instance)
            except:
                instance_uuid = None
            instances[instance] = (conn.get_instance_status(instance), instance_uuid)

        if request.method == 'POST':
            name = request.POST.get('name', '')
            if 'start' in request.POST:
                conn.start(name)
                return HttpResponseRedirect(request.get_full_path())
            if 'shutdown' in request.POST:
                conn.shutdown(name)
                return HttpResponseRedirect(request.get_full_path())
            if 'destroy' in request.POST:
                conn.force_shutdown(name)
                return HttpResponseRedirect(request.get_full_path())
            if 'suspend' in request.POST:
                conn.suspend(name)
                return HttpResponseRedirect(request.get_full_path())
            if 'resume' in request.POST:
                conn.resume(name)
                return HttpResponseRedirect(request.get_full_path())

        conn.close()

    except libvirtError as msg_error:
        errors.append(msg_error.message)

    return render_to_response('instances.html', locals(), context_instance=RequestContext(request))

def instance(request, host_id, vname):
    """
    Instance block
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    time_refresh = TIME_JS_REFRESH
    messages = []
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmInstance(compute.hostname,
                           compute.login,
                           compute.password,
                           compute.type,
                           vname)

        status = conn.get_status()
        vcpu = conn.get_vcpu()
        memory = conn.get_memory()
        description = conn.get_description()
        disks = conn.get_disk_device()
        networks = conn.get_net_device()
        media_iso = sorted(conn.get_iso_media())
        vcpu_range = conn.get_max_cpus()
        memory_range = [256, 512, 1024, 2048, 4096, 8192, 16384]
        vnc_port = conn.get_vnc()

        try:
            instance = Instance.objects.get(vname=vname)
        except:
            instance = None

        if request.method == 'POST':
            if 'start' in request.POST:
                dom.create()
                return HttpResponseRedirect(request.get_full_path())
            if 'power' in request.POST:
                if 'shutdown' == request.POST.get('power', ''):
                    dom.shutdown()
                    return HttpResponseRedirect(request.get_full_path())
                if 'destroy' == request.POST.get('power', ''):
                    dom.destroy()
                    return HttpResponseRedirect(request.get_full_path())
            if 'suspend' in request.POST:
                dom.suspend()
                return HttpResponseRedirect(request.get_full_path())
            if 'resume' in request.POST:
                dom.resume()
                return HttpResponseRedirect(request.get_full_path())
            if 'delete' in request.POST:
                if dom.info()[0] == 1:
                    dom.destroy()
                if request.POST.get('image', ''):
                    conn.vds_remove_hdd(vname)
                try:
                    instance = Instance.objects.get(host=host_id, vname=vname)
                    instance.delete()
                except:
                    pass
                dom.undefine()
                return HttpResponseRedirect('/overview/%s/' % host_id)
            if 'snapshot' in request.POST:
                conn.vds_create_snapshot(vname)
                msg = _("Create snapshot for instance successful")
                messages.append(msg)
            if 'remove_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                conn.vds_umount_iso(vname, image)
                return HttpResponseRedirect(request.get_full_path())
            if 'add_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                conn.vds_mount_iso(vname, image)
                return HttpResponseRedirect(request.get_full_path())
            if 'edit' in request.POST:
                description = request.POST.get('description', '')
                vcpu = request.POST.get('vcpu', '')
                ram = request.POST.get('ram', '')
                conn.vds_edit(vname, description, ram, vcpu)
                return HttpResponseRedirect(request.get_full_path())
            if 'xml_edit' in request.POST:
                xml = request.POST.get('vm_xml', '')
                if xml:
                    conn.defineXML(xml)
                    return HttpResponseRedirect(request.get_full_path())
            if 'vnc_pass' in request.POST:
                if request.POST.get('auto_pass', ''):
                    from string import letters, digits
                    from random import choice
                    passwd = ''.join([choice(letters + digits) for i in range(12)])
                else:
                    passwd = request.POST.get('vnc_passwd', '')
                    if not passwd:
                        msg = _("Enter the VNC password or select Generate")
                        errors.append(msg)
                if not errors:
                    try:
                        vnc_pass = Instance.objects.get(vname=vname)
                        vnc_pass.vnc_passwd = passwd
                    except:
                        vnc_pass = Instance(host_id=host_id, vname=vname, vnc_passwd=passwd)
                        conn.vds_set_vnc_passwd(vname, passwd)
                        vnc_pass.save()
                    return HttpResponseRedirect(request.get_full_path())

        conn.close()

    except libvirtError as msg_error:
        errors.append(msg_error.message)

    return render_to_response('instance.html', locals(), context_instance=RequestContext(request))
