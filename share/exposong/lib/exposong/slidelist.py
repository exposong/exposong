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
import random

import exposong.screen

slidelist = None #will hold instance of SlideList
slide_scroll = None

class SlideList(gtk.TreeView):
  '''
  Class to manipulate the text_area in the presentation program.
  '''
  def __init__(self):
    self.pres = None
    self.__timer = 0 #Used to stop or reset the timer if the presentation or slide changes.
    gtk.TreeView.__init__(self)
    self.set_size_request(280, 200)
    self.set_enable_search(False)
    
    self.column1 = gtk.TreeViewColumn( _("Slide"))
    self.column1.set_resizable(False)
    self.append_column(self.column1)
    #self.set_column()
    
    self.set_model(gtk.ListStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING))
    #self.set_headers_visible(False)
    self.connect("cursor-changed", self._on_slide_activate)
    
  #def set_slides(self, slides):
  #  'Set the text to a Song.'
  #  slist = self.get_model()
  #  slist.clear()
  #  for sl in slides:
  #    slist.append([sl, sl.get_markup()])
  #  print 1
  
  def set_presentation(self, pres):
    'Set the active presentation.'
    self.pres = pres
    slist = self.get_model()
    if pres is None:
      slist.clear()
    else:
      slist.clear()
      if not hasattr(self, 'pres_type') or self.pres_type is not pres.type:
        self.pres_type = pres.type
        pres.slide_column(self.column1)
      slist = self.get_model()
      for slide in pres.get_slide_list():
        slist.append(slide)
    self.__timer += 1
    men = slist.get_iter_first() is not None
    exposong.application.main.main_actions.get_action("pres-slide-next").set_sensitive(men)
    exposong.application.main.main_actions.get_action("pres-slide-prev").set_sensitive(men)
  
  def get_active_item(self):
    'Return the selected `Slide` object.'
    (model, s_iter) = self.get_selection().get_selected()
    if s_iter:
      return model.get_value(s_iter, 0)
    else:
      return False
  
  def prev_slide(self, widget):
    'Move to the previous slide.'
    (model, s_iter) = self.get_selection().get_selected()
    if s_iter:
      path = model.get_path(s_iter)
      if path[0] > 0:
        path = (path[0]-1,)
        self.set_cursor(path)
        self.scroll_to_cell(path)
  
  def next_slide(self, widget):
    'Move to the next slide.'
    selection = self.get_selection()
    (model, itr) = selection.get_selected()
    if itr:
      itr2 = model.iter_next(itr)
      if itr2:
        selection.select_iter(itr2)
        self.scroll_to_cell(model.get_path(itr2))
      elif self.pres and self.pres.timer_loop:
        selection.select_iter(model.get_iter_first())
        self.scroll_to_point(0,0)
      else: #The last slide is active.
        return False
    elif model.get_iter_first():
      selection.select_iter(model.get_iter_first())
      self.scroll_to_point(0,0)
    else: #No slides available.
      return False
    exposong.screen.screen.draw()
  
  def _on_slide_activate(self, *args):
    'Present the selected slide to the screen.'
    exposong.screen.screen.draw()
    self.__timer += 1
    if self.pres.timer:
      gobject.timeout_add(self.pres.timer*1000, self._set_timer, self.__timer)
  
  def _set_timer(self, t):
    'Starts the timer, or continues a current timer.'
    if t <> self.__timer:
      return False
    self.next_slide(None)
    return True

