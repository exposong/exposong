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
import gtk.gdk
from xml.dom import minidom
import imp					#to dynamically load type modules
import os
from os.path import join

from exposong import RESOURCE_PATH, DATA_PATH, SHARED_FILES
from exposong import prefs, screen, preslist, schedlist, slidelist
from exposong.about import About
from exposong.schedule import Schedule # ? where to put library
import exposong.plugins, exposong.plugins._abstract

main = None

DRAGDROP_SCHEDULE = [("text/treeview-path", 0,0)]


class Main (gtk.Window):
	'''
	Primary user interface.
	'''
	def __init__(self):
		#define this instance in the global scope
		global main
		main = self
		
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		gtk.window_set_default_icon_list(
				gtk.gdk.pixbuf_new_from_file(join(RESOURCE_PATH, 'es128.png')),
				gtk.gdk.pixbuf_new_from_file(join(RESOURCE_PATH, 'es64.png')),
				gtk.gdk.pixbuf_new_from_file(join(RESOURCE_PATH, 'es48.png')),
				gtk.gdk.pixbuf_new_from_file(join(RESOURCE_PATH, 'es32.png')),
				gtk.gdk.pixbuf_new_from_file(join(RESOURCE_PATH, 'es16.png')))
		self.set_title( "ExpoSong" )
		self.connect("destroy", self._quit)
		self.set_default_size(700, 500)
		
		#dynamically load plugins
		exposong.plugins.load_plugins()
		
		
		##	GUI
		win_v = gtk.VBox()
		
		#These have to be initialized for the menus to render properly
		pres_prev = gtk.DrawingArea()
		screen.screen = screen.Screen(pres_prev)
		screen.screen.auto_locate(self)
		
		schedlist.schedlist = schedlist.ScheduleList()
		preslist.preslist = preslist.PresList()
		slidelist.slidelist = slidelist.SlideList()
		
		menu = self._create_menu()
		win_v.pack_start(menu, False)
		
		## Main Window Area
		win_h = gtk.HPaned()
		### Main left area
		win_lft = gtk.VPaned()
		#### Schedule
		schedlist.schedlist.connect("cursor-changed", schedlist.schedlist._on_schedule_activate)
		schedlist.schedlist.connect("button-release-event", self._on_schedule_rt_click)
		schedule_scroll = gtk.ScrolledWindow()
		schedule_scroll.add(schedlist.schedlist)
		schedule_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		win_lft.pack1(schedule_scroll, True, True)
		
		#### Presentation List
		preslist.preslist.connect("cursor-changed", preslist.preslist._on_pres_activate)
		preslist.preslist.connect("button-release-event", self._on_pres_rt_click)
		pres_list_scroll = gtk.ScrolledWindow()
		pres_list_scroll.add(preslist.preslist)
		pres_list_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		win_lft.pack2(pres_list_scroll, True, True)
		
		#Drag and Drop
		preslist.preslist.enable_model_drag_source(gtk.gdk.BUTTON1_MASK,
				DRAGDROP_SCHEDULE, gtk.gdk.ACTION_COPY)
		preslist.preslist.connect("drag-data-get", preslist.preslist._on_drag_get)
		preslist.preslist.connect("drag-data-received", preslist.preslist._on_pres_drag_received)
		schedlist.schedlist.enable_model_drag_dest(DRAGDROP_SCHEDULE, gtk.gdk.ACTION_DEFAULT)
		schedlist.schedlist.connect("drag-drop", schedlist.schedlist._on_pres_drop)
		schedlist.schedlist.connect("drag-data-received", schedlist.schedlist._on_sched_drag_received)
		schedlist.schedlist.set_drag_dest_row((1,), gtk.TREE_VIEW_DROP_INTO_OR_BEFORE)
		
		win_h.pack1(win_lft, False, False)
		
		### Main right area
		win_rt = gtk.VBox()
		#### Slide List
		slidelist.slidelist.connect("cursor-changed", slidelist.slidelist._on_slide_activate)
		slide_scroll = gtk.ScrolledWindow()
		slide_scroll.add(slidelist.slidelist)
		slide_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		win_rt.pack_start(slide_scroll)
		
		#### Preview and Presentation Buttons
		win_rt_btm = gtk.HBox()
		win_rt_btm.pack_start(pres_prev, True, False, 10)
		
		pres_buttons = gtk.VButtonBox()
		self.pbut_present = gtk.Button( _("Present") )
		self.action_group.get_action('Present').connect_proxy(self.pbut_present)
		pres_buttons.add(self.pbut_present)
		self.pbut_background = gtk.Button( _("Background") )
		self.action_group.get_action('Background').connect_proxy(self.pbut_background)
		pres_buttons.add(self.pbut_background)
		self.pbut_black = gtk.Button( _("Black Screen") )
		self.action_group.get_action('Black Screen').connect_proxy(self.pbut_black)
		pres_buttons.add(self.pbut_black)
		self.pbut_hide = gtk.Button( _("Hide") )
		self.action_group.get_action('Hide').connect_proxy(self.pbut_hide)
		pres_buttons.add(self.pbut_hide)
		
		win_rt_btm.pack_end(pres_buttons, False, False, 10)
		win_rt.pack_start(win_rt_btm, False, True)
		win_h.pack2(win_rt, True, False)
		win_v.pack_start(win_h, True)
		
		## Status bar
		self.status_bar = gtk.Statusbar()
		win_v.pack_end(self.status_bar, False)
		
		self.build_schedule()
		
		self.add(win_v)
		self.show_all()
	
	def _create_menu(self):
		'Set up the menus and popup menus.'
		uimanager = gtk.UIManager()
		self.add_accel_group(uimanager.get_accel_group())
		
		self.action_group = gtk.ActionGroup('exposong')
		self.action_group.add_actions([('File', None, _('_File') ),
				('Edit', None, _('_Edit') ),
				('Schedule', None, _("_Schedule") ),
				('Presentation', None, _('P_resentation')),
				('Help', None, _('_Help')),
				('Quit', gtk.STOCK_QUIT, None, None, None, self._quit),
				('Preferences', gtk.STOCK_PREFERENCES, None, None, None, self._on_prefs),
				('sched-new', gtk.STOCK_NEW, None, None, _("Create a new schedule"),
						schedlist.schedlist._on_new),
				('sched-rename', None, _("_Rename"), None,
						_("Rename the selected schedule"), schedlist.schedlist._on_rename),
				('sched-delete', gtk.STOCK_DELETE, None, None,
						_("Delete the currently selected schedule"),
						schedlist.schedlist._on_sched_delete ),
				('pres-new', gtk.STOCK_NEW, None, "", _("Create a new presentation")),
				('pres-edit', gtk.STOCK_EDIT, None, None,
						_("Edit the currently selected presentation"),
						preslist.preslist._on_pres_edit),
				('pres-delete', gtk.STOCK_DELETE, None, None,
						_("Delete the presentation"), self._on_pres_delete),
				('pres-delete-from-schedule', gtk.STOCK_DELETE,
						_("Delete from _Schedule"), None, None,
						preslist.preslist._on_pres_delete_from_schedule),
				('pres-import', None, _("_Import"), None,
						_("Open a presentation from file")),
				('pres-export', None, _("_Export"), None,
						_("Export presentation")),
				('Present', gtk.STOCK_FULLSCREEN, _('_Present'), "<Alt>p", None,
						screen.screen.show),
				('Background', gtk.STOCK_CLEAR, _('_Background'), "<Alt>b", None,
						screen.screen.to_background),
				('Black Screen', None, _('Blac_k Screen'), "<Alt>k", None,
						screen.screen.to_black),
				('Hide', gtk.STOCK_CLOSE, _('Hi_de'), "<Alt>d", None,
						screen.screen.hide),
				('HelpContents', gtk.STOCK_HELP),
				('About', gtk.STOCK_ABOUT, None, None, None, self._on_about)])
		uimanager.insert_action_group(self.action_group, 0)
		uimanager.add_ui_from_string('''
				<menubar name="MenuBar">
					<menu action="File">
						<menuitem action="Quit" />
					</menu>
					<menu action="Edit">
						<menuitem action="Preferences" />
					</menu>
					<menu action="Schedule">
						<menu action='sched-new'></menu>
						<menuitem action='sched-rename' />
						<menuitem action='sched-delete' />
					</menu>
					<menu action="Presentation">
						<menu action="pres-new"></menu>
						<menuitem action="pres-edit" />
						<menuitem action="pres-delete" />
						<menuitem action="pres-delete-from-schedule" />
						<!--<menuitem action="pres-import" />
						<menuitem action="pres-export" />-->
						<separator />
						<menuitem action="Present" />
						<menuitem action="Background" />
						<menuitem action="Black Screen" />
						<menuitem action="Hide" />
					</menu>
					<menu action="Help">
						<menuitem action="HelpContents" />
						<menuitem action="About" />
					</menu>
				</menubar>''')
		
		for mod in exposong.plugins.get_plugins_by_capability(exposong.plugins._abstract.Menu):
			mod().merge_menu(uimanager)
		
		menu = uimanager.get_widget('/MenuBar')
		self.pres_list_menu = gtk.Menu()
		self.pres_list_menu.append(self.action_group
				.get_action('pres-edit').create_menu_item())
		self.pres_list_menu.append(self.action_group
				.get_action('pres-delete').create_menu_item())
		self.pres_list_menu.show_all()
		
		self.pres_list_sched_menu = gtk.Menu() #Custom schedule menu
		self.pres_list_sched_menu.append(self.action_group
				.get_action('pres-edit').create_menu_item())
		self.pres_list_sched_menu.append(self.action_group
				.get_action('pres-delete-from-schedule').create_menu_item())
		self.pres_list_sched_menu.show_all()
		
		self.sched_list_menu = gtk.Menu()
		self.sched_list_menu.append(self.action_group
				.get_action('sched-rename').create_menu_item())
		self.sched_list_menu.append(self.action_group
				.get_action('sched-delete').create_menu_item())
		self.sched_list_menu.show_all()
		
		return menu
	
	def build_pres_list(self):
		'Load presentations and add them to self.library.'
		directory = join(DATA_PATH, "pres")
		'Add items to the presentation list.'
		dir_list = os.listdir(directory)
		for filenm in dir_list:
			if filenm.endswith(".xml"):
				try:
					dom = minidom.parse(join(directory,filenm))
				except Exception, details:
					print "Error reading presentation file (%s): %s" % (filenm, details)
				if dom:
					root_elem = dom.documentElement
					if root_elem.tagName == "presentation" and root_elem.hasAttribute("type"):
						filetype = root_elem.getAttribute("type")
						plugins = exposong.plugins.get_plugins_by_capability(exposong.plugins._abstract.Presentation)
						for plugin in plugins:
							if str(filetype) == plugin.get_type():
								pres = plugin(dom.documentElement, filenm)
								self.library.append(pres)
								break
					else:
						print "%s is not a presentation file." % filenm
					dom.unlink()
					del dom
	
	def build_schedule(self):
		'Add builtin lists to the schedule, and load all custom lists.'
		directory = join(DATA_PATH, "sched")
		'Add items to the schedule list.'
		self.library = Schedule( _("Library"))
		self.build_pres_list()
		schedlist.schedlist.append(None, self.library, 1)
		
		#Add the presentation type schedules
		
		#Add custom schedules from the data directory
		schedlist.schedlist.custom_schedules = schedlist.schedlist.append(None,
				(None, _("Custom Schedules"), 40))
		
		dir_list = os.listdir(directory)
		for filenm in dir_list:
			if filenm.endswith(".xml"):
				dom = None
				try:
					dom = minidom.parse(directory+"/"+filenm)
				except Exception, details:
					print "Error reading schedule file (%s): %s" % (filenm, details)
				if dom:
					if dom.documentElement.tagName == "schedule":
						schedule = Schedule(filename=filenm)
						schedule.load(dom.documentElement, self.library)
						schedlist.schedlist.append(schedlist.schedlist.custom_schedules, schedule)
					else:
						print "%s is not a schedule file." % filenm
					dom.unlink()
					del dom
		schedlist.schedlist.expand_all()
	
	def _on_pres_rt_click(self, widget, event):
		'The user right clicked in the presentation list area.'
		if event.button == 3:
			path = preslist.preslist.get_path_at_pos(int(event.x), int(event.y))
			if path is not None:
				if preslist.preslist.get_model().builtin:
					menu = self.pres_list_menu
				else:
					menu = self.pres_list_sched_menu
				menu.popup(None, None, None, event.button, event.get_time())
	
	def _on_schedule_rt_click(self, widget, event):
		'The user right clicked in the schedule area.'
		if event.button == 3:
			if widget.get_active_item() and not widget.get_active_item().builtin:
				self.sched_list_menu.popup(None, None, None, event.button, event.get_time())
	
	def _on_pres_delete(self, *args):
		'Delete the selected presentation.'
		item = preslist.preslist.get_active_item()
		if not item:
			return False
		dialog = gtk.MessageDialog(self, gtk.DIALOG_MODAL,
				gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
				_('Are you sure you want to delete "%s" from your library?') % item.title)
		dialog.set_title( _("Delete Presentation?") )
		resp = dialog.run()
		dialog.hide()
		if resp == gtk.RESPONSE_YES:
			schmod = schedlist.schedlist.get_model()
			
			#Remove from builtin modules
			itr = schmod.get_iter_first()
			while itr:
				sched = schmod.get_value(itr, 0)
				if sched:
					sched.remove_if(presentation=item.presentation)
				itr = schmod.iter_next(itr)
			
			#Remove from custom schedules
			itr = schmod.iter_children(schedlist.schedlist.custom_schedules)
			while itr:
				sched = schmod.get_value(itr, 0)
				sched.remove_if(presentation=item.presentation)
				itr = schmod.iter_next(itr)
			os.remove(join(DATA_PATH,"pres",item.filename))
			preslist.preslist._on_pres_activate()
	
	def _on_about(self, *args):
		'Shows the about dialog.'
		About(self)
	
	def _on_prefs(self, *args):
		'Shows the preferences dialog.'
		prefs.config.dialog(self)
	
	def _quit(self, *args):
		'Cleans up and exits the program.'
		model = schedlist.schedlist.get_model()
		sched = model.iter_children(schedlist.schedlist.custom_schedules)
		while sched:
			model.get_value(sched, 0).save()
			sched = model.iter_next(sched)
		
		gtk.main_quit()


def run():
	Main()
	gtk.main()

