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
from distutils.core import setup

data_files = []

# Add images
data_files.append(('share/exposong/images/',
                   glob.glob('share/exposong/res/*.png')))

# Add translations
for filepath in glob.glob('share/exposong/i18n/*/LC_MESSAGES/exposong.mo'):
    data_files.append((filepath.replace('LC_MESSAGES/exposong.mo', ''),
                       [filepath]))

# Add help files
data_files.append(('share/exposong/help/', ['help/es.png', 'help/style.css']))
for filepath in glob.glob('help/*/index.html'):
    data_files.append((os.path.join(
        'share/exposong',filepath.rstrip('index.html')), [filepath]))


setup(name='ExpoSong',
    version='0.7',
    description='Worship presentation software',
    long_description="""
    ExpoSong is a presentation software with a focus on displaying lyrics, 
    text and image slides in a Christian setting.

    Features:
    - Lyric, text and image presentations
    - Schedule creation
    - On-screen notification
    - Gradient or image backgrounds
    - Uses OpenLyrics to store Lyrics
    - and more""",
    author='Samuel Mehrbrodt',
    author_email='s.mehrbrodt@gmail.com',
    url='http://www.exposong.org/',
    license='GPLv3',
    scripts = ['bin/exposong'],
    package_dir = {'': 'share/exposong/lib'},
    packages=['exposong',
            'exposong.plugins'],
    data_files = data_files,
    )
