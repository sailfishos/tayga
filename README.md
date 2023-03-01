******************************************************************************
                           README for TAYGA v0.9.2
******************************************************************************

Last updated 2010-12-12

--------
Overview
--------

TAYGA is an out-of-kernel stateless NAT64 implementation for Linux.  It uses
the TUN driver to exchange packets with the kernel, which is the same driver
used by OpenVPN and QEMU/KVM.  TAYGA needs no kernel patches or out-of-tree
modules, and it is compatible with all 2.4 and 2.6 kernels.

If you're impatient and you know what stateless NAT64 is, you can skip to the
Installation & Basic Configuration section.

-------------------------------
Stateless versus Stateful NAT64
-------------------------------

Most people are familiar with stateful NAT, which allows N:1 address mapping
by tracking TCP and UDP sessions and rewriting port numbers on each packet.
Most commonly this is used to translate sessions from multiple "internal"
hosts (which are numbered with private IPv4 addresses) onto a single global
IPv4 address on the NAT device's "external" interface.

Stateless NAT does no such session tracking or port number rewriting.  It
simply performs a 1:1 substitution of IP addresses using a mapping table
provided by the network administrator.  For example, an organization whose
global address allocation was 198.51.100.0/24 but whose hosts were using
addresses in 192.0.2.0/24 could use a stateless NAT to rewrite 192.0.2.1 into
198.51.100.1, 192.0.2.35 into 198.51.100.35, etc, in the outbound direction,
and the reverse in the inbound direction.  This is commonly done when an
organization moves to a new ISP and receives a new IPv4 address delegation of
the same size as their old delegation but does not want to renumber their
network.

TAYGA and other stateless NAT64 translators operate in this fashion.  When
translating packets between IPv4 and IPv6, the source and destination
addresses in the packet headers are substituted using a 1:1 mapping.  This
means that, in order to exchange packets across the NAT64, each IPv4 host must
be represented by a unique IPv6 address, and each IPv6 host must be
represented by a unique IPv4 address.  How this mapping is performed is
discussed in the next sections.

In situations where stateful NAT64 is required, TAYGA can be used in
combination with a stateful IPv4 NAT such as the iptables MASQUERADE target.
This allows the administrator a great deal more flexibility than if stateful
NAT were implemented directly in TAYGA.

----------------------
Mapping IPv4 into IPv6
----------------------

TAYGA maps IPv4 addresses into the IPv6 network according to RFC 6052.  This
states that a 32-bit IPv4 address should be appended to a designated IPv6
prefix, which we call the NAT64 prefix, and the resulting IPv6 address can be
used to contact the IPv4 host through the NAT64.

The NAT64 prefix should be assigned out of a site's global IPv6 address
allocation.  For example, if a site is allocated 2001:db8:1::/48, the prefix
2001:db8:1:ffff::/96 could be set aside for NAT64.  (There are several options
for the length of the NAT64 prefix, but a /96 is recommended.)  The IPv4 host
198.51.100.10 could then be accessed through the NAT64 using the address
2001:db8:1:ffff::c633:640a.  Conveniently, it is possible to use the syntax
2001:db8:1:ffff::198.51.100.10 instead.

RFC 6052 also specifies a Well-Known Prefix 64:ff9b::/96 which can be used for
NAT64 service rather than allocating a prefix from the site's IPv6 address
block.  However, this comes with several restrictions, primarily that hosts
with private IPv4 addresses (10.x.x.x, 192.168.x.x, etc) cannot be accessed
through the NAT64.  See RFC 6052 for more information.

If NAT64 service is needed for only a few hosts instead of the entire IPv4
address space, TAYGA can be configured without a NAT64 prefix, and address
maps can be assigned on a host-by-host basis.

----------------------
Mapping IPv6 into IPv4
----------------------

Being a stateless NAT, TAYGA requires that a unique IPv4 address is assigned
to every IPv6 host that needs NAT64 service.  This assignment can be done
statically by the network administrator, or dynamically by TAYGA from a pool
of IPv4 addresses designated for this purpose.

Static address mapping is desirable for servers or other hosts requiring a
well-known address.  Statically mapped addresses may be entered into DNS, for
example.

Dynamic address mapping allows TAYGA to assign IPv4 addresses to IPv6 hosts as
they are needed.  By default, these assignments are guaranteed to remain
usable for up to two hours after the last packet seen, but they are retained
for up to two weeks as long as the address pool does not become empty.
Assignments are written to disk so they persist through a restart of the TAYGA
daemon, allowing existing TCP and UDP sessions to continue uninterrupted.

(Of course, TAYGA also supports the addressing architecture described in RFC
6052 in which IPv6 hosts are numbered with "IPv4-translatable IPv6 addresses"
carved out of the NAT64 prefix.)

----------------------------------
Installation & Basic Configuration
----------------------------------

TAYGA uses the GNU Automake/Autoconf system, which requires the `configure`
script to be run to generate the Makefile prior to building.  The --prefix
and/or --sysconfdir options can be specified to the configure script to
specify the top-level installation path and tayga.conf file directory,
respectively.

After unpacking the distribution tar.bz2 file, run:

  # ./configure && make && make install

This will install the tayga executable in /usr/local/sbin/tayga and the sample
config file in /usr/local/etc/tayga.conf.example.

Next, if you would like dynamic maps to be persistent between TAYGA restarts,
create a directory to store the dynamic.map file:

  # mkdir -p /var/db/tayga

Now create your site-specific tayga.conf configuration file.  The installed
tayga.conf.example file can be copied to tayga.conf and modified to suit your
site.  Here is a sample minimal configuration:

  tun-device nat64
  ipv4-addr 192.168.255.1
  prefix 2001:db8:1:ffff::/96     # replace with a prefix from
                                  # your site's address range
  dynamic-pool 192.168.255.0/24
  data-dir /var/db/tayga          # omit if you do not need persistent
                                  # dynamic address maps

Before starting the TAYGA daemon, the routing setup on your system will need
to be changed to send IPv4 and IPv6 packets to TAYGA.  First create the TUN
network interface:

  # tayga --mktun

If TAYGA prints any errors, you will need to fix your config file before
continuing.  Otherwise, the new nat64 interface can be configured and the
proper routes can be added to your system:

  # ip link set nat64 up
  # ip addr add 2001:db8:1::1 dev nat64  # replace with your router's address
  # ip addr add 192.168.0.1 dev nat64    # replace with your router's address
  # ip route add 2001:db8:1:ffff::/96 dev nat64  # from tayga.conf
  # ip route add 192.168.255.0/24 dev nat64      # from tayga.conf

Firewalling your NAT64 prefix from outside access is highly recommended:

  # ip6tables -A FORWARD -s 2001:db8:1::/48 -d 2001:db8:1:ffff::/96 -j ACCEPT
  # ip6tables -A FORWARD -d 2001:db8:1:ffff::/96 -j DROP

At this point, you may start the tayga process:

  # tayga

Check your system log (/var/log/syslog or /var/log/messages) for status
information.

If you are having difficulty configuring TAYGA, use the -d option to run the
tayga process in the foreground and send all log messages to stdout:

  # tayga -d
