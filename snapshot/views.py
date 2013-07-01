  # -*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from vds.models import Host
from webvirtmgr.server import ConnServer


def snapshot(request, host_id):
    """

    Snapshot block

    """

    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    host = Host.objects.get(id=host_id)
    conn = ConnServer(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        all_vm = conn.vds_get_node()
        all_vm_snap = conn.snapshots_get_node()

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

    snapshot_page = True
    host = Host.objects.get(id=host_id)
    conn = ConnServer(host)

    if type(conn) == dict:
        return HttpResponseRedirect('/overview/%s/' % host_id)
    else:
        all_vm = conn.vds_get_node()
        all_vm_snap = conn.snapshots_get_node()
        vm_snapshot = conn.snapshots_get_vds(vname)

        if request.method == 'POST':
            if 'delete' in request.POST:
                snap_name = request.POST.get('name', '')
                conn.snapshot_delete(vname, snap_name)
                return HttpResponseRedirect('/snapshot/%s/%s/' % (host_id, vname))
            if 'revert' in request.POST:
                snap_name = request.POST.get('name', '')
                conn.snapshot_revert(vname, snap_name)
                message = _("Successful revert snapshot: ")
                message = message + snap_name

    return render_to_response('snapshot.html', locals(), context_instance=RequestContext(request))
