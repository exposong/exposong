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

import exposong.screen
import exposong.theme
from exposong import DATA_PATH
from exposong.config import config

themeselect = None
_example_slide = None
CELL_HEIGHT = 65
UNSCALE = 4


class ThemeSelect(gtk.ComboBox, object):
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
        task = self._load_themes()
        gobject.idle_add(task.next)
    
    def get_active(self):
        "Get the currently selected theme."
        itr = self.get_active_iter()
        if itr:
            return self.liststore.get_value(itr, 1)
    
    def _load_themes(self):
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
            exposong.log.info('Loading theme image "%s".',
                              filenm)
            theme = exposong.theme.Theme(path)
            itr = self.liststore.append([path, theme])
            if path == active or (active == None and path.endswith("/exposong.xml")):
                self.set_active_iter(itr)
            yield True
        yield False
    
    def _get_theme_title(self, column, cell, model, titer):
        ''
        path = model.get_value(titer, 0)
        if path:
            t = os.path.basename(path).rstrip('.xml')
            cell.set_property('text', t.title())
    
    def _on_change(self, combo):
        'A new image was selected.'
        itr = combo.get_active_iter()
        if itr:
            mod = combo.get_model()
            config.set("screen", "theme", mod.get_value(itr, 0))
            exposong.screen.screen.set_dirty()
            exposong.screen.screen.draw()


class CellRendererTheme(gtk.GenericCellRenderer):
    "A widget with a theme drawing."
    __gproperties__ = {
                "theme": (gobject.TYPE_PYOBJECT, "Theme",
                "Theme", gobject.PARAM_READWRITE),
        }
    def __init__(self):
        self.__gobject_init__()
        self.theme = None
        self.xpad = 2
        self.ypad = 8
        self.xalign = 0.5
        self.yalign = 0.5
        self.active = 0
    
    def on_render(self, window, widget, background_area, cell_area, expose_area,
               flags):
        ""
        global _example_slide
        if not self.theme:
            return
        x_offset, y_offset, width, height = self.on_get_size(widget, cell_area)
        width -= self.xpad*2
        height -= self.ypad*2
        
        if width <= 0 or height <= 0:
            return
        
        ccontext = window.cairo_create()
        size = exposong.screen.screen.get_size()
        ccontext.scale(float(width) / size[0] * UNSCALE,
                       float(height) / size[1] * UNSCALE)
        bounds = ((cell_area.x + x_offset) * size[0] / float(width) / UNSCALE,
                  (cell_area.y + y_offset) * size[1] / float(height) / UNSCALE,
                  size[0] / UNSCALE, size[1] / UNSCALE)
        if _example_slide is None:
            _example_slide = _ExampleSlide()
        self.theme.render(ccontext, bounds, _example_slide)
    
    def on_get_size(self, widget, cell_area):
        ""
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
