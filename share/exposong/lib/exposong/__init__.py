#! /usr/bin/env python
#
# Copyright (C) 2008-2010 Exposong.org
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

import os.path, os
from os.path import abspath, dirname, join, pardir, expanduser
from exposong import config

SHARED_FILES = abspath(join(dirname(__file__), pardir, pardir))
LOCALE_PATH = join(SHARED_FILES, 'i18n')
RESOURCE_PATH = join(SHARED_FILES, 'res')
DATA_PATH = None


if config.config.has_option("general", "data-path"):
  DATA_PATH = config.config.get("general", "data-path")
else:
  _defs = None
  try:
    _defs_files = abspath(join(SHARED_FILES, pardir, pardir, "defs.py"))
    import imp
    _defs = imp.load_source('defs', _defs_files)
  except IOError:
    pass
  
  if hasattr(_defs, "DATA_PATH") and isinstance(_defs.DATA_PATH, str):
    DATA_PATH = _defs.DATA_PATH
  else:
    DATA_PATH = join(expanduser("~"),"exposong","data")
  del _defs

# Initialize the data directories. This assumes that if they exist, they are
# either directories or symlinks. We might need to handle the case where they
# could be files at a later point (TODO).
if not os.path.exists(DATA_PATH):
  os.makedirs(DATA_PATH)
for folder in ('bg','pres','sched','image'):
  if not os.path.exists(join(DATA_PATH, folder)):
    os.mkdir(join(DATA_PATH,folder))


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

