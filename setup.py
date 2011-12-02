#!/usr/bin/env python
#
# Copyright (C) 2008-2011 Exposong.org
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

# Add icons
data_files.append((normpath('share/exposong/res/icons'),
                   glob.glob(normpath('share/exposong/res/icons/*.png'))))

# Add css file(s)
data_files.append((normpath('share/exposong/res'),
                   glob.glob(normpath('share/exposong/res/*.css'))))

# Add translations
for filepath in glob.glob(normpath('share/exposong/i18n/*/LC_MESSAGES/exposong.mo')):
    data_files.append((os.path.dirname(filepath), [filepath]))

# Add menu entry for Linux
data_files.append(('share/applications',
                   [normpath("debian/exposong.desktop")]))
data_files.append(('share/mime/packages/exposong.xml',
                   [normpath("debian/exposong.xml")]))
data_files.append(('share/pixmaps',
                   [normpath('share/exposong/res/es64.png')]))

setup(name       = 'exposong',
    version      = '0.8',
    description  = 'ExpoSong',
    long_description="""
    ExpoSong is a presentation software with a focus on displaying Songs and
    generic slides in a Christian setting.
    
    Features
    * Create Songs or ExpoSong Presentations with mixed images and text
    * Themes with background images, colors and gradients
    * Schedules
    * On-screen notifications
    * Logo and black screen
    * Importing and Exporting
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
                    'exposong_openlyrics', 'exposong_openlyrics.tools'],
    py_modules   = ['undobuffer', 'gettext_windows'],
    data_files   = data_files,
    )
