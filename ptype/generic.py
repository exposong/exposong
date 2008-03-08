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
import os.path
import xml.dom
import xml.dom.minidom

import ptype

'''
Supports a generic presentation.

All other presentation types should use these classes as
base classes, changing only the necessary items.
'''

menu_name = _("Generic")
type_name = "generic"
icon = gtk.gdk.pixbuf_new_from_file('images/generic.png')


class Presentation (ptype.Presentation):
	'''
	Sets information from an xml file.
	
	Requires at minimum	a title and slides (Slides object list)
	'''
	def __init__(self, dom = None, filename = None):
		ptype.Presentation.__init__(self, dom, filename)
		self.type = "generic"
	
	def get_icon(self):
		'Return a pixbuf that represents the ptype'
		return icon

