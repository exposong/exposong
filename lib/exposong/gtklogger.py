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

import logging
import gtk
from exposong import gui

_SEV_LEVELS = ['CRITICAL','ERROR','WARNING','INFO','DEBUG']

class GTKHandler (logging.Handler, object):
    def __init__(self, level=logging.NOTSET):
        self.liststore = gtk.ListStore(*(str,)*6)
        logging.Handler.__init__(self, level)
        # \x1e is an ASCII character for "Field divider", which prevents getting
        # collisions in the message that might be a part of the data.
        _fmt = logging.Formatter("\x1e".join(["%(asctime)s",
                                              "%(levelname)s",
                                              "%(filename)s:%(lineno)d",
                                              "%(message)s"]))
        self.setFormatter(_fmt)
    
    def emit(self, record):
        r2 = self.format(record).split("\x1e")
        color = self._get_color(r2[1])
        self.liststore.append(r2+color)
    
    def _get_color(self, levelname):
        if levelname == "CRITICAL":
            return ["Red","White"]
        if levelname == "ERROR":
            return ["Orange","Black"]
        if levelname == "WARNING":
            return ["Yellow","Black"]
        if levelname == "INFO":
            return ["Green","Black"]
        if levelname == "DEBUG":
            return ["Cadet Blue","Black"]
    
    def show_window(self, action, topwindow):
        win = gtk.Dialog("Event Log", None, 0,
                         (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))
        win.set_transient_for(topwindow)
        win.set_default_size(600, 400)
        win.connect("destroy", self._destroy)
        win.connect("response", self._destroy)
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label(_("Filter Severity:")), False, True, 4)
        combo = gtk.combo_box_new_text()
        for opt in _SEV_LEVELS:
            itr = combo.append_text(opt)
        combo.set_active(3)
        list = self.liststore.filter_new()
        combo.connect("changed", lambda combo: list.refilter())
        hbox.pack_start(combo, True, True, 4)
        list.set_visible_func(self._row_filter, combo)
        win.vbox.pack_start(hbox, False, True, 4)
        
        treeview = gtk.TreeView()
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Time'))
        col.pack_start(cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 0)
        col.add_attribute(cell, 'background', 4)
        col.add_attribute(cell, 'foreground', 5)
        treeview.append_column(col)
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Severity'))
        col.pack_start(cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 1)
        col.add_attribute(cell, 'background', 4)
        col.add_attribute(cell, 'foreground', 5)
        treeview.append_column(col)
        # Skipping "module:linenum". May want to have it added later.
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Message'))
        col.pack_start(cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 3)
        col.add_attribute(cell, 'background', 4)
        col.add_attribute(cell, 'foreground', 5)
        treeview.append_column(col)
        
        treeview.set_model(list)
        
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.add(treeview)
        scroll.show_all()
        # TODO Allow saving to file
        
        win.vbox.pack_start(scroll, True, True, 4)
        win.show_all()
    
    def _destroy(self, win, response_id=None):
        "Close the window."
        win.destroy()
    
    def _row_filter(self, model, itr, combo):
        "Filter based on `combo` selection."
        try:
            filt = _SEV_LEVELS.index(combo.get_active_text())
            cur = _SEV_LEVELS.index(model.get_value(itr, 1))
            return cur <= filt
        except ValueError:
            return False
