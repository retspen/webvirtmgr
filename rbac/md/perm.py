# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import CsrfViewMiddleware
from django.shortcuts import redirect, HttpResponse
import re


class CheckPermission(MiddlewareMixin):
    """ 用户权限信息校验"""

    def process_request(self, request):
        """请求进入时触发
        1 获取url
        2 获取session
        3 匹配permission
        """
        valid_url_list = ['^/login/?$', '^/admin/?']
        current_url = request.path_info
        for valid_url in valid_url_list:
            if re.match(valid_url, current_url):
                print "valid list pass"
                return None
        permission_list = request.session.get('webvirtmgr_permission_url_list_key')
        if not permission_list:
            print 'no login'
            return redirect('/login')
        else:
            print permission_list
        print permission_list
        match_flag = False
        for url in permission_list:
            print re.match(url, current_url), url, current_url
            if re.match(url, current_url):
                 #'有权限'
                print "permission pass"
                return None
            else:
                pass
        return HttpResponse('没有权限')

    # def process_response(self, request, response):
    #     return None