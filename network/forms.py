from django import forms
from django.utils.translation import ugettext_lazy as _
import re


class AddNetPool(forms.Form):
    name = forms.CharField(max_length=20)
    subnet = forms.CharField(max_length=20)
    forward = forms.CharField(max_length=100)
    dhcp = forms.CharField(max_length=100, required=False)

    def clean_name(self):
        name = self.cleaned_data['name']
        have_simbol = re.search('[^a-zA-Z0-9_\-\.]+', name)
        if have_simbol:
            raise forms.ValidationError(_('The pool name must not contain any special characters'))
        elif len(name) > 20:
            raise forms.ValidationError(_('The pool name must not exceed 20 characters'))
        return name

    def clean_subnet(self):
        subnet = self.cleaned_data['subnet']
        have_simbol = re.search('[^0-9\.\/]+', subnet)
        if have_simbol:
            raise forms.ValidationError(_('The pool subnet must not contain any special characters'))
        elif len(subnet) > 20:
            raise forms.ValidationError(_('The pool subnet must not exceed 20 characters'))
        return subnet