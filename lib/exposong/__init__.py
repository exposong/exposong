#
# vim: ts=4 sw=4 expandtab ai:
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

import __builtin__
import exposong.version
import gettext
import gettext_windows
import gtk
import imp
import locale
import logging
import os
import os.path
import platform
import pygtk
import shutil
import sys
import traceback
from optparse import OptionParser, OptionGroup
from os.path import abspath, dirname, join, pardir, expanduser


# Tell Windows that I am my own application, and not just python:
if sys.platform == 'win32':
    import ctypes
    myappid = 'ExpoSong.%s' % exposong.version.__version__
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)


# Set up argument handling
# TODO These cannot currently be translated, due to the required order. Do they
# need to be?
parser = OptionParser(version=exposong.version.__version__,
                      description="A presentation software with a focus on Christian worship settings.")
parser.add_option('-v', '--verbose', dest='debug', action='count',
                  help='Print verbose debugging information to the command line')
parser.add_option('-o', '--log', dest='log', action='store',
                  help='Write the log to a file.')
parser.add_option('-i', '--import', dest='import_', action='store',
                  help='Import an ExpoSong data file. Can import for existing program.')

group = OptionGroup(parser, 'Locations')
group.add_option('-d', '--data-path', dest='data_path', action='store',
                 help='Choose another location for storing program data.')
group.add_option('-c', '--config', dest='config', action='store',
                 help='Use a config file at a given location')
group.add_option('--reset', dest='reset', action='store_true',
                 help='Deletes the contents of the data folder.')
group.add_option('-e', dest='clear_cache', action='store_true',
                 help='Clear the cache in case of errors.')
parser.add_option_group(group)
del group

group = OptionGroup(parser, 'Remote Control',
                    'Use these options to manipulate a running instance of ExpoSong')
group.add_option('-n', '--next', dest='next', action='store_true',
                 help='Move to the next slide.')
group.add_option('-p', '--prev', dest='prev', action='store_true',
                 help='Move to the previous slide.')
group.add_option('-s', '--present', '--show', dest='show', action='store_true',
                 help='Show the presentation screen.')
group.add_option('-x', '--exit', '--hide', dest='hide', action='store_true',
                 help='Hide the presentation screen.')
group.add_option('-b', '--black', dest='black', action='store_true',
                 help='Show black screen.')
group.add_option('--background', dest='background', action='store_true',
                 help='Show the background.')
group.add_option('--logo', dest='logo', action='store_true',
                 help='Show the logo.')
parser.add_option_group(group)
del group

(options, args) = parser.parse_args()
del parser

# Set up logging
log = logging.getLogger("exposong")
log.setLevel(logging.DEBUG)
_handler = logging.StreamHandler()
if options.debug >= 2:
    _handler.setLevel(logging.DEBUG)
elif options.debug == 1:
    _handler.setLevel(logging.INFO)
else:
    _handler.setLevel(logging.WARNING)
_fmt = logging.Formatter("%(asctime)s:%(levelname)s: %(message)s")
_handler.setFormatter(_fmt)
log.addHandler(_handler)

# Logging to the Exposong Debug Window
import exposong.gtklogger
exposong.gtklogger.handler = exposong.gtklogger.GTKHandler(logging.DEBUG)
log.addHandler(exposong.gtklogger.handler)

# Log to a file.
if options.log:
    _handler = logging.FileHandler(options.log)
    _handler.setLevel(logging.INFO)
    _fmt = logging.Formatter("%(asctime)s:%(filename)\
            s@%(lineno)d:%(levelname)s: %(message)s")
    _handler.setFormatter(_fmt)
    log.addHandler(_handler)

log.info("Starting ExpoSong.")

# Send exceptoins to our logger.
def excepthook(type, value, tb):
    "Send exceptions to our custom logger."
    exposong.log.error("".join(traceback.format_exception(type, value, tb)))
sys.excepthook = excepthook

pygtk.require("2.0")

# Log some system information
info = ["System Information",
        " * Python Version: %s" % platform.python_version(),
        " * Platform: %s" % platform.system(),]
if platform.system() == "Linux":
    info.append(" * Distribution: %s" % " ".join(platform.linux_distribution()))
elif platform.system() == "Windows":
    info.append(" * Windows Version: %s" % " ".join(platform.win32_ver()))
exposong.log.info("\n".join(info))

# Set file locations
DATA_PATH = None
SHARED_FILES = None
LOCALE_PATH = None
RESOURCE_PATH = None

# Find the 'share' folder
for i in range(6):
    _p = abspath(join(*([__file__] + [pardir] * i + ['share', 'exposong'])))
    if os.path.exists(_p):
        SHARED_FILES = _p
        break
else:
    log.exception("Program files not found. Will now exit.")
    exit(0)

log.debug('Shared files found at "%s".', SHARED_FILES)

LOCALE_PATH = join(SHARED_FILES, 'i18n')
RESOURCE_PATH = join(SHARED_FILES, 'res')

#Set up translations for the program
gettext_windows.setup_env()
locale.setlocale(locale.LC_ALL, '')
log.debug('Locale set to "%s".', locale.LC_ALL)
gettext.bindtextdomain('exposong', LOCALE_PATH)
gettext.textdomain('exposong')
__builtin__._ = gettext.gettext

# Make sure only one instance of ExpoSong is running
import exposong._instance

# This needs to be after we locate SHARED_FILES, but before DATA_PATH is
# defined.
from exposong import config

if options.data_path:
    DATA_PATH = abspath(options.data_path)
elif config.config.has_option("general", "data-path"):
    DATA_PATH = config.config.get("general", "data-path")
else:
    DATA_PATH = join(expanduser("~"), "exposong", "data")

log.debug('Data is located at "%s".', DATA_PATH)

if options.reset:
    msg = _("Are you sure you want to empty the data folder? This cannot be undone.")
    dlg = gtk.MessageDialog(type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_YES_NO,
                            message_format=msg)
    if dlg.run() == gtk.RESPONSE_YES:
        dlg.hide()
        shutil.rmtree(DATA_PATH)
    dlg.destroy()
elif options.clear_cache:
    shutil.rmtree(os.path.join(DATA_PATH,'.cache'))

# Initialize the data directories. This assumes that if they exist, they are
# either directories or symlinks. We might need to handle the case where they
# could be files at a later point (TODO).
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)
for folder in ('bg', 'pres', 'sched', 'image', 'theme'):
    if not os.path.exists(join(DATA_PATH, folder)):
        os.mkdir(join(DATA_PATH, folder))

# Import this last.
from exposong.application import run
