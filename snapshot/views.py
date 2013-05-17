# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from dashboard.models import Host
from libvirt_func import libvirt_conn, vds_get_node, snapshots_get_node, snapshots_get_vds, snapshot_delete, snapshot_revert


def snapshot(request, host_id):
    """

    Snapshot block

    """


    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        all_vm = vds_get_node(conn)
        all_vm_snap = snapshots_get_node(conn)

        conn.close()

    if all_vm_snap:
        return HttpResponseRedirect('/snapshot/%s/%s/' % (host_id, all_vm_snap.keys()[0]))

    return render_to_response('snapshot.html', locals(), context_instance=RequestContext(request))


def dom_snapshot(request, host_id, vname):
    """

    Snapshot block

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        dom = conn.lookupByName(vname)
        all_vm = vds_get_node(conn)
        all_vm_snap = snapshots_get_node(conn)
        vm_snapshot = snapshots_get_vds(vname)

        if request.method == 'POST':
            if 'delete' in request.POST:
                name = request.POST.get('name', '')
                snapshot_delete(name)
                return HttpResponseRedirect('/snapshot/%s/%s/' % (host_id, vname))
            if 'revert' in request.POST:
                name = request.POST.get('name', '')
                snapshot_revert(name)
                message = _("Successful revert snapshot: ")
                message = message + name

    return render_to_response('snapshot.html', locals(), context_instance=RequestContext(request))
