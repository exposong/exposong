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
import gtk
import gtk.gdk
import gobject
import xml.dom
from glob import *
from os.path import join

from exposong import DATA_PATH, preslist, ptype


class Schedule(gtk.ListStore):
	'''
	Schedule of presentations.'
	'''
	def __init__(self, title="", filename = None, builtin = True, filter_type = None):
		gtk.ListStore.__init__(self, *preslist.PresList.get_model_args())
		self.title = title
		self.filename = filename
		self.builtin = builtin
		self.filter_type = filter_type
	
	def load(self, dom, library):
		'Loads from an xml file.'
		self.clear()
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
					gtk.ListStore.append(self, ScheduleItem(pres, comment).get_row())
				else:
					print 'Presentation file "%s" not found.' % filenm
			
	def save(self):
		'Write schedule to disk.'
		directory = join(DATA_PATH, 'sched')
		self.filename = check_filename(self.title, directory, self.filename)
		dom = xml.dom.getDOMImplementation().createDocument(None, None, None)
		root = dom.createElement("schedule")
		root.setAttribute("created", "0")
		root.setAttribute("modified", "0")
		tNode = dom.createElement("title")
		tNode.appendChild(dom.createTextNode(self.title))
		root.appendChild(tNode)
		
		itr = self.get_iter_first()
		while itr:
			item = self.get_value(itr, 0)
			
			pNode = dom.createElement("presentation")
			tNode = dom.createElement("file")
			tNode.appendChild(dom.createTextNode(item.filename))
			pNode.appendChild(tNode)
			tNode = dom.createElement("comment")
			tNode.appendChild(dom.createTextNode(item.comment))
			pNode.appendChild(tNode)
			root.appendChild(pNode)
			itr = self.iter_next(itr)
		dom.appendChild(root)
		outfile = open(join(directory, self.filename), 'w')
		dom.writexml(outfile)
		dom.unlink()
	
	def append(self, pres, comment = ""):
		'Add a presentation to the schedule.'
		if self.filter_type and self.filter_type != pres.type:
			return False
		sched = ScheduleItem(pres, comment)
		gtk.ListStore.append(self, sched.get_row())
	
	def remove(self, itr):
		'Remove a presentation from a schedule.'
		gtk.ListStore.remove(self, itr)
	
	def remove_if(self, presentation):
		'Searches and removes a schedule if it is presentation.'
		itr = self.get_iter_first()
		ret = False
		while itr:
			item = self.get_value(itr, 0)
			if item.presentation == presentation:
				itr2 = self.iter_next(itr)
				self.remove(itr)
				itr = itr2
				ret = True
			else:
				itr = self.iter_next(itr)
		return ret
	
	def set_model(self, model):
		'Filter all presentations.'
		gtk.ListStore = model
	
	def get_model(self):
		'Return the filtered ListModel'
		return self
	
	def refresh_model(self):
		'Clears and repopulates the model.'
		itr = self.get_iter_first()
		while itr:
			self.set_value(itr, 1, self.get_value(itr, 0).title)
			itr = self.iter_next(itr)
		if self.builtin:
			self.set_sort_column_id(1, gtk.SORT_ASCENDING)
	
	def is_reorderable(self):
		'Checks to see if the list should be reorderable.'
		return not self.builtin
	
	def find(self, filename):
		'Searches the schedule for the matching filename.'
		itr = self.get_iter_first()
		while itr:
			item = self.get_value(itr, 0)
			if item.filename == filename:
				return item.presentation
			itr = self.iter_next(itr)


class ScheduleItem:
	'''
	An item for a schedule, including a presentation and a comment.
	'''
	def __init__(self, presentation, comment):
		assert(isinstance(presentation, ptype.Presentation))
		self.presentation = presentation
		self.comment = comment
	
	def __getattr__(self, name):
		'Get the attribute from the presentation if possible.'
		if hasattr(self.presentation, name):
			return getattr(self.presentation, name)
		raise AttributeError
	
	def get_row(self):
		'Get a row to put into the presentation list.'
		return (self, self.title)

