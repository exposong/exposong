#
# vim: ts=4 sw=4 expandtab ai:
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

import gtk
import gobject

statusbar = None

class timedStatusbar(gtk.Statusbar):
    "A gtk.Statusbar supporting timeout for messages"
    def __init__(self):
        gtk.Statusbar.__init__(self)
        self.last_tag = None
    
    def output(self, msg, timeout=5):
        "Puts the message 'msg' for 'timeout' seconds on the statusbar"
        self._del_timer()
        self.pop(1)
        self.push(1,msg)
        self._set_timer(timeout)
    
    def _del_timer(self):
        if self.last_tag:
            gobject.source_remove(self.last_tag)
        #self.last_tag = None
    
    def _set_timer(self, timeout):
        if timeout > 0:
            self.last_tag = gobject.timeout_add(timeout*1000, self._clear)
    
    def _clear(self):
        self.pop(1)
        self.push(1,"")
        return False
