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
from datetime import datetime

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
auth_types = {
  "words": _("Words"),
  "music": _("Music"),
  "translation": _("Translation"),
  "_default": _("Written By"),
  }

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
    lang = ''
    
    def __init__(self, pres, value):
      lines = []
      self.pres = pres
      if(isinstance(value, xml.dom.Node)):
        self.title = value.getAttribute("name")
        self.lang = value.getAttribute("lang")
        self.lines = [_Lines(l) for l in value.getElementsByTagName("lines")]
        if len(self.lines) > 0:
          self.text = str(self.lines[0])
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
      author = ';  '.join( '%s: %s' % (auth_types.get(a.type,"_default"), str(a)) \
          for a in _Author.get_authors(self.pres.authors) )
      if len(author) > 0:
        jn.append(author)
      if hasattr(self.pres, "copyright") and len(self.pres.copyright):
        jn.append(u"Copyright \xA9 %s" % self.pres.copyright)
      if config['general.ccli']:
        jn.append("CCLI# %s" % config['general.ccli'])
      return '\n'.join(jn)
  
    def to_node(self, doc, node):
      'Populate the node element'
      node.setAttribute("lang","en")
      if self.title:
        node.setAttribute("name", self.title)
      lines = doc.createElement("lines")
      for ln in self.text.split("\n"):
        line = doc.createElement("line")
        line.appendChild( doc.createTextNode(ln) )
        lines.appendChild( line )
      node.appendChild(lines)
    
    @staticmethod
    def get_version():
      'Return the version number of the plugin.'
      return (1,0)
  
    @staticmethod
    def get_description():
      'Return the description of the plugin.'
      return "A lyric presentation type."
  
  
  def __init__(self, dom = None, filename = None):
    self.titles = []
    self.authors = []
    self.slides = []
    self._createdIn = "ExpoSong"
    self._order = []
    self.filename = filename
    
    if isinstance(dom, xml.dom.Node):
      props = dom.getElementsByTagName("properties")
      if len(props) > 0:
        props = props[0]
        self.titles = [_Title(t) for t in props.getElementsByTagName("title")]
        self.authors = [_Author(a) for a in props.getElementsByTagName("author")]
        copyright = props.getElementsByTagName("copyright")
        if len(copyright):
          self.copyright = get_node_text(copyright[0])
        ordernode = props.getElementsByTagName("verseOrder")
        if len(ordernode) > 0:
          self._order = get_node_text(ordernode[0]).split()
          for o in self._order:
            if o.strip() == "":
              self._order.remove(o)
      
      slides = dom.getElementsByTagName("verse")
      for sl in slides:
        self.slides.append(self.Slide(self, sl))
      self.title = str(_Title.get_title(self.titles))

  def get_order(self):
    'Returns the order in which the slides should be presented.'
    if len(self._order) > 0:
      return tuple(self.get_slide_from_order(n) for n in self._order)
    else:
      return _abstract.Presentation.get_order(self)

  def get_slide_from_order(self, order_value):
    'Gets the slide index.'
    i = 0
    for sl in self.slides:
      if re.match(order_value,sl.title.lower()):
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
    if 'words' in self.authors:
      self._fields['words'].set_text(str(self.authors[self.authors.index('words')]))
    hbox.pack_start(self._fields['words'], True, True, 5)
    vbox.pack_start(hbox, False, True)
    
    hbox = gtk.HBox()
    label = gtk.Label(_("Music:"))
    hbox.pack_start(label, False, True, 5)
    self._fields['music'] = gtk.Entry(50)
    if 'music' in self.authors:
      self._fields['music'].set_text(str(self.authors[self.authors.index('music')]))
    hbox.pack_start(self._fields['music'], True, True, 5)
    vbox.pack_start(hbox, False, True)
    
    # TODO Translators
    
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
    
    self.copyright = self._fields['copyright'].get_text()
    self._order = self._fields['order'].get_text().split()
    
    #TODO: This should not always be index 0... But adding multilingual titles
    # will fix this.
    self.titles[0:0] = ( _Title(self._fields['title'].get_text()), )
    self.title = str(_Title.get_title(self.titles))
    
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
    root = doc.createElement("song")
    root.setAttribute("version", "0.7")
    root.setAttribute("createdIn", self._createdIn)
    root.setAttribute("modifiedIn", "ExpoSong")
    root.setAttribute("modifiedDate", datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
    
    properties = doc.createElement("properties")
    
    titles = doc.createElement("titles")
    properties.appendChild(titles)
    
    for t in self.titles:
      t.to_node(doc, titles)
    
    authors = doc.createElement("authors")
    properties.appendChild(authors)
    
    for a in self.authors:
      a.to_node(doc, authors)
    
    if self._order != "":
      node = doc.createElement("verseOrder")
      node.appendChild(doc.createTextNode(' '.join(self._order)))
      properties.appendChild(node)
    
    node = doc.createElement("copyright")
    node.appendChild(doc.createTextNode(self.copyright))
    properties.appendChild(node)
    
    lyrics = doc.createElement("lyrics")
    for s in self.slides:
      sNode = doc.createElement("verse")
      s.to_node(doc, sNode)
      lyrics.appendChild(sNode)
    
    root.appendChild(properties)
    root.appendChild(lyrics)
    
    doc.appendChild(root)
    outfile = open(join(directory, self.filename), 'w')
    doc.writexml(outfile, "\t","\t","\n")
    doc.unlink()
  
  @classmethod
  def is_type(class_, dom):
    if dom.tagName == "song":
        return True
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



class _Title:
  '''
  Stores a title with attributes.
  '''
  title = ""
  lang = ""
  
  def __init__(self, element):
    'Create a new title'
    if isinstance(element, xml.dom.Node):
      self.title = get_node_text(element)
      self.lang = element.getAttribute("lang")
    elif isinstance(element, str):
      self.title = element
  
  def __str__(self):
    return self.title
  
  def to_node(self, doc, node):
    'Create an xml entity from this class.'
    t = doc.createElement("title")
    if len(self.lang):
      t.setAttribute("lang", self.lang)
    t.appendChild(doc.createTextNode(self.title))
    node.appendChild(t)
  
  @staticmethod
  def get_title(list_):
    'Return the current title.'
    #TODO Get title for current language
    if len(list_) > 0:
      return list_[0]
    else:
      return _("(No Title)")

class _Author:
  '''
  Stores an author with attributes.
  '''
  author = ""
  type = ""
  lang = ""
  
  def __init__(self, element = None, author = None, type = None):
    'Create a new title'
    if isinstance(element, xml.dom.Node):
      self.author = get_node_text(element)
      self.type = element.getAttribute("type")
      if self.type == 'translation':
        self.lang = element.getAttribute("lang")
    elif author != None and type != None:
      self.author = author
      self.type = type
    if len(self.type) > 0:
      assert(self.type in auth_types)
  
  def __str__(self):
    'Create a string from this attribute.'
    return self.author
  
  def __eq__(self, other):
    if isinstance(other, str):
      return self.type == other
  
  def to_node(self, doc, node):
    'Create an xml entity from this class.'
    t = doc.createElement("author")
    t.setAttribute("type", self.type)
    if self.type =='translation':
      t.setAttribute("lang", self.lang)
    t.appendChild(doc.createTextNode(self.author))
    node.appendChild(t)
  
  @staticmethod
  def get_authors(list_):
    'Returns a list of authors for displaying.'
    #TODO Get current language translator.
    return (a for a in list_ if a.type in ('words','music'))

class _Lines:
  '''
  A group of lines that can be used to separate parts for a lyric.
  '''
  part = ""
  def __init__(self, element = None):
    self.lines = []
    if isinstance(element, xml.dom.Node):
      for ln in element.getElementsByTagName("line"):
        self.lines.append(get_node_text(ln))
  
  def __str__(self):
    'Get the text value.'
    return "\n".join(self.lines)
