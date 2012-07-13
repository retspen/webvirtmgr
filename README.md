Version 2.6:
- bugfix
- manual authtorization when manage host
- fix templates

Version 2.5:
- bugfix
- add template for new VM
- new design control VM
- fix translate

Version 2.4:
- bugfix
- add gettext (russian)
- change template

Version 2.3:
- bugfix
- add logs
- change templates

Version 2.2:
- fix template
- add exceptions for all operation
- add support qemu without kvm

Version 2.1:
- fix bootstrap height (text input)

Version 2.0:
- new design build on bootstrap
- delete interfaces for ubuntu support
- optimized code

Version 1.0.1a:

WebVirtMgr is a libvirt-based Web interface for managing virtual machines. It allows you to create and configure new domains, and adjust a domain's resource allocation. A VNC viewer over a SSH tunnel presents a full graphical console to the guest domain. KVM is currently the only hypervisor supported

Technology:

The application logic is written in Python & Django. The LIBVIRT Python bindings 
are used to interacting with the underlying hypervisor. KVM primary supported platform.
