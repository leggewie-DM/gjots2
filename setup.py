#!/usr/bin/env python

# A command to install gjots2 using the 'standard' method for python.
# I prefer to install with rpm or emerge but this might be useful if
# you have neither or just plain prefer the setup.py script.

# Install gjots2 with:
#		python setup.py install
# or perhaps:
#		python setup.py install --prefix=/usr/local

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

setup(name = "gjots2",
      version = gjots_version,
      description = "gnome-2 notes utility",
      long_description = "gnome-2 notes utility",
      author = "Bob Hepple",
      author_email = "bhepple@freeshell.org",
      url = "http://bhepple.freeshell.org/gjots/",
      scripts = ['bin/gjots2','bin/gjots2docbook','bin/docbook2gjots','bin/gjots2html','bin/gjots2lpr'],
	  data_files = [('lib/gjots2',['lib/__init__.py', 'lib/file.py', 'lib/general.py', 'lib/prefs.py', 'lib/common.py', 'lib/find.py', 'lib/gui.py', 'lib/prefs.py', 'lib/version.py', 'lib/printDialog.py', 'lib/sortDialog.py']),
					('share/man/man1', ['share/man/man1/gjots2.1','share/man/man1/gjots2docbook.1','share/man/man1/docbook2gjots.1','share/man/man1/gjots2html.1']),
					('share/doc/gjots2-' + gjots_version, ['gjots2.gjots','AUTHORS','README','INSTALL', 'COPYING', 'ChangeLog']),
					('share/doc/gjots2-' + gjots_version, ['gjots2.en_US.gjots']),
					('share/doc/gjots2-' + gjots_version, ['gjots2.fr.gjots']),
					('share/doc/gjots2-' + gjots_version, ['gjots2.no.gjots']),
					('share/doc/gjots2-' + gjots_version, ['gjots2.nb.gjots']),
					('share/doc/gjots2-' + gjots_version, ['gjots2.ru.gjots']),
					('share/doc/gjots2-' + gjots_version, ['gjots2.es.gjots']),
					('share/pixmaps', ['gjots.png']),
					('share/gjots2', ['gjots.glade3']),
					('share/gjots2', ['gjots.png']),
					('share/gjots2', ['gjots2-new-page.png']),
					('share/gjots2', ['gjots2-new-child.png']),
					('share/gjots2', ['gjots2-merge-items.png']),
					('share/gjots2', ['gjots2-split-item.png']),
					('share/gjots2', ['gjots2-hide-all.png']),
					('share/gjots2', ['gjots2-show-all.png']),
					('share/locale/en_US/LC_MESSAGES', ['po/en_US/LC_MESSAGES/gjots2.mo']),
					('share/locale/fr/LC_MESSAGES', ['po/fr/LC_MESSAGES/gjots2.mo']),
					('share/locale/no/LC_MESSAGES', ['po/no/LC_MESSAGES/gjots2.mo']),
					('share/locale/nb/LC_MESSAGES', ['po/nb/LC_MESSAGES/gjots2.mo']),
					('share/locale/ru/LC_MESSAGES', ['po/ru/LC_MESSAGES/gjots2.mo']),
					('share/locale/it/LC_MESSAGES', ['po/it/LC_MESSAGES/gjots2.mo']),
					('share/locale/cs/LC_MESSAGES', ['po/cs/LC_MESSAGES/gjots2.mo']),
					('share/locale/es/LC_MESSAGES', ['po/es/LC_MESSAGES/gjots2.mo']),
					('share/applications',['gjots2.desktop']),
				   ],
	  license = 'GNU GPL',
	  platforms = 'posix',
      )
