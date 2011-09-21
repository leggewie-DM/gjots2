# Copyright 1999-2004 Gentoo Technologies, Inc.
# Distributed under the terms of the GNU General Public License v2
# $Header: /cvsroot/gjots2/gjots/gjots2.ebuild,v 1.7.2.18 2011/05/10 05:46:24 bhepple Exp $

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
	>=dev-python/gnome-python-2.0.2
	>=dev-python/pygtk-2.4.1
	>=dev-python/pyorbit-2.0.0"

MAKEOPTS="${MAKEOPTS} -j1"

#src_compile() {
#	emake || die "make failed"
#}

src_install() {
	cd ${S}
	dobin bin/gjots2 bin/gjots2html bin/gjots2html.py bin/gjots2docbook bin/docbook2gjots bin/gjots2emacs bin/gjots2lpr

	insinto /usr/lib/gjots2
	doins lib/*.py

	insinto /usr/share/gjots2
	doins gjots.glade3

	insinto /usr/share/gjots2
	doins gjots.png gjots2-hide-all.png gjots2-merge-items.png gjots2-new-child.png gjots2-new-page.png gjots2-show-all.png gjots2-split-item.png

	insinto /usr/share/pixmaps
	doins gjots.png

	insinto /usr/share/applications
	doins gjots2.desktop

	insinto /usr/share/man/man1
	doins share/man/man1/gjots2.1  share/man/man1/gjots2html.1  share/man/man1/gjots2docbook.1  share/man/man1/docbook2gjots.1 

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
}

pkg_postinst() {
	python_mod_optimize /usr/lib/gjots2
}

pkg_postrm() {
	python_mod_cleanup /usr/lib/gjots2
}
