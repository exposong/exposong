#! /usr/bin/env python
#
# Copyright (C) 2008 Fishhookweb.com
#
# ExpoSong is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from os.path import abspath, dirname, join, pardir

SHARED_FILES = abspath(join(dirname(__file__), pardir, pardir))
LOCALE_PATH = join(SHARED_FILES, 'i18n')
RESOURCE_PATH = join(SHARED_FILES, 'res')
DATA_PATH = abspath(join(SHARED_FILES, pardir, pardir, 'data'))


import pygtk
pygtk.require("2.0")

#Set up translations for the program
import gettext
import locale

locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain('exposong', LOCALE_PATH)
gettext.textdomain('exposong')

import __builtin__
__builtin__._ = gettext.gettext

HELP_URL = abspath(join(SHARED_FILES, pardir, pardir, 'help', _('en') ,
    'index.html'))
    
#import the main application
from exposong.application import run

