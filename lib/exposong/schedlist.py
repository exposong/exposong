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
The ScheduleList class provides a list of builtin and custom schedules that the
user can select.
"""

import gtk
import gtk.gdk
import gobject
import os

import exposong.main
import exposong._hook
import exposong.preslist
import exposong.schedule
from exposong import DATA_PATH
from exposong import statusbar

schedlist = None
DRAGDROP_SCHEDULE = [("text/treeview-path", gtk.TARGET_SAME_APP, 4121)]

class ScheduleList(gtk.TreeView, exposong._hook.Menu, exposong._hook.Toolbar):
    '''
    A TreeView of presentation schedules.
    '''
    def __init__(self):
        "Initialize the interface of the schedule."
        gtk.TreeView.__init__(self)
        self.set_size_request(200, 80)
        #Columns: Schedule, Name, Sort, is_separator
        self.model = gtk.TreeStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING,
                                   gobject.TYPE_STRING, gobject.TYPE_BOOLEAN)
        self.model.set_sort_column_id(2, gtk.SORT_ASCENDING)
        self.set_model(self.model)
        self.set_enable_search(False)
        self.set_headers_visible(False)
        self.set_row_separator_func(self._row_separator)
        
        sched_rend = gtk.CellRendererText()
        column = gtk.TreeViewColumn( _("Schedules"), sched_rend, text=1)
        
        sched_rend.connect("editing-started",
                exposong.main.main.disable_shortcuts)
        sched_rend.connect("editing-canceled",
                exposong.main.main.enable_shortcuts)
        sched_rend.connect("edited", exposong.main.main.enable_shortcuts)
        sched_rend.connect("edited", self._rename_schedule)
        column.set_resizable(False)
        column.set_cell_data_func(sched_rend, self._cell_data_func)
        self.append_column(column)
        self.get_selection().connect("changed", self._on_schedule_activate)
        
        self.enable_model_drag_dest(DRAGDROP_SCHEDULE, gtk.gdk.ACTION_DEFAULT)
        self.connect("button-release-event", self._on_rt_click)
        self.connect("drag-drop", self._on_pres_drop)
        self.connect("drag-data-received", self._on_sched_drag_received)
        #self.set_drag_dest_row((1,), gtk.TREE_VIEW_DROP_INTO_OR_BEFORE)

    def append(self, parent, row, sort=None):
        'Add an item to the list.'
        if isinstance(row, exposong.schedule.Schedule):
            if sort is None:
                sort = row.title
            else:
                sort = "%03u" % sort
            ret = self.model.append(parent, (row, row.title, sort, False))
        elif isinstance(row, tuple):
            ret = self.model.append(parent, row)
        elif not row: #Separator
            return self.model.append(parent, (None, None, sort, True))
        else:
            exposong.log.warning("Schedule cannot append this item: %r" % row)
            return
        self._add_to_schedule_menu()
        return ret
    
    def remove(self, item):
        'Remove the item from the model.'
        model = self.get_model()
        itr = model.iter_children(self.custom_schedules)
        while model.get_value(itr, 0).filename != item.filename:
            itr = model.iter_next(itr)
        self.get_model().remove(itr)
        self._add_to_schedule_menu()
    
    def get_active_item(self):
        'Get the currently selected Schedule.'
        (model, s_iter) = self.get_selection().get_selected()
        if s_iter:
            return model.get_value(s_iter, 0)
        else:
            return False
    
    def has_selection(self):
        'Returns if an item is selected.'
        return self.get_selection().count_selected_rows() > 0
    
    def _on_schedule_activate(self, *args):
        'Change the presentation list to the current schedule.'
        preslist = exposong.preslist.preslist
        if self.has_selection():
            sched = self.get_active_item()
            if isinstance(sched, exposong.schedule.Schedule):
                preslist.set_model(sched.get_model())
                preslist.columns_autosize()
                if sched.is_reorderable():
                    preslist.enable_model_drag_dest(DRAGDROP_SCHEDULE,
                                                    gtk.gdk.ACTION_DEFAULT)
                else:
                    preslist.unset_rows_drag_dest()
        try:
            enable = isinstance(sched, exposong.schedule.Schedule)\
                     and not sched.builtin
        except UnboundLocalError:
            enable = False

        self._actions.get_action("sched-rename").set_sensitive(enable)
        self._actions.get_action("sched-delete").set_sensitive(enable)
        
        preslist.get_model().connect("row-changed", preslist._on_pres_added)
    
    def _on_sched_delete(self, action):
        'Delete the selected schedule.'
        item = self.get_active_item()
        if not item or item.builtin:
            return False
        win = self
        while not isinstance(win, gtk.Window):
            win = win.get_parent()
        dialog = gtk.MessageDialog(win, gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
                                   _('Are you sure you want to delete "%s"?') %
                                   item.title)
        dialog.set_title( _("Delete Schedule?") )
        resp = dialog.run()
        dialog.hide()
        if resp == gtk.RESPONSE_YES:
            exposong.log.info('Deleting custom schedule "%s".', item.title)
            if item.filename and os.path.isfile(item.filename):
                os.remove(os.path.join(DATA_PATH, "sched",item.filename))
            self.remove(item)
            self.set_cursor((0,))
    
    def _on_pres_drop(self, treeview, context, x, y, timestamp):
        'Makes sure that the schedule was dropped on a custom schedule.'
        drop_info = treeview.get_dest_row_at_pos(x, y)
        if drop_info:
            path, position = drop_info
            model = treeview.get_model()
            val = model.get_value(model.get_iter(path), 0)
            if val and not val.builtin:
                return
        return True
    
    @staticmethod
    def _on_sched_drag_received(treeview, context, x, y, selection, info, timestamp):
        'A presentation was dropped onto a schedule.'
        drop_info = treeview.get_dest_row_at_pos(x, y)
        if drop_info:
            model = treeview.get_model()
            path, position = drop_info
            
            pmodel = exposong.preslist.preslist.get_filter_model()
            pres = pmodel.get_value(pmodel.get_iter_from_string(selection.data),
                                   0).presentation
            sched = model.get_value(model.get_iter(path), 0)
            
            sched.append(pres)
            context.finish(True, False)
            msg = _('Added Presentation "%(presentation)s" to Schedule "%(schedule)s"')
            statusbar.statusbar.output(msg % {"presentation":pres.get_title(),
                                              "schedule": sched.title})
            exposong.log.info('Added Presentation "%s" to Schedule "%s"',
                              pres.get_title(), sched.title)
    
    def _on_new(self, *args):
        'Create a new schedule.'
        name = _("New Schedule")
        curnames = []
        itr = self.model.iter_children(self.custom_schedules)
        while itr:
            if self.model.get_value(itr, 1).startswith(name):
                curnames.append(self.model.get_value(itr, 1))
            itr = self.model.iter_next(itr)
        if len(curnames) == 0:
            name += " 1"
        else:
            name += " "+str(int(curnames[len(curnames)-1][-2:]) + 1)
        sched = exposong.schedule.Schedule(name, builtin=False)
        itrnew = self.append(self.custom_schedules, sched)
        exposong.log.info('Creating New Schedule "%s".', name)
        pathnew = self.model.get_path(itrnew)
        self.expand_to_path(pathnew)
        self.set_cursor(pathnew, self.get_column(0), True)
    
    def _on_rename(self, *args):
        'Rename an existing schedule.'
        (path, focus) = self.get_cursor()
        self.set_cursor(path, focus, True)
    
    def _cell_data_func(self, column, cell, model, iter1):
        'Set whether the cell is editable or not.'
        sched = model.get_value(iter1, 0)
        cell.set_property('editable',
                          isinstance(sched, exposong.schedule.Schedule)
                          and sched.builtin is False)
    
    def _row_separator(self, model, itr):
        "Determines wheter the current row should be a separator"
        return model.get_value(itr, 3)
    
    def _rename_schedule(self, text_rend, path, new_text):
        "Rename a schedule in the list and its filename."
        if len(new_text.strip()) == 0:
            return
        iter1 = self.model.get_iter(path)
        exposong.log.info('Renaming custom schedule "%s" to "%s".',
                          self.model.get_value(iter1, 0).title, new_text)
        self.model.get_value(iter1, 0).title = new_text
        self.model.set_value(iter1, 1, new_text)
        self.model.set_value(iter1, 2, new_text)
        self._add_to_schedule_menu()
    
    def _on_rt_click(self, widget, event):
        'The user right clicked in the schedule area.'
        if event.button == 3:
            if widget.get_active_item() and not widget.get_active_item().builtin:
                menu = gtk.Menu()
                menu.append(self._actions.get_action('sched-rename').create_menu_item())
                menu.append(self._actions.get_action('sched-delete').create_menu_item())
                menu.show_all()
                menu.popup(None, None, None, event.button, event.get_time())
    
    def get_add_sched_actions(self):
        'Returns the "Add to Schedule" Actions.'
        if hasattr(self, '_sched_actiongroup'):
            return self._sched_actiongroup.list_actions()
        return []
    
    def _add_to_schedule_menu(self):
        "Creates the context menu 'Add to Schedule'"
        if not hasattr(self, 'custom_schedules'):
            return False
        model = self.get_model()
        scheds = []
        itr = model.iter_children(self.custom_schedules)
        while itr:
            scheds.append((model.get_value(itr, 0), model.get_value(itr, 1)))
            itr = model.iter_next(itr)
        
        uimanager = exposong.main.main.uimanager
        
        if hasattr(self,'_sched_actiongroup'):
            uimanager.remove_action_group(self._sched_actiongroup)
            uimanager.remove_ui(self._sched_mergeid)
        
        self._sched_actiongroup = gtk.ActionGroup('addtosched')
        str_ = _("Add to Schedule %s")
        self._sched_actiongroup.add_actions(
                [('pres-add-%s' % s[1], None, s[1], None,
                 str_ %s[1], s[0].append_action) for s in scheds])
        
        uimanager.insert_action_group(self._sched_actiongroup)
        self._sched_mergeid = uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="Edit">
                    <menu action="edit-pres">
                            <menu action="pres-add-to-schedule">
                                %s
                            </menu>
                    </menu>
                </menu>
            </menubar>
            """ % '\n'.join(["<menuitem action='pres-add-%s' />" % s[1] for s in scheds])
            )
    
    @classmethod
    def merge_menu(cls, uimanager):
        "Create menu items."
        global schedlist
        cls._actions = gtk.ActionGroup('schedlist')
        cls._actions.add_actions([
                ('sched-new', gtk.STOCK_NEW, _("New Schedule"), "",
                        _("Create a new schedule"), schedlist._on_new),
                ('sched-rename', None, _("_Rename Schedule"), None,
                        _("Rename the selected schedule"), schedlist._on_rename),
                ('sched-delete', gtk.STOCK_DELETE, _("Delete Schedule"), None,
                        _("Delete the currently selected schedule"),
                        schedlist._on_sched_delete ),
                ])
        
        uimanager.insert_action_group(cls._actions, -1)
        uimanager.add_ui_from_string("""
                <menubar name="MenuBar">
                    <menu action="File">
                        <menu action="file-new">
                            <placeholder name="file-new-sched" >
                                <menuitem action='sched-new' position='bot' />
                            </placeholder>
                        </menu>
                    </menu>
                    <menu action="Edit">
                        <menu action="edit-schedule">
                            <menuitem action='sched-rename' />
                            <menuitem action='sched-delete' />
                        </menu>
                    </menu>
                </menubar>
                """)
        # unmerge_menu not implemented, because we will never uninstall this as
        # a module.
    
    @classmethod
    def merge_toolbar(cls, uimanager):
        'Merge new values with the uimanager'
        cls.tb_merge_id = uimanager.add_ui_from_string("""
            <toolbar name='Toolbar'>
                <placeholder name="file-new-sched">
                    <toolitem action='sched-new' />
                </placeholder>
            </toolbar>
            """)
