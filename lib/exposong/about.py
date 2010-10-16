#
# Copyright (C) 2008-2010 Exposong.org
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
import os.path
import platform

import exposong.application
import exposong.schedlist
from exposong import RESOURCE_PATH


class About:
    '''Creates an About dialog to show details about the program.'''

    def __init__(self, parent=None):
        self.dialog = gtk.AboutDialog()
        self.dialog.set_transient_for(parent)
        self.dialog.set_name("ExpoSong")
        self.dialog.set_version("0.7.1")
        self.dialog.set_copyright(_("Copyright %s") % "2008-2010 Exposong.org")
        self.dialog.set_authors(("Brad Landis",
                                 "Samuel Mehrbrodt",
                                 "Siegwart Bogatscher",))
        self.dialog.set_artists(("Tango (http://tango.freedesktop.org)",))
        if _("translator-credits") is not "translator-credits":
            self.dialog.set_translator_credits(_("translator-credits"))
        self.dialog.set_logo(gtk.gdk.pixbuf_new_from_file(
                os.path.join(RESOURCE_PATH, "exposong.png")))
        self.dialog.set_website("http://exposong.org")
        self.dialog.set_modal(False)
        self.dialog.run()
        self.dialog.destroy()

class Statistics(gtk.Dialog):
    '''
    Show a window with stats and data about this instance of ExpoSong.
    '''
    def __init__(self, parent=None):
        gtk.Dialog.__init__(self, _("Statistics and System Information"),
                            parent, gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CLOSE, gtk.RESPONSE_NONE))
        self.set_modal(False)
        self.connect("destroy", self._destroy)
        self.connect("response", self._destroy)
        
        self.table = gtk.Table(1,2)
        self.table.set_row_spacings(4)
        self._idx = 0
        self.exposong_stats()
        self.system_info()
        
        self.vbox.pack_start(self.table, True, True, 0)
        
        self.show_all()
    
    def exposong_stats(self):
        "Display statistics for ExpoSong."
        self.append_header(_("ExpoSong Statistics"))
        sch = exposong.schedlist.schedlist
        self.append(_("Custom Schedules"),
                    sch.get_model().iter_n_children(sch.custom_schedules))
        self.append(_("Presentations"), len(exposong.application.main.library))
    
    def system_info(self):
        "Adds the system information to the TextBuffer."
        self.append_header(_("System Information"))
        self.append(_("Platform:"), platform.system())
        if platform.system() == "Linux":
          self.append(_("Distribution:"), platform.dist())
    
    def append(self, key, val):
        "Adds a line of information."
        keylabel = self.get_label(key, True)
        vallabel = self.get_label(val)
        idx = self._new_row()
        self.table.attach(keylabel, 0, 1, idx, idx + 1, xpadding=12)
        self.table.attach(vallabel, 1, 2, idx, idx + 1, xpadding=4)
    
    def append_header(self, header):
        "Adds a header row."
        label = gtk.Label()
        label.set_markup("<b>%s</b>" % header)
        label.set_alignment(0.0, 1.0)
        idx = self._new_row()
        self.table.attach(label, 0, 2, idx, idx + 1, xpadding=4)
    
    def _new_row(self):
        "Sets the number of rows in the table."
        self._idx += 1
        self.table.resize(self._idx, 2)
        return self._idx
    
    @staticmethod
    def get_label(value, isheader = False):
        "Gets a formated label."
        label = gtk.Label(value)
        if isheader:
            label.set_alignment(1.0, 0.0)
        else:
            label.set_alignment(0.0, 0.0)
        return label
    
    def _destroy(self, win, response_id=None):
        "Close the window."
        win.destroy()

gtk.about_dialog_set_url_hook(lambda dlg, url: webbrowser.open(url))
