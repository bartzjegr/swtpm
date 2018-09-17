# --- swtpm rpm-spec ---

%bcond_without gnutls

%global name      swtpm
%global version   0.1.0
%global release   1

Summary: TPM Emulator
Name:           %{name}
Version:        %{version}
Release:        %{release}.dev2%{?dist}
License:        BSD
Source:         http://github.com/stefanberger/swtpm/archive/v%{version}.tar.gz

# due to gnutls backlevel API:
%if 0%{?rhel} < 7 || 0%{?fedora} < 19
    %bcond_with gnutls
%endif

BuildRequires:  automake
BuildRequires:  autoconf
BuildRequires:  bash
BuildRequires:  coreutils
BuildRequires:  libtool
BuildRequires:  sed
BuildRequires:  libtpms-devel >= 0.6.0
BuildRequires:  fuse-devel
BuildRequires:  glib2-devel
BuildRequires:  gmp-devel
BuildRequires:  expect
BuildRequires:  net-tools
BuildRequires:  openssl-devel
BuildRequires:  socat
BuildRequires:  python
BuildRequires:  python-twisted
BuildRequires:  trousers >= 0.3.9
BuildRequires:  tpm-tools >= 1.3.8-6
%if %{with gnutls}
BuildRequires:  gnutls >= 3.1.0
BuildRequires:  gnutls-devel
BuildRequires:  gnutls-utils
BuildRequires:  libtasn1-devel
BuildRequires:  libtasn1
%if 0%{?fedora}
BuildRequires:  libtasn1-tools
%endif
%endif
%if 0%{?fedora} > 16
BuildRequires:  kernel-modules-extra
%endif

Requires:       fuse
Requires:       libtpms >= 0.6.0
%if 0%{?fedora} > 16
Requires:       kernel-modules-extra
%endif

%description
TPM emulator built on libtpms providing TPM functionality for QEMU VMs

%package        libs
Summary:        Common libraries for TPM emulators
Group:          System Environment/Libraries
License:        BSD

%description    libs
A library with callback functions for libtpms based TPM emulator

%package        cuse
Summary:        TPM emulator with CUSE interface
Group:          Applications/Emulators
License:        BSD
BuildRequires:  selinux-policy-devel

%description    cuse
TPM Emulator with CUSE interface

%package        devel
Summary:        Include files for the TPM emulator's CUSE interface for usage by clients
Group:          Development/Libraries
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description    devel
Include files for the TPM emulator's CUSE interface.

%package        tools
Summary:        Tools for the TPM emulator
License:        BSD
Group:          Applications/Emulators
Requires:       swtpm = %{version}-%{release} fuse
Requires:       trousers >= 0.3.9 tpm-tools >= 1.3.8-6 expect bash net-tools gnutls-utils

%description    tools
Tools for the TPM emulator from the swtpm package

%files
%{_bindir}/swtpm
%{_mandir}/man8/swtpm.8*
%{_datadir}/selinux/packages/swtpm.pp
%{_datadir}/selinux/packages/swtpm_svirt.pp

%files cuse
%{_bindir}/swtpm_cuse
%{_mandir}/man8/swtpm_cuse.8*
%{_datadir}/selinux/packages/swtpmcuse.pp

%files libs
%{_libdir}/%{name}/libswtpm_libtpms.so.0
%{_libdir}/%{name}/libswtpm_libtpms.so.0.0.0

%files devel
%{_libdir}/%{name}/libswtpm_libtpms.so

%dir %{_includedir}/%{name}
%{_includedir}/%{name}/*.h
%{_mandir}/man3/swtpm_ioctls.3*

%files tools
%{_bindir}/swtpm_bios
%if %{with gnutls}
%{_bindir}/swtpm_cert
%endif
%{_bindir}/swtpm_setup
%attr( 755, tss , tss)  %{_bindir}/swtpm_setup.sh
%{_bindir}/swtpm_ioctl
%{_mandir}/man8/swtpm_bios.8*
%{_mandir}/man8/swtpm_cert.8*
%{_mandir}/man8/swtpm_ioctl.8*
%{_mandir}/man8/swtpm-localca.conf.8*
%{_mandir}/man8/swtpm-localca.options.8*
%{_mandir}/man8/swtpm-localca.8*
%{_mandir}/man8/swtpm_setup.8*
%{_mandir}/man8/swtpm_setup.conf.8*
%{_mandir}/man8/swtpm_setup.sh.8*
%config(noreplace) %{_sysconfdir}/swtpm_setup.conf
%config(noreplace) %{_sysconfdir}/swtpm-localca.options
%config(noreplace) %{_sysconfdir}/swtpm-localca.conf
%{_datadir}/swtpm/swtpm-localca
%attr( 755, tss, tss) %{_localstatedir}/lib/swtpm-localca

%prep
%setup -q

%build

NOCONFIGURE=1 ./autogen.sh
%configure \
%if %{with gnutls}
        --with-gnutls
%endif

%make_build

%check
make %{?_smp_mflags} check

%install

%make_install
rm -f $RPM_BUILD_ROOT%{_libdir}/%{name}/*.{a,la}

%post
if [ -n "$(type -p semodule)" ]; then
  for pp in /usr/share/selinux/packages/swtpm.pp /usr/share/selinux/packages/swtpm_svirt.pp ; do
    echo "Activating SELinux policy $pp"
    semodule -i $pp
  done
fi

if [ -n "$(type -p restorecon)" ]; then
  restorecon /usr/bin/swtpm
fi

%postun
if [ $1 -eq  0 ]; then
  if [ -n "$(type -p semodule)" ]; then
    for p in swtpm swtpm_svirt ; do
      echo "Removing SELinux policy $p"
      semodule -r $p
    done
  fi
fi

%post cuse
if [ -n "$(type -p semodule)" ]; then
  for pp in /usr/share/selinux/packages/swtpmcuse.pp ; do
    echo "Activating SELinux policy $pp"
    semodule -i $pp
  done
fi

if [ -n "$(type -p restorecon)" ]; then
  restorecon /usr/bin/swtpm_cuse
fi

%postun cuse
if [ $1 -eq  0 ]; then
  if [ -n "$(type -p semodule)" ]; then
    for p in swtpmcuse ; do
      echo "Removing SELinux policy $p"
      semodule -r $p
    done
  fi
fi

%ldconfig_post libs
%ldconfig_postun libs

%changelog
* Mon Sep 17 2018 Stefan Berger - 0.1.0-0.20180917gitfd755d731e
- Created initial version of rpm spec files
- Version is now 0.1.0
