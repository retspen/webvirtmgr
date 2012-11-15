# -*- coding: utf-8 -*-
import libvirt, re
import virtinst.util as util
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

	def get_storages():
		try:
			storages = {}
			for name in conn.listStoragePools():
				stg = conn.storagePoolLookupByName(name)
				status = stg.isActive()
				storages[name] = status
			for name in conn.listDefinedStoragePools():
				stg = conn.storagePoolLookupByName(name)
				status = stg.isActive()
				storages[name] = status
			return storages
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

	storages = get_storages()
	all_vm = get_vms()

	if storages == None:
		return HttpResponseRedirect('/overview/%s/' % (host_id))
	elif len(storages) == 0:
		return HttpResponseRedirect('/storage/%s/new_stg_pool/' % (host_id))
	else:
		return HttpResponseRedirect('/storage/%s/%s/' % (host_id, storages.keys()[0]))

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

	def get_storages():
		try:
			storages = {}
			for name in conn.listStoragePools():
				stg = conn.storagePoolLookupByName(name)
				status = stg.isActive()
				storages[name] = status
			for name in conn.listDefinedStoragePools():
				stg = conn.storagePoolLookupByName(name)
				status = stg.isActive()
				storages[name] = status
			return storages
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
			stg = conn.storagePoolLookupByName(pool)
			return stg
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def pool_start():
		try:
			stg.create(0)
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def pool_stop():
		try:
			stg.destroy()
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def pool_delete():
		try:
			stg.undefine()
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"
			
	def pool_refresh():
		try:
			stg.refresh(0)
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def get_stg_info(get):
		try:
			if get == "info":
				if stg.info()[3] == 0:
					percent = 0
				else:
					percent = (stg.info()[2] * 100) / stg.info()[1]
				stg_info = stg.info()
				stg_info.append(percent)
				return stg_info
			elif get == "status":
				return stg.isActive()
			elif get == "start":
				return stg.autostart()
			elif get == "list":
				return stg.listVolumes()
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def get_type():
		try:
			xml = stg.XMLDesc(0)
			return util.get_xml_path(xml, "/pool/@type")
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def get_target_path():
		try:
			xml = stg.XMLDesc(0)
			return util.get_xml_path(xml, "/pool/target/path")
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def delete_volume(img):
		try:
			vol = stg.storageVolLookupByName(img)
			vol.delete(0)
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def stg_set_autostart(pool):
		try:
			stg = conn.storagePoolLookupByName(pool)
			stg.setAutostart(1)
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def create_volume(img, size_max):
		try:
			size_max = int(size_max) * 1073741824
			xml = """
				<volume>
					<name>%s.img</name>
					<capacity>%s</capacity>
					<allocation>0</allocation>
					<target>
						<format type='qcow2'/>
					</target>
				</volume>""" % (img, size_max)
			stg.createXML(xml,0)
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def create_stg_pool(name_pool, path_pool):
		try:
			xml = """
				<pool type='dir'>
					<name>%s</name>
						<target>
							<path>%s</path>
						</target>
				</pool>""" % (name_pool, path_pool)
			conn.storagePoolDefineXML(xml,0)
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def clone_volume(img, new_img):
		try:
			vol = stg.storageVolLookupByName(img)
			xml = """
				<volume>
					<name>%s</name>
					<capacity>0</capacity>
					<allocation>0</allocation>
					<target>
						<format type='qcow2'/>
					</target>
				</volume>""" % (new_img)
			stg.createXMLFrom(xml, vol, 0)
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"

	def get_vl_info(listvol):
		try:
			volinfo = {}
			if stg.isActive() != 0:
				for name in listvol:
					vol = stg.storageVolLookupByName(name)
					xml = vol.XMLDesc(0)
					size = vol.info()[1]
					format = util.get_xml_path(xml, "/volume/target/format/@type")
	 				volinfo[name] = size,format
			return volinfo
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"
	
	conn = vm_conn()
	errors = []

	if conn == "error":
		return HttpResponseRedirect('/overview/%s/' % (host_id))

	pools = get_storages()
	all_vm = get_vms()
	
	if pool != 'new_stg_pool':
		stg = get_conn_pool(pool)
		status = get_stg_info('status')
		if status == 1:
			pool_refresh()
			info = get_stg_info('info')
			stype = get_type()
			spath = get_target_path()
			start = get_stg_info('start')
			listvol = get_stg_info('list')
			volinfo = get_vl_info(listvol)
			hdd_size = range(1,321)
		errors = []

	if request.method == 'POST':
		if request.POST.get('new_stg_pool',''):
			name_pool = request.POST.get('name_pool','')
			path_pool = request.POST.get('path_pool','')
			simbol = re.search('[^a-zA-Z0-9\_]+', name_pool)
			if len(name_pool) > 20:
				msg = _('The name of the storage pool must not exceed 20 characters')
				errors.append(msg)
			if simbol:
				msg = _('The name of the storage pool must not contain any characters and Russian characters')
				errors.append(msg)
			if not name_pool:
				msg = _('Enter the name of the pool')
				errors.append(msg)
			if not path_pool:
				msg = _('Enter the path of the pool')
				errors.append(msg)
			if not errors:
				if create_stg_pool(name_pool, path_pool) is "error":
					msg = _('Such a pool already exists')
					errors.append(msg)
				else:
					stg = get_conn_pool(name_pool)
					stg_set_autostart(name_pool)
					if pool_start() is "error":
						msg = _('Pool is created, but when I run the pool fails, you may specify the path does not exist')
						errors.append(msg)
						return HttpResponseRedirect('/storage/%s/%s/' % (host_id, name_pool))
					else:
						msg = _('Creating a storage pool: ')
						msg = msg + name_pool
						add_error(msg,'user')
						return HttpResponseRedirect('/storage/%s/%s/' % (host_id, name_pool))
				if errors:
					return render_to_response('storage.html', locals(), context_instance=RequestContext(request))
		if request.POST.get('stop_pool',''):
			pool_stop()
			msg = _('Stop storage pool: ')
			msg = msg + pool
			add_error(msg,'user')
			return HttpResponseRedirect('/storage/%s/%s/' % (host_id, pool))
		if request.POST.get('start_pool',''):
			pool_start()
			msg = _('Start storage pool: ')
			msg = msg + pool
			add_error(msg,'user')
			return HttpResponseRedirect('/storage/%s/%s/' % (host_id, pool))
		if request.POST.get('del_pool',''):
			pool_delete()
			msg = _('Delete storage pool: ')
			msg = msg + pool
			add_error(msg,'user')
			return HttpResponseRedirect('/storage/%s/' % (host_id))
		if request.POST.get('vol_del',''):
			img = request.POST['img']
			delete_volume(img)
			msg = _('Delete image: ')
			msg = msg + img
			add_error(msg,'user')
			return HttpResponseRedirect('/storage/%s/%s/' % (host_id, pool))
		if request.POST.get('vol_add',''):
			img = request.POST.get('img','')
			size_max = request.POST.get('size_max','')
			simbol = re.search('[^a-zA-Z0-9\_]+', img)
			if len(img) > 20:
				msg = _('The name of the images must not exceed 20 characters')
				errors.append(msg)
			if simbol:
				msg = _('The name of the image must not contain any characters and Russian characters')
				errors.append(msg)
			if not img:
				msg = _('Enter image name')
				errors.append(msg)
			if not size_max:
				msg = _('Enter image size')
				errors.append(msg)
			if not errors:
				create_volume(img, size_max)
				msg = _('Create image: ')
				msg = msg + img + '.img'
				add_error(msg,'user')
				return HttpResponseRedirect('/storage/%s/%s/' % (host_id, pool))
		if request.POST.get('vol_clone',''):
			img = request.POST.get('img','')
			new_img = request.POST.get('new_img','')
			simbol = re.search('[^a-zA-Z0-9\_]+', new_img)
			new_img = new_img + '.img'
			if new_img == '.img':
				msg = _('Enter image name')
				errors.append(msg)
			if len(new_img) > 20:
				msg = _('The name of the images must not exceed 20 characters')
				errors.append(msg)
			if simbol:
				msg = _('The name of the image must not contain any characters and Russian characters')
				errors.append(msg)
			if new_img in listvol:
				msg = _('The image of the same name already exists')
				errors.append(msg)
			if re.search('.ISO', img) or re.search('.iso', img):
				msg = _('You can only clone a virtual machine images')
				errors.append(msg)
			if not errors:
				clone_volume(img, new_img)
				msg = _('Cloning image: ')
				msg = msg + img + ' => ' + new_img
				add_error(msg,'user')
				return HttpResponseRedirect('/storage/%s/%s/' % (host_id, pool))

	conn.close()
				
	return render_to_response('storage.html', locals(), context_instance=RequestContext(request))

def redir(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	else:
		return HttpResponseRedirect('/dashboard/')