# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings

def init_permission(request, current_user):
    """
    用户权限的初始化
    :param current_user : 当前用户对象
    :param request: 请求所有相关属性
    :return:
    """
    print current_user
    permission_quiryset = current_user.roles.filter(permissions__isnull=False).values("permissions__id", "permissions__url").distinct()
    # permission_list = []
    # for item in permission_quiryset:
    #     permission_list.append(item["permissions_url"])
    permission_list = [item["permissions__url"] for item in permission_quiryset]
    request.session[settings.PERMISSION_SESSION_KEY] = permission_list

def del_permission(request, current_user):
    pass