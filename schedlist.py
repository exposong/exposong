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
import xml.dom
from glob import *

from schedule import Schedule

class ScheduleList(gtk.TreeView):
	"A TreeView of presentation schedules."
	def __init__(self):
		gtk.TreeView.__init__(self)
		self.set_size_request(200, 190)
		#Columns: Schedule, Name
		self.model = gtk.TreeStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING, gobject.TYPE_STRING)
		self.model.set_sort_column_id(2, gtk.SORT_ASCENDING)
		self.set_model(self.model)
		self.set_enable_search(False)
		
		sched_rend = gtk.CellRendererText()
		sched_rend.connect("edited", self._rename_schedule)
		column = gtk.TreeViewColumn("Schedule", sched_rend, text=1)
		column.set_resizable(False)
		column.set_cell_data_func(sched_rend, self._cell_data_func)
		self.append_column(column)
		
	
	def append(self, parent, row, sort = None):
		'Add an item to the list.'
		if isinstance(row, Schedule):
			if sort is None:
				sort = row.title
			else:
				sort = "%03u" % sort
			return self.model.append( parent, (row, row.title, sort) )
		elif isinstance(row, tuple):
			return self.model.append( parent, row )
	
	def remove(self, item, custom_sched): #TODO custom_sched from class (?)
		'''Remove the item from the model.
		
		@param custom_sched Should be main.custom_schedule.'''
		model = self.get_model()
		itr = model.iter_children(custom_sched)
		while model.get_value(itr, 0).filename != item.filename:
			itr = model.iter_next(itr)
		self.get_model().remove(itr)
	
	def get_active_item(self):
		'Get the currently selected Schedule.'
		(model, s_iter) = self.get_selection().get_selected()
		if s_iter:
			return model.get_value(s_iter, 0)
		else:
			return False
	
	def has_selection(self):
		'Returns if an item is selected.'
		return self.get_selection().count_selected_rows() > 0
	
	def _cell_data_func(self, column, cell, model, iter1):
		'Set whether the cell is editable or not.'
		sched = model.get_value(iter1, 0)
		cell.set_property('editable', isinstance(sched, Schedule) and sched.builtin is False)
	
	def _rename_schedule(self, text_rend, path, new_text):
		"Rename a schedule in the list and it's filename"
		if len(new_text.strip()) == 0:
			return
		iter1 = self.model.get_iter(path)
		self.model.get_value(iter1, 0).title = new_text
		self.model.set_value(iter1, 1, new_text)
		self.model.set_value(iter1, 2, new_text)

