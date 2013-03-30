# coding: utf-8
# vim: ts=4 sw=4 expandtab ai:
#
# SearchEntry - An enhanced search entry with alternating background colouring 
#         and timeout support
#
# Copyright (C) 2007 Sebastian Heinlein
#               2007-2009 Canonical Ltd.
#               2010-2011 Exposong.org
#
# Authors:
#  Sebastian Heinlein <glatzor@ubuntu.com>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA 02111-1307 USA

"""
The PresFilter class will allow the user to search the presentations by text.
"""

import gtk
import gobject
import re

import exposong.main
import exposong.preslist

presfilter = None # will hold PresFilter instance
blacklist = "[.,'?!]" # [ and ] are part of the regex

class PresFilter(gtk.Entry, exposong._hook.Menu):
    """
    This provides an interface that will allow the user to search the
    presentations by text.
    
    It creates an enhanced IconEntry that supports a timeout when typing
    and uses a different background colour when the search is active.    
    """

    __gsignals__ = {'terms-changed':(gobject.SIGNAL_RUN_FIRST,
                                    gobject.TYPE_NONE,
                                    (gobject.TYPE_STRING,))}

    SEARCH_TIMEOUT = 300
    
    def __init__(self):
        "Initialize the PresFilter."
        gtk.Entry.__init__(self)
        
        self._handler_changed = self.connect_after("changed",
                                                   self._on_changed)
        
        self.connect("key-press-event", self._on_key_pressed)
        self.connect("focus-in-event", exposong.main.main.disable_shortcuts)
        self.connect("focus-out-event", exposong.main.main.enable_shortcuts)
        self.connect("terms-changed", self.filter)
        
        # Make sure icons are supported by GTK version
        self.use_icons = gtk.gtk_version[0] >= 2 and gtk.gtk_version[1] > 16
        if self.use_icons:
            self.set_icon_from_stock(gtk.ENTRY_ICON_PRIMARY, gtk.STOCK_FIND)
            self.connect("icon-press", self._on_icon_pressed)
        
        # Do not draw a yellow bg if an a11y theme is used
        settings = gtk.settings_get_default()
        theme = settings.get_property("gtk-theme-name")
        self._a11y = (theme.startswith("HighContrast") or
                        theme.startswith("LowContrast"))
        
        # set sensible atk name
        atk_desc = self.get_accessible()
        atk_desc.set_name(_("Search"))

        # data
        self._timeout_id = 0
        self.__fmodel = None

    def _on_icon_pressed(self, widget, icon, mouse_button):
        """
        Emit the terms-changed signal without any time out when the clear
        button was clicked
        """
        if icon == gtk.ENTRY_ICON_SECONDARY:
            # clear with no signal and emit manually to avoid the
            # search-timeout
            self.clear_with_no_signal()
            self.grab_focus()
            self.emit("terms-changed", "")
        elif icon == gtk.ENTRY_ICON_PRIMARY:
            self.grab_focus()

    def _on_key_pressed(self, widget, event):
        "Detect a keypress in the text box. Clear the text on 'Escape'."
        if event.keyval == gtk.keysyms.Escape:
            self.clear_with_no_signal()
            self.emit("terms-changed", "")

    def clear(self):
        "Removes the text from the entry."
        self.set_text("")
        self._check_style()

    def clear_with_no_signal(self):
        "Clear and do not send a term-changed signal."
        self.handler_block(self._handler_changed)
        self.clear()
        self.handler_unblock(self._handler_changed)

    def _emit_terms_changed(self):
        "Sends the 'terms-changed' signal"
        text = self.get_text()
        self.emit("terms-changed", text)

    def _on_changed(self, widget):
        """
        Call the actual search method after a small timeout to allow the user
        to enter a longer search term
        """
        self._check_style()
        if self._timeout_id > 0:
            gobject.source_remove(self._timeout_id)
        self._timeout_id = gobject.timeout_add(self.SEARCH_TIMEOUT,
                                                 self._emit_terms_changed)

    def _check_style(self):
        "Use a different background color if a search is active."
        # show/hide icon
        if self.use_icons:
            if self.get_text() != "":
                self.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, gtk.STOCK_CLEAR)
            else:
                self.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY, None)
        # Based on the Rhythmbox code
        yellowish = gtk.gdk.Color(63479, 63479, 48830)
        black = gtk.gdk.Color(0, 0, 0)
        if self._a11y == True:
            return
        if self.get_text() == "":
            self.modify_base(gtk.STATE_NORMAL, None)
            self.modify_text(gtk.STATE_NORMAL, None)
        else:
            self.modify_base(gtk.STATE_NORMAL, yellowish)
            self.modify_text(gtk.STATE_NORMAL, black)
            
    def filter(self, *args):
        'Filters preslist by the keywords.'
        preslist = exposong.preslist.preslist
        if self.get_text() == "":
            if preslist.get_model() == self.__fmodel:
                preslist.set_model(preslist.get_model().get_model())
            self.__fmodel = None
        else:
            if preslist.get_model() == self.__fmodel:
                self.__fmodel = preslist.get_model().get_model().filter_new()
            else:
                self.__fmodel = preslist.get_model().filter_new()
            self.__fmodel.set_visible_func(self._visible_func)
            preslist.set_model(self.__fmodel)

    def _visible_func(self, model, itr):
        'Tests the row for visibility.'
        global blacklist
        pres = model.get_value(itr, 0)
        if pres is not None:
            for word in re.sub(blacklist, "", self.get_text()).split():
                exposong.log.debug('Searching for "%s".',
                                   word)
                if not pres.matches(word):
                    exposong.log.debug('"%s" not found in presentation "%s".',
                                       word, pres.get_title())
                    return False
            return True
        return False

    def focus(self, *args):
        'Sets the focus (for a menu action).'
        self.grab_focus()
    
    @classmethod
    def merge_menu(cls, uimanager):
        'Merge new values with the uimanager.'
        global presfilter
        cls._actions = gtk.ActionGroup('presfilter')
        cls._actions.add_actions([
                ('Search', gtk.STOCK_FIND, _('_Find Presentation'), "<Ctrl>f",
                        _('Search for a presentation'), presfilter.focus),
                ])
        
        uimanager.insert_action_group(cls._actions, -1)
        uimanager.add_ui_from_string("""
            <accelerator action="Search" />
            """)
        # unmerge_menu not implemented, because we will never uninstall this as
        # a module.

def matches(word, element):
    "Takes an item, and tests it for a matching word."
    if isinstance(element, (list, tuple)):
        for item in element:
            if matches(word, item):
                return True
    else:
        regex = re.compile("\\b"+re.escape(word), re.U|re.I)
        try:
            if regex.search(str(element)):
                return True
        except:
            pass

    return False
