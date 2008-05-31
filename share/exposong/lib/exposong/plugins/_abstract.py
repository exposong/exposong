#! /usr/bin/env python
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
import gobject
import xml.dom
import xml.dom.minidom
from os.path import join

from exposong.glob import *
from exposong import DATA_PATH
from exposong.plugins import Plugin
import exposong.application
import exposong.schedlist

'''
Abstract classes that create plugin functionality.

These classes should not be referrenced, with the exception of `Slide`.
'''

# Abstract functions should use the following:
# `raise NotImplementedError`


class Presentation:
  '''
  A presentation type to store the text or data for a presentation.
  
  Requires at minimum a title and slides.
  '''
  class Slide:
    '''
    A plain text slide.
  
    Reimplementing this class is optional.
    '''
    def __init__(self, pres, value):
      self.pres = pres
      if isinstance(value, xml.dom.Node):
        self.text = get_node_text(value)
        self.title = value.getAttribute("title")
      elif isinstance(value, str):
        self.text = value
        self.title = None
  
    def get_text(self):
      'Get the text for the presentation.'
      return self.text
  
    def get_markup(self):
      'Get the text for the slide selection.'
      if(self.title):
        return "<b>" + self.title + "</b>\n" + self.text
      else:
        return self.text
  
    def to_node(self, document, node):
      'Populate the node element'
      if(self.title):
        node.setAttribute("title", self.title)
      node.appendChild( document.createTextNode(self.text) )
    
    def header_text(self):
      'Draw on the header.'
      return NotImplemented
    
    def footer_text(self):
      'Draw text on the footer.'
      return NotImplemented
    
    def body_text(self):
      'Draw text in the center of the screen.'
      return self.get_text()
    
    def draw(self, widget):
      'Overrides all text rendering to render custom slides.'
      return NotImplemented
  
  
  def __init__(self, dom = None, filename = None):
    if self.__class__ is Presentation:
      raise NotImplementedError("This class cannot be instantiated.")
    self.type = ""
    self.title = ''
    self.copyright = ''
    self.author = {}
    self.slides = []
    self.filename = filename
    if isinstance(dom, xml.dom.Node):
      self.title = get_node_text(dom.getElementsByTagName("title")[0])
      for el in dom.getElementsByTagName("author"):
        atype = el.getAttribute("type")
        self.author[atype] = get_node_text(el)
      copyright = dom.getElementsByTagName("copyright")
      if len(copyright):
        self.copyright = get_node_text(copyright[0])
      
      self._set_slides(dom)
  
  @staticmethod
  def get_type():
    'Return the presentation type.'
    raise NotImplementedError
  
  @staticmethod
  def get_icon():
    'Return the pixbuf icon.'
    raise NotImplementedError
  
  def _set_slides(self, dom):
    'Set the slides from xml.'
    slides = dom.getElementsByTagName("slide")
    for sl in slides:
      self.slides.append(self.Slide(self, sl))
  
  def get_row(self):
    'Gets the data to add to the presentation list.'
    return (self, self.title)
  
  def set_text_buffer(self, tbuf):
    'Sets the value of a text buffer.'
    rval = ''
    for sl in self.slides:
      rval += sl.get_text() + "\n\n"
    tbuf.set_text(rval[:-2])
  
  def edit(self):
    'Run the edit dialog for the presentation.'
    dialog = gtk.Dialog(_("New Presentation"), exposong.application.main, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    dialog.set_default_size(340, 400)
    if(self.title):
      dialog.set_title(_("Editing %s") % self.title)
    else:
      dialog.set_title(_("New %s Presentation") % self.type.title())
    notebook = gtk.Notebook()
    dialog.vbox.pack_start(notebook, True, True, 6)
    
    self._fields = dict()
    
    self._edit_tabs(notebook)
    
    notebook.show_all()
    
    if(dialog.run() == gtk.RESPONSE_ACCEPT):
      self._edit_save()
      del(self._fields)
      
      self.to_xml()
      
      dialog.hide()
      return True
    else:
      dialog.hide()
      return False
  
  def _edit_tabs(self, notebook):
    'Tabs for the dialog.'
    pass # Later we'll have presentation specific backgrounds.
  
  def _edit_save(self):
    'Save the fields if the user clicks ok.'
    pass
  
  def to_xml(self):
    'Save the data to disk.'
    directory = join(DATA_PATH, 'pres')
    self.filename = check_filename(self.title, directory, self.filename)
    
    doc = xml.dom.getDOMImplementation().createDocument(None, None, None)
    root = doc.createElement("presentation")
    root.setAttribute("type", self.type)
    tNode = doc.createElement("title")
    tNode.appendChild(doc.createTextNode(self.title))
    root.appendChild(tNode)
    for s in self.slides:
      sNode = doc.createElement("slide")
      s.to_node(doc, sNode)
      root.appendChild(sNode)
    doc.appendChild(root)
    outfile = open(join(directory, self.filename), 'w')
    doc.writexml(outfile)
    doc.unlink()
  
  def slide_column(self, col):
    'Set the column to use text.'
    col.clear()
    text_cr = gtk.CellRendererText()
    #text_cr.ellipsize = pango.ELLIPSIZE_END
    col.pack_start(text_cr, False)
    col.add_attribute(text_cr, 'markup', 1)
    exposong.slidelist.slidelist.set_model(\
        gtk.ListStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING))
  
  def get_slide_list(self):
    'Get the slide list.'
    return tuple( (sl, sl.get_markup()) for sl in self.slides)
  
  def _on_pres_new(self, action):
    pres = self.__class__()
    if pres.edit():
      sched = exposong.schedlist.schedlist.get_active_item()
      if sched and not sched.builtin:
        sched.append(pres)
      #Add presentation to appropriate builtin schedules
      model = exposong.schedlist.schedlist.get_model()
      itr = model.get_iter_first()
      while itr:
        sched = model.get_value(itr, 0)
        if sched:
          sched.append(pres)
        itr = model.iter_next(itr)


class Menu:
  '''
  Subclasses can modify the menu using uimanager.
  '''
  def merge_menu(self, uimanager):
    'Merge new values with the uimanager.'
    raise NotImplementedError
  def unmerge_menu(self, uimanager):
    'Remove merged items from the menu.'
    raise NotImplementedError


class Schedule:
  '''
  Hooks to add built-in schedules.
  '''
  @classmethod
  def schedule_name(cls):
    'Return the string schedule name.'
    raise NotImplementedError
  
  @classmethod
  def schedule_filter(cls, pres):
    'Called on each presentation, and return True if it can be added.'
    raise NotImplementedError


class Screen:
  '''
  Hooks into the presentation screen.
  '''
  def draw(self, surface, priority=1):
    'Draw anywhere on the screen.'
    return NotImplemented

