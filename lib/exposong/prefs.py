#
# vim: ts=4 sw=4 expandtab ai:
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
import os

from exposong import gui
from exposong import DATA_PATH
from exposong import SHARED_FILES
from exposong.config import config
import exposong.screen
import exposong.application

'''
Dialog for changing settings in ExpoSong.
'''

class PrefsDialog(gtk.Dialog):
    '''
    Dialog to configure user preferences.
    '''
    def __init__(self, parent):
        gtk.Dialog.__init__(self, _("Preferences"), parent, 0,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        self.set_default_size(350, 410)
        notebook = gtk.Notebook()
        self.vbox.pack_start(notebook, True, True, 5)
        
        #General Page
        table = gui.Table(10)
        
        if config.has_option("general", "data-path"):
            folder = config.get("general", "data-path")
        else:
            folder = DATA_PATH
        g_data = gui.append_folder(table, _("Data folder"), folder, 0)
        msg = _("The place where all your presentations, schedules and background images are stored.")
        g_data.set_tooltip_text(msg)
        
        g_title = gui.append_checkbutton(table, _("Slides"), _("Insert title slide"), 1)
        if config.get("general", "title_slide") == "True":
            g_title.set_active(True)
        
        gui.append_section_title(table, _("Lyrics"), 2)
        g_ccli = gui.append_entry(table, "CCLI #", config.get("general","ccli"), 3)
        songbooks = [sbook.name for t in exposong.application.main.library
                     if t[0].get_type() == "lyric"
                     for sbook in t[0].song.props.songbooks]
        songbooks = sorted(set(songbooks))
        g_songbook = gui.append_combo(table, _("Songbook"), songbooks,
                                      config.get("general","songbook"), 4)
        
        notebook.append_page(table, gtk.Label( _("General") ))
        
        #Screen Page
        table = gui.Table(15)
        
        gui.append_section_title(table, _("Font"), 0)
        p_txt = gui.append_color(table, _("Text Color"),
                                 config.getcolor("screen","text_color"), 1)
        p_shad = gui.append_color(table, _("Text Shadow"),
                                  config.getcolor("screen","text_shadow"), 2,
                                  True)
        p_maxsize = gui.append_spinner(table, _("Max Font Size"),
                                       gtk.Adjustment(config.getfloat("screen",
                                       "max_font_size"), 0, 96, 1),3)
        
        gui.append_section_title(table, _("Logo"), 5)
        p_logo = gui.append_file(table, _("Image"), config.get("screen","logo"), 6)
        p_logo_bg = gui.append_color(table, _("Background"),
                                     config.getcolor("screen","logo_bg"), 7)
        
        gui.append_section_title(table, _("Notify"), 9)
        p_notify_bg = gui.append_color(table, _("Background"),
                                       config.getcolor("screen","notify_bg"), 10)
        
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
        
        gui.append_section_title(table, _("Position"), 11)
        p_monitor = gui.append_combo(table, _("Monitor"), monitor_name, sel, 12)
        
        notebook.append_page(table, gtk.Label( _("Screen")))
        
        self.show_all()
        if self.run() == gtk.RESPONSE_ACCEPT:
            config.set("general", "ccli", g_ccli.get_text())
            if g_songbook.get_active_text():
                config.set("general", "songbook", g_songbook.get_active_text())
            if config.get("general", "title_slide") != str(g_title.get_active()):
                config.set("general", "title_slide", str(g_title.get_active()))
                exposong.preslist.preslist._on_pres_activate()
            if g_data.get_current_folder() != config.get("general", "data-path"):
                config.set("general", "data-path", g_data.get_current_folder())
                msg = _("You will have to restart ExpoSong so that the new data folder will be used.")
                dlg = gtk.MessageDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT,
                        gtk.MESSAGE_INFO, gtk.BUTTONS_OK, msg)
                dlg.run()
                dlg.destroy()
            
            txtc = p_txt.get_color()
            config.setcolor("screen", "text_color", (txtc.red, txtc.green,
                            txtc.blue))
            txts = p_shad.get_color()
            config.setcolor("screen", "text_shadow", (txts.red, txts.green,
                            txts.blue, p_shad.get_alpha()))
            config.set("screen", "max_font_size", str(p_maxsize.get_value()))
            
            if p_logo.get_filename() != None:
                config.set("screen", "logo", p_logo.get_filename())
            logoc = p_logo_bg.get_color()
            config.setcolor("screen", "logo_bg", (logoc.red, logoc.green, logoc.blue))
            ntfc = p_notify_bg.get_color()
            config.setcolor("screen", "notify_bg", (ntfc.red, ntfc.green, ntfc.blue))
            
            config.set('screen','monitor', monitor_value[p_monitor.get_active()])
            exposong.screen.screen.reposition(parent)
            
            exposong.screen.screen.set_dirty()
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

def getGeometryFromRect(_g1):
    return ','.join( map(str, (_g1.x, _g1.y, _g1.width, _g1.height)) )
