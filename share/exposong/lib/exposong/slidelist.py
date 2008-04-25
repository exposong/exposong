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

slidelist = None #will hold instance of SlideList

class SlideList(gtk.TreeView):
  '''
  Class to manipulate the text_area in the presentation program.
  '''
  def __init__(self):
    gtk.TreeView.__init__(self)
    self.set_size_request(280, 200)
    self.set_enable_search(False)
    
    text_cr = gtk.CellRendererText()
    text_cr.ellipsize = pango.ELLIPSIZE_END
    column1 = gtk.TreeViewColumn( _("Slide"), text_cr, markup=1)
    column1.set_resizable(False)
    self.append_column(column1)
    
    self.slide_list = gtk.ListStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING)
    self.set_model(self.slide_list)
    #self.set_headers_visible(False)
    
  def set_slides(self, slides):
    'Set the text to a Song.'
    self.slide_list.clear()
    for sl in slides:
      self.slide_list.append([sl, sl.get_markup()])
  
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


