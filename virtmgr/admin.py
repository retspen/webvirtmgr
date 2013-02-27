from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin
from django.contrib.sites.models import Site
from webvirtmgr.virtmgr.models import *

admin.site.unregister(Group)
admin.site.unregister(User)
admin.site.unregister(Site)


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active',)
    list_filter = ('is_staff', 'is_superuser', 'is_active',)

admin.site.register(User, CustomUserAdmin)
