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
import os
import mimetypes
import shutil

from exposong import DATA_PATH
from exposong.glob import *
from exposong.config import config
import exposong.screen
import exposong.application

thsz = (80, 50)

class BGSelect (gtk.VBox):
  '''
  Select the background.
  '''
  def __init__(self):
    gtk.VBox.__init__(self)
    
    bgtype = config.get("screen","bg_type")
    bgimage = config.get("screen","bg_image")    
    bgcolor1 = config.getcolor("screen","bg_color_1")
    bgcolor2 = config.getcolor("screen","bg_color_2")
    
    
    # Image Background
    hbox = gtk.HBox()
    vbox = gtk.VBox()
    self.imgradio = gtk.RadioButton()
    hbox.pack_start(self.imgradio, False, True, 2)
    self.imgmodel = gtk.ListStore(str, gtk.gdk.Pixbuf)
    self.imgcombo = gtk.ComboBox(self.imgmodel)
    vbox.pack_start(self.imgcombo, True, True, 2)
    self.imgcombo.set_wrap_width(2)
    cell = gtk.CellRendererPixbuf()
    self.imgcombo.pack_start(cell, True)
    self.imgcombo.add_attribute(cell, 'pixbuf', 1)
    if bgtype == 'image':
      self.set_background_to_image()
    else:
      self.imgcombo.set_sensitive(False)
    
    directory = os.path.join(DATA_PATH, "bg")
    dir_list = os.listdir(directory)
    for filenm in dir_list:
      if os.path.isfile(os.path.join(directory, filenm)):
        mime = mimetypes.guess_type(filenm)
        if mime[0] and mime[0].startswith("image"):
          path = os.path.join(directory, filenm)
          pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(path, thsz[0], thsz[1])
          itr = self.imgmodel.append([path, pixbuf])
          if path == bgimage:
            self.imgcombo.set_active_iter(itr)
    
    self.new_image = gtk.Button( _("Add"), gtk.STOCK_ADD, False)
    self.new_image.connect("clicked", self._on_new_image)
    vbox.pack_start(self.new_image, False, True, 2)
    hbox.pack_start(vbox, True, True, 2)
    self.pack_start(hbox, True, True, 2)
    
    # Gradient Background
    hbox = gtk.HBox()
    self.gradradio = gtk.RadioButton(self.imgradio)
    hbox.pack_start(self.gradradio, False, True, 2)
    self.graddir = gtk.combo_box_new_text()
    graddirlist = [ u'\u2192', u'\u2198', u'\u2193', u'\u2199' ]
    for st in graddirlist:
      self.graddir.append_text( st)
    if config.get("screen","bg_angle") in graddirlist:
      self.graddir.set_active(graddirlist.index(config.get("screen","bg_angle")))
    else:
      self.graddir.set_active(0)
    hbox.pack_start(self.graddir, True, True, 2)
    self.grad1 = gtk.ColorButton()
    self.grad2 = gtk.ColorButton()
    hbox.pack_start(self.grad1, True, True)
    hbox.pack_start(self.grad2, True, True)
    
    self.grad1.set_color(gtk.gdk.Color(bgcolor1[0], bgcolor1[1], bgcolor1[2]))
    self.grad2.set_color(gtk.gdk.Color(bgcolor2[0], bgcolor2[1], bgcolor2[2]))
    if bgtype == 'color':
      self.set_background_to_color()
      
    self._on_image_radio(self.imgradio)
    self._on_grad_radio(self.gradradio)
    self.pack_start(hbox, True, True, 2)
    
    self.imgradio.connect("toggled", self._on_image_radio)
    self.imgcombo.connect('changed', self._on_image_change)
    self.gradradio.connect("toggled", self._on_grad_radio)
    self.graddir.connect("changed", self._on_grad_change)
    self.grad1.connect("color-set", self._on_grad_change)
    self.grad2.connect("color-set", self._on_grad_change)
  
  def _on_image_change(self, imgcombo):
    'A new image was selected.'
    itr = imgcombo.get_active_iter()
    if itr:
      mod = imgcombo.get_model()
      config.set("screen", "bg_image", mod.get_value(itr, 0))
      exposong.screen.screen.set_dirty()
      exposong.screen.screen.draw()
  
  def _on_grad_change(self, *args):
    'The gradient has been modified.'
    grad1 = self.grad1.get_color()
    grad2 = self.grad2.get_color()
    config.setcolor("screen", "bg_color_1", (grad1.red,grad1.green,grad1.blue))
    config.setcolor("screen", "bg_color_2", (grad2.red,grad2.green,grad2.blue))
    config.set("screen", "bg_angle", self.graddir.get_active_text())
    exposong.screen.screen.draw()
  
  def _on_image_radio(self, radio):
    'The image radioButton was changed.'
    self.imgcombo.set_sensitive(radio.get_active())
    self.new_image.set_sensitive(radio.get_active())
    if radio.get_active():
      self._on_image_change(self.imgcombo)
      config.set("screen", "bg_type", "image")
  
  def _on_grad_radio(self, radio):
    'The gradient radioButton was changed.'
    self.graddir.set_sensitive(radio.get_active())
    self.grad1.set_sensitive(radio.get_active())
    self.grad2.set_sensitive(radio.get_active())
    if radio.get_active():
      self._on_grad_change()
      config.set("screen", "bg_type", "color")
  
  def _on_new_image(self, button):
    'The user added a new image as a background.'
    fltr = gtk.FileFilter()
    fltr.set_name( _("Image Types"))
    fltr.add_mime_type("image/jpeg")
    fltr.add_mime_type("image/png")
    fltr.add_mime_type("image/gif")
    dlg = gtk.FileChooserDialog( _("Add Image"), exposong.application.main,
        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK,
        gtk.RESPONSE_ACCEPT))
    dlg.add_filter(fltr)
    dlg.set_current_folder(os.path.expanduser("~"))
    dlg.set_select_multiple(True)
    if dlg.run() == gtk.RESPONSE_ACCEPT:
      images = dlg.get_filenames()
      dlg.destroy()
      self.add_images(images)
    else:
      dlg.destroy()

  def set_background_to_color(self):
    self.gradradio.set_active(True) 

  def set_background_to_image(self):
    self.imgradio.set_active(True)

  def add_images(self, images):
    'Adds new images to the background selector'
    itr = None
    for img in images:
      newimg = find_freefile(os.path.join(DATA_PATH, 'bg', os.path.basename(img)))
      shutil.copyfile(img, newimg)
      itr = self.imgmodel.append([newimg,
          gtk.gdk.pixbuf_new_from_file_at_size(newimg, thsz[0], thsz[1])])
    if itr:
      self.imgcombo.set_active_iter(itr)
    