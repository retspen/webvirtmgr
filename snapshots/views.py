from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from servers.models import Compute

from libvirt import libvirtError


def snapshots(request, host_id):
    """

    Snapshot block

    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None

    if not conn:
        errors.append(e.message)
    else:
        all_vm_snap = conn.snapshots_get_node()
        conn.close()

        if all_vm_snap:
            return HttpResponseRedirect('/snapshot/%s/%s/' % (host_id, all_vm_snap.keys()[0]))

    return render_to_response('snapshot.html', locals(), context_instance=RequestContext(request))


def snapshot(request, host_id, vname):
    """

    Snapshot block

    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    message = ''
    snapshot_page = True
    host = Host.objects.get(id=host_id)

    try:
        conn = ConnServer(host)
    except libvirtError as e:
        conn = None

    if not conn:
        errors.append(e.message)
    else:
        all_vm = sort_host(conn.vds_get_node())
        all_vm_snap = conn.snapshots_get_node()
        vm_snapshot = conn.snapshots_get_vds(vname)

        if request.method == 'POST':
            if 'delete' in request.POST:
                snap_name = request.POST.get('name', '')
                try:
                    conn.snapshot_delete(vname, snap_name)
                    return HttpResponseRedirect('/snapshot/%s/%s/' % (host_id, vname))
                except libvirtError as error_msg:
                    errors.append(error_msg.message)
            if 'revert' in request.POST:
                snap_name = request.POST.get('name', '')
                try:
                    conn.snapshot_revert(vname, snap_name)
                    message = _("Successful revert snapshot: ")
                    message += snap_name
                except libvirtError as error_msg:
                    errors.append(error_msg.message)

    return render_to_response('snapshot.html', {'host_id': host_id,
                                                'vname': vname,
                                                'errors': errors,
                                                'message': message,
                                                'snapshot_page': snapshot_page,
                                                'all_vm': all_vm,
                                                'all_vm_snap': all_vm_snap,
                                                'vm_snapshot': vm_snapshot
                                                },
                              context_instance=RequestContext(request))
