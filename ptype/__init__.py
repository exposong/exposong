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
import os
from glob import *
import os.path
import xml.dom
import xml.dom.minidom

'''
Provides the different types of presentations.

The type folder contains python scripts that add some ability to create
and edit different types of slideshows. Follow the code of 'generics.py'
to create a new type.
'''


class Presentation:
	'''
	Sets information from an xml file.
	
	Requires at minimum	a title and slides.
	'''
	def __init__(self, dom = None, filename = None):
		self.type = ""
		self.title = ''
		self.author = {}
		self.copyright = ''
		self.slides = []
		self.filename = filename
		if isinstance(dom, xml.dom.Node):
			self.title = get_node_text(dom.getElementsByTagName("title")[0])
			for el in dom.getElementsByTagName("author"):
				atype = dom.getAttribute("type")
				self.author[atype] = get_node_text(el)
			
			self._set_slides(dom)
	
	def _set_slides(self, dom):
		'Set the slides from xml.'
		slides = dom.getElementsByTagName("slide")
		for sl in slides:
			self.slides.append(Slide(sl))
	
	def get_row(self):
		'Gets the data to add to the presentation list.'
		return (self, self.title, self.type)
	
	def set_text_buffer(self, tbuf):
		'Sets the value of a text buffer.'
		rval = ''
		for sl in self.slides:
			rval += sl.get_text() + "\n\n"
		tbuf.set_text(rval[:-2])
	
	def get_icon(self):
		'Return a pixbuf that represents the ptype'
		pass
	
	def edit(self, parent):
		'''
		Run the edit dialog for the presentation.
		
		Always define this function in subclasses if a custom "Edit"
		class is used.
		'''
		edit = Edit(parent, self)
		rval = edit.run()
		
		if(rval):
			self.title = rval[0]
			self.slides = []
			for sl in rval[1].split("\n\n"):
				self.slides.append(Slide(sl))
			self.to_xml()
			return True
	
	def to_xml(self, directory = "data/pres/"):
		'Save the data to disk.'
		self.filename = check_filename(self.title, directory, self.filename)
		
		doc = xml.dom.getDOMImplementation().createDocument(None, None, None)
		root = doc.createElement("presentation")
		root.setAttribute("type", self.type)
		tNode = doc.createElement("title")
		tNode.appendChild(doc.createTextNode(self.title))
		root.appendChild(tNode)
		for s in self.slides:
			sNode = doc.createElement("slide")
			s.to_node(doc, sNode)
			root.appendChild(sNode)
		doc.appendChild(root)
		outfile = open(directory+self.filename, 'w')
		doc.writexml(outfile)
		doc.unlink()


class Slide:
	'''
	A basic slide for the presentation.
	'''
	def __init__(self, value):
		if isinstance(value, xml.dom.Node):
			self.text = get_node_text(value)
			self.title = value.getAttribute("title")
		elif isinstance(value, str):
			self.text = value
			self.title = None
	
	def get_text(self):
		'Get the text for the presentation.'
		return self.text
	
	def get_markup(self):
		'Get the text for the slide selection.'
		if(self.title):
			return "<b>"+self.title+"</b>\n"+self.text
		else:
			return self.text
	def to_node(self, document, node):
		'Populate the node element'
		if(self.title):
			node.setAttribute("title", self.title)
		node.appendChild( document.createTextNode(self.text) )


#TODO Replace this
class Edit:
	'''Creates a GTK Entry to edit or add a new item'''
	def __init__(self, parent, pres = None):
		'Parent: parent dialog. Pres: Presentation to edit.'
		self.dialog = gtk.Dialog("New Presentation", parent, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
				(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		if(pres.title):
			self.dialog.set_title("Editing " + pres.title)
		else:
			self.dialog.set_title("New " + pres.type.title() + " Presentation")
		self.dialog.vbox.set_spacing(4)
		
		label = gtk.Label("Title:")
		label.set_alignment(0.0, 0.0)
		self.dialog.vbox.pack_start(label, False, True)
		label.show()
		
		self.title = gtk.Entry(45)
		self.title.set_text(pres.title)
		self.dialog.vbox.pack_start(self.title, False, True)
		self.title.show()
		
		label = gtk.Label("Text:")
		label.set_alignment(0.0, 0.0)
		self.dialog.vbox.pack_start(label, False, True)
		label.show()
		
		self.text = gtk.TextView()
		self.text.set_wrap_mode(gtk.WRAP_WORD)
		pres.set_text_buffer(self.text.get_buffer())
		text_scroll = gtk.ScrolledWindow()
		text_scroll.add(self.text)
		text_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		text_scroll.set_size_request(300, 200)
		text_scroll.set_shadow_type(gtk.SHADOW_IN)
		text_scroll.show_all()
		
		self.dialog.vbox.pack_start(text_scroll, True, True)
	
	def run(self):
		rval = False
		if(self.dialog.run() == gtk.RESPONSE_ACCEPT):
			bounds = self.text.get_buffer().get_bounds()
			rval = (self.title.get_text(), self.text.get_buffer().get_text(bounds[0], bounds[1]))
		self.dialog.hide()
		return rval
	
	def copy(self, *args):
		pass
	def cut(self, *args):
		pass
	def paste(self, *args):
		pass


