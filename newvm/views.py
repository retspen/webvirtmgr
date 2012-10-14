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

	def add_error(msg, type_err):
		error_msg = Log(host_id=host_id, 
			            type=type_err, 
			            message=msg, 
			            user_id=request.user.id
			            )
		error_msg.save()

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
	
	def get_all_stg():
		try:
			storages = []
			for name in conn.listStoragePools():
				storages.append(name)
			for name in conn.listDefinedStoragePools():
				storages.append(name)
			return storages
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def get_all_net():
		try:
			networks = []
			for name in conn.listNetworks():
				networks.append(name)
			for name in conn.listDefinedNetworks():
				networks.append(name)
			# Not support all distro but Fedora!!!
			#for ifcfg in conn.listInterfaces():
			#	if ifcfg != 'lo' and not re.findall("eth", ifcfg):
			#		networks.append(ifcfg)
			#for ifcfg in conn.listDefinedInterfaces():
			#	if ifcfg != 'lo' and not re.findall("eth", ifcfg):
			#		networks.append(ifcfg)
			return networks
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"
	
	def find_all_iso():
		try:
			iso = []
			for storage in storages:
				stg = conn.storagePoolLookupByName(storage)
				stg.refresh(0)
				for img in stg.listVolumes():
					if re.findall(".iso", img) or re.findall(".ISO", img):
						iso.append(img)
			return iso
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def find_all_img():
		try:		
			disk = []
			for storage in storages:
				stg = conn.storagePoolLookupByName(storage)
				stg.refresh(0)
				for img in stg.listVolumes():
					if re.findall(".img", img) or re.findall(".IMG", img):
						disk.append(img)
			return disk
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"
	
	def get_img_path(vol):
		try:
			for storage in storages:
				stg = conn.storagePoolLookupByName(storage)
				for img in stg.listVolumes():
					if vol == img:
						vl = stg.storageVolLookupByName(vol)
						return vl.path()
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def get_img_format(vol):
		try:
			for storage in storages:
				stg = conn.storagePoolLookupByName(storage)
				for img in stg.listVolumes():
					if vol == img:
						vl = stg.storageVolLookupByName(vol)
						xml = vl.XMLDesc(0)
						format = util.get_xml_path(xml, "/volume/target/format/@type")
						return format
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def get_cpus():
		try:
			return conn.getInfo()[2]
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"
	
	def get_mem():
		try:
			return conn.getInfo()[1]
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def get_emulator():
		try:
			emulator = []
			xml = conn.getCapabilities()
			arch = conn.getInfo()[0]
			if arch == 'x86_64':
				emulator.append(util.get_xml_path(xml,"/capabilities/guest[1]/arch/emulator"))
				emulator.append(util.get_xml_path(xml,"/capabilities/guest[2]/arch/emulator"))
			else:
				emulator = util.get_xml_path(xml,"/capabilities/guest/arch/emulator")
			return emulator
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	def get_machine():
		try:
			xml = conn.getCapabilities()
			machine = util.get_xml_path(xml,"/capabilities/guest/arch/machine/@canonical")
			return machine
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"
			
	def create_volume(stg_pool, img, size_max):
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
			stg = conn.storagePoolLookupByName(stg_pool)
			stg.createXML(xml,0)
		except libvirt.libvirtError as e:
			add_error(e,'libvirt')
			return "error"
	
	def add_vm(name, mem, cpus, machine, emul, img, iso, bridge):
		try:
			arch = conn.getInfo()[0]
			if not iso:
				iso = ''
			memaloc = mem
			xml = """<domain type='kvm'>
					  <name>%s</name>
					  <memory>%s</memory>
					  <currentMemory>%s</currentMemory>
					  <vcpu>%s</vcpu>
					  <os>
					    <type arch='%s' machine='%s'>hvm</type>
					    <boot dev='hd'/>
					    <boot dev='cdrom'/>
					    <bootmenu enable='yes'/>
					  </os>
					  <features>
					    <acpi/>
					    <apic/>
					    <pae/>
					  </features>
					  <clock offset='utc'/>
					  <on_poweroff>destroy</on_poweroff>
					  <on_reboot>restart</on_reboot>
					  <on_crash>restart</on_crash>
					  <devices>""" % (name, mem, memaloc, cpus, arch, machine)
				
			if arch == 'x86_64':
				xml += """<emulator>%s</emulator>""" % (emul[1])
			else:
				xml += """<emulator>%s</emulator>""" % (emul)

			xml += """<disk type='file' device='disk'>
					      <driver name='qemu' type='qcow2'/>
					      <source file='%s'/>
					      <target dev='hda' bus='ide'/>
					    </disk>
					    <disk type='file' device='cdrom'>
					      <driver name='qemu' type='raw'/>
					      <source file='%s'/>
					      <target dev='hdc' bus='ide'/>
					      <readonly/>
					    </disk>
					    <controller type='ide' index='0'>
					      <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x1'/>
					    </controller>
					    """ % (img, iso)

			if re.findall("br", bridge):
				xml += """<interface type='bridge'>
						<source bridge='%s'/>""" % (bridge)
			else:
				xml += """<interface type='network'>
						<source network='%s'/>""" % (bridge)
				
			xml += """<address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/>
					    </interface>
					    <input type='tablet' bus='usb'/>
					    <input type='mouse' bus='ps2'/>
					    <graphics type='vnc' port='-1' autoport='yes'/>
					    <video>
					      <model type='cirrus' vram='9216' heads='1'/>
					      <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>
					    </video>
					    <memballoon model='virtio'>
					      <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
					    </memballoon>
					  </devices>
					</domain>"""
			conn.defineXML(xml)
			dom = conn.lookupByName(name)
			dom.setAutostart(1)
		except libvirt.libvirtError as e:
			add_error(e, 'libvirt')
			return "error"

	conn = vm_conn()

	if conn == "error":
		return HttpResponseRedirect('/overview/' + host_id + '/')

	errors = []
	cores = get_cpus()
	all_vm = get_all_vm()
	storages = get_all_stg()
	all_iso = find_all_iso()
	all_img = find_all_img()
	if all_iso is "error" or all_img is "error":
		msg = _('Storage pools are not available or are not active')
		errors.append(msg)	
	bridge = get_all_net()
	if bridge == "error":
		msg = _('Network pools are not available or are not active')
		errors.append(msg)			
	emul = get_emulator()
	machine = get_machine()
	addmem = get_mem()
	
	cpus = []
	for cpu in range(1,cores+1):
		cpus.append(cpu)

	if request.method == 'POST':
		name = request.POST.get('name','')
		setmem = request.POST.get('memory','')
		cpus = request.POST.get('cpus','')
		iso = request.POST.get('iso','')		
		img = request.POST.get('img','')
		netbr = request.POST.get('bridge','')
		setmem = int(setmem) * 1024
		hdd = get_img_path(img)
		cdrom = get_img_path(iso)
		hdd_frmt = get_img_format(img)
		simbol = re.search('[^a-zA-Z0-9\_]+', name)
		if name in all_vm:
			msg = _('This is the name of the virtual machine already exists')
			errors.append(msg)
		if len(name) > 20:
			msg = _('The name of the virtual machine must not exceed 20 characters')
			errors.append(msg)
		if simbol:
			msg = _('The name of the virtual machine must not contain any characters and Russian characters')
			errors.append(msg)
		if not request.POST.get('hdd','') and not img or img == 'error':
			msg = _('Images of the HDD to a virtual machine not available. You need to create an HDD image')
			errors.append(msg)
		if not name:
			msg = _('Enter the name of the virtual machine')
			errors.append(msg)
		if not errors:
			if request.POST.get('hdd',''):
				size = request.POST.get('hdd','')
				stg_pool = request.POST.get('stg_pool','')
				create_volume(stg_pool, name, size)
				img = name + '.img'
				hdd = get_img_path(img)
			add_vm(name, setmem, cpus, machine, emul, hdd, cdrom, netbr)
			msg = _('Creating a virtual machine: ')
			msg = msg + name
			add_error(msg,'user')
			return HttpResponseRedirect('/vm/%s/%s/' % (host_id, name))

	conn.close()

	return render_to_response('newvm.html', locals(), context_instance=RequestContext(request))

def redir(request):
	if not request.user.is_authenticated():
		return HttpResponseRedirect('/')
	else:
		return HttpResponseRedirect('/dashboard/')
