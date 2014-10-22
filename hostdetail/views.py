from libvirt import libvirtError

from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
import json
import time

from servers.models import Compute
from vrtManager.hostdetails import wvmHostDetails
from webvirtmgr.settings import TIME_JS_REFRESH


def hostusage(request, host_id):
    """
    Return Memory and CPU Usage
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    points = 5
    datasets = {}
    cookies = {}
    compute = Compute.objects.get(id=host_id)
    curent_time = time.strftime("%H:%M:%S")

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
        mem_usage = 0

    try:
        cookies['cpu'] = request._cookies['cpu']
        cookies['cpu_time'] = request._cookies['cpu_time']
        cookies['mem'] = request._cookies['mem']
        cookies['mem_time'] = request._cookies['mem_time']
    except KeyError:
        cookies['cpu'] = None
        cookies['cpu_time'] = None
        cookies['mem'] = None
        cookies['mem_time'] = None

    if not cookies['cpu'] and not cookies['mem']:
        datasets['cpu'] = [0]
        datasets['mem'] = [0]
    else:
        datasets['cpu'] = eval(cookies['cpu'])
        datasets['mem'] = eval(cookies['mem'])

    if not cookies['cpu_time'] and not cookies['mem_time']:
        datasets['cpu_time'] = [curent_time]
        datasets['mem_time'] = [curent_time]
    else:
        datasets['cpu_time'] = eval(cookies['cpu_time'])
        datasets['mem_time'] = eval(cookies['mem_time'])

    if len(datasets['cpu_time']) <= points:
        datasets['cpu_time'].append(curent_time)
    if len(datasets['cpu_time']) >= points:
        del datasets['cpu_time'][0]

    if len(datasets['cpu']) <= points:
        datasets['cpu'].append(int(cpu_usage['usage']))
    if len(datasets['cpu']) >= points:
        del datasets['cpu'][0]

    if len(datasets['mem']) <= points:
        datasets['mem'].append(int(mem_usage['usage']) / 1048576)
    if len(datasets['mem']) >= points:
        del datasets['mem'][0]

    if len(datasets['mem_time']) <= points:
        datasets['mem_time'].append(curent_time)
    if len(datasets['mem_time']) >= points:
        del datasets['mem_time'][0]

    cpu = {
        'labels': datasets['cpu_time'],
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
        'labels': datasets['mem_time'],
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
    response.cookies['cpu_time'] = datasets['cpu_time']
    response.cookies['mem'] = datasets['mem']
    response.cookies['mem_time'] = datasets['mem_time']
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
