from django.conf.urls.defaults import patterns, include, url
from webvirtmgr import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Static pages
    url(r'^$', 'webvirtmgr.pages.views.index'),
    url(r'^docs/$', 'webvirtmgr.pages.views.docs'),
    
    # Host
    url(r'^dashboard/$', 'webvirtmgr.dashboard.views.index'),

    # NewVM
    url(r'^newvm/(\d+)/$', 'webvirtmgr.newvm.views.index'),
    url(r'^newvm/', 'webvirtmgr.newvm.views.redir'),

    # Overview
    url(r'^overview/(\d+)/$', 'webvirtmgr.overview.views.index'),
    url(r'^overview/', 'webvirtmgr.overview.views.redir'),

    # Storage
    url(r'^storage/(\d+)/$', 'webvirtmgr.storage.views.index'),
    url(r'^storage/(\d+)/(\w+)/$', 'webvirtmgr.storage.views.pool'),
    url(r'^storage/', 'webvirtmgr.storage.views.redir'),

    # Network
    url(r'^network/(\d+)/$', 'webvirtmgr.network.views.index'),
    url(r'^network/(\d+)/(\w+)/$', 'webvirtmgr.network.views.pool'),
    url(r'^network/', 'webvirtmgr.network.views.redir'),

    # Snapshot
    url(r'^snapshot/(\d+)/$', 'webvirtmgr.snapshot.views.index'),
    url(r'^snapshot/(\d+)/(\w+)/$', 'webvirtmgr.snapshot.views.snapshot'),
    url(r'^snapshot/', 'webvirtmgr.snapshot.views.redir'),
    
    # Logs
    url(r'^logs/(\d+)/$', 'webvirtmgr.logs.views.logs'),
    url(r'^logs/', 'webvirtmgr.logs.views.redir'),

    # Interfaces
    #url(r'^interfaces/(\w+)/$', 'webvirtmgr.interfaces.views.index'),
    #url(r'^interfaces/(\w+)/(\w+)/$', 'webvirtmgr.interfaces.views.ifcfg'),
    #url(r'^interfaces/', 'webvirtmgr.interfaces.views.redir'),

    # VM
    url(r'^vm/(\d+)/(\w+)/$', 'webvirtmgr.vm.views.index'),
    url(r'^vm/(\d+)/$', 'webvirtmgr.vm.views.redir_two'),
    url(r'^vm/', 'webvirtmgr.vm.views.redir_one'),
    
    # VNC    
    url(r'^vnc/(\d+)/(\w+)/$', 'webvirtmgr.vnc.views.index'),
    url(r'^vnc/(\d+)/$', 'webvirtmgr.vnc.views.redir_two'),
    url(r'^vnc/', 'webvirtmgr.vnc.views.redir_one'),

    # Media
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': False}),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
