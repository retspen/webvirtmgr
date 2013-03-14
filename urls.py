from django.conf.urls.defaults import patterns, include, url
from webvirtmgr import settings

urlpatterns = patterns('',
    url(r'^$', 'webvirtmgr.virtmgr.views.index'),

    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': 'logout.html'}),

    url(r'^dashboard/$', 'webvirtmgr.virtmgr.views.dashboard'),

    url(r'^clusters/$', 'webvirtmgr.virtmgr.views.clusters'),

    url(r'^overview/(\d+)/$', 'webvirtmgr.virtmgr.views.overview'),

    url(r'^newvm/(\d+)/$', 'webvirtmgr.virtmgr.views.newvm'),

    url(r'^storage/(\d+)/$', 'virtmgr.views.storage', {'pool': None}),
    url(r'^storage/(\d+)/([\w\-]+)/$', 'virtmgr.views.storage'),

    url(r'^network/(\d+)/$', 'virtmgr.views.network', {'pool': None}),
    url(r'^network/(\d+)/([\w\-]+)/$', 'virtmgr.views.network'),

    url(r'^vm/(\d+)/([\w\-\.]+)/$', 'virtmgr.views.vm'),

    url(r'^vnc/(\d+)/([\w\-\.]+)/$', 'virtmgr.views.vnc'),

    url(r'^snapshot/(\d+)/$', 'virtmgr.views.snapshot'),
    url(r'^snapshot/(\d+)/([\w\-]+)/$', 'virtmgr.views.dom_snapshot'),

    url(r'^setup/$', 'virtmgr.views.page_setup', name='page_setup'),

    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT, 'show_indexes': False}),
)
