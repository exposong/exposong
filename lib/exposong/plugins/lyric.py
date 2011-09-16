# -*- coding: utf-8 -*-
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
import gtk.gdk
try:
    import gtkspell
except ImportError:
    pass
import gobject
import re
import os.path
from xml.sax.saxutils import escape, unescape

import exposong.main
import exposong.slidelist
import exposong._hook
import undobuffer
from exposong.glob import *
from exposong import RESOURCE_PATH, DATA_PATH
from exposong import gui, theme
from exposong.plugins import Plugin, _abstract
from exposong.config import config
from openlyrics import openlyrics
from exposong import version


"""
Lyric presentations.
"""
information = {
        'name': _("Song"),
        'description': __doc__,
        'required': False,
        }
type_icon = gtk.gdk.pixbuf_new_from_file_at_size(
        os.path.join(RESOURCE_PATH, 'icons', 'pres-song.png'), 20, 14)

# TODO These do not remain in order, so when creating the pull-down, the items
# are in arbitrary order.
auth_types = {
    'words': _('Words'),
    'music': _('Music'),
    'translation': _('Translation'),
    None: _('Written By'),
    }
verse_names = {
    "v": _("Verse"),
    "p": _("Pre-Chorus"),
    "c": _("Chorus"),
    "r": _("Refrain"),
    "b": _("Bridge"),
    "e": _("Ending"),
    # For Song-Select
    "m": _("Miscellaneous"),
}


