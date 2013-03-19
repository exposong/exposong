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

from gi.repository import Gtk, GObject

statusbar = None

class timedStatusbar(Gtk.Statusbar):
    "A Gtk.Statusbar supporting timeout for messages"
    def __init__(self):
        super(Gtk.Statusbar, self).__init__()
        self.last_tag = None
    
    def output(self, msg, timeout=5):
        "Puts the message 'msg' for 'timeout' seconds on the statusbar"
        self._del_timer()
        self.pop(1)
        self.push(1,msg)
        self._set_timer(timeout)
    
    def _del_timer(self):
        "Delete the timer (when a new message is sent)"
        if self.last_tag:
            GObject.source_remove(self.last_tag)
    
    def _set_timer(self, timeout):
        "Sets a timer to a message"
        if timeout > 0:
            self.last_tag = GObject.timeout_add(timeout*1000, self._clear)
    
    def _clear(self):
        "Clears the statusbar"
        self.pop(1)
        self.push(1,"")
        return False
