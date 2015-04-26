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

BuildArch:      noarch
BuildRequires:  python-setuptools

Requires:       python-setuptools libvirt-python libxml2-python python-websockify python-django15 python-gunicorn python-lockfile
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
%{__python} setup.py install --skip-build --install-lib=%{python_sitelib}/%{name} --root $RPM_BUILD_ROOT
cp -r templates $RPM_BUILD_ROOT%{python_sitelib}/%{name}/
cp -r webvirtmgr/static $RPM_BUILD_ROOT%{python_sitelib}/%{name}/

mkdir -p $RPM_BUILD_ROOT%{python_sitelib}/%{name}/conf
cp conf/gunicorn.conf.py $RPM_BUILD_ROOT%{python_sitelib}/%{name}/conf/gunicorn.conf.py

mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/init
cp conf/init/webvirtmgr-redhat.conf $RPM_BUILD_ROOT%{_sysconfdir}/init/webvirtmgr.conf

mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/init.d
cp conf/initd/webvirtmgr-console-redhat $RPM_BUILD_ROOT%{_sysconfdir}/init.d/webvirtmgr-console

cp manage.py $RPM_BUILD_ROOT%{python_sitelib}/%{name}/
rm -rf $RPM_BUILD_ROOT%{_bindir}/manage.py

%post
/sbin/chkconfig --add webvirtmgr-console

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{python_sitelib}/*
%{_sysconfdir}/init/*
%{_sysconfdir}/init.d/*

%changelog
* Wed Jan 26 2015 Edoardo Spadoni <edoardo.spadoni@nethesis.it> - 4.8.8
- first version
