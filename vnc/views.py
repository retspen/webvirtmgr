import libvirt
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponse, HttpResponseRedirect
import virtinst.util as util
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

def index(request, host_id, vname):

   if not request.user.is_authenticated():
      return HttpResponseRedirect('/')

   usr_id = request.user.id
   kvm_host = Host.objects.get(user=usr_id, id=host_id)
   host_ip = kvm_host.ipaddr

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
      except:
         print "Not connected"

   def get_vm_vnc():
      try:
         xml = dom.XMLDesc(0)
         vnc = util.get_xml_path(xml, "/domain/devices/graphics/@port")
         return vnc
      except:
         print "Get vnc port failed"

   conn = vm_conn(host_ip, creds)
   dom = get_dom(vname)

   if conn == None:
      return HttpResponseRedirect('/overview/%s/' % (host_id))

   vnc_port = get_vm_vnc()
   conn.close()

   return render_to_response('vnc.html', locals())

def redir_two(request, host_id):
   if not request.user.is_authenticated():
      return HttpResponseRedirect('/')
   else:
      return HttpResponseRedirect('/dashboard/')

def redir_one(request):
   if not request.user.is_authenticated():
      return HttpResponseRedirect('/')
   else:
      return HttpResponseRedirect('/')
