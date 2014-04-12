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

"""
This script will copy all po files from a specified folder to the
exposong i18n folder and generate the mo-files afterwards. All existing
files will be overwritten.
"""

import os
import shutil
import sys

# i18n folder in translations-export branch from launchpad
PO_FILES = None
if len(sys.argv)>1 and os.path.isdir(sys.argv[1]):
  PO_FILES = sys.argv[1]
else:
  print "Please pass the i18n folder in translation-export branch from"+\
        "Launchpad as a command line argument if you want it to be imported."
EXPOSONG_TRANSLATIONS = os.path.realpath(os.path.join(__file__, '..', '..', 'share', 'exposong', 'i18n'))

# Copy po files
if PO_FILES:
  cnt = 0
  for file in os.listdir(PO_FILES):
      if not os.path.isfile(os.path.join(PO_FILES, file)):
          continue
      path = os.path.join(EXPOSONG_TRANSLATIONS, file.split(".")[0])
      if not os.path.exists(path):
          os.mkdir(path)
          shutil.copy(os.path.join(PO_FILES, file), os.path.join(path, file))
      cnt += 1
  print "Copied %i po-files."%cnt
  
# Generate mo-files
cnt = 0
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
    cnt += 1
print "Generated %i mo-Files."%cnt
