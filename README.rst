=========================
WebVirtMgr panel - v5.0
=========================

-------
更新信息
-------
模块升级
django 框架已经升级到1.11版
gunicorn 升级到19.10.0

功能调整
1、调整磁盘和虚拟机创建时的页面位数限制
2、添加支持ARM架构操作系统的创建（由于麒麟v10版本vnc工作不正常，暂时不支持novnc功能）
3、servers页面创建服务器后将添加arch字段，自动检查服务器架构，并影响创建虚拟机时的内容，以及页面默认内存的数值。

----------
Whats new?
----------

- Added RPM specs (Thanks: `Edoardo Spadoni <https://github.com/edospadoni>`_)
- Added support SPICE, SSH Tunnel, fixed some bugs (Thanks: `brenard <https://github.com/brenard>`_)
- Responsive design (Thanks: `Michel Käser <https://github.com/MaddinXx>`_)
- Added VNC WebSocket support (Thanks: `Tolbkni Kao <https://github.com/tolbkni>`_)
- Added novnc proxy supporting new websockify versions (Thanks: `casell <https://github.com/casell>`_)
- Added support `TLS <http://libvirt.org/remote.html#Remote_certificates>`_ connection (Thanks: `junkb <https://github.com/junkb>`_)
- `Puppet module to control libvirt/kvm <https://github.com/ITBlogger/puppet-kvm>`_ (Thanks: `Alex Scoble <https://github.com/ITBlogger>`_)
- `Deployment via Fabric/Fabtools <https://github.com/retspen/webvirtmgr/tree/master/deploy/fabric>`_ (Thanks: `Mohab Usama <https://github.com/mohabusama>`_)

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
