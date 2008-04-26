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
import os
import mimetypes

from exposong import DATA_PATH
import exposong.prefs
import exposong.screen

class BGSelect (gtk.VBox):
  '''
  Select the background.
  '''
  def __init__(self):
    gtk.VBox.__init__(self)
    
    curbg = exposong.prefs.config['pres.bg']
    
    hbox = gtk.HBox()
    self.imgradio = gtk.RadioButton()
    hbox.pack_start(self.imgradio, False, True, 2)
    self.imgmodel = gtk.ListStore(str, gtk.gdk.Pixbuf)
    self.imgcombo = gtk.ComboBox(self.imgmodel)
    hbox.pack_start(self.imgcombo, True, True, 2)
    self.imgcombo.set_wrap_width(2)
    cell = gtk.CellRendererPixbuf()
    self.imgcombo.pack_start(cell, True)
    self.imgcombo.add_attribute(cell, 'pixbuf', 1)
    if isinstance(curbg, str):
      self.imgradio.set_active(True)
    else:
      self.imgcombo.set_sensitive(False)
    
    directory = os.path.join(DATA_PATH, "bg")
    dir_list = os.listdir(directory)
    for filenm in dir_list:
      if os.path.isfile(os.path.join(directory, filenm)) and\
          mimetypes.guess_type(filenm)[0].startswith("image"):
        path = os.path.join(directory, filenm)
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(path, 80, 50)
        itr = self.imgmodel.append([path, pixbuf])
        if isinstance(curbg, str) and path == curbg:
          self.imgcombo.set_active_iter(itr)
    self.pack_start(hbox, False, True, 2)
    
    hbox = gtk.HBox()
    self.gradradio = gtk.RadioButton(self.imgradio)
    hbox.pack_start(self.gradradio, False, True, 2)
    self.graddir = gtk.combo_box_new_text()
    graddirlist = [ u'\u2192', u'\u2198', u'\u2193', u'\u2199' ]
    for st in graddirlist:
      self.graddir.append_text( st)
    if exposong.prefs.config['pres.bg_angle'] in graddirlist:
      self.graddir.set_active(graddirlist.index(exposong.prefs.config['pres.bg_angle']))
    else:
      self.graddir.set_active(0)
    vbox = gtk.VBox()
    vbox.pack_start(self.graddir, True, True, 2)
    self.grad1 = gtk.ColorButton()
    self.grad2 = gtk.ColorButton()
    hbox2 = gtk.HBox()
    hbox2.pack_start(self.grad1, True, True)
    hbox2.pack_start(self.grad2, True, True)
    vbox.pack_start(hbox2, True, True, 2)
    hbox.pack_start(vbox, True, True, 2)
    
    if isinstance(curbg, tuple):
      self.gradradio.set_active(True)
      self.grad1.set_color(gtk.gdk.Color(curbg[0][0], curbg[0][1], curbg[0][2]))
      self.grad2.set_color(gtk.gdk.Color(curbg[1][0], curbg[1][1], curbg[1][2]))
    
    self._on_image_radio(self.imgradio)
    self._on_grad_radio(self.gradradio)
    self.pack_start(hbox, False, True, 2)
    
    self.imgradio.connect("toggled", self._on_image_radio)
    self.imgcombo.connect('changed', self._on_image_change)
    self.gradradio.connect("toggled", self._on_grad_radio)
    self.graddir.connect("changed", self._on_grad_change)
    self.grad1.connect("color-set", self._on_grad_change)
    self.grad2.connect("color-set", self._on_grad_change)
  
  def _on_image_change(self, imgcombo):
    'Change to the selected image.'
    itr = imgcombo.get_active_iter()
    mod = imgcombo.get_model()
    exposong.prefs.config['pres.bg'] = mod.get_value(itr, 0)
    exposong.screen.screen.set_dirty()
  
  def _on_grad_change(self, *args):
    'The gradient has been modified.'
    exposong.prefs.config['pres.bg_angle'] = self.graddir.get_active_text()
    grad1 = self.grad1.get_color()
    grad2 = self.grad2.get_color()
    exposong.prefs.config['pres.bg'] = ((grad1.red,grad1.green,grad1.blue),
        (grad2.red,grad2.green,grad2.blue))
  
  def _on_image_radio(self, radio):
      self.imgcombo.set_sensitive(radio.get_active())
  
  def _on_grad_radio(self, radio):
      self.graddir.set_sensitive(radio.get_active())
      self.grad1.set_sensitive(radio.get_active())
      self.grad2.set_sensitive(radio.get_active())
    

