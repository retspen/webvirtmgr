import libvirt
import virtinst.util as util
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
from webvirtmgr.model.models import *

def vm_conn(host_ip, creds):
   	try:
		flags = [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE]
  		auth = [flags, creds, None]
		uri = 'qemu+tcp://' + host_ip + '/system'
	   	conn = libvirt.openAuth(uri, auth, 0)
	   	return conn
	except:
		print "Not connected"

def get_interfaces(conn):
	try:
		interfaces = []
		for name in conn.listInterfaces():
			interfaces.append(name)
		for name in conn.listDefinedInterfaces():
			interfaces.append(name)
		return interfaces
	except:
		print "Get interface failed"

def index(request, host):
	
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	
 	usr_id = request.user.id
	kvm_host = Host.objects.get(user=usr_id,hostname=host)
	usr_name = request.user
	host_ip = kvm_host.ipaddr

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

	conn = vm_conn(host_ip, creds)
	interfaces = get_interfaces(conn)

	if interfaces == None:
		return HttpResponseRedirect('/overview/' + host + '/')
	else:
		return HttpResponseRedirect('/interfaces/' + host + '/' + interfaces[0] + '/')

def ifcfg(request, host, face):

	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')

 	usr_id = request.user.id
	usr_name = request.user
	kvm_host = Host.objects.get(user=usr_id,hostname=host)

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

 	def get_ifcfg(face):
		ifcfg = conn.interfaceLookupByName(face)
		return ifcfg
	
	def get_status():
		return ifcfg.isActive()

	def get_mac():
		return ifcfg.MACString()

	def get_ip():
		xml = ifcfg.XMLDesc(0)
		ip = util.get_xml_path(xml, "/interface/protocol/ip/@address")
		return ip

	def get_eth():
		xml = ifcfg.XMLDesc(0)
		eth = util.get_xml_path(xml, "/interface/bridge/interface/@name")
		return eth

	conn = vm_conn(host_ip, creds)

	if conn == None:
		return HttpResponseRedirect('/overview/' + host + '/')

	interfaces = get_interfaces(conn)
	ifcfg = get_ifcfg(face)
	status = get_status()
	mac = get_mac()
	ipaddr = get_ip()
	bridge = get_eth()
	conn.close()

	return render_to_response('interfaces.html', locals())

def redir(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	else:
		return HttpResponseRedirect('/hosts')
