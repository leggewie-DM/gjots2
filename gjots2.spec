# -*-Mode: rpm-spec -*-

Name:    gjots2
Version: 3.1.5
Release: 1%{?dist}
Summary: A hierarchical note jotter - organize your ideas, notes, facts in a tree
License: GPLv2
URL:     http://bhepple.freeshell.org/gjots
Source0: https://downloads.sourceforge.net/%{name}/%{name}-%{version}.tgz

BuildArch: noarch

BuildRequires: python3-devel
BuildRequires: python3-setuptools
BuildRequires: libappstream-glib
BuildRequires: desktop-file-utils

Requires: python3-gobject
Requires: gtk3
Requires: gtksourceview4

%description

gjots2 ("gee-jots" or, if you prefer, "gyachts"!) is a way to marshal
and organize your text notes in a convenient, hierarchical way. For
example, use it for all your notes on Unix, personal bits and pieces,
recipes and even PINs and passwords (encrypted with ccrypt(1), gpg(1)
or openssl(1)).

You can also use it to "mind-map" your compositions - write down all
your thoughts and then start to organize them into a tree. By
manipulating the tree you can easily reorder your thoughts and
structure them appropriately.

%prep
%autosetup -p1

# setup.py installs python code in /usr/local/lib/gjots2, but we want
# /usr/lib/python3.7/site-packages/gjots2:
sed -i -e 's@lib/gjots2@lib/python%{python3_version}/site-packages/gjots2@g' setup.py
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

desktop-file-install \
        --dir %{buildroot}%{_datadir}/applications              \
        --remove-category Application                           \
        %{name}.desktop

%check
appstream-util validate-relax --nonet %{buildroot}%{_datadir}/metainfo/*.metainfo.xml

%files -f gjots2.lang
%license COPYING
%doc AUTHORS ChangeLog README doc/gjots2.gjots
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
%{_datadir}/metainfo/gjots2.metainfo.xml
%{_datadir}/applications/*gjots2.desktop
%{_datadir}/glib-2.0/schemas/org.gtk.gjots2.gschema.xml
%{_mandir}/man1/%{name}*
%{_mandir}/man1/docbook2gjots*

%changelog
* Sat May 02 2020 Bob Hepple <bob.hepple@gmail.com> - 3.1.5-1
- in response to RHBZ#1823599

* Sun Apr 19 2020 <bob.hepple@gmail.com> - 3.1.4-1
- Update more FSF addresses
- Change shebangs to absolute paths (fedora required)
- Change appdata to metainfo

* Fri Apr 17 2020 <bob.hepple@gmail.com> - 3.1.3-1
- new version upstream - fixed FSF address

* Sun Mar 08 2020 <bob.hepple@gmail.com> - 3.1.2-2
- minor spec file fixes

* Sun Mar 08 2020 <bob.hepple@gmail.com> - 3.1.2-1
- merged fedora-30 spec file
