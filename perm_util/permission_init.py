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
    print request.session.get(settings.PERMISSION_SESSION_KEY), "session PERMISSION_SESSION_KEY"
    permission_quiryset = current_user.roles.filter(permissions__isnull=False).values("permissions__method", "permissions__url").distinct()
    permission_list = []
    for item in permission_quiryset:
        permission_list.append({"url": item["permissions__url"], "method": item["permissions__method"]})
    # permission_list = [item["permissions__url"] for item in permission_quiryset]
    if request.session.get(settings.PERMISSION_SESSION_KEY) is None:
        request.session[settings.PERMISSION_SESSION_KEY]= {current_user.username: permission_list}
    else:
        request.session.get(settings.PERMISSION_SESSION_KEY)[current_user.username] = permission_list
    print request.session[settings.PERMISSION_SESSION_KEY]
    menu_quiryset = current_user.roles.filter(menu__isnull=False).values("menu__menuname", "menu__pagename").distinct()
    menu_list = []
    for item in menu_quiryset:
        menu_list.append({"menuname": item["menu__menuname"], "pagename": item["menu__pagename"]})
    if request.session.get(settings.MENU_SESSION_KEY) is None:
        request.session[settings.MENU_SESSION_KEY] = {current_user.username: menu_list}
    else:
        request.session.get(settings.MENU_SESSION_KEY)[current_user.username] = menu_list
    print request.session.get(settings.MENU_SESSION_KEY), "session MENU_SESSION_KEY"

    button_quiryset = current_user.roles.filter(button__isnull=False).values("button__buttonname", "button__pagename").distinct()
    button_list = []
    for item in button_quiryset:
        button_list.append({"buttonname": item["button__buttonname"], "pagename": item["button__pagename"]})
    if request.session.get(settings.BUTTON_SESSION_KEY) is None:
        request.session[settings.BUTTON_SESSION_KEY] = {current_user.username: button_list}
    else:
        request.session.get(settings.BUTTON_SESSION_KEY)[current_user.username] = button_list
    print request.session.get(settings.BUTTON_SESSION_KEY), "session BUTTON_SESSION_KEY"


def get_button_permissions(request):
    url = request.path_info
    # urlname
    pass