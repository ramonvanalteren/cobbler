%define name koan
%define version 0.1.0
%define release 1

Summary: Network provisioning tool for Xen and Existing Non-Bare Metal
Name: %{name}
Version: %{version}
Release: 1%{?dist}
Source0: %{name}-%{version}.tar.gz
License: GPL
Group: Applications/System
Requires: mkinitrd
Requires: syslinux
Requires: python >= 2.3
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Vendor: Michael DeHaan <mdehaan@redhat.com>
Url: http://michaeldehaan.net/software/RPMS/koan-0.1.0-1.src.rpm

%description

koan standards for ’kickstart-over-a-network’ and allows for both
network provisioning of new Xen guests and destructive re-provisioning of
any existing system.  For use with a boot-server configured with
'cobbler'


%prep
%setup

%build
python setup.py build

%install
rm -rf $RPM_BUILD_ROOT
python setup.py install --optimize=1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)

%changelog
* Wed Jun 28 2005 - 0.1.0-1
- rpm genesis
