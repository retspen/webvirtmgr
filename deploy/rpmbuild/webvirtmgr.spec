%global name webvirtmgr
%global version 4.8.9
%global release 1

Name:           %{name}
Version:        %{version}
Release:        %{release}%{?dist}
Summary:        WebVirtMgr panel for manage virtual machine

License:        Apache Licence, Version 2.0
URL:            http://github.com/retspen/webvirtmgr
Source0:        https://github.com/retspen/webvirtmgr/archive/master.tar.gz

%if 0%{?rhel} >= 7 || 0%{?fedora}
%bcond_without systemd	# enabled
Requires(post):   systemd
Requires(preun):  systemd
Requires(postun): systemd
BuildRequires:    systemd
%else
%bcond_with systemd	# disabled
Requires(post): chkconfig
Requires(postun): /sbin/service
Requires(preun): /sbin/service
Requires(preun): chkconfig
%endif

BuildArch:      noarch
BuildRequires:  python-setuptools

Requires:       python-setuptools libvirt-python libxml2-python python-websockify python-gunicorn python-lockfile
%if 0%{?rhel} >= 7
Requires:	python-django
%else
Requires:       python-django15
%endif

Requires:       libvirt qemu-kvm

%description
WebVirtMgr is a libvirt-based Web interface for managing virtual machines.
It allows you to create and configure new domains, and adjust a domain resource allocation.
A VNC viewer presents a full graphical console to the guest domain.
KVM is currently the only hypervisor supported.

%prep
%setup -n %{name}-master

%build
%{__python} setup.py build

%install
%{__python} setup.py install --skip-build --install-lib=%{python_sitelib}/%{name} --root %{buildroot}
cp -r templates %{buildroot}%{python_sitelib}/%{name}/
cp -r webvirtmgr/static %{buildroot}%{python_sitelib}/%{name}/

mkdir -p %{buildroot}%{python_sitelib}/%{name}/conf
cp conf/gunicorn.conf.py %{buildroot}%{python_sitelib}/%{name}/conf/gunicorn.conf.py


%if %{with systemd}
mkdir -p %{buildroot}%{_unitdir}
install -m0644 conf/init/webvirtmgr-console.service %{buildroot}%{_unitdir}/webvirtmgr-console.service
install -m0644 conf/init/webvirtmgr.service %{buildroot}%{_unitdir}/webvirtmgr.service
%else
mkdir -p %{buildroot}%{_sysconfdir}/init
cp conf/init/webvirtmgr-redhat.conf %{buildroot}%{_sysconfdir}/init/webvirtmgr.conf
mkdir -p %{buildroot}%{_sysconfdir}/init.d
cp conf/initd/webvirtmgr-console-redhat %{buildroot}%{_sysconfdir}/init.d/webvirtmgr-console
%endif

cp manage.py %{buildroot}%{python_sitelib}/%{name}/
rm -rf %{buildroot}%{_bindir}/manage.py

%post
%if %{with systemd}
%systemd_post webvirtmgr.service
%systemd_post webvirtmgr-console.service
%else
/sbin/chkconfig --add webvirtmgr
/sbin/chkconfig --add webvirtmgr-console
%endif

%preun
%if %{with systemd}
%systemd_preun webvirtmgr.service
%systemd_preun webvirtmgr-console.service
%else
if [ $1 -eq 0 ]; then
    /sbin/stop webvirtmgr >/dev/null 2>&1 || :
    /sbin/chkconfig --del webvirtmgr
    /sbin/service webvirtmgr stop >/dev/null 2>&1 || :
    /sbin/chkconfig --del webvirtmgr-console
fi
%endif

%postun
%if %{with systemd}
%systemd_postun_with_restart webvirtmgr.service
%systemd_postun_with_restart webvirtmgr-console.service
%else
if [ $1 -ge 1 ]; then
    /sbin/restart webvirtmgr >/dev/null 2>&1 || :
    /sbin/service webvirtmgr-console restart >/dev/null 2>&1 || :
fi
%endif


%files
%defattr(-,root,root)
%{python_sitelib}/*
%config %{python_sitelib}/%{name}/conf/gunicorn.conf.py
%if %{with systemd}
%{_unitdir}/webvirtmgr.service
%{_unitdir}/webvirtmgr-console.service
%else
%{_sysconfdir}/init/*
%{_sysconfdir}/init.d/*
%endif

%changelog
* Mon Jan 18 2016 Giacomo Sanchietti <giacomo.sanchietti@nethesis.it> - 4.8.9
- Support rhel 7
- Upgrade to 4.8.9

* Wed Jan 26 2015 Edoardo Spadoni <edoardo.spadoni@nethesis.it> - 4.8.8
- first version
