# -*- coding: utf-8 -*-
import libvirt, re, time
import virtinst.util as util
from django.shortcuts import render_to_response
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from webvirtmgr.model.models import *
from django.template import RequestContext

def index(request, host_id, vname):

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

   def get_storages():
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

   def get_dom(vname):
      try:
         dom = conn.lookupByName(vname)
         return dom
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

   def get_vm_active():
      try:
         state = dom.isActive()
         return state
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def get_vm_uuid():
      try:
         xml = dom.XMLDesc(0)
         uuid = util.get_xml_path(xml, "/domain/uuid")
         return uuid
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def get_vm_xml():
      try:
         xml = dom.XMLDesc(0)
         xml_spl = xml.split('\n')
         return xml_spl
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def get_vm_mem():
      try:
         xml = dom.XMLDesc(0)
         mem = util.get_xml_path(xml, "/domain/currentMemory")
         mem = int(mem) * 1024
         return mem
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def get_vm_core():
      try:
         xml = dom.XMLDesc(0)
         cpu = util.get_xml_path(xml, "/domain/vcpu")
         return cpu
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def get_vm_vnc():
      try:
         xml = dom.XMLDesc(0)
         vnc = util.get_xml_path(xml, "/domain/devices/graphics/@port")
         return vnc
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def get_vm_hdd():
      try:
         xml = dom.XMLDesc(0)
         hdd_path = util.get_xml_path(xml, "/domain/devices/disk[1]/source/@file")
         hdd_fmt = util.get_xml_path(xml, "/domain/devices/disk[1]/driver/@type")
         #image = re.sub('\/.*\/', '', hdd_path)
         size = dom.blockInfo(hdd_path, 0)[0]
         #return image, size, hdd_fmt
         return hdd_path, size, hdd_fmt
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def get_vm_cdrom():
      try:
         xml = dom.XMLDesc(0)
         cdr_path = util.get_xml_path(xml, "/domain/devices/disk[2]/source/@file")
         if cdr_path:
            #image = re.sub('\/.*\/', '', cdr_path)
            size = dom.blockInfo(cdr_path, 0)[0]
            #return image, cdr_path, size
            return cdr_path, cdr_path, size
         else:
            return cdr_path
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def get_vm_boot_menu():
      try:
         xml = dom.XMLDesc(0)
         boot_menu = util.get_xml_path(xml, "/domain/os/bootmenu/@enable")
         return boot_menu
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"
   
   def get_vm_arch():
      try:
         xml = dom.XMLDesc(0)
         arch = util.get_xml_path(xml, "/domain/os/type/@arch")
         return arch
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def get_vm_nic():
      try:
         xml = dom.XMLDesc(0)
         mac = util.get_xml_path(xml, "/domain/devices/interface/mac/@address")
         nic = util.get_xml_path(xml, "/domain/devices/interface/source/@network")
         if nic is None:
         	nic = util.get_xml_path(xml, "/domain/devices/interface/source/@bridge")
         return mac, nic
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"
      
   def mnt_iso_on(vol):
      try:
         for storage in storages:
            stg = conn.storagePoolLookupByName(storage)
            for img in stg.listVolumes():
               if vol == img:
                  vl = stg.storageVolLookupByName(vol)
         xml = """<disk type='file' device='cdrom'>
                     <driver name='qemu' type='raw'/>
                     <target dev='hdc' bus='ide'/>
                     <source file='%s'/>
                     <readonly/>
                  </disk>""" % vl.path()
         dom.attachDevice(xml)
         xmldom = dom.XMLDesc(0)
         conn.defineXML(xmldom)
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def mnt_iso_off(vol):
      try:
         for storage in storages:
            stg = conn.storagePoolLookupByName(storage)
            for img in stg.listVolumes():
               if vol == img:
                  vl = stg.storageVolLookupByName(vol)
         xml = dom.XMLDesc(0)
         iso = "<disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>\n      <source file='%s'/>" % vl.path()
         xmldom = xml.replace("<disk type='file' device='cdrom'>\n      <driver name='qemu' type='raw'/>", iso)
         conn.defineXML(xmldom)
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def umnt_iso_on():
      try:
         xml = """<disk type='file' device='cdrom'>
                     <driver name="qemu" type='raw'/>
                     <target dev='hdc' bus='ide'/>
                     <readonly/>
                  </disk>"""
         dom.attachDevice(xml)
         xmldom = dom.XMLDesc(0)
         conn.defineXML(xmldom)
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def umnt_iso_off():
      try:
         xml = dom.XMLDesc(0)
         cdrom = get_vm_cdrom()[1]
         xmldom = xml.replace("<source file='%s'/>\n" % cdrom,"")
         conn.defineXML(xmldom)
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
   
   def get_vm_autostart():
      try:
         return dom.autostart()
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def page_refresh():
      try:
         return HttpResponseRedirect('/vm/' + host_id + '/' + vname + '/' )
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def get_vm_state():
      try:
         return dom.info()[0]
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def vm_cpu_usage():
      try:
         nbcore = conn.getInfo()[2]
         cpu_use_ago = dom.info()[4]
         time.sleep(1) 
         cpu_use_now = dom.info()[4]
         diff_usage = cpu_use_now - cpu_use_ago
         cpu_usage = 100 * diff_usage / (1 * nbcore * 10**9L)
         return cpu_usage
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def get_memusage():
      try:
         allmem = conn.getInfo()[1] * 1048576
         dom_mem = dom.info()[1] * 1024
         percent = (dom_mem * 100) / allmem
         return allmem, percent
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def get_all_core():
      try:
         allcore = conn.getInfo()[2]
         return allcore
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def vm_create_snapshot():
      try:
         xml = """<domainsnapshot>\n
                     <name>%d</name>\n
                     <state>shutoff</state>\n
                     <creationTime>%d</creationTime>\n""" % (time.time(), time.time())
         xml += dom.XMLDesc(0)
         xml += """<active>0</active>\n
                  </domainsnapshot>"""
         dom.snapshotCreateXML(xml, 0)
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   def get_snapshot_num():
      try:
         return dom.snapshotNum(0)
      except libvirt.libvirtError as e:
         add_error(e, 'libvirt')
         return "error"

   conn = vm_conn()
   errors = []

   if conn == None:
      return HttpResponseRedirect('/overview/' + host + '/')

   all_vm = get_vms()
   dom = get_dom(vname)
   active = get_vm_active()
   state = get_vm_state()
   uuid = get_vm_uuid()
   memory = get_vm_mem()
   core =  get_vm_core()
   autostart = get_vm_autostart()
   vnc_port = get_vm_vnc()
   hdd = get_vm_hdd()
   boot_menu = get_vm_boot_menu()
   vm_arch = get_vm_arch()
   vm_nic = get_vm_nic()
   cdrom = get_vm_cdrom()
   storages = get_storages()
   isos = find_all_iso()
   all_core = get_all_core()
   cpu_usage = vm_cpu_usage()
   mem_usage = get_memusage()
   num_snapshot = get_snapshot_num()
   vm_xml = get_vm_xml()

   # Post form html
   if request.method == 'POST':
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
      if request.POST.get('snapshot',''):
         try:
            msg = _('Create snapshot for VM: ')
            msg = msg + vname
            add_error(msg, 'user')
            vm_create_snapshot()
            message = _('Successful create snapshot')
            return render_to_response('vm.html', locals(), context_instance=RequestContext(request))
         except libvirt.libvirtError as e:
            add_error(e, 'libvirt')
            msg = _('Error: create snapshot')
            errors.append(msg)
      if request.POST.get('auto_on',''):
         try:
            msg = _('Enable autostart for VM: ')
            msg = msg + vname
            add_error(msg, 'user')
            dom.setAutostart(1)
         except libvirt.libvirtError as e:
            add_error(e, 'libvirt')
            return "error"
      if request.POST.get('auto_off',''):
         try:
            msg = _('Disable autostart for VM: ')
            msg = msg + vname
            add_error(msg, 'user')
            dom.setAutostart(0)
         except libvirt.libvirtError as e:
            add_error(e, 'libvirt')
            return "error"
      if request.POST.get('disconnect',''):
         iso = request.POST.get('iso_img','')
         if state == 1:
            umnt_iso_on()
         else:
            umnt_iso_off()
      if request.POST.get('connect',''):
         iso = request.POST.get('iso_img','')     
         if state == 1:
            mnt_iso_on(iso)
         else:
            mnt_iso_off(iso)
      if request.POST.get('undefine',''):
         try:
            dom.undefine()
            msg = _('Undefine VM: ')
            msg = msg + vname
            add_error(msg, 'user')
            return HttpResponseRedirect('/overview/%s/' % (host_id))
         except libvirt.libvirtError as e:
            add_error(e, 'libvirt')
            return "error"
      if not errors:
         return HttpResponseRedirect('/vm/%s/%s/' % (host_id, vname))
      else:
         return render_to_response('vm.html', locals(), context_instance=RequestContext(request))

   conn.close()
   
   return render_to_response('vm.html', locals(), context_instance=RequestContext(request))

def redir_two(request, host_id):
   if not request.user.is_authenticated():
      return HttpResponseRedirect('/user/login')
   else:
      return HttpResponseRedirect('/dashboard')

def redir_one(request):
   if not request.user.is_authenticated():
      return HttpResponseRedirect('/user/login')
   else:
      return HttpResponseRedirect('/dashboard/')
