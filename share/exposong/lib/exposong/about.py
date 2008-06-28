#! /usr/bin/env python
#
# Copyright (C) 2008 Fishhookweb.com
#
# ExpoSong is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import gtk
import gtk.gdk
import webbrowser
from os.path import join

from exposong import RESOURCE_PATH

class About:
  '''Creates an About dialog to show details about the program.'''
  def __init__(self, parent = None):
    self.dialog = gtk.AboutDialog()
    self.dialog.set_transient_for(parent)
    self.dialog.set_name("ExpoSong")
    self.dialog.set_version( "0.5" )
    self.dialog.set_copyright(_("Copyright %s") % "2008 Fishhookweb.com")
    self.dialog.set_authors(("Brad Landis","Siegwart Bogatscher", "Alessandro Felici"))
    if _("Translators Name") is not "Translators Name":
      self.dialog.set_translator_credits(_("Translators Name"))
    self.dialog.set_logo(gtk.gdk.pixbuf_new_from_file(
        join(RESOURCE_PATH, "exposong.png")))
    self.dialog.set_website("http://exposong.org")
    self.dialog.set_modal(False)
    self.dialog.run()
    self.dialog.hide()

gtk.about_dialog_set_url_hook(lambda dlg, url: webbrowser.open(url))

