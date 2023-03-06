Name:        tayga
Version:    0.9.2
Release:    0
Summary:    Simple, no-fuss NAT64
License:    GPLv2+
URL:        http://www.litech.org/%{name}/
Source0:    http://www.litech.org/%{name}/%{name}-%{version}.tar.bz2
Patch1:     0001-use-var-spool.patch
Patch2:     0002-manpage.patch
Patch3:     0003-cflags-override.patch
Patch4:     0004-quote-make-var.patch
Patch5:     0005-guard-chdir.patch
Patch6:     0006-guard-write.patch
Patch8:     0008-manpage-RFC.patch
Patch9:     0009-include-for-writev.patch

BuildRoot:    %{_tmppath}/%{name}-%{version}-build
Requires:    iproute

BuildRequires:    gcc
BuildRequires:    make
BuildRequires:    coreutils
BuildRequires:    autoconf
BuildRequires:    automake

%description
TAYGA is an out-of-kernel stateless NAT64 implementation for Linux that uses
the TUN driver to exchange IPv4 and IPv6 packets with the kernel. It is
intended to provide production-quality NAT64 service for networks where
dedicated NAT64 hardware would be overkill.


%prep
%autosetup -p1 -n %{name}-%{version}/upstream


%build
CFLAGS="%{optflags} -fPIE"
LDFLAGS="$LDFLAGS -Wl,-z,now" 
export CFLAGS
export LDFLAGS
autoreconf -fiv

%configure

%make_build

%install
make install DESTDIR=%{buildroot} INSTALL="install -p"
mkdir -p %{buildroot}%{_sysconfdir}/%{name}
mkdir -p %{buildroot}%{_sharedstatedir}/%{name}

%clean
rm -rf %{buildroot}

%files
%doc README
%license COPYING
%{_sbindir}/%{name}
%{_sharedstatedir}/%{name}
%exclude %{_sysconfdir}/%{name}.conf.example
%exclude %{_mandir}/man*/%{name}.*.gz
