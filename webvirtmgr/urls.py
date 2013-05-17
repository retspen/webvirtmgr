from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^$', 'dashboard.views.index', name='index'),
    url(r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'template_name': 'logout.html'}, name='logout'),
    url(r'^dashboard/$', 'dashboard.views.dashboard', name='dashboard'),
    url(r'^setup/$', 'dashboard.views.page_setup', name='page_setup'),
    url(r'^clusters/$', 'dashboard.views.clusters', name='clusters'),
    url(r'^overview/(\d+)/$', 'overview.views.overview', name='overview'),

    # url(r'^newvm/(\d+)/$', 'webvirtmgr.virtmgr.views.newvm'),

    # url(r'^storage/(\d+)/$', 'virtmgr.views.storage', {'pool': None}),
    # url(r'^storage/(\d+)/([\w\-]+)/$', 'virtmgr.views.storage'),

    # url(r'^network/(\d+)/$', 'virtmgr.views.network', {'pool': None}),
    # url(r'^network/(\d+)/([\w\-]+)/$', 'virtmgr.views.network'),

    # url(r'^vm/(\d+)/([\w\-\.]+)/$', 'virtmgr.views.vm'),

    # url(r'^vnc/(\d+)/([\w\-\.]+)/$', 'virtmgr.views.vnc'),

    # url(r'^snapshot/(\d+)/$', 'virtmgr.views.snapshot'),
    # url(r'^snapshot/(\d+)/([\w\-]+)/$', 'virtmgr.views.dom_snapshot'),    
)
