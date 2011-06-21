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
Manages the presentations from the current schedule.
"""

import os
import gtk
import gtk.gdk
import gobject
import pango

import exposong._hook
import exposong.slidelist
import exposong.schedlist
import exposong.main
from exposong import DATA_PATH, RESOURCE_PATH

# Will hold the PresList instance
preslist = None

class PresList(gtk.TreeView, exposong._hook.Menu):
    """
    Manage the presentation list from the currently selected schedule.
    """
    def __init__(self):
        "Create the presentation interface."
        gtk.TreeView.__init__(self)
        self.set_size_request(-1, 250)
        self.prev_selection = None
        
        pixbufrend = gtk.CellRendererPixbuf()
        textrend = gtk.CellRendererText()
        textrend.set_property("ellipsize", pango.ELLIPSIZE_END)
        column = gtk.TreeViewColumn( _("Presentations") )
        column.set_resizable(False)
        column.pack_start(pixbufrend, False)
        column.set_cell_data_func(pixbufrend, self._get_row_icon)
        column.pack_start(textrend, True)
        column.set_cell_data_func(textrend, self._get_row_text)
        column.set_property('spacing', 4)
        pixbufrend = gtk.CellRendererPixbuf()
        column.pack_start(pixbufrend, False)
        column.set_cell_data_func(pixbufrend, self._get_timer_icon)
        self.append_column(column)
        self.set_headers_clickable(False)
        self.get_selection().connect("changed", self.activate_pres)
        
        self.connect("button-release-event", self._on_pres_rt_click)
        self.connect("drag-data-get", self._on_drag_get)
        self.connect("drag-data-received", self._on_pres_drag_received)
        self.enable_model_drag_source(gtk.gdk.BUTTON1_MASK,
                exposong.schedlist.DRAGDROP_SCHEDULE,
                gtk.gdk.ACTION_DEFAULT | gtk.gdk.ACTION_MOVE)
        
    def _on_pres_added(self, model, path, itr):
        "Select the recently added schedule."
        self.set_cursor(path)
    
    def get_active_item(self):
        "Return the presentation of the currently selected item."
        (model, s_iter) = self.get_selection().get_selected()
        if s_iter:
            return model.get_value(s_iter, 0)
        else:
            return False
    
    def append(self, item):
        'Add a presentation to the list.'
        self.get_model().append((item, item.get_title(), item.get_type()))
    
    def remove(self, item):
        'Delete a presentation from the list.'
        model = self.get_model()
        iter1 = model.get_iter_first()
        while model.get_value(iter1, 0).filename != item.filename:
            iter1 = model.iter_next(iter1)
        self.get_model().remove(iter1)
    
    def has_selection(self):
        'Return true if an item is selected.'
        return bool(self.get_selection().count_selected_rows())
    
    def get_model(self):
        "Get the model (schedule) that contains the items."
        model = gtk.TreeView.get_model(self)
        if isinstance(model, (gtk.TreeModelFilter, gtk.TreeModelSort)):
            return model.get_model()
        return model
    
    def get_filter_model(self):
        'Return the filtered model if filter is active, else the unfiltered model.'
        return gtk.TreeView.get_model(self)
    
    def next_pres(self, *args):
        'Go to the next presentation.'
        selection = self.get_selection()
        (model, itr) = selection.get_selected()
        if itr:
            itr2 = model.iter_next(itr)
            if itr2:
                selection.select_iter(itr2)
                self.scroll_to_cell(model.get_path(itr2))
            else: #The last presentation is active.
                return False
        elif model.get_iter_first():
            selection.select_iter(model.get_iter_first())
            self.scroll_to_point(0,0)
        else:
            #No presentations available.
            return False
        self.activate_pres()
    
    def prev_pres(self, *args):
        'Go to the previous presentation.'
        (model, s_iter) = self.get_selection().get_selected()
        if s_iter:
            path = model.get_path(s_iter)
            if path[0] > 0:
                path = (path[0]-1,)
                self.set_cursor(path)
                self.scroll_to_cell(path)
    
    def activate_pres(self, *args):
        'Change the slides to the current presentation.'
        if self.prev_selection != None:
            self.prev_selection.presentation.on_deselect()
        if self.has_selection():
            exposong.slidelist.slidelist.set_presentation(
                    self.get_active_item().presentation)
            self.prev_selection = self.get_active_item()
            self.get_active_item().on_select()
        else:
            exposong.slidelist.slidelist.set_presentation(None)
            self.prev_selection = None
        
        exposong.slidelist.slide_scroll.emit('scroll-child', gtk.SCROLL_START, False)
        
        self._actions.get_action("pres-edit").set_sensitive(self.has_selection())
        pres_delete = self._actions.get_action("pres-delete")
        pres_remove = self._actions.get_action("pres-remove-from-schedule")
        pres_add = self._actions.get_action("pres-add-to-schedule")
        pres_delete.set_sensitive(self.has_selection() and self.get_model().builtin)
        pres_remove.set_sensitive(self.has_selection() and not self.get_model().builtin)
        pres_remove.set_visible(not self.get_model().builtin)
        pres_add.set_sensitive(self.has_selection())
        for action in exposong.schedlist.schedlist.get_add_sched_actions():
            action.set_sensitive(self.has_selection())
    
    def is_first_pres_active(self):
        'True if the currently activated presentation is the first one in the schedule'
        (model, s_iter) = self.get_selection().get_selected()
        if s_iter:
            if model.get_path(s_iter)[0] == 0:
                return True
        return False
    
    def is_last_pres_active(self):
        'True if the currently activated presentation is the last one in the schedule'
        (model, s_iter) = self.get_selection().get_selected()
        if s_iter:
            if model.get_path(s_iter)[0] == len(self.get_model())-1:
                return True
        return False
    
    def _on_pres_edit(self, *args):
        'Edit the presentation.'
        field = exposong.slidelist.slidelist.pres
        if not field:
            return False
        if field.edit():
            exposong.slidelist.slidelist.update()
    
    def _on_drag_get(self, treeview, context, selection, info, timestamp):
        'A presentation was dragged.'
        model, iter1 = treeview.get_selection().get_selected()
        selection.set('text/treeview-path', info,
                      model.get_string_from_iter(iter1))
    
    def _on_pres_drag_received(self, treeview, context, x, y, selection, info,
            timestamp):
        'A presentation was reordered.'
        drop_info = treeview.get_dest_row_at_pos(x, y)
        sched = self.get_model() #Gets the current schedule
        path_mv = int(selection.data)
        
        if drop_info:
            path_to, position = drop_info
            itr_to = sched.get_iter(path_to)
        else:
            # Assumes that if there's no drop info, it's at the end of the list
            path_to = path_mv + 1
            position = gtk.TREE_VIEW_DROP_BEFORE
            itr_to = None
        itr_mv = sched.get_iter(path_mv)
        
        if position is gtk.TREE_VIEW_DROP_AFTER or\
                position is gtk.TREE_VIEW_DROP_INTO_OR_AFTER:
            sched.move_after(itr_mv, itr_to)
        elif position is gtk.TREE_VIEW_DROP_BEFORE or\
                position is gtk.TREE_VIEW_DROP_INTO_OR_BEFORE:
            sched.move_before(itr_mv, itr_to)
        
        context.finish(True, False)

    def _on_pres_delete(self, *args):
        'Delete the selected presentation.'
        item = self.get_active_item()
        if not item:
            return False
        msg = _('Are you sure you want to delete "%s" from your library?')
        dialog = gtk.MessageDialog(exposong.main.main, gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
                                   msg % item.get_title())
        dialog.set_title( _("Delete Presentation?") )
        resp = dialog.run()
        dialog.destroy()
        if resp == gtk.RESPONSE_YES:
            item.on_delete()
            schmod = exposong.schedlist.schedlist.get_model()
            
            #Remove from builtin modules
            itr = schmod.get_iter_first()
            while itr:
                sched = schmod.get_value(itr, 0)
                if sched:
                    sched.remove_if(presentation=item.presentation)
                itr = schmod.iter_next(itr)
            
            #Remove from custom schedules
            itr = schmod.iter_children(exposong.schedlist.schedlist.custom_schedules)
            while itr:
                sched = schmod.get_value(itr, 0)
                sched.remove_if(presentation=item.presentation)
                itr = schmod.iter_next(itr)
            os.remove(os.path.join(DATA_PATH,"pres",item.filename))
            self.activate_pres()

    def _on_pres_remove_from_schedule(self, *args):
        'Remove the presentation from the current schedule.'
        sched, itr = self.get_selection().get_selected()
        if not itr or sched.builtin:
            return False
        sched.remove(itr)
    
    def _get_row_icon(self, column, cell, model, titer):
        'Returns the icon of the current presentation.'
        pres = model.get_value(titer, 0)
        cell.set_property('pixbuf', pres.get_icon())
    
    def _get_timer_icon(self, column, cell, model, titer):
        'Returns a timer icon if the timer is set.'
        if not hasattr(self, "_timer_icon"):
            fl = os.path.join(RESOURCE_PATH, 'timer.png')
            self._timer_icon = gtk.gdk.pixbuf_new_from_file_at_size(fl, 20, 14)
        pres = model.get_value(titer, 0)
        if pres.get_timer():
            cell.set_property('pixbuf', self._timer_icon)
        else:
            cell.set_property('pixbuf', None)
    
    def _get_row_text(self, column, cell, model, titer):
        'Returns the title of the current presentation.'
        pres = model.get_value(titer, 0)
        cell.set_property('text', pres.get_title())
    
    def _on_pres_rt_click(self, widget, event):
        'Display the context menu on right click.'
        if event.button != 3:
            return
        actions = self._actions
        menu = gtk.Menu()
        sch = actions.get_action('pres-add-to-schedule').create_menu_item()
        menu2 = gtk.Menu()
        sch.set_submenu(menu2)
        menu.append(sch)
        for action in exposong.schedlist.schedlist.get_add_sched_actions():
            menu2.append(action.create_menu_item())
        menu.append(actions.get_action('pres-edit').create_menu_item())
        menu.append(actions.get_action('pres-delete').create_menu_item())
        menu.append(actions.get_action('pres-remove-from-schedule').create_menu_item())
        menu.show_all()
        
        path = self.get_path_at_pos(int(event.x), int(event.y))
        if path is not None:
            menu.popup(None, None, None, event.button, event.get_time())
    
    @staticmethod
    def get_model_args():
        "Get the arguments for the model."
        return (gobject.TYPE_PYOBJECT,)
    
    @classmethod
    def merge_menu(cls, uimanager):
        "Create menu items."
        global preslist
        cls._actions = gtk.ActionGroup('preslist')
        cls._actions.add_actions([
                ('pres-add-to-schedule', gtk.STOCK_ADD, _("_Add to Schedule"),
                        None, _("Add the Selected Presentation to a Schedule"),
                        None),
                ('pres-edit', gtk.STOCK_EDIT, None, None,
                        _("Edit the currently selected presentation"),
                        preslist._on_pres_edit),
                ('pres-remove-from-schedule', gtk.STOCK_REMOVE,
                        _("_Remove from Schedule"), "Delete",
                        _("Remove the presentation from schedule"),
                        preslist._on_pres_remove_from_schedule),
                ('pres-delete', gtk.STOCK_DELETE, None, "Delete",
                        _("Delete the presentation"), preslist._on_pres_delete),
                ('pres-prev', None, _("Previous Presentation"), "<Ctrl>Page_Up",
                        None, preslist.prev_pres),
                ('pres-next', None, _("Next Presentation"), "<Ctrl>Page_Down",
                        None, preslist.next_pres),
                ])
        
        uimanager.insert_action_group(cls._actions, -1)
        uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="Edit">
                    <menu action="edit-pres">
                        <menuitem action="pres-edit" />
                        <menuitem action="pres-delete" />
                        <placeholder name="add-to-schedule" />
                        <menuitem action="pres-remove-from-schedule" />
                    </menu>
                </menu>
                <menu action="Presentation">
                    <placeholder name="pres-movement">
                        <menuitem action="pres-prev" position="bot" />
                        <menuitem action="pres-next" position="bot" />
                    </placeholder>
                </menu>

            </menubar>
            """)
        # unmerge_menu not implemented, because we will never uninstall this as
        # a module.
