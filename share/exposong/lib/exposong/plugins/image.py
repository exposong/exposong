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
import shutil

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
type_icon = gtk.gdk.pixbuf_new_from_file_at_size(
    join(RESOURCE_PATH,'pres_image.png'), 20, 14)
thsz = (150, 150)

def get_rotate_const(rotate):
  if rotate == "cw":
    return gtk.gdk.PIXBUF_ROTATE_CLOCKWISE
  elif rotate == "ud":
    return gtk.gdk.PIXBUF_ROTATE_UPSIDEDOWN
  elif rotate == "ccw":
    return gtk.gdk.PIXBUF_ROTATE_COUNTERCLOCKWISE
  else:
    return gtk.gdk.PIXBUF_ROTATE_NONE

def get_rotate_str(rotate):
  if rotate == gtk.gdk.PIXBUF_ROTATE_CLOCKWISE:
    return "cw"
  elif rotate == gtk.gdk.PIXBUF_ROTATE_UPSIDEDOWN:
    return "ud"
  elif rotate == gtk.gdk.PIXBUF_ROTATE_COUNTERCLOCKWISE:
    return "ccw"
  else:
    return "n"


class ImageNotFoundError( Exception ):
  def __init__(self, image):
    self.image = image


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
      elif(isinstance(value, str)):
        self.title = ''
        self.image = value
        self.rotate = get_rotate_const("n") #TODO Make this possible
      
      if not os.path.isabs(self.image):
        self.image = os.path.join(DATA_PATH, 'image', self.image)
      elif not self.image.startswith(os.path.join(DATA_PATH, 'image')):
        newimg = os.path.join(DATA_PATH, 'image', os.path.split(self.image)[1])
        shutil.copyfile(self.image, newimg)
        self.image = newimg
      if not os.path.isfile(self.image):
        raise ImageNotFoundError(self.image)
      
      self._set_id(value)
    
    def get_thumb(self):
      if hasattr(self, "image"):
        if not hasattr(self, "thumb"):
          try:
            self.thumb = gtk.gdk.pixbuf_new_from_file_at_size(self.image, thsz[0], thsz[1])
            self.thumb.rotate_simple(self.rotate)
            return self.thumb
          except gobject.GError:
            print "Error: Could not open file."
      if hasattr(self, "thumb"):
        return self.thumb
      else:
        return gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 150, 150)
    
    def to_node(self, document, node):
      'Populate the node element'
      if(self.title):
        node.setAttribute("title", self.title)
      
      # <img src='..' rotate='n|cw|ccw|ud' />
      img = document.createElement("img")
      #if os.path.split(self.image)[0] == os.path.join(DATA_PATH,'image'):
      img.setAttribute("src", os.path.split(self.image)[1])
      #else:
      #  img.setAttribute("src", self.image)
      img.setAttribute("rotate", get_rotate_str(self.rotate))
      node.appendChild(img)
    
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
      ccontext = widget.window.cairo_create()
      bounds = widget.window.get_size()
      
      #draw a black background
      ccontext.set_source_rgb(0, 0, 0)
      ccontext.paint()
      
      if not hasattr(self,'pixbuf') or bounds[0] <> self.pixbuf.get_width()\
          or bounds[1] <> self.pixbuf.get_height():
        try:
          self.pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(self.image,\
              bounds[0], bounds[1]).rotate_simple(self.rotate)
        except gobject.GError:
          print "Error: Could not open background file."
          return
      ccontext.set_source_pixbuf(self.pixbuf, (bounds[0]-self.pixbuf.get_width())/2,\
      (bounds[1]-self.pixbuf.get_height())/2)
      ccontext.paint()
      return
  
  def __init__(self, dom = None, filename = None):
    _abstract.Presentation.__init__(self, dom, filename)
  
  def _set_slides(self, dom):
    'Set the slides from xml.'
    slides = dom.getElementsByTagName("slide")
    for sl in slides:
      try:
        self.slides.append(self.Slide(self, sl))
      except ImageNotFoundError, err:
        print "Image not found (%s), slide was not added to the \"%s.\"" % (err.image, self.title)
  
  def _edit_tabs(self, notebook, parent):
    'Tabs for the dialog.'
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
    
    toolbar = gtk.Toolbar()
    toolbar.set_style(gtk.TOOLBAR_ICONS)
    img_add = gtk.ToolButton(gtk.STOCK_ADD)
    toolbar.insert(img_add, 0)
    img_del = gtk.ToolButton(gtk.STOCK_DELETE)
    toolbar.insert(img_del, 1)
    vbox.pack_start(toolbar, False, True)
    
    self._fields['images'] = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_OBJECT)
    imgtree = gtk.TreeView(self._fields['images'])
    imgtree.set_reorderable(True)
    col = gtk.TreeViewColumn()
    img_cr = gtk.CellRendererPixbuf()
    col.pack_start(img_cr, False)
    col.add_attribute(img_cr, 'pixbuf', 1)
    imgtree.append_column(col)
    imgtree.set_headers_visible(False)
    imgscroll = gtk.ScrolledWindow()
    imgscroll.add(imgtree)
    imgscroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
    imgscroll.set_size_request(300, 290)
    
    for sl in self.slides:
      self._fields['images'].append( (sl.image, sl.get_thumb()) )
    vbox.pack_start(imgscroll, True, True)
    
    notebook.append_page(vbox, gtk.Label(_("Edit")))
    
    img_add.connect("clicked", self._on_img_add, imgtree)
    img_del.connect("clicked", self._on_img_del, imgtree)
    
    _abstract.Presentation._edit_tabs(self, notebook, parent)
  
  def _edit_save(self):
    'Save the fields if the user clicks ok.'
    self.title = self._fields['title'].get_text()
    self.slides = []
    itr = self._fields['images'].get_iter_first()
    while itr:
      self.slides.append(self.Slide(self, self._fields['images'].get_value(itr, 0)))
      itr = self._fields['images'].iter_next(itr)
    _abstract.Presentation._edit_save(self)
  
  def _on_img_add(self, button, treeview):
    'Add an image to the presentation.'
    fchooser = gtk.FileChooserDialog( _("Add Images"), button.get_toplevel(),\
        gtk.FILE_CHOOSER_ACTION_OPEN, (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,\
        gtk.STOCK_OK, gtk.RESPONSE_ACCEPT) )
    fchooser.set_select_multiple(True)
    progress = gtk.ProgressBar()
    fchooser.set_extra_widget(progress)
    
    filt = gtk.FileFilter()
    filt.set_name( _("Image Types") )
    filt.add_pixbuf_formats()
    fchooser.add_filter(filt)
    if fchooser.run() == gtk.RESPONSE_ACCEPT:
      files = fchooser.get_filenames()
      for fl in files:
        treeview.get_model().append( (fl, \
            gtk.gdk.pixbuf_new_from_file_at_size(fl, thsz[0], thsz[1])) )
        progress.set_fraction(progress.get_fraction() + 1.0/len(files))
        #It may be better to use generator statements here.
        #http://faq.pygtk.org/index.py?req=show&file=faq23.020.htp
        #This makes the progressbar change.
        while gtk.events_pending():
          gtk.main_iteration()
      
    fchooser.hide()
  
  def _on_img_del(self, button, treeview):
    'Remove an image from the presentation.'
    (model, s_iter) = treeview.get_selection().get_selected()
    if s_iter:
      if model.get_value(s_iter, 0).startswith(DATA_PATH):
        os.remove(model.get_value(s_iter, 0))
      model.remove(s_iter)
  
  def on_delete(self):
    'Called when the presentation is deleted.'
    for sl in self.slides:
      os.remove(sl.image)
  
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
  
  def slide_column(self, col, list_):
    'Set the column to use images.'
    col.clear()
    img_cr = gtk.CellRendererPixbuf()
    col.pack_start(img_cr, False)
    col.add_attribute(img_cr, 'pixbuf', 1)
    list_.set_model(gtk.ListStore(gobject.TYPE_PYOBJECT, gobject.TYPE_OBJECT))
  
  def get_slide_list(self):
    'Get the slide list.'
    return tuple( (sl, sl.get_thumb()) for sl in self.slides)
  
  def merge_menu(self, uimanager):
    'Merge new values with the uimanager.'
    factory = gtk.IconFactory()
    factory.add('exposong-image',gtk.IconSet(gtk.gdk.pixbuf_new_from_file(
        join(RESOURCE_PATH,'pres_image.png'))))
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
    return pres.__class__ is cls
  
  @staticmethod
  def get_version():
    'Return the version number of the plugin.'
    return (1,0)
  
  @staticmethod
  def get_description():
    'Return the description of the plugin.'
    return "A image presentation type."

