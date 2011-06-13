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
The SlideList class displays the slides for the currently select presentation.
"""

import gtk
import gobject

import exposong.screen
import exposong.statusbar
from exposong import config

slidelist = None #will hold instance of SlideList
slide_scroll = None

class SlideList(gtk.TreeView, exposong._hook.Menu):
    '''
    The slides of a presentation.
    '''
    def __init__(self):
        "Create the interface."
        self.pres = None
        self.pres_type = None
        
        # Used to go to the previous (-1) / next (1) pres when reaching the last slide
        # See check_open_next_pres()
        self.__pres_mv = 0
        # Used to stop or reset the timer if the presentation or slide changes.
        self.__timer = 0

        gtk.TreeView.__init__(self)
        self.set_size_request(250, -1)
        self.set_enable_search(False)
        
        self.column1 = gtk.TreeViewColumn(_("Slides"))
        self.column1.set_resizable(False)
        self.append_column(self.column1)
        
        self.set_model(gtk.ListStore(gobject.TYPE_PYOBJECT, #Slide object
                                     gobject.TYPE_STRING))  #Slide markup
        self.get_selection().connect("changed", self._on_slide_activate)
    
    def set_presentation(self, pres):
        'Set the active presentation.'
        self.pres = pres
        slist = self.get_model()
        slist.clear()
        
        if pres is None:
            return
        
        self.set_model(slist)
        exposong.log.debug('Activating "%s" %s presentation.',
                           pres.get_title(), pres.get_type())
        if not hasattr(self, 'pres_type') or\
                self.pres_type is not pres.get_type():
            self.pres_type = pres.get_type()
            pres.slide_column(self.column1)
        
        if config.config.get('songs', 'show_in_order') == "True"\
                and pres.get_type() == "song":
            slides = pres.get_slides_in_order()
        else:
            slides = pres.get_slide_list()
        for slide in slides:
            slist.append(slide)
        
        if pres.get_type() == "song" and config.config.get('songs', 'title_slide') == "True":
            slist.insert(0,pres.get_title_slide())
        
        self.__timer += 1
        men = slist.get_iter_first() is not None
        self._actions.get_action("pres-slide-next").set_sensitive(men)
        self._actions.get_action("pres-slide-prev").set_sensitive(men)
    
    def update(self):
        '''When something in the presentation has changed, reset the slidelist and
        activate the slide that was active before'''
        (model, itr) = self.get_selection().get_selected()
        slide = None
        if itr:
            slide = model.get_value(itr,0)
            p = model.get_path(itr)
        
        self.set_presentation(self.pres)
        
        if slide:
            #Try to activate the same slide as before
            for row in model:
                if slide == row[0]:
                    p = row.path
                    break
            self.set_cursor(p)
    
    def get_active_item(self):
        'Return the selected `Slide` object.'
        (model, s_iter) = self.get_selection().get_selected()
        if s_iter:
            return model.get_value(s_iter, 0)
        else:
            return False
    
    def _move_to_slide(self, mv):
        'Move to the slide at mv.'
        (model, itr) = self.get_selection().get_selected()
        if itr:
            cur = int(model.get_string_from_iter(itr))
        else:
            cur = -1
        self.to_slide(cur+mv)
    
    def prev_slide(self, *args):
        'Move to the previous slide.'
        return self._move_to_slide(-1)
    
    def next_slide(self, *args):
        'Move to the next slide.'
        return self._move_to_slide(1)
    
    def to_slide(self, slide_num):
        'Move to the slide at slide_num'
        model = self.get_model()
        if slide_num < 0:
            slide_num = 0
        itr = model.iter_nth_child(None, slide_num)
        if itr:
            selection = self.get_selection()
            selection.select_iter(itr)
            self.scroll_to_cell(model.get_path(itr))
        self.check_open_pres(slide_num)
    
    def check_open_pres(self, cur_slide):
        '''Activates the next/previous presentation if:
         * The user presses the PgUp/PgDn key at the beginning/end of the list twice
         * The schedule is a user-defined one
         * The current presentation is not the last respectively the first one in the schedule.'''
        if exposong.schedlist.schedlist.get_active_item().builtin:
            return
        preslist = exposong.preslist.preslist
        if self.__pres_mv == 1 and not preslist.is_last_pres_active():
            preslist.next_pres()
            self.set_cursor(0)
        elif self.__pres_mv == -1 and not preslist.is_first_pres_active():
            preslist.prev_pres()
            self.set_cursor(0)
        
        if cur_slide == len(self.get_model()) and not preslist.is_last_pres_active():
            self.__pres_mv = 1
            exposong.statusbar.statusbar.output(
                _("Press %s once again to go to the next presentation")%_("Page Down"))
        elif cur_slide == 0 and not preslist.is_first_pres_active():
            self.__pres_mv = -1
            exposong.statusbar.statusbar.output(
                _("Press %s once again to go to the previous presentation")%_("Page Down"))
        else:
            self.__pres_mv = 0
    
    def _on_slide_activate(self, *args):
        'Present the selected slide to the screen.'
        exposong.screen.screen.draw()
        self.reset_timer()
    
    def reset_timer(self):
        'Restart the timer.'
        self.__timer += 1
        if self.pres and self.pres.get_timer():
            gobject.timeout_add(self.pres.get_timer()*1000, self._set_timer,
                                self.__timer)
    
    def _set_timer(self, t):
        'Starts the timer, or continues a current timer.'
        if t != self.__timer:
            return False
        if not exposong.screen.screen.is_running():
            return False
        if not self.next_slide(None) and self.pres.is_timer_looped():
            self.to_slide(0)
        # Return False, because the slide is activated, adding another timeout
        return False
    
    def toggle_show_order(self, widget):
        'Called when the "pres-show-in-order" action was toggled'
        config.config.set("songs", "show_in_order", str(widget.get_active()))
        self.update()
    
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
        cls._actions.add_toggle_actions([
            ('pres-show-in-order', None, _("Show Slides in Order"), None, None,
                        slidelist.toggle_show_order),
        ])
        
        uimanager.insert_action_group(cls._actions, -1)
        uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="Presentation">
                    <menuitem action="pres-slide-prev" position="bot" />
                    <menuitem action="pres-slide-next" position="bot" />
                    <menuitem action="pres-show-in-order" position="bot" />
                </menu>
            </menubar>
            """)
        cls._actions.get_action("pres-slide-next").set_sensitive(False)
        cls._actions.get_action("pres-slide-prev").set_sensitive(False)
        action = cls._actions.get_action('pres-show-in-order')
        if config.config.get('songs', 'show_in_order') == "True":
            action.set_active(True)
        exposong.preslist.preslist.get_selection().connect('changed',
                                cls._show_in_order_active, action)
        # unmerge_menu not implemented, because we will never uninstall this as
        # a module.
    
    @classmethod
    def get_order_checkbutton(cls):
        "Return the 'Use Order' checkbox"
        cb = gtk.CheckButton()
        cls._actions.get_action('pres-show-in-order').connect_proxy(cb)
        return cb
    
    @staticmethod
    def _show_in_order_active(sel, action):
        'Activates or deactives the "Show in Order" Checkbutton'
        if sel.count_selected_rows() > 0:
            (model, itr) = sel.get_selected()
            pres = model.get_value(itr, 0)
            if pres and pres.get_type() == 'song':
                action.set_sensitive(True)
                return
        action.set_sensitive(False)
