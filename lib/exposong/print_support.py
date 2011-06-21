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
import datetime
import locale
import pango

import exposong.preslist
import exposong.main
import exposong._hook

"""
Adds functionality to print a Song or a list of Songs
"""

_COLUMN_COUNT = 3

# TODO Multiple pages is not supported right now:
# http://library.gnome.org/devel/pygtk/stable/class-gtkprintoperation.html#method-gtkprintoperation--set-n-pages

class Print(exposong._hook.Menu):
    '''
    Print a song or a list of songs
    '''
    def __init__(self):
        pass
    
    def _get_page_setup(self):
        'Returns the PageSetup object to be used by all Pages'
        ps = gtk.PageSetup()
        ps.set_left_margin(20, gtk.UNIT_MM)
        ps.set_right_margin(20, gtk.UNIT_MM)
        ps.set_top_margin(20, gtk.UNIT_MM)
        ps.set_bottom_margin(20, gtk.UNIT_MM)
        return ps
    
    def print_presentation(self, *args):
        "Print a single presentation."
        if not exposong.preslist.preslist.get_active_item().can_print():
            # TODO Error Dialog
            return False
        print_op = gtk.PrintOperation()
        print_op.set_default_page_setup(self._get_page_setup())
        print_op.set_n_pages(1)
        print_op.connect("draw_page", self._presentation_markup)
        print_op.run(gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG, None)
    
    def _presentation_markup(self, operation=None, context=None, page_nr=None):
        "Create the page layout for a presentation."
        pres = exposong.preslist.preslist.get_active_item()
        markup = pres.get_print_markup()
        if markup == NotImplemented:
            return False
        
        page_width = context.get_width() * pango.SCALE
        page_height = context.get_height() * pango.SCALE
        self.pangolayout = context.create_pango_layout()
        self.pangolayout.set_width(int(page_width))
        self.pangolayout.set_indent(0)
        self.pangolayout.set_wrap(pango.WRAP_WORD)
        
        size = 12000
        self.pangolayout.set_markup(markup % {'fontsize': size})
        while self.pangolayout.get_size()[1] > page_height:
            size *= 0.95
            self.pangolayout.set_indent(-int(size / 1000 * pango.SCALE * 20))
            self.pangolayout.set_markup(markup % {'fontsize': int(size)})
        
        cairo_context = context.get_cairo_context()
        cairo_context.show_layout(self.pangolayout)
        return
    
    @classmethod
    def merge_menu(cls, uimanager):
        "Merge new values with the uimanager."
        self = cls()
        actiongroup = gtk.ActionGroup('print')
        actiongroup.add_actions([
                ('print-presentation', None,
                 _("_Print"),
                 None, None, self.print_presentation),
                ])
        
        action = actiongroup.get_action('print-presentation')
        exposong.preslist.preslist.get_selection().connect('changed',
                                                           self._print_pres_active,
                                                           action)
        uimanager.insert_action_group(actiongroup, -1)
        
        cls.menu_merge_id = uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="File">
                    <placeholder name="print">
                        <menuitem action="print-presentation" />
                    </placeholder>
                </menu>
            </menubar>
            """)
    
    @staticmethod
    def _print_pres_active(sel, action):
        "Is printing available for the selected item."
        if sel.count_selected_rows() > 0:
            (model, itr) = sel.get_selected()
            pres = model.get_value(itr, 0)
            if pres and pres.can_print():
                action.set_sensitive(True)
                return
        action.set_sensitive(False)
    
    @classmethod
    def unmerge_menu(cls, uimanager):
        'Remove merged items from the menu.'
        uimanager.remove_ui(cls.menu_merge_id)
