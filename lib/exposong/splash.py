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
import gtk.gdk
import os.path

import exposong
from exposong import RESOURCE_PATH

class SplashScreen(gtk.Window, object):
    """
    Show a splash screen for ExpoSong.
    """
    def __init__(self, parent):
        self._num = 0.0
        self._den = 0
        gtk.Window.__init__(self)
        self._progress = gtk.ProgressBar()
        
        exposong.log.debug("Initializing the splash screen.")
        
        vbox = gtk.VBox()
        self.set_title(_("Loading ExpoSong"))
        self.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_SPLASHSCREEN)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_transient_for(parent)
        self.set_modal(True)
        
        # TODO This takes a while to show... not sure why.
        img = gtk.image_new_from_file(os.path.join(RESOURCE_PATH, 'exposong.png'))
        img.show_all()
        vbox.pack_start(img)
        
        self._progress.set_text(_('Loading, Please Wait.'))
        self._progress.set_fraction(0.0)
        vbox.pack_start(self._progress, True, False, 0)
        
        self.add(vbox)
        self.show_all()
    
    def incr(self, other):
        "Add to the numerator. Usage: `splash += 1`."
        self._num += other
        if self._den <= 0.0:
            self._progress.set_fraction(self._num / 1000)
        self._progress.set_fraction(self._num / self._den)
    
    def incr_total(self, tot):
        "Add to the denominator."
        self._den += tot
        if self._num > 0.0 and self._den > 0.0:
            self._progress.set_fraction(self._num / self._den)

splash = None
