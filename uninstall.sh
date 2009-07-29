#!/bin/sh

# Use this if you installed with setup.py - if you used emerge/rpm to
# install then use the following to uninstall:

# emerge unmerge gjots2
#    OR
# rpm -e gjots2

# Python's setup.py provides no uninstallation method so here is
# something to help:

# Maybe customise this:
prefix="/usr"

rm -rf $prefix/lib/gjots2 $prefix/share/doc/gjots2-* $prefix/share/gjots2
rm -f $prefix/bin/gjots2html $prefix/bin/docbook2gjots $prefix/bin/gjots2 $prefix/bin/gjots2docbook $prefix/bin/gjots2lpr
rm -f $prefix/share/man/man1/gjots2html.1 $prefix/share/man/man1/docbook2gjots.1 $prefix/share/man/man1/gjots2.1 $prefix/share/man/man1/gjots2docbook.1
rm -f $prefix/share/pixmaps/gjots.png $prefix/share/application/gjots2.desktop
for LOCALE in en_US fr no nb ru cs it; do
	rm -f $prefix/share/locale/$LOCALE/LC_MESSAGES/gjots2.mo
done