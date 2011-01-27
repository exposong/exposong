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

"""
A widget to change the currently active theme.
"""

import gobject
import gtk
import os.path
import pango
import re
from gtk.gdk import pixbuf_new_from_file as pb_new

import exposong.application
import exposong.screen
import exposong.theme
from exposong import themeeditor
from exposong import DATA_PATH
from exposong.config import config

themeselect = None
_example_slide = None
CELL_HEIGHT = 65
UNSCALE = 4


class ThemeSelect(gtk.ComboBox, exposong._hook.Menu, object):
    """
    A theme selection combo box for the main screen.
    """
    def __init__(self):
        self.liststore = gtk.ListStore(gobject.TYPE_STRING,
                                       gobject.TYPE_PYOBJECT)
        cell = gtk.CellRendererPixbuf
        
        gtk.ComboBox.__init__(self, self.liststore)
        themerend = CellRendererTheme()
        self.pack_start(themerend, False)
        self.add_attribute(themerend, 'theme', 1)
        textrend = gtk.CellRendererText()
        textrend.set_property("ellipsize", pango.ELLIPSIZE_END)
        self.pack_start(textrend, True)
        self.set_cell_data_func(textrend, self._get_theme_title)
        self.connect("changed", self._on_change)
        
        task = self._load_builtin()
        gobject.idle_add(task.next)
        task = self._load_themes()
        gobject.idle_add(task.next)
    
    def get_active(self):
        "Get the currently selected theme."
        itr = self.get_active_iter()
        if itr:
            return self.liststore.get_value(itr, 1)
        return None
    
    def _load_builtin(self):
        "Load some builtin themes."
        try:
            active = config.get("screen", "theme")
        except Exception:
            active = None
        
        yield True
        
        themes = {}
        
        themes['_builtin_black'] = exposong.theme.Theme(builtin=True)
        themes['_builtin_black'].meta['title'] = _('Black')
        
        themes['_builtin_white'] = exposong.theme.Theme(builtin=True)
        themes['_builtin_white'].meta['title'] = _('White')
        themes['_builtin_white'].backgrounds.append(exposong.theme.ColorBackground("#fff"))
        themes['_builtin_white'].body.color = '#000'
        themes['_builtin_white'].body.shadow_color = '#fff'
        themes['_builtin_white'].footer.color = '#000'
        themes['_builtin_white'].footer.shadow_color = '#fff'
        
        themes['_builtin_blue_gradient'] = exposong.theme.Theme(builtin=True)
        themes['_builtin_blue_gradient'].meta['title'] = _('ES Blue')
        bg = exposong.theme.GradientBackground(45)
        bg.stops.append(exposong.theme.GradientStop(0.0, '#034'))
        bg.stops.append(exposong.theme.GradientStop(1.0, '#069'))
        themes['_builtin_blue_gradient'].backgrounds.append(bg)
        
        for k,v in themes.iteritems():
            itr = self.liststore.append([k, v])
            if k == active:
                self.set_active_iter(itr)
            yield True
        yield False
    
    def _load_themes(self):
        "Load all the themes from disk."
        exposong.log.debug("Loading theme previews.")
        try:
            active = config.get("screen", "theme")
        except Exception:
            active = None
        dir = os.path.join(DATA_PATH, "theme")
        yield True
        for filenm in os.listdir(dir):
            if not filenm.endswith('.xml'):
                continue
            if not os.path.isfile(os.path.join(dir, filenm)):
                continue
            path = os.path.join(dir, filenm)
            exposong.log.info('Loading theme "%s".',
                              filenm)
            theme = exposong.theme.Theme(path)
            itr = self.liststore.append([path, theme])
            if path == active or (active == None and path.endswith("/exposong.xml")):
                self.set_active_iter(itr)
            yield True
        task = self._load_theme_thumbs()
        gobject.idle_add(task.next, priority=gobject.PRIORITY_LOW)
        yield False
    
    def _load_theme_thumbs(self):
        "Force loading of theme thumbnails."
        cell = self.get_cells()[0]
        size = (int(CELL_HEIGHT * exposong.screen.screen.get_aspect()),
                  CELL_HEIGHT)
        yield True
        for row in self.liststore:
            cell.theme = row[1]
            cell._get_pixmap(self.window, size)
            yield True
        yield False
    
    def _get_theme_title(self, column, cell, model, titer):
        "Set the title."
        thm = model.get_value(titer, 1)
        if thm:
            cell.set_property('text', thm.get_title())
    
    def _on_change(self, combo):
        "A new image was selected."
        itr = combo.get_active_iter()
        if itr:
            mod = combo.get_model()
            config.set("screen", "theme", mod.get_value(itr, 0))
            t = os.path.basename(mod.get_value(itr, 0)).rstrip('.xml').title()
            exposong.log.info('Changing theme to "%s".',t)
            exposong.screen.screen.draw()
        self._set_menu_items_disabled()
    
    def new_theme(self, *args):
        themeeditor.ThemeEditor(exposong.application.main)
        
    def edit_theme(self, *args):
        print self.get_active()
        theme = self.get_active()
        if theme.is_builtin():
            raise Exception("Builtin themes cannot be modified.")
        themeeditor.ThemeEditor(exposong.application.main, theme.filename)
    
    def delete_theme(self, *args):
        #TODO
        pass
        
    @classmethod
    def merge_menu(cls, uimanager):
        'Merge new values with the uimanager.'
        global themeselect
        
        cls._actions = gtk.ActionGroup('theme')
        cls._actions.add_actions([
                ('theme-new', gtk.STOCK_NEW, _('New Theme'), None,
                        _("Create a new theme using the Theme Editor"), themeselect.new_theme),
                ('theme-edit', gtk.STOCK_EDIT, _('Edit Theme'), None,
                        _("Edit the current theme"), themeselect.edit_theme),
                ('theme-delete', gtk.STOCK_DELETE, _("Delete Theme"), None,
                        _('Delete the current theme'), themeselect.delete_theme),
                ])
        
        uimanager.insert_action_group(cls._actions, -1)
        uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="Theme">
                    <menuitem action="theme-new" position="bot" />
                    <menuitem action="theme-edit" position="bot" />
                    <menuitem action="theme-delete" position="bot" />
                </menu>
            </menubar>
            """)
        # unmerge_menu not implemented, because we will never uninstall this as
        # a module.
    
    def _set_menu_items_disabled(self):
        'Disable buttons if the presentation is not shown.'
        enabled = not self.get_active().is_builtin()
        self._actions.get_action("theme-edit").set_sensitive(enabled)
        self._actions.get_action("theme-delete").set_sensitive(enabled)
    
    @classmethod
    def get_button_bar(cls):
        "Return the presentation button widget."
        tb = gtk.Toolbar()
        # FIXME It would be nice to get rid of the shadow on the toolbars, but
        # they are read-only style properties.
        tb.set_style(gtk.TOOLBAR_ICONS)
        tb.set_icon_size(gtk.ICON_SIZE_SMALL_TOOLBAR)
        button = cls._actions.get_action('theme-new').create_tool_item()
        button.set_is_important(True)
        tb.add(button)
        button = cls._actions.get_action('theme-edit').create_tool_item()
        button.set_is_important(True)
        tb.add(button)
        button = cls._actions.get_action('theme-delete').create_tool_item()
        button.set_is_important(True)
        tb.add(button)
        return tb


class CellRendererTheme(gtk.GenericCellRenderer):
    "A theme preview cell renderer."
    __gproperties__ = {
                "theme": (gobject.TYPE_PYOBJECT, "Theme",
                "Theme", gobject.PARAM_READWRITE),
        }
    def __init__(self):
        self.__gobject_init__()
        self.theme = None
        self.xpad = 2
        self.ypad = 2
        self.xalign = 0.5
        self.yalign = 0.5
        self.active = 0
        self._pm = {}
    
    def _get_pixmap(self, window, size):
        "Render to an offscreen pixmap."
        global _example_slide
        if self.theme.is_builtin():
            fname = '_builtin_' + re.sub('[^a-z]+','_',self.theme.meta['title'].lower()).rstrip('_')
        else:
            fname = os.path.basename(os.path.splitext(self.theme.filename)[0])
        fname += '.%s.png' % 'x'.join(map(str, size))
        if fname in self._pm:
            return self._pm[fname]
        
        exposong.log.info('Generating theme thumbnail "%s".', fname)
        width, height = size
        
        self._pm[fname] = gtk.gdk.Pixmap(window, width, height)
        
        cache_dir = os.path.join(DATA_PATH, ".cache", "theme")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        cpath = os.path.join(cache_dir, fname)
        
        ccontext = self._pm[fname].cairo_create()
        if os.path.exists(cpath):
            # Load the image from memory, or disk if available
            pb = pb_new(cpath)
            ccontext.set_source_pixbuf(pb, 0, 0)
            ccontext.paint()
        else:
            scrsize = exposong.screen.screen.get_size()
            bounds = (0, 0, scrsize[0] / UNSCALE, scrsize[1] / UNSCALE)
            ccontext.scale(float(width) / scrsize[0] * UNSCALE,
                           float(height) / scrsize[1] * UNSCALE)
            if _example_slide is None:
                _example_slide = _ExampleSlide()
            self.theme.render(ccontext, bounds, _example_slide)
            # Save the rendered image to cache
            pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, width,
                                height)
            pb.get_from_drawable(self._pm[fname], self._pm[fname].get_colormap(),
                                 0, 0, 0, 0, width, height)
            pb.save(cpath, "png")
        return self._pm[fname]

    def on_render(self, window, widget, background_area, cell_area, expose_area,
               flags):
        "Display the theme preview."
        global _example_slide
        if not self.theme:
            return
        
        cell_position = list(self.on_get_size(widget, cell_area))
        cell_position[2] -= self.xpad*2
        cell_position[3] -= self.ypad*2
        x_offset, y_offset, width, height = cell_position
        if width <= 0 or height <= 0:
            return
        
        pm = self._get_pixmap(window, cell_position[2:4])
        scrsize = exposong.screen.screen.get_size()
        window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL],
                             pm, 0, 0, cell_area.x + x_offset,
                             cell_area.y + y_offset, width, height)
    
    def on_get_size(self, widget, cell_area):
        "Return the widgets size and position."
        calc_width = self.xpad * 2 + CELL_HEIGHT * exposong.screen.screen.get_aspect()
        calc_height = self.ypad * 2 + CELL_HEIGHT
        
        if cell_area:
            x_offset = self.xalign * (cell_area.width - calc_width) + self.xpad
            x_offset = max(x_offset, 0)
            y_offset = self.yalign * (cell_area.height - calc_height) + self.ypad
            y_offset = max(y_offset, 0)
        else:
            x_offset = self.xpad
            y_offset = self.ypad
        
        return int(x_offset), int(y_offset), int(calc_width), int(calc_height)
    
    # GObject Functions
    def do_set_property(self, pspec, value):
        setattr(self, pspec.name, value)
    
    def do_get_property(self, pspec):
        return getattr(self, pspec.name)
gobject.type_register(CellRendererTheme)

class _ExampleSlide(object):
    """
    A slide to draw as an example for the theme selection widget.
    """
    def __init__(self):
        object.__init__(self)
        self.body = [
                exposong.theme.Text('\n'.join([
                    'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'
                    'Phasellus magna eros, congue vel euismod ut, suscipit nec sapien.'
                    'Vestibulum vel est augue, quis viverra elit.'
                    'Sed quis arcu sit amet dui lobortis accumsan sed eget tellus.'
                    'Sed elit est, suscipit sit amet euismod quis, placerat ac neque.'
                    'Maecenas ac diam porttitor sem porttitor dictum.']),
                    pos=[0.0, 0.0, 1.0, 1.0], margin=10,
                    align=exposong.theme.CENTER, valign=exposong.theme.MIDDLE),
                ]
        self.foot = []

    def get_body(self):
        return self.body
    
    def get_footer(self):
        return self.foot
    
    def get_slide(self):
        return NotImplemented

