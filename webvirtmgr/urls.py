from django.conf.urls import patterns, url
from django.conf import settings

urlpatterns = patterns('',
    url(r'^$', 'dashboard.views.index', name='index'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': 'logout.html'}, name='logout'),
    url(r'^servers/$', 'servers.views.servers_list', name='servers_list'),
    url(r'^setup/$', 'servers.views.page_setup', name='page_setup'),
    url(r'^infrastructure/$', 'servers.views.infrastructure', name='infrastructure'),
    url(r'^overview/(\d+)/$', 'overview.views.overview', name='overview'),
    url(r'^create/(\d+)/$', 'create.views.create', name='create'),
    url(r'^storage/(\d+)/$', 'storage.views.storage', {'pool': None}, name='storage'),
    url(r'^storage/(\d+)/([\w\-\.]+)/$', 'storage.views.storage', name='storage'),
    url(r'^network/(\d+)/$', 'network.views.network', {'pool': None}, name='network'),
    url(r'^network/(\d+)/([\w\-\.]+)/$', 'network.views.network', name='network'),
    url(r'^snapshot/(\d+)/$', 'snapshot.views.snapshot', name='snapshot'),
    url(r'^snapshot/(\d+)/([\w\-\.]+)/$', 'snapshot.views.dom_snapshot', name='dom_snapshot'),
    url(r'^instance/(\d+)/([\w\-\.]+)/$', 'instance.views.instance', name='instance'),
    url(r'^console/(\d+)/([\w\-\.]+)/$', 'console.views.console', name='console'),
    url(r'^info/cpu/(\d+)/$', 'overview.views.cpuusage', name='cpuusage'),
    url(r'^info/memory/(\d+)/$', 'overview.views.memusage', name='memusage'),
    url(r'^info/vds/cpu/(\d+)/([\w\-\.]+)/$', 'instance.views.cpuusage', name='vdscpuusage'),
    url(r'^info/vds/net/(\d+)/([\w\-\.]+)/$', 'instance.views.netusage', name='vdsnetusage'),
    url(r'^info/vds/disk/(\d+)/([\w\-\.]+)/$', 'instance.views.diskusage', name='vdsdiskusage'),
)

urlpatterns += patterns('',
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
)
