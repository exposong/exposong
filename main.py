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

import gettext
import __builtin__
__builtin__._ = gettext.gettext

from presentation import Presentation
from preslist import PresList
from slidelist import SlideList
from about import About
import prefs
from schedule import Schedule
from schedlist import ScheduleList


type_mods = {} #dynamically loaded presentation modules

DRAGDROP_SCHEDULE = [("text/treeview-path", 0,0)]


class Main (gtk.Window):
	'''Primary user interface'''
	
	def __init__(self):
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		gtk.window_set_default_icon_list(gtk.gdk.pixbuf_new_from_file('images/es128.png'),
				gtk.gdk.pixbuf_new_from_file('images/es64.png'),
				gtk.gdk.pixbuf_new_from_file('images/es48.png'),
				gtk.gdk.pixbuf_new_from_file('images/es32.png'),
				gtk.gdk.pixbuf_new_from_file('images/es16.png'))
		self.set_title( "ExpoSong" )
		self.connect("destroy", self._quit)
		self.set_default_size(700, 500)
		self.config = prefs.Prefs()
		
		#dynamically load all presentation types
		for fl in os.listdir("ptype"):
			if fl.endswith(".py") and fl != "__init__.py":
				type_mods[fl[:-3]] = imp.load_source(fl[:-3], 'ptype/'+fl)
		
		##	GUI
		win_v = gtk.VBox()
		
		#These have to be initialized for the menus to render properly
		pres_geom = self.get_pres_geometry()
		self.pres_prev = gtk.DrawingArea()
		self.pres_prev.set_size_request(135*pres_geom[2]/pres_geom[3], 135)
		self.presentation = Presentation(self, pres_geom, self.pres_prev)
		self.schedule_list = ScheduleList()
		
		menu = self._create_menu()
		win_v.pack_start(menu, False)
		
		## Main Window Area
		win_h = gtk.HPaned()
		### Main left area
		win_lft = gtk.VPaned()
		#### Schedule
		self.schedule_list.connect("cursor-changed", self._on_schedule_activate)
		self.schedule_list.connect("button-release-event", self._on_schedule_rt_click)
		schedule_scroll = gtk.ScrolledWindow()
		schedule_scroll.add(self.schedule_list)
		schedule_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		win_lft.pack1(schedule_scroll, True, True)
		
		#### Presentation List
		self.pres_list = PresList()
		self.pres_list.connect("cursor-changed", self._on_pres_activate)
		self.pres_list.connect("button-release-event", self._on_pres_rt_click)
		pres_list_scroll = gtk.ScrolledWindow()
		pres_list_scroll.add(self.pres_list)
		pres_list_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		win_lft.pack2(pres_list_scroll, True, True)
		
		#Drag and Drop
		self.pres_list.enable_model_drag_source(gtk.gdk.BUTTON1_MASK, DRAGDROP_SCHEDULE, gtk.gdk.ACTION_COPY)
		self.pres_list.connect("drag-data-get", self.pres_list._on_drag_get)
		self.pres_list.connect("drag-data-received", self._on_pres_drag_received)
		self.schedule_list.enable_model_drag_dest(DRAGDROP_SCHEDULE, gtk.gdk.ACTION_DEFAULT)
		self.schedule_list.connect("drag-drop", self.schedule_list._on_pres_drop)
		self.schedule_list.connect("drag-data-received", self._on_sched_drag_received)
		self.schedule_list.set_drag_dest_row((1,), gtk.TREE_VIEW_DROP_INTO_OR_BEFORE)
		
		win_h.pack1(win_lft, False, False)
		
		### Main right area
		win_rt = gtk.VBox()
		#### Slide List
		self.slide_list = SlideList()
		self.slide_list.connect("cursor-changed", self._on_slide_activate)
		slide_scroll = gtk.ScrolledWindow()
		slide_scroll.add(self.slide_list)
		slide_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
		win_rt.pack_start(slide_scroll)
		
		#### Preview and Presentation Buttons
		win_rt_btm = gtk.HBox()
		win_rt_btm.pack_start(self.pres_prev, True, False, 10)
		
		pres_buttons = gtk.VButtonBox()
		self.pbut_present = gtk.Button( _("Present") )
		self.action_group.get_action('Present').connect_proxy(self.pbut_present)
		#self.pbut_present.connect("clicked", self.presentation.show)
		pres_buttons.add(self.pbut_present)
		self.pbut_background = gtk.Button( _("Background") )
		self.action_group.get_action('Background').connect_proxy(self.pbut_background)
		#self.pbut_background.connect("clicked", self.presentation.to_background)
		pres_buttons.add(self.pbut_background)
		self.pbut_black = gtk.Button( _("Black Screen") )
		self.action_group.get_action('Black Screen').connect_proxy(self.pbut_black)
		#self.pbut_black.connect("clicked", self.presentation.to_black)
		pres_buttons.add(self.pbut_black)
		self.pbut_hide = gtk.Button( _("Hide") )
		self.action_group.get_action('Hide').connect_proxy(self.pbut_hide)
		#self.pbut_hide.connect("clicked", self.presentation.hide)
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
		
		self.action_group = gtk.ActionGroup('presenter')
		self.action_group.add_actions([('File', None, _('_File') ),
								('Quit', gtk.STOCK_QUIT, None, None, None, self._quit),
								('Edit', None, _('_Edit') ),
								('Preferences', gtk.STOCK_PREFERENCES, None, None, None, self._on_prefs),
								('Schedule', None, _("_Schedule") ),
								('sched-new', gtk.STOCK_NEW, None, None, _("Create a new schedule"), self.schedule_list._on_new),
								('sched-rename', None, _("_Rename"), None, _("Rename the selected schedule"), self.schedule_list._on_rename),
								('sched-delete', gtk.STOCK_DELETE, None, None, _("Delete the currently selected schedule"), self.schedule_list._on_sched_delete ),
								('Presentation', None, '_Presentation'),
								('pres-new', gtk.STOCK_NEW, None, "", _("Create a new presentation")),
								('pres-edit', gtk.STOCK_EDIT, None, None, _("Edit the currently selected presentation"), self._on_pres_edit),
								('pres-delete', gtk.STOCK_DELETE, None, None, _("Delete the presentation"), self._on_pres_delete),
								('pres-delete-from-schedule', gtk.STOCK_DELETE, _("Delete from _Schedule"), None, None, self._on_pres_delete_from_schedule),
								('pres-import', None, _("_Import"), None, _("Open a presentation from file")),
								('pres-export', None, _("_Export"), None, _("Export presentation")),
								('Present', gtk.STOCK_FULLSCREEN, _('_Present'), "F11", None, self.presentation.show),
								('Background', gtk.STOCK_CLEAR, _('_Background'), None, None, self.presentation.to_background),
								('Black Screen', None, _('Blac_k Screen'), None, None, self.presentation.to_black),
								('Hide', gtk.STOCK_CLOSE, _('_Hide'), "Escape", None, self.presentation.hide),
								('Help', None, _('_Help')),
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
						<menuitem action='sched-new' />
						<menuitem action='sched-rename' />
						<menuitem action='sched-delete' />
					</menu>
					<menu action="Presentation">
						<menuitem action="pres-new" />
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
		
		menu = uimanager.get_widget('/MenuBar')
		self.pres_list_menu = gtk.Menu()
		self.pres_list_menu.append(self.action_group.get_action('pres-edit').create_menu_item())
		self.pres_list_menu.append(self.action_group.get_action('pres-delete').create_menu_item())
		self.pres_list_menu.show_all()
		
		self.pres_list_sched_menu = gtk.Menu() #Custom schedule menu
		self.pres_list_sched_menu.append(self.action_group.get_action('pres-edit').create_menu_item())
		self.pres_list_sched_menu.append(self.action_group.get_action('pres-delete-from-schedule').create_menu_item())
		self.pres_list_sched_menu.show_all()
		
		self.sched_list_menu = gtk.Menu()
		self.sched_list_menu.append(self.action_group.get_action('sched-rename').create_menu_item())
		self.sched_list_menu.append(self.action_group.get_action('sched-delete').create_menu_item())
		self.sched_list_menu.show_all()
		
		pres_new_submenu = gtk.Menu()
		for (ptype, mod) in type_mods.items():
			mitem = gtk.Action(mod.type_name, mod.menu_name, None, None)
			mitem.connect("activate", self._on_pres_new, ptype)
			self.action_group.add_action(mitem)
			if hasattr(mod, "icon"):
				mitem.set_menu_item_type(gtk.ImageMenuItem)
				mimg = gtk.Image()
				mimg.set_from_pixbuf(mod.icon)
				mitem = mitem.create_menu_item()
				mitem.set_image(mimg)
			else:
				mitem = mitem.create_menu_item()
			pres_new_submenu.append(mitem)
		
		pres_new_submenu.show_all()
		uimanager.get_widget('/MenuBar/Presentation/pres-new').set_submenu(pres_new_submenu)
		return menu
	
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
		'''Add items to the presentation list.'''
		dir_list = os.listdir(directory)
		for filenm in dir_list:
			if filenm.endswith(".xml"):
				try:
					dom = minidom.parse(directory+"/"+filenm)
				except Exception, details:
					print "Error reading presentation file (%s): %s" % (filenm, details)
				if dom:
					root_elem = dom.documentElement
					if root_elem.tagName == "presentation" and root_elem.hasAttribute("type"):
						filetype = root_elem.getAttribute("type")
						if filetype in type_mods:
							pres = type_mods[filetype].Presentation(dom.documentElement, filenm)
							self.library.append(pres)
					else:
						print "%s is not a presentation file." % filenm
					dom.unlink()
					del dom
	
	def build_schedule(self, directory="data/sched"):
		'''Add items to the schedule list.'''
		self.library = Schedule( _("Library"), pres_model=PresList.get_empty_model())
		self.build_pres_list()
		self.schedule_list.append(None, self.library, 1)
		
		#Add the presentation type lists
		i = 2
		for (ptype, mod) in type_mods.items():
			schedule = Schedule(mod.menu_name, pres_model=PresList.get_empty_model(), filter_type=ptype)
			for item in self.library.items:
				schedule.append(item.presentation)
			self.schedule_list.append(None, schedule, i)
			i += 1
		
		#Add custom schedules from the data directory
		self.schedule_list.custom_schedules = self.schedule_list.append(None, (None, _("Custom Schedules"), i+5))
		
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
						schedule = Schedule(filename=filenm, pres_model=PresList.get_empty_model())
						schedule.load(dom.documentElement, self.library)
						self.schedule_list.append(self.schedule_list.custom_schedules, schedule)
					else:
						print "%s is not a schedule file." % filenm
					dom.unlink()
					del dom
		self.schedule_list.expand_all()
	
	def _on_schedule_activate(self, *args):
		'''Change the presentation list to the current schedule.'''
		if self.schedule_list.has_selection():
			sched = self.schedule_list.get_active_item()
			if isinstance(sched, Schedule) and sched.get_model():
				self.pres_list.set_model(sched.get_model())
				if sched.is_reorderable():
					self.pres_list.enable_model_drag_dest(DRAGDROP_SCHEDULE, gtk.gdk.ACTION_COPY)
					self.pres_list.set_headers_clickable(False)
				else:
					self.pres_list.unset_rows_drag_dest()
					self.pres_list.set_headers_clickable(True)
	
	def _on_sched_drag_received(self, treeview, context, x, y, selection, info, timestamp):
		'''A presentation was dropped onto a schedule.'''
		drop_info = treeview.get_dest_row_at_pos(x, y)
		if drop_info:
			model = treeview.get_model()
			path, position = drop_info
			
			pres = self.pres_list.get_model().get_value(
					self.pres_list.get_model().get_iter_from_string(selection.data), 0).presentation
			sched = model.get_value(model.get_iter(path), 0)
			
			sched.append(pres)
			context.finish(True, False)
		return
	
	def _on_pres_drag_received(self, treeview, context, x, y, selection, info, timestamp):
		'A presentation was reordered.'
		drop_info = treeview.get_dest_row_at_pos(x, y)
		model = treeview.get_model()
		schedule = self.schedule_list.get_active_item()
		#currently requires the user not to change or unselect the schedule
		if not schedule or schedule.get_model() is not self.pres_list.get_model():
			return
		path_mv = int(selection.data)
		
		if drop_info:
			path_to, position = drop_info
			path_to = path_to[0]
			if path_mv > path_to and (position is gtk.TREE_VIEW_DROP_AFTER or position is gtk.TREE_VIEW_DROP_INTO_OR_AFTER):
				path_to += 1
			elif path_mv < path_to and (position is gtk.TREE_VIEW_DROP_BEFORE or position is gtk.TREE_VIEW_DROP_INTO_OR_BEFORE):
				path_to -= 1
		else:
			path_to = len(schedule.items)-1
		
		schedule.move(path_mv, path_to)
		
		context.finish(True, False)
		return
	
	def _on_pres_activate(self, *args):
		'''Change the slides to the current presentation.'''
		if self.pres_list.has_selection():
			self.slide_list.set_slides(self.pres_list.get_active_item().slides)
		else:
			self.slide_list.set_slides([])
	
	def _on_pres_rt_click(self, widget, event):
		'''Popup the right click menu for the presentation.'''
		if event.button == 3:
			if self.schedule_list.get_active_item().builtin:
				menu = self.pres_list_menu
			else:
				menu = self.pres_list_sched_menu
			menu.popup(None, None, None, event.button, event.get_time())
	
	def _on_schedule_rt_click(self, widget, event):
		if event.button == 3:
			if widget.get_active_item() and not widget.get_active_item().builtin:
				self.sched_list_menu.popup(None, None, None, event.button, event.get_time())
	
	def _on_slide_activate(self, *args):
		'''Present the selected slide to the screen.'''
		self.presentation.set_text(self.slide_list.get_active_item().get_text())
	
	def _on_pres_new(self, menuitem, ptype):
		'''Add a new presentation.'''
		pres = type_mods[ptype].Presentation()
		if pres.edit(self):
			sched = self.schedule_list.get_active_item()
			if sched and not sched.builtin:
				sched.append(pres)
			model = self.schedule_list.get_model()
			itr = model.get_iter_first()
			while itr:
				sched = model.get_value(itr, 0)
				if sched:
					sched.append(pres)
				itr = model.iter_next(itr)
	
	def _on_pres_edit(self, *args):
		'''Edit the presentation.'''
		field = self.pres_list.get_active_item()
		if not field:
			return False
		if field.edit(self):
			self.pres_list.update()
			self._on_pres_activate()
	
	def _on_pres_delete(self, *args):
		'''Delete the selected presentation.'''
		item = self.pres_list.get_active_item()
		if not item:
			return False
		dialog = gtk.MessageDialog(self, gtk.DIALOG_MODAL,
				gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
				_('Are you sure you want to delete "%s" from your library?') % item.title)
		dialog.set_title( _("Delete Presentation?") )
		resp = dialog.run()
		dialog.hide()
		if resp == gtk.RESPONSE_YES:
			schmod = self.schedule_list.get_model()
			#Remove from builtin modules
			itr = schmod.get_iter_first()
			while itr:
				sched = schmod.get_value(itr, 0)
				if sched:
					for item2 in sched.items:
						if item2.presentation is item.presentation:
							sched.items.remove(item2)
					sched.refresh_model()
				itr = schmod.iter_next(itr)
			#Remove from custom schedules
			itr = schmod.iter_children(self.schedule_list.custom_schedules)
			while itr:
				sched = schmod.get_value(itr, 0)
				for item2 in sched.items:
					if item2.presentation is item.presentation:
						sched.items.remove(item2)
				sched.refresh_model()
				itr = schmod.iter_next(itr)
			os.remove("data/pres/"+item.filename)
			self._on_pres_activate()
	
	def _on_pres_delete_from_schedule(self, *args):
		'Remove the schedule from the current schedule.'
		schedule = self.schedule_list.get_active_item()
		if not schedule or schedule.builtin:
			return False
		item = self.pres_list.get_active_item()
		if not item:
			return False
		schedule.remove(item)
	
	def _on_about(self, *args):
		'''Shows the about dialog.'''
		About(self)
	
	def _on_prefs(self, *args):
		'''Shows the preferences dialog.'''
		self.config.dialog(self)
	
	
	def _quit(self, *args):
		'Cleans up and exits the program.'
		model = self.schedule_list.get_model()
		sched = model.iter_children(self.schedule_list.custom_schedules)
		while sched:
			model.get_value(sched, 0).save()
			sched = model.iter_next(sched)
		gtk.main_quit()

if __name__ == "__main__":
	m = Main()
	gtk.main()

