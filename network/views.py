# -*- coding: utf-8 -*-
import libvirt, re
import virtinst.util as util
from django.utils.translation import ugettext_lazy as _
from webvirtmgr.network.IPy import IP
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from webvirtmgr.model.models import *

def index(request, host_id):
	
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/user/login')
	
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

	def get_networks():
		try:
			networks = {}
			for name in conn.listNetworks():
				net = conn.networkLookupByName(name)
				status = net.isActive()
				networks[name] = status
			for name in conn.listDefinedNetworks():
				net = conn.networkLookupByName(name)
				status = net.isActive()
				networks[name] = status
			return networks
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

	networks = get_networks()
	all_vm = get_vms()

	if networks == None:
		return HttpResponseRedirect('/overview/%s/' % (host_id))
	elif len(networks) == 0:
		return HttpResponseRedirect('/network/%s/new_net_pool/' % (host_id))
	else:
		return HttpResponseRedirect('/network/%s/%s/' % (host_id, networks.keys()[0]))

def pool(request, host_id, pool):

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
			add_error(e, 'libvirt')
			return "error"

	def get_networks():
		try:
			networks = {}
			for name in conn.listNetworks():
				net = conn.networkLookupByName(name)
				status = net.isActive()
				networks[name] = status
			for name in conn.listDefinedNetworks():
				net = conn.networkLookupByName(name)
				status = net.isActive()
				networks[name] = status
			return networks
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def vm_conn():
		try:
			flags = [libvirt.VIR_CRED_AUTHNAME, libvirt.VIR_CRED_PASSPHRASE]
			auth = [flags, creds, None]
			uri = 'qemu+tcp://' + kvm_host.ipaddr + '/system'
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
			
	def get_conn_pool(pool):
		try:
			net = conn.networkLookupByName(pool)
			return net
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def pool_start():
		try:
			net.create()
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def pool_stop():
		try:
			net.destroy()
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def pool_delete():
		try:
			net.undefine()
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def net_set_autostart(pool):
		try:
			net = conn.networkLookupByName(pool)
			net.setAutostart(1)
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def get_net_info(get):
		try:
			if get == "bridge":
				return net.bridgeName()
			elif get == "status":
				return net.isActive()
			elif get == "start":
				return net.autostart()
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def get_ipv4_net():
		try:
			net = conn.networkLookupByName(pool)
			xml = net.XMLDesc(0)
			addrStr = util.get_xml_path(xml, "/network/ip/@address")
			netmaskStr = util.get_xml_path(xml, "/network/ip/@netmask")

			netmask = IP(netmaskStr)
			gateway = IP(addrStr)

			network = IP(gateway.int() & netmask.int())
			return IP(str(network) + "/" + netmaskStr)
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def get_ipv4_dhcp_range():
		try:
			net = conn.networkLookupByName(pool)
			xml = net.XMLDesc(0)
			dhcpstart = util.get_xml_path(xml, "/network/ip/dhcp/range[1]/@start")
			dhcpend = util.get_xml_path(xml, "/network/ip/dhcp/range[1]/@end")
			if not dhcpstart or not dhcpend:
				return None
			
			return [IP(dhcpstart), IP(dhcpend)]
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def get_ipv4_forward():
		try:
			xml = net.XMLDesc(0)
			fw = util.get_xml_path(xml, "/network/forward/@mode")
			forwardDev = util.get_xml_path(xml, "/network/forward/@dev")
			return [fw, forwardDev]
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def create_net_pool(name_pool, forward, ipaddr, netmask, dhcp, s_dhcp, e_dhcp):
		try:
			xml = """
				<network>
					<name>%s</name>""" % (name_pool)

			if forward == "nat" or "route":
				xml += """<forward mode='%s'/>""" % (forward)

			xml += """<bridge stp='on' delay='0' />
						<ip address='%s' netmask='%s'>""" % (gw_ipaddr, netmask)

			if dhcp == "yes":
				xml += """<dhcp>
							<range start='%s' end='%s' />
						</dhcp>""" % (s_dhcp, e_dhcp)
					
			xml += """</ip>
				</network>"""
			conn.networkDefineXML(xml)
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	conn = vm_conn()

	if conn == None:
		return HttpResponseRedirect('/overview/%s/' % (host_id))

	pools = get_networks()
	all_vm = get_vms()
	errors = []

	if pool != 'new_net_pool':
		net = get_conn_pool(pool)
		bridge = get_net_info('bridge')
		status = get_net_info('status')
		if status == 1:
			start = get_net_info('start')
			network = get_ipv4_net()
			dhcprange = get_ipv4_dhcp_range()
			netmode = get_ipv4_forward()

	if request.method == 'POST':
		if request.POST.get('new_net_pool',''):
			name_pool = request.POST.get('name_pool','')
			net_addr = request.POST.get('net_addr','')
			forward = request.POST.get('forward','')
			dhcp = request.POST.get('dhcp','')
			simbol = re.search('[^a-zA-Z0-9\_]+', name_pool)
			if len(name_pool) > 20:
				msg = _('The name of the network pool must not exceed 20 characters')
				errors.append(msg)
			if simbol:
				msg = _('The name of the network pool must not contain any characters and Russian characters')
				errors.append(msg)
			if not name_pool:
				msg = _('Enter the name of the pool')
				errors.append(msg)
			if not net_addr:
				msg = _('Enter the IP subnet')
				errors.append(msg)
			try:
				netmask = IP(net_addr).strNetmask()
				ipaddr = IP(net_addr)
				gw_ipaddr = ipaddr[1].strNormal()
				start_dhcp = ipaddr[2].strNormal()
				end_dhcp = ipaddr[254].strNormal()
			except:
				msg = _('IP subnet must be 192.168.1.0/24 or 192.168.1.0/26')
				errors.append(msg)
			if errors:
				return render_to_response('network.html', locals())
			if not errors:
				if create_net_pool(name_pool, forward, gw_ipaddr, netmask, dhcp, start_dhcp, end_dhcp) is "error":
					msg = _('Such a pool already exists')
					errors.append(msg)
				if not errors:
					net_set_autostart(name_pool)
					net = get_conn_pool(name_pool)
					if pool_start() is "error":
						msg = _('Pool is created, but when I run the pool fails, you may specify an existing network')
						errors.append(msg)
					else:
						msg = _('Creating a network pool: ') 
						msg = msg + name_pool
						add_error(msg, 'user')
						return HttpResponseRedirect('/network/%s/%s/' % (host_id, name_pool))
					if errors:
						return render_to_response('network.html', locals())
		if request.POST.get('stop_pool',''):
			msg = _('Stop network pool: ')
			msg = msg + pool
			pool_stop()
			add_error(msg, 'user')
		if request.POST.get('start_pool',''):
			msg = _('Start network pool: ')
			msg = msg + pool
			pool_start()
			add_error(msg, 'user')
		if request.POST.get('del_pool',''):
			msg = _('Delete network pool: ')
			msg = msg + pool
			pool_delete()
			add_error(msg, 'user')
			return HttpResponseRedirect('/network/%s/' % (host_id))
		return HttpResponseRedirect('/network/%s/%s/' % (host_id, pool))

	conn.close()

	return render_to_response('network.html', locals())

def redir(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/user/login')
	else:
		return HttpResponseRedirect('/dashboard')
