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

import undobuffer

"""
Edit a text slide
"""

class SlideEdit(gtk.Dialog):
  'Create a new window for editing a single slide.'
  def __init__(self, parent, slide_name, slide_text):
    gtk.Dialog.__init__(self, _("Editing Slide"), parent,\
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
    
    cancelbutton = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
    cancelbutton.connect("clicked", self._quit_without_save)
    okbutton = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
    okbutton.connect("clicked", self._quit_with_save)
    
    self.connect("delete-event", self._quit_without_save)
    
    
    self.slide_name = slide_name
    self.slide_text = slide_text
    
    self.set_border_width(4)
    self.vbox.set_spacing(7)
    hbox = gtk.HBox()
    label = gtk.Label(_("Title:"))
    label.set_alignment(0.5,0.5)
    hbox.pack_start(label, False, True)
    
    self.title_entry = gtk.Entry()
    self.title_entry.set_text(slide_name)
    hbox.pack_start(self.title_entry, True, True)
    self.vbox.pack_start(hbox, False, True)
    
    editSlideToolbar = gtk.Toolbar()
    self.undo_btn = gtk.ToolButton(gtk.STOCK_UNDO)
    self.undo_btn.set_sensitive(False)
    self.undo_btn.connect("clicked", self._undo)
    editSlideToolbar.insert(self.undo_btn, -1)
    self.redo_btn = gtk.ToolButton(gtk.STOCK_REDO)
    self.redo_btn.set_sensitive(False)
    self.redo_btn.connect("clicked", self._redo)
    editSlideToolbar.insert(self.redo_btn, -1)
    self.vbox.pack_start(editSlideToolbar, False, True)
    
    self.buffer = undobuffer.UndoableBuffer()
    self.buffer.begin_not_undoable_action()
    self.buffer.set_text(self.slide_text)
    self.buffer.end_not_undoable_action()
    self.buffer.set_modified(False)
    self.buffer.connect("changed", self._on_text_changed)
    
    text = gtk.TextView()
    text.set_wrap_mode(gtk.WRAP_WORD)
    text.set_buffer(self.buffer)
    text_scroll = gtk.ScrolledWindow()
    text_scroll.add(text)
    text_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
    text_scroll.set_size_request(400, 250)
    self.vbox.pack_start(text_scroll, True, True)
    
    self.vbox.show_all()
    
    self.run()
  
  def get_slide_name(self):
    'Returns the name of the edited slide'
    return self.slide_name
  
  def get_slide_text(self):
    'Returns the text of the edited slide'
    return self.slide_text
  
  def _save(self):
    self.slide_name = self.title_entry.get_text()
    bounds = self.buffer.get_bounds()
    self.slide_text = self.buffer.get_text(bounds[0], bounds[1])
      
  def _ok_to_continue(self):
    if self.buffer.can_undo or\
        self.title_entry.get_text() != self.slide_name:
      dlg = gtk.MessageDialog(self, gtk.DIALOG_MODAL,
                              gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                              _('Unsaved Changes exist. Do you really \
want to continue without saving?'))
      resp = dlg.run()
      dlg.destroy()
      if resp == gtk.RESPONSE_NO:
        return False
      elif resp == gtk.RESPONSE_YES:
        self._save()
    return True
  
  def _on_text_changed(self, event):
    self.undo_btn.set_sensitive(self.buffer.can_undo)
    self.redo_btn.set_sensitive(self.buffer.can_redo)
    if self.buffer.can_undo:
      if not self.get_title().startswith("*"):
        self.set_title("*%s"%self.get_title())
    else:
      self.set_title(self.get_title().lstrip("*"))
  
  def _undo(self, event):
    self.buffer.undo()
  
  def _redo(self, event):
    self.buffer.redo()
  
  def _quit_with_save(self, event, *args):
    if self.title_entry.get_text() == "":
      info_dialog = gtk.MessageDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT,
          gtk.MESSAGE_INFO, gtk.BUTTONS_OK, _("Please enter a Title."))
      info_dialog.run()
      info_dialog.destroy()
      self.title_entry.grab_focus()
      return False
    self._save()
    self.destroy()
  
  def _quit_without_save(self, event, *args):
    if self._ok_to_continue():
      self.destroy()
