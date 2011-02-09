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
import gobject
import pango
import random

import exposong.screen

slidelist = None #will hold instance of SlideList
slide_scroll = None

class SlideList(gtk.TreeView, exposong._hook.Menu):
    '''
    Class to manipulate the text_area in the presentation program.
    '''
    def __init__(self):
        self.pres = None
        self.slide_order = ()
        self.slide_order_index = -1
        # Used to stop or reset the timer if the presentation or slide changes.
        self.__timer = 0

        gtk.TreeView.__init__(self)
        self.set_size_request(250, -1)
        self.set_enable_search(False)
        #self.set_headers_visible(False)
        
        self.column1 = gtk.TreeViewColumn( _("Slides"))
        self.column1.set_resizable(False)
        self.append_column(self.column1)
        
        self.set_model(gtk.ListStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING))
        self.get_selection().connect("changed", self._on_slide_activate)
    
    def set_presentation(self, pres):
        'Set the active presentation.'
        self.pres = pres
        slist = self.get_model()
        if pres is None:
            slist.clear()
        else:
            exposong.log.debug('Activating "%s" %s presentation.',
                               pres.get_title(), pres.get_type())
            slist.clear()
            if not hasattr(self, 'pres_type') or self.pres_type is not pres.get_type():
                self.pres_type = pres.get_type()
                pres.slide_column(self.column1, exposong.slidelist.slidelist)
            slist = self.get_model()
            for slide in pres.get_slide_list_with_title():
                slist.append(slide)
            self.slide_order = pres.get_order()
            self.slide_order_index = -1
            self.order_entry.set_text(pres.get_order_string())
        self.__timer += 1
        men = slist.get_iter_first() is not None
        self._actions.get_action("pres-slide-next").set_sensitive(men)
        self._actions.get_action("pres-slide-prev").set_sensitive(men)
    
    def get_active_item(self):
        'Return the selected `Slide` object.'
        (model, s_iter) = self.get_selection().get_selected()
        if s_iter:
            return model.get_value(s_iter, 0)
        else:
            return False
    
    def _move_to_slide(self, mv):
        'Move to the slide at mv. This ignores slide_order_index.'
        order_index = self.slide_order_index
        if self.slide_order_index == -1 and\
                self.get_selection().count_selected_rows() > 0:
            (model,itr) = self.get_selection().get_selected()
            cur = model.get_string_from_iter(itr)
            cnt = 0
            for o in self.slide_order:
                if o == int(cur):
                    if len(self.slide_order) > cnt+mv and cnt+mv > 0:
                        self.to_slide(self.slide_order[cnt+mv])
                        self.slide_order_index = cnt+mv
                        return True
                    else:
                        return False
                cnt += 1
        if order_index == self.slide_order_index and \
                len(self.slide_order) > order_index+mv and order_index+mv >= 0:
            self.to_slide(self.slide_order[order_index + mv])
            self.slide_order_index = order_index + mv
            return True
        return False
    
    def prev_slide(self, *args):
        'Move to the previous slide.'
        return self._move_to_slide(-1)
    
    def next_slide(self, *args):
        'Move to the next slide.'
        return self._move_to_slide(1)
    
    def to_start(self):
        'Reset to the first slide.'
        self.slide_order_index = 0
        if len(self.slide_order):
            self.to_slide(self.slide_order[0])
            return True
        return False
    
    def to_slide(self, slide_num):
        model = self.get_model()
        itr = model.iter_nth_child(None, slide_num)
        if itr:
            selection = self.get_selection()
            selection.select_iter(itr)
            self.scroll_to_cell(model.get_path(itr))
    
    def _on_slide_activate(self, *args):
        'Present the selected slide to the screen.'
        exposong.screen.screen.draw()
        self.slide_order_index = -1
        
        self.reset_timer()
    
    def reset_timer(self):
        'Restart the timer.'
        self.__timer += 1
        if self.pres and self.pres.get_timer():
            gobject.timeout_add(self.pres.get_timer()*1000, self._set_timer,
                                self.__timer)
    
    def _set_timer(self, t):
        'Starts the timer, or continues a current timer.'
        if t <> self.__timer:
            return False
        if not exposong.screen.screen.is_running():
            return False
        if not self.next_slide(None) and self.pres.is_timer_looped():
            self.to_start()
        # Return False, because the slide is activated, adding another timeout
        return False
    
    @classmethod
    def merge_menu(cls, uimanager):
        'Merge new values with the uimanager.'
        global slidelist
        cls._actions = gtk.ActionGroup('slidelist')
        cls._actions.add_actions([
                ('pres-slide-prev', None, _("Previous Slide"), "Page_Up", None,
                        slidelist.prev_slide),
                ('pres-slide-next', None, _("Next Slide"), "Page_Down", None,
                        slidelist.next_slide),
                ])
        
        uimanager.insert_action_group(cls._actions, -1)
        uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="Presentation">
                    <menuitem action="pres-slide-prev" position="bot" />
                    <menuitem action="pres-slide-next" position="bot" />
                </menu>
            </menubar>
            """)
        cls._actions.get_action("pres-slide-next").set_sensitive(False)
        cls._actions.get_action("pres-slide-prev").set_sensitive(False)
        # unmerge_menu not implemented, because we will never uninstall this as
        # a module.
        
    @classmethod
    def get_slide_control_bar(cls):
        "Return the slide control bar widget."
        h = gtk.HBox()
        #cls.checkbox_use_order = gtk.CheckButton("Use Order")
        #h.pack_start(cls.checkbox_use_order)
        button = gtk.Button("<")
        cls._actions.get_action('pres-slide-prev').connect_proxy(button)
        h.pack_start(button)
        cls.order_entry = gtk.Entry()
        cls.order_entry.set_editable(False)
        cls.order_entry.set_property("can-focus", False)
        h.pack_start(cls.order_entry)
        button = gtk.Button(">")
        cls._actions.get_action('pres-slide-next').connect_proxy(button)
        h.pack_start(button)
        return h
