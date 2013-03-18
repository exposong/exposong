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

from gi.repository import Gtk
from gi.repository import Pango

import exposong.main
import exposong.screen
from exposong.config import config

"""
The Notify class will give the user a GUI to alert the audience of any
necessary news/events. An example of usage is for nursury alerts.
"""

class Notify(Gtk.HBox):
    """
    A GUI that will allow the user to alert the audience.
    """
    def __init__(self):
        "Initialize the notification interface."
        super(Gtk.HBox, self).__init__()
        self._text = ""
        
        self.notify = Gtk.Entry()
        self._handler_changed = self.notify.connect_after("changed",
                                                          self._on_changed)
        self.notify.set_width_chars(15) #Prevent it from expanding wider than the preview
        self.notify.set_tooltip_text("Notification Text")
        self.notify.connect("activate", self._on_activate)
        self.notify.connect("focus-in-event",
                            exposong.main.main.disable_shortcuts)
        self.notify.connect("focus-out-event",
                            exposong.main.main.enable_shortcuts)
        self.notify.connect("key-press-event", self._on_key_pressed)
        self.pack_start(self.notify, True, True, 0)
        
        # Do not draw a yellow bg if an a11y theme is used
        settings = Gtk.Settings.get_default()
        theme = settings.get_property("gtk-theme-name")
        self._a11y = (theme.startswith("HighContrast") or
                        theme.startswith("LowContrast"))
        
        # Make sure icons are supported by GTK version
        self.notify.set_icon_from_stock(Gtk.EntryIconPosition.PRIMARY, Gtk.STOCK_APPLY)
        self.notify.connect("icon-press", self._on_icon_pressed)
    
    def draw(self, ccontext, bounds):
        "Draw the notification to the screen if available."
        if not self._text:
            return
        layout = ccontext.create_layout()
        w,h = bounds
        layout.set_text(self._text)
        
        sz = int(h / 12.0)
        layout.set_font_description(Pango.FontDescription(
                                    "Sans Bold " + str(sz)))
        while layout.get_pixel_size()[0] > w * 0.6:
            sz = int(sz * 0.89)
            layout.set_font_description(Pango.FontDescription(
                                        "Sans Bold "+str(sz)))
        nbounds = layout.get_pixel_size()
        pad = sz/14.0
        ccontext.rectangle(w-nbounds[0]-pad*2,
                           h-nbounds[1]-pad*2,
                           w, h)
        col = exposong.screen.c2dec(config.getcolor("screen", "notify_bg"))
        ccontext.set_source_rgb(*col)
        ccontext.fill()
        col = exposong.screen.c2dec(config.getcolor("screen", "notify_color"))
        ccontext.set_source_rgb(*col)
        ccontext.move_to(w-nbounds[0]-pad, h-nbounds[1]-pad)
        ccontext.show_layout(layout)
    
    def _on_icon_pressed(self, widget, icon, mouse_button):
        """
        Emit the terms-changed signal without any time out when the clear
        button was clicked.
        """
        if icon == Gtk.EntryIconPosition.SECONDARY:
            self._on_clear(None)
        elif icon == Gtk.EntryIconPosition.PRIMARY:
            self._on_save(None)
    
    def _on_changed(self, widget):
        "Show the clear icon."
        self._check_style()

    def _on_key_pressed(self, widget, event):
        "Detect a keypress in the text box. Clear the text on 'Escape'."
        if event.keyval == Gdk.KEY_Escape:
            self.clear_with_no_signal()
            self.emit("terms-changed", "")

    def _on_save(self, *args):
        "Apply the text to the screen."
        exposong.log.info('Setting notification to "%s".',
                          self.notify.get_text())
        self._text = self.notify.get_text()
        exposong.screen.screen.draw()
    
    def _on_clear(self, *args):
        "Remove the text from the screen."
        exposong.log.info('Clearing notification.')
        self.notify.set_text("")
        self._text = ""
        exposong.screen.screen.draw()
    
    def _check_style(self):
        "Use a different background color if a search is active."
        # show/hide icon
        if self.notify.get_text() != "":
            self.notify.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY,
                                            Gtk.STOCK_CLEAR)
        else:
            self.notify.set_icon_from_stock(Gtk.EntryIconPosition.SECONDARY, None)
        # Based on the Rhythmbox code
        yellowish = Gdk.Color(63479, 63479, 48830)
        black = Gdk.Color(0, 0, 0)
        if self._a11y == True:
            return
        if self.notify.get_text() == "":
            self.notify.modify_base(Gtk.StateType.NORMAL, None)
            self.notify.modify_text(Gtk.StateType.NORMAL, None)
        else:
            self.notify.modify_base(Gtk.StateType.NORMAL, yellowish)
            self.notify.modify_text(Gtk.StateType.NORMAL, black)
            
    def _on_activate(self, *args):
        "The user clicked enter on the entry."
        self._on_save()

#notify = Notify()
notify = None
