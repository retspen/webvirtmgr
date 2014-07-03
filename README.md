# WebVirtMgr panel - v4.8.4

### Whats new?

* Added page interfaces
* Added novnc proxy supporting new websockify versions (Thanks: <a href="https://github.com/casell">casell</a>)
* Added support CEPH
* Added instance creating from XML
* Added support <a href="http://libvirt.org/remote.html#Remote_certificates">TLS</a> connection (Thanks: <a href="https://github.com/junkb">junkb</a>)
* <a href="https://github.com/ITBlogger/puppet-kvm">Puppet module to control libvirt/kvm</a> (Thanks: <a href="https://github.com/ITBlogger">Alex Scoble</a>)
* <a href="https://github.com/retspen/webvirtmgr/tree/master/deploy/fabric">Deployment via Fabric/Fabtools</a> (Thanks: <a href="https://github.com/mohabusama">Mohab Usama</a>)
* Added instance cloning (Settings -> Clone)

### <a href="https://github.com/retspen/webvirtmgr/wiki/Screenshots">Screenshots</a>

## Introduction

WebVirtMgr is a libvirt-based Web interface for managing virtual machines. It allows you to create and configure new domains, and adjust a domain's resource allocation. A VNC viewer presents a full graphical console to the guest domain. KVM is currently the only hypervisor supported.

### Technology:

The application logic is written in Python & Django. The LIBVIRT Python bindings are used to interacting with the underlying hypervisor.

## Installation (Only web panel)

### <a href="https://github.com/retspen/webvirtmgr/wiki/Install-WebVirtMgr">Install WebVirtMgr</a>

## Setup host server (Server for VM's)

### <a href="https://github.com/retspen/webvirtmgr/wiki/Setup-Host-Server">Setup Host Server</a>

### License

WebVirtMgr is licensed under the <a href="http://www.apache.org/licenses/LICENSE-2.0.html">Apache Licence, Version 2.0</a>.

[![Donate](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=CEN82VLX7GD7S)
