# -*- coding: utf-8 -*-
import libvirt
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from webvirtmgr.model.models import *

def redir(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/user/login/')
	else:
		return HttpResponseRedirect('/dashboard/')

def logs(request, host_id):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/user/login/')

	kvm_host = Host.objects.get(user=request.user.id, id=host_id)
	all_logs = Log.objects.filter(host=host_id, user=request.user.id).order_by('-date')[:50]

	def add_error(msg):
		error_msg = Log(host_id=host_id, 
						type='libvirt', 
						message=msg, 
						user_id=request.user.id
						)
		error_msg.save()

	def get_vms():
		try:
			vname = {}
			for id in conn.listDomainsID():
				id = int(id)
				dom = conn.lookupByID(id)
				vname[dom.name()] = dom.info()[0]
			for id in conn.listDefinedDomains():
				dom = conn.lookupByName(id)
				vname[dom.name()] = dom.info()[0]
			return vname
		except libvirt.libvirtError as e:
			add_error(e)
			return "error"

	def vm_conn():
	   	try:
			flags = [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE]
	  		auth = [flags, creds, None]
			uri = 'qemu+tcp://' + kvm_host.ipaddr + '/system'
		   	conn = libvirt.openAuth(uri, auth, 0)
		   	return conn
		except libvirt.libvirtError as e:
			add_error(e)
			return "error"

	if not kvm_host.login or not kvm_host.passwd:
		def creds(credentials, user_data):
			for credential in credentials:
				if credential[0] == libvirt.VIR_CRED_AUTHNAME:
					credential[4] = request.session['login_kvm']
					if len(credential[4]) == 0:
						credential[4] = credential[3]
				elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
					credential[4] = request.session['passwd_kvm']
				else:
					return -1
			return 0
	else:
		def creds(credentials, user_data):
			for credential in credentials:
				if credential[0] == libvirt.VIR_CRED_AUTHNAME:
					credential[4] = kvm_host.login
					if len(credential[4]) == 0:
						credential[4] = credential[3]
				elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
					credential[4] = kvm_host.passwd
				else:
					return -1
			return 0

	conn = vm_conn()

	if conn != "error":
		all_vm = get_vms()

	return render_to_response('logs.html', locals())