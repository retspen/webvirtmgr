# -*- coding: utf-8 -*-
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.utils import translation

def index(request):
	if request.user.is_authenticated():
		return HttpResponseRedirect('/dashboard/')
	else:
		return HttpResponseRedirect('/admin/')

def docs(request):
	return render_to_response('docs.html', locals())
