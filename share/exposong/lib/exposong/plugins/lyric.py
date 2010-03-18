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
from exposong.plugins import Plugin, _abstract, text
import exposong.application
import exposong.slidelist
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
    join(RESOURCE_PATH,'pres_lyric.png'), 20, 14)

title_re = re.compile("(chorus|refrain|verse|bridge|end(ing)?|soprano|alto|tenor|bass)\\b", re.I)

def key_shortcuts(accel_group, acceleratable, keyval, modifier):
  'Adds the shortcuts to skip to a given slide.'
  pres = exposong.slidelist.slidelist.pres
  if pres != None:
    slnum = None
    if chr(keyval) == 'c':
      #print pres.get_slide_from_order('c')
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
      
      self._set_id(value)
  
    def footer_text(self):
      'Draw text on the footer.'
      jn = ['"%s"' % self.pres.title]
      author = ';  '.join( _(k.title())+": "+v for k,v in self.pres.author.iteritems() if v )
      if author:
        jn.append(author)
      if hasattr(self.pres, "copyright") and len(self.pres.copyright):
        jn.append(u"Copyright \xA9 %s" % self.pres.copyright)
      if config['general.ccli']:
        jn.append("CCLI# %s" % config['general.ccli'])
      return '\n'.join(jn)
  
    @staticmethod
    def get_version():
      'Return the version number of the plugin.'
      return (1,0)
  
    @staticmethod
    def get_description():
      'Return the description of the plugin.'
      return "A lyric presentation type."
  
  
  def __init__(self, dom = None, filename = None):
    text.Presentation.__init__(self, dom, filename)

  def get_order(self):
    'Returns the order in which the slides should be presented.'
    if len(self._order) > 0:
      return tuple(self.get_slide_from_order(n) for n in self._order)
    else:
      return _abstract.Presentation.get_order(self)

  def get_slide_from_order(self, order_value):
    'Gets the slide index.'
    title = ""
    try:
      title = '^'+{'v':'verse','c':'chorus','b':'bridge',
              'e':'end(ing)?','r':'refrain'}[order_value[0].lower()]
      if len(order_value) == 1 or order_value[1:] == '1':
        title += '( 1)?'
      else:
        title += ' '+order_value[1:]
      title += '$'
    except KeyError:
      #return _abstract.Presentation.get_slide_from_order(self, order_value)
      return False
      
    i = 0
    for sl in self.slides:
      if re.match(title,sl.title.lower()):
        return i
      i += 1

  def _edit_tabs(self, notebook, parent):
    'Run the edit dialog for the presentation.'
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

    vbox.pack_start(gtk.HSeparator(), False, True)

    hbox = gtk.HBox()
    label = gtk.Label(_("Order:"))
    hbox.pack_start(label, False, True, 5)
    self._fields['order'] = gtk.Entry(50)
    self._fields['order'].set_text(' '.join(self._order))
    vbox2 = gtk.VBox()
    vbox2.pack_start(self._fields['order'], True, True, 5)
    label = gtk.Label(_("Input can be any of the following: \
%(verse)s for verses, %(chorus)s for chorus, %(refrain)s for refrain, \
%(bridge)s for bridge, %(ending)s for ending.")\
        %{"verse":"v1...v9","chorus":"c",\
        "refrain":"r", "bridge":"b",\
        "ending":"e"})
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
    self.author['words'] = self._fields['words'].get_text()
    self.author['music'] = self._fields['music'].get_text()
    self.copyright = self._fields['copyright'].get_text()
    self._order = self._fields['order'].get_text().split()
    text.Presentation._edit_save(self)
  
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
    title.set_text(self.title)
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
      self.title = title.get_text()
      bounds = text.get_buffer().get_bounds()
      sval = text.get_buffer().get_text(bounds[0], bounds[1])
      self.slides = []
      for sl in sval.split("\n\n"):
        self.slides.append(self.Slide(self, sl))
      
      self._fields['title'].set_text(self.title)
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
    directory = join(DATA_PATH, 'pres')
    self.filename = check_filename(self.title, directory, self.filename)
    
    doc = xml.dom.getDOMImplementation().createDocument(None, None, None)
    root = doc.createElement("presentation")
    root.setAttribute("type", self.get_type())
    
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

    if self._order != "":
      node = doc.createElement("order")
      node.appendChild(doc.createTextNode(' '.join(self._order)))
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
        join(RESOURCE_PATH,'pres_lyric.png'))))
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

