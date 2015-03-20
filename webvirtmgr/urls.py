from django.conf.urls import patterns, url
from django.conf import settings
from instance.views import InstanceList

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
    url(r'^interfaces/(\d+)/$', 'interfaces.views.interfaces', name='interfaces'),
    url(r'^interface/(\d+)/([\w\.\:]+)/$', 'interfaces.views.interface', name='interface'),
    url(r'^instance/(\d+)/([\w\-\.]+)/$', 'instance.views.instance', name='instance'),
    url(r'^instances/(?P<host_id>[\d]+)/$', InstanceList.as_view(), name='instances'),
    url(r'^secrets/(\d+)/$', 'secrets.views.secrets', name='secrets'),
    url(r'^console/$', 'console.views.console', name='console'),
    url(r'^info/hostusage/(\d+)/$', 'hostdetail.views.hostusage', name='hostusage'),
    url(r'^info/insts_status/(\d+)/$', 'instance.views.insts_status', name='insts_status'),
    url(r'^info/instusage/(\d+)/([\w\-\.]+)/$', 'instance.views.instusage', name='instusage'),
)

urlpatterns += patterns('',
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
)
