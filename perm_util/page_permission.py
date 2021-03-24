# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.urls import resolve
from django.conf import settings


def get_menus(request):
    urlname = resolve(request.path_info).url_name
    menu_permission_list = []
    menu_list = request.session.get(settings.MENU_SESSION_KEY)[request.user.username]
    print "menu", urlname, request.user.username, menu_list
    for menu in menu_list:
        if menu['pagename'] == urlname:
            menu_permission_list.append(menu['menuname'])
    return menu_permission_list


def get_buttons(request):
    urlname = resolve(request.path_info).url_name
    button_permission_list = []
    button_list = request.session.get(settings.BUTTON_SESSION_KEY)[request.user.username]
    print "button", urlname, request.user.username, button_list
    for button in button_list:
        if button['pagename'] == urlname:
            button_permission_list.append(button['buttonname'])
    return button_permission_list
