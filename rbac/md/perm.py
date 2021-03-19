# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect, render, reverse
import re
from django.conf import settings

class CheckPermission(MiddlewareMixin):
    """ 用户权限信息校验"""

    def process_request(self, request):
        """请求进入时触发
        1 获取url
        2 获取session
        3 匹配permission
        """

        current_url = request.path_info
        for valid_url in settings.VALID_URL_LIST:
            if re.match(valid_url, current_url):
                print "valid list pass"
                return None
        permission_dict = request.session.get(settings.PERMISSION_SESSION_KEY)
        # if permission_dict or not permission_dict.has_keys(request.user.username):
        if permission_dict is None or request.user.username not in permission_dict:
            return redirect(reverse('login'))
        else:
            print permission_dict.keys()
        for dict in permission_dict[request.user.username]:
            print re.match(dict['url'], current_url), dict['url'], current_url, dict['method'], request.method
            if re.match(dict['url'], current_url):
                 #'有权限'
                if dict['method'] == request.method:
                    return None
            else:
                pass
        return render(request, '403.html')

    # def process_response(self, request, response):
    #     return None