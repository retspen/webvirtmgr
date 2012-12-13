from django.conf.urls.defaults import patterns, include, url
from webvirtmgr import settings

urlpatterns = patterns('',
    url(r'^$', 'webvirtmgr.polls.views.index'),

    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': 'logout.html'}),

    url(r'^dashboard/$', 'webvirtmgr.polls.views.dashboard'),

    url(r'^overview/(\d+)/$', 'webvirtmgr.polls.views.overview'),

    url(r'^newvm/(\d+)/$', 'webvirtmgr.polls.views.newvm'),

    url(r'^storage/(\d+)/$', 'polls.views.storage'),
    url(r'^storage/(\d+)/(\w+)/$', 'polls.views.storage_pool'),

    url(r'^network/(\d+)/$', 'polls.views.network'),
    url(r'^network/(\d+)/(\w+)/$', 'polls.views.network_pool'),

    url(r'^vm/(\d+)/(\w+)/$', 'polls.views.vm'),

    url(r'^vnc/(\d+)/(\w+)/$', 'polls.views.vnc'),

    url(r'^snapshot/(\d+)/$', 'polls.views.snapshot'),
    url(r'^snapshot/(\d+)/(\w+)/$', 'polls.views.dom_snapshot'),

    url(r'^setup/$', 'polls.views.page_setup', name='page_setup'),

    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT, 'show_indexes': False}),
)
