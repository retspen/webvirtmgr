# -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from dashboard.models import Host
import libvirt_func


def snapshot(request, host_id):
    """

    Snapshot block

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = libvirt_func.libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        all_vm = libvirt_func.vds_get_node(conn)
        all_vm_snap = libvirt_func.snapshots_get_node(conn)

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
    conn = libvirt_func.libvirt_conn(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        dom = conn.lookupByName(vname)
        all_vm = libvirt_func.vds_get_node(conn)
        all_vm_snap = libvirt_func.snapshots_get_node(conn)
        vm_snapshot = libvirt_func.snapshots_get_vds(dom)

        print vm_snapshot

        if request.method == 'POST':
            if 'delete' in request.POST:
                snap_name = request.POST.get('name', '')
                libvirt_func.snapshot_delete(dom, snap_name)
                return HttpResponseRedirect('/snapshot/%s/%s/' % (host_id, vname))
            if 'revert' in request.POST:
                snap_name = request.POST.get('name', '')
                libvirt_func.snapshot_revert(dom, snap_name)
                message = _("Successful revert snapshot: ")
                message = message + name

    return render_to_response('snapshot.html', locals(), context_instance=RequestContext(request))
