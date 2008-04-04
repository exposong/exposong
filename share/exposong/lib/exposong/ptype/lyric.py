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
from os.path import join

from exposong.glob import *
from exposong import ptype, RESOURCE_PATH

'''This creates lyrics for presentation.'''
menu_name = _("Lyrics")
type_name = 'lyrics'
icon = gtk.gdk.pixbuf_new_from_file(join(RESOURCE_PATH,'lyric.png'))
title_re = re.compile("(chorus|refrain|verse|bridge)", re.I)


class Presentation(ptype.Presentation):
	'''
	Sets information from an xml file.
	
	Requires at minimum	a title and slides.
	'''
	def __init__(self, dom = None, filename = None):
		ptype.Presentation.__init__(self, dom, filename)
		self.type = 'lyric'
	
	def _set_slides(self, dom):
		'Set the slides from xml.'
		slides = dom.getElementsByTagName("slide")
		for sl in slides:
			self.slides.append(Slide(sl))
	
	def get_icon(self):
		'Return a pixbuf that represents the ptype'
		return icon
	
	def edit(self, parent = None):
		'Run the edit dialog for the presentation.'
		return ptype.Presentation.edit(self, parent)
	
	def set_text_buffer(self, tbuf):
		'Sets the value of a text buffer.'
		it1 = tbuf.get_start_iter()
		titleTag = tbuf.create_tag("titleTag", weight=pango.WEIGHT_BOLD, background="orange")
		
		for sl in self.slides:
			if(hasattr(sl, 'title') and len(sl.title) > 0):
				tbuf.insert_with_tags(it1, sl.title, titleTag)
				tbuf.insert(it1, "\n")
			tbuf.insert(it1, sl.get_text())
			if(sl is not self.slides[len(self.slides)-1]):
				tbuf.insert(it1, "\n\n")


class Slide(ptype.Slide):
	'''
	A lyric slide for the presentation.
	'''
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

