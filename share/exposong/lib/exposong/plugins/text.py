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
import gtk.gdk
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
type_icon = gtk.gdk.pixbuf_new_from_file(join(RESOURCE_PATH,'text.png'))

class Presentation (Plugin, _abstract.Presentation, _abstract.Menu,
    _abstract.Schedule):
  '''
  Text presentation type.
  '''
  
  def __init__(self, dom = None, filename = None):
    _abstract.Presentation.__init__(self, dom, filename)
    self.type = "text"
  
  def _edit_tabs(self, notebook):
    'Tabs for the dialog.'
    tabs = list()
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
    
    self._fields['text'] = gtk.TextView()
    self._fields['text'].set_wrap_mode(gtk.WRAP_WORD)
    self.set_text_buffer(self._fields['text'].get_buffer())
    text_scroll = gtk.ScrolledWindow()
    text_scroll.add(self._fields['text'])
    text_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
    text_scroll.set_size_request(300, 200)
    vbox.pack_start(text_scroll, True, True)
    notebook.append_page(vbox, gtk.Label(_("Edit")))
    
    _abstract.Presentation._edit_tabs(self, notebook)
  
  def _edit_save(self):
    'Save the fields if the user clicks ok.'
    self.title = self._fields['title'].get_text()
    bounds = self._fields['text'].get_buffer().get_bounds()
    sval = self._fields['text'].get_buffer().get_text(bounds[0], bounds[1])
    self.slides = []
    for sl in sval.split("\n\n"):
      self.slides.append(self.Slide(self, sl))
  
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
        join(RESOURCE_PATH,'text.png'))))
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

