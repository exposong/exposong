#
# vim: ts=4 sw=4 expandtab ai:
#
# Copyright (C) 2008-2011 Exposong.org
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
import os
import webbrowser

import exposong._hook
from exposong import DATA_PATH

exampledata = None

class ExampleData(exposong._hook.Menu):
    'Offers example data for download.'
    def __init__(self, parent):
        pass
    
    def check_presentations(self, parent):
        "Check if any presentation exists, otherwise offer example data for download"
        if len(os.listdir(os.path.join(DATA_PATH, "pres"))) > 0:
            return
        msg = _("It seems you have no presentations yet created.\n"+\
                    "Would you like to download some example data?")
        dialog = gtk.MessageDialog(parent, gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                                   msg)
        dialog.set_title( _("Example Content") )
        resp = dialog.run()
        dialog.destroy()
        if resp == gtk.RESPONSE_YES:
            self._offer_download(parent)
    
    def _offer_download(self, parent=None):
        "Show download options for ExpoSong data"
        msg = _("1. Download the packages you want\n"+\
                "2. Import them using File->Import->ExpoSong Data (.expo)")
        dialog = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_INFO, gtk.BUTTONS_CANCEL,
                                   msg)
        dialog.set_title(_("Download Example Data"))
        downloads = {gtk.CheckButton(_("Free English Lyrics")):
            "http://exposong.googlecode.com/files/lyrics-pack1.expo",
            gtk.CheckButton(_("Background Pack")):
            "http://exposong.googlecode.com/files/background-pack1.expo"}
        for checkbutton, url in downloads.iteritems():
            dialog.vbox.pack_start(checkbutton)
            checkbutton.show()
        dialog.add_button(_("Download using Webbrowser"), gtk.RESPONSE_OK)
        dialog.show_all()
        if dialog.run() == gtk.RESPONSE_OK:
            for checkbox, url in downloads.iteritems():
                if checkbox.get_active():
                    webbrowser.open(url)
        dialog.destroy()
    
    @classmethod
    def merge_menu(cls, uimanager):
        'Merge new values with the uimanager.'
        cls._actions = gtk.ActionGroup('exampledata')
        cls._actions.add_actions([
                ('ExampleData', None, _('_Download Example Data'), None,
                        _('Offer Example Data for Download'),
                        exampledata._offer_download),
                ])
        
        uimanager.insert_action_group(cls._actions, -1)
        uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="Help">
                    <menuitem action="ExampleData" position="top" />
                </menu>
            </menubar>
            """)
