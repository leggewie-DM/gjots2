# $Id: gjots2.spec,v 1.12.2.12 2006/01/23 17:26:14 bhepple Exp $

#   Copyright (C) 2002-2005 Robert Hepple 
#
#   This program is free software; you can redistribute it and/or
#   modify it under the terms of the GNU General Public License as
#   published by the Free Software Foundation; either version 2 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful, but
#   WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program; if not, write to the Free Software
#   Foundation, Inc., 59 Temple Place - Suite 330, Boston,
#   MA 02111-1307, USA.

%define ver 2.3.4
%define rel 1
%define prefix /usr

Summary: A note jotter. Organise your ideas, notes, facts in a hierarchy.
Name: gjots2
Version: %{ver}
Release: %{rel}
URL: http://bhepple.freeshell.org/gjots
#Source: http://bhepple.freeshell.org/gjots/gjots2-%{ver}.tar.gz
Source0: %{name}-%{version}.tgz
License: GPL
Group: Applications/Productivity
BuildRoot: %{_tmppath}/root-%{name}-%{version}
Prefix: %{_prefix}
BuildArch: noarch

Requires: python >= 2.3, pygtk2 >= 2.4.0, gnome-python2 >= 2.0.2
Requires: libglade2 >= 2.4, gnome-python2-gconf >= 2.6.0

%description

gjots2 ("gee-jots" or, if you prefer, "gyachts"!) is a way to marshall
and organise your text notes in a convenient, hierachical way. I use
it for all my notes on Unix, my personal bits and pieces, recipes and
even PINs and passwords (encrypted with ccrypt(1)).

You can also use it to "mind-map" your compositions - write down all
your thoughts and then start to organise them into a tree. By
manipulating the tree you can easily reorder your thoughts and
structure them appropriately.

This is a Python/GTK-2 version of the original gjots program by the same author.

%prep
%setup
%build
%install

# typically:
#	buildroot=/var/tmp/root-gjots2-2.3.4
#	_datadir=/usr/share
#	_bindir=/usr/bin
#	_libdir=/usr/lib

%{__rm} -rf %{buildroot}
%{__install} -d -m0755  \
                        %{buildroot}%{_datadir}/applications \
                        %{buildroot}%{_datadir}/%{name} \
                        %{buildroot}%{_datadir}/pixmaps \
                        %{buildroot}%{_datadir}/man/man1 \
                        %{buildroot}%{_libdir}/%{name} \
                        %{buildroot}%{_bindir} \
						%{buildroot}%{_datadir}/locale/en_US/LC_MESSAGES \
						%{buildroot}%{_datadir}/locale/fr/LC_MESSAGES \
						%{buildroot}%{_datadir}/locale/no/LC_MESSAGES \
						%{buildroot}%{_datadir}/locale/nb/LC_MESSAGES \
						%{buildroot}%{_datadir}/locale/ru/LC_MESSAGES

%{__install} -m0755 bin/gjots2 bin/gjots2docbook bin/gjots2html bin/gjots2html.py bin/docbook2gjots %{buildroot}%{_bindir}/
%{__install} -m0755 lib/*.py %{buildroot}%{_libdir}/%{name}/
%{__install} -m0644 gjots.glade2 %{buildroot}%{_datadir}/%{name}
%{__install} -m0644 gjots.png %{buildroot}%{_datadir}/%{name}
%{__install} -m0644 gjots.png %{buildroot}%{_datadir}/pixmaps/
%{__install} -m0644 gjots2-hide-all.png %{buildroot}%{_datadir}/%{name}
%{__install} -m0644 gjots2-merge-items.png %{buildroot}%{_datadir}/%{name}
%{__install} -m0644 gjots2-new-child.png %{buildroot}%{_datadir}/%{name}
%{__install} -m0644 gjots2-new-page.png %{buildroot}%{_datadir}/%{name}
%{__install} -m0644 gjots2-show-all.png %{buildroot}%{_datadir}/%{name}
%{__install} -m0644 gjots2-split-item.png %{buildroot}%{_datadir}/%{name}
%{__install} -m0644 gjots2.desktop %{buildroot}%{_datadir}/applications/
%{__install} -m0644 share/man/man1/gjots2.1 %{buildroot}%{_datadir}/man/man1
%{__install} -m0644 share/man/man1/gjots2html.1 %{buildroot}%{_datadir}/man/man1
%{__install} -m0644 share/man/man1/gjots2docbook.1 %{buildroot}%{_datadir}/man/man1
%{__install} -m0644 share/man/man1/docbook2gjots.1 %{buildroot}%{_datadir}/man/man1
%{__install} -m0644 po/en_US/LC_MESSAGES/gjots2.mo %{buildroot}%{_datadir}/locale/en_US/LC_MESSAGES
%{__install} -m0644 po/fr/LC_MESSAGES/gjots2.mo %{buildroot}%{_datadir}/locale/fr/LC_MESSAGES
%{__install} -m0644 po/no/LC_MESSAGES/gjots2.mo %{buildroot}%{_datadir}/locale/no/LC_MESSAGES
%{__install} -m0644 po/nb/LC_MESSAGES/gjots2.mo %{buildroot}%{_datadir}/locale/nb/LC_MESSAGES
%{__install} -m0644 po/ru/LC_MESSAGES/gjots2.mo %{buildroot}%{_datadir}/locale/ru/LC_MESSAGES

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc AUTHORS INSTALL README COPYING ChangeLog gjots2.gjots gjots2.en_US.gjots gjots2.fr.gjots gjots2.nb.gjots gjots2.no.gjots gjots2.ru.gjots
/

