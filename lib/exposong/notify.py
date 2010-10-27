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

import exposong.screen
import exposong.application

class Notify(gtk.HBox):
    def __init__(self):
        gtk.HBox.__init__(self)
        
        self.notify = gtk.Entry(45)
        self._handler_changed = self.notify.connect_after("changed",
                                                          self._on_changed)
        self.notify.set_width_chars(15) #Prevent it from expanding wider than the preview
        self.notify.set_tooltip_text("Notification Text")
        self.notify.connect("activate", self._on_activate)
        self.notify.connect("focus-in-event",
                            exposong.application.main.disable_shortcuts)
        self.notify.connect("focus-out-event",
                            exposong.application.main.enable_shortcuts)
        self.notify.connect("key-press-event", self._on_key_pressed)
        self.pack_start(self.notify, True, True, 0)
        
        # Do not draw a yellow bg if an a11y theme is used
        settings = gtk.settings_get_default()
        theme = settings.get_property("gtk-theme-name")
        self._a11y = (theme.startswith("HighContrast") or
                        theme.startswith("LowContrast"))
        
        # Make sure icons are supported by GTK version
        self._button_icons = gtk.gtk_version[0] >= 2 and gtk.gtk_version[1] > 16
        if self._button_icons:
            self.notify.set_icon_from_stock(gtk.ENTRY_ICON_PRIMARY, gtk.STOCK_APPLY)
            self.notify.connect("icon-press", self._on_icon_pressed)
        else:
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
    
    def _on_icon_pressed(self, widget, icon, mouse_button):
        """
        Emit the terms-changed signal without any time out when the clear
        button was clicked
        """
        if icon == gtk.ENTRY_ICON_SECONDARY:
            self._on_clear(None)
        elif icon == gtk.ENTRY_ICON_PRIMARY:
            self._on_save(None)
    
    def _on_changed(self, widget):
        "Show the clear icon"
        self._check_style()

    def _on_key_pressed(self, widget, event):
        if event.keyval == gtk.keysyms.Escape:
            self.clear_with_no_signal()
            self.emit("terms-changed", "")

    def _on_save(self, *args):
        'The user clicked save.'
        exposong.log.info('Setting notification to "%s".',
                          self.notify.get_text())
        exposong.screen.screen.notify(self.notify.get_text())
    
    def _on_clear(self, *args):
        'The user clicked clear.'
        exposong.log.info('Clearing notification.')
        self.notify.set_text("")
        exposong.screen.screen.notify()
    
    def _check_style(self):
        """
        Use a different background colour if a search is active
        """
        # show/hide icon
        if self._button_icons:
            if self.notify.get_text() != "":
                self.notify.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY,
                                                gtk.STOCK_CLEAR)
            else:
                self.notify.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, None)
        # Based on the Rhythmbox code
        yellowish = gtk.gdk.Color(63479, 63479, 48830)
        black = gtk.gdk.Color(0, 0, 0)
        if self._a11y == True:
            return
        if self.notify.get_text() == "":
            self.notify.modify_base(gtk.STATE_NORMAL, None)
            self.notify.modify_text(gtk.STATE_NORMAL, None)
        else:
            self.notify.modify_base(gtk.STATE_NORMAL, yellowish)
            self.notify.modify_text(gtk.STATE_NORMAL, black)
            
    def _on_activate(self, *args):
        'The user clicked enter on the entry.'
        self._on_save()

#notify = Notify()
notify = None
