from django import forms
from instance.models import Flavor
from django.utils.translation import ugettext_lazy as _
import re


class FlavorAddForm(forms.Form):
    name = forms.CharField(label="Name",
                           error_messages={'required': _('No flavor name has been entered')},
                           max_length=20)
    vcpu = forms.IntegerField(label="VCPU",
                              error_messages={'required': _('No VCPU has been entered')},)
    hdd = forms.IntegerField(label="HDD",
                             error_messages={'required': _('No HDD image has been entered')},)
    ram = forms.IntegerField(label="RAM",
                             error_messages={'required': _('No RAM size has been entered')},)

    def clean_name(self):
        name = self.cleaned_data['name']
        have_symbol = re.match('[^a-zA-Z0-9._-]+', name)
        if have_symbol:
            raise forms.ValidationError(_('The flavor name must not contain any special characters'))
        elif len(name) > 20:
            raise forms.ValidationError(_('The flavor name must not exceed 20 characters'))
        try:
            Flavor.objects.get(name=name)
        except Flavor.DoesNotExist:
            return name
        raise forms.ValidationError(_('Flavor name is already use'))


class NewVMForm(forms.Form):
    name = forms.CharField(error_messages={'required': _('No Virtual Machine name has been entered')},
                           max_length=20)
    vcpu = forms.IntegerField(error_messages={'required': _('No VCPU has been entered')})
    host_model = forms.BooleanField(required=False)
    hdd = forms.IntegerField(required=False)
    ram = forms.IntegerField(error_messages={'required': _('No RAM size has been entered')})
    networks = forms.CharField(error_messages={'required': _('No Network pool has been choice')})
    storage = forms.CharField(max_length=20, required=False)
    images = forms.CharField(required=False)
    hdd_size = forms.IntegerField(required=False)
    virtio = forms.BooleanField(required=False)
    autostart = forms.BooleanField(required=False)

    def clean_name(self):
        name = self.cleaned_data['name']
        have_symbol = re.match('[^a-zA-Z0-9._-]+', name)
        if have_symbol:
            raise forms.ValidationError(_('The name of the virtual machine must not contain any special characters'))
        elif len(name) > 20:
            raise forms.ValidationError(_('The name of the virtual machine must not exceed 20 characters'))
        return name
