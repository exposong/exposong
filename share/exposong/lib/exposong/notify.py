#! /usr/bin/env python
import gtk
import exposong.screen

class Notify(gtk.HBox):
  def __init__(self):
    gtk.HBox.__init__(self)
    
    self.notify = gtk.Entry(45)
    self.notify.set_width_chars(15) #Prevent it from expanding wider than the preview
    self.notify.set_tooltip_text("Notification Text")
    self.notify.connect("activate", self._on_activate)
    self.notify.connect("focus-in-event", self._on_focus)
    self.notify.connect("focus-out-event", self._on_blur)
    self.pack_start(self.notify, True, True, 0)
    
    notify_clear = gtk.Button()
    img = gtk.Image()
    img.set_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_BUTTON)
    notify_clear.set_image(img)
    notify_clear.connect("clicked", self._on_clear)
    self.pack_start(notify_clear, False, True, 0)
    
    notify_save = gtk.Button()
    img = gtk.Image()
    img.set_from_stock(gtk.STOCK_OK, gtk.ICON_SIZE_BUTTON)
    notify_save.set_image(img)
    notify_save.connect("clicked", self._on_save)
    self.pack_start(notify_save, False, True, 0)
  
  def _on_save(self, *args):
    'The user clicked save.'
    exposong.screen.screen.notify(self.notify.get_text())
  
  def _on_clear(self, *args):
    'The user clicked clear.'
    self.notify.set_text("")
    exposong.screen.screen.notify()
  
  def _on_activate(self, *args):
    'The user clicked enter on the entry.'
    self._on_save()

  def _on_focus(self, *args):
    app = exposong.application
    for k in app.keys_to_disable:
      app.main.main_actions.get_action(k).disconnect_accelerator()
  
  def _on_blur(self, *args):
    app = exposong.application
    for k in app.keys_to_disable:
      app.main.main_actions.get_action(k).connect_accelerator()

notify = Notify()

