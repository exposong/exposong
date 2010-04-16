#! /usr/bin/env python
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
    pres = None
    id = None
    title = ''
    text = ''
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
      self._set_id(value)
    
    def get_text(self):
      'Get the text for the presentation.'
      return self.text
  
    def get_markup(self):
      'Get the text for the slide selection.'
      if self.title:
        return "<b>" + self.title + "</b>\n" + self.text
      else:
        return self.text
    
    def to_node(self, document, node):
      'Populate the node element'
      if self.title:
        node.setAttribute("title", self.title)
      if self.id:
        node.setAttribute("id", self.id)
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
      
    def _set_id(self, value = None):
      if isinstance(value, xml.dom.Node):
        self.id = value.getAttribute("id")
      if not self.id:
        if(len(self.title) > 0):
          self.id = str(self.title).replace(" ","").lower()  + '_' + random_string(8)
        else:
          self.id = random_string(8)
  
  title = ''
  copyright = ''
  timer = None
  timer_loop = False
  filename = None
  
  def __init__(self, dom = None, filename = None):
    if self.__class__ is Presentation:
      raise NotImplementedError("This class cannot be instantiated.")
    self.filename = filename
    self.slides = []
    
    if isinstance(dom, xml.dom.Node):
      self.title = get_node_text(dom.getElementsByTagName("title")[0])
      copyright = dom.getElementsByTagName("copyright")
      if len(copyright):
        self.copyright = get_node_text(copyright[0])
      timer = dom.getElementsByTagName("timer")
      if len(timer) > 0:
        self.timer = int(timer[0].getAttribute("time"))
        self.timer_loop = bool(timer[0].getAttribute("loop"))
      
      self._set_slides(dom)
  
  @classmethod
  def is_type(class_, dom):
    if dom.tagName == "presentation" and dom.hasAttribute("type"):
      if str(dom.getAttribute("type")) == class_.get_type():
        return True
    return False
  
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
  
  def get_order(self):
    'Returns the order in which the slides should be presented.'
    order = []
    cnt = 0
    for slide in self.slides:
      order.append(cnt)
      cnt += 1
    return order

  def get_slide_from_order(self, order_value):
    'Gets the slide index.'
    return int(order_value)

  def set_text_buffer(self, tbuf):
    'Sets the value of a text buffer.'
    rval = ''
    for sl in self.slides:
      rval += sl.get_text() + "\n\n"
    tbuf.set_text(rval[:-2])
  
  def matches(self, text):
    'Tests to see if the presentation matches `text`.'
    regex = re.compile("\\b"+re.escape(text), re.I)
    if regex.search(self.title):
      return True
    if hasattr(self.slides[0], 'text') and regex.search(" ".join(\
        s.title+" "+s.text for s in self.slides)):
      return True
  
  def edit(self):
    'Run the edit dialog for the presentation.'
    dialog = gtk.Dialog(_("New Presentation"), exposong.application.main,\
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    dialog.set_default_size(340, 400)
    if(self.title):
      dialog.set_title(_("Editing %s") % self.title)
    else:
      # TODO get_type() needs to be translated as well. Find the best way to do this.
      dialog.set_title(_("New %s Presentation") % self.get_type().title())
    notebook = gtk.Notebook()
    dialog.vbox.pack_start(notebook, True, True, 6)
    
    self._fields = dict()
    
    self._edit_tabs(notebook, dialog)
    
    notebook.show_all()
    
    if dialog.run() == gtk.RESPONSE_ACCEPT:
      self._edit_save()
      del(self._fields)
      
      self.to_xml()
      
      dialog.hide()
      return True
    else:
      dialog.hide()
      return False
  
  def _edit_tabs(self, notebook, parent):
    'Tabs for the dialog.'
    #Slide Timer
    if self._has_timer():
      timer = gtk.VBox()
      timer.set_border_width(8)
      timer.set_spacing(7)
      
      label = gtk.Label()
      label.set_markup(_("<b>Timer</b>"))
      label.set_alignment(0.0, 0.5)
      timer.pack_start(label, False)
      
      self._fields['timer_on'] = gtk.CheckButton(_("Use Timer"))
      self._fields['timer_on'].set_active(self.timer is not None)
      self._fields['timer_on'].connect("toggled",\
          lambda chk: self._fields['timer'].set_sensitive(chk.get_active()))
      self._fields['timer_on'].connect("toggled",\
          lambda chk: self._fields['timer_loop'].set_sensitive(chk.get_active()))
      timer.pack_start(self._fields['timer_on'], False)
      
      hbox = gtk.HBox()
      hbox.set_spacing(18)
      hbox.pack_start(gtk.Label(_("Seconds Per Slide")), False, False)
      
      self._fields['timer'] = gtk.SpinButton(gtk.Adjustment(1, 1, 25, 1, 3, 10), 1, 0)
      self._fields['timer'].set_sensitive(self.timer is not None)
      if isinstance(self.timer, (int, float)):
        self._fields['timer'].set_value(self.timer)
      hbox.pack_start(self._fields['timer'], False, False)
      timer.pack_start(hbox, False)
      
      self._fields['timer_loop'] = gtk.CheckButton(_("Loop Slides"))
      self._fields['timer_loop'].set_active(self.timer_loop)
      self._fields['timer_loop'].set_sensitive(self.timer is not None)
      timer.pack_start(self._fields['timer_loop'], False, False)
      
      notebook.append_page(timer, gtk.Label( _("Timer") ))
    
    # TODO: Presentation specific backgrounds.
  
  def _edit_save(self):
    'Save the fields if the user clicks ok.'
    if self._has_timer():
      if self._fields['timer_on'].get_active():
        self.timer = self._fields['timer'].get_value_as_int()
        self.timer_loop = self._fields['timer_loop'].get_active()
  
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
    
    if self.timer:
      node = doc.createElement("timer")
      node.setAttribute('time', str(self.timer))
      if self.timer_loop:
        node.setAttribute('loop', "1")
      root.appendChild(node)
    
    for s in self.slides:
      sNode = doc.createElement("slide")
      s.to_node(doc, sNode)
      root.appendChild(sNode)
    doc.appendChild(root)
    outfile = open(join(directory, self.filename), 'w')
    doc.writexml(outfile)
    doc.unlink()
  
  def slide_column(self, col, list_):
    'Set the column to use text.'
    col.clear()
    text_cr = gtk.CellRendererText()
    col.pack_start(text_cr, False)
    col.add_attribute(text_cr, 'markup', 1)
    list_.set_model(gtk.ListStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING))
  
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
  
  @staticmethod
  def _has_timer():
    'Returns boolean to show if we want to have timers.'
    return True
  
  def on_delete(self):
    'Called when the presentation is deleted.'
    pass

  def on_select(self):
    'Called when the presentation is focused.'
    pass

  def on_deselect(self):
    'Called when the presentation is blurred.'
    pass

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

