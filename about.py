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

class About:
	'''Creates an About dialog to show details about the program. Use about.run()
	to start the dialog.'''
	def __init__(self, parent = None):
		self.dialog = gtk.AboutDialog()
		self.dialog.set_transient_for(parent)
		self.dialog.set_name("ExpoSong")
		self.dialog.set_version( "0.3 Beta" )
		self.dialog.set_copyright(_(u"Copyright ")+u"\xA9 2008 Fishhookweb.com")
		self.dialog.set_authors(("Brad Landis","Robert Nix","Siegwart Bogatscher"))
		self.dialog.set_logo(gtk.gdk.pixbuf_new_from_file("images/exposong.png"))
		self.dialog.set_website("http://exposong.org")
		self.dialog.set_modal(False)
		self.dialog.run()
		self.dialog.hide()

