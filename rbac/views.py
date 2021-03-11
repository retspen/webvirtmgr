# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render, redirect
from models import UserInfo
from rbac.permission_init import init_permission
from django.contrib.auth import  login as login_func, logout as logout_func

# Create your views here.


def login(request):
    if request.method == "GET":
        return render(request, 'login2.html')

    user = request.POST.get('username')
    pwd = request.POST.get('password')
    next = request.POST.get('next')
    obj = UserInfo.objects.filter(username=user).first()
    if not obj:
        print 'obj is empty', user, pwd, obj
        return render(request, 'login2.html', {'msg': 'user or password invalid'})
    # form.error 需要研究。

    init_permission(request, obj)
    print 'next login'
    login_func(request, obj)
    print 'redirct login'
    return redirect(next)


def logout(request):
    logout_func(request)
    return redirect('/login')