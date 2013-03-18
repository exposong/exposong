# -*- coding: utf-8 -*-
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

from gi.repository import Gtk
import os

from exposong_openlyrics.tools.opensong2openlyrics import OpenLyricsConverter

import exposong.main
import exposong._hook
from exposong.glob import *
from exposong import DATA_PATH
from exposong.plugins import Plugin, _abstract
from exposong.config import config

"""
A converter from OpenSong Lyrics type.
"""
information = {
        'name': _("OpenSong Lyrics Converter"),
        'description': __doc__,
        'required': False,
        }

class LyricConvert(_abstract.ConvertPresentation, exposong._hook.Menu, Plugin):
    """
    Convert from OpenSong Lyrics type to OpenLyrics.
    """
    
    @staticmethod
    def is_type(filename):
        """
        Should return True if this file should be converted.
        """
        return False
    
    @staticmethod
    def convert(filename, newfile=None):
        """
        Converts the file.
        
        filename   The name of the file for input.
        newfile    Set to True if the file is not to be overwritten.
        """
        
        if not newfile:
            newfile = os.path.join(DATA_PATH, "pres", os.path.basename(
                find_freefile(filename)))
            if not filename.endswith(".xml"):
                newfile += ".xml"
        
        converter = OpenLyricsConverter(filename)
        converter.convert()
        converter.save(newfile)
        
        return newfile
    
    @classmethod
    def import_dialog(cls, action):
        'Show the file dialog for importing OpenSong files'
        dlg = Gtk.FileChooserDialog(_("Import OpenSong File(s)"),
                exposong.main.main, Gtk.FileChooserAction.OPEN,
                (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT, Gtk.STOCK_OK,
                Gtk.ResponseType.ACCEPT))
        dlg.set_select_multiple(True)
        dlg.set_current_folder(config.get("open-save-dialogs", "opensong-import-dir"))
        if dlg.run() == Gtk.ResponseType.ACCEPT:
            dlg.hide()
            files = dlg.get_filenames()
            for f in files:
                filename = cls.convert(unicode(f))
                exposong.main.main.load_pres(filename)
            config.set("open-save-dialogs", "opensong-import-dir", os.path.dirname(f))
        dlg.destroy()
    
    @classmethod
    def merge_menu(cls, uimanager):
        'Merge new values with the uimanager.'
        actiongroup = Gtk.ActionGroup('opensong-import-grp')
        actiongroup.add_actions([('import-opensong', None,
                _('_OpenSong File(s) ...'), None,
                _('Import a Lyric Presentation from OpenSong'),
                cls.import_dialog)])
        uimanager.insert_action_group(actiongroup, -1)
        
        cls.menu_merge_id = uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="File">
                    <menu action='file-import'>
                        <menuitem action="import-opensong" />
                    </menu>
                </menu>
            </menubar>
            """)
    
    @classmethod
    def unmerge_menu(cls, uimanager):
        'Remove merged items from the menu.'
        uimanager.remove_ui(cls.menu_merge_id)
