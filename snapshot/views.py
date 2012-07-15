# -*- coding: utf-8 -*-
from datetime import datetime
import libvirt
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from webvirtmgr.model.models import *
from django.template import RequestContext

def index(request, host_id):
	
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	
	kvm_host = Host.objects.get(user=request.user.id, id=host_id)

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

	def get_vm_snapshots():
	   	try:
	   		vname = {}
	   		for id in conn.listDomainsID():
	   			id = int(id)
	   			dom = conn.lookupByID(id)
	   			if dom.snapshotNum(0) != 0:
					vname[dom.name()] = dom.info()[0]
			for id in conn.listDefinedDomains():
				dom = conn.lookupByName(id)
				if dom.snapshotNum(0) != 0:
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

	if conn == "error":
		return HttpResponseRedirect('/overview/%s/' % (host_id))

	all_vm_snap = get_vm_snapshots()
	all_vm = get_vms()

	if all_vm_snap:
		return HttpResponseRedirect('/snapshot/%s/%s/' % (host_id, all_vm_snap.keys()[0]))

	return render_to_response('snapshot.html', locals(), context_instance=RequestContext(request))

def snapshot(request, host_id, vname):

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')

	kvm_host = Host.objects.get(user=request.user.id, id=host_id)

	def add_error(msg, type_err):
		error_msg = Log(host_id=host_id, 
			            type=type_err, 
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
			add_error(e,'libvirt')
			return "error"

	def get_vm_snapshots():
		try:
			vname = {}
			for id in conn.listDomainsID():
				id = int(id)
				dom = conn.lookupByID(id)
				if dom.snapshotNum(0) != 0:
					vname[dom.name()] = dom.info()[0]
			for id in conn.listDefinedDomains():
				dom = conn.lookupByName(id)
				if dom.snapshotNum(0) != 0:
					vname[dom.name()] = dom.info()[0]
			return vname
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def vm_conn():
	   	try:
			flags = [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE]
	  		auth = [flags, creds, None]
			uri = 'qemu+tcp://' + kvm_host.ipaddr + '/system'
		   	conn = libvirt.openAuth(uri, auth, 0)
		   	return conn
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
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

	def get_dom(vname):
		try:
			dom = conn.lookupByName(vname)
			return dom
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def get_snapshots():
		try:
			snapshots = {}
			all_snapshot = dom.snapshotListNames(0)
			for snapshot in all_snapshot:
				snapshots[snapshot] = (datetime.fromtimestamp(int(snapshot)), dom.info()[0])
			return snapshots
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def del_snapshot(name_snap):
		try:
			snap = dom.snapshotLookupByName(name_snap,0)
			snap.delete(0)
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def revert_snapshot(name_snap):
		try:
			snap = dom.snapshotLookupByName(name_snap,0)
			dom.revertToSnapshot(snap,0)
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	conn = vm_conn()
	all_vm_snapshots = get_vm_snapshots()
	dom = get_dom(vname)
	vm_snapshot = get_snapshots()
	all_vm = get_vms()

	if not vm_snapshot:
		return HttpResponseRedirect('/snapshot/%s/' % (host_id))

	if request.method == 'POST':
		if request.POST.get('delete',''):
			name = request.POST.get('name','')
			msg = _('Delete snapshot VM: ')
			msg = msg + vname + ' => ' + name
			add_error(msg,'user')
			del_snapshot(name)
			return HttpResponseRedirect('/snapshot/%s/%s/' % (host_id, vname))
		if request.POST.get('revert',''):
			name = request.POST.get('name','')
			msg = _('Revert snapshot VM: ')
			msg = msg + vname + ' => ' + name
			add_error(msg,'user')
        	revert_snapshot(name)
        	message = _('Successful revert snapshot: ')
        	message = message + name

	conn.close()

	return render_to_response('snapshot.html', locals(), context_instance=RequestContext(request))

def redir(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/user/login')
	else:
		return HttpResponseRedirect('/dashboard')