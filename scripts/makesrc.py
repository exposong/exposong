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

import zipfile
import sys, os, os.path

def getFiles(dir):
  for root, dirs, files in os.walk(dir):
    #Exclude hidden files
    if os.sep+'.' in root or root[0] == '.':
      continue
    
    for fl in files:
      if fl[0] == '.':
        continue
      if fl.endswith('.pyc') or fl.endswith('~'):
        continue
      yield os.path.join(root,fl)


def makeSrc():
  pwd = os.getcwd()
  os.chdir(sys.argv[2])

  exposongZip = zipfile.ZipFile("%s/exposong-%s.zip" % (pwd, sys.argv[1]), "w")

  for fl in ('README.txt','CHANGELOG.txt','LICENSE.txt','defs.py'):
    exposongZip.write(fl, os.path.join('exposong',fl))
  for fl in getFiles('bin'):
    exposongZip.write(fl, os.path.join('exposong',fl))
  for fl in getFiles('share'):
    exposongZip.write(fl, os.path.join('exposong',fl))
  for fl in getFiles('help'):
    exposongZip.write(fl, os.path.join('exposong',fl))

  exposongZip.close()


if __name__ == "__main__":
  
  if len(sys.argv) < 3:
    print """Usage: makesrc.py versionString exposongRoot
File will be output to the current directory in the format "exposong-{versionString}.py".
"""
    exit(2)
  makeSrc()

