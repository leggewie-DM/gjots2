# Copyright 1999-2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
# $Header: /home/bhepple/fun/sf/g/gjots/gjots2.ebuild,v 1.7.2.23 2012-06-02 12:42:57 bhepple Exp $

#### NOT TESTED FOR _AGES_ - I no longer have a gentoo system - if
#### anyone wants to support this, please let me know.

inherit python gnome.org

DESCRIPTION="A graphical (GNOME 2) jotter tool"
HOMEPAGE="http://bhepple.freeshell.org/gjots/"
SRC_URI="http://bhepple.freeshell.org/gjots/${P}.tgz"

LICENSE="GPL-2"
SLOT="0"
KEYWORDS="~x86"
IUSE=""

DEPEND=">=dev-lang/python-2.3.4
>=gnome-base/libglade-2.4.0
>=gnome-base/libgnome-2
>=dev-python/pygtk-2.4.1
>=dev-python/pyorbit-2.0.0
dev-python/libgnome-python
dev-python/gconf-python"

MAKEOPTS="${MAKEOPTS} -j1"

#src_compile() {
#	emake || die "make failed"
#}

src_install() {
	cd ${S}
	dobin bin/gjots2 bin/gjots2html bin/gjots2html.py bin/gjots2docbook bin/docbook2gjots bin/gjots2emacs bin/gjots2lpr

	insinto /usr/lib/gjots2
	doins lib/*.py

	insinto /usr/share/gjots2/ui
	doins ui/*.ui

	insinto /usr/share/gjots2/pixmaps
	doins pixmaps/*.png

	insinto /usr/share/applications
	doins gjots2.desktop

	insinto /usr/share/man/man1
	doins doc/man/man1/*.1

	dodoc README AUTHORS COPYING INSTALL ChangeLog
	insinto /usr/share/doc/${PF}
	doins gjots2.gjots 
	doins gjots2.en_US.gjots
	doins gjots2.fr.gjots
	doins gjots2.no.gjots
	doins gjots2.nb.gjots
	doins gjots2.ru.gjots
	doins gjots2.es.gjots
# not available:
#	doins gjots2.it.gjots
#	doins gjots2.cs.gjots

	insinto /usr/share/locale/en_US/LC_MESSAGES
	doins po/en_US/LC_MESSAGES/gjots2.mo

	insinto /usr/share/locale/fr/LC_MESSAGES
	doins po/fr/LC_MESSAGES/gjots2.mo

	insinto /usr/share/locale/no/LC_MESSAGES
	doins po/no/LC_MESSAGES/gjots2.mo
	insinto /usr/share/locale/nb/LC_MESSAGES
	doins po/nb/LC_MESSAGES/gjots2.mo

	insinto /usr/share/locale/ru/LC_MESSAGES
	doins po/ru/LC_MESSAGES/gjots2.mo

	insinto /usr/share/locale/it/LC_MESSAGES
	doins po/it/LC_MESSAGES/gjots2.mo

	insinto /usr/share/locale/cs/LC_MESSAGES
	doins po/cs/LC_MESSAGES/gjots2.mo

	insinto /usr/share/locale/es/LC_MESSAGES
	doins po/es/LC_MESSAGES/gjots2.mo

	insinto /usr/share/locale/sl/LC_MESSAGES
	doins po/sl/LC_MESSAGES/gjots2.mo

	insinto /usr/share/locale/de_DE/LC_MESSAGES
	doins po/de_DE/LC_MESSAGES/gjots2.mo

	insinto /usr/share/locale/zh_TW/LC_MESSAGES
	doins po/zh_TW/LC_MESSAGES/gjots2.mo

	insinto /usr/share/locale/sv/LC_MESSAGES
	doins po/sv/LC_MESSAGES/gjots2.mo
}

pkg_postinst() {
	python_mod_optimize /usr/lib/gjots2
}

pkg_postrm() {
	python_mod_cleanup /usr/lib/gjots2
}
