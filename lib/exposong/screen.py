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

"""
The Screen class provides the presentation screen for ExpoSong. This will
initialize the window and set up a few things, but most of the rendering is
done by the theme.
"""

from gi.repository import Gtk, Gdk, GObject
import os

import exposong.main
import exposong.prefs
import exposong.slidelist
import exposong.theme
import exposong.notify

from exposong.config import config
from exposong import RESOURCE_PATH


def c2dec(color):
    """Convert the GTK color to decimal (Values of 0.0 to 1.0).
    
    color: A tuple or list representing the color. It will normally look like
           [Red, Green, Blue], or [Red, Green, Blue, Opacity].
    """
    if isinstance(color, (tuple, list)):
        return tuple(c2dec(x) for x in color)
    else:
        return color / 65535.0

#This will be the instance variable for Screen once Main runs.
screen = None

#This static value determines the height of the preview screen.
PREV_HEIGHT = 145

class Screen(exposong._hook.Menu):
    '''
    The presentation screen for ExpoSong.
    '''
    def __init__(self):
        "Create the screen's GUI."
        self.aspect = 4 / 3
        self._size = None
        
        self.window = Gtk.Window(Gtk.WindowType.POPUP)
        
        self.pres = Gtk.DrawingArea()
        self.pres.connect("draw", self._expose_screen)
        self.window.add(self.pres)
        
        self.preview = Gtk.DrawingArea()
        self.preview.connect("draw", self._expose_screen)
        
        
        # Themes being used for the preview when black, background or logo  is active
        t = exposong.theme
        pos = [0.0, 0.3, 1.0, 0.7]
        # Black theme
        self._theme_black = t.Theme()
        self._theme_black.backgrounds.append(t.ColorBackground(color='#000'))
        self._theme_black.backgrounds.append(t.ImageBackground(
                os.path.join(RESOURCE_PATH, 'icons', 'screen-black.png'),
                aspect=exposong.theme.ASPECT_FIT, pos=pos))
        # Background theme
        self._theme_bg = t.Theme()
        self._theme_bg.backgrounds.append(t.ColorBackground(color='#000'))
        self._theme_bg.backgrounds.append(t.ImageBackground(
                os.path.join(RESOURCE_PATH, 'icons', 'screen-bg.png'),
                aspect=exposong.theme.ASPECT_FIT, pos=pos))
        # Logo theme
        self._theme_logo = t.Theme()
        self._theme_logo.backgrounds.append(t.ColorBackground(color='#000'))
        self._theme_logo.backgrounds.append(t.ImageBackground(
                os.path.join(RESOURCE_PATH, 'icons', 'screen-logo.png'),
                aspect=exposong.theme.ASPECT_FIT, pos=pos))
        # Freeze theme
        self._theme_freeze = t.Theme()
        self._theme_freeze.backgrounds.append(t.ColorBackground(color='#000'))
        self._theme_freeze.backgrounds.append(t.ImageBackground(
                os.path.join(RESOURCE_PATH, 'icons', 'screen-freeze.png'),
                aspect=exposong.theme.ASPECT_FIT, pos=pos))
    
    def reposition(self, parent):
        '''
        Finds the best location for the screen.
        
        If the user is using one monitor, use the bottom right corner for
        the presentation screen_, otherwise, use the 2nd monitor.
        '''
        geometry = None
        screen_ = parent.get_screen()
        num_monitors = screen_.get_n_monitors()
        
        if config.has_option('screen','monitor'):
            if config.get('screen', 'monitor') == '1h':
                scr_geom = screen_.get_monitor_geometry(0)
                geometry = (scr_geom.width/2, scr_geom.height/2,
                            scr_geom.width/2, scr_geom.height/2)
            elif num_monitors >= config.getint('screen','monitor'):
                scr_geom = screen_.get_monitor_geometry(
                                        config.getint('screen','monitor')-1)
                geometry = (scr_geom.x, scr_geom.y, scr_geom.width,
                            scr_geom.height)
        
        if geometry == None:
            if(num_monitors > 1):
                scr_geom = screen_.get_monitor_geometry(1)
                geometry = (scr_geom.x, scr_geom.y, scr_geom.width,
                            scr_geom.height)
            else:
                # No 2nd monitor, so preview it small in the corner of the screen_
                scr_geom = screen_.get_monitor_geometry(0)
                parent.move(0,0)
                geometry = (scr_geom.width/2, scr_geom.height/2,
                            scr_geom.width/2, scr_geom.height/2)
        exposong.log.info('Setting presentation screen position to %s.',
                           "x=%d, y=%d, w=%d, h=%d" % geometry)
        self.window.move(geometry[0], geometry[1])
        self.window.resize(geometry[2], geometry[3])
        self.aspect = float(geometry[2])/geometry[3]
        self.preview.set_size_request(int(PREV_HEIGHT*self.aspect), PREV_HEIGHT)
        self._size = geometry[2:4]
    
    def get_size(self):
        "Get the current screen size."
        return self._size
    
    def get_aspect(self):
        "Returns the current aspect ratio (width / height)."
        return self.aspect
    
    def draw(self):
        '''
        Redraw the presentation and preview screens.
        Draw preview only when freeze is active.
        '''
        if self._actions.get_action('Freeze').get_active() or not self.is_viewable():
            self.preview.queue_draw()
        else:
            self.pres.queue_draw()
    
    def hide(self, action=None):
        'Remove the presentation screen from view.'
        self._actions.get_action("Present").set_visible(True)
        self._actions.get_action("Hide").set_visible(False)
        self.window.hide()
        self._set_menu_items_disabled()
        for nm in ('Freeze', 'Background', 'Logo', 'Black Screen'):
            nmaction = self._actions.get_action(nm)
            if action != nmaction:
                nmaction.set_active(False)
        self.preview.queue_draw()
    
    def show(self, *args):
        'Show the presentation screen.'
        exposong.log.info('Showing the presentation screen.')
        self._actions.get_action("Hide").set_visible(True)
        self._actions.get_action("Present").set_visible(False)
        self.window.show_all()
        self._set_menu_items_disabled()
        self._secondary_button_toggle()
        self.draw()
        exposong.slidelist.slidelist.grab_focus()
        exposong.slidelist.slidelist.reset_timer()
    
    def _expose_screen(self, widget, event):
        'Redraw the presentation screen.'
        self._draw(widget)
    
    def is_viewable(self):
        "Return true if the screen is currently visible."
        state = self.pres.get_window() and self.pres.get_window().is_viewable()
        if state is None:
            return False
        return state
    
    def is_running(self):
        'The presentation is visible and running (not black or background).'
        return self.is_viewable() and not (
               self._actions.get_action('Black Screen').get_active() or
               self._actions.get_action('Logo').get_active() or
               self._actions.get_action('Background').get_active() or
               self._actions.get_action('Freeze').get_active())
    
    def _draw(self, widget):
        'Render `widget`.'
        if not widget.get_window() or not widget.get_window().is_viewable():
            return False
        
        if self.pres.get_window() and self.pres.get_window().get_size() != self._size:
            exposong.log.error('The screen sizes are inconsistent. '
                               + 'Screen: "%s"; Stored: "%s".',
                               self.pres.window.get_size(), self._size)
            self._size = self.pres.window.get_size()
        
        ccontext = widget.get_window().cairo_create()
        bounds = widget.get_window().get_size()
        if widget is self.preview:
            if self.pres.window:
                #Scale if the presentation window size is available
                bounds = self.pres.window.get_size()
            elif self._size:
                bounds = self._size
            if bounds:
                width = int(float(PREV_HEIGHT)*bounds[0]/bounds[1])
                ccontext.scale(float(width)/bounds[0],
                               float(PREV_HEIGHT)/bounds[1])
        elif widget is self.pres:
            self.preview.queue_draw()
        
        slide = exposong.slidelist.slidelist.get_active_item()
        theme = None
        
        if slide:
            theme = slide.get_theme()
        if theme is None:
            theme = exposong.themeselect.themeselect.get_active()
        if theme is None:
            # Select the first theme if nothing is set as the default.
            exposong.themeselect.themeselect.set_active(0)
            theme = exposong.themeselect.themeselect.get_active()
        
        if widget is self.pres:
            if self._actions.get_action('Black Screen').get_active():
                exposong.theme.Theme.render_color(ccontext, bounds, '#000')
            elif self._actions.get_action('Logo').get_active():
                logoclr = Gdk.Color(*config.getcolor('screen', 'logo_bg'))
                exposong.theme.Theme.render_color(ccontext, bounds, logoclr.to_string())
                self.__logo_img.draw(ccontext, bounds, None)
            elif self._actions.get_action('Background').get_active():
                theme.render(ccontext, bounds, None)
            else:
                theme.render(ccontext, bounds, slide)
        
        # In Preview show the themes defined in __init__ when
        # one of the secondary buttons is active.
        if widget is self.preview:
            if self._actions.get_action('Black Screen').get_active():
                self._theme_black.render(ccontext, bounds, None)
            elif self._actions.get_action('Background').get_active():
                self._theme_bg.render(ccontext, bounds, None)
            elif self._actions.get_action('Logo').get_active():
                self._theme_logo.render(ccontext, bounds, None)
            elif self._actions.get_action('Freeze').get_active():
                self._theme_freeze.render(ccontext, bounds, None)
            else:
                theme.render(ccontext, bounds, slide)
        
        exposong.notify.notify.draw(ccontext, bounds)
            
        return True
    
    def _set_menu_items_disabled(self):
        'Disable buttons if the presentation is not shown.'
        enabled = self.is_viewable()
        self._actions.get_action("Background").set_sensitive(enabled)
        self._actions.get_action("Logo").set_sensitive(enabled)
        self._actions.get_action("Black Screen").set_sensitive(enabled)
        self._actions.get_action("Freeze").set_sensitive(enabled)
        self._actions.get_action('Hide').set_sensitive(enabled)
    
    @classmethod
    def merge_menu(cls, uimanager):
        'Create menu items.'
        global screen
        #Gtk.stock_add([
        #    ("screen-black",_("_Black"), Gdk.ModifierType.MOD1_MASK, 0, "pymserv"),
        #    ("screen-bg",_("Bac_kground"), Gdk.ModifierType.MOD1_MASK, 0, "pymserv"),
        #    ("screen-logo",_("Lo_go"), Gdk.ModifierType.MOD1_MASK, 0, "pymserv"),
        #    ("screen-freeze",_("_Freeze"), Gdk.ModifierType.MOD1_MASK, 0, "pymserv"),
        #    ])
        cls._actions = Gtk.ActionGroup('screen')
        cls._actions.add_actions([
                ('Present', Gtk.STOCK_MEDIA_PLAY, _('Start _Presentation'), "F5",
                        _("Show the presentation screen"), screen.show),
                ('Hide', Gtk.STOCK_MEDIA_STOP, _('_Exit Presentation'), "Escape",
                        _("Hide the presentation screen"), screen.hide),
                #('Pause', Gtk.STOCK_MEDIA_PAUSE, None, None,
                #        _('Pause a timed slide.'), screen.pause),
                ])
        cls._actions.add_toggle_actions([
                ('Black Screen', Gtk.STOCK_DIALOG_QUESTION, _('_Black Screen'), "b",
                        _("Show a black screen."),
                        screen._secondary_button_toggle),
                ('Background', Gtk.STOCK_DIALOG_QUESTION, _('Bac_kground'), None,
                        _("Show only the background."),
                        screen._secondary_button_toggle),
                ('Logo', Gtk.STOCK_DIALOG_QUESTION, _('Lo_go'), "<Ctrl>g",
                        _("Display the logo."), screen.to_logo),
                ('Freeze', Gtk.STOCK_DIALOG_QUESTION, _('_Freeze'), None ,
                        _("Freeze the screen."),
                        screen._secondary_button_toggle),
                ])
        
        uimanager.insert_action_group(cls._actions, -1)
        uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="Presentation">
                    <menuitem action="Present" position="bot" />
                    <menuitem action="Hide" position="bot" />
                    <menu action="pres-controls">
                        <menuitem action="Black Screen" position="bot" />
                        <menuitem action="Background" position="bot" />
                        <menuitem action="Logo" position="bot" />
                        <menuitem action="Freeze" position="bot" />
                    </menu>
                </menu>
            </menubar>
            """)
        # unmerge_menu not implemented, because we will never uninstall this as
        # a module.
        
        cls._set_menu_items_disabled(screen)
    
    @classmethod
    def get_button_bar_main(cls):
        "Return the presentation button widget."
        tb = Gtk.Toolbar()
        # FIXME It would be nice to get rid of the shadow on the toolbars, but
        # they are read-only style properties.
        tb.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        tb.set_icon_size(Gtk.IconSize.SMALL_TOOLBAR)
        button = cls._actions.get_action('Present').create_tool_item()
        button.set_is_important(True)
        tb.add(button)
        button = cls._actions.get_action('Hide').create_tool_item()
        button.set_is_important(True)
        tb.add(button)
        return tb
    
    @classmethod
    def get_button_bar_secondary(cls):
        "Return the presentation display widget."
        tb = Gtk.Toolbar()
        tb.set_show_arrow(False)
        
        #For screens smaller than 650px high (Netbooks usually) display these buttons horizontally
        scr_geom = exposong.main.main.get_screen().get_monitor_geometry(0)
        if scr_geom.height>650:
            tb.set_orientation(Gtk.Orientation.VERTICAL)
            tb.set_style(Gtk.ToolbarStyle.BOTH_HORIZ)
        else:
            tb.set_orientation(Gtk.Orientation.HORIZONTAL)
            tb.set_style(Gtk.ToolbarStyle.ICONS)
            tb.set_icon_size(Gtk.IconSize.LARGE_TOOLBAR)
        
        # FIXME It would be nice to get rid of the shadow on the toolbars, but
        # they are read-only style properties.
        button = cls._actions.get_action('Black Screen').create_tool_item()
        tb.add(button)
        button = cls._actions.get_action('Background').create_tool_item()
        tb.add(button)
        button = cls._actions.get_action('Logo').create_tool_item()
        tb.add(button)
        button = cls._actions.get_action('Freeze').create_tool_item()
        tb.add(button)
        return tb
    
    def _secondary_button_toggle(self, action=None, state=None):
        'Toggle a state button.'
        if state != None:
            action.set_active(True)
        for nm in ('Freeze', 'Background', 'Logo', 'Black Screen'):
            nmaction = self._actions.get_action(nm)
            if action and action.get_active() and action != nmaction:
                nmaction.set_sensitive(False)
            else:
                nmaction.set_sensitive(True)
                self.draw()
        self.draw()
    
    def to_logo(self, action=None):
        'Set the screen to the ExpoSong logo or a user-defined one.'
        if action == None:
            action = self._actions.get_action('Logo')
        if not action.get_active():
            self._secondary_button_toggle(action)
            return
        if config.has_option("screen", "logo") and \
                os.path.isfile(config.get("screen", "logo")):
            # TODO should we resize the logo? If not, we need to add the
            # feature to theme.Image
            try:
                if self.__logo_fl != config.get("screen", "logo"):
                    self.__logo_fl = config.get('screen', 'logo')
                    self.__logo_img = exposong.theme.Image(self.__logo_fl,
                            pos=[0.2, 0.2, 0.8, 0.8])
            except AttributeError:
                self.__logo_fl = config.get('screen', 'logo')
                self.__logo_img = exposong.theme.Image(self.__logo_fl,
                        pos=[0.2, 0.2, 0.8, 0.8])
            self._secondary_button_toggle(action, True)
        else:
            self._secondary_button_toggle(None)
            msg = _('No Logo set. Do you want to choose a Logo now?')
            dialog = Gtk.MessageDialog(exposong.main.main, Gtk.DialogFlags.MODAL,
                                       Gtk.MessageType.WARNING, Gtk.ButtonsType.YES_NO,
                                       msg)
            dialog.set_default_response(Gtk.ResponseType.YES)
            dialog.set_title( _("Set Logo?") )
            resp = dialog.run()
            dialog.destroy()
            if resp == Gtk.ResponseType.YES:
                exposong.prefs.PrefsDialog(exposong.main.main)
                if os.path.isfile(config.get("screen", "logo")):
                    self.to_logo()
            else:
                self.to_background()
