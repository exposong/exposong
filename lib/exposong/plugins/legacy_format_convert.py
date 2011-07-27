# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 expandtab:
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
import gtk.gdk
import shutil
from xml.etree import cElementTree as etree

import exposong.main
import exposong.slidelist
import exposong._hook
import exposong.plugins.pres
from exposong.glob import *
from exposong import DATA_PATH, theme
from exposong.plugins import Plugin, _abstract
from exposong.config import config
from openlyrics import openlyrics

"""
A converter from an old ExpoSong (< 0.8) format.
"""
information = {
        'name': _("ExpoSong Converter"),
        'description': __doc__,
        'required': False,
        }

class LegacyConvert(_abstract.ConvertPresentation, exposong._hook.Menu, Plugin):
    """
    Convert from an old ExpoSong format (< 0.8) to a new format.
    """
    
    @staticmethod
    def is_type(filename):
        """
        Should return True if this file should be converted.
        """
        fl = open(filename, 'r')
        match = r'<presentation\b[^>]*\btype=[\'"]([^"\']*)[\'"]'
        lncnt = 0
        for ln in fl:
            if lncnt > 2:
                break
            result = re.search(match, ln)
            if result and result.group(1) in ('lyric', 'text', 'image'):
                fl.close()
                return True
            lncnt += 1
        fl.close()
        return False
    
    @classmethod
    def convert(cls, filename, newfile=False):
        """
        Converts the file.
        
        filename   The name of the file for input.
        newfile    Set to True if the file is not to be overwritten.
        """
        fl = open(filename, 'r')
        flnm = False
        match = r'<presentation\b[^>]*\btype=[\'"]([^"\']*)[\'"]'
        lncnt = 0
        for ln in fl:
            if lncnt > 2:
                break
            result = re.search(match, ln)
            if result:
                fl.close()
                if result.group(1) == 'lyric':
                    flnm = cls._convert_lyric(filename, newfile)
                if result.group(1) in ('text', 'image'):
                    flnm = cls._convert_pres(filename, result.group(1), newfile)
                break
            lncnt += 1
        fl.close()
        return flnm
    
    @classmethod
    def _convert_lyric(cls, filename, newfile=False):
        "Convert a lyric file to openlyrics."
        tree = etree.parse(filename)
        if isinstance(tree, etree.ElementTree):
            root = tree.getroot()
        else:
            root = tree
        
        song = openlyrics.Song()
        title = root.findall('title')
        if title:
            song.props.titles.append(openlyrics.Title(title[0].text))
        authors = root.findall('author')
        for author in authors:
            if author.text:
                song.props.authors.append(openlyrics.Author(author.text,
                                                            author.get("type")))
        copyright_ = root.findall('copyright')
        if copyright_:
            song.props.copyright = copyright_[0].text
        order = root.findall('order')
        if order:
            song.props.order = order[0].text
        slides = root.findall('slide')
        for slide in slides:
            verse = openlyrics.Verse()
            if not slide.get("title"):
                vname = _("Undefined Title")
            else:
                vname = slide.get("title").lower()[0] \
                        + slide.get('title').partition(' ')[2]
            verse.name = vname
            lines = openlyrics.Lines()
            if slide.text: # To skip empty slides
                lines.lines = [openlyrics.Line(l) for l in
                               slide.text.split('\n')]
                verse.lines = [lines]
                song.verses.append(verse)
        if newfile:
            outfile = check_filename(title_to_filename(title[0].text),
                    os.path.join(DATA_PATH, "pres"))
        else:
            outfile = filename
        song.write(outfile)
        return outfile
    
    @classmethod
    def _convert_pres(cls, filename, type_, newfile=False):
        "Convert a text or image presentation to the new ExpoSong format."
        tree = etree.parse(filename)
        if isinstance(tree, etree.ElementTree):
            root = tree.getroot()
        else:
            root = tree
        
        pres = exposong.plugins.pres.Presentation()
        elems = root.findall("title")
        if len(elems):
            pres._title = elems[0].text
        elems = root.findall("copyright")
        if len(elems):
            pres._meta['copyright'] = elems[0].text
        elems = root.findall("timer")
        if len(elems):
            pres._timer = int(elems[0].get("time"))
            pres._timer_loop = bool(elems[0].get("loop"))
        elems = root.findall("slide")
        for sl in elems:
            slide = exposong.plugins.pres.Presentation.Slide(pres)
            slide.title = sl.get("title")
            if type_ == 'text':
                slide._content.append(theme.Text(sl.text))
            if type_ == 'image':
                osrc = sl.findall("img")[0].get("src")
                src = find_freefile(os.path.join(DATA_PATH, 'pres', 'res', osrc))
                if os.path.exists(src):
                    shutil.move(os.path.join(DATA_PATH, 'image', osrc), src)
                    slide._content.append(theme.Image(src))
            pres.slides.append(slide)
        if not newfile:
            pres.filename = filename
        pres.to_xml()
        return pres.filename
    
    @classmethod
    def import_dialog(cls, action):
        'Show the dialog for importing an ExpoSong Legacy File'
        dlg = gtk.FileChooserDialog(_("Import ExpoSong Legacy File(s)"),
                exposong.main.main, gtk.FILE_CHOOSER_ACTION_OPEN,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK,
                gtk.RESPONSE_ACCEPT))
        dlg.set_select_multiple(True)
        filt = gtk.FileFilter()
        filt.set_name(_("ExpoSong Legacy File"))
        filt.add_pattern("*.xml")
        dlg.add_filter(filt)
        dlg.set_current_folder(config.get("open-save-dialogs", "exposong_legacy-import-dir"))
        if dlg.run() == gtk.RESPONSE_ACCEPT:
            dlg.hide()
            files = dlg.get_filenames()
            for fl in files:
                filename = cls.convert(unicode(fl), True)
                exposong.main.main.load_pres(filename)
            config.set("open-save-dialogs", "exposong_legacy-import-dir", os.path.dirname(file))
        dlg.destroy()
    
    @classmethod
    def merge_menu(cls, uimanager):
        'Merge new values with the uimanager.'
        actiongroup = gtk.ActionGroup('lyric-legacy-grp')
        actiongroup.add_actions([('import-lyric-legacy', None,
                _('_ExpoSong Legacy File(s) ...'), None,
                _('Import a Lyric Presentation from ExpoSong before 0.7'),
                cls.import_dialog)])
        uimanager.insert_action_group(actiongroup, -1)
        
        cls.menu_merge_id = uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="File">
                    <menu action='file-import'>
                        <menuitem action="import-lyric-legacy" />
                    </menu>
                </menu>
            </menubar>
            """)
    
    @classmethod
    def unmerge_menu(cls, uimanager):
        'Remove merged items from the menu.'
        uimanager.remove_ui(cls.menu_merge_id)


