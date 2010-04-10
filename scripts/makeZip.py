#! /usr/bin/env python
#
# Copyright (C) 2008 Fishhookweb.com
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

import zipfile
import sys, os, os.path

def getFiles(dir):
  for root, dirs, files in os.walk(dir):
    #Exclude hidden files
    if '/.' in root or root[0] == '.':
      continue
    
    for fl in files:
      if fl[0] == '.':
        continue
      if fl.endswith('.pyc') or fl.endswith('~'):
        continue
      yield os.path.join(root,fl)
  

if __name__ == "__main__":
  
  if len(sys.argv) < 3:
    print """Usage: makeZip.py versionString exposongRoot
File will be output to the current directory in the format "exposong-{versionString}.py".
"""
    exit(2)

  pwd = os.getcwd()
  os.chdir(sys.argv[2])

  outfile = zipfile.ZipFile("%s/exposong-%s.zip" % (pwd, sys.argv[1]), "w")

  for fl in ('README.txt','CHANGELOG.txt','LICENSE.txt','defs.py'):
    outfile.write(fl)
  for fl in getFiles('bin'):
    outfile.write(fl)
  for fl in getFiles('share'):
    outfile.write(fl)
  for fl in getFiles('help'):
    outfile.write(fl)

  outfile.close()
