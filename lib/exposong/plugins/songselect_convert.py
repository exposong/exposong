# -*- coding: utf-8 -*-
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

from openlyrics import openlyrics
from xml.etree import cElementTree as etree

import exposong.application
import exposong.slidelist
import exposong._hook
from exposong.glob import *
from exposong import RESOURCE_PATH, DATA_PATH
from exposong.plugins import Plugin, _abstract
from exposong.prefs import config

# TODO Possible, there is also a text format...

"""
A converter from ExpoSong (<= 0.6.2) Lyrics type.
"""
information = {
        'name': _("SongSelect Lyrics Converter"),
        'description': __doc__,
        'required': False,
        }

# Defines the version of SongSelect file to limit to.
MAX_VERSION = 3.0

class LyricConvert(_abstract.ConvertPresentation, exposong._hook.Menu, Plugin):
    """
    Convert from ExpoSong (<= 0.6.2) Lyrics type to OpenLyrics.
    """
    
    @staticmethod
    def is_type(filename):
        """
        Should return True if this file should be converted.
        """
        fl = open(filename, 'r')
        match = r'Type=SongSelect Import File'
        lncnt = 0
        for ln in fl:
            if lncnt > 2:
                break
            if re.search(match, ln):
                fl.close()
                return True
            lncnt += 1
        fl.close()
        return False
    
    @staticmethod
    def convert(filename, newfile=False):
        """
        Converts the file.
        
        filename   The name of the file for input.
        newfile    Set to True if the file is not to be overwritten.
        """
        oldfile = open(filename,'r')
        
        song = openlyrics.Song()
        verses = None
        verse_names = None
        for ln in oldfile:
            # Remove \n
            ln = ln[:-1]
            if ln == "[File]":
                continue
            elif ln.lower().startswith("[s a"):
                song.props.ccli_no = ln[4:-1]
            elif ln and "=" in ln:
                (key, val) = ln.split("=", 1)
                if key == "Version":
                    if float(val) > MAX_VERSION:
                        exposong.log.warning("SongSelect version may have unsupported features.")
                elif key == "Title":
                    song.props.titles.append(openlyrics.Title(val))
                elif key == "Author":
                    for auth in val.split("|"):
                        auth = auth.strip()
                        if "," in auth:
                            auth = ' '.join(auth.split(',',1)[::-1])
                        song.props.authors.append(openlyrics.Author(auth))
                elif key == "Copyright":
                    song.props.copyright = val
                elif key == "Admin":
                    song.props.publisher = val
                elif key == "Themes":
                    #TODO Assign ThemeIDs
                    song.props.themes = [openlyrics.Theme(t) for t in
                                         val.split("/t")]
                elif key == "Keys":
                    song.props.key = val
                elif key == "Fields":
                    verse_names = val.split("/t")
                elif key == "Words":
                    verses = val.split("/t")
                elif key == "Type":
                    pass
                else:
                    exposong.log.error("Unknown variable: %s", key)
        
        # TODO Might need extra error checking.
        for i in range(len(verses)):
            verse = openlyrics.Verse()
            #if not verses[i]:
            #  continue
            if i >= len(verse_names):
                verse.name = "m"
            elif verse_names[i].partition(' ')[0] in ('Chorus', 'Coro',
                                                      'Chorus', 'Coro'):
                verse.name = 'c'+verse_names[i].partition(' ')[2]
            elif verse_names[i].partition(' ')[0] in ('Verse', 'Estribillo',
                                                      'Vers', 'Verso'):
                verse.name = 'v'+verse_names[i].partition(' ')[2]
            else:
                miscnm = verses[i].split("/n")[0]
                if miscnm.lower().startswith("(bridge"):
                    verse.name = "b"
                    verses[i] = "/n".join(verses[i].split("/n")[1:])
                elif miscnm.lower().startswith("(end"):
                    verse.name = "e"
                    verses[i] = "\n".join(verses[i].split("\n")[1:])
            if not verse.name:
                # How should we handle this?
                verse.name = 'm'
            lines = openlyrics.Lines()
            # Intentionally "/n", as it is in the format.
            lines.lines = [openlyrics.Line(l) for l
                           in verses[i].strip("/n").split("/n")]
            verse.lines = [lines]
            song.verses.append(verse)
        
        if newfile:
            outfile = check_filename(title_to_filename(song.props.titles[0]),
                    os.path.join(DATA_PATH, "pres"))
        else:
            outfile = filename
        song.write(outfile)
        return outfile
    
    @classmethod
    def import_dialog(cls, action):
        dlg = gtk.FileChooserDialog(_("Import SongSelect Lyrics"),
                                    exposong.application.main,
                                    gtk.FILE_CHOOSER_ACTION_OPEN,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        dlg.set_select_multiple(True)
        filter = gtk.FileFilter()
        filter.set_name(_("SongSelect File (%s)") % ".usr")
        filter.add_pattern("*.usr")
        dlg.add_filter(filter)
        dlg.set_current_folder(os.path.expanduser("~"))
        if dlg.run() == gtk.RESPONSE_ACCEPT:
            dlg.hide()
            files = dlg.get_filenames()
            for file in files:
                filename = cls.convert(file, True)
                exposong.application.main.load_pres(filename)
        dlg.destroy()
    
    @classmethod
    def merge_menu(cls, uimanager):
        "Merge new values with the uimanager."
        actiongroup = gtk.ActionGroup('songselect-import-grp')
        actiongroup.add_actions([('import-songselect', None,
                                  _("_SongSelect Lyrics ..."), None,
                                  _("Converts a SongSelect file to OpenLyrics"),
                                  cls.import_dialog)])
        uimanager.insert_action_group(actiongroup, -1)
        
        cls.menu_merge_id = uimanager.add_ui_from_string("""
            <menubar name='MenuBar'>
                <menu action='File'>
                    <menu action='file-import'>
                        <menuitem action='import-songselect' />
                    </menu>
                </menu>
            </menubar>
            """)
    
    @classmethod
    def unmerge_menu(cls, uimanager):
        "Remove merged items from the menu."
        uimanager.remove_ui(cls.menu_merge_id)
