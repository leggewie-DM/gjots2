# $Id: gjots2.spec,v 1.12.2.29 2012-06-02 12:42:57 bhepple Exp $

#   Copyright (C) 2002-2020 Robert Hepple 
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

Name: gjots2
Version: 3.1.2
Release: 1.wef
Summary: A note jotter. Organise your ideas, notes, facts in a hierarchy.
License: GPLv2+
URL: http://bhepple.freeshell.org/gjots
Source0: http://downloads.sourceforge.net/%{name}/%{name}-%{version}.tgz

BuildArch: noarch

BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: libappstream-glib
BuildRequires: desktop-file-utils

Requires: python3-gobject
Requires: gtk3
Requires: gtksourceview4

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
%autosetup -p1

sed -i -e 's@lib/gjots2@lib/python%{python3_version}/site-packages/gjots2@g' setup.py
sed -i -e 's@Icon=gjots2@Icon=gjots@g' gjots2.desktop
# Convert to utf-8
for file in doc/man/man1/*.1; do
		iconv -f ISO-8859-1 -t UTF-8 -o $file.new $file && \
		touch -r $file $file.new && \
		mv $file.new $file
done

%build
%py3_build

%install
%py3_install

rm -rf %{buildroot}%{_datadir}/doc/gjots2-%{version}/

for file in $(find po/ -name gjots2.mo | sed 's|po/||') ; do
	install -Dpm0644 po/$file %{buildroot}%{_datadir}/locale/$file
done

%find_lang %{name}

%check
desktop-file-install \
        --dir %{buildroot}%{_datadir}/applications              \
        --remove-category Application                           \
        %{name}.desktop

appstream-util validate-relax --nonet %{buildroot}%{_datadir}/appdata/*.appdata.xml

%files -f gjots2.lang
%doc AUTHORS COPYING ChangeLog README doc/gjots2.gjots 
%doc %lang(en_US) doc/gjots2.en_US.gjots 
%doc %lang(fr) doc/gjots2.fr.gjots
%doc %lang(nb) doc/gjots2.nb.gjots
%doc %lang(no) doc/gjots2.no.gjots
%doc %lang(ru) doc/gjots2.ru.gjots
%doc %lang(es) doc/gjots2.es.gjots
%{_bindir}/gjots2
%{_bindir}/gjots2org
%{_bindir}/org2gjots
%{_bindir}/gjots2html*
%{_bindir}/gjots2docbook
%{_bindir}/docbook2gjots
%{_bindir}/gjots2emacs
%{_bindir}/gjots2lpr
%{python3_sitelib}/%{name}/
%{python3_sitelib}/%{name}-%{version}-py%{python3_version}.egg-info
%{_datadir}/%{name}/
%{_datadir}/pixmaps/gjots.png
%{_datadir}/appdata/gjots2.appdata.xml
%{_datadir}/applications/*gjots2.desktop
%{_datadir}/glib-2.0/schemas/org.gtk.gjots2.gschema.xml
%{_mandir}/man1/%{name}*
%{_mandir}/man1/docbook2gjots*

%changelog
* Sun Mar  8 2020 <bob.hepple@gmail.com> - 3.1.1-1
- merged fedora-30 spec file
