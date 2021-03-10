# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, HttpResponse, redirect
from models import UserInfo, Role, Permission

# Create your views here.
def login(request):
    if request.method == "GET":
        return render(request, 'login2.html')

    user = request.POST.get('username')
    pwd = request.POST.get('password')
    next = request.POST.get('next')
    obj = UserInfo.objects.filter(name=user, password=pwd).first()
    if not obj:
        print "there is no permissions"
        return render(request, 'login2.html', {'msg': 'user or password invalid'})
    permission_quiryset = obj.roles.filter(permissions__isnull=False).values("permissions__id", "permissions__url").distinct()
    print obj, permission_quiryset
    # permission_list = []
    # for item in permission_quiryset:
    #     permission_list.append(item["permissions_url"])

    permission_list = [ item["permissions__url"] for item in permission_quiryset]
    request.session["webvirtmgr_permission_url_list_key"] = permission_list
    return redirect(next)