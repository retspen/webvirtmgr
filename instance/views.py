from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson

from instance.models import Instance
from servers.models import Compute

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
    return request


def instance(request, host_id, vname):
    """

    VDS block

    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    time_refresh = TIME_JS_REFRESH
    messages = []
    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None

    if not conn:
        errors.append(e.message)
    else:
        all_vm = sort_host(conn.vds_get_node())
        vcpu, memory, networks, description = conn.vds_get_info(vname)
        hdd_image = conn.vds_get_hdd(vname)
        iso_images = sorted(conn.get_all_media())
        media, media_path = conn.vds_get_media(vname)
        dom = conn.lookupVM(vname)
        vcpu_range = [str(x) for x in range(1, 9)]
        memory_range = [128, 256, 512, 768, 1024, 2048, 4096, 8192, 16384]
        vnc_port = conn.vnc_get_port(vname)

        try:
            instance = Instance.objects.get(vname=vname)
        except:
            instance = None

        if request.method == 'POST':
            if 'start' in request.POST:
                try:
                    dom.create()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'power' in request.POST:
                if 'shutdown' == request.POST.get('power', ''):
                    try:
                        dom.shutdown()
                        return HttpResponseRedirect(request.get_full_path())
                    except libvirtError as msg_error:
                        errors.append(msg_error.message)
                if 'destroy' == request.POST.get('power', ''):
                    try:
                        dom.destroy()
                        return HttpResponseRedirect(request.get_full_path())
                    except libvirtError as msg_error:
                        errors.append(msg_error.message)
            if 'suspend' in request.POST:
                try:
                    dom.suspend()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'resume' in request.POST:
                try:
                    dom.resume()
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'delete' in request.POST:
                try:
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
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'snapshot' in request.POST:
                try:
                    conn.vds_create_snapshot(vname)
                    msg = _("Create snapshot for instance successful")
                    messages.append(msg)
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'remove_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                try:
                    conn.vds_umount_iso(vname, image)

                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'add_iso' in request.POST:
                image = request.POST.get('iso_img', '')
                try:
                    conn.vds_mount_iso(vname, image)
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'edit' in request.POST:
                description = request.POST.get('description', '')
                vcpu = request.POST.get('vcpu', '')
                ram = request.POST.get('ram', '')
                try:
                    conn.vds_edit(vname, description, ram, vcpu)
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
            if 'xml_edit' in request.POST:
                xml = request.POST.get('vm_xml', '')
                try:
                    if xml:
                        conn.defineXML(xml)
                    return HttpResponseRedirect(request.get_full_path())
                except libvirtError as msg_error:
                    errors.append(msg_error.message)
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
                    try:
                        conn.vds_set_vnc_passwd(vname, passwd)
                        vnc_pass.save()
                    except libvirtError as msg_error:
                        errors.append(msg_error.message)
                    return HttpResponseRedirect(request.get_full_path())

        conn.close()

    return render_to_response('instance.html', {'host_id': host_id,
                                                'vname': vname,
                                                'messages': messages,
                                                'errors': errors,
                                                'instance': instance,
                                                'all_vm': all_vm,
                                                'vcpu': vcpu, 'vcpu_range': vcpu_range,
                                                'description': description,
                                                'networks': networks,
                                                'memory': memory, 'memory_range': memory_range,
                                                'hdd_image': hdd_image, 'iso_images': iso_images,
                                                'media': media, 'path': media_path,
                                                'dom': dom,
                                                'vm_xml': dom.XMLDesc(VIR_DOMAIN_XML_SECURE),
                                                'vnc_port': vnc_port,
                                                'time_refresh': time_refresh
                                                },
                              context_instance=RequestContext(request))
