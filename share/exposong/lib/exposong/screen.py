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
import pango
import cairo
import time
import gobject

import exposong.prefs
import exposong.slidelist
import exposong.application
from exposong.config import config


def c2dec(color):
  if isinstance(color, (tuple, list)):
    return tuple(c2dec(x) for x in color)
  else:
    return color / 65535.0

screen = None # will be the instance variable for Screen once Main runs
preview_height = 145

class Screen:
  '''
  Manage the window for presentation.
  '''
  
  def __init__(self, preview):
    self._black = self._background = self._logo = False
    self.bg_dirty = False
    self._notification = None
    self.bg_img = {}
    
    self.window = gtk.Window(gtk.WINDOW_POPUP)
    
    self.pres = gtk.DrawingArea()
    self.pres.connect("expose-event", self.expose)
    #self.pres.set_redraw_on_allocate(False) #This may fix the compiz redraw problem.
    self.pres.show()
    self.window.add(self.pres)
    
    if isinstance(preview, gtk.DrawingArea):
      self.preview = preview
      self.preview.connect("expose-event", self.expose)
    else:
      raise Exception("'preview' must be gtk.DrawingArea")
    
    #self.draw()
  
  def reposition(self, parent):
    '''
    Finds the best location for the screen.
    
    If the user is using one monitor, use the bottom right corner for
    the presentation screen, otherwise, use the 2nd monitor.
    '''
    if config.has_option('screen','monitor'):
      geometry = map(int, config.get('screen', 'monitor').split(','))
    else:
      screen = parent.get_screen()
      num_monitors = screen.get_n_monitors()
      if(num_monitors > 1):
        scr_geom = screen.get_monitor_geometry(1)
        geometry = (scr_geom.x, scr_geom.y, scr_geom.width, scr_geom.height)
      else:
        # No 2nd monitor, so preview it small in the corner of the screen
        scr_geom = screen.get_monitor_geometry(0)
        parent.move(0,0)
        geometry = (scr_geom.width/2, scr_geom.height/2, scr_geom.width/2, scr_geom.height/2)
    self.window.move(geometry[0], geometry[1])
    self.window.resize(geometry[2], geometry[3])
    self.aspect = float(geometry[2])/geometry[3]
    self.preview.set_size_request(int(preview_height*self.aspect), preview_height)
  
  #def set_background(self, **keys):
  # 'Set the background color.'
  # self._set_background(self.preview, **keys)
  # if hasattr(self, "pres") and self.pres.window:
  #   self._set_background(self.pres, **keys)
  
  #def set_text(self, text):
  #  'Set the text of the window.'
  #  self.text = str(text)
  #  self.draw()
  
  def draw(self):
    'Redraw the presentation and preview screens.'
    if self.pres.window and self.pres.window.is_viewable():
      self.pres.queue_draw()
    else:
      self.preview.queue_draw()
  
  def to_black(self, button):
    'Set the screen to black.'
    self._black = True
    self._background = self._logo = False
    self.draw()
  
  def to_logo(self, button):
    'Set the screen to black.'
    if config.has_option("screen", "logo"):
      self._logo = True
      self._black = self._background = False
      self.draw()
    else:
      dialog = gtk.MessageDialog(exposong.application.main, gtk.DIALOG_MODAL,
        gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
        _('No Logo set. Do you want to choose a Logo now?'))
      dialog.set_title( _("Set Logo?") )
      resp = dialog.run()
      dialog.hide()
      if resp == gtk.RESPONSE_YES:
        exposong.prefs.prefs.dialog(exposong.application.main)
        self.to_logo(None)
      else:
        self.to_background(None)
  
  def to_background(self, button):
    'Hide text from the screen.'
    self._background = True
    self._black = self._logo = False
    self.draw()
  
  def hide(self, button):
    'Remove the presentation screen from view.'
    self._background = self._black = self._logo = False
    self.window.hide()
    self._set_menu_items_disabled()
  
  def show(self, *args):
    'Show the presentation screen.'
    self._background = self._black = self._logo = False
    self.window.show_all()
    self.draw()
    self._set_menu_items_disabled()
  
  def expose(self, widget, event):
    'Redraw `widget`.'
    self._draw(widget)
  
  def set_dirty(self, dirty = True):
    'Reload the background image if necessary.'
    self.bg_dirty = dirty
  
  def notify(self, text = None):
    'Put up notification text on the screen.'
    self._notification = text
    self.draw()
  
  def _set_background(self, widget, ccontext = None, bounds = None):
    'Set the background of `widget` to `color`.'
    if not widget.window:
      return False
    
    if ccontext is None:
      ccontext = widget.window.cairo_create()
    if bounds is None:
      bounds = widget.window.get_size()
    
    if self._black and widget is self.pres:
      bg = (0, 0, 0)
    elif self._logo and widget is self.pres:
      if not hasattr(self,"_logo_pbuf"):
        try:
          self._logo_pbuf = gtk.gdk.pixbuf_new_from_file_at_size(
              config.get("screen", "logo"), int(bounds[0]/1.5), int(bounds[1]/1.5))
        except gobject.GError:
          print "Error: Could not open logo file."
          self._logo_pbuf = None
      bg = c2dec(config.getcolor("screen", "logo_bg"))
      ccontext.set_source_rgb(bg[0], bg[1], bg[2])
      ccontext.paint()
      if self._logo_pbuf <> None:
        ccontext.set_source_pixbuf(self._logo_pbuf, (bounds[0]-self._logo_pbuf.get_width())/2,\
        (bounds[1]-self._logo_pbuf.get_height())/2)
        ccontext.paint()
      return
    else:
      bgtype = config.get("screen", "bg_type")
      bgimage = config.get("screen", "bg_image")    
      bgcolor1 = config.getcolor("screen", "bg_color_1")
      bgcolor2 = config.getcolor("screen", "bg_color_2")
    
    if bgtype == 'image':
      bgkey = str(bounds[0])+'x'+str(bounds[1])
      try:
        if self.bg_dirty or bgkey not in self.bg_img:
          pixbuf = gtk.gdk.pixbuf_new_from_file(bgimage)
          self.bg_img[bgkey] = pixbuf.scale_simple(bounds[0], bounds[1],
              gtk.gdk.INTERP_BILINEAR)
      except gobject.GError:
        print "Error: Could not open background file."
        if hasattr(self, 'bg_img') and bgkey in self.bg_img:
          del self.bg_img[bgkey]
        bg = (0,0,0)
        #Set back to the default
        config.setcolor("screen", "bg_color_1", (0, 13107, 19660))
        config.setcolor("screen", "bg_color_2", (0, 26214, 39321))
      else:
        ccontext.set_source_pixbuf(self.bg_img[bgkey], 0, 0)
        ccontext.paint()
        return
      finally:
        self.bg_dirty = False
    
    elif bgtype == 'color':
      color = (c2dec(bgcolor1), c2dec(bgcolor2))
    
      if len(color) >= 3 and isinstance(color[0], (float, int)):
        # Draw a solid color
        ccontext.set_source_rgb(color[0], color[1], color[2])
        ccontext.paint()
      elif isinstance(color[0], tuple):
        # Draw a gradiant
        if config.get("screen", "bg_angle") == u"\u2193": #Down
          gr_x1 = gr_y1 = gr_x2 = 0
          gr_y2 = bounds[1]
        elif config.get("screen", "bg_angle") == u'\u2199': #Down-Left
          gr_x2 = gr_y1 = 0
          (gr_x1, gr_y2) = bounds
        elif config.get("screen", "bg_angle") == u'\u2192': #Right
          gr_x1 = gr_y1 = gr_y2 = 0
          gr_x2 = bounds[0]
        else: # Down-Right
          gr_x1 = gr_y1 = 0
          (gr_x2, gr_y2) = bounds
        gradient = cairo.LinearGradient(gr_x1, gr_y1, gr_x2, gr_y2)
        for i in range(len(color)):
          gradient.add_color_stop_rgb(1.0*i/(len(color)-1), color[i][0],
              color[i][1], color[i][2])
        ccontext.rectangle(0,0, bounds[0], bounds[1])
        ccontext.set_source(gradient)
        ccontext.fill()
      else:
        print "_set_background: Incorrect color"
  
  def _draw(self, widget):
    'Render `widget`.'
    if not widget.window or not widget.window.is_viewable():
      return False
    
    ccontext = widget.window.cairo_create()
    screenW, screenH = widget.window.get_size()
    if widget is self.preview and self.pres.window and self.pres.window.is_viewable():
      #Scale if the presentation window size is available
      win_sz = self.pres.window.get_size()
      width = int(float(preview_height)*win_sz[0]/win_sz[1])
      screenW = screenW*win_sz[0]/width
      screenH = screenH*win_sz[1]/preview_height
      ccontext.scale(float(width)/win_sz[0], float(preview_height)/win_sz[1])
    elif widget is self.pres:
      self.preview.queue_draw()
    
    slide = exposong.slidelist.slidelist.get_active_item()
    
    if widget is self.pres and (self._background or self._black or self._logo) \
        or not slide:
      #When there's no text to render, just draw the background
      self._set_background(widget, ccontext, (screenW, screenH))
    else:
      
      if slide.draw(widget) is not NotImplemented:
        return True
      
      self._set_background(widget, ccontext, (screenW, screenH))
      
      txcol = c2dec(config.getcolor("screen", "text_color"))
      screenCenterY = screenH/2
      # Header text
      # TODO
      
      # Footer text
      ftext = slide.footer_text()
      if ftext is not NotImplemented:
        ftext = str(ftext)
        if isinstance(ftext, (unicode, str)) and len(ftext):
          layout = ccontext.create_layout()
          layout.set_text(ftext)
          layout.set_alignment(pango.ALIGN_CENTER)
          layout.set_width(int(screenW*pango.SCALE * 0.97))
          
          layout.set_font_description(pango.FontDescription("Sans Bold "+str(int(screenH/54.0))))
          
          footer_height = layout.get_pixel_size()[1]
          
          ccontext.set_source_rgba(txcol[0], txcol[1], txcol[2], 1.0)
          ccontext.move_to(screenW * 0.015, screenH - footer_height)
          ccontext.show_layout(layout)
          
          screenH -= footer_height
          screenCenterY -= footer_height/2
          
      # Body Text
      layout = ccontext.create_layout()
      
      size = 16
      layout.set_text(str(slide.body_text()))
      layout.set_alignment(pango.ALIGN_CENTER)
      layout.set_width(int(screenW*pango.SCALE * 0.97))
      
      layout.set_font_description(pango.FontDescription("Sans Bold "+str(size)))
      
      min_sz = 0
      max_sz = config.getfloat("screen", "max_font_size")
      
      #Loop through until the text is between 78% of the height and 94%, or
      #until we get a number that is not a multiple of 4 (2,6,10,14, etc) to
      #make it simpler... TODO Double check that it doesn't overflow
      while True:
        if layout.get_pixel_size()[0] > screenW*0.97 \
            or layout.get_pixel_size()[1] > screenH*0.94:
          max_sz = size
          size = (min_sz + max_sz) / 2
        elif size % 4 != 0 or max_sz - min_sz < 3:
          break
        elif layout.get_pixel_size()[1] < screenH*0.78:
          min_sz = size
          if(max_sz):
            size = (min_sz + max_sz) / 2
          else:
            size = size * 2
        else:
          break
        layout.set_font_description(pango.FontDescription("Sans Bold "+str(size)))
      
      if config.getcolor("screen", "text_shadow"):
        shcol = c2dec(config.getcolor("screen", "text_shadow"))
        ccontext.set_source_rgba(shcol[0], shcol[1], shcol[2], shcol[3])
        ccontext.move_to(screenW * 0.015 + size*0.1,
            screenCenterY - layout.get_pixel_size()[1]/2.0 + size*0.1)
        ccontext.show_layout(layout)
      ccontext.set_source_rgba(txcol[0], txcol[1], txcol[2], 1.0)
      ccontext.move_to(screenW * 0.015,screenCenterY - layout.get_pixel_size()[1]/2.0)
      ccontext.show_layout(layout)
    
    #Draw notification
    if widget is self.pres and self._notification:
      layout = ccontext.create_layout()
      layout.set_text(self._notification)
      
      notify_sz = int(screenH/12.0)
      layout.set_font_description(pango.FontDescription("Sans Bold "+str(notify_sz)))
      while layout.get_pixel_size()[0] > screenW*0.6:
        notify_sz = int(notify_sz*0.89)
        layout.set_font_description(pango.FontDescription("Sans Bold "+str(notify_sz)))
      sbounds = widget.window.get_size()
      nbounds = layout.get_pixel_size()
      pad = notify_sz/14.0
      ccontext.rectangle(sbounds[0]-nbounds[0]-pad*2, sbounds[1]-nbounds[1]-pad*2,
          sbounds[0], sbounds[1])
      ccontext.set_source_rgb(config.getcolor("screen", "notify_bg")[0],
          config.getcolor("screen", "notify_bg")[1],
          config.getcolor("screen", "notify_bg")[2])
      ccontext.fill()
      ccontext.set_source_rgb(1.0, 1.0, 1.0)
      ccontext.move_to(sbounds[0]-nbounds[0]-pad, sbounds[1]-nbounds[1]-pad)
      ccontext.show_layout(layout)
    return True
  
  def _set_menu_items_disabled(self):
    'Disable buttons if the presentation is not shown.'
    enabled = self.pres.window and self.pres.window.is_viewable()
    actions = exposong.application.main.main_actions
    actions.get_action("Background").set_sensitive(enabled)
    actions.get_action("Logo").set_sensitive(enabled)
    actions.get_action("Black Screen").set_sensitive(enabled)
    actions.get_action("Hide").set_sensitive(enabled)

