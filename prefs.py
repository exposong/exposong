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
import pygtk
import gtk
import gtk.gdk
import imp

class Prefs:
	def __init__(self):
		self.cfg = {'general.ccli': '',
				'pres.max_font_size': 56,
				'pres.bg': ((0.0, 0.2, 0.3), (0.0, 0.4, 0.6)),
				'pres.text_color': (1.0, 1.0, 1.0),
				'pres.text_shadow': (0.0, 0.0, 0.0, 0.4)}
		self.load()
	def __getitem__(self, key):
		if key in self.cfg:
			return self.cfg[key]
		raise KeyError, 'Could not find key: '+key
	def __setitem__(self, key, value):
		if value == None:
			self.__delitem__(key, value)
		else:
			self.cfg[key] = value
	def __delitem__(self, key):
		del self.cfg[key]
	
	def load(self):
		try:
			config = imp.load_source('config', 'config.py')
		except IOError:
			return False
		for k,v in self.cfg.iteritems():
			ksp = k.split(".")
			if hasattr(config, ksp[0]) and hasattr(getattr(config, ksp[0]), ksp[1]):
				self.cfg[k] = getattr(getattr(config, ksp[0]), ksp[1])
			
	def save(self):
		cfile = open('config.py', 'r+')
		cnt = 0
		for line in cfile:
			cnt += len(line)
			if line.startswith('# @START_WRITE'):
				break
		cfile.seek(cnt)
		cfile.write("\n\n")
		cnt += 1
		
		for key, value in self.cfg.iteritems():
			ln = key+' = '+repr(value)+'\n'
			cfile.write(ln)
			cnt += len(ln)
		
		cfile.truncate(cnt)
		cfile.close()
	
	def dialog(self, parent):
		if(PrefsDialog(parent, self)):
			self.save()
			parent.presentation.draw()

class PrefsDialog(gtk.Dialog):
	def __init__(self, parent, config):
		self.widgets = {}
		gtk.Dialog.__init__(self, "Preferences", parent, 0,
				(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
		notebook = gtk.Notebook()
		self.vbox.pack_start(notebook, True, True, 5)
		
		#General Page
		general = gtk.VBox()
		general.set_spacing(10)
		general.set_border_width(10)
		
		general.pack_start(self.section_title("Legal"), False, False, 0)
		general.pack_start(self.text_pref("CCLI #", config['general.ccli'], name='ccli'), False, False, 0)
		
		notebook.append_page(general, gtk.Label("General"))
		
		#Presentation Page
		presentation = gtk.VBox()
		presentation.set_spacing(10)
		presentation.set_border_width(10)
		
		presentation.pack_start(self.section_title("Background"), False, False, 0)
		presentation.pack_start(self.color_pref("Gradiant Top-Left", config['pres.bg'][0], name='bg_tlf'), False, False, 0)
		presentation.pack_start(self.color_pref("Gradiant Bottom-Right", config['pres.bg'][1], name='bg_brt'), False, False, 0)
		presentation.pack_start(self.section_title("Font"), False, False, 0)
		presentation.pack_start(self.color_pref("Text Color", config['pres.text_color'], name='txt_color'), False, False, 0)
		presentation.pack_start(self.color_pref("Text Shadow", config['pres.text_shadow'], True, name='txt_shadow'), False, False, 0)
		presentation.pack_start(self.spinner_pref("Max Font Size", config['pres.max_font_size'], name='max_font'), False, False, 0)
		
		notebook.append_page(presentation, gtk.Label("Presentation"))
		
		self.show_all()
		if(self.run() == gtk.RESPONSE_ACCEPT):
			tlf = self.widgets['bg_tlf'].get_color()
			brt = self.widgets['bg_brt'].get_color()
			config['pres.bg'] = ((tlf.red/65535.0, tlf.green/65535.0, tlf.blue/65535.0),
					(brt.red/65535.0, brt.green/65535.0, brt.blue/65535.0))
			txtc = self.widgets['txt_color'].get_color()
			config['pres.text_color'] = (txtc.red/65535.0, txtc.green/65535.0, txtc.blue/65535.0)
			txts = self.widgets['txt_shadow'].get_color()
			config['pres.text_shadow'] = (txts.red/65535.0, txts.green/65535.0, txts.blue/65535.0, self.widgets['txt_shadow'].get_alpha()/65535.0)
			config['pres.max_font_size'] = self.widgets['max_font'].get_value()
			config['general.ccli'] = self.widgets['ccli'].get_text()
			
			config.save()
		
		self.hide()
	
	def section_title(self, title):
		hbox = gtk.HBox()
		label = gtk.Label()
		label.set_markup("<b>"+title+"</b>")
		hbox.pack_start(label, False, False, 0)
		return hbox
	
	def text_pref(self, title, value, name=None):
		hbox = gtk.HBox()
		label = gtk.Label(title)
		hbox.pack_start(label, False, False, 10)
		
		entry = gtk.Entry(10)
		entry.set_text(value)
		hbox.pack_start(entry, False, False, 10)
		if(name):
			self.widgets[name] = entry
		return hbox
	
	def color_pref(self, title, value, alpha=False, name=None):
		hbox = gtk.HBox()
		label = gtk.Label(title)
		hbox.pack_start(label, False, False, 10)
		
		button = gtk.ColorButton(gtk.gdk.Color(int(value[0]*65535), int(value[1]*65535), int(value[2]*65535)))
		if(alpha):
			button.set_alpha(int(value[3]*65535))
			button.set_use_alpha(True)
		hbox.pack_start(button, False, False, 10)
		if(name):
			self.widgets[name] = button
		return hbox
	
	def spinner_pref(self, title, value, name=None):
		hbox = gtk.HBox()
		label = gtk.Label(title)
		hbox.pack_start(label, False, False, 5)
		
		spinner = gtk.SpinButton(gtk.Adjustment(value, 0, 96, 1), 2.0, 0)
		hbox.pack_start(spinner, False, False, 5)
		if(name):
			self.widgets[name] = spinner
		return hbox


