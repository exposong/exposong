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

"""
A widget to handle logged data for easy user access and filtering.
"""

import logging
from gi.repository import GObject, Gtk
import os.path

_SEV_LEVELS = ['CRITICAL','ERROR','WARNING','INFO','DEBUG']

class GTKHandler (logging.Handler, object):
    def __init__(self, level=logging.NOTSET):
        self.liststore = Gtk.ListStore(*([object] + [str] * 6))
        self.scroll = None
        logging.Handler.__init__(self, level)
        # \x1e is an ASCII character for "Field divider", which prevents getting
        # collisions in the message that might be a part of the data.
        _fmt = logging.Formatter("\x1e".join(["%(relativeCreated)3f",
                                              "%(levelname)s",
                                              "%(filename)s:%(lineno)d",
                                              "%(message)s"]))
        self.setFormatter(_fmt)
    
    def emit(self, record):
        r2 = self.format(record).split("\x1e")
        self.liststore.append([record] + r2 + self._get_color(r2[1]))
        GObject.timeout_add(150, self.scroll_to_end)
    
    def _get_color(self, levelname):
        'Return the colors to be used in the table for `levelname`'
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
        "Display the log."
        win = Gtk.Dialog("Event Log", None, 0,
                         (Gtk.STOCK_SAVE, Gtk.ResponseType.ACCEPT,
                         Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE))
        win.set_transient_for(topwindow)
        win.set_default_size(600, 400)
        win.connect("destroy", self._destroy)
        win.connect("response", self._destroy)
        hbox = Gtk.HBox()
        hbox.pack_start(Gtk.Label(_("Filter Severity:")), False, True, 4)
        combo = Gtk.ComboBoxText()
        for opt in _SEV_LEVELS:
            combo.append_text(opt)
        combo.set_active(3)
        list_ = self.liststore.filter_new()
        combo.connect("changed", lambda combo: self._refilter(list_))
        hbox.pack_start(combo, True, True, 4)
        list_.set_visible_func(self._row_filter, combo)
        win.vbox.pack_start(hbox, False, True, 4)
        
        treeview = Gtk.TreeView()
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(_('Time'))
        col.pack_start(cell, True, True, 0)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 1)
        col.add_attribute(cell, 'background', 5)
        col.add_attribute(cell, 'foreground', 6)
        treeview.append_column(col)
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn( _('Severity'))
        col.pack_start(cell, True, True, 0)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 2)
        col.add_attribute(cell, 'background', 5)
        col.add_attribute(cell, 'foreground', 6)
        treeview.append_column(col)
        # Skipping "module:linenum". May want to have it added later.
        cell = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn( _('Message'))
        col.pack_start(cell, True, True, 0)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 4)
        col.add_attribute(cell, 'background', 5)
        col.add_attribute(cell, 'foreground', 6)
        treeview.append_column(col)
        
        treeview.set_model(list_)
        
        self.scroll = Gtk.ScrolledWindow()
        self.scroll.add(treeview)
        self.scroll.show_all()
        win.vbox.pack_start(self.scroll, True, True, 4)
        
        win.show_all()
        GObject.timeout_add(150, self.scroll_to_end)
    
    def scroll_to_end(self):
        "Scroll the list to the most recent log entry."
        if self.scroll:
            self.scroll.emit('scroll-child', Gtk.SCROLL_END, False)
    
    def _destroy(self, win, response_id=None):
        "Close the window."
        if response_id == Gtk.ResponseType.ACCEPT:
            if not self._save(win):
                return
        self.scroll = None
        win.destroy()
    
    def _row_filter(self, model, itr, combo):
        "Filter based on `combo` selection."
        try:
            filt = _SEV_LEVELS.index(combo.get_active_text())
            cur = _SEV_LEVELS.index(model.get_value(itr, 2))
            return cur <= filt
        except ValueError:
            return False
    
    def _refilter(self, list_):
        "Call to force it to refilter the TreeFilter."
        GObject.timeout_add(150, self.scroll_to_end)
        list_.refilter()
    
    def _save(self, toplevel):
        "Save the log to file."
        dlg = Gtk.FileChooserDialog("Save Log File", toplevel,
                                    Gtk.FileChooserAction.SAVE,
                                    (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                                    Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT))
        # Could be ".log" file, but ".txt" is Windows friendly.
        dlg.set_current_name(u"exposong-log.txt")
        dlg.set_current_folder(os.path.expanduser("~"))
        dlg.set_do_overwrite_confirmation(True)
        if dlg.run() == Gtk.ResponseType.ACCEPT:
            dlg.hide()
            outfile = dlg.get_filename()
            out = open(outfile, "w")
            for record in self.liststore:
                out.write(" | ".join(self.format(record[0]).split("\x1e"))+"\n")
            out.close()
            dlg.destroy()
            return True
        dlg.destroy()
        return False
