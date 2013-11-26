from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = patterns('',
    url(r'^$', 'servers.views.index', name='index'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': 'logout.html'}, name='logout'),
    url(r'^servers/$', 'servers.views.servers_list', name='servers_list'),
    url(r'^infrastructure/$', 'servers.views.infrastructure', name='infrastructure'),
    url(r'^overview/(\d+)/$', 'overview.views.overview', name='overview'),
    url(r'^create/(\d+)/$', 'create.views.create', name='create'),
    url(r'^storages/(\d+)/$', 'storages.views.storage', {'pool': None}, name='storage'),
    url(r'^storages/(\d+)/([\w\-\.]+)/$', 'storages.views.storage', name='storage'),
    url(r'^networks/(\d+)/$', 'networks.views.network', {'pool': None}, name='network'),
    url(r'^networks/(\d+)/([\w\-\.]+)/$', 'networks.views.network', name='network'),
    url(r'^snapshots/(\d+)/$', 'snapshots.views.snapshot', name='snapshot'),
    url(r'^snapshots/(\d+)/([\w\-\.]+)/$', 'snapshots.views.dom_snapshot', name='dom_snapshot'),
    url(r'^instances/(\d+)/([\w\-\.]+)/$', 'instances.views.instance', name='instance'),
    url(r'^console/(\d+)/([\w\-\.]+)/$', 'console.views.console', name='console'),
    url(r'^info/cpu/(\d+)/$', 'overview.views.cpuusage', name='cpuusage'),
    url(r'^info/memory/(\d+)/$', 'overview.views.memusage', name='memusage'),
    url(r'^info/vds/cpu/(\d+)/([\w\-\.]+)/$', 'instances.views.cpuusage', name='vdscpuusage'),
    url(r'^info/vds/net/(\d+)/([\w\-\.]+)/$', 'instances.views.netusage', name='vdsnetusage'),
    url(r'^info/vds/disk/(\d+)/([\w\-\.]+)/$', 'instances.views.diskusage', name='vdsdiskusage'),
)

urlpatterns += patterns('',
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
)
