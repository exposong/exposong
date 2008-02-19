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
import pango
import re
import xml.dom
import xml.dom.minidom
from ptype import generic
from ptype.generic import get_node_text

'''This creates lyrics for presentation.'''
menu_name = "Lyrics"
title_re = re.compile("(chorus|refrain|verse|bridge)", re.I)
#icon = gtk.gdk.pixbuf_new_from_file('images/generic.png')

class Presentation(generic.Presentation):
	'''Sets information from an xml file.
		
		Requires at minimum	a title and slides (Slides object list)'''
	def __init__(self, dom = None, filename = None):
		self.type = 'lyric'
		self.title = '[None]' #TODO Require title always
		self.slides = []
		self.filename = filename
		if isinstance(dom, xml.dom.Node):
			self.title = get_node_text(dom.getElementsByTagName("title")[0])
			
			slides = dom.getElementsByTagName("slide")
			for sl in slides:
				self.slides.append(Slide(sl))
	
	def edit(self, parent = None):
		'''Run the edit dialog for the presentation.'''
		edit = Edit(parent, self)
		rval = edit.run()
		
		if(rval):
			self.title = rval[0]
			self.slides = []
			for sl in rval[1].split("\n\n"):
				self.slides.append(Slide(sl))
			self.to_xml()
			return True
	
	def set_text_buffer(self, tbuf):
		it1 = tbuf.get_start_iter()
		titleTag = tbuf.create_tag("titleTag", weight=pango.WEIGHT_BOLD, background="orange")
		
		for sl in self.slides:
			if(hasattr(sl, 'title') and len(sl.title) > 0):
				tbuf.insert_with_tags(it1, sl.title, titleTag)
				tbuf.insert(it1, "\n")
			tbuf.insert(it1, sl.get_text())
			if(sl is not self.slides[len(self.slides)-1]):
				tbuf.insert(it1, "\n\n")


class Slide(generic.Slide):
	'''A basic slide for the presentation.'''
	
	def __init__(self, value):
		if(isinstance(value, xml.dom.Node)):
			self.text = get_node_text(value)
			self.title = value.getAttribute("title")
		elif(isinstance(value, str)):
			value = value.strip()
			if(title_re.match(value, endpos=30)):
				(self.title, self.text) = value.split("\n", 1)
			else:
				self.title = ''
				self.text = value
	
	def get_markup(self):
		"Get the text for the slide selection."
		if(self.title):
			return "<b>"+self.title+"</b>\n"+generic.Slide.get_markup(self)
		else:
			return generic.Slide.get_markup(self)

class Edit(generic.Edit):
	'''Creates a GTK Entry to edit or add a new item'''
	def __init__(self, parent = None, edit = None):
		generic.Edit.__init__(self, parent, edit)
		
		#self.dialog.set_title("Lyric")
		self.text.get_buffer().connect("changed", self.text_changed)
	
	def text_changed(self, tbuf):
		it = tbuf.get_start_iter()
		tbuf.remove_tag_by_name("titleTag", it, tbuf.get_end_iter())
		cont = True
		while cont:
			end_ln = it.copy().forward_search('\n', gtk.TEXT_SEARCH_VISIBLE_ONLY)
			if(not end_ln):
				end_ln = tbuf.get_end_iter()
			else:
				end_ln = end_ln[1]
			line = it.get_text(end_ln)
			if(title_re.match(line, endpos=30)):
				tbuf.apply_tag_by_name("titleTag", it, end_ln)
				
			cont = it.forward_line()


