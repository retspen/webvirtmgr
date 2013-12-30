from libvirt import libvirtError

from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.utils import simplejson

from servers.models import Compute
from vrtManager.hostdetails import wvmHostDetails
from webvirtmgr.settings import TIME_JS_REFRESH


def cpuusage(request, host_id):
    """
    Return CPU Usage in %
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    datasets = []
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmHostDetails(compute.hostname,
                              compute.login,
                              compute.password,
                              compute.type)
        cpu_usage = conn.get_cpu_usage()
        conn.close()
    except libvirtError:
        cpu_usage = 0

    try:
        cookies = request._cookies['cpu_usage']
    except KeyError:
        cookies = None

    if not cookies:
        datasets.append(0)
    else:
        datasets = eval(cookies)
    if len(datasets) > 10:
        while datasets:
            del datasets[0]
            if len(datasets) == 10:
                break
    if len(datasets) <= 9:
        datasets.append(int(cpu_usage['usage']))
    if len(datasets) == 10:
        datasets.append(int(cpu_usage['usage']))
        del datasets[0]

    # Some fix division by 0 Chart.js
    if len(datasets) == 10:
        if sum(datasets) == 0:
            datasets[9] += 0.1
        if sum(datasets) / 10 == datasets[0]:
            datasets[9] += 0.1

    cpu = {
        'labels': [""] * 10,
        'datasets': [
            {
                "fillColor": "rgba(241,72,70,0.5)",
                "strokeColor": "rgba(241,72,70,1)",
                "pointColor": "rgba(241,72,70,1)",
                "pointStrokeColor": "#fff",
                "data": datasets
            }
        ]
    }

    data = simplejson.dumps(cpu)
    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    response.cookies['cpu_usage'] = datasets
    response.write(data)
    return response


def memusage(request, host_id):
    """
    Return Memory Usage in % and numeric
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    datasets = []
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmHostDetails(compute.hostname,
                              compute.login,
                              compute.password,
                              compute.type)
        mem_usage = conn.get_memory_usage()
        conn.close()
    except libvirtError:
        mem_usage = 0

    try:
        cookies = request._cookies['memory_usage']
    except KeyError:
        cookies = None

    if not cookies:
        datasets.append(0)
    else:
        datasets = eval(cookies)
    if len(datasets) > 10:
        while datasets:
            del datasets[0]
            if len(datasets) == 10:
                break
    if len(datasets) <= 9:
        datasets.append(int(mem_usage['usage']) / 1048576)
    if len(datasets) == 10:
        datasets.append(int(mem_usage['usage']) / 1048576)
        del datasets[0]

    # Some fix division by 0 Chart.js
    if len(datasets) == 10:
        if sum(datasets) == 0:
            datasets[9] += 0.1
        if sum(datasets) / 10 == datasets[0]:
            datasets[9] += 0.1

    memory = {
        'labels': [""] * 10,
        'datasets': [
            {
                "fillColor": "rgba(249,134,33,0.5)",
                "strokeColor": "rgba(249,134,33,1)",
                "pointColor": "rgba(249,134,33,1)",
                "pointStrokeColor": "#fff",
                "data": datasets
            }
        ]
    }

    data = simplejson.dumps(memory)
    response = HttpResponse()
    response['Content-Type'] = "text/javascript"
    response.cookies['memory_usage'] = datasets
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
        errors.append(err.message)

    return render_to_response('hostdeatil.html', locals(), context_instance=RequestContext(request))
