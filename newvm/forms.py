from django import forms
from instance.models import Flavor
from django.utils.translation import ugettext_lazy as _
import re


class FlavorAddForm(forms.Form):
    name = forms.CharField(max_length=20)
    vcpu = forms.IntegerField()
    hdd = forms.IntegerField()
    ram = forms.IntegerField()

    def clean_name(self):
        name = self.cleaned_data['name']
        have_simbol = re.search('[^a-zA-Z0-9]+', name)
        if have_simbol:
            raise forms.ValidationError(_('The flavor name must not contain any special characters'))
        elif len(name) > 20:
            raise forms.ValidationError(_('The flavor name must not exceed 20 characters'))
        try:
            Flavor.objects.get(name=name)
        except Flavor.DoesNotExist:
            return name
        raise forms.ValidationError(_('Flavor name is already use'))


class NewVMForm(forms.Form):
    name = forms.CharField(max_length=20)
    vcpu = forms.IntegerField()
    hdd = forms.IntegerField(required=False)
    ram = forms.IntegerField()
    network = forms.CharField(max_length=20)
    storage = forms.CharField(max_length=20, required=False)
    image = forms.CharField(max_length=20, required=False)
    hdd_size = forms.IntegerField(required=False)
    virtio = forms.BooleanField(required=False)

    def clean_name(self):
        name = self.cleaned_data['name']
        have_simbol = re.search('[^a-zA-Z0-9\_\-\.]+', name)
        if have_simbol:
            raise forms.ValidationError(_('The name of the virtual machine must not contain any special characters'))
        elif len(name) > 20:
            raise forms.ValidationError(_('The name of the virtual machine must not exceed 20 characters'))
        return name
