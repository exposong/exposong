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


# Usage:
# To use this file, move to defs.py in the root folder of exposong.

from os.path import abspath, join, dirname

# DATA_PATH can be used to customize where the data will be stored. If no value
# is specified, it defaults to ~/exposong/data
#
# The following example uses "data" directly under the program directory:
#
DATA_PATH = abspath(join(dirname(__file__),'data'))
#
# Or you can use "~/Documents/exposong"
# directory.
#
#DATA_PATH = os.path.join(os.path.expanduser('~'),'Documents','exposong')

# SHARED_FILES defines where program images, translations, and other
# miscellaneous files.
# 
SHARED_FILES = abspath(join(dirname(__file__), 'share', 'exposong'))

# HELP_PATH defines where help is located.
HELP_PATH = abspath(join(dirname(__file__), 'help'))
