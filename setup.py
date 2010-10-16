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

import glob
import os
from os.path import normpath
from distutils.core import setup

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

# Add menu entry for Linux
data_files.append(('share/applications',
                   [normpath("debian/exposong.desktop")]))
data_files.append(('share/pixmaps',
                   [normpath('share/exposong/res/es64.png')]))

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
    author       = 'ExpoSong Team',
    author_email = 'exposong@googlegroups.com',
    maintainer   = 'Samuel Mehrbrodt',
    maintainer_email = 's.mehrbrodt@gmail.com',
    url          = 'http://www.exposong.org/',
    license      = 'GPLv3',
    scripts      = ['bin/exposong'],
    package_dir  = {'': 'lib'},
    packages     = ['exposong', 'exposong.plugins',
                    'openlyrics', 'openlyrics.tools'],
    py_modules   = ['undobuffer'],
    data_files   = data_files,
    )
