from django.conf.urls import url, include
from django.conf.urls.static import static
from django.conf import settings
from servers.views import index,servers_list, infrastructure
from django.contrib.auth import views as auth_views
from hostdetail.views import overview
from create.views import create
from storages.views import storages, storage
from networks.views import networks, network
from interfaces.views import interfaces, interface
from instance.views import instance, instances, insts_status, inst_status, instusage
from secrets.views import secrets
from console.views import console
from hostdetail.views import hostusage
from django.contrib import admin
from rbac.views import login

urlpatterns = [
    url(r'^$', index, name='index'),
    # url(r'^login/$', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    url(r'^login$', login, name='login'),
    url(r'^logout/$',auth_views.LogoutView.as_view(template_name='logout.html'), name='logout'),
    url(r'^servers/$', servers_list, name='servers_list'),
    url(r'^infrastructure/$', infrastructure, name='infrastructure'),
    url(r'^host/(\d+)/$', overview, name='overview'),
    url(r'^create/(\d+)/$', create, name='create'),
    url(r'^storages/(\d+)/$', storages, name='storages'),
    url(r'^storage/(\d+)/([\w\-\.]+)/$', storage, name='storage'),
    url(r'^networks/(\d+)/$', networks, name='networks'),
    url(r'^network/(\d+)/([\w\-\.]+)/$', network, name='network'),
    url(r'^interfaces/(\d+)/$', interfaces, name='interfaces'),
    url(r'^interface/(\d+)/([\w\.\:]+)/$', interface, name='interface'),
    url(r'^instance/(\d+)/([\w\-\.]+)/$', instance, name='instance'),
    url(r'^instances/(\d+)/$', instances, name='instances'),
    url(r'^secrets/(\d+)/$', secrets, name='secrets'),
    url(r'^console/$', console, name='console'),
    url(r'^info/hostusage/(\d+)/$', hostusage, name='hostusage'),
    url(r'^info/insts_status/(\d+)/$', insts_status, name='insts_status'),
    url(r'^info/inst_status/(\d+)/([\w\-\.]+)/$', inst_status, name='inst_status'),
    url(r'^info/instusage/(\d+)/([\w\-\.]+)/$', instusage, name='instusage'),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^admin/',include(admin.site.urls)),
]

# urlpatterns += [
#     (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
# ]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)