#! /usr/bin/env python
#
# Copyright (C) 2008 Fishhookweb.com
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
from exposong.plugins import _abstract, Plugin

"""
Adds functionality to move schedules, or a full library to another exposong
instance.
"""

information = {
  'name': _("Export/Import Functions"),
  'description': __doc__,
  'required': False,
}

class Export(Plugin, _abstract.Menu, gtk.FileChooserDialog):
  '''
  Export to file.
  '''
  def __init__(self, parent=None):
    gtk.FileChooserDialog.__init__(self, "Export", parent,
        gtk.FILE_CHOOSER_ACTION_SAVE, None, None)
  
  def merge_menu(self, uimanager):
    'Merge new values with the uimanager.'
    actiongroup = gtk.ActionGroup('export-import')
    actiongroup.add_actions([('import', None, _("_Import"), None,
            _("Import a schedule or full library."), None),
        ('export-sched', None, _("_Export Schedule"), None,
            None),
        ('export-lib', None, _("Export _Library"), None,
            None)])
    uimanager.insert_action_group(actiongroup, -1)
    
    #Had to use position='top' to put them above "Quit"
    self.menu_merge_id = uimanager.add_ui_from_string("""
      <menubar name="MenuBar">
        <menu action="File">
          <separator position="top" />
          <menuitem action="export-sched" position="top" />
          <menuitem action="export-lib" position="top" />
          <menuitem action="import" position="top" />
        </menu>
      </menubar>
      """)
  
  def unmerge_menu(self, uimanager):
    'Remove merged items from the menu.'
    uimanager.remove_ui(self.menu_merge_id)

