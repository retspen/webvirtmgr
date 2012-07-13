Applince WebVirtMgr for personal use

WebVirtMgr is a libvirt-based Web interface for managing virtual machines. It allows you to create and configure new domains, and adjust a domain's resource allocation. A VNC viewer over a SSH tunnel presents a full graphical console to the guest domain. KVM is currently the only hypervisor supported

Technology:

The application logic is written in Python & Django. The LIBVIRT Python bindings 
are used to interacting with the underlying hypervisor. KVM primary supported platform.

Install (Fedora 16)
$ git clone https://github.com/retspen/webvirtmgr

# yum install Django kvm libvirtd httpd

$ ./manage.py syncdb
Creating tables ...
Creating table auth_permission
Creating table auth_group_permissions
Creating table auth_group
Creating table auth_user_user_permissions
Creating table auth_user_groups
Creating table auth_user
Creating table auth_message
Creating table django_content_type
Creating table django_session
Creating table django_site
Creating table django_admin_log
Creating table model_host
Creating table model_log

You just installed Django's auth system, which means you don't have any superusers defined.
Would you like to create one now? (yes/no): yes (Put: yes)
Username (Leave blank to use 'admin'): admin (Put: your username or login)
E-mail address: username@domain.local (Put: your email)
Password: xxxxxx (Put: your password)
Password (again): xxxxxx (Put: confirm password)
Superuser created successfully.

Run appliance for test:
$ ./manage.py runserver x.x.x.x:8080 (x.x.x.x - your IP address server)

Setup your apache for Django.
