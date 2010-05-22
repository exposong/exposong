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
import pango
import re
import os.path
import xml.dom
import xml.dom.minidom
from datetime import datetime

from exposong.glob import *
from exposong import RESOURCE_PATH, DATA_PATH
from exposong.plugins import Plugin, _abstract, text
import exposong.application
import exposong.slidelist
from exposong.prefs import config
import openlyrics

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

title_re = re.compile(
    "(chorus|refrain|verse|bridge|end(ing)?|soprano|alto|tenor|bass)\\b",
    re.I)
auth_types = {
  "words": _("Words"),
  "music": _("Music"),
  "translation": _("Translation"),
  }

def key_shortcuts(accel_group, acceleratable, keyval, modifier):
  'Adds the shortcuts to skip to a given slide.'
  pres = exposong.slidelist.slidelist.pres
  if pres != None:
    slnum = None
    if chr(keyval) == 'c':
      slnum = pres.get_slide_from_order('c')
    elif chr(keyval) >= '0' and chr(keyval) <= '9':
      slnum = pres.get_slide_from_order("v%s" % chr(keyval))
    if(slnum != None):
      exposong.slidelist.slidelist.to_slide(slnum)

_lyrics_accel = gtk.AccelGroup()
_lyrics_accel.connect_group(ord("c"), 0,0, key_shortcuts)
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
    lang = ''
    
    def __init__(self, pres, verse):
      lines = []
      self.pres = pres
      
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
  
    def footer_text(self):
      'Draw text on the footer.'
      jn = ['"%s"' % self.pres.title]
      # TODO List only translators for the current translation.
      author = ';  '.join( '%s: %s' % (auth_types.get(a.type,_("Written By")),
          str(a)) for a in self.pres.song.props.authors )
      if len(author) > 0:
        jn.append(author)
      if len(self.pres.song.props.copyright):
        jn.append(u"Copyright \xA9 %s" % self.pres.song.props.copyright)
      if config.get("general", "ccli"):
        jn.append("Song CCLI ID# %s; CCLI# %s" % (self.pres.song.props.ccli_no,
            config.get("general", "ccli")))
      return '\n'.join(jn)
  
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
    order = self.song.props.verse_order.split()
    if len(order) > 0:
      return tuple(self.get_slide_from_order(n) for n in order
          if isinstance(self.get_slide_from_order(n),int))
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
  
  def edit(self):
    return NotImplemented
  
  def _edit_tabs(self, notebook, parent):
    'Run the edit dialog for the presentation.'
    vbox = gtk.VBox()
    vbox.set_border_width(4)
    vbox.set_spacing(7)
    
    # TODO Titles, Authors
    
    hbox = gtk.HBox()
    label = gtk.Label(_("Copyright:"))
    hbox.pack_start(label, False, True, 5)
    self._fields['copyright'] = gtk.Entry(50)
    self._fields['copyright'].set_text(self.song.props.copyright)
    hbox.pack_start(self._fields['copyright'], True, True, 5)
    vbox.pack_start(hbox, False, True)

    vbox.pack_start(gtk.HSeparator(), False, True)

    hbox = gtk.HBox()
    label = gtk.Label(_("Order:"))
    hbox.pack_start(label, False, True, 5)
    self._fields['order'] = gtk.Entry(50)
    self._fields['order'].set_text(self.song.props.verse_order)
    vbox2 = gtk.VBox()
    vbox2.pack_start(self._fields['order'], True, True, 5)
    label = gtk.Label( _("Use the slide titles to modify the order.") )
    label.set_justify(gtk.JUSTIFY_LEFT)
    label.set_alignment(0,0.5)
    label.set_line_wrap(True)
    vbox2.pack_start(label, True, True, 5)
    hbox.pack_start(vbox2)
    vbox.pack_start(hbox, False, True)

    notebook.append_page(vbox, gtk.Label(_("Information")))
    
    text.Presentation._edit_tabs(self, notebook, parent)
    
    btn = gtk.ToolButton(gtk.STOCK_PASTE)
    btn.set_label( _("Paste As Text") )
    btn.connect("clicked", self._paste_as_text, parent)
    self._slideToolbar.insert(btn, -1)
  
  def _edit_save(self):
    'Save the fields if the user clicks ok.'
    if 'words' in self.authors:
      self.authors[self.authors.index('words')].author = self._fields['words'].get_text()
    else:
      self.authors.append(_Author(author=self._fields['words'].get_text(), type='words'))
    
    if 'music' in self.authors:
      self.authors[self.authors.index('music')].author = self._fields['music'].get_text()
    else:
      self.authors.append(_Author(author=self._fields['music'].get_text(), type='music'))
    
    self.song.props.copyright = self._fields['copyright'].get_text()
    self.song.props.order = self._fields['order'].get_text().split()
    
    
    model = self._fields['slides'].get_model()
    itr = model.get_iter_first()
    self.slides = []
    while itr:
      self.slides.append(model.get_value(itr,0))
      itr = model.iter_next(itr)
    del self._slideToolbar
  
  def _paste_as_text(self, *args):
    'Dialog to paste full lyrics.'
    dialog = gtk.Dialog(_("Editing Slide"), exposong.application.main,\
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
         gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    
    dialog.set_border_width(4)
    dialog.vbox.set_spacing(7)
    hbox = gtk.HBox()
    
    label = gtk.Label(_("Title:"))
    label.set_alignment(0.5, 0.5)
    hbox.pack_start(label, False, True, 5)
    title = gtk.Entry(80)
    title.set_text(self._fields['title'].get_text())
    hbox.pack_start(title, True, True)
    
    dialog.vbox.pack_start(hbox, False, True)
    
    text = gtk.TextView()
    text.set_wrap_mode(gtk.WRAP_WORD)
    text.get_buffer().connect("changed", self._text_changed)
    self.set_text_buffer(text.get_buffer())
    text_scroll = gtk.ScrolledWindow()
    text_scroll.add(text)
    text_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    text_scroll.set_size_request(340, 240)
    dialog.vbox.pack_start(text_scroll, True, True)
    
    dialog.vbox.show_all()
      
    if dialog.run() == gtk.RESPONSE_ACCEPT:
      # TODO Titles, Authors
      bounds = text.get_buffer().get_bounds()
      sval = text.get_buffer().get_text(bounds[0], bounds[1])
      self.slides = []
      for sl in sval.split("\n\n"):
        self.slides.append(self.Slide(self, sl))
      
      self._fields['title'].set_text(self.get_title())
      slide_model = self._fields['slides'].get_model()
      slide_model.clear()
      for sl in self.get_slide_list():
        slide_model.append(sl)
      
      dialog.hide()
      return True
    else:
      dialog.hide()
      return False
  
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
    assert(self.song.props.titles[0])
    return str(self.song.props.titles[0])
  
  title = property(get_title)
  
  @classmethod
  def is_type(cls, fl):
    match = '<song\\b'
    lncnt = 0
    for ln in fl:
        if lncnt > 3: break
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
  
  def set_text_buffer(self, tbuf):
    'Sets the value of a text buffer.'
    it1 = tbuf.get_start_iter()
    titleTag = tbuf.create_tag("titleTag", weight=pango.WEIGHT_BOLD, background="orange")
    
    for sl in self.slides:
      if(hasattr(sl, 'title') and len(sl.title) > 0):
        tbuf.insert_with_tags(it1, sl.title, titleTag)
        tbuf.insert(it1, "\n")
      tbuf.insert(it1, sl.get_text())
      if(sl is not self.slides[len(self.slides)-1]):
        tbuf.insert(it1, "\n\n")
  
  def _text_changed(self, tbuf):
    it = tbuf.get_start_iter()
    tbuf.remove_tag_by_name("titleTag", it, tbuf.get_end_iter())
    cont = True
    while cont:
      end_ln = it.copy().forward_search('\n', gtk.TEXT_SEARCH_VISIBLE_ONLY)
      if(not end_ln):
        end_ln = tbuf.get_end_iter()
      else:
        end_ln = end_ln[1]
      line = it.get_text(end_ln)
      if(title_re.match(line, endpos=30)):
        tbuf.apply_tag_by_name("titleTag", it, end_ln)
              
      cont = it.forward_line()
  
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


