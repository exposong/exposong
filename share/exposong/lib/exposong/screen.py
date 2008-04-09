#! /usr/bin/env python
#
#	Copyright (C) 2008 Fishhookweb.com
#
#	ExpoSong is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
import gtk
import pango
import cairo
import time

from exposong import prefs

COLOR_BLACK = (0, 0, 0)
def c2dec(color):
	if isinstance(color, tuple):
		return tuple(c2dec(x) for x in color)
	else:
		return color / 65535.0

screen = None # will be the instance variable for Screen once Main runs

class Screen:
	'''
	Manage the window for presentation.
	'''
	
	def __init__(self, preview):
		self.text = ''
		self.black = self.background = False
		
		self.window = gtk.Window(gtk.WINDOW_POPUP)
		
		self.pres = gtk.DrawingArea()
		self.pres.connect("expose-event", self.expose)
		self.pres.show()
		self.window.add(self.pres)
		
		if isinstance(preview, gtk.DrawingArea):
			self.preview = preview
			self.preview.connect("expose-event", self.expose)
		else:
			raise Exception("'preview' must be gtk.DrawingArea")
		
		self.set_background()
	
	def auto_locate(self, main):
		'''
		Finds the best location for the screen.
		
		If the user is using one monitor, use the bottom right corner for
		the presentation screen, otherwise, use the 2nd monitor.
		'''
		screen = main.get_screen()
		num_monitors = screen.get_n_monitors()
		if(num_monitors > 1):
			scr_geom = screen.get_monitor_geometry(1)
			geometry = (scr_geom.x, scr_geom.y, scr_geom.width, scr_geom.height)
		else:
			# No 2nd monitor, so preview it small in the corner of the screen
			scr_geom = screen.get_monitor_geometry(0)
			main.move(0,0)
			geometry = (scr_geom.width/2, scr_geom.height/2, scr_geom.width/2, scr_geom.height/2)
		self.window.move(geometry[0], geometry[1])
		self.window.resize(geometry[2], geometry[3])
		self.preview.set_size_request(135*geometry[2]/geometry[3], 135)
	
	def set_background(self, color = None):
		'Set the background color.'
		self._set_background(self.preview, color)
		if hasattr(self, "pres") and self.pres.window:
			self._set_background(self.pres, color)
	
	def set_text(self, text):
		'Set the text of the window.'
		self.text = str(text)
		self.draw()
	
	def draw(self):
		'Redraw the presentation and preview screens.'
		self._draw(self.pres)
		self._draw(self.preview)
	
	def to_black(self, button):
		'Set the screen to black.'
		self.black = True
		self.background = False
		self.set_background(COLOR_BLACK)
	
	def to_background(self, button):
		'Hide text from the screen.'
		self.background = True
		self.black = False
		self.set_background()
	
	def hide(self, button):
		'Remove the presentation screen from view.'
		self.background = self.black = False
		self.window.hide()
	
	def show(self, *args):
		'Show the presentation screen.'
		self.background = self.black = False
		self.window.show_all()
		self.draw()
	
	def expose(self, widget, event):
		'Redraw `widget`.'
		self._draw(widget)
	
	
	
	def _set_background(self, widget, color = None):
		'Set the background of `widget` to `color`.'
		if color == None:
			color = c2dec(prefs.config['pres.bg'])
		
		if not widget.window:
			return False
		ccontext = widget.window.cairo_create()
		if len(color) >= 3 and isinstance(color[0], (float, int)):
			ccontext.set_source_rgb(color[0], color[1], color[2])
			ccontext.paint()
		elif isinstance(color[0], tuple):
			bounds = widget.window.get_size()
			#TODO Strings are too long for comparison. Constants or 2-4
			# character strings would be better.
			if prefs.config['pres.bg_angle'] == "Top to Bottom":
				gr_x1 = gr_y1 = gr_x2 = 0
				gr_y2 = bounds[1]
			elif prefs.config['pres.bg_angle'] == 'Top Right to Bottom Left':
				gr_x2 = gr_y1 = 0
				(gr_x1, gr_y2) = bounds
			elif prefs.config['pres.bg_angle'] == 'Left to Right':
				gr_x1 = gr_y1 = gr_y2 = 0
				gr_x2 = bounds[0]
			else:
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
		if widget is self.preview and self.pres.window and self.pres.window.is_viewable():
			#Get a copy of the presentation window if it's visible
			win_sz = self.pres.window.get_size()
			width = int(135.0*win_sz[0]/win_sz[1])
			#widget.set_size_request(width, 135)
			ccontext = widget.window.cairo_create()
			ccontext.scale(float(width)/win_sz[0], 135.0/win_sz[1])
			ccontext.set_source_surface(self.pres.window.cairo_create().get_target(), 1, 1)
			ccontext.paint()
			return True
		
		if self.black:
			self._set_background(widget, COLOR_BLACK)
			return True
		elif len(self.text) == 0 or self.background:
			#When there's no text to render, just draw the background
			self._set_background(widget)
			return True
		
		ccontext = widget.window.cairo_create()
		layout = ccontext.create_layout()
		bounds = widget.window.get_size()
		
		size = 16
		layout.set_text(self.text)
		layout.set_alignment(pango.ALIGN_CENTER)
		layout.set_width(int(bounds[0]*pango.SCALE * 0.97))
		
		attrs = pango.AttrList()
		attrs.insert(pango.AttrFontDesc(pango.FontDescription("Sans Bold "+str(size)),
				end_index = len(self.text)))
		layout.set_attributes(attrs)
		
		min_sz = 0
		max_sz = int(prefs.config['pres.max_font_size'])
		#Loop through until the text is between 80% of the height and 94%, or
		#until we get a number that is not a multiple of 4 (2,6,10,14, etc) to
		#make it simpler... TODO Double check that it doesn't overflow
		while True:
			if layout.get_pixel_size()[0] > bounds[0]*0.97 \
					or layout.get_pixel_size()[1] > bounds[1]*0.94:
				max_sz = size
				size = (min_sz + max_sz) / 2
			elif size % 4 != 0 or max_sz - min_sz < 3:
				break
			elif layout.get_pixel_size()[1] < bounds[1]*0.78:
				min_sz = size
				if(max_sz):
					size = (min_sz + max_sz) / 2
				else:
					size = size * 2
			else:
				break
			attrs.insert(pango.AttrFontDesc(pango.FontDescription("Sans Bold "+str(size)),
				end_index = len(self.text)))
			layout.set_attributes(attrs)
		
		self._set_background(widget)
		if prefs.config['pres.text_shadow']:
			shcol = c2dec(prefs.config['pres.text_shadow'])
			ccontext.set_source_rgba(shcol[0], shcol[1], shcol[2], shcol[3])
			ccontext.move_to(bounds[0] * 0.03 + size*0.1,
					(bounds[1] - layout.get_pixel_size()[1])/2.0 + size*0.1)
			ccontext.show_layout(layout)
		txcol = c2dec(prefs.config['pres.text_color'])
		ccontext.set_source_rgba(txcol[0], txcol[1], txcol[2], 1.0)
		ccontext.move_to(bounds[0] * 0.03,(bounds[1] - layout.get_pixel_size()[1])/2.0)
		ccontext.show_layout(layout)
		return True

