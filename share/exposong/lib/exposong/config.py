#! /usr/bin/env python
#
# Copyright (C) 2010 Fishhookweb.com
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

import ConfigParser
import os
import shutil

class Config(ConfigParser.SafeConfigParser):
  def __init__(self):
    ConfigParser.SafeConfigParser.__init__(self)
    cfile = os.path.join(os.path.expanduser("~"), ".exposong.cfg")
    
    self.add_section("main_window")
    
    self.configfile = cfile
    self.read(self.configfile)

  def write(self):
    tmpname = self.configfile+".new"
    f=open(tmpname, "w")
    ConfigParser.SafeConfigParser.write(self, f)
    f.close()
    shutil.move(tmpname, self.configfile)

config = None
