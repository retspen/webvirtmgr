## WebVirtMgr panel \(a fork by [daniviga](http://daniele.vigano.me)\)

### Introduction

This personal fork is based on the great [**WebVirtMgr**](https://github.com/retspen/webvirtmgr/) made by [Anatoliy Guskov \(retspen\)](https://github.com/retspen/webvirtmgr). WebVirtMgr is a libvirt-based Web interface for managing virtual machines. It allows you to create and configure new domains, and adjust a domain's resource allocation. A VNC viewer presents a full graphical console to the guest domain. KVM is currently the only hypervisor supported.

### What are the differences with the original one?

* The old connections list page (with a table instead of boxes) has been backported
* A very basic ACL support (users can access only a predefined set of VMs)
* A basic LXC support through _libvirtd_ (coming soon)

The fork is kept up-to-date with [retspen's](https://github.com/retspen) master.

### Installation

[See WebVirtMgr original wiki](https://github.com/retspen/webvirtmgr/wiki/)

### License

**WebVirtMgr** has been originally developed by [Anatoliy Guskov \(retspen\)](https://github.com/retspen) and modified by [me \(daniviga\)](http://daniele.vigano.me).
WebVirtMgr is licensed under the [Apache Licence, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0.html).

The original __README.rst__ can be seen on the orginal repo: https://github.com/retspen/webvirtmgr/blob/master/README.rst.

If you enjoyed **WebVirtMgr** please make a donation to the [original project](https://github.com/retspen/webvirtmgr/).
