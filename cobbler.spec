%define name cobbler
%define version 0.1.0
%define release 1

Summary: Boot server configurator
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.gz
License: GPL
Group: Applications/System
Requires: python >= 2.3
Requires: httpd
Requires: tftp-server
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Url: http://michaeldehaan.net/software/RPMS/cobbler-0.1.0-1.src.rpm

%description

Cobbler is a command line tool for simplified configuration of provisioning 
servers.  It is also accessible as a Python library.  Cobbler supports PXE, 
Xen, and re-provisioning an existing Linux system via auto-kickstart.  The
last two modes require 'koan' to be run on the remote system.



%prep
%setup

%build
python setup.py build

%install
python setup.py install --optimize=1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)

%changelog
* Tue Jun 28 2005 - 0.1.0-1
- rpm genesis
