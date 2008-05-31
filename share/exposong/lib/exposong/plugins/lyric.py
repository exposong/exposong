#! /usr/bin/env python
# -*- coding: utf-8 -*-
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
from os.path import join
import xml.dom
import xml.dom.minidom
import pango
import re

from exposong.glob import *
from exposong import RESOURCE_PATH, DATA_PATH
from exposong.plugins import Plugin, _abstract
import exposong.application
from exposong.prefs import config

"""
Lyric presentations.
"""
information = {
    'name': _("Lyric Presentation"),
    'description': __doc__,
    'required': False,
}
type_icon = gtk.gdk.pixbuf_new_from_file(join(RESOURCE_PATH,'lyric.png'))

title_re = re.compile("(chorus|refrain|verse|bridge)", re.I)


class Presentation (Plugin, _abstract.Presentation, _abstract.Menu,
    _abstract.Schedule, _abstract.Screen):
  '''
  Lyric presentation type.
  '''
  class Slide (Plugin, _abstract.Presentation.Slide):
    '''
    A lyric slide for the presentation.
    '''
    def __init__(self, pres, value):
      self.pres = pres
      if(isinstance(value, xml.dom.Node)):
        self.text = get_node_text(value)
        self.title = value.getAttribute("title")
      elif(isinstance(value, str)):
        value = value.strip()
        if(title_re.match(value, endpos=30)):
          (self.title, self.text) = value.split("\n", 1)
        else:
          self.title = ''
          self.text = value
  
    @staticmethod
    def get_version():
      'Return the version number of the plugin.'
      return (1,0)
  
    @staticmethod
    def get_description():
      'Return the description of the plugin.'
      return "A lyric presentation type."
  
    def footer_text(self):
      'Draw text on the footer.'
      jn = ['"%s"' % self.pres.title]
      author = ';  '.join( _(k.title())+": "+v for k,v in self.pres.author.iteritems() if v )
      if author:
        jn.append(author)
      if hasattr(self.pres, "copyright"):
        jn.append(u"Copyright \xA9 %s" % self.pres.copyright)
      if config['general.ccli']:
        jn.append("CCLI# %s" % config['general.ccli'])
      return '\n'.join(jn)
  
  
  def __init__(self, dom = None, filename = None):
    _abstract.Presentation.__init__(self, dom, filename)
    self.type = 'lyric'
  
  def _edit_tabs(self, notebook):
    'Run the edit dialog for the presentation.'
    vbox = gtk.VBox()
    vbox.set_border_width(4)
    vbox.set_spacing(7)
    hbox = gtk.HBox()
    
    label = gtk.Label(_("Title:"))
    label.set_alignment(0.5, 0.5)
    hbox.pack_start(label, False, True, 5)
    self._fields['title'] = gtk.Entry(45)
    self._fields['title'].set_text(self.title)
    hbox.pack_start(self._fields['title'], True, True)
    
    vbox.pack_start(hbox, False, True)
    
    self._fields['text'] = gtk.TextView()
    self._fields['text'].set_wrap_mode(gtk.WRAP_WORD)
    self._fields['text'].get_buffer().connect("changed", self._text_changed)
    self.set_text_buffer(self._fields['text'].get_buffer())
    text_scroll = gtk.ScrolledWindow()
    text_scroll.add(self._fields['text'])
    text_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
    text_scroll.set_size_request(340, 240)
    vbox.pack_start(text_scroll, True, True)
    notebook.append_page(vbox, gtk.Label(_("Edit")))
    
    vbox = gtk.VBox()
    vbox.set_border_width(4)
    vbox.set_spacing(7)
    
    hbox = gtk.HBox()
    label = gtk.Label(_("Words:"))
    hbox.pack_start(label, False, True, 5)
    self._fields['words'] = gtk.Entry(50)
    self._fields['words'].set_text(self.author.get('words',''))
    hbox.pack_start(self._fields['words'], True, True, 5)
    vbox.pack_start(hbox, False, True)
    
    hbox = gtk.HBox()
    label = gtk.Label(_("Music:"))
    hbox.pack_start(label, False, True, 5)
    self._fields['music'] = gtk.Entry(50)
    self._fields['music'].set_text(self.author.get('music',''))
    hbox.pack_start(self._fields['music'], True, True, 5)
    vbox.pack_start(hbox, False, True)
    
    hbox = gtk.HBox()
    label = gtk.Label(_("Copyright:"))
    hbox.pack_start(label, False, True, 5)
    self._fields['copyright'] = gtk.Entry(50)
    self._fields['copyright'].set_text(self.copyright)
    hbox.pack_start(self._fields['copyright'], True, True, 5)
    vbox.pack_start(hbox, False, True)
    notebook.append_page(vbox, gtk.Label(_("Information")))
    
    _abstract.Presentation._edit_tabs(self, notebook)
  
  def _edit_save(self):
    'Save the fields if the user clicks ok.'
    self.title = self._fields['title'].get_text()
    self.author['words'] = self._fields['words'].get_text()
    self.author['music'] = self._fields['music'].get_text()
    self.copyright = self._fields['copyright'].get_text()
    bounds = self._fields['text'].get_buffer().get_bounds()
    sval = self._fields['text'].get_buffer().get_text(bounds[0], bounds[1])
    self.slides = []
    for sl in sval.split("\n\n"):
      self.slides.append(self.Slide(self, sl))
  
  def to_xml(self):
    'Save the data to disk.'
    directory = join(DATA_PATH, 'pres')
    self.filename = check_filename(self.title, directory, self.filename)
    
    doc = xml.dom.getDOMImplementation().createDocument(None, None, None)
    root = doc.createElement("presentation")
    root.setAttribute("type", self.type)
    
    node = doc.createElement("title")
    node.appendChild(doc.createTextNode(self.title))
    root.appendChild(node)
    
    node = doc.createElement("author")
    node.setAttribute('type', 'words')
    node.appendChild(doc.createTextNode(self.author.get('words', '')))
    root.appendChild(node)
    
    node = doc.createElement("author")
    node.setAttribute('type', 'music')
    node.appendChild(doc.createTextNode(self.author.get('music', '')))
    root.appendChild(node)
    
    node = doc.createElement("copyright")
    node.appendChild(doc.createTextNode(self.copyright))
    root.appendChild(node)
    
    for s in self.slides:
      sNode = doc.createElement("slide")
      s.to_node(doc, sNode)
      root.appendChild(sNode)
    doc.appendChild(root)
    outfile = open(join(directory, self.filename), 'w')
    doc.writexml(outfile)
    doc.unlink()
  
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
  
  def merge_menu(self, uimanager):
    'Merge new values with the uimanager.'
    factory = gtk.IconFactory()
    factory.add('exposong-lyric',gtk.IconSet(gtk.gdk.pixbuf_new_from_file(
        join(RESOURCE_PATH,'lyric.png'))))
    factory.add_default()
    gtk.stock_add([("exposong-lyric",_("_Lyric"), gtk.gdk.MOD1_MASK, 
        0, "pymserv")])
    
    actiongroup = gtk.ActionGroup('exposong-lyric')
    actiongroup.add_actions([("pres-new-lyric", 'exposong-lyric', None, None,
        None, self._on_pres_new)])
    uimanager.insert_action_group(actiongroup, -1)
    
    self.menu_merge_id = uimanager.add_ui_from_string("""
      <menubar name='MenuBar'>
        <menu action="Presentation">
            <menu action="pres-new">
              <menuitem action='pres-new-lyric' />
            </menu>
        </menu>
      </menubar>
      """)
  
  def unmerge_menu(self, uimanager):
    'Remove merged items from the menu.'
    uimanager.remove_ui(self.menu_merge_id)
  
  @classmethod
  def schedule_name(cls):
    'Return the string schedule name.'
    return _('Lyric Presentations')
  
  @classmethod
  def schedule_filter(cls, pres):
    'Called on each presentation, and return True if it can be added.'
    return isinstance(pres, cls)
  
  @staticmethod
  def get_version():
    'Return the version number of the plugin.'
    return (1,0)
  
  @staticmethod
  def get_description():
    'Return the description of the plugin.'
    return "A lyric presentation type."

