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

class Schedule:
	"Schedule of presentations."
	def __init__(self, name):
		self.name = name
		self.model = None
	
	def load(self, filename):
		"Loads from an xml file"
		self.filename = filename
		#TODO load from xml.dom
	
	def save(self):
		"Save to file"
		pass
		#TODO save to xml.dom
	
	def set_model(self, model):
		"""Filter all presentations.
		
		{filt} should be a gtk.TreeViewFilter."""
		self.model = model
	
	def get_model(self):
		'Return the filtered ListModel'
		return self.model
	
	def get_list_row():
		return (self, self.name)

class ScheduleList(gtk.TreeView):
	"A TreeView of presentation schedules."
	def __init__(self):
		gtk.TreeView.__init__(self)
		self.set_size_request(200, 190)
		#Columns: Schedule, Name
		self.model = gtk.TreeStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING)
		self.set_model(self.model)
		self.set_enable_search(False)
		
		column = gtk.TreeViewColumn("Schedule", gtk.CellRendererText(), text=1)
		column.set_resizable(False)
		self.append_column(column)
		
	
	def append(self, parent, row):
		if isinstance(row, Schedule):
			return self.model.append( parent, (row, row.name) )
		elif isinstance(row, tuple):
			return self.model.append( parent, row )
	
	def get_active_item(self):
		(model, s_iter) = self.get_selection().get_selected()
		if(s_iter):
			return model.get_value(s_iter, 0)
		else:
			return False
	
	def has_selection(self):
		return bool(self.get_selection().count_selected_rows())


