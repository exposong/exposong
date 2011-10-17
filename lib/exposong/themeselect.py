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
A widget to change the currently active theme.
"""

import gobject
import gtk
import os, os.path
import pango
import re
from gtk.gdk import pixbuf_new_from_file as pb_new

import exposong.main
import exposong.screen
import exposong.theme
import exposong.exampleslide
from exposong import themeeditor
from exposong import DATA_PATH
from exposong.config import config

themeselect = None
SCALED_HEIGHT = 600
CELL_HEIGHT = 65
CELL_ASPECT = 16.0 / 9


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
        themerend.slide = exposong.exampleslide._ExampleTextSlide()
        self.pack_start(themerend, False)
        self.add_attribute(themerend, 'theme', 1)
        textrend = gtk.CellRendererText()
        textrend.set_property("ellipsize", pango.ELLIPSIZE_END)
        self.pack_start(textrend, True)
        self.set_cell_data_func(textrend, self._get_theme_title)
        self.connect("changed", self._theme_changed)
        
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
        themes['_builtin_white'].backgrounds.append(
                exposong.theme.ColorBackground("#fff"))
        themes['_builtin_white'].body.color = '#000'
        themes['_builtin_white'].body.shadow_color = '#fff'
        themes['_builtin_white'].footer.color = '#000'
        themes['_builtin_white'].footer.shadow_color = '#fff'
        
        themes['_builtin_blue_gradient'] = exposong.theme.Theme(builtin=True)
        themes['_builtin_blue_gradient'].meta['title'] = _('ES Blue')
        themes['_builtin_blue_gradient'].body.outline_color = '#000'
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
        size = (int(CELL_HEIGHT * CELL_ASPECT),
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
    
    def _theme_changed(self, combo):
        "A new theme was selected."
        itr = combo.get_active_iter()
        if itr:
            mod = combo.get_model()
            config.set("screen", "theme", mod.get_value(itr, 0))
            t = mod.get_value(itr, 1).get_title()
            exposong.log.info('Changing theme to "%s".',t)
            self.set_tooltip_text(t)
            exposong.screen.screen.draw()
        self._set_menu_items_disabled()
    
    def new_theme(self, *args):
        editor = themeeditor.ThemeEditor(exposong.main.main, exposong.theme.Theme())
        editor.connect('destroy', self._add_theme)
        
    def _add_theme(self, editor):
        if editor.theme.filename: #Not cancelled
            itr = self.liststore.append([editor.theme.filename, editor.theme])
            self.set_active_iter(itr)
            self._load_theme_thumbs()
        
    def _edit_theme(self, *args):
        theme = self.get_active()
        if theme.is_builtin():
            raise Exception("Builtin themes cannot be modified.")
        editor = themeeditor.ThemeEditor(exposong.main.main, theme)
        editor.connect('destroy', self._update_theme, theme)
    
    def _update_theme(self, editor, theme, *args):
        self._delete_theme_thumb(theme)
        exposong.screen.screen.draw()
    
    def _delete_theme(self, *args):
        theme = self.get_active()
        msg = _('Are you sure you want to delete the theme "%s"?')
        dialog = gtk.MessageDialog(exposong.main.main, gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
                                   msg % theme.get_title())
        dialog.set_title(_("Delete Theme?"))
        resp = dialog.run()
        dialog.destroy()
        if resp == gtk.RESPONSE_YES:
            os.remove(os.path.join(DATA_PATH, 'theme', theme.filename))
            for bg in theme.backgrounds:
                if isinstance(bg, exposong.theme.ImageBackground):
                    os.remove(os.path.join(DATA_PATH, 'theme', 'res', bg.src))
            size = (int(CELL_HEIGHT * CELL_ASPECT), CELL_HEIGHT)
            self.get_cells()[0]._delete_pixmap(size)
            self.liststore.remove(self.get_active_iter())
            del theme
            self.set_active(0)
    
    def _delete_theme_thumb(self, theme):
        cell = self.get_cells()[0]
        cell.theme = theme
        size = (int(CELL_HEIGHT * CELL_ASPECT), CELL_HEIGHT)
        cell._get_pixmap(self.window, size, False)
    
    @classmethod
    def merge_menu(cls, uimanager):
        'Merge new values with the uimanager.'
        global themeselect
        
        cls._actions = gtk.ActionGroup('theme')
        cls._actions.add_actions([
                ('theme-new', gtk.STOCK_NEW, _('New Theme'), "",
                        _("Create a new theme using the Theme Editor"), themeselect.new_theme),
                ('theme-edit', gtk.STOCK_EDIT, _('Edit Theme'), None,
                        _("Edit the current theme"), themeselect._edit_theme),
                ('theme-delete', gtk.STOCK_DELETE, _("Delete Theme"), None,
                        _('Delete the current theme'), themeselect._delete_theme),
                ])
        
        uimanager.insert_action_group(cls._actions, -1)
        uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="File">
                    <menu action="file-new">
                        <placeholder name="file-new-theme">
                            <menuitem action="theme-new" />
                        </placeholder>
                    </menu>
                </menu>
                <menu action="Edit">
                    <menu action="edit-theme">
                        <menuitem action="theme-edit" position="bot" />
                        <menuitem action="theme-delete" position="bot" />
                    </menu>
                </menu>
            </menubar>
            """)
        # unmerge_menu not implemented, because we will never uninstall this as
        # a module.
    
    def _set_menu_items_disabled(self):
        'Disable buttons if the presentation is not shown.'
        enabled = False
        if self.get_active() is not None:
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
                "slide": (gobject.TYPE_PYOBJECT, "Slide",
                "Slide", gobject.PARAM_READWRITE),
        }
    def __init__(self):
        self.__gobject_init__()
        self.height = CELL_HEIGHT
        self.theme = None
        self.slide = None
        self.can_cache = True
        self.xpad = 2
        self.ypad = 2
        self.xalign = 0.5
        self.yalign = 0.5
        self.active = 0
        self._pm = {}
    
    def _delete_pixmap(self, size):
        'Deletes the cached image when the theme was deleted.'
        fname  = self._get_pixmap_name(size)
        if fname in self._pm:
            del self._pm[fname]
        pm = os.path.join(DATA_PATH, '.cache', 'theme', fname)
        if os.path.exists(pm):
            os.remove(pm)
    
    def _get_pixmap_name(self, size):
        'Return the filename of the pixmap (includes size)'
        if self.theme.is_builtin():
            fname = '_builtin_' + re.sub('[^a-z]+','_',self.theme.meta['title'].lower()).rstrip('_')
        else:
            fname = os.path.basename(os.path.splitext(self.theme.filename)[0])
        if self.slide is None:
            return None
        fname += '.%s' % self.slide.id
        fname += '.%s.png' % 'x'.join(map(str, size))
        return fname
    
    def _get_pixmap(self, window, size, cache=True):
        "Render to an offscreen pixmap."
        cache = cache and self.can_cache
        if not cache:
            self._delete_pixmap(size)
        fname = self._get_pixmap_name(size)
        if not fname:
            return None
        if cache and fname in self._pm:
            return self._pm[fname]
        
        width, height = size
        
        self._pm[fname] = gtk.gdk.Pixmap(window, width, height)
        
        cache_dir = os.path.join(DATA_PATH, ".cache", "theme")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        cpath = os.path.join(cache_dir, fname)
        
        ccontext = self._pm[fname].cairo_create()
        if cache and os.path.exists(cpath):
            # Load the image from memory, or disk if available
            exposong.log.debug('Loading theme thumbnail "%s".', fname)
            pb = pb_new(cpath)
            ccontext.set_source_pixbuf(pb, 0, 0)
            ccontext.paint()
        else:
            exposong.log.debug('Generating theme thumbnail "%s".', fname)
            bounds = (0, 0, SCALED_HEIGHT * CELL_ASPECT, SCALED_HEIGHT)
            ccontext.scale(float(width) / bounds[2],
                           float(height) / bounds[3])
            self.theme.render(ccontext, bounds, self.slide)
            if self.can_cache:
                # Save the rendered image to cache
                pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, width,
                                    height)
                pb.get_from_drawable(self._pm[fname],
                                     self._pm[fname].get_colormap(), 0, 0, 0, 0,
                                     width, height)
                pb.save(cpath, "png")
        return self._pm[fname]

    def on_render(self, window, widget, background_area, cell_area, expose_area,
               flags):
        "Display the theme preview."
        if not self.theme:
            return False
        
        cell_position = list(self.on_get_size(widget, cell_area))
        cell_position[2] -= self.xpad*2
        cell_position[3] -= self.ypad*2
        x_offset, y_offset, width, height = cell_position
        if width <= 0 or height <= 0:
            return
        
        pm = self._get_pixmap(window, cell_position[2:4])
        if pm is None:
            return False
        window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL],
                             pm, 0, 0, cell_area.x + x_offset,
                             cell_area.y + y_offset, width, height)
    
    def on_get_size(self, widget, cell_area):
        "Return the widgets size and position."
        calc_width = int(self.xpad * 2 + self.height * CELL_ASPECT)
        calc_height = self.ypad * 2 + self.height
        
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

