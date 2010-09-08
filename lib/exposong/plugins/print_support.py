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
import datetime
import locale

from exposong.plugins import _abstract, Plugin
import exposong.preslist
import exposong.application

"""
Adds functionality print a song or a list of Songs
"""

information = {
    'name': _("Print"),
    'description': __doc__,
    'required': False,
}


class Print(Plugin, _abstract.Menu):
    '''
    Print a song or a list of songs
    '''
    def __init__(self):
        pass
    
    def print_presentation(self, *args):
        "Print a single presentation."
        # TODO This button should be enabled or disabled based on preslist
        # selection
        if not exposong.preslist.preslist.get_active_item():
            msg = _('Please select the presentation you want to print.')
            dialog = gtk.MessageDialog(exposong.application.main,
                                       gtk.DIALOG_MODAL, gtk.MESSAGE_WARNING,
                                       gtk.BUTTONS_OK, msg)
            dialog.set_title( _("Select Presentation") )
            resp = dialog.run()
            dialog.destroy()
            return
        
        print_op = gtk.PrintOperation()
        print_op.set_n_pages(1)
        print_op.connect("draw_page", self._presentation_markup)
        res = print_op.run(gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG, None)
    
    def _presentation_markup(self, operation=None, context=None, page_nr=None):
        "Create the page layout for a presentation."
        pres = exposong.preslist.preslist.get_active_item()
        markup = "<span face='sans' weight='bold' size='large'>%s</span>"%pres.get_title()
        markup += "\n\n\n"
        for slide in pres.get_slide_list():
            markup += "<span weight='bold' face='sans' size='medium'>%s</span>\n"\
                                %slide[0].get_title()
            markup += "<span face='sans'>%s</span>\n\n"%slide[0].get_text()
        
        #TODO: Handle too long lines
        
        self.pangolayout = context.create_pango_layout()
        self.pangolayout.set_markup(markup)
        cairo_context = context.get_cairo_context()
        cairo_context.show_layout(self.pangolayout)
        return
    
    def print_songlist(self, *args):
        "Print a list of all songs"
        print_op = gtk.PrintOperation()
        print_op.set_n_pages(1)
        print_op.connect("draw_page", self._songlist_markup)
        res = print_op.run(gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG, None)
    
    def _songlist_markup(self, operation=None, context=None, page_nr=None):
        'Create the page layout for the songlist'
        library = exposong.application.main.library
        songs = ""
        for item in library:
            if item[0].get_type() == "lyric":
                songs += "%s\n"%item[0].title
        
        markup = """<span face='sans' size='large' weight='bold'>%(title)s</span>
<span face='sans' size='x-small'>%(date)s</span>\n\n
<span face='sans 'size='small'>%(text)s</span>
        """ %{'title' : _("Alphabetical list of Songs"),
                    'date'  : datetime.datetime.now().strftime(
                              locale.nl_langinfo(locale.D_FMT)),
                    'text'  : songs}
        
        #TODO: Multiples Columns, pango cannot do it
        
        self.pangolayout = context.create_pango_layout()
        self.pangolayout.set_markup(markup)
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
                 _("_Current Presentation"),
                 None, None, self.print_presentation),
                ('print-songlist', None, _("_List of all Songs"), None,
                        None, self.print_songlist)
                ])
        uimanager.insert_action_group(actiongroup, -1)
        
        #Had to use position='top' to put them above "Quit"
        cls.menu_merge_id = uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="File">
                    <menu action="file-print">
                        <menuitem action="print-presentation" />
                        <menuitem action="print-songlist" />
                    </menu>
                </menu>
            </menubar>
            """)
    
    @classmethod
    def unmerge_menu(cls, uimanager):
        'Remove merged items from the menu.'
        uimanager.remove_ui(cls.menu_merge_id)
