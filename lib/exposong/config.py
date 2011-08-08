#
# vim: ts=4 sw=4 expandtab ai:
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

import ConfigParser
import os
import shutil

import exposong
from exposong import SHARED_FILES
# NOTE: If you import something that uses DATA_PATH, the results could be bad.
# This includes almost all of exposong.*.


class Config(ConfigParser.SafeConfigParser):

    """
    Manages user preferences in the system.
    """
    # Put this here for easy access 
    NoOptionError = ConfigParser.NoOptionError
    
    def __init__(self):
        ConfigParser.SafeConfigParser.__init__(self)
        if exposong.options.config:
            cfile = os.path.abspath(exposong.options.config)
        else:
            if os.name == 'nt':
                try:
                    d = os.path.join(os.environ["LOCALAPPDATA"], "exposong")
                except KeyError:
                    d = os.path.join(os.path.expanduser("~"), "exposong")
            else:
                d = os.path.join(os.path.expanduser("~"), ".config", "exposong")
            if not os.path.exists(d):
                os.makedirs(d)
            cfile = os.path.join(d, "exposong.conf")
            exposong.log.info('Loading config file from "%s".', cfile)
            del d
        
        self.add_section("main_window")
        self.add_section("dialogs")
        self.add_section("general")
        self.add_section("screen")
        self.add_section("updates")
        self.add_section("songs")

        self.set("general", "data-path", "")
        
        self.set("dialogs", "songselect-import-dir", os.path.expanduser("~"))
        self.set("dialogs", "exposong_legacy-import-dir", os.path.expanduser("~"))
        self.set("dialogs", "opensong-import-dir", os.path.expanduser("~"))
        
        self.set("screen", "logo",
                 os.path.join(SHARED_FILES, "res", "exposong.png"))
        self.setcolor("screen", "logo_bg", (65535, 43690, 4369))
        self.setcolor("screen", "notify_color", (65535, 65535, 65535))
        self.setcolor("screen", "notify_bg", (65535, 0, 0))
        
        self.set("updates", "check_for_updates", "True")
        self.set("updates", "last_check", "")
        
        self.set("songs", "ccli", "")
        self.set("songs", "songbook", "")
        self.set("songs", "show_in_order", "True")
        self.set("songs", "title_slide", "False")
        
        self.configfile = cfile
        self.read(self.configfile)
    
    def getcolor(self, section, option):
        "Returns a tuple of integers."
        return map(int, self.get(section, option).split(','))
    
    def setcolor(self, section, option, value):
        "Sets a value from a tuple of integers."
        self.set(section, option, ','.join(map(str, value)))

    def write(self):
        "Save the config to file."
        tmpname = self.configfile + ".new"
        f = open(tmpname, 'w')
        ConfigParser.SafeConfigParser.write(self, f)
        f.close()
        
        exposong.log.info('Saving config file to "%s".', self.configfile)
        shutil.move(tmpname, self.configfile)

config = Config()
