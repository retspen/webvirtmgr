from django.conf.urls import patterns, include, url
from django.conf import settings

urlpatterns = patterns('',
    url(r'^$', 'dashboard.views.index', name='index'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': 'logout.html'}, name='logout'),
    url(r'^dashboard/$', 'dashboard.views.dashboard', name='dashboard'),
    url(r'^setup/$', 'dashboard.views.page_setup', name='page_setup'),
    url(r'^clusters/$', 'dashboard.views.clusters', name='clusters'),
    url(r'^overview/(\d+)/$', 'overview.views.overview', name='overview'),
    url(r'^newvm/(\d+)/$', 'newvm.views.newvm', name='newvm'),
    url(r'^storage/(\d+)/$', 'storage.views.storage', {'pool': None}, name='storage'),
    url(r'^storage/(\d+)/([\w\-]+)/$', 'storage.views.storage', name='storage'),
    url(r'^network/(\d+)/$', 'network.views.network', {'pool': None}, name='network'),
    url(r'^network/(\d+)/([\w\-]+)/$', 'network.views.network', name='network'),
    url(r'^snapshot/(\d+)/$', 'snapshot.views.snapshot', name='snapshot'),
    url(r'^snapshot/(\d+)/([\w\-]+)/$', 'snapshot.views.dom_snapshot', name='dom_snapshot'),
    url(r'^vds/(\d+)/([\w\-\.]+)/$', 'vds.views.vds', name='vds'),
    url(r'^vnc/(\d+)/([\w\-\.]+)/$', 'vnc.views.vnc', name='vnc'),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT, 'show_indexes': False}),
)
