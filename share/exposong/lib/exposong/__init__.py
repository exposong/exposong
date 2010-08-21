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

import imp
import os.path, os
import pygtk
import gettext
import locale
import __builtin__
from os.path import abspath, dirname, join, pardir, expanduser

DATA_PATH = None
SHARED_FILES = None
LOCALE_PATH = None
RESOURCE_PATH = None
HELP_PATH = None
HELP_URL = None

pygtk.require("2.0")

#Set up translations for the program
locale.setlocale(locale.LC_ALL, '')
gettext.bindtextdomain('exposong', LOCALE_PATH)
gettext.textdomain('exposong')
__builtin__._ = gettext.gettext

# TODO We need a better method of searching for defs.py.
_defs_files = None
p = os.path.join(dirname(__file__), pardir, pardir, pardir, pardir)
if not os.path.exists(p):
  p = os.path.join('/', 'usr', 'share', 'exposong')
  if not os.path.exists(p):
    p = None

if p:
  _defs_files = abspath(join(p,"defs.py"))
else:
  print "Program files not found. Will now exit"
  exit(0)

_defs = imp.load_source('defs', _defs_files)

del _defs_files

if _defs:
  SHARED_FILES = _defs.SHARED_FILES
  HELP_PATH = _defs.HELP_PATH

if not SHARED_FILES:
  print "Program files not found. Will now exit"
  exit(0)

LOCALE_PATH = join(SHARED_FILES, 'i18n')
RESOURCE_PATH = join(SHARED_FILES, 'res')
HELP_URL = join(HELP_PATH, _('en') , 'index.html')

# This needs to be after we locate SHARED_FILES, but before DATA_PATH is
# defined.
from exposong import config

if config.config.has_option("general", "data-path"):
  DATA_PATH = config.config.get("general", "data-path")
else:
  if _defs and hasattr(_defs, "DATA_PATH"):
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

# Import this last.
from exposong.application import run
