from django import forms
from django.utils.translation import ugettext_lazy as _
import re


class AddNetPool(forms.Form):
    name = forms.CharField(error_messages={'required': _('No pool name has been entered')},
                           max_length=20)
    subnet = forms.CharField(error_messages={'required': _('No subnet has been entered')},
                             max_length=20)
    forward = forms.CharField(max_length=100)
    dhcp = forms.BooleanField(required=False)
    fixed = forms.BooleanField(required=False)
    bridge_name = forms.CharField(max_length=20, required=False)
    openvswitch = forms.BooleanField(required=False)

    def clean_name(self):
        name = self.cleaned_data['name']
        have_symbol = re.match('^[a-zA-Z0-9._-]+$', name)
        if not have_symbol:
            raise forms.ValidationError(_('The pool name must not contain any special characters'))
        elif len(name) > 20:
            raise forms.ValidationError(_('The pool name must not exceed 20 characters'))
        return name

    def clean_subnet(self):
        subnet = self.cleaned_data['subnet']
        have_symbol = re.match('^[0-9./]+$', subnet)
        if not have_symbol:
            raise forms.ValidationError(_('The pool subnet must not contain any special characters'))
        elif len(subnet) > 20:
            raise forms.ValidationError(_('The pool subnet must not exceed 20 characters'))
        return subnet

    def clean_bridge_name(self):
        bridge_name = self.cleaned_data['bridge_name']
        if self.cleaned_data['forward'] == 'bridge':
            have_symbol = re.match('^[a-zA-Z0-9._-]+$', bridge_name)
            if not have_symbol:
                raise forms.ValidationError(_('The pool bridge name must not contain any special characters'))
            elif len(bridge_name) > 20:
                raise forms.ValidationError(_('The pool bridge name must not exceed 20 characters'))
            return bridge_name
