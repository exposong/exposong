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

class Schedule:
	"Schedule of presentations."
	def __init__(self, title="", filename = None, pres_model = None, builtin = True):
		self.title = title
		self.filename = filename
		self.pres_model = pres_model
		self.items = []
		self.builtin = builtin
	
	def load(self, dom, library):
		"Loads from an xml file"
		self.items = []
		self.builtin = False
		self.title = get_node_text(dom.getElementsByTagName("title")[0])
		for presNode in dom.getElementsByTagName("presentation"):
			filenm = comment = ""
			try:
				filenm = get_node_text(presNode.getElementsByTagName("file")[0])
				hasFile = True
				comment = get_node_text(presNode.getElementsByTagName("comment")[0])
			except IndexError:
				pass
			if filenm:
				pres = library.find(filename=filenm)
				if pres:
					self.items.append(ScheduleItem(pres, comment))
					#self.pres_model.append(pres.get_row())
		self.refresh_model()
			
	def save(self, directory='data/sched/'):
		"Write schedule to disk."
		self.filename = check_filename(self.title, directory, self.filename)
		dom = xml.dom.getDOMImplementation().createDocument(None, None, None)
		root = dom.createElement("schedule")
		root.setAttribute("created", "0")
		root.setAttribute("modified", "0")
		tNode = dom.createElement("title")
		tNode.appendChild(dom.createTextNode(self.title))
		root.appendChild(tNode)
		for item in self.items:
			pNode = dom.createElement("presentation")
			tNode = dom.createElement("file")
			tNode.appendChild(dom.createTextNode(item.filename))
			pNode.appendChild(tNode)
			tNode = dom.createElement("comment")
			tNode.appendChild(dom.createTextNode(item.comment))
			pNode.appendChild(tNode)
			root.appendChild(pNode)
		dom.appendChild(root)
		outfile = open(directory+self.filename, 'w')
		dom.writexml(outfile)
		dom.unlink()
	
	def append(self, pres, comment = ""):
		"Add a presentation to the schedule."
		sched = ScheduleItem(pres, comment)
		self.items.append(sched)
		if self.pres_model is not None:
			self.pres_model.append(sched.get_row())
	
	def remove(self, pres):
		"Remove a presentation from a schedule."
		self.items.remove(pres)
		self.refresh_model()
	
	def set_model(self, model):
		"Filter all presentations."
		self.pres_model = model
	
	def get_model(self):
		'Return the filtered ListModel'
		if self.builtin:
			self.pres_model.set_sort_column_id(1, gtk.SORT_ASCENDING)
		return self.pres_model
	
	def refresh_model(self):
		'Clears and repopulates the model.'
		self.pres_model.clear()
		for sched in self.items:
			self.pres_model.append(sched.get_row())
	
	def is_reorderable(self):
		'Checks to see if the list should be reorderable.'
		return not self.builtin
	
	def find(self, filename):
		'''Searches the schedule for the matching filename.'''
		
		for item in self.items:
			if item.filename == filename:
				return item

class ScheduleItem:
	'An item for a schedule, including a presentation and a comment.'
	def __init__(self, presentation, comment):
		self.presentation = presentation
		self.comment = comment
	
	def __getattr__(self, name):
		'Get the attribute from the presentation if possible.'
		if hasattr(self.presentation, name):
			return getattr(self.presentation, name)
		raise AttributeError
	
	def get_row(self):
		'Get a row to put into the presentation list.'
		return (self,) + self.presentation.get_row()[1:]

