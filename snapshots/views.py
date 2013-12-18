from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _

from servers.models import Compute
from vrtManager.connection import wvmConnect

from libvirt import libvirtError


def snapshots(request, host_id):
    """
    Snapshots block
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmConnect(compute.hostname,
                          compute.login,
                          compute.password,
                          compute.type)
        snapshots = conn.get_snapshots()
        conn.close()
    except libvirtError as msg_error:
        errors.append(msg_error.message)

    return render_to_response('snapshots.html', locals(), context_instance=RequestContext(request))


def snapshot(request, host_id, vname):
    """
    Snapshot block
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    message = ''
    snapshot_page = True
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmConnect(compute.hostname,
                          compute.login,
                          compute.password,
                          compute.type)
        vm_snapshot = conn.get_snapshot(vname)

        if request.method == 'POST':
            if 'delete' in request.POST:
                snap_name = request.POST.get('name', '')
                conn.snapshot_delete(vname, snap_name)
                return HttpResponseRedirect('/snapshot/%s/%s/' % (host_id, vname))
            if 'revert' in request.POST:
                snap_name = request.POST.get('name', '')
                conn.snapshot_revert(vname, snap_name)
                message = _("Successful revert snapshot: ")
                message += snap_name

        conn.close()
    except libvirtError as msg_error:
        errors.append(msg_error.message)

    return render_to_response('snapshot.html', locals(), context_instance=RequestContext(request))
