from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = patterns('',
    url(r'^$', 'servers.views.index', name='index'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': 'logout.html'}, name='logout'),
    url(r'^servers/$', 'servers.views.servers_list', name='servers_list'),
    url(r'^infrastructure/$', 'servers.views.infrastructure', name='infrastructure'),
    url(r'^host/(\d+)/$', 'hostdetail.views.overview', name='overview'),
    url(r'^create/(\d+)/$', 'create.views.create', name='create'),
    url(r'^storages/(\d+)/$', 'storages.views.storages', name='storages'),
    url(r'^storage/(\d+)/([\w\-\.]+)/$', 'storages.views.storage', name='storage'),
    url(r'^networks/(\d+)/$', 'networks.views.networks', name='networks'),
    url(r'^network/(\d+)/([\w\-\.]+)/$', 'networks.views.network', name='network'),
    url(r'^snapshots/(\d+)/$', 'snapshots.views.snapshots', name='snapshots'),
    url(r'^snapshot/(\d+)/([\w\-\.]+)/$', 'snapshots.views.snapshot', name='snapshot'),
    url(r'^instance/(\d+)/([\w\-\.]+)/$', 'instance.views.instance', name='instance'),
    url(r'^instances/(\d+)/$', 'instance.views.instances', name='instances'),
    url(r'^console/$', 'console.views.console', name='console'),
    url(r'^info/cpu/(\d+)/$', 'hostdetail.views.cpuusage', name='cpuusage'),
    url(r'^info/memory/(\d+)/$', 'hostdetail.views.memusage', name='memusage'),
    url(r'^info/inst/cpu/(\d+)/([\w\-\.]+)/$', 'instance.views.cpuusage', name='vdscpuusage'),
    url(r'^info/inst/net/(\d+)/([\w\-\.]+)/$', 'instance.views.netusage', name='vdsnetusage'),
    url(r'^info/inst/disk/(\d+)/([\w\-\.]+)/$', 'instance.views.diskusage', name='vdsdiskusage'),
)

urlpatterns += patterns('',
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
)
