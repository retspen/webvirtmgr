# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect, HttpResponse
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
        permission_list = request.session.get(settings.PERMISSION_SESSION_KEY)
        if not permission_list:
            return redirect('/login')
        else:
            print permission_list
        for url in permission_list:
            print re.match(url, current_url), url, current_url
            if re.match(url, current_url):
                 #'有权限'
                return None
            else:
                pass
        return HttpResponse('没有权限')

    # def process_response(self, request, response):
    #     return None