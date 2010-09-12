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

class GTKHandler (logging.Handler, object):
    def __init__(self, level=logging.NOTSET):
        self.records = []
        self.liststore = None
        logging.Handler.__init__(self, level)
        _fmt = logging.Formatter("\x1e".join(["%(asctime)s",
                                              "%(levelname)s",
                                              "%(filename)s:%(lineno)d",
                                              "%(message)s"]))
        self.setFormatter(_fmt)
    
    def emit(self, record):
        r2 = self.format(record).split("\x1e")
        self.records.append(r2)
        self._append_row(r2)
    
    def show_window(self, *args):
        # TODO Set parent
        win = gtk.Dialog("Event Log", None, 0,
                         (gtk.STOCK_CLOSE, gtk.RESPONSE_ACCEPT))
        win.set_default_size(400, 450)
        # TODO Add filters
        # TODO Color rows based on severity
        treeview = gtk.TreeView()
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Time'))
        col.pack_start(cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 0)
        treeview.append_column(col)
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Severity'))
        col.pack_start(cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 1)
        treeview.append_column(col)
        #cell = gtk.CellRendererText()
        #col = gtk.TreeViewColumn( _('Module'))
        #col.pack_start(cell)
        #col.set_resizable(True)
        #col.add_attribute(cell, 'text', 2)
        #treeview.append_column(col)
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Message'))
        col.pack_start(cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 3)
        treeview.append_column(col)
        
        self.liststore = gtk.ListStore(str, str, str, str)
        treeview.set_model(self.liststore)
        
        for record in self.records:
            self._append_row(record)
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.add(treeview)
        scroll.show_all()
        # TODO Allow saving to file
        
        win.vbox.pack_start(scroll)
        # TODO Run stops the other interface. Make it show_all, and handle close
        win.run()
        self.liststore = None
        win.destroy()
    
    def _append_row(self, record):
        if self.liststore:
            self.liststore.append(record)