#! /usr/bin/env python
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

import ConfigParser
import os
import shutil
from exposong import SHARED_FILES
# NOTE: Do NOT import anything that uses DATA_PATH here. This is almost
# all of exposong.* .

class Config(ConfigParser.SafeConfigParser):
  def __init__(self):
    ConfigParser.SafeConfigParser.__init__(self)
    cfile = os.path.join(os.path.expanduser("~"), ".exposong.conf")
    
    self.add_section("main_window")
    self.add_section("general")
    self.add_section("screen")
    
    self.set('general', 'ccli', '')
    self.set("screen", "bg_type", 'color')
    self.set("screen", "bg_image", "")
    self.setcolor("screen", "bg_color_1", (0, 13107, 19660))
    self.setcolor("screen", "bg_color_2", (0, 26214, 39321))
    self.set("screen", "bg_angle", u'\u2198')
    self.set("screen", "max_font_size", "56.0")
    self.setcolor("screen", "text_color", (65535, 65535, 65535))
    self.setcolor("screen", "text_shadow", (0, 0, 0, 26214))
    self.set("screen", "logo",
        os.path.join(SHARED_FILES,"res","exposong.png"))
    self.setcolor("screen", "logo_bg", (65535, 43690, 4369))
    self.setcolor("screen", "notify_bg", (65535, 0, 0))
    
    self.configfile = cfile
    self.read(self.configfile)
  
  def getcolor(self, section, option):
    ''
    return map(int, self.get(section, option).split(','))
  
  def setcolor(self, section, option, value):
    ''
    self.set(section, option, ','.join(map(str,value)))

  def write(self):
    tmpname = self.configfile+".new"
    with open(tmpname, 'w') as f:
      ConfigParser.SafeConfigParser.write(self, f)
    
    shutil.move(tmpname, self.configfile)

config = Config()
