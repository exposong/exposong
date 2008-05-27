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
import gobject
import pango

import exposong.screen
import cellrendererimage

slidelist = None #will hold instance of SlideList

class SlideList(gtk.TreeView):
  '''
  Class to manipulate the text_area in the presentation program.
  '''
  def __init__(self):
    gtk.TreeView.__init__(self)
    self.set_size_request(280, 200)
    self.set_enable_search(False)
    
    self.column1 = gtk.TreeViewColumn( _("Slide"))
    self.column1.set_resizable(False)
    self.append_column(self.column1)
    #self.set_column()
    
    self.slide_list = gtk.ListStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING)
    self.set_model(self.slide_list)
    #self.set_headers_visible(False)
    
  def set_slides(self, slides):
    'Set the text to a Song.'
    self.slide_list.clear()
    for sl in slides:
      self.slide_list.append([sl, sl.get_markup()])
  
  def set_presentation(self, pres):
    'Set the active presentation.'
    if pres is None:
      self.slide_list.clear()
    else:
      self.slide_list.clear()
      if not hasattr(self, 'pres_type') or self.pres_type is not pres.type:
        self.pres_type = pres.type
        pres.slide_column(self.column1)
      for slide in pres.get_slide_list():
        self.slide_list.append(slide)
    
  
  #def set_column(self, img=False):
  #  'Set the display column to image type.'
  #  self.column1.clear()
  #  if img:
  #    img_cr = cellrendererimage.CellRendererImage()
  #    self.column1.pack_start(img_cr, False)
  #    self.column1.add_attribute(img_cr, 'image', 1)
  #  else:
  #    text_cr = gtk.CellRendererText()
  #    text_cr.ellipsize = pango.ELLIPSIZE_END
  #    self.column1.pack_start(text_cr, False)
  #    self.column1.add_attribute(text_cr, 'markup', 1)
  
  def get_active_item(self):
    'Return the selected `Slide` object.'
    (model, s_iter) = self.get_selection().get_selected()
    if s_iter:
      return model.get_value(s_iter, 0)
    else:
      return False
  
  def prev_slide(self, widget):
    'Move to the previous slide.'
    print 'prev'
  
  def next_slide(self, widget):
    'Move to the next slide.'
    print 'next'
  
  def _on_slide_activate(self, *args):
    'Present the selected slide to the screen.'
    exposong.screen.screen.draw()


