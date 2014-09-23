from libvirt import libvirtError

from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
import json

from servers.models import Compute
from vrtManager.hostdetails import wvmHostDetails
from webvirtmgr.settings import TIME_JS_REFRESH


def hostusage(request, host_id):
    """
    Return Memory and CPU Usage
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    datasets = {}
    cookies = {}
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmHostDetails(compute.hostname,
                              compute.login,
                              compute.password,
                              compute.type)
        cpu_usage = conn.get_cpu_usage()
        mem_usage = conn.get_memory_usage()
        conn.close()
    except libvirtError:
        cpu_usage = 0

    try:
        cookies['cpu'] = request._cookies['cpu']
        cookies['mem'] = request._cookies['mem']
    except KeyError:
        cookies['cpu'] = None
        cookies['mem'] = None

    if not cookies['cpu'] and not cookies['mem']:
        datasets['cpu'] = [0]
        datasets['mem'] = [0]
    else:
        datasets['cpu'] = eval(cookies['cpu'])
        datasets['mem'] = eval(cookies['mem'])

    if len(datasets['cpu']) > 10:
        while datasets['cpu']:
            del datasets['cpu'][0]
            if len(datasets['cpu']) == 10:
                break

    if len(datasets['mem']) > 10:
        while datasets['mem']:
            del datasets['mem'][0]
            if len(datasets['mem']) == 10:
                break

    if len(datasets['cpu']) <= 9:
        datasets['cpu'].append(int(cpu_usage['usage']))
    if len(datasets['cpu']) == 10:
        datasets['cpu'].append(int(cpu_usage['usage']))
        del datasets['cpu'][0]

    if len(datasets['mem']) <= 9:
        datasets['mem'].append(int(mem_usage['usage']) / 1048576)
    if len(datasets['mem']) == 10:
        datasets['mem'].append(int(mem_usage['usage']) / 1048576)
        del datasets['mem'][0]

    cpu = {
        'labels': [""] * 10,
        'datasets': [
            {
                "fillColor": "rgba(241,72,70,0.5)",
                "strokeColor": "rgba(241,72,70,1)",
                "pointColor": "rgba(241,72,70,1)",
                "pointStrokeColor": "#fff",
                "data": datasets['cpu']
            }
        ]
    }

    memory = {
        'labels': [""] * 10,
        'datasets': [
            {
                "fillColor": "rgba(249,134,33,0.5)",
                "strokeColor": "rgba(249,134,33,1)",
                "pointColor": "rgba(249,134,33,1)",
                "pointStrokeColor": "#fff",
                "data": datasets['mem']
            }
        ]
    }

    data = json.dumps({'cpu': cpu, 'memory': memory})
    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    response.cookies['cpu'] = datasets['cpu']
    response.cookies['mem'] = datasets['mem']
    response.write(data)
    return response


def overview(request, host_id):
    """
    Overview page.
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    time_refresh = TIME_JS_REFRESH

    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmHostDetails(compute.hostname,
                              compute.login,
                              compute.password,
                              compute.type)
        hostname, host_arch, host_memory, logical_cpu, model_cpu, uri_conn = conn.get_node_info()
        hypervisor = conn.hypervisor_type()
        mem_usage = conn.get_memory_usage()
        conn.close()
    except libvirtError as err:
        errors.append(err)

    return render_to_response('hostdetail.html', locals(), context_instance=RequestContext(request))
