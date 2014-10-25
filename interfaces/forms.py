import re
from django.utils.translation import ugettext_lazy as _
from django import forms


class AddInterface(forms.Form):
    name = forms.CharField(max_length=10, required=True)
    itype = forms.ChoiceField(required=True, choices=(('bridge', 'bridge'), ('ethernet', 'ethernet')))
    start_mode = forms.ChoiceField(required=True,
                                   choices=(('none', 'none'), ('onboot', 'onboot'), ('hotplug', 'hotplug')))
    netdev = forms.CharField(max_length=15, required=True)
    ipv4_type = forms.ChoiceField(required=True, choices=(('dhcp', 'dhcp'), ('static', 'static'), ('none', 'none')))
    ipv4_addr = forms.CharField(max_length=18, required=False)
    ipv4_gw = forms.CharField(max_length=15, required=False)
    ipv6_type = forms.ChoiceField(required=True, choices=(('dhcp', 'dhcp'), ('static', 'static'), ('none', 'none')))
    ipv6_addr = forms.CharField(max_length=100, required=False)
    ipv6_gw = forms.CharField(max_length=100, required=False)
    stp = forms.ChoiceField(required=False, choices=(('on', 'on'), ('off', 'off')))
    delay = forms.IntegerField(required=False)

    def clean_ipv4_addr(self):
        ipv4_addr = self.cleaned_data['ipv4_addr']
        have_symbol = re.match('^[0-9./]+$', ipv4_addr)
        if not have_symbol:
            raise forms.ValidationError(_('The ipv4 must not contain any special characters'))
        elif len(ipv4_addr) > 20:
            raise forms.ValidationError(_('The ipv4 must not exceed 20 characters'))
        return ipv4_addr

    def clean_ipv4_gw(self):
        ipv4_gw = self.cleaned_data['ipv4_gw']
        have_symbol = re.match('^[0-9.]+$', ipv4_gw)
        if not have_symbol:
            raise forms.ValidationError(_('The ipv4 gateway must not contain any special characters'))
        elif len(ipv4_gw) > 20:
            raise forms.ValidationError(_('The ipv4 gateway must not exceed 20 characters'))
        return ipv4_gw

    def clean_ipv6_addr(self):
        ipv6_addr = self.cleaned_data['ipv6_addr']
        have_symbol = re.match('^[0-9a-f./:]+$', ipv6_addr)
        if not have_symbol:
            raise forms.ValidationError(_('The ipv6 must not contain any special characters'))
        elif len(ipv6_addr) > 100:
            raise forms.ValidationError(_('The ipv6 must not exceed 100 characters'))
        return ipv6_addr

    def clean_ipv6_gw(self):
        ipv6_gw = self.cleaned_data['ipv6_gw']
        have_symbol = re.match('^[0-9.]+$', ipv6_gw)
        if not have_symbol:
            raise forms.ValidationError(_('The ipv6 gateway must not contain any special characters'))
        elif len(ipv6_gw) > 100:
            raise forms.ValidationError(_('The ipv6 gateway must not exceed 100 characters'))
        return ipv6_gw

    def clean_name(self):
        name = self.cleaned_data['name']
        have_symbol = re.match('^[a-z0-9.]+$', name)
        if not have_symbol:
            raise forms.ValidationError(_('The interface must not contain any special characters'))
        elif len(name) > 10:
            raise forms.ValidationError(_('The interface must not exceed 10 characters'))
        return name

    def clean_netdev(self):
        netdev = self.cleaned_data['netdev']
        have_symbol = re.match('^[a-z0-9.]+$', netdev)
        if not have_symbol:
            raise forms.ValidationError(_('The interface must not contain any special characters'))
        elif len(netdev) > 10:
            raise forms.ValidationError(_('The interface must not exceed 10 characters'))
        return netdev
