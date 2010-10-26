#!/usr/bin/env python
#
# Copyright (C) 2010 Exposong.org
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

#Running:
# python setup_cx.py bdist_msi

import glob
import os
import sys
import re
from cx_Freeze import setup, Executable
from os.path import normpath, isfile

sys.path.insert(0,'lib')
sys.path.insert(0,'./')
GTK_DIR = normpath("C:/GTK")

data_files = []

# Add images
data_files.append((normpath('share/exposong/res'),
                   glob.glob(normpath('share/exposong/res/*.png'))))

# Add translations
for filepath in glob.glob(normpath('share/exposong/i18n/*/LC_MESSAGES/exposong.mo')):
    data_files.append((os.path.dirname(filepath), [filepath]))

# Add help files
data_files.append((normpath('share/exposong/help'),
                   [normpath('share/exposong/help/es.png'),
                    normpath('share/exposong/help/style.css')]))
for filepath in glob.glob(normpath('share/exposong/help/*/index.html')):
    data_files.append((os.path.dirname(filepath), [filepath]))

#plugins = ['exposong.plugins.%s' % p[:-3]
#           for p in os.listdir(normpath('lib/exposong/plugins'))
#           if p.endswith(".py") and not p.startswith("_")]

# Some GTK Data files
data_files.append((normpath('etc/gtk-2.0'),
                  [GTK_DIR + normpath('/etc/gtk-2.0/gtkrc')]))
data_files.append((normpath('lib/gtk-2.0/2.10.0/engines'),
                   [GTK_DIR + normpath('/lib/gtk-2.0/2.10.0/engines/libpixmap.dll')]))


def recursive_add(dir, pre):
    global data_files
    for p1 in glob.glob(dir):
        if isfile(p1):
            if re.match("^[A-Za-z_][A-Za-z0-9_.-]*$", p1.rpartition(os.sep)[2]):
                data_files.append((p1.lstrip(pre).rpartition(os.sep)[0], [p1]))
            continue
        recursive_add(p1+normpath("/*"), pre)

recursive_add(GTK_DIR+normpath('/share/themes/VistaBut/*'), GTK_DIR)


setup(name       = 'exposong',
    version      = '0.7.1',
    description  = 'Worship presentation software',
    long_description="""
    ExpoSong is a presentation software with a focus on displaying lyrics, 
    text and image slides in a Christian setting.

    Features:
    * Image, lyric, and text presentations
    * Images and gradient backgrounds
    * Schedules
    * On-screen notifications
    * Logo and black screen
    * Importing and Exporting possibilities
    * Printing Support
    * OpenLyrics Data Format
    * Full-text search""",
    author       = 'Exposong Team',
    author_email = 'exposong@googlegroups.com',
    maintainer   = 'Brad Landis',
    maintainer_email = 'bradleelandis@gmail.com',
    url          = 'http://www.exposong.org/',
    license      = 'GPLv3',
    scripts      = ['bin/exposong'],
    package_dir  = {'': 'lib'},
    packages     = ['exposong', 'exposong.plugins',
                    'openlyrics', 'openlyrics.tools'],
    py_modules   = ['undobuffer'],#+plugins,
    executables=[Executable(
        script       = 'bin/exposong',
        icon         = 'share/exposong/res/es.ico',
        shortcutName = 'ExpoSong',
        shortcutDir  = 'ProgramMenuFolder',
    #    includes =['defs'],
    #    packages =['exposong','exposong.plugins'],
        # Hide the command line.
        base         = "Win32GUI",
        )],
    data_files   = data_files,
    )
