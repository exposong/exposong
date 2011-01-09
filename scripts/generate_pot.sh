#! /bin/bash
# -*- coding: utf-8 -*-
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

##################################################################################
## Used to generate a file 'messages.pot' to upload to Launchpad for translating #
## Also generates a po file if the language is provided as a parameter           #
##################################################################################

xgettext --output messages.pot --language=Python -n lib/exposong/*.py lib/exposong/plugins/*.py

if [ -f share/exposong/i18n/$1/$1.po ]
then
    msgmerge share/exposong/i18n/$1/$1.po messages.pot --output-file=$1.po
elif [ ! $1 == "" ]
then
    cp messages.pot $1.po
fi
