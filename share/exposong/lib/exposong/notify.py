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
import gtk
import exposong.screen, exposong.application

class Notify(gtk.HBox):
  def __init__(self):
    gtk.HBox.__init__(self)
    
    self.notify = gtk.Entry(45)
    self.notify.set_width_chars(15) #Prevent it from expanding wider than the preview
    self.notify.set_tooltip_text("Notification Text")
    self.notify.connect("activate", self._on_activate)
    self.notify.connect("focus-in-event", exposong.application.main.disable_shortcuts)
    self.notify.connect("focus-out-event", exposong.application.main.enable_shortcuts)
    self.pack_start(self.notify, True, True, 0)
    
    notify_clear = gtk.Button()
    img = gtk.Image()
    img.set_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON)
    notify_clear.set_image(img)
    notify_clear.connect("clicked", self._on_clear)
    self.pack_start(notify_clear, False, True, 0)
    
    notify_save = gtk.Button()
    img = gtk.Image()
    img.set_from_stock(gtk.STOCK_OK, gtk.ICON_SIZE_BUTTON)
    notify_save.set_image(img)
    notify_save.connect("clicked", self._on_save)
    self.pack_start(notify_save, False, True, 0)
  
  def _on_save(self, *args):
    'The user clicked save.'
    exposong.screen.screen.notify(self.notify.get_text())
  
  def _on_clear(self, *args):
    'The user clicked clear.'
    self.notify.set_text("")
    exposong.screen.screen.notify()
  
  def _on_activate(self, *args):
    'The user clicked enter on the entry.'
    self._on_save()

#notify = Notify()
notify = None

