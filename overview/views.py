# -*- coding: utf-8 -*-
import libvirt, time
import virtinst.util as util
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from webvirtmgr.model.models import *

def index(request, host_id):

	""" Overview block """

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/user/login/')

	def add_error(msg, type_err):
		error_msg = Log(host_id=host_id, 
                      type=type_err, 
                      message=msg, 
                      user_id=request.user.id
                      )
		error_msg.save()

	kvm_host = Host.objects.get(user=request.user.id, id=host_id)

	def vm_conn():
		flags = [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE]
	  	auth = [flags, creds, None]
		uri = 'qemu+tcp://' + kvm_host.ipaddr + '/system'
		try:
		   	conn = libvirt.openAuth(uri, auth, 0)
		   	return conn
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
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

	def get_all_vm():
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
			add_error(e, 'libvirt')
			return "error"

	def get_info():
		try:
			info = []
			xml_inf = conn.getSysinfo(0)
			info.append(conn.getHostname())
			info.append(conn.getInfo()[0])
			info.append(conn.getInfo()[2])
			info.append(util.get_xml_path(xml_inf, "/sysinfo/processor/entry[6]"))
			return info
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def get_mem_usage():
		try:
			allmem = conn.getInfo()[1] * 1048576
			get_freemem = conn.getMemoryStats(-1,0)
			if type(get_freemem) == dict:
				freemem = (get_freemem.values()[0] + get_freemem.values()[2] + get_freemem.values()[3]) * 1024
				percent = (freemem * 100) / allmem
				percent = 100 - percent
				memusage = (allmem - freemem)
			else:
				memusage = None
				percent = None
			return allmem, memusage, percent
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def get_cpu_usage():
		try:
			prev_idle = 0
			prev_total = 0
			cpu = conn.getCPUStats(-1,0)
			if type(cpu) == dict:
				for num in range(2):
				        idle = conn.getCPUStats(-1,0).values()[1]
				        total = sum(conn.getCPUStats(-1,0).values())
				        diff_idle = idle - prev_idle
				        diff_total = total - prev_total
				        diff_usage = (1000 * (diff_total - diff_idle) / diff_total + 5) / 10
				        prev_total = total
				        prev_idle = idle
				        if num == 0: 
			        		time.sleep(1)
			        	else:
			        		if diff_usage < 0:
			        			diff_usage = 0
			else:
				diff_usage = None
			return diff_usage
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"
	
	def get_dom(vname):
		try:
			dom = conn.lookupByName(vname)
			return dom
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	errors = []

	if request.method == 'POST':
		login_kvm = request.POST.get('login_kvm','')
		passwd_kvm = request.POST.get('passwd_kvm','')
		if login_kvm or passwd_kvm:
			request.session['login_kvm'] = login_kvm 
			request.session['passwd_kvm'] = passwd_kvm
			return HttpResponseRedirect('/overview/%s/' % (host_id))
		vname = request.POST.get('vname','')
		if vname:
			conn = vm_conn()
			dom = get_dom(vname)
		if request.POST.get('suspend',''):
			try:
				dom.suspend()
				msg = _('Suspend VM: ')
				msg = msg + vname
				add_error(msg, 'user')
			except libvirt.libvirtError as e:
				add_error(e, 'libvirt')
				msg = _('Error: VM alredy suspended')
				errors.append(msg)
		if request.POST.get('resume',''):
			try:
				dom.resume()
				msg = _('Resume VM: ')
				msg = msg + vname
				add_error(msg, 'user')
			except libvirt.libvirtError as e:
				add_error(e, 'libvirt')
				msg = _('Error: VM alredy resume')
				errors.append(msg)
		if request.POST.get('start',''):
			try:
				dom.create()
				msg = _('Start VM: ')
				msg = msg + vname
				add_error(msg, 'user')
			except libvirt.libvirtError as e:
				add_error(e, 'libvirt')
				msg = _('Error: VM alredy start')
				errors.append(msg)
		if request.POST.get('shutdown',''):
			try:
				dom.shutdown()
				msg = _('Shutdown VM: ')
				msg = msg + vname
				add_error(msg, 'user')
			except libvirt.libvirtError as e:
				add_error(e, 'libvirt')
				msg = _('Error: VM alredy shutdown')
				errors.append(msg)
		if request.POST.get('destroy',''):
			try:
				dom.destroy()
				msg = _('Force shutdown VM: ')
				msg = msg + vname
				add_error(msg, 'user')
			except libvirt.libvirtError as e:
				add_error(e, 'libvirt')
				msg = _('Error: VM alredy shutdown')
				errors.append(msg)
            
		if not errors:
			return HttpResponseRedirect('/overview/%s/' % (host_id))

	conn = vm_conn()

	if conn != "error":
		all_vm = get_all_vm()
		host_info = get_info()
		mem_usage = get_mem_usage()
		cpu_usage = get_cpu_usage()
		lib_virt_ver = conn.getLibVersion()
		conn_type = conn.getURI()
		conn.close()
	else:
		msg = _('Error connecting: Check the KVM login and KVM password')
		errors.append(msg)
		
	return render_to_response('overview.html', locals())

def redir(request):
	""" redirect if not have in request host_id """
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/user/login/')
	else:
		return HttpResponseRedirect('/dashboard/')
