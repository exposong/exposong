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


class PresList:
	'''Manage the presentation list'''
	def __init__(self, treeview):
		self.pres_list_view = treeview
		self.pres_list_view.set_size_request(165, 250)
		
		column1 = gtk.TreeViewColumn("Presentation", gtk.CellRendererText(), text=1)
		column1.set_sort_column_id(1)
		self.pres_list_view.append_column(column1)
		#TODO(?) Icon to represent the type
		#column2 = gtk.TreeViewColumn(" ", gtk.CellRendererPixbuf(), text=2)
		#column2.set_sort_column_id(2)
		#column2.set_resizable(False)
		#self.pres_list_view.append_column(column2)
		
		self.pres_list = gtk.ListStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING)
		self.pres_list.set_sort_column_id(1, gtk.SORT_ASCENDING)
		
		self.pres_list_view.set_model(self.pres_list)
	
	def get_active_item(self):
		(model, s_iter) = self.pres_list_view.get_selection().get_selected()
		if(s_iter):
			return model.get_value(s_iter, 0)
		else:
			return False
	
	def append(self, item):
		self.pres_list.append((item, item.title))
	
	def remove(self, item):
		model = self.pres_list_view.get_model()
		iter1 = model.get_iter_first()
		while model.get_value(iter1, 0).filename != item.filename:
			iter1 = model.iter_next(iter1)
		self.pres_list.remove(iter1)
	
	def update_selected(self):
		#May need to pass in variable to be updated instead of just
		# updating the selected item. Shouldn't take much processing
		# to just update all items.
		(model, s_iter) = self.pres_list_view.get_selection().get_selected()
		self.pres_list.set(s_iter, 1, model.get_value(s_iter, 0).title)
	
	def has_selection(self):
		return bool(self.pres_list_view.get_selection().count_selected_rows())

