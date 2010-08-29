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
import gobject
import pango
import re
import string
import os.path
import xml.dom
import xml.dom.minidom
from datetime import datetime

from openlyrics import openlyrics
import undobuffer

import exposong.application
import exposong.slidelist
from exposong.glob import *
from exposong import RESOURCE_PATH, DATA_PATH
from exposong import gui
from exposong.plugins import Plugin, _abstract, text
from exposong.prefs import config


"""
Lyric presentations.
"""
information = {
    'name': _("Lyric Presentation"),
    'description': __doc__,
    'required': False,
    }
type_icon = gtk.gdk.pixbuf_new_from_file_at_size(
    os.path.join(RESOURCE_PATH,'pres_lyric.png'), 20, 14)

# TODO These do not remain in order, so when creating the pull-down, the items
# are in arbitrary order.
auth_types = {
  "words": _("Words"),
  "music": _("Music"),
  "translation": _("Translation"),
  }
verse_names = {
  "v": _("Verse"),
  "p": _("Pre-Chorus"),
  "c": _("Chorus"),
  "r": _("Refrain"),
  "b": _("Bridge"),
  "e": _("Ending"),
}

def key_shortcuts(accel_group, acceleratable, keyval, modifier):
  'Adds the shortcuts to skip to a given slide.'
  pres = exposong.slidelist.slidelist.pres
  if pres != None:
    slnum = None
    if chr(keyval) in string.ascii_letters:
      slnum = pres.get_slide_from_order(chr(keyval))
    elif chr(keyval) >= '0' and chr(keyval) <= '9':
      slnum = pres.get_slide_from_order("v%s" % chr(keyval))
    if(slnum != None):
      exposong.slidelist.slidelist.to_slide(slnum)

_lyrics_accel = gtk.AccelGroup()
_lyrics_accel.connect_group(ord("c"), 0,0, key_shortcuts)
_lyrics_accel.connect_group(ord("r"), 0,0, key_shortcuts)
_lyrics_accel.connect_group(ord("b"), 0,0, key_shortcuts)
_lyrics_accel.connect_group(ord("e"), 0,0, key_shortcuts)
for i in range(1,10):
  _lyrics_accel.connect_group(ord("%d"%i), 0,0, key_shortcuts)


