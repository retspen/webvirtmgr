from string import letters, digits
from random import choice

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson

from instance.models import Instance
from servers.models import Compute

from vrtManager.instance import wvmInstances, wvmInstance

from libvirt import libvirtError, VIR_DOMAIN_XML_SECURE
from webvirtmgr.settings import TIME_JS_REFRESH


def diskusage(request, host_id, vname):
    """
    VM disk IO
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmInstance(compute.hostname,
                           compute.login,
                           compute.password,
                           compute.type,
                           vname)
        blk_usage = conn.disk_usage()
        data = simplejson.dumps(blk_usage)
        conn.close()
    except libvirtError as msg_error:
        data = msg_error.message

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

    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmInstance(compute.hostname,
                           compute.login,
                           compute.password,
                           compute.type,
                           vname)
        net_usage = conn.net_usage()
        data = simplejson.dumps(net_usage)
        conn.close()
    except libvirtError as msg_error:
        data = msg_error.message

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

    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmInstance(compute.hostname,
                           compute.login,
                           compute.password,
                           compute.type,
                           vname)
        cpu_usage = conn.cpu_usage()
        data = simplejson.dumps(cpu_usage)
        conn.close()
    except libvirtError as msg_error:
        data = msg_error.message

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
    instances = []
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmInstances(compute.hostname,
                            compute.login,
                            compute.password,
                            compute.type)
        get_instances = conn.get_instances()
    except libvirtError as msg_error:
        errors.append(msg_error.message)

    for instance in get_instances:
        try:
            inst = Instance.objects.get(compute_id=host_id, name=instance)
            uuid = inst.uuid
        except Instance.DoesNotExist:
            uuid = None
        instances.append({'name': instance,
                          'status': conn.get_instance_status(instance),
                          'uuid': uuid})

    try:
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
    messages = []
    time_refresh = TIME_JS_REFRESH
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmInstance(compute.hostname,
                           compute.login,
                           compute.password,
                           compute.type,
                           vname)

        status = conn.get_status()
        autostart = conn.get_autostart()
        vcpu = conn.get_vcpu()
        uuid = conn.get_uuid()
        memory = conn.get_memory()
        description = conn.get_description()
        disks = conn.get_disk_device()
        media = conn.get_media_device()
        networks = conn.get_net_device()
        media_iso = sorted(conn.get_iso_media())
        vcpu_range = conn.get_max_cpus()
        memory_range = [256, 512, 1024, 2048, 4096, 8192, 16384]
        vnc_port = conn.get_vnc()
        inst_xml = conn._XMLDesc(VIR_DOMAIN_XML_SECURE)

    except libvirtError as msg_error:
        errors.append(msg_error.message)

    try:
        instance = Instance.objects.get(compute_id=host_id, name=vname)
        if instance.uuid != uuid:
            instance.uuid = uuid
            instance.save()
    except Instance.DoesNotExist:
        instance = Instance(compute_id=host_id, name=vname, uuid=uuid)
        instance.save()

    try:
        if request.method == 'POST':
            if 'start' in request.POST:
                conn.start()
                return HttpResponseRedirect(request.get_full_path())
            if 'power' in request.POST:
                if 'shutdown' == request.POST.get('power', ''):
                    conn.shutdown()
                    return HttpResponseRedirect(request.get_full_path())
                if 'destroy' == request.POST.get('power', ''):
                    conn.force_shutdown()
                    return HttpResponseRedirect(request.get_full_path())
            if 'suspend' in request.POST:
                conn.suspend()
                return HttpResponseRedirect(request.get_full_path())
            if 'resume' in request.POST:
                conn.resume()
                return HttpResponseRedirect(request.get_full_path())
            if 'delete' in request.POST:
                if conn.get_status() == 1:
                    conn.force_shutdown()
                if request.POST.get('delete_disk', ''):
                    conn.delete_disk()
                try:
                    instance = Instance.objects.get(compute_id=host_id, name=vname)
                    instance.delete()
                finally:
                    conn.delete()
                return HttpResponseRedirect('/instances/%s/' % host_id)
            if 'snapshot' in request.POST:
                conn.create_snapshot()
                msg = _("Create snapshot for instance successful")
                messages.append(msg)
            if 'umount_iso' in request.POST:
                image = request.POST.get('iso_media', '')
                conn.umount_iso(image)
                return HttpResponseRedirect(request.get_full_path())
            if 'mount_iso' in request.POST:
                image = request.POST.get('iso_media', '')
                conn.mount_iso(image)
                return HttpResponseRedirect(request.get_full_path())
            if 'set_autostart' in request.POST:
                conn.set_autostart(1)
                return HttpResponseRedirect(request.get_full_path())
            if 'unset_autostart' in request.POST:
                conn.set_autostart(0)
                return HttpResponseRedirect(request.get_full_path())
            if 'change_settings' in request.POST:
                description = request.POST.get('description', '')
                vcpu = request.POST.get('vcpu', '')
                memory = request.POST.get('memory', '')
                conn.change_settings(description, memory, vcpu)
                return HttpResponseRedirect(request.get_full_path())
            if 'change_xml' in request.POST:
                xml = request.POST.get('inst_xml', '')
                if xml:
                    conn._defineXML(xml)
                    return HttpResponseRedirect(request.get_full_path())
            if 'set_vnc_passwd' in request.POST:
                if request.POST.get('auto_pass', ''):
                    passwd = ''.join([choice(letters + digits) for i in xrange(12)])
                else:
                    passwd = request.POST.get('vnc_passwd', '')
                    if not passwd:
                        msg = _("Enter the VNC password or select Generate")
                        errors.append(msg)
                if not errors:
                    conn.set_vnc_passwd(passwd)
                    return HttpResponseRedirect(request.get_full_path())
        conn.close()

    except libvirtError as msg_error:
        errors.append(msg_error.message)

    return render_to_response('instance.html', locals(), context_instance=RequestContext(request))
