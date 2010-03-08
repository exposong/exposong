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
import gtk, gtk.gdk, gobject
from os.path import join
import xml.dom
import xml.dom.minidom

from exposong.glob import *
from exposong import RESOURCE_PATH
from exposong.plugins import Plugin, _abstract
import exposong.application

"""
Plain text presentations.
"""
information = {
    'name': _("Text Presentation"),
    'description': __doc__,
    'required': False,
}
type_icon = gtk.gdk.pixbuf_new_from_file_at_size(
    join(RESOURCE_PATH,'pres_text.png'), 20, 14)

class Presentation (Plugin, _abstract.Presentation, _abstract.Menu,
    _abstract.Schedule):
  '''
  Text presentation type.
  '''
  
  class Slide (Plugin, _abstract.Presentation.Slide):
    '''
    A text slide.
    '''
    def __init__(self, pres, value):
      _abstract.Presentation.Slide.__init__(self, pres, value)
    
    def _edit_window(self, parent):
      'Create a new window for editing.'
      dialog = gtk.Dialog(_("Editing Slide"), exposong.application.main,\
          gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,\
          (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
      
      dialog.set_border_width(4)
      dialog.vbox.set_spacing(7)
      hbox = gtk.HBox()
      label = gtk.Label(_("Title:"))
      label.set_alignment(0.5,0.5)
      hbox.pack_start(label, False, True)
      
      title = gtk.Entry(80)
      title.set_text(self.title)
      hbox.pack_start(title, True, True)
      dialog.vbox.pack_start(hbox, False, True)
      
      text = gtk.TextView()
      text.set_wrap_mode(gtk.WRAP_WORD)
      text.get_buffer().set_text(self.text)
      text_scroll = gtk.ScrolledWindow()
      text_scroll.add(text)
      text_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
      text_scroll.set_size_request(350, 250)
      dialog.vbox.pack_start(text_scroll, True, True)
      
      dialog.vbox.show_all()
      
      if dialog.run() == gtk.RESPONSE_ACCEPT:
        self.title = title.get_text()
        bounds = text.get_buffer().get_bounds()
        self.text = text.get_buffer().get_text(bounds[0], bounds[1])
        dialog.hide()
        return True
      else:
        dialog.hide()
        return False
  
  def __init__(self, dom = None, filename = None):
    _abstract.Presentation.__init__(self, dom, filename)
    self.type = "text"
  
  def _edit_tabs(self, notebook, parent):
    'Tabs for the dialog.'
    vbox = gtk.VBox()
    vbox.set_border_width(4)
    vbox.set_spacing(7)
    hbox = gtk.HBox()
    
    label = gtk.Label(_("Title:"))
    label.set_alignment(0.5, 0.5)
    hbox.pack_start(label, False, True, 5)
    
    self._fields['title'] = gtk.Entry(45)
    self._fields['title'].set_text(self.title)
    hbox.pack_start(self._fields['title'], True, True)
    vbox.pack_start(hbox, False, True)
    
    # TODO Add signal detection and make these do something.
    slideToolbar = gtk.Toolbar()
    btn = gtk.ToolButton(gtk.STOCK_ADD)
    btn.connect("clicked", self._slide_add_dialog, parent)
    slideToolbar.insert(btn, -1)
    btn = gtk.ToolButton(gtk.STOCK_EDIT)
    btn.connect("clicked", self._slide_edit_dialog, parent)
    slideToolbar.insert(btn, -1)
    btn = gtk.ToolButton(gtk.STOCK_DELETE)
    btn.connect("clicked", self._slide_delete_dialog, parent)
    slideToolbar.insert(btn, -1)
    slideToolbar.insert(gtk.SeparatorToolItem(), -1)
    
    vbox.pack_start(slideToolbar, False, True)
    
    hbox = gtk.HBox()
    self._fields['slides'] = gtk.TreeView()
    self._fields['slides'].set_enable_search(False)
    self._fields['slides'].set_reorderable(True)
    col = gtk.TreeViewColumn( _("Slide") )
    col.set_resizable(False)
    self.slide_column(col, self._fields['slides'])
    self._fields['slides'].append_column(col)
    
    # Add the slides
    slide_model = self._fields['slides'].get_model()
    for sl in self.get_slide_list():
      slide_model.append(sl)
    
    text_scroll = gtk.ScrolledWindow()
    text_scroll.add(self._fields['slides'])
    text_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
    text_scroll.set_size_request(400, 250)
    vbox.pack_start(text_scroll, True, True)
    
    vbox.show_all()
    
    notebook.append_page(vbox, gtk.Label(_("Edit")))
    
    _abstract.Presentation._edit_tabs(self, notebook, parent)
  
  def _edit_save(self):
    'Save the fields if the user clicks ok.'
    self.title = self._fields['title'].get_text()
    model = self._fields['slides'].get_model()
    itr = model.get_iter_first()
    self.slides = []
    while itr:
      self.slides.append(model.get_value(itr,0))
      itr = model.iter_next(itr)
  
  def _slide_add_dialog(self, btn, parent):
    'Create a dialog for a new slide.'
    sl = self.Slide(self,None)
    if(sl._edit_window(parent)):
      sl._set_id()
      model = self._fields['slides'].get_model()
      model.append( (sl, sl.get_markup()) )
    
  def _slide_edit_dialog(self, btn, parent):
    'Create a dialog for an existing slide.'
    (model, itr) = self._fields['slides'].get_selection().get_selected()
    if not itr:
      return False
    sl = model.get_value(itr, 0)
    old_title = sl.title
    sel_path = model.get_path(itr)
    if(sl._edit_window(parent)):
      if(len(old_title) == 0 or old_title <> sl.title): sl._set_id()
      model.set(itr, 0, sl, 1, sl.get_markup())
    
  def _slide_delete_dialog(self, btn, parent):
    'Remove the selected slide.'
    pass
  
  @staticmethod
  def get_type():
    'Return the presentation type.'
    return 'text'
  
  @staticmethod
  def get_icon():
    'Return the pixbuf icon.'
    return type_icon
  
  def merge_menu(self, uimanager):
    'Merge new values with the uimanager.'
    factory = gtk.IconFactory()
    factory.add('exposong-text',gtk.IconSet(gtk.gdk.pixbuf_new_from_file(
        join(RESOURCE_PATH,'pres_text.png'))))
    factory.add_default()
    gtk.stock_add([("exposong-text",_("_Text"), gtk.gdk.MOD1_MASK, 
        0, "pymserv")])
    
    actiongroup = gtk.ActionGroup('exposong-text')
    actiongroup.add_actions([("pres-new-text", 'exposong-text', None, None,
        None, self._on_pres_new)])
    uimanager.insert_action_group(actiongroup, -1)
    
    self.menu_merge_id = uimanager.add_ui_from_string("""
      <menubar name='MenuBar'>
        <menu action="Presentation">
            <menu action="pres-new">
              <menuitem action='pres-new-text' />
            </menu>
        </menu>
      </menubar>
      """)
  
  def unmerge_menu(self, uimanager):
    'Remove merged items from the menu.'
    uimanager.remove_ui(self.menu_merge_id)
  
  @classmethod
  def schedule_name(cls):
    'Return the string schedule name.'
    return _('Text Presentations')
  
  @classmethod
  def schedule_filter(cls, pres):
    'Called on each presentation, and return True if it can be added.'
    return isinstance(pres, cls)
  
  @staticmethod
  def get_version():
    'Return the version number of the plugin.'
    return (1,0)
  
  @staticmethod
  def get_description():
    'Return the description of the plugin.'
    return "A text presentation type."

