#! /usr/bin/env python
#
#	Copyright (C) 2008 Fishhookweb.com
#
#	ExpoSong is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
import pygtk
import gtk
import gtk.gdk
import gobject


class PresList(gtk.TreeView):
	'''Manage the presentation list'''
	def __init__(self):
		gtk.TreeView.__init__(self)
		self.set_size_request(200, 250)
		
		pixbufrend = gtk.CellRendererPixbuf()
		textrend = gtk.CellRendererText()
		#column = gtk.TreeViewColumn(None, column_rend)
		#column.set_sort_column_id(2)
		#column.set_resizable(False)
		#column.set_cell_data_func(column_rend, self._get_row_icon)
		#self.append_column(column)
		column = gtk.TreeViewColumn("Presentation")
		column.pack_start(pixbufrend, False)
		column.set_cell_data_func(pixbufrend, self._get_row_icon)
		column.pack_start(textrend, True)
		column.set_attributes(textrend, text=1)
		column.set_sort_column_id(1)
		column.set_resizable(True)
		column.set_property('spacing', 4)
		self.append_column(column)
	
	def get_active_item(self):
		(model, s_iter) = self.get_selection().get_selected()
		if s_iter:
			return model.get_value(s_iter, 0)
		else:
			return False
	
	def append(self, item):
		self.get_model().append((item, item.title, item.type))
	
	def remove(self, item):
		model = self.get_model()
		iter1 = model.get_iter_first()
		while model.get_value(iter1, 0).filename != item.filename:
			iter1 = model.iter_next(iter1)
		self.get_model().remove(iter1)
	
	def update(self):
		#May need to pass in variable to be updated instead of just
		# updating the selected item. Shouldn't take much processing
		# to just update all items.
		model = self.get_model()
		iter1 = model.get_iter_first()
		while iter1:
			model.set_value(iter1, 1, model.get_value(iter1, 0).title)
			iter1 = model.iter_next(iter1)
	
	def has_selection(self):
		return bool(self.get_selection().count_selected_rows())
	
	def get_model(self):
		return gtk.TreeView.get_model(self)
	
	@staticmethod
	def get_empty_model():
		return gtk.ListStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING, gobject.TYPE_STRING)
	
	def _get_row_icon(self, column, cell, model, titer):
		pres = model.get_value(titer, 0)
		cell.set_property('pixbuf', pres.get_icon())

