%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: Network provisioning tool for Xen and Bare Metal Machines 
Name: koan
Version: 1.7.0
Release: 1%{?dist}
Source0: %{name}-%{version}.tar.gz
License: GPLv2+
Group: Applications/System
Requires: mkinitrd
Requires: python >= 1.5
Requires: python-urlgrabber
BuildRequires: python-devel
%if 0%{?fedora} >= 11 || 0%{?rhel} >= 6
%{!?pyver: %define pyver %(%{__python} -c "import sys ; print sys.version[:3]")}
Requires: python(abi)=%{pyver}
%endif
%if 0%{?fedora} >= 8
BuildRequires: python-setuptools-devel
%else
BuildRequires: python-setuptools
%endif
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Url: http://fedorahosted.org/cobbler/

%description

Koan stands for kickstart-over-a-network and allows for both
network installation of new virtualized guests and reinstallation 
of an existing system.  For use with a boot-server configured with Cobbler

%prep
%setup -q

%build
%{__python} setup.py build

%install
test "x$RPM_BUILD_ROOT" != "x" && rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --optimize=1 --root=$RPM_BUILD_ROOT

%clean
test "x$RPM_BUILD_ROOT" != "x" && rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%if 0%{?fedora} > 8
%{python_sitelib}/koan*.egg-info
%endif
%dir /var/spool/koan
%{_bindir}/koan
%{_bindir}/cobbler-register
%dir %{python_sitelib}/koan
%{python_sitelib}/koan/*.py*
%{_mandir}/man1/koan.1.gz
%{_mandir}/man1/cobbler-register.1.gz
%dir /var/log/koan

%doc AUTHORS COPYING CHANGELOG README

%changelog

* Wed Apr 8 2009 Michael DeHaan <mdehaan@redhat.com> - 1.7.0-1
- Upstream changes (see CHANGELOG)

* Wed Mar 4 2009 Michael DeHaan <mdehaan@redhat.com> - 1.5.0-1
- Upstream changes (see CHANGELOG)
- added cobbler-register script and manpage

* Tue Feb 17 2009 Michael DeHaan <mdehaan@redhat.com> - 1.4.3-1
- Upstream changes (see CHANGELOG)
- Reduce python version requirements

