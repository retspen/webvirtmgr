from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext

from servers.models import Compute
from secrets.forms import AddSecret

from vrtManager.secrets import wvmSecrets

from libvirt import libvirtError


def secrets(request, host_id):
    """
    Networks block
    """
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/login')

    errors = []
    secrets_all = []
    compute = Compute.objects.get(id=host_id)

    try:
        conn = wvmSecrets(compute.hostname,
                          compute.login,
                          compute.password,
                          compute.type)
        secrets = conn.get_secrets()
        for uuid in secrets:
            secrt = conn.get_secret(uuid)
            try:
                secret_value = conn.get_secret_value(uuid)
            except:
                secret_value = ''
            secrets_all.append({'usage': secrt.usageID(),
                                'uuid': secrt.UUIDString(),
                                'usageType': secrt.usageType(),
                                'value': secret_value
            })
        if request.method == 'POST':
            if 'create' in request.POST:
                form = AddSecret(request.POST)
                if form.is_valid():
                    data = form.cleaned_data
                    conn.create_secret(data['ephemeral'], data['private'], data['usage_type'], data['data'])
                    return HttpResponseRedirect(request.get_full_path())
            if 'delete' in request.POST:
                uuid = request.POST.get('uuid', '')
                conn.delete_secret(uuid)
                return HttpResponseRedirect(request.get_full_path())
            if 'set_value' in request.POST:
                uuid = request.POST.get('uuid', '')
                value = request.POST.get('value', '')
                conn.set_secret_value(uuid, value)
                return HttpResponseRedirect(request.get_full_path())
    except libvirtError as err:
        errors.append(err)

    return render_to_response('secrets.html', locals(), context_instance=RequestContext(request))
