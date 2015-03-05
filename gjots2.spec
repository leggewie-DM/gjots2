# $Id: gjots2.spec,v 1.12.2.29 2012-06-02 12:42:57 bhepple Exp $

#   Copyright (C) 2002-2014 Robert Hepple 
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

%define ver 2.4.2
%define rel 1

%define _source_filedigest_algorithm md5
%define _binary_filedigest_algorithm md5
%define _source_payload nil
%define _binary_payload nil
%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Summary: A note jotter. Organise your ideas, notes, facts in a hierarchy.
Name: gjots2
Version: %{ver}
Release: %{rel}
URL: http://bhepple.freeshell.org/gjots
#Source: http://bhepple.freeshell.org/gjots/gjots2-%{ver}.tar.gz
Source0: %{name}-%{version}.tgz
License: GPLv2+
Group: Applications/Productivity
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildArch: noarch
BuildRequires: python desktop-file-utils

Requires: python >= 2.3, gnome-python2-gnome
Requires: gnome-python2-gconf >= 2.6.0
Requires: gnome-python2-bonobo
Requires: pygtksourceview
# how to 'require' libglade3 if it's available otherwise glade2???? ie
# to require it on f-19+ but not on RHEL6??? Without building separate
# packages for them, of course!

%description

gjots2 ("gee-jots" or, if you prefer, "gyachts"!) is a way to marshall
and organise your text notes in a convenient, hierarchical way. For
example, use it for all your notes on Unix, personal bits and pieces,
recipes and even PINs and passwords (encrypted with ccrypt(1), gpg(1)
or openssl(1)).

You can also use it to "mind-map" your compositions - write down all
your thoughts and then start to organise them into a tree. By
manipulating the tree you can easily reorder your thoughts and
structure them appropriately.

%prep
%setup

# Convert to utf-8
for file in doc/man/man1/*.1; do
		iconv -f ISO-8859-1 -t UTF-8 -o $file.new $file && \
		touch -r $file $file.new && \
		mv $file.new $file
done

%build
%install

# typically:
#	buildroot=/var/tmp/root-gjots2-2.4.2
#	_datadir=/usr/share
#	_bindir=/usr/bin
#	_libdir=/usr/lib

mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{python_sitelib}/%{name}
mkdir -p %{buildroot}%{_datadir}/{applications,%{name},pixmaps}
mkdir -p %{buildroot}%{_datadir}/%{name}/pixmaps
mkdir -p %{buildroot}%{_datadir}/%{name}/ui
mkdir -p %{buildroot}%{_datadir}/doc/%{name}
mkdir -p %{buildroot}%{_mandir}/man1

install -pm0755 bin/* %{buildroot}%{_bindir}/
install -pm0755 lib/*.py %{buildroot}%{python_sitelib}/%{name}/
install -pm0644 gjots.glade2 %{buildroot}%{_datadir}/%{name}
install -pm0644 pixmaps/gjots.png %{buildroot}%{_datadir}/pixmaps/
install -pm0644 pixmaps/*.png %{buildroot}%{_datadir}/%{name}/pixmaps/
install -pm0644 ui/*.ui %{buildroot}%{_datadir}/%{name}/ui/

desktop-file-install \
        --dir %{buildroot}%{_datadir}/applications              \
        --remove-category Application                           \
        %{name}.desktop

install -pm0644 doc/man/man1/*.1 %{buildroot}%{_mandir}/man1

for file in $(find po/ -name gjots2.mo | sed 's|po/||') ; do
	install -Dpm0644 po/$file %{buildroot}%{_datadir}/locale/$file
done

%find_lang %{name}

%clean
[ "$RPM_BUILD_ROOT" != "/" ] && rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc AUTHORS INSTALL README COPYING ChangeLog doc/gjots2.gjots 

%doc %lang(en_US) doc/gjots2.en_US.gjots 
%doc %lang(fr) doc/gjots2.fr.gjots
%doc %lang(nb) doc/gjots2.nb.gjots
%doc %lang(no) doc/gjots2.no.gjots
%doc %lang(ru) doc/gjots2.ru.gjots
%doc %lang(es) doc/gjots2.es.gjots

%dir %{python_sitelib}/%{name}
%{python_sitelib}/%{name}/*.py
%{_bindir}/*
%{_datadir}/*
