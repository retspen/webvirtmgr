from django.contrib import admin
from django.contrib.admin.options import ModelAdmin
from models import Instance


class InstanceAdmin(ModelAdmin):
    pass

admin.site.register(Instance, InstanceAdmin)
