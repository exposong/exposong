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
import gtk.gdk
import gobject
import xml.dom

import exposong.schedule
import exposong.preslist
import exposong.application
from glob import *
from exposong import DATA_PATH
from exposong import statusbar

schedlist = None
DRAGDROP_SCHEDULE = [("text/treeview-path", gtk.TARGET_SAME_APP, 4121)]

class ScheduleList(gtk.TreeView):
  '''
  A TreeView of presentation schedules.
  '''
  def __init__(self):
    gtk.TreeView.__init__(self)
    self.set_size_request(200, 190)
    #Columns: Schedule, Name
    self.model = gtk.TreeStore(gobject.TYPE_PYOBJECT, gobject.TYPE_STRING,
                               gobject.TYPE_STRING)
    self.model.set_sort_column_id(2, gtk.SORT_ASCENDING)
    self.set_model(self.model)
    self.set_enable_search(False)
    
    sched_rend = gtk.CellRendererText()
    column = gtk.TreeViewColumn( _("Schedule"), sched_rend, text=1)
    
    sched_rend.connect("editing-started",
        exposong.application.main.disable_shortcuts)
    sched_rend.connect("editing-canceled",
        exposong.application.main.enable_shortcuts)
    sched_rend.connect("edited", exposong.application.main.enable_shortcuts)
    sched_rend.connect("edited", self._rename_schedule)
    column.set_resizable(False)
    column.set_cell_data_func(sched_rend, self._cell_data_func)
    self.append_column(column)
    self.get_selection().connect("changed", self._on_schedule_activate)
    
    self.enable_model_drag_dest(DRAGDROP_SCHEDULE,
        gtk.gdk.ACTION_DEFAULT)
    self.connect("drag-drop", self._on_pres_drop)
    self.connect("drag-data-received", self._on_sched_drag_received)
    #self.set_drag_dest_row((1,), gtk.TREE_VIEW_DROP_INTO_OR_BEFORE)

  def append(self, parent, row, sort = None):
    'Add an item to the list.'
    if isinstance(row, exposong.schedule.Schedule):
      if sort is None:
        sort = row.title
      else:
        sort = "%03u" % sort
      return self.model.append( parent, (row, row.title, sort) )
    elif isinstance(row, tuple):
      return self.model.append( parent, row )
  
  def remove(self, item):
    'Remove the item from the model.'
    model = self.get_model()
    itr = model.iter_children(self.custom_schedules)
    while model.get_value(itr, 0).filename != item.filename:
      itr = model.iter_next(itr)
    self.get_model().remove(itr)
  
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
    if self.has_selection():
      sched = self.get_active_item()
      if isinstance(sched, exposong.schedule.Schedule):
        exposong.preslist.preslist.set_model(sched)
        exposong.preslist.preslist.columns_autosize()
        if sched.is_reorderable():
          exposong.preslist.preslist.enable_model_drag_dest(DRAGDROP_SCHEDULE,
              gtk.gdk.ACTION_DEFAULT)
        else:
          exposong.preslist.preslist.unset_rows_drag_dest()
    try:
      enable = isinstance(sched, exposong.schedule.Schedule) and not sched.builtin
    except UnboundLocalError:
      enable = False

    exposong.application.main.main_actions.get_action("sched-rename")\
        .set_sensitive(enable)
    exposong.application.main.main_actions.get_action("sched-delete")\
        .set_sensitive(enable)
    
    exposong.preslist.preslist.get_model()\
        .connect("row-changed", exposong.preslist.preslist._on_pres_added)
  
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
        _('Are you sure you want to delete "%s"?') % item.title)
    dialog.set_title( _("Delete Schedule?") )
    resp = dialog.run()
    dialog.hide()
    if resp == gtk.RESPONSE_YES:
      if item.filename:
        os.remove(os.path.join(DATA_PATH, "sched",item.filename))# directory <- for search
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
      
      pres = exposong.preslist.preslist.get_filter_model().get_value(
          exposong.preslist.preslist.get_filter_model().get_iter_from_string(
              selection.data), 0).presentation
      sched = model.get_value(model.get_iter(path), 0)
      
      sched.append(pres)
      context.finish(True, False)
      statusbar.statusbar.output(
          _('Added Presentation >%(presentation)s< to Schedule >%(schedule)s<')%
          {"presentation":pres.get_title(), "schedule": sched.title})
  
  def _on_new(self, *args):
    'Create a new schedule.'
    name = _("New Schedule")
    curnames = []
    num = 1
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
    pathnew = self.model.get_path(itrnew)
    self.expand_all()
    self.set_cursor(pathnew, self.get_column(0), True)
  
  def _on_rename(self, *args):
    'Rename an existing schedule.'
    (path, focus) = self.get_cursor()
    self.set_cursor(path, focus, True)
  
  def _cell_data_func(self, column, cell, model, iter1):
    'Set whether the cell is editable or not.'
    sched = model.get_value(iter1, 0)
    cell.set_property('editable', isinstance(sched, exposong.schedule.Schedule) and sched.builtin is False)
  
  def _rename_schedule(self, text_rend, path, new_text):
    "Rename a schedule in the list and it's filename."
    if len(new_text.strip()) == 0:
      return
    iter1 = self.model.get_iter(path)
    self.model.get_value(iter1, 0).title = new_text
    self.model.set_value(iter1, 1, new_text)
    self.model.set_value(iter1, 2, new_text)

