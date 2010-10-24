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

"""
This script will copy all po files from a specified folder to the
exposong i18n folder and generate the mo-files afterwards. All existing
files will be overwritten.
"""

import os
import shutil

# i18n folder in translations-export branch from launchpad
PO_FILES = ""
EXPOSONG_TRANSLATIONS = "../share/exposong/i18n"

# Copy po files
for file in os.listdir(PO_FILES):
    if not os.path.isfile(os.path.join(PO_FILES, file)):
        continue
    path = os.path.join(EXPOSONG_TRANSLATIONS, file.rstrip(".po"))
    if not os.path.exists(path):
        os.mkdir(path)
    shutil.copy(os.path.join(PO_FILES, file), os.path.join(path, file))
  
# Generate mo-files
for folder in os.listdir(EXPOSONG_TRANSLATIONS):
    if not os.path.isdir(os.path.join(EXPOSONG_TRANSLATIONS, folder))\
            or folder.startswith("."):
        continue
    path = os.path.join(EXPOSONG_TRANSLATIONS, folder)
    mo_dir = os.path.join(path, "LC_MESSAGES")
    mo_file = os.path.join(mo_dir, "exposong.mo")
    if not os.path.exists(mo_dir):
        os.mkdir(mo_dir)
    po_file = os.path.join(path, folder+".po")
    os.system("msgfmt -o %(mo)s %(po)s"%{"mo":mo_file,"po":po_file})