class Presentation (_abstract.Presentation, Plugin, exposong._hook.Menu,
        exposong._hook.Toolbar, _abstract.Schedule, _abstract.Screen):
    '''
    Lyric presentation type.
    '''
    class Slide (_abstract.Presentation.Slide, Plugin):
        '''
        A lyric slide for the presentation.
        '''
        def __init__(self, pres, verse):
            self.pres = pres
            
            if verse:
                self.verse = verse
                self.title = verse.name
                self.lang = verse.lang
            else:
                self.verse = openlyrics.Verse()
        
        def get_text(self):
            lineList = []
            if len(self.verse.lines) > 1:
                for i in range(max(len(l.lines) for l in self.verse.lines)):
                    for lines in self.verse.lines:
                        if i < len(lines.lines):
                            lineList.append("%s: %s" % (lines.part,
                                            lines.lines[i]))
                return '\n'.join(lineList)
            elif len(self.verse.lines) == 1:
                return '\n'.join(str(l) for l in self.verse.lines[0].lines)
            else:
                return ''
        
        def set_attributes(self, layout):
            'Set attributes on a pango.Layout object.'
            #TODO
            pass
        
        def get_title(self, editing=False):
            '''Return a formatted title.
            Appends the original slide title in brackets if `editing` is True.'''
            if self.title[0] in verse_names:
                if editing and self.title[1:] == "":
                    return "%s (%s)" % (verse_names[self.title[0]], self.title)
                elif editing:
                    return "%s %s (%s)" % (verse_names[self.title[0]],
                                           self.title[1:], self.title)
                else:
                    return "%s %s" % (verse_names[self.title[0]],
                                      self.title[1:])
            else:
                return self.title
        
        def get_footer(self):
            'Return a list of renderable theme items.'
            f = [theme.Text(self.footer_text(), align=theme.CENTER, 
                 valign=theme.MIDDLE, pos=[0.25, 0.0, 0.75, 1.0], margin=5)]
            for s in self.pres.song.props.songbooks:
                if s.name == config.get("songs","songbook"):
                    f.append(theme.Text("<big>%s</big>\n<small>%s</small>" % \
                             (s.entry, s.name), pos=[0.0, 0.0, 0.25, 1.0],
                             align=theme.LEFT, valign=theme.BOTTOM, margin=5))
                    break
            return f
        
        def footer_text(self):
            'Get the footer ownership information for the centered footer.'
            jn = ['"%s"' % self.pres.title]
            # TODO List only translators for the current translation.
            author = self.pres.get_authors_string()
            if len(author) > 0:
                jn.append(escape(author))
            if len(self.pres.song.props.copyright):
                jn.append(u"Copyright \xA9 %s" % \
                          escape(self.pres.song.props.copyright))
            if config.get("songs", "ccli"):
                jn.append("CCLI# %s" % escape(config.get("songs", "ccli")))
            return '\n'.join(jn)
        
        def _edit_window(self, parent):
            'Open the Slide Editor'
            ret = False
            editor = SlideEdit(parent, self)
            ans = editor.run()
            if editor.changed:
                old_title = self.title
                self.title = editor.get_slide_title()
                self.verse.name = self.title
                self._set_lines(editor.get_slide_text())
                self.pres.rename_order(old_title, self.title)
                ret = True
            if ans == gtk.RESPONSE_APPLY:
                ret = 2
            return ret
        
        def copy(self):
            'Create a duplicate of the slide.'
            slide = Presentation.Slide(self.pres, None)
            slide.verse = openlyrics.Verse()
            slide.title = self.title
            slide.verse.name = self.title
            # TODO actually copy verses.
            slide._set_lines(self.get_text())
            slide.lang = self.verse.lang
            return slide
        
        def _set_lines(self, text):
            'Set the text from a string.'
            lines = openlyrics.Lines()
            for line in text.split('\n'):
                lines.lines.append(openlyrics.Line(line))
            self.verse.lines = [lines]
        
        @staticmethod
        def get_version():
            'Return the version number of the plugin.'
            return (1, 0)
    
        @staticmethod
        def get_description():
            'Return the description of the plugin.'
            return "A lyric presentation type."
    
    
    def __init__(self, filename=''):
        self.filename = filename
        self.slides = []
        
        if filename:
            fl = open(filename, 'r')
            if not self.is_type(fl):
                fl.close()
                raise _abstract.WrongPresentationType
            fl.close()
            
            self.song = openlyrics.Song(filename)
            for v in self.song.verses:
                self.slides.append(self.Slide(self, v))
        else:
            self.song = openlyrics.Song()
    
    def get_order_string(self):
        'Return the verse order as a string'
        return " ".join(self.song.props.verse_order)
    
    def get_slides_in_order(self, editing=False):
        """Returns the list of verses in order.
        Shows only first few words when verse appears a second time"""
        a = []
        markups = []
        if len(self.song.props.verse_order) > 0:
            for i in self.get_order():
                markup = self.slides[i].get_markup(editing)
                if not i in a:
                    a.append(i)
                    markups.append((self.slides[i], markup))
                else:
                    #Keep only the title and the first few words of the verse
                    short_markup = markup.split("\n")[:2]
                    short_markup[1] = " ".join(short_markup[1].split()[:7])
                    short_markup[1] = "%s ..."% short_markup[1]
                    markups.append((self.slides[i], "\n".join(short_markup)))
            return tuple(m for m in markups)
        else:
            return _abstract.Presentation.get_slide_list(self)
    
    def get_title_slide(self):
        'Returns a `Slide` with the song title as text'
        verse = openlyrics.Verse()
        verse.name = _("Title")
        slide = self.Slide(self, verse)
        slide._set_lines(self.get_title())
        return (slide, slide.get_markup())

    def get_order(self, custom_order=True):
        'Returns the order in which the slides should be presented.'
        if len(self.song.props.verse_order) > 0 and custom_order:
            return tuple(self.get_slide_from_order(n) for n in \
                         self.song.props.verse_order \
                         if self.get_slide_from_order(n) >= 0)
        elif not custom_order:
            pass
        else:
            return _abstract.Presentation.get_order(self)

    def get_slide_from_order(self, order_value):
        'Gets the slide index.'
        i = 0
        for sl in self.slides:
            if re.match(order_value, sl.title.lower()):
                return i
            i += 1
        exposong.log.warning("Slide in order does not exist: %s", order_value)
        return -1
    
    def _edit_tabs(self, notebook, parent):
        'Run the edit dialog for the presentation.'
        #Title field
        vbox = gtk.VBox()
        self._fields['title_list'] = gtk.ListStore(gobject.TYPE_STRING,
                gobject.TYPE_STRING)
        for title in self.song.props.titles:
            self._fields['title_list'].append( (title, title.lang) )
        title_list = gtk.TreeView(self._fields['title_list'])
        title_list.connect('row-activated', self._title_dlg, True)
        title_list.set_reorderable(True)
        # TODO Add row-activated signal for editing.
        #Toolbar
        toolbar = gtk.Toolbar()
        button = gtk.ToolButton(gtk.STOCK_ADD)
        button.connect('clicked', gui.edit_treeview_row_btn, title_list,
                       self._title_dlg)
        toolbar.insert(button, -1)
        button = gtk.ToolButton(gtk.STOCK_EDIT)
        button.connect('clicked', gui.edit_treeview_row_btn, title_list,
                       self._title_dlg, True)
        title_list.get_selection().connect('changed',
                                           gui.treesel_disable_widget, button)
        toolbar.insert(button, -1)
        button = gtk.ToolButton(gtk.STOCK_DELETE)
        button.connect('clicked', gui.del_treeview_row, title_list)
        title_list.get_selection().connect('changed',
                                           gui.treesel_disable_widget, button)
        toolbar.insert(button, -1)
        vbox.pack_start(toolbar, False, True)
        title_list.get_selection().emit('changed')
        #Table
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Title'))
        col.pack_start(cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 0)
        title_list.append_column(col)
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Language'))
        col.pack_start(cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 1)
        title_list.append_column(col)
        scroll = gtk.ScrolledWindow()
        scroll.add(title_list)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        vbox.pack_start(scroll, True, True)
        table = gui.Table(3)
        self._fields['variant'] = gui.append_entry(table, _("Variant:"),
                self.song.props.variant, 0)
        self._fields['custom_version'] = gui.append_entry(table,
                _("Custom Version:"), self.song.props.custom_version, 1)
        # TODO Change release_date to calendar
        self._fields['rel_date'] = gui.append_entry(table,
                                                    _("Release Date:"),
                                                    self.song.props.release_date,
                                                    2)
        vbox.pack_start(table, False, True)
        notebook.append_page(vbox, gtk.Label( _('Title')) )
        
        #Ownership Tab
        vbox = gtk.VBox()
        self._fields['author'] = gtk.ListStore(gobject.TYPE_STRING,
                                               gobject.TYPE_STRING,
                                               gobject.TYPE_STRING)
        for author in self.song.props.authors:
            self._fields['author'].append( (author, auth_types[author.type],
                                            author.lang) )
        author_list = gtk.TreeView(self._fields['author'])
        author_list.connect('row-activated', self._author_dlg, True)
        author_list.set_reorderable(True)
        #Toolbar
        toolbar = gtk.Toolbar()
        button = gtk.ToolButton(gtk.STOCK_ADD)
        button.connect('clicked', gui.edit_treeview_row_btn, author_list,
                       self._author_dlg)
        toolbar.insert(button, -1)
        button = gtk.ToolButton(gtk.STOCK_EDIT)
        button.connect('clicked', gui.edit_treeview_row_btn, author_list,
                       self._author_dlg, True)
        author_list.get_selection().connect('changed', gui.treesel_disable_widget,
                                            button)
        toolbar.insert(button, -1)
        button = gtk.ToolButton(gtk.STOCK_DELETE)
        button.connect('clicked', gui.del_treeview_row, author_list)
        author_list.get_selection().connect('changed', gui.treesel_disable_widget,
                                            button)
        toolbar.insert(button, -1)
        vbox.pack_start(toolbar, False, True)
        author_list.get_selection().emit('changed')
        #Table
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Author'), cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 0)
        author_list.append_column(col)
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Type'), cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 1)
        author_list.append_column(col)
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Language'), cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 2)
        author_list.append_column(col)
        scroll = gtk.ScrolledWindow()
        scroll.add(author_list)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        vbox.pack_start(scroll, True, True)
        table = gui.Table(3)
        self._fields['copyright'] = gui.append_entry(table, _('Copyright:'),
                                                     self.song.props.copyright,
                                                     0)
        self._fields['ccli_no'] = gui.append_entry(table,
                                                   _("CCLI Song ID:"),
                                                   self.song.props.ccli_no, 1)
        self._fields['publisher'] = gui.append_entry(table, _("Publisher:"),
                                                     self.song.props.publisher,
                                                     2)
        vbox.pack_start(table, False, True)
        notebook.append_page(vbox, gtk.Label( _('Ownership')) )
        
        
        #Theme field
        vbox = gtk.VBox()
        self._fields['theme'] = gtk.ListStore(gobject.TYPE_STRING,
                                              gobject.TYPE_STRING,
                                              gobject.TYPE_STRING)
        for theme in self.song.props.themes:
            self._fields['theme'].append( (theme, theme.lang, theme.id) )
        theme_list = gtk.TreeView(self._fields['theme'])
        theme_list.connect('row-activated', self._theme_dlg, True)
        theme_list.set_reorderable(True)
        #Toolbar
        toolbar = gtk.Toolbar()
        button = gtk.ToolButton(gtk.STOCK_ADD)
        button.connect('clicked', gui.edit_treeview_row_btn, theme_list,
                       self._theme_dlg)
        toolbar.insert(button, -1)
        button = gtk.ToolButton(gtk.STOCK_EDIT)
        button.connect('clicked', gui.edit_treeview_row_btn, theme_list,
                       self._theme_dlg, True)
        theme_list.get_selection().connect('changed',
                                           gui.treesel_disable_widget, button)
        toolbar.insert(button, -1)
        button = gtk.ToolButton(gtk.STOCK_DELETE)
        button.connect('clicked', gui.del_treeview_row, theme_list)
        theme_list.get_selection().connect('changed',
                                           gui.treesel_disable_widget, button)
        toolbar.insert(button, -1)
        vbox.pack_start(toolbar, False, True)
        theme_list.get_selection().emit('changed')
        #Table
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Theme'))
        col.pack_start(cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 0)
        theme_list.append_column(col)
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Language'))
        col.pack_start(cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 1)
        theme_list.append_column(col)
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('ID'))
        col.pack_start(cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 2)
        theme_list.append_column(col)
        scroll = gtk.ScrolledWindow()
        scroll.add(theme_list)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        vbox.pack_start(scroll, True, True)
        
        table = gui.Table(1)
        self._fields['keywords'] = gui.append_entry(table, _("Keywords:"),
                                                    self.song.props.keywords, 0)
        vbox.pack_start(table, False, True)
        notebook.append_page(vbox, gtk.Label( _('Theme')) )
        
        #Songbook field
        vbox = gtk.VBox()
        self._fields['songbook'] = gtk.ListStore(gobject.TYPE_STRING,
                                                 gobject.TYPE_STRING)
        for songbook in self.song.props.songbooks:
            self._fields['songbook'].append( (songbook.name, songbook.entry) )
        songbook_list = gtk.TreeView(self._fields['songbook'])
        songbook_list.connect('row-activated', self._songbook_dlg, True)
        songbook_list.set_reorderable(True)
        #Toolbar
        toolbar = gtk.Toolbar()
        button = gtk.ToolButton(gtk.STOCK_ADD)
        button.connect('clicked', gui.edit_treeview_row_btn, songbook_list,
                       self._songbook_dlg)
        toolbar.insert(button, -1)
        button = gtk.ToolButton(gtk.STOCK_EDIT)
        button.connect('clicked', gui.edit_treeview_row_btn, songbook_list,
                       self._songbook_dlg, True)
        songbook_list.get_selection().connect('changed',
                                              gui.treesel_disable_widget,
                                              button)
        toolbar.insert(button, -1)
        button = gtk.ToolButton(gtk.STOCK_DELETE)
        button.connect('clicked', gui.del_treeview_row, songbook_list)
        songbook_list.get_selection().connect('changed',
                                              gui.treesel_disable_widget,
                                              button)
        toolbar.insert(button, -1)
        vbox.pack_start(toolbar, False, True)
        songbook_list.get_selection().emit('changed')
        #Table
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Songbook Name'))
        col.pack_start(cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 0)
        songbook_list.append_column(col)
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Entry')) # As in songbook number
        col.pack_start(cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 1)
        songbook_list.append_column(col)
        scroll = gtk.ScrolledWindow()
        scroll.add(songbook_list)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        vbox.pack_start(scroll, True, True)
        
        table = gui.Table(4)
        trans_adjustment = gtk.Adjustment(int(self.song.props.transposition),
                                          -12, 12)
        self._fields['transposition'] = gui.append_spinner(table,
                                                           _("Transposition:"),
                                                           trans_adjustment, 0)
        self._fields['tempo'] = gui.append_entry(table, _("Tempo:"),
                                                 self.song.props.tempo, 1)
        # TODO Put a spinner for BPM, Combo for a string setting on same line.
        self._fields['tempo_type'] = gui.append_combo(table, _("Tempo Type:"),
                                                      (_("bpm"), _("Text")),
                                                      self.song.props.tempo_type,
                                                      2)
        key_list = ('Ab', 'A', 'A#', 'Bb', 'B', 'C', 'C#', 'Db', 'D', 'D#', 'Eb',
                    'E', 'F', 'F#', 'Gb', 'G', 'G#')
        self._fields['key'] = gui.append_combo(table, _('Key:'), key_list,
                                               self.song.props.key, 3)
        vbox.pack_start(table, False, True)
        notebook.append_page(vbox, gtk.Label( _('Music Info')) )
        
        #Other
        table = gui.Table(1)
        comments = '\n'.join(self.song.props.comments)
        self._fields['comments'] = gui.append_textview(table, _('Comments:'),
                                                       comments, 0)
        notebook.append_page(table, gtk.Label(_("Other")))
        
        # Add verses and slide order.
        vbox = gtk.VBox()
        vbox.set_border_width(4)
        vbox.set_spacing(7)
        hbox = gtk.HBox()
        
        label = gtk.Label(_("Title:"))
        label.set_alignment(0.5, 0.5)
        hbox.pack_start(label, False, True, 5)
        
        self._fields['title'] = gtk.Entry(45)
        self._fields['title'].set_text(self.get_title())
        hbox.pack_start(self._fields['title'], True, True)
        vbox.pack_start(hbox, False, True)
        
        self._fields['slides'] = gtk.ListStore(gobject.TYPE_PYOBJECT, str)
        # Add the slides
        for sl in self.get_slide_list(True):
            self._fields['slides'].append(sl)
        self._fields['slides'].connect("row-changed", self._on_slide_added)
        
        self._slide_list = gtk.TreeView(self._fields['slides'])
        self._slide_list.set_enable_search(False)
        self._slide_list.set_reorderable(True)
        # Double click to edit
        self._slide_list.connect("row-activated", self._slide_dlg, True)
        col = gtk.TreeViewColumn( _("Slide") )
        col.set_resizable(False)
        cell = gtk.CellRendererText()
        col.pack_start(cell, False)
        col.add_attribute(cell, 'markup', 1)
        self._slide_list.append_column(col)
        
        toolbar = gtk.Toolbar()
        btn = gtk.ToolButton(gtk.STOCK_ADD)
        btn.connect("clicked", gui.edit_treeview_row_btn, self._slide_list,
                       self._slide_dlg)
        toolbar.insert(btn, -1)
        btn = gtk.ToolButton(gtk.STOCK_EDIT)
        btn.connect("clicked", gui.edit_treeview_row_btn, self._slide_list,
                       self._slide_dlg, True)
        toolbar.insert(btn, -1)
        btn = gtk.ToolButton(gtk.STOCK_DELETE)
        btn.connect("clicked", self._on_slide_delete, self._slide_list, parent)
        toolbar.insert(btn, -1)
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        vbox.pack_start(toolbar, False, True)
        
        scroll = gtk.ScrolledWindow()
        scroll.add(self._slide_list)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.set_size_request(400, 250)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        vbox.pack_start(scroll, True, True)
        
        vbox.show_all()
        notebook.insert_page(vbox, gtk.Label(_("Edit")), 0)
        
        self._fields['title'].grab_focus()
        
        _abstract.Presentation._edit_tabs(self, notebook, parent)
        
        self._fields['title'].connect("changed", self._title_entry_changed)
        for event in ("row-changed","row-deleted","row-inserted","rows-reordered"):
            self._fields['title_list'].connect(event, self._title_list_changed)
        
        table = gui.Table(1)
        vorder = self.get_order_string()
        self._fields['verse_order'] = gui.append_entry(table, _("Verse Order:"),
                                                       vorder, 0)
        txt = _("Use the Slide names in brackets to modify the order")
        self._fields['verse_order'].set_tooltip_text(txt)
        notebook.get_nth_page(0).pack_start(table, False, True)
        table.show_all()
    
    def _edit_save(self):
        'Save the fields if the user clicks ok.'
        self.song.props.verse_order = self._fields['verse_order'].get_text().split()
        self.song.props.variant = self._fields['variant'].get_text()
        self.song.props.custom_version = self._fields['custom_version'].get_text()
        self.song.props.release_date = self._fields['rel_date'].get_text()
        self.song.props.copyright = self._fields['copyright'].get_text()
        self.song.props.ccli_no = self._fields['ccli_no'].get_text()
        self.song.props.publisher = self._fields['publisher'].get_text()
        self.song.props.keywords = self._fields['keywords'].get_text()
        self.song.props.transposition = self._fields['transposition'].get_text()
        self.song.props.tempo = self._fields['tempo'].get_text()
        self.song.props.tempo_type = self._fields['tempo_type'].get_active_text()
        self.song.props.key = self._fields['key'].get_active_text()
        
        self.song.props.titles = []
        for row in self._fields['title_list']:
            self.song.props.titles.append(openlyrics.Title(*row))
        
        self.song.props.authors = []
        for row in self._fields['author']:
            for (k,v) in auth_types.iteritems():
                if v == row[1]:
                    atype = k
                    break
            else:
                atype = None
            self.song.props.authors.append(openlyrics.Author(row[0], atype,
                                                             row[2]))
        
        self.song.props.songbooks = []
        for row in self._fields['songbook']:
            self.song.props.songbooks.append(openlyrics.Songbook(*row))
        
        self.song.props.themes = []
        for row in self._fields['theme']:
            self.song.props.themes.append(openlyrics.Theme(row[0], row[2], row[1]))
        
        self.song.props.comments = self._fields['comments'].get_buffer().get_text(
                *self._fields['comments'].get_buffer().get_bounds()).split('\n')
        
        itr = self._fields['slides'].get_iter_first()
        self.slides = []
        self.song.verses = []
        while itr:
            slide = self._fields['slides'].get_value(itr,0)
            self.slides.append(slide)
            self.song.verses.append(slide.verse)
            itr = self._fields['slides'].iter_next(itr)
    
    def _slide_dlg(self, treeview, path, col, edit=False):
        "Create a dialog for a new slide."
        model = treeview.get_model()
        if edit:
            itr = model.get_iter(path)
            if not itr:
                return False
            # Edit on a copy, so Cancel will work.
            sl = model.get_value(itr, 0).copy()
            old_title = sl.title
        else:
            sl = self.Slide(self, None)
        
        ans = sl._edit_window(treeview.get_toplevel())
        if ans:
            if edit:
                if len(old_title) == 0 or old_title != sl.title:
                    sl._set_id()
                model.set(itr, 0, sl, 1, sl.get_markup(True))
            else:
                sl._set_id()
                model.append( (sl, sl.get_markup(True)) )
        if ans == 2:
            self._slide_dlg(treeview, None, None)
    
    def _on_slide_added(self, model, path, iter):
        self._slide_list.set_cursor(path)
        
    def _on_slide_delete(self, btn, treeview, parent):
        'Remove the selected slide.'
        (model, itr) = treeview.get_selection().get_selected()
        if not itr:
            return False
        msg = _('Are you sure you want to delete this slide? This cannot be undone.')
        dialog = gtk.MessageDialog(exposong.main.main, gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
                                   msg)
        dialog.set_title( _('Delete Slide?') )
        resp = dialog.run()
        dialog.hide()
        if resp == gtk.RESPONSE_YES:
            model.remove(itr)
    
    def _title_dlg(self, treeview, path, col, edit=False):
        "Add or edit a title."
        dialog = gtk.Dialog(_("New Title"), treeview.get_toplevel(),
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        table = gui.Table(2)
        dialog.vbox.pack_start(table, True, True)
        
        model = treeview.get_model()
        title_value = lang_value = None
        if edit:
            itr = model.get_iter(path)
            if model.get_value(itr,0):
                dialog.set_title( _('Editing Title "%s"') % model.get_value(itr,0) )
                title_value = model.get_value(itr,0)
            if model.get_value(itr,1):
                lang_value = model.get_value(itr,1)
        
        title = gui.append_entry(table, _("Title:"), title_value, 0)
        lang = gui.append_language_combo(table, lang_value, 1)
        dialog.vbox.show_all()
        
        while True:
            if dialog.run() == gtk.RESPONSE_ACCEPT:
                if not title.get_text():
                    info_dialog = gtk.MessageDialog(treeview.get_toplevel(),
                                                    gtk.DIALOG_DESTROY_WITH_PARENT,
                                                    gtk.MESSAGE_INFO,
                                                    gtk.BUTTONS_OK,
                                                    _("Please enter a Title."))
                    info_dialog.run()
                    info_dialog.destroy()
                else:
                    if edit:
                        model.set_value(itr, 0, title.get_text())
                        model.set_value(itr, 1, lang.get_active_text())
                    else:
                        self._fields['title_list'].append((title.get_text(),
                                                          lang.get_active_text()))
                    dialog.hide()
                    return True
            else:
                dialog.hide()
                return False
    
    def _author_dlg(self, treeview, path, col, edit=False):
        "Add or edit an author."
        dialog = gtk.Dialog(_("New Author"), treeview.get_toplevel(),
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        table = gui.Table(3)
        dialog.vbox.pack_start(table, True, True)
        
        model = treeview.get_model()
        author_value = type_value = lang_value = None
        if edit:
            itr = model.get_iter(path)
            if model.get_value(itr,0):
                dialog.set_title( _('Editing Author "%s"') % model.get_value(itr,0) )
            author_value = model.get_value(itr,0)
            for (k,v) in auth_types.iteritems():
                if v == model.get_value(itr,1):
                    type_value = k
                    break
            else:
                type_value = None
            lang_value = model.get_value(itr,2)
        
        
        authors = [a.name for t in exposong.main.main.library
                     if t[0].get_type() == "song"
                     for a in t[0].song.props.authors]
        authors = sorted(set(authors))
        
        author = gui.append_combo_entry(table, _('Author Name:'),
                                        authors, author_value, 0)
        type = gui.append_combo2(table, _('Author Type:'),
                                 tuple(auth_types.iteritems()), type_value, 1)
        tmodel = type.get_model()
        lang = gui.append_language_combo(table, lang_value, 2)
        type.connect('changed', lambda combo: lang.set_sensitive(
                     tmodel.get_value(type.get_active_iter(),0)=='translation') )
        type.emit('changed')
        dialog.vbox.show_all()
        
        while True:
            if dialog.run() == gtk.RESPONSE_ACCEPT:
                if not author.get_active_text():
                    info_dialog = gtk.MessageDialog(treeview.get_toplevel(),
                                            gtk.DIALOG_DESTROY_WITH_PARENT,
                                            gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
                                            _("Please enter an Author Name."))
                    info_dialog.run()
                    info_dialog.destroy()
                else:
                    val = tmodel.get_value(type.get_active_iter(),1)
                    if edit:
                        model.set_value(itr, 0, author.get_active_text())
                        model.set_value(itr, 1, val)
                        if tmodel.get_value(type.get_active_iter(),0) == 'translation':
                            model.set_value(itr, 2, lang.get_active_text())
                    else:
                        self._fields['author'].append( (author.get_active_text(), val,
                                                    lang.get_active_text()))
                    dialog.hide()
                    return True
            else:
                dialog.hide()
                return False
    
    def _theme_dlg(self, treeview, path, col, edit=False):
        "Add or edit a theme."
        dialog = gtk.Dialog(_("New Theme"), treeview.get_toplevel(),\
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
                (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        table = gui.Table(2)
        dialog.vbox.pack_start(table, True, True)
        
        model = treeview.get_model()
        theme_value = lang_value = None
        if edit:
            itr = model.get_iter(path)
            if model.get_value(itr,0):
                dialog.set_title( _('Editing Theme "%s"') % model.get_value(itr,0) )
            theme_value = model.get_value(itr,0)
            lang_value = model.get_value(itr,1)
        themes = [thm.name for t in exposong.main.main.library
                     if t[0].get_type() == "song"
                     for thm in t[0].song.props.themes]
        themes = sorted(set(themes))
        theme_ = gui.append_combo_entry(table, _('Theme Name:'),
                                          themes, theme_value, 0)
        #theme = gui.append_entry(table, _('Theme Name:'), theme_value, 0)
        lang = gui.append_language_combo(table, lang_value, 1)
        dialog.vbox.show_all()
        
        while True:
            if dialog.run() == gtk.RESPONSE_ACCEPT:
                if not theme_.get_active_text():
                    info_dialog = gtk.MessageDialog(treeview.get_toplevel(),
                            gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO,
                            gtk.BUTTONS_OK, _("Please enter an Theme Name."))
                    info_dialog.run()
                    info_dialog.destroy()
                else:
                    if edit:
                        model.set_value(itr, 0, theme_.get_active_text())
                        model.set_value(itr, 1, lang.get_active_text())
                    else:
                        self._fields['theme'].append( (theme_.get_active_text(),
                                lang.get_active_text(), "") )
                    dialog.hide()
                    return True
            else:
                dialog.hide()
                return False
    
    def _songbook_dlg(self, treeview, path, col, edit=False):
        "Add or edit a songbook."
        dialog = gtk.Dialog(_("New songbook"), treeview.get_toplevel(),
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK,
                gtk.RESPONSE_ACCEPT))
        table = gui.Table(2)
        dialog.vbox.pack_start(table, True, True)
        
        model = treeview.get_model()
        songbook_value = entry_value = None
        if edit:
            itr = model.get_iter(path)
            if model.get_value(itr,0):
                dialog.set_title( _('Editing Songbook "%s"') % model.get_value(itr,0) )
            songbook_value = model.get_value(itr,0)
            entry_value = model.get_value(itr,1)
        songbooks = [sbook.name for t in exposong.main.main.library
                     if t[0].get_type() == "song"
                     for sbook in t[0].song.props.songbooks]
        songbooks = sorted(set(songbooks))
        songbook = gui.append_combo_entry(table, _('Songbook Name:'),
                                          songbooks, songbook_value, 0)
        entry = gui.append_entry(table, _('Entry:'), entry_value, 1)
        dialog.vbox.show_all()
        
        while True:
            if dialog.run() == gtk.RESPONSE_ACCEPT:
                if not songbook.get_active_text():
                    info_dialog = gtk.MessageDialog(treeview.get_toplevel(),
                            gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO,
                            gtk.BUTTONS_OK, _("Please enter a Songbook."))
                    info_dialog.run()
                    info_dialog.destroy()
                else:
                    if edit:
                        model.set_value(itr, 0, songbook.get_active_text())
                        model.set_value(itr, 1, entry.get_active_text())
                    else:
                        self._fields['songbook'].append( (songbook.get_active_text(),
                                entry.get_text()) )
                    dialog.hide()
                    return True
            else:
                dialog.hide()
                return False
    
    def _paste_as_text(self, *args):
        "Dialog to paste full lyrics."
        # TODO Redo this dialog
        pass
    
    def _is_editing_complete(self, parent):
        "Test to see if all fields have been filled which are required."
        if len(self._fields['title_list']) == 0:
            info_dialog = gtk.MessageDialog(parent, gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
                    _("You must enter at least one title."))
            info_dialog.run()
            info_dialog.destroy()
            return False
        return _abstract.Presentation._is_editing_complete(self, parent)
    
    def to_xml(self):
        'Save the data to disk.'
        if self.filename:
            self.filename = check_filename(self.get_title(), self.filename)
            self.song.modifiedIn = "ExpoSong %s"% exposong.version.__version__
        else:
            self.filename = check_filename(self.get_title(),
                    os.path.join(DATA_PATH, "pres"))
            self.song.createdIn = "ExpoSong %s"% exposong.version.__version__
        self.song.write(self.filename)
    
    def get_title(self):
        if len(self.song.props.titles) == 0:
            return os.path.basename(self.filename)
        return str(self.song.props.titles[0])
    
    title = property(get_title)
    
    def _title_entry_changed(self, entry):
        'The title entry has changed.'
        if getattr(self,'_title_lock', False):
            return
        self._title_lock = True
        lst = self._fields['title_list']
        if not lst.get_iter_first():
            lst.append()
        lst.set_value(lst.get_iter_first(), 0, entry.get_text())
        self._title_lock = False
    
    def _title_list_changed(self, model, path, iter=None, new_order=None):
        'The title list has been changed.'
        if getattr(self,'_title_lock', False):
            return
        self._title_lock = True
        val = model.get_value(model.get_iter_first(), 0)
        if val:
            self._fields['title'].set_text(val)
        else:
            self._fields['title'].set_text('')
        self._title_lock = False
    
    def rename_order(self, old_title, new_title):
        'If a slide title was changed, update the order with the new title.'
        if old_title == new_title:
            return
        order = self._fields['verse_order'].get_text().split()
        for i in range(len(order)):
            if order[i] == old_title:
                order[i] = new_title
        self._fields['verse_order'].set_text(" ".join(order))

    def get_authors_string(self):
        """"
        Returns a string with the authors of the song.
        Summarizes multiple occurrences
        e.g.: Text & Music: Author A   OR   Text: Author A / Author B
        """
        authlist = []
        for a in self.song.props.authors:
            auth_type = auth_types.get(a.type, _("Written By"))
            same = False
            for auth in authlist:
                if auth[0] == auth_type:
                    auth[1] = "%s / %s"% (auth[1], str(a))
                    same = True
            if not same:
                for auth in authlist:
                    if auth[1] == str(a):
                        auth[0] = "%s & %s"% (auth[0], auth_type)
                        same = True
            if not same:
                authlist.append([auth_type, str(a)])
        s = "; ".join(u'%s: %s'%(a[0], a[1]) for a in authlist)
        return s
    
    def get_print_markup(self):
        "Return the presentation markup for printing."
        markup = "<span face='sans' weight='bold' size='large'>%s</span>\n"\
                 % self.get_title()
        info = []
        if self.song.props.authors:
            info.append(escape(self.get_authors_string()))
        if self.song.props.copyright:
            info.append(u"Copyright \xA9 %s" % escape(self.song.props.copyright))
        if config.get("songs", "ccli"):
            info.append("CCLI# %s" % escape(config.get("songs", "ccli")))
        if self.song.props.songbooks:
            info.append("; ".join(u'%s\xA0#%s' % (escape(s.name), escape(s.entry))
                        for s in self.song.props.songbooks))
        if self.song.props.verse_order:
            verses = _("Order:")
            for v in self.song.props.verse_order:
                verses += " %s" %verse_names[v[0]]
                if v[1:]:
                    verses += " %s"%v[1:]
                verses += ","
            verses = verses.strip(",") #remove last comma
            info.append(verses)
        markup += "<span face='sans' style='italic' size='x-small'>%s</span>\n"\
                 % "\n".join(info)
        markup += "\n\n"
        # Should this print the slides in order, or just the order list?
        ##  I think the order list is ok. In Songbooks you also have each verse only once
        for slide in self.get_slide_list():
            markup += "<span weight='bold' face='sans' size='%%(fontsize)d'>%s</span>\n"\
                      % slide[0].get_title()
            markup += "<span face='sans' size='%%(fontsize)d'>%s</span>\n\n"\
                      % slide[0].get_text()
        return markup
    
    def can_print(self):
        "Return True if printing is available."
        return True
    
    @classmethod
    def is_type(cls, fl):
        "Test to see if this file is the correct type."
        match = r'<song\b'
        lncnt = 0
        for ln in fl:
            if lncnt > 2:
                break
            if re.search(match, ln):
                return True
            lncnt += 1
        return False
    
    @staticmethod
    def get_type_name():
        'Return the presentation type.'
        return information['name']
    
    @staticmethod
    def get_type():
        'Return the presentation type.'
        return 'song'
    
    @staticmethod
    def get_icon():
        'Return the pixbuf icon.'
        return type_icon
    
    @classmethod
    def merge_menu(cls, uimanager):
        'Merge new values with the uimanager.'
        gtk.stock_add([("pres-song",_("_Song"), gtk.gdk.MOD1_MASK, 0,
                        "pymserv")])
        
        actiongroup = gtk.ActionGroup('exposong-song')
        actiongroup.add_actions([("pres-new-song", 'pres-song-new', _("New Song"), "<Ctrl>n",
                                _("New Song"), cls._on_pres_new)])
        uimanager.insert_action_group(actiongroup, -1)
        
        cls.menu_merge_id = uimanager.add_ui_from_string("""
            <menubar name='MenuBar'>
                <menu action="File">
                        <menu action="file-new">
                            <placeholder name="file-new-song">
                                <menuitem action='pres-new-song' />
                            </placeholder>
                        </menu>
                </menu>
            </menubar>
            """)
    
    @classmethod
    def unmerge_menu(cls, uimanager):
        'Remove merged items from the menu.'
        uimanager.remove_ui(cls.menu_merge_id)

    @classmethod
    def merge_toolbar(cls, uimanager):
        'Merge new values with the uimanager'
        cls.tb_merge_id = uimanager.add_ui_from_string("""
            <toolbar name='Toolbar'>
                <placeholder name="file-new-song">
                    <toolitem action='pres-new-song' />
                </placeholder>
            </toolbar>
            """)
    
    @classmethod
    def unmerge_toolbar(cls, uimanager):
        'Remove merged items from the toolbar.'
        uimanager.remove_ui(cls.tb_merge_id)
    
    @classmethod
    def schedule_name(cls):
        'Return the string schedule name.'
        return _('Songs')
    
    @classmethod
    def schedule_filter(cls, pres):
        'Called on each presentation, and return True if it can be added.'
        return pres.__class__ is cls
    
    @staticmethod
    def get_version():
        'Return the version number of the plugin.'
        return (1, 0)
    
    @staticmethod
    def get_description():
        'Return the description of the plugin.'
        return "A Song presentation type."


class SlideEdit(gtk.Dialog):
    'A slide editing dialog.'
    def __init__(self, parent, slide):
        gtk.Dialog.__init__(self, _("Editing Slide"), parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        
        self._build_menu()
        
        cancelbutton = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        cancelbutton.connect("clicked", self._quit_without_save)
        newbutton = self.add_button(_("Save and New"), gtk.RESPONSE_APPLY)
        newimg = gtk.Image()
        newimg.set_from_stock(gtk.STOCK_NEW, gtk.ICON_SIZE_BUTTON)
        newbutton.set_image(newimg)
        newbutton.connect("clicked", self._quit_with_save)
        okbutton = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        okbutton.connect("clicked", self._quit_with_save)
        
        self.connect("delete-event", self._quit_without_save)
        
        #TODO: unescape() temporarily until HTML Editor
        self.slide_title = unescape(slide.title)
        self.slide_text = unescape(slide.get_text())
        self.changed = False
        
        self.set_border_width(4)
        self.vbox.set_spacing(7)
        
        # Title
        self.vbox.pack_start(self._get_title_box(), False, True)
        
        # Toolbar
        self._toolbar = gtk.Toolbar()
        self.undo_btn = self._get_toolbar_item(gtk.ToolButton(gtk.STOCK_UNDO),
                                               self._undo, False)
        self.redo_btn = self._get_toolbar_item(gtk.ToolButton(gtk.STOCK_REDO),
                                               self._redo, False)
        self.vbox.pack_start(self._toolbar, False, True)
        
        self._buffer = self._get_buffer()
        self._buffer.connect("changed", self._on_text_changed)
        
        text = gtk.TextView()
        text.set_wrap_mode(gtk.WRAP_NONE)
        text.set_buffer(self._buffer)
        try:
            gtkspell.Spell(text)
        except Exception:
            pass
        scroll = gtk.ScrolledWindow()
        scroll.add(text)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.set_size_request(450, 250)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        self.vbox.pack_start(scroll, True, True)
        
        self.vbox.show_all()
    
    def _build_menu(self):
        self.uimanager = gtk.UIManager()
        self.add_accel_group(self.uimanager.get_accel_group())
        self._actions = gtk.ActionGroup('main')
        self._actions.add_actions([
                ('Edit', None, '_Edit' ),
                ("edit-undo", gtk.STOCK_UNDO, "Undo",
                    "<Ctrl>z", "Undo the last operation", self._undo),
                ("edit-redo", gtk.STOCK_REDO, "Redo",
                    "<Ctrl>y", "Redo the last operation", self._redo)
                ])
        self.uimanager.insert_action_group(self._actions, 0)
        self.uimanager.add_ui_from_string('''
                <menubar name='MenuBar'>
                    <menu action='Edit'>
                        <menuitem action='edit-undo'/>
                        <menuitem action='edit-redo'/>
                    </menu>
                </menubar>''')
    
    def _get_title_box(self):
        hbox = gtk.HBox()
        label = gtk.Label(_("Name:"))
        label.set_alignment(0.5,0.5)
        hbox.pack_start(label, False, True, 1)
        
        title_list = gtk.ListStore(str, str)
        self._title_entry = gtk.ComboBox(title_list)
        if not self.slide_title:
            self.slide_title = "v"
        for (abbr, name) in verse_names.iteritems():
            itr = title_list.append( (abbr, name) )
            if self.slide_title[0] == abbr:
                self._title_entry.set_active_iter(itr)
        cell = gtk.CellRendererText()
        self._title_entry.pack_start(cell, True)
        self._title_entry.add_attribute(cell, 'text', 1)
        hbox.pack_start(self._title_entry, True, True, 1)
        
        label = gtk.Label(" "+_("Index:"))
        label.set_alignment(0.5,0.5)
        hbox.pack_start(label, False, True, 1)
        
        self._title_num = gtk.Entry(4)
        self._title_num.set_text(self.slide_title[1:])
        self._title_num.set_width_chars(4)
        hbox.pack_start(self._title_num, False, True, 1)
        
        return hbox

    def _get_title_value(self):
        itr = self._title_entry.get_active_iter()
        return self._title_entry.get_model().get_value(itr, 0) \
                + self._title_num.get_text()
    
    def _get_toolbar_item(self, toolbutton, proxy, sensitive=True):
        btn = toolbutton
        btn.set_sensitive(sensitive)
        btn.connect('clicked', proxy)
        self._toolbar.insert(btn, -1)
        return btn
    
    def _get_buffer(self):
        buffer = undobuffer.UndoableBuffer()
        buffer.begin_not_undoable_action()
        buffer.set_text(self.slide_text)
        buffer.end_not_undoable_action()
        buffer.set_modified(False)
        return buffer
    
    def get_slide_title(self):
        "Returns the title of the edited slide."
        return self.slide_title
    
    def get_slide_text(self):
        "Returns the text of the edited slide."
        return self.slide_text
    
    def _save(self):
        #TODO: escape() temporarily until HTML Editor
        self.slide_title = escape(self._get_title_value())
        bounds = self._buffer.get_bounds()
        self.slide_text = escape(self._buffer.get_text(bounds[0], bounds[1]))
        self.changed = True
    
    def _ok_to_continue(self):
        if self._buffer.can_undo or self._get_title_value() != self.slide_title:
            msg = _('Unsaved Changes exist. Do you want to continue without saving?')
            dlg = gtk.MessageDialog(self, gtk.DIALOG_MODAL,
                    gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, msg)
            resp = dlg.run()
            dlg.destroy()
            if resp == gtk.RESPONSE_NO:
                return False
        self.changed = False
        return True
    
    def _on_text_changed(self, event):
        self.undo_btn.set_sensitive(self._buffer.can_undo)
        self.redo_btn.set_sensitive(self._buffer.can_redo)
        if self._buffer.can_undo:
            if not self.get_title().startswith("*"):
                self.set_title("*%s"%self.get_title())
        else:
            self.set_title(self.get_title().lstrip("*"))
    
    def _undo(self, event):
        self._buffer.undo()
    
    def _redo(self, event):
        self._buffer.redo()
    
    def _quit_with_save(self, event, *args):
        if self._get_title_value() == "":
            info_dialog = gtk.MessageDialog(self,
                    gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO,
                    gtk.BUTTONS_OK, _("Please enter a Title."))
            info_dialog.run()
            info_dialog.destroy()
            self._title_entry.grab_focus()
            return False
        self._save()
        self.destroy()
    
    def _quit_without_save(self, event, *args):
        if self._ok_to_continue():
            self.destroy()

