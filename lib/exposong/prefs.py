#
# vim: ts=4 sw=4 expandtab ai:
#
# Copyright (C) 2008-2011 Exposong.org
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

from exposong import gui
from exposong import DATA_PATH
from exposong.config import config
import exposong.screen
import exposong.main

'''
Dialog for changing settings in ExpoSong.
'''

class PrefsDialog(gtk.Dialog):
    '''
    Dialog to configure user preferences.
    '''
    def __init__(self, parent):
        """
        Create the preferences GUI dialog.
        
        parent: the primary window that the dialog will be centered on.
        """
        gtk.Dialog.__init__(self, _("Preferences"), parent, 0,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.set_default_size(350, 410)
        notebook = gtk.Notebook()
        self.vbox.pack_start(notebook, True, True, 5)
        
        #General Page
        table = gui.ESTable(10, auto_inc_y=True)
        
        if config.has_option("general", "data-path"):
            folder = config.get("general", "data-path")
        else:
            folder = DATA_PATH
        g_data = table.attach_folderchooser(folder, label=_("Data folder"))
        msg = _("The place where all your presentations, schedules and \
themes are stored.")
        g_data.set_tooltip_text(msg)
        table.attach_section_title(_("Updates"))
        g_update = table.attach_checkbutton(
            _("Automatically check for a new version"))
        if config.get("updates", "check_for_updates") == "True":
            g_update.set_active(True)
        
        table.attach_section_title(_("Songs"))
        g_title = table.attach_checkbutton(_("Insert title slide"))
        if config.get("songs", "title_slide") == "True":
            g_title.set_active(True)

        g_ccli = table.attach_entry(config.get("songs","ccli"),
                                    label="CCLI License #")
        songbooks = [sbook.name for t in exposong.main.main.library
                     if t[0].get_type() == "song"
                     for sbook in t[0].song.props.songbooks]
        songbooks = sorted(set(songbooks))
        g_songbook = table.attach_combo(songbooks,
                                        config.get("songs","songbook"),
                                        label=_("Songbook"))
        table.attach_comment(_("Songbooks in Songs are automatically \
added to this list."))
        
        notebook.append_page(table, gtk.Label( _("General") ))
        
        #Screen Page
        table = gui.ESTable(9, auto_inc_y=True)
        
        table.attach_section_title(_("Logo"))
        p_logo = table.attach_filechooser(config.get("screen","logo"),
                                          label=_("Image"))
        p_logo_bg = table.attach_color(config.getcolor("screen","logo_bg"),
                                       label=_("Background"))
        
        table.attach_section_title(_("Notify"))
        p_notify_color = table.attach_color(config.getcolor("screen","notify_color"),
                                            label=_("Font Color"))
        p_notify_bg = table.attach_color(config.getcolor("screen","notify_bg"),
                                         label=_("Background"))
        
        # Monitor Selection
        monitor_name = tuple()
        sel = 0
        screen = parent.get_screen()
        num_monitors = screen.get_n_monitors()
        monitor_name = (_("Primary"), _("Primary (Bottom-Right)"),
                        _("Secondary"), _("Tertiary"), _("Monitor 4")
                        )[0:num_monitors+1]
        monitor_value = ('1', '1h', '2', '3', '4')[0:num_monitors+1]
        if num_monitors == 1:
            sel = monitor_name[1]
        else:
            sel = monitor_name[2]
        
        try:
            if config.get('screen', 'monitor') == '1':
                sel = monitor_name[0]
            if config.get('screen', 'monitor') == '1h':
                sel = monitor_name[1]
            else:
                sel = monitor_name[config.getint('screen', 'monitor')]
        except config.NoOptionError:
            pass
        except IndexError:
            pass
        
        table.attach_section_title(_("Position"))
        p_monitor = table.attach_combo(monitor_name, sel, label=_("Monitor"))
        
        notebook.append_page(table, gtk.Label(_("Screen")))
        
        self.show_all()
        if self.run() == gtk.RESPONSE_ACCEPT:
            if config.has_option("general", "data-path"):
                curpath = config.get("general", "data-path")
            else:
                curpath = DATA_PATH
            if g_data.get_current_folder() != curpath:
                config.set("general", "data-path", g_data.get_current_folder())
                msg = _("You will have to restart ExpoSong so that the new data folder will be used.")
                dlg = gtk.MessageDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT,
                        gtk.MESSAGE_INFO, gtk.BUTTONS_OK, msg)
                dlg.run()
                dlg.destroy()
            
            if config.get("songs", "title_slide") != str(g_title.get_active()):
                config.set("songs", "title_slide", str(g_title.get_active()))
                exposong.slidelist.slidelist.update()
            config.set("songs", "ccli", g_ccli.get_text())
            if g_songbook.get_active_text():
                config.set("songs", "songbook", g_songbook.get_active_text())
            config.set("updates", "check_for_updates", str(g_update.get_active()))
            
            if p_logo.get_filename() != None:
                config.set("screen", "logo", p_logo.get_filename())
            logoc = p_logo_bg.get_color()
            config.setcolor("screen", "logo_bg", (logoc.red, logoc.green, logoc.blue))
            ntfc = p_notify_color.get_color()
            config.setcolor("screen", "notify_color", (ntfc.red, ntfc.green, ntfc.blue))
            ntfb = p_notify_bg.get_color()
            config.setcolor("screen", "notify_bg", (ntfb.red, ntfb.green, ntfb.blue))
            
            config.set('screen','monitor', monitor_value[p_monitor.get_active()])
            exposong.screen.screen.reposition(parent)
            
            if hasattr(exposong.screen.screen,"_logo_pbuf"):
                del exposong.screen.screen._logo_pbuf
            exposong.screen.screen.draw()
        
        self.hide()
    
    def _on_toggle(self, button, target):
        'Enables or disables target if button is set.'
        if isinstance(target, gtk.Widget):
            target.set_sensitive(button.get_active())
        elif isinstance(target, (tuple, list)):
            for t in target:
                self._on_toggle(button, t)