class Presentation (text.Presentation, Plugin, _abstract.Menu,
    _abstract.Schedule, _abstract.Screen):
  '''
  Lyric presentation type.
  '''
  class Slide (text.Presentation.Slide, Plugin):
    '''
    A lyric slide for the presentation.
    '''
    def __init__(self, pres, verse):
      lines = []
      self.pres = pres
      
      if verse:
        self.verse = verse
        self.title = verse.name
        self.lang = verse.lang
        lineList = []
        if len(verse.lines) > 1:
          for i in range(max(len(l.lines) for l in verse.lines)):
            for lines in verse.lines:
              if i < len(lines.lines):
                lineList.append("%s: %s" % (lines.part, lines.lines[i]))
          self.text = '\n'.join(lineList)
        elif len(verse.lines) == 1:
          self.text = '\n'.join(str(l) for l in verse.lines[0].lines)
      else:
        self.verse = openlyrics.Verse()
    
    def set_attributes(self, layout):
      'Set attributes on a pango.Layout object.'
      #TODO
      pass
    
    def get_title(self, editing=False):
      'Return a formatted title.'
      if self.title[0] in verse_names:
        if editing:
          return "%s %s (%s)" % (verse_names[self.title[0]], self.title[1:],
                            self.title)
        else:
          return "%s %s" % (verse_names[self.title[0]], self.title[1:])
      else:
        return self.title
    
    def footer_text(self):
      'Draw text on the footer.'
      jn = ['"%s"' % self.pres.title]
      # TODO List only translators for the current translation.
      author = ';  '.join(u'%s: %s' % (auth_types.get(a.type,_("Written By")),
          str(a)) for a in self.pres.song.props.authors )
      if len(author) > 0:
        jn.append(author)
      if len(self.pres.song.props.copyright):
        jn.append(u"Copyright \xA9 %s" % self.pres.song.props.copyright)
      if config.get("general", "ccli"):
        jn.append("Song CCLI ID# %s; CCLI# %s" % (self.pres.song.props.ccli_no,
            config.get("general", "ccli")))
      songbooks = "; ".join(u'%s\xA0#%s' % (s.name, s.entry) for s in
          self.pres.song.props.songbooks)
      if len(songbooks):
        jn.append(songbooks)
      return '\n'.join(jn)
    
    def _edit_window(self, parent):
      editor = SlideEdit(parent, self)
      editor.run()
      if editor.changed:
        old_title = self.title
        self.title = editor.get_slide_title()
        self.verse.name = self.title
        self._set_lines(editor.get_slide_text())
        self.pres._rename_order(old_title, self.title)
        return True
      return False
    
    def copy(self):
      'Create a duplicate of the slide.'
      slide = Presentation.Slide(self.pres, None)
      slide.verse = openlyrics.Verse()
      slide.title = self.title
      slide.verse.name = self.title
      slide._set_lines(self.text)
      slide.lang = self.verse.lang
      return slide
    
    def _set_lines(self, text):
      'Set the text from a string.'
      self.text = text
      lines = openlyrics.Lines()
      for line in self.text.split('\n'):
        lines.lines.append(openlyrics.Line(line))
      self.verse.lines = [lines]
    
    @staticmethod
    def get_version():
      'Return the version number of the plugin.'
      return (1,0)
  
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
      self.song.createdIn = "ExpoSong"
  
  def get_order(self):
    'Returns the order in which the slides should be presented.'
    if len(self.song.props.verse_order) > 0:
      return tuple(self.get_slide_from_order(n) for n in
          self.song.props.verse_order if self.get_slide_from_order(n) >= 0)
    else:
      return _abstract.Presentation.get_order(self)

  def get_slide_from_order(self, order_value):
    'Gets the slide index.'
    i = 0
    for sl in self.slides:
      if re.match(order_value,sl.title.lower()):
        return i
      i += 1
    print "Slide in order does not exist: %s" % order_value
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
    button.connect('clicked', self._title_dlg_btn, title_list)
    toolbar.insert(button, -1)
    button = gtk.ToolButton(gtk.STOCK_EDIT)
    button.connect('clicked', self._title_dlg_btn, title_list, True)
    title_list.get_selection().connect('changed', gui.treesel_disable_widget,
        button)
    toolbar.insert(button, -1)
    button = gtk.ToolButton(gtk.STOCK_DELETE)
    button.connect('clicked', self._del_treeview_row, title_list)
    title_list.get_selection().connect('changed', gui.treesel_disable_widget,
        button)
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
    self._fields['release_date'] = gui.append_entry(table, _("Release Date:"),
        self.song.props.release_date, 2)
    vbox.pack_start(table, False, True)
    notebook.append_page(vbox, gtk.Label( _('Title')) )
    
    #Ownership Tab
    vbox = gtk.VBox()
    self._fields['author'] = gtk.ListStore(gobject.TYPE_STRING,
        gobject.TYPE_STRING, gobject.TYPE_STRING)
    for author in self.song.props.authors:
      self._fields['author'].append( (author, author.type, author.lang) )
    author_list = gtk.TreeView(self._fields['author'])
    author_list.connect('row-activated', self._author_dlg, True)
    author_list.set_reorderable(True)
    #Toolbar
    toolbar = gtk.Toolbar()
    button = gtk.ToolButton(gtk.STOCK_ADD)
    button.connect('clicked', self._author_dlg_btn, author_list)
    toolbar.insert(button, -1)
    button = gtk.ToolButton(gtk.STOCK_EDIT)
    button.connect('clicked', self._author_dlg_btn, author_list, True)
    author_list.get_selection().connect('changed', gui.treesel_disable_widget,
        button)
    toolbar.insert(button, -1)
    button = gtk.ToolButton(gtk.STOCK_DELETE)
    button.connect('clicked', self._del_treeview_row, author_list)
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
        self.song.props.copyright, 0)
    self._fields['ccli_no'] = gui.append_entry(table, _("CCLI Number:"),
        self.song.props.ccli_no, 1)
    self._fields['publisher'] = gui.append_entry(table, _("Publisher:"),
        self.song.props.publisher, 2)
    vbox.pack_start(table, False, True)
    notebook.append_page(vbox, gtk.Label( _('Ownership')) )
    
    
    #Theme field
    vbox = gtk.VBox()
    self._fields['theme'] = gtk.ListStore(gobject.TYPE_STRING,
        gobject.TYPE_STRING, gobject.TYPE_STRING)
    for theme in self.song.props.themes:
      self._fields['theme'].append( (theme, theme.lang, theme.id) )
    theme_list = gtk.TreeView(self._fields['theme'])
    theme_list.connect('row-activated', self._theme_dlg, True)
    theme_list.set_reorderable(True)
    #Toolbar
    toolbar = gtk.Toolbar()
    button = gtk.ToolButton(gtk.STOCK_ADD)
    button.connect('clicked', self._theme_dlg_btn, theme_list)
    toolbar.insert(button, -1)
    button = gtk.ToolButton(gtk.STOCK_EDIT)
    button.connect('clicked', self._theme_dlg_btn, theme_list, True)
    theme_list.get_selection().connect('changed', gui.treesel_disable_widget,
        button)
    toolbar.insert(button, -1)
    button = gtk.ToolButton(gtk.STOCK_DELETE)
    button.connect('clicked', self._del_treeview_row, theme_list)
    theme_list.get_selection().connect('changed', gui.treesel_disable_widget,
        button)
    toolbar.insert(button, -1)
    vbox.pack_start(toolbar, False, True)
    theme_list.get_selection().emit('changed')
    #Table
    #Columns
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
    button.connect('clicked', self._songbook_dlg_btn, songbook_list)
    toolbar.insert(button, -1)
    button = gtk.ToolButton(gtk.STOCK_EDIT)
    button.connect('clicked', self._songbook_dlg_btn, songbook_list, True)
    songbook_list.get_selection().connect('changed', gui.treesel_disable_widget,
        button)
    toolbar.insert(button, -1)
    button = gtk.ToolButton(gtk.STOCK_DELETE)
    button.connect('clicked', self._del_treeview_row, songbook_list)
    songbook_list.get_selection().connect('changed', gui.treesel_disable_widget,
        button)
    toolbar.insert(button, -1)
    vbox.pack_start(toolbar, False, True)
    songbook_list.get_selection().emit('changed')
    #Columns
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
    self._fields['transposition'] = gui.append_spinner(table,
        _("Transposition:"), gtk.Adjustment(int(self.song.props.transposition),
        -12, 12), 0)
    self._fields['tempo'] = gui.append_entry(table, _("Tempo:"),
        self.song.props.tempo, 1)
    # TODO Put a spinner for BPM, Combo for a string setting on same line.
    self._fields['tempo_type'] = gui.append_combo(table, _("Tempo Type:"),
        (_("bpm"), _("Text")), self.song.props.tempo_type, 2)
    key_list = ('Ab', 'A', 'A#', 'Bb', 'B', 'C', 'C#', 'Db', 'D', 'D#', 'Eb',
        'E', 'F', 'F#', 'Gb', 'G', 'G#')
    self._fields['key'] = gui.append_combo(table, _('Key:'), key_list,
        self.song.props.key, 3)
    vbox.pack_start(table, False, True)
    notebook.append_page(vbox, gtk.Label( _('Music Info')) )
    
    #Other
    table = gui.Table(1)
    self._fields['comments'] = gui.append_textview(table, _('Comments:'),
        '\n'.join(self.song.props.comments), 0)
    notebook.append_page(table, gtk.Label(_("Other")))
    
    # Add verses and slide order.
    text.Presentation._edit_tabs(self, notebook, parent)
    self._fields['title'].connect("changed", self._title_entry_changed)
    for event in ("row-changed","row-deleted","row-inserted","rows-reordered"):
      self._fields['title_list'].connect(event, self._title_list_changed)
    
    table = gui.Table(1)
    self._fields['verse_order'] = gui.append_entry(table, _("Verse Order:"),
        " ".join(self.song.props.verse_order), 0)
    self._fields['verse_order'].set_tooltip_text(_("Use the Slide names in \
brackets to modify the order"))
    notebook.get_nth_page(0).pack_start(table, False, True)
    table.show_all()
  
  def _edit_save(self):
    'Save the fields if the user clicks ok.'
    self.song.props.verse_order = self._fields['verse_order'].get_text().split()
    self.song.props.variant = self._fields['variant'].get_text()
    self.song.props.custom_version = self._fields['custom_version'].get_text()
    self.song.props.release_date = self._fields['release_date'].get_text()
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
      self.song.props.authors.append(openlyrics.Author(*row))
    
    self.song.props.songbooks = []
    for row in self._fields['songbook']:
      self.song.props.songbooks.append(openlyrics.Songbook(*row))
    
    self.song.props.themes = []
    for row in self._fields['theme']:
      self.song.props.themes.append(openlyrics.Theme(*row))
    
    self.song.props.comments = self._fields['comments'].get_buffer().get_text(
        *self._fields['comments'].get_buffer().get_bounds()).split('\n')
    
    ## TODO: Slides
    itr = self._fields['slides'].get_iter_first()
    self.slides = []
    self.song.verses = []
    while itr:
      slide = self._fields['slides'].get_value(itr,0)
      self.slides.append(slide)
      self.song.verses.append(slide.verse)
      itr = self._fields['slides'].iter_next(itr)
  
  def _del_treeview_row(self, button, treeview):
    (model, itr) = treeview.get_selection().get_selected()
    if itr:
      model.remove(itr)
  
  def _title_dlg_btn(self, btn, treeview, edit=False):
    "Add or edit a title."
    path = None
    col = None
    if edit:
      (model, itr) = treeview.get_selection().get_selected()
      path = model.get_path(itr)
    self._title_dlg(treeview, path, col, edit)
  
  def _title_dlg(self, treeview, path, col, edit=False):
    "Add or edit a title."
    dialog = gtk.Dialog(_("New Title"), treeview.get_toplevel(),\
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
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
              gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
              _("Please enter a Title."))
          info_dialog.run()
          info_dialog.destroy()
        else:
          if edit:
            model.set_value(itr, 0, title.get_text())
            model.set_value(itr, 1, lang.get_active_text())
          else:
            self._fields['title_list'].append( (title.get_text(),
                lang.get_active_text()) )
          dialog.hide()
          return True
      else:
        dialog.hide()
        return False
  
  def _author_dlg_btn(self, btn, treeview, edit=False):
    "Add or edit an author."
    path = None
    col = None
    if edit:
      (model, itr) = treeview.get_selection().get_selected()
      path = model.get_path(itr)
    self._author_dlg(treeview, path, col, edit)
  
  def _author_dlg(self, treeview, path, col, edit=False):
    "Add or edit an author."
    dialog = gtk.Dialog(_("New Author"), treeview.get_toplevel(),\
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
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
      type_value = model.get_value(itr,1)
      lang_value = model.get_value(itr,2)
    author = gui.append_entry(table, _('Author Name:'), author_value, 0)
    type = gui.append_combo2(table, _('Author Type:'),
        (('', _("None")),) + tuple(auth_types.iteritems()), type_value, 1)
    tmodel = type.get_model()
    lang = gui.append_language_combo(table, lang_value, 2)
    type.connect('changed', lambda combo: lang.set_sensitive(
        tmodel.get_value(type.get_active_iter(),0)=='translation') )
    type.emit('changed')
    dialog.vbox.show_all()
    
    while True:
      if dialog.run() == gtk.RESPONSE_ACCEPT:
        if not author.get_text():
          info_dialog = gtk.MessageDialog(treeview.get_toplevel(),
              gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
              _("Please enter an Author Name."))
          info_dialog.run()
          info_dialog.destroy()
        else:
          if edit:
            model.set_value(itr, 0, author.get_text())
            model.set_value(itr, 1,
                tmodel.get_value(type.get_active_iter(),0))
            if tmodel.get_value(type.get_active_iter(),0) == 'translation':
              model.set_value(itr, 2, lang.get_active_text())
          else:
            self._fields['author'].append( (author.get_text(),
                tmodel.get_value(type.get_active_iter(),0),
                lang.get_active_text()))
          dialog.hide()
          return True
      else:
        dialog.hide()
        return False
  
  def _theme_dlg_btn(self, btn, treeview, edit=False):
    "Add or edit a theme."
    path = None
    col = None
    if edit:
      (model, itr) = treeview.get_selection().get_selected()
      path = model.get_path(itr)
    self._theme_dlg(treeview, path, col, edit)
  
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
    theme = gui.append_entry(table, _('Theme Name:'), theme_value, 0)
    lang = gui.append_language_combo(table, lang_value, 1)
    dialog.vbox.show_all()
    
    while True:
      if dialog.run() == gtk.RESPONSE_ACCEPT:
        if not theme.get_text():
          info_dialog = gtk.MessageDialog(treeview.get_toplevel(),
              gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
              _("Please enter an Theme Name."))
          info_dialog.run()
          info_dialog.destroy()
        else:
          if edit:
            model.set_value(itr, 0, theme.get_text())
            model.set_value(itr, 1, lang.get_active_text())
          else:
            self._fields['theme'].append( (theme.get_text(),
                lang.get_active_text(), -1) )
          dialog.hide()
          return True
      else:
        dialog.hide()
        return False
  
  def _songbook_dlg_btn(self, btn, treeview, edit=False):
    "Add or edit a songbook."
    path = None
    col = None
    if edit:
      (model, itr) = treeview.get_selection().get_selected()
      path = model.get_path(itr)
    self._songbook_dlg(treeview, path, col, edit)
  
  def _songbook_dlg(self, treeview, path, col, edit=False):
    "Add or edit a songbook."
    dialog = gtk.Dialog(_("New songbook"), treeview.get_toplevel(),\
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
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
    songbook = gui.append_entry(table, _('Songbook Name:'), songbook_value, 0)
    entry = gui.append_entry(table, _('Entry:'), entry_value, 1)
    dialog.vbox.show_all()
    
    while True:
      if dialog.run() == gtk.RESPONSE_ACCEPT:
        if not songbook.get_text():
          info_dialog = gtk.MessageDialog(treeview.get_toplevel(),
              gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
              _("Please enter a Songbook."))
          info_dialog.run()
          info_dialog.destroy()
        else:
          if edit:
            model.set_value(itr, 0, songbook.get_text())
            # TODO Need to keep 'words', etc, not the translation of it.
            model.set_value(itr, 1, entry.get_text())
          else:
            self._fields['songbook'].append( (songbook.get_text(),
                entry.get_text()) )
          dialog.hide()
          return True
      else:
        dialog.hide()
        return False
  
  def _paste_as_text(self, *args):
    'Dialog to paste full lyrics.'
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
    else:
      self.filename = check_filename(self.get_title(),
          os.path.join(DATA_PATH, "pres"))
    self.song.createdIn = "ExpoSong"
    self.song.write(self.filename)
  
  def get_title(self):
    if len(self.song.props.titles) == 0: return os.path.basename(self.filename)
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
    lst.set_value(lst.get_iter_first(),
                  0, entry.get_text())
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
  
  def _rename_order(self, old_title, new_title):
    'If a slide title was changed, update the order with the new title.'
    if old_title == new_title: return
    order = self._fields['verse_order'].get_text().split()
    for i in range(len(order)):
      if order[i] == old_title:
        order[i] = new_title
    self._fields['verse_order'].set_text(" ".join(order))
  
  @classmethod
  def is_type(cls, fl):
    match = r'<song\b'
    lncnt = 0
    for ln in fl:
        if lncnt > 2: break
        if re.search(match, ln):
            return True
        lncnt += 1
    return False
  
  @staticmethod
  def get_type():
    'Return the presentation type.'
    return 'lyric'
  
  @staticmethod
  def get_icon():
    'Return the pixbuf icon.'
    return type_icon
  
  @staticmethod
  def _has_timer():
    'Returns boolean to show if we want to have timers.'
    return False
  
  @classmethod
  def merge_menu(cls, uimanager):
    'Merge new values with the uimanager.'
    factory = gtk.IconFactory()
    factory.add('exposong-lyric',gtk.IconSet(gtk.gdk.pixbuf_new_from_file(
        os.path.join(RESOURCE_PATH,'pres_lyric.png'))))
    factory.add_default()
    gtk.stock_add([("exposong-lyric",_("_Lyric"), gtk.gdk.MOD1_MASK, 
        0, "pymserv")])
    
    actiongroup = gtk.ActionGroup('exposong-lyric')
    actiongroup.add_actions([("pres-new-lyric", 'exposong-lyric', None, None,
        None, cls._on_pres_new)])
    uimanager.insert_action_group(actiongroup, -1)
    
    cls.menu_merge_id = uimanager.add_ui_from_string("""
      <menubar name='MenuBar'>
        <menu action="Presentation">
            <menu action="pres-new">
              <menuitem action='pres-new-lyric' />
            </menu>
        </menu>
      </menubar>
      """)
  
  @classmethod
  def unmerge_menu(cls, uimanager):
    'Remove merged items from the menu.'
    uimanager.remove_ui(cls.menu_merge_id)
  
  @classmethod
  def schedule_name(cls):
    'Return the string schedule name.'
    return _('Lyric Presentations')
  
  @classmethod
  def schedule_filter(cls, pres):
    'Called on each presentation, and return True if it can be added.'
    return pres.__class__ is cls
  
  @staticmethod
  def get_version():
    'Return the version number of the plugin.'
    return (1,0)
  
  @staticmethod
  def get_description():
    'Return the description of the plugin.'
    return "A lyric presentation type."

  @staticmethod
  def on_select():
    'Called when the presentation is focused.'
    exposong.application.main.add_accel_group(_lyrics_accel)

  @staticmethod
  def on_deselect():
    'Called when the presentation is blurred.'
    exposong.application.main.remove_accel_group(_lyrics_accel)


class SlideEdit(text.SlideEdit):
  'text.SlideEdit with custom title box'
  def __init__(self, parent, slide):
    text.SlideEdit.__init__(self, parent, slide)
    
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
