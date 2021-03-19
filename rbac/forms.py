# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django import forms


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField()
