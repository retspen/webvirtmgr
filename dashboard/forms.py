from django import forms
from instance.models import Host
from django.utils.translation import ugettext_lazy as _
import re


class HostAddTcpForm(forms.Form):
    name = forms.CharField(max_length=20)
    hostname = forms.CharField(max_length=100)
    login = forms.CharField(max_length=20)
    password1 = forms.CharField(max_length=20)
    password2 = forms.CharField(max_length=20)

    def match_password(self):
        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']
        if password1 != password2:
            raise forms.ValidationError(_('Your password didn\'t match. Please try again.'))
        return password1, password2

    def clean_name(self):
        name = self.cleaned_data['name']
        have_simbol = re.search('[^a-zA-Z0-9_\-\.]+', name)
        if have_simbol:
            raise forms.ValidationError(_('The host name must not contain any special characters'))
        elif len(name) > 20:
            raise forms.ValidationError(_('The host name must not exceed 20 characters'))
        try:
            Host.objects.get(name=name)
        except Host.DoesNotExist:
            return name
        raise forms.ValidationError(_('This host is already connected'))

    def clean_hostname(self):
        hostname = self.cleaned_data['hostname']
        have_simbol = re.search('[^a-z0-9\.\-]+', hostname)
        domain = re.search('[\.]+', hostname)
        wrong_ip = re.search('^0\.|^255\.', hostname)
        if have_simbol or not domain:
            raise forms.ValidationError(_('Hostname must contain only numbers, or the domain name separated by "."'))
        elif wrong_ip:
            raise forms.ValidationError(_('Wrong IP address'))
        try:
            Host.objects.get(hostname=hostname)
        except Host.DoesNotExist:
            return hostname
        raise forms.ValidationError(_('This host is already connected'))


class HostAddSshForm(forms.Form):
    name = forms.CharField(max_length=20)
    hostname = forms.CharField(max_length=100)
    login = forms.CharField(max_length=20)
    port = forms.IntegerField()

    def clean_name(self):
        name = self.cleaned_data['name']
        have_simbol = re.search('[^a-zA-Z0-9_\-\.]+', name)
        if have_simbol:
            raise forms.ValidationError(_('The name of the host must not contain any special characters'))
        elif len(name) > 20:
            raise forms.ValidationError(_('The name of the host must not exceed 20 characters'))
        try:
            Host.objects.get(name=name)
        except Host.DoesNotExist:
            return name
        raise forms.ValidationError(_('This host is already connected'))

    def clean_hostname(self):
        hostname = self.cleaned_data['hostname']
        have_simbol = re.search('[^a-z0-9\.\-]+', hostname)
        domain = re.search('[\.]+', hostname)
        wrong_ip = re.search('^0\.|^255\.', hostname)
        if have_simbol or not domain:
            raise forms.ValidationError(_('Hostname must contain only numbers, or the domain name separated by "."'))
        elif wrong_ip:
            raise forms.ValidationError(_('Wrong IP address'))
        try:
            Host.objects.get(hostname=hostname)
        except Host.DoesNotExist:
            return hostname
        raise forms.ValidationError(_('This host is already connected'))

    def clean_port(self):
        port = self.cleaned_data['port']
        if not port.isdigit():
            raise forms.ValidationError(_('SSH port must be digits'))
        if int(port) <= 21:
            raise forms.ValidationError(_('SSH port must be >= 22'))
        return port
