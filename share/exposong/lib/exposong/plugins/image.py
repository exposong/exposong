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
import gobject

from exposong.glob import *
from exposong import RESOURCE_PATH, DATA_PATH
from exposong.plugins import Plugin, _abstract
import exposong.application
from exposong.prefs import config

"""
Image presentations.
"""
information = {
    'name': _("Image Presentation"),
    'description': __doc__,
    'required': False,
}
type_icon = gtk.gdk.pixbuf_new_from_file(join(RESOURCE_PATH,'image.png'))

def get_rotate_const(rotate):
  if rotate == "cw":
    return gtk.gdk.PIXBUF_ROTATE_CLOCKWISE
  elif rotate == "ud":
    return gtk.gdk.PIXBUF_ROTATE_UPSIDEDOWN
  elif rotate == "ccw":
    return gtk.gdk.PIXBUF_ROTATE_COUNTERCLOCKWISE
  else:
    return gtk.gdk.PIXBUF_ROTATE_NONE

class Presentation (Plugin, _abstract.Presentation, _abstract.Menu,
    _abstract.Schedule, _abstract.Screen):
  '''
  Image presentation type.
  '''
  class Slide (Plugin, _abstract.Presentation.Slide):
    '''
    An image slide.
    '''
    def __init__(self, pres, value):
      self.pres = pres
      
      if(isinstance(value, xml.dom.Node)):
        self.title = value.getAttribute("title")
        imgdom = value.getElementsByTagName("img").item(0)
        if imgdom:
          self.image = imgdom.getAttribute("src")
          self.rotate = get_rotate_const(imgdom.getAttribute("rotate"))
        
      elif(isinstance(value, gtk.Image)):
        self.title = ''
        self.image = value
      
      if not os.path.isabs(self.image):
        self.image = DATA_PATH + '/image/' + self.image
      
      if hasattr(self, "image"):
        self.thumb = gtk.gdk.pixbuf_new_from_file_at_size(self.image, 150, 150)\
            .rotate_simple(self.rotate)
    
    @staticmethod
    def get_version():
      'Return the version number of the plugin.'
      return (1, 0)
    
    @staticmethod
    def get_description():
      'Return the description of the plugin.'
      return "An image presentation type."
    
    def draw(self, widget):
      'Override screen to draw an image instead of text.'
      return True
  
  def __init__(self, dom = None, filename = None):
    _abstract.Presentation.__init__(self, dom, filename)
    self.type = 'image'
  
  def edit(self):
    'Run the edit dialog for the presentation.'
    raise Exception("Does not work yet.")
    
    dialog = gtk.Dialog(_("New Presentation"), exposong.application.main, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    if(self.title):
      dialog.set_title(_("Editing %s") % self.title)
    else:
      dialog.set_title(_("New %s Presentation") % self.type.title())
    notebook = gtk.Notebook()
    dialog.vbox.pack_start(notebook, True, True, 6)
    
    vbox = gtk.VBox()
    vbox.set_border_width(4)
    vbox.set_spacing(7)
    hbox = gtk.HBox()
    
    label = gtk.Label(_("Title:"))
    label.set_alignment(0.5, 0.5)
    hbox.pack_start(label, False, True, 5)
    title = gtk.Entry(45)
    title.set_text(self.title)
    hbox.pack_start(title, True, True)
    
    vbox.pack_start(hbox, False, True)
    
    #text = gtk.TextView()
    #text.set_wrap_mode(gtk.WRAP_WORD)
    #self.set_text_buffer(text.get_buffer())
    #text_scroll = gtk.ScrolledWindow()
    #text_scroll.add(text)
    #text_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
    #text_scroll.set_size_request(340, 240)
    #vbox.pack_start(text_scroll, True, True)
    notebook.append_page(vbox, gtk.Label(_("Edit")))
    
    notebook.show_all()
    
    if(dialog.run() == gtk.RESPONSE_ACCEPT):
      bounds = text.get_buffer().get_bounds()
      self.title = title.get_text()
      self.author['words'] = words.get_text()
      self.author['music'] = music.get_text()
      self.copyright = copyright.get_text()
      sval = text.get_buffer().get_text(bounds[0], bounds[1])
      self.slides = []
      for sl in sval.split("\n\n"):
        self.slides.append(self.Slide(self, sl))
      self.to_xml()
      
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
    root.setAttribute("type", self.type)
    
    node = doc.createElement("title")
    node.appendChild(doc.createTextNode(self.title))
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
    return 'image'
  
  @staticmethod
  def get_icon():
    'Return the pixbuf icon.'
    return type_icon
  
  def set_text_buffer(self, tbuf):
    'Sets the value of the buffer.'
    pass
  
  def slide_column(self, col):
    'Set the column to use images.'
    col.clear()
    img_cr = gtk.CellRendererPixbuf()
    col.pack_start(img_cr, False)
    col.add_attribute(img_cr, 'pixbuf', 1)
    
    exposong.slidelist.slidelist.set_model(\
        gtk.ListStore(gobject.TYPE_PYOBJECT, gobject.TYPE_OBJECT))
  
  def get_slide_list(self):
    'Get the slide list.'
    return tuple( (sl, sl.thumb) for sl in self.slides)
  
  def merge_menu(self, uimanager):
    'Merge new values with the uimanager.'
    factory = gtk.IconFactory()
    factory.add('exposong-image',gtk.IconSet(gtk.gdk.pixbuf_new_from_file(
        join(RESOURCE_PATH,'image.png'))))
    factory.add_default()
    gtk.stock_add([("exposong-image",_("_Image"), gtk.gdk.MOD1_MASK, 
        0, "pymserv")])
    
    actiongroup = gtk.ActionGroup('exposong-image')
    actiongroup.add_actions([("pres-new-image", 'exposong-image', None, None,
        None, self._on_pres_new)])
    uimanager.insert_action_group(actiongroup, -1)
    
    self.menu_merge_id = uimanager.add_ui_from_string("""
      <menubar name='MenuBar'>
        <menu action="Presentation">
            <menu action="pres-new">
              <menuitem action='pres-new-image' />
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
    return _('Image Presentations')
  
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
    return "A image presentation type."

