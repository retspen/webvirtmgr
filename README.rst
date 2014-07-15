=========================
WebVirtMgr panel - v4.8.5
=========================

----------
Whats new?
----------

- Added webvirtmgr to pypi
- Update Chart.js
- Added page interfaces
- Added novnc proxy supporting new websockify versions (Thanks: `casell <https://github.com/casell>`_)
- Added support CEPH
- Added instance creating from XML
- Added support `TLS <http://libvirt.org/remote.html#Remote_certificates>`_ connection (Thanks: `junkb <https://github.com/junkb>`_)
- `Puppet module to control libvirt/kvm <https://github.com/ITBlogger/puppet-kvm>`_ (Thanks: `Alex Scoble <https://github.com/ITBlogger>`_)
- `Deployment via Fabric/Fabtools <https://github.com/retspen/webvirtmgr/tree/master/deploy/fabric>`_ (Thanks: `Mohab Usama <https://github.com/mohabusama>`_)
- Added instance cloning (Settings -> Clone)

Screenshots
-----------
`Show <https://github.com/retspen/webvirtmgr/wiki/Screenshots>`_


Introduction
------------

WebVirtMgr is a libvirt-based Web interface for managing virtual machines. It allows you to create and configure new domains, and adjust a domain's resource allocation. A VNC viewer presents a full graphical console to the guest domain. KVM is currently the only hypervisor supported.

Technology:
***********

The application logic is written in Python & Django. The LIBVIRT Python bindings are used to interacting with the underlying hypervisor.

Installation (Only web panel)
-----------------------------

`Install WebVirtMgr <https://github.com/retspen/webvirtmgr/wiki/Install-WebVirtMgr>`_


Setup host server (Server for VM's)
-----------------------------------

`Setup Host Server <https://github.com/retspen/webvirtmgr/wiki/Setup-Host-Server>`_

License
*******

WebVirtMgr is licensed under the `Apache Licence, Version 2.0 <http://www.apache.org/licenses/LICENSE-2.0.html>`_.

.. image:: https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif
    :target: https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=CEN82VLX7GD7S
    :alt: Donate
