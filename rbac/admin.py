# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from models import Permission, Role, UserInfo

# Register your models here.
admin.site.register(Permission)
admin.site.register(Role)
admin.site.register(UserInfo)