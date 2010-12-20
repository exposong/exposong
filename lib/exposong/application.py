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
import gtk.gdk
import gobject
import os
import os.path
import webbrowser
from gtk.gdk import pixbuf_new_from_file as pb_new
from xml.dom import minidom

import exposong.about
import exposong.plugins
import exposong.plugins._abstract
import exposong.notify
import exposong._hook
import exposong.help
import exposong.themeselect
from exposong import RESOURCE_PATH, DATA_PATH, SHARED_FILES
from exposong import config, prefs, screen, schedlist, splash, exampledata
from exposong import preslist, presfilter, slidelist, statusbar
from exposong.schedule import Schedule # ? where to put library

main = None
keys_to_disable = ("Background", "Black Screen")


class Main (gtk.Window):
    '''
    Primary user interface.
    '''

    def __init__(self):
        # Define this instance in the global scope. This has to be done
        global main
        main = self
        exposong.log.debug("Loading Main:")
        splash.splash = splash.SplashScreen(self)
        
        #dynamically load plugins
        exposong.log.debug("Loading plugins.")
        exposong.plugins.load_plugins()
        
        exposong.log.debug("Initializing the main window.")
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        gtk.window_set_default_icon_list(
                pb_new(os.path.join(RESOURCE_PATH, 'es128.png')),
                pb_new(os.path.join(RESOURCE_PATH, 'es64.png')),
                pb_new(os.path.join(RESOURCE_PATH, 'es48.png')),
                pb_new(os.path.join(RESOURCE_PATH, 'es32.png')),
                pb_new(os.path.join(RESOURCE_PATH, 'es16.png')))
        self.set_title("ExpoSong")
        self.connect("configure_event", self._on_configure_event)
        self.connect("window_state_event", self._on_window_state_event)
        self.connect("destroy", self._quit)
        
        ##  GUI
        win_v = gtk.VBox()
        
        #These have to be initialized for the menus to render properly
        exposong.log.debug("Loading the presentation screen.")
        screen.screen = screen.Screen()
        screen.screen.reposition(self)
        
        exposong.log.debug("Initializing custom widgets.")
        schedlist.schedlist = schedlist.ScheduleList()
        presfilter.presfilter = presfilter.PresFilter()
        preslist.preslist = preslist.PresList()
        slidelist.slidelist = slidelist.SlideList()
        exampledata.exampledata = exampledata.ExampleData(self)
        
        exposong.log.debug("Creating the menus.")
        menu = self._create_menu()
        win_v.pack_start(menu, False)
        
        exposong.log.debug("Laying out the schedlist and preslist.")
        ## Main Window Area
        win_h_mn = gtk.HBox()
        self.win_h = gtk.HPaned()
        ### Main left area
        left_vbox = gtk.VBox()
        self.win_lft = gtk.VPaned()
        #### Schedule
        schedule_scroll = gtk.ScrolledWindow()
        schedule_scroll.add(schedlist.schedlist)
        schedule_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.win_lft.pack1(schedule_scroll, False, False)
        
        #### Presentation List
        preslist_scroll = gtk.ScrolledWindow()
        preslist_scroll.add(preslist.preslist)
        preslist_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.win_lft.pack2(preslist_scroll, False, False)
        left_vbox.pack_start(self.win_lft, True, True)
        left_vbox.pack_start(presfilter.presfilter, False, True, 2)
        
        left_vbox.show_all()
        self.win_h.pack1(left_vbox, False, False)
        
        exposong.log.debug("Laying out the slidelist.")
        ### Main right area
        win_rt = gtk.VBox()
        #### Slide List
        slidelist.slide_scroll = gtk.ScrolledWindow()
        slidelist.slide_scroll.add(slidelist.slidelist)
        slidelist.slide_scroll.set_policy(gtk.POLICY_AUTOMATIC,
                                          gtk.POLICY_AUTOMATIC)
        
        slide_v = gtk.VBox()
        slide_v.pack_start(slidelist.slide_scroll, True, True)
        slide_v.pack_start(slidelist.slidelist.get_slide_control_bar(), False, True, 3)
        self.win_h.pack2(slide_v, False, False)
        win_h_mn.pack_start(self.win_h, True, True, 0)
        
        win_h_mn.pack_start(self._pane_right(), False, True, 10)
        win_v.pack_start(win_h_mn, True)
        
        ## Status bar
        exposong.log.debug("Status bar.")
        statusbar.statusbar = statusbar.timedStatusbar()
        win_v.pack_end(statusbar.statusbar, False)
        
        gtk.settings_get_default().set_long_property('gtk-button-images', True,
                                                     'application:__init__')
        task = self.build_schedule()
        gobject.idle_add(task.next)
        
        win_v.show_all()
        self.add(win_v)
        
        self.restore_window()
        gobject.idle_add(self.restore_panes,
                         priority=gobject.PRIORITY_HIGH_IDLE + 2)
        # Need to call twice because some in some themes
        # the left divider would move down at each start
        gobject.idle_add(self.restore_panes)
        # All custom schedules should load after the presentations.
        gobject.idle_add(self._ready, priority=gobject.PRIORITY_LOW)
        exposong.log.debug("Loading Main completed.")
    
    def _ready(self):
        "Called when ExpoSong is fully loaded."
        gobject.timeout_add(200, splash.splash.destroy)
        self.show_all()
        # Prepares all button visibility by hiding the screen.
        screen.screen.hide()
        statusbar.statusbar.output(_("Ready"))
        exposong.log.info('Ready.')
        exampledata.exampledata.check_presentations(self)
        return False
    
    def _pane_right(self):
        "Render the right pane with the preview screen and other settings."
        exposong.log.debug("Laying out the preview area.")
        #### Preview and Presentation Buttons
        vbox = gtk.VBox()
        vbox.pack_start(gtk.VSeparator(), False, True, 10)
        exposong.log.debug("Rendering Main Buttons")
        vbox.pack_start(screen.screen.get_button_bar_main(), False, False, 0)
        
        exposong.log.debug("Rendering Preview")
        # Wrap the pres_preview it so that the aspect ratio is kept
        prev_aspect = gtk.AspectFrame(None, 0.5, 0.5,
                                      exposong.screen.screen.aspect, False)
        prev_aspect.set_label(_("Preview"))
        prev_aspect.add(screen.screen.preview)
        vbox.pack_start(prev_aspect, False, False, 0)
        
        exposong.log.debug("Rendering Secondary Buttons")
        vbox.pack_start(screen.screen.get_button_bar_secondary(), False, False, 10)
        
        ##TODO Theme Select
        frame = gtk.Frame()
        frame.set_label(_("Theme"))
        #exposong.bgselect.bgselect = exposong.bgselect.BGSelect()
        exposong.themeselect.themeselect = exposong.themeselect.ThemeSelect()
        frame.add(exposong.themeselect.themeselect)
        vbox.pack_start(frame, False, False, 0)
        
        exposong.log.debug("Rendering Notification")
        frame = gtk.Frame()
        frame.set_label(_("Notify"))
        exposong.notify.notify = exposong.notify.Notify()
        frame.add(exposong.notify.notify)
        vbox.pack_start(frame, False, False, 0)
        
        return vbox
    
    def _create_menu(self):
        'Set up the menus and popup menus.'
        self.uimanager = gtk.UIManager()
        self.add_accel_group(self.uimanager.get_accel_group())
        
        self.main_actions = gtk.ActionGroup('main')
        self.main_actions.add_actions([
                ('File', None, _('_File')),
                ('Edit', None, _('_Edit')),
                ('Schedule', None, _("_Schedule")),
                ('Presentation', None, _('P_resentation')),
                ('pres-controls', None, _("Presentation _Controls")),
                ('Help', None, _('_Help')),
                ('Quit', gtk.STOCK_QUIT, None, None, None, self._quit),
                ('Preferences', gtk.STOCK_PREFERENCES,
                        None, None, None, self._on_prefs),
                ('file-import', None, _("_Import"), "",
                        _("Import a .expo package or other format")),
                ('file-export', None, _("_Export"), "", _("Export a .expo package")),
                ('file-print', None, _("_Print"), "", None),
                ('pres-new', gtk.STOCK_NEW, None, "", _("Create a new presentation")),
                ('Statistics', None, _("Statistics and System Information"),
                        None, None, self._on_stats),
                ('About', gtk.STOCK_ABOUT, None, None, None, self._on_about),
                ])
        self.main_actions.add_actions([
                ('view-log', gtk.STOCK_PROPERTIES, _('View _Log'), None,
                        _("Show the event log"),
                        exposong.gtklogger.handler.show_window)], self)
        self.uimanager.insert_action_group(self.main_actions, 0)
        # UIManager is not as flexible as hoped for, so I have to define actions
        # that are created elsewhere to keep the desired order.
        self.uimanager.add_ui_from_string('''
                <menubar name="MenuBar">
                    <menu action="File">
                        <menu action="file-import"/>
                        <menu action="file-export"/>
                        <menu action="file-print"/>
                        <separator/>
                        <menuitem action="Quit" position="bot" />
                    </menu>
                    <menu action="Edit">
                        <menuitem action="Search" position="bot" />
                        <separator />
                        <menuitem action="view-log" position="bot" />
                        <menuitem action="Preferences" position="bot" />
                    </menu>
                    <menu action="Schedule"></menu>
                    <menu action="Presentation">
                        <menu action="pres-new" position="top"></menu>
                        <menuitem action="pres-edit" />
                        <menuitem action="pres-delete" />
                        <separator />
                        <menu action="pres-add-to-schedule"></menu>
                        <menuitem action="pres-remove-from-schedule" />
                        <separator />
                        <menuitem action="Present" position="bot" />
                        <menuitem action="Hide" position="bot" />
                        <menu action="pres-controls" position="bot">
                            <menuitem action="Black Screen" position="bot" />
                            <menuitem action="Background" position="bot" />
                            <menuitem action="Logo" position="bot" />
                            <menuitem action="Freeze" position="bot" />
                        </menu>
                        <separator />
                        <menuitem action="pres-prev" position="bot" />
                        <menuitem action="pres-next" position="bot" />
                        <menuitem action="pres-slide-prev" position="bot" />
                        <menuitem action="pres-slide-next" position="bot" />
                    </menu>
                    <menu action="Help">
                        <menuitem action="UsageGuide" />
                        <menuitem action="Contribute" />
                        <menuitem action="Statistics" />
                        <menuitem action="About" />
                    </menu>
                </menubar>''')
        
        for mod in exposong._hook.get_hooks(exposong._hook.Menu):
            mod.merge_menu(self.uimanager)
        
        menu = self.uimanager.get_widget('/MenuBar')
        return menu
    
    def load_pres(self, filenm):
        'Load a single presentation.'
        filenm = os.path.join(DATA_PATH, "pres", filenm)
        pres = None
        
        # TODO Might need to attempt to read the file first, then convert if
        # reading it fails.
        plugins = exposong.plugins.get_plugins_by_capability(
                exposong.plugins._abstract.ConvertPresentation)
        for plugin in plugins:
            if plugin.is_type(filenm):
                exposong.log.info('Converting "%s" to openlyrics.', filenm)
                plugin.convert(filenm)
        
        plugins = exposong.plugins.get_plugins_by_capability(
                exposong.plugins._abstract.Presentation)
        for plugin in plugins:
            try:
                pres = plugin(filenm)
                self.library.append(pres)
                exposong.log.info('Adding %s presentation "%s" to Library.',
                                  pres.get_type(), os.path.basename(filenm))
                break
            except exposong.plugins._abstract.WrongPresentationType, details:
                continue
            except Exception, details:
                exposong.log.error('Error in file "%s":\n  %s', filenm, details)
                raise
        else:
            exposong.log.warning('"%s" is not a presentation file.', filenm)
        
    def build_pres_list(self):
        'Load presentations and add them to self.library.'
        directory = os.path.join(DATA_PATH, "pres")
        dir_list = os.listdir(directory)
        splash.splash.incr_total(len(dir_list))
        for filenm in dir_list:
            if filenm.endswith(".xml"):
                self.load_pres(filenm)
                yield True
            splash.splash.incr(1)
        yield False
    
    def load_sched(self, filenm):
        'Load a single schedule.'
        filenm = os.path.join(DATA_PATH, "sched", filenm)
        dom = None
        sched = None
        try:
            dom = minidom.parse(filenm)
        except Exception, details:
            exposong.log.error('Error reading schedule file "%s":\n  %s',
                os.path.join(filenm), details)
        if dom:
            if dom.documentElement.tagName == "schedule":
                sched = Schedule(filename=filenm, builtin=False)
                sched.load(dom.documentElement, self.library)
                schedlist.schedlist.append(schedlist.schedlist.custom_schedules, sched)
            else:
                exposong.log.error("%s is not a schedule file.",
                                   os.path.join(directory, filenm))
            dom.unlink()
            del dom
        return sched

    def build_schedule(self):
        'Add items to the schedule list.'
        #Initialize the Library
        directory = os.path.join(DATA_PATH, "sched")
        self.library = Schedule(_("Library"))
        task = self.build_pres_list()
        gobject.idle_add(task.next, priority=gobject.PRIORITY_DEFAULT_IDLE - 10)
        yield True
        libitr = schedlist.schedlist.append(None, self.library, 1)
        schedlist.schedlist.get_selection().select_iter(libitr)
        schedlist.schedlist._on_schedule_activate()
        
        #Add schedules from plugins
        plugins = exposong.plugins.get_plugins_by_capability(
                exposong.plugins._abstract.Schedule)
        splash.splash.incr_total(len(plugins))
        for plugin in plugins:
            schedule = Schedule(plugin.schedule_name(),
                                filter_func=plugin.schedule_filter)
            itr = self.library.get_iter_first()
            while itr:
                item = self.library.get_value(itr, 0).presentation
                schedule.append(item)
                itr = self.library.iter_next(itr)
            schedlist.schedlist.append(libitr, schedule, 2)
            splash.splash.incr(1)
            yield True
        
        #Add custom schedules from the data directory
        schedlist.schedlist.custom_schedules = schedlist.schedlist.append(None,
                (None, _("Custom Schedules"), 40))
        
        dir_list = os.listdir(directory)
        for filenm in dir_list:
            if filenm.endswith(".xml"):
                self.load_sched(filenm)
                yield True
        schedlist.schedlist.expand_all()
        
        schedmodel = schedlist.schedlist.get_model()
        schedlist.schedlist.collapse_row(schedmodel.get_path(libitr))
        yield False
    
    def _on_stats(self, *args):
        'Shows the statistics dialog.'
        exposong.about.Statistics(self)
    
    def _on_about(self, *args):
        'Shows the about dialog.'
        exposong.about.About(self)
    
    def _on_prefs(self, *args):
        'Shows the preferences dialog.'
        prefs.PrefsDialog(self)
    
    def _save_schedules(self):
        'Save all schedules to disk.'
        model = schedlist.schedlist.get_model()
        sched = model.iter_children(schedlist.schedlist.custom_schedules)
        while sched:
            model.get_value(sched, 0).save()
            sched = model.iter_next(sched)
    
    def disable_shortcuts(self, *args):
        'Disables keyboard shortcuts to allow typing.'
        for k in keys_to_disable:
            screen.screen._actions.get_action(k).disconnect_accelerator()

    def enable_shortcuts(self, *args):
        'Enables keyboard shortcuts after disabling.'
        for k in keys_to_disable:
            screen.screen._actions.get_action(k).connect_accelerator()
    
    def _on_configure_event(self, widget, *args):
        'Sets the size and position in the config (matters, if not maximized)'
        if not config.config.has_option("main_window", "maximized") or \
                not config.config.getboolean("main_window", "maximized"):
            config.config.set("main_window", "size", ','.join(
                    map(str, self.get_size())))
            config.config.set("main_window", "position", ",".join(
                    map(str, self.get_position())))
        
    def _on_window_state_event(self, widget, event, *args):
        'Sees if window is maximized or not and sets it in the config'
        maximized = (event.new_window_state == gtk.gdk.WINDOW_STATE_MAXIMIZED)
        config.config.set("main_window", "maximized", str(maximized))

    def restore_window(self):
        'Restores window position and size.'
        if config.config.has_option("main_window", "size"):
            (x, y) = config.config.get("main_window", "size").split(",")
            self.set_default_size(int(x), int(y))
        if config.config.has_option("main_window", "position"):
            (x, y) = config.config.get("main_window", "position").split(",")
            self.move(int(x), int(y))
        if config.config.has_option("main_window", "maximized"):
            if config.config.getboolean("main_window", "maximized"):
                self.maximize()

    def restore_panes(self):
        'Restores the size of the two panes'
        if config.config.has_option("main_window", "left-paned"):
            self.win_lft.set_position(int(config.config.get(
                    "main_window", "left-paned")))
        if config.config.has_option("main_window", "main-paned"):
            self.win_h.set_position(int(config.config.get(
                    "main_window", "main-paned")))
        return False

    def save_state(self):
        'Saves the state of the panes in the window'
        config.config.set("main_window", "left-paned",
                                            str(self.win_lft.get_position()))
        config.config.set("main_window", "main-paned",
                                            str(self.win_h.get_position()))

    def _quit(self, *args):
        'Cleans up and exits the program.'
        self._save_schedules()
        self.save_state()
        config.config.write()
        exposong.help.help.delete_help_file()
        gtk.main_quit()


def run():
    Main()
    gtk.main()
