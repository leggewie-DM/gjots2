#!/usr/bin/env python3

# A command to install gjots2 using the 'standard' method for python.
# I prefer to install with rpm or emerge but this might be useful if
# you have neither or just plain prefer the setup.py script.

# Install gjots2 with:
#               python setup.py install
# or perhaps:
#               python setup.py install --prefix=/usr/local

# Please help! How do I get this script to automatically generate the
# .pyc files at installation time?

# There is no "uninstall" command in the Python setup.py utility :-(
# so I have provided an uninstall.sh script which you can customise
# and use.

import os, sys
sys.path = [os.curdir+ '/lib'] + sys.path

from distutils.core import setup
from lib.version import *

datadir = "lib/gjots2"

setup(
    name = "gjots2",
    version = gjots_version,
    description = "gtk3 notes utility",
    long_description = "gtk3 notes utility",
    author = "Bob Hepple",
    author_email = "bob.hepple@gmail.com",
    url = "http://bhepple.freeshell.org/gjots/",
    scripts = ['bin/gjots2','bin/gjots2docbook','bin/docbook2gjots','bin/gjots2html','bin/gjots2html.py','bin/gjots2lpr','bin/gjots2emacs','bin/gjots2org','bin/org2gjots'],
    data_files = [
        ( 'lib/gjots2',
          [
              'lib/__init__.py', 'lib/file.py', 'lib/general.py', 'lib/prefs.py', 'lib/common.py', 'lib/find.py', 'lib/gui.py', 'lib/prefs.py', 'lib/version.py', 'lib/printDialog.py', 'lib/sortDialog.py'
          ]
        ),
        ( 'share/man/man1',
          [
              'doc/man/man1/gjots2.1','doc/man/man1/gjots2docbook.1','doc/man/man1/docbook2gjots.1','doc/man/man1/gjots2html.1'
          ]
        ),
        ( 'share/doc/gjots2-' + gjots_version,
          [
              'doc/gjots2.gjots','AUTHORS','README','INSTALL', 'COPYING', 'ChangeLog'
          ]
        ),
        ('share/doc/gjots2-' + gjots_version, ['doc/gjots2.en_US.gjots']),
        ('share/doc/gjots2-' + gjots_version, ['doc/gjots2.fr.gjots']),
        ('share/doc/gjots2-' + gjots_version, ['doc/gjots2.no.gjots']),
        ('share/doc/gjots2-' + gjots_version, ['doc/gjots2.nb.gjots']),
        ('share/doc/gjots2-' + gjots_version, ['doc/gjots2.ru.gjots']),
        ('share/doc/gjots2-' + gjots_version, ['doc/gjots2.es.gjots']),
        ('share/pixmaps', ['pixmaps/gjots.png']),
        ('share/gjots2/ui', ['ui/gjots.ui']),
        ('share/gjots2/ui', ['ui/fileDialog.ui']),
        ('share/gjots2/ui', ['ui/findDialog.ui']),
        ('share/gjots2/ui', ['ui/fontDialog.ui']),
        ('share/gjots2/ui', ['ui/generalDialog.ui']),
        ('share/gjots2/ui', ['ui/prefsDialog.ui']),
        ('share/gjots2/ui', ['ui/printDialog.ui']),
        ('share/gjots2/ui', ['ui/sortDialog.ui']),
        ('share/gjots2/ui', ['ui/treeContextMenu.ui']),
        ('share/gjots2/pixmaps', ['pixmaps/gjots.png']),
        ('share/gjots2/pixmaps', ['pixmaps/gjots2-new-page.png']),
        ('share/gjots2/pixmaps', ['pixmaps/gjots2-new-child.png']),
        ('share/gjots2/pixmaps', ['pixmaps/gjots2-merge-items.png']),
        ('share/gjots2/pixmaps', ['pixmaps/gjots2-split-item.png']),
        ('share/gjots2/pixmaps', ['pixmaps/gjots2-hide-all.png']),
        ('share/gjots2/pixmaps', ['pixmaps/gjots2-show-all.png']),
        ('share/gjots2/pixmaps', ['pixmaps/gjots2-clock.png']),
        ('share/locale/en_US/LC_MESSAGES', ['po/en_US/LC_MESSAGES/gjots2.mo']),
        ('share/locale/fr/LC_MESSAGES', ['po/fr/LC_MESSAGES/gjots2.mo']),
        ('share/locale/no/LC_MESSAGES', ['po/no/LC_MESSAGES/gjots2.mo']),
        ('share/locale/nb/LC_MESSAGES', ['po/nb/LC_MESSAGES/gjots2.mo']),
        ('share/locale/ru/LC_MESSAGES', ['po/ru/LC_MESSAGES/gjots2.mo']),
        ('share/locale/it/LC_MESSAGES', ['po/it/LC_MESSAGES/gjots2.mo']),
        ('share/locale/cs/LC_MESSAGES', ['po/cs/LC_MESSAGES/gjots2.mo']),
        ('share/locale/es/LC_MESSAGES', ['po/es/LC_MESSAGES/gjots2.mo']),
        ('share/locale/sl/LC_MESSAGES', ['po/sl/LC_MESSAGES/gjots2.mo']),
        ('share/locale/sv/LC_MESSAGES', ['po/sv/LC_MESSAGES/gjots2.mo']),
        ('share/locale/de_DE/LC_MESSAGES', ['po/de_DE/LC_MESSAGES/gjots2.mo']),
        ('share/locale/en_US/LC_MESSAGES', ['po/en_US/LC_MESSAGES/gjots2.mo']),
        ('share/applications',['gjots2.desktop']),
        ('share/appdata',['gjots2.appdata.xml']),
        ('share/glib-2.0/schemas', ['org.gtk.gjots2.gschema.xml']),
    ],
    license = 'GNU GPL',
    platforms = 'posix',
)
