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
pygtk.require("2.0")
import gtk
import gtk.gdk
from xml.dom import minidom
import imp					#to dynamically load type modules
import os

from presentation import Presentation
from preslist import PresList
from slidelist import SlideList
from about import About
from prefs import Prefs
from prefs import PrefsDialog

type_mods = {} #dynamically loaded presentation modules

menu = '''<menubar name="MenuBar">
	<menu action="File">
		<menuitem action="Quit" />
	</menu>
	<menu action="Edit">
		<menuitem action="Preferences" />
	</menu>
	<menu action="Presentation">
		<menuitem action="Present" />
		<menuitem action="Background" />
		<menuitem action="Black Screen" />
		<menuitem action="Hide" />
		<separator />
		<menuitem action="pres-new" />
		<menuitem action="pres-edit" />
		<menuitem action="pres-delete" />
		<menuitem action="pres-import" />
		<menuitem action="pres-export" />
	</menu>
	<menu action="Help">
		<menuitem action="HelpContents" />
		<menuitem action="About" />
	</menu>
</menubar>'''

class Main (gtk.Window):
	'''Primary user interface'''
	
	def __init__(self):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		gtk.window_set_default_icon_list(gtk.gdk.pixbuf_new_from_file('images/es128.png'),
				gtk.gdk.pixbuf_new_from_file('images/es64.png'),
				gtk.gdk.pixbuf_new_from_file('images/es48.png'),
				gtk.gdk.pixbuf_new_from_file('images/es32.png'),
				gtk.gdk.pixbuf_new_from_file('images/es16.png'))
		self.set_title("ExpoSong")
		self.connect("destroy", gtk.main_quit)
		self.set_default_size(700, 500)
		self.config = Prefs()
		
		#dynamically load all presentation types
		for fl in os.listdir("ptype"):
			if fl.endswith(".py") and fl != "__init__.py":
				type_mods[fl[:-3]] = imp.load_source(fl[:-3], 'ptype/'+fl)
		
		##	GUI
		win_v = gtk.VBox()
		
		#These have to be initialized for the menus to render properly
		pres_geom = self.get_pres_geometry()
		self.pres_prev = gtk.DrawingArea()
		self.pres_prev.set_size_request(135*pres_geom[2]/pres_geom[3], 135) # TODO set according to pres_window size
		self.presentation = Presentation(self, pres_geom, self.pres_prev)
		
		## Menu
		uimanager = gtk.UIManager()
		self.add_accel_group(uimanager.get_accel_group())
		
		actiongroup = gtk.ActionGroup('presenter')
		actiongroup.add_actions([('File', None, '_File'),
								('Quit', gtk.STOCK_QUIT, None, None, None, gtk.main_quit),
								('Edit', None, '_Edit'),
								('Preferences', gtk.STOCK_PREFERENCES, None, None, None, self.on_prefs),
								('Presentation', None, '_Presentation'),
								('Present', None, '_Present', None, None, self.presentation.show),
								('Background', None, '_Background', None, None, self.presentation.to_background),
								('Black Screen', None, 'Blac_k Screen', None, None, self.presentation.to_black),
								('Hide', None, '_Hide', None, None, self.presentation.hide),
								('pres-new', gtk.STOCK_NEW, None, None, "New presentation"),
								('pres-edit', gtk.STOCK_EDIT, None, None, "Edit presentation", self.on_pres_edit),
								('pres-delete', gtk.STOCK_DELETE, None, None, "Delete the presentation", self.on_pres_delete),
								('pres-import', None, "_Import", None, "Open a presentation from file"),
								('pres-export', None, "_Export", None, "Export presentation"),
								#('Playlist', None, '_Playlist'),
								('Help', None, '_Help'),
								('HelpContents', gtk.STOCK_HELP),
								('About', gtk.STOCK_ABOUT, None, None, None, self.on_about)])
		uimanager.insert_action_group(actiongroup, 0)
		uimanager.add_ui_from_string(menu)
		
		self.menu = uimanager.get_widget('/MenuBar')
		win_v.pack_start(self.menu, False)
		self.pres_list_menu = gtk.Menu()
		self.pres_list_menu.append(actiongroup.get_action('pres-edit').create_menu_item())
		self.pres_list_menu.append(actiongroup.get_action('pres-delete').create_menu_item())
		self.pres_list_menu.show_all()
		
		self.pres_new_submenu = gtk.Menu()
		for (ptype, mod) in type_mods.items():
			mitem = gtk.MenuItem(mod.menu_name)
			mitem.connect("activate", self.on_pres_new, ptype)
			self.pres_new_submenu.append(mitem)
		
		self.pres_new_submenu.show_all()
		uimanager.get_widget('/MenuBar/Presentation/pres-new').set_submenu(self.pres_new_submenu)
		
		
		## Main Window Area
		win_h = gtk.HPaned()
		### Main left area
		win_lft = gtk.VPaned()
		#### Playlist   TODO Toolbar
		#playlist_tb = gtk.Toolbar()
		#self.playlist = gtk.TreeView()
		#self.playlist.set_size_request(150, 140)
		#playlist_scroll = gtk.ScrolledWindow()
		#playlist_scroll.add(self.playlist)
		#playlist_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		#win_lft_vb1 = gtk.VBox()
		#win_lft_vb1.pack_start(playlist_tb, False, True, 0)
		#win_lft_vb1.pack_start(playlist_scroll, True, True, 0)
		#win_lft.pack1(win_lft_vb1, True, True)
		
		#### Presentation List
		#pres_list_tb = uimanager.get_widget('/Preslist')
		#pres_list_tb.set_tooltips(True)
		#pres_list_tb.set_style(gtk.TOOLBAR_ICONS)
		#pres_list_tb.set_icon_size(gtk.ICON_SIZE_MENU)
		#win_lft_vb2.pack_start(pres_list_tb, False, True)
		self.pres_list = PresList()
		self.pres_list.connect("row-activated", self.on_pres_activate)
		self.pres_list.connect("button-press-event", self.on_pres_rt_click)
		self.build_pres_list()
		pres_list_scroll = gtk.ScrolledWindow()
		pres_list_scroll.add(self.pres_list)
		pres_list_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		win_lft_vb2 = gtk.VBox()
		win_lft_vb2.pack_start(pres_list_scroll, True, True)
		#win_lft.pack2(win_lft_vb2, True, True)
		
		
		#win_h.pack1(win_lft, False, False)
		win_h.pack1(win_lft_vb2, False, False)
		
		### Main right area
		win_rt = gtk.VBox()
		#### Slide List
		slide_list = gtk.TreeView()
		slide_list.connect("cursor-changed", self.on_slide_activate)
		self.slide_list = SlideList(slide_list)
		text_scroll = gtk.ScrolledWindow()
		text_scroll.add(slide_list)
		text_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		win_rt.pack_start(text_scroll)
		
		#### Preview and Presentation Buttons
		win_rt_btm = gtk.HBox()
		win_rt_btm.pack_start(self.pres_prev, True, False, 10)
		
		pres_buttons = gtk.VButtonBox()
		self.pbut_present = gtk.Button("Present")
		actiongroup.get_action('Present').connect_proxy(self.pbut_present)
		#self.pbut_present.connect("clicked", self.presentation.show)
		pres_buttons.add(self.pbut_present)
		self.pbut_background = gtk.Button("Background")
		actiongroup.get_action('Background').connect_proxy(self.pbut_background)
		#self.pbut_background.connect("clicked", self.presentation.to_background)
		pres_buttons.add(self.pbut_background)
		self.pbut_black = gtk.Button("Black Screen")
		actiongroup.get_action('Black Screen').connect_proxy(self.pbut_black)
		#self.pbut_black.connect("clicked", self.presentation.to_black)
		pres_buttons.add(self.pbut_black)
		self.pbut_hide = gtk.Button("Hide")
		actiongroup.get_action('Hide').connect_proxy(self.pbut_hide)
		#self.pbut_hide.connect("clicked", self.presentation.hide)
		pres_buttons.add(self.pbut_hide)
		
		win_rt_btm.pack_end(pres_buttons, False, False, 10)
		
		win_rt.pack_start(win_rt_btm, False, True)
		
		win_h.pack2(win_rt, True, False)
		
		win_v.pack_start(win_h, True)
		
		## Status bar
		self.status_bar = gtk.Statusbar()
		
		win_v.pack_end(self.status_bar, False)
		self.add(win_v)
		self.show_all()
	
	def get_pres_geometry(self):
		'''Finds the best location for the screen.
		
		If the user is using one monitor, use the bottom right corner for
		the presentation screen, otherwise, use the 2nd monitor.'''
		screen = self.get_screen()
		num_monitors = screen.get_n_monitors()
		if(num_monitors > 1):
			scr_geom = screen.get_monitor_geometry(1)
			return (scr_geom.x, scr_geom.y, scr_geom.width, scr_geom.height)
		else:
			# No 2nd monitor, so preview it small in the corner of the screen
			scr_geom = screen.get_monitor_geometry(0)
			self.move(0,0)
			return (scr_geom.width/2, scr_geom.height/2, scr_geom.width/2, scr_geom.height/2)
	
	def build_pres_list(self, directory="data/pres"):
		dir_list = os.listdir(directory)
		for filenm in dir_list:
			if filenm.endswith(".xml"):
				try:
					dom = minidom.parse(directory+"/"+filenm)
				except Exception, details:
					print "Error reading xml file:", details
				if dom:
					root_elem = dom.documentElement
					if root_elem.tagName == "presentation" and root_elem.hasAttribute("type"):
						filetype = root_elem.getAttribute("type")
						if filetype in type_mods:
							obj = type_mods[filetype].Presentation(dom.documentElement, filenm)
							self.pres_list.append(obj)
							obj = None
					dom.unlink()
					del dom
	
	def on_pres_activate(self, *args):
		if(self.pres_list.has_selection()):
			self.slide_list.set_slides(self.pres_list.get_active_item().slides)
		else:
			self.slide_list.set_slides([])
	def on_pres_rt_click(self, widget, event):
		if(event.button == 3):
			self.pres_list_menu.popup(None, None, None, event.button, event.get_time())
	def on_slide_activate(self, *args):
		self.presentation.set_text(self.slide_list.get_active_item().get_text())
	def on_pres_new(self, menuitem, ptype):
		pres = type_mods[ptype].Presentation()
		if(pres.edit(self)):
			self.pres_list.append(pres)
	def on_pres_edit(self, *args):
		field = self.pres_list.get_active_item()
		if(field):
			if(field.edit(self)):
				self.pres_list.update_selected()
				self.on_pres_activate()
	def on_pres_delete(self, *args):
		item = self.pres_list.get_active_item()
		dialog = gtk.MessageDialog(self, gtk.DIALOG_MODAL,
				gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
				"Are you sure you want to delete "+item.title+"?")
		resp = dialog.run()
		dialog.hide()
		if resp == gtk.RESPONSE_YES:
			os.remove("data/"+item.filename)
			self.pres_list.remove(item)
			self.on_pres_activate()
	
	def on_about(self, *args):
		About(self)
	def on_prefs(self, *args):
		self.config.dialog(self)

if __name__ == "__main__":
	m = Main()
	gtk.main()

