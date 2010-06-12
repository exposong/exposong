# -*- coding: utf-8 -*-
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

_LABEL_SPACING = 12
_WIDGET_SPACING = 4

def Table(rows):
  'Returns a gtk Table.'
  table = gtk.Table(rows, 4)
  table.set_row_spacings(8)
  table.set_border_width(6)
  return table

def append_entry(table, label, value, top, max_len = 0):
  'Adds a text entry widget to a table and returns it.'
  set_label(table, label, top)
  
  entry = gtk.Entry(max_len)
  if value:
    entry.set_text(value)
  table.attach(entry, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, _WIDGET_SPACING)
  return entry

def append_textview(table, label, value, top):
  'Adds a textview widget to a table and returns it'
  set_label(table, label, top)
  
  textview = gtk.TextView()
  textview.set_size_request(250, 200)
  if value:
    textview.get_buffer().set_text(value)
  scroll = gtk.ScrolledWindow()
  scroll.add(textview)
  scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
  table.attach(scroll, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL,
      gtk.EXPAND|gtk.FILL, _WIDGET_SPACING)
  return textview

def append_file(table, label, value, top):
  'Adds a file widget to a table and returns it.'
  set_label(table, label, top)
  
  filech = gtk.FileChooserButton( _("Choose File") )
  filech.set_width_chars(15)
  if value:
    filech.set_filename(value)
  else:
    filech.set_current_folder(os.path.expanduser('~'))
  table.attach(filech, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, _WIDGET_SPACING)
  return filech

def append_folder(table, label, value, top):
  'Adds a folder widget to a table and returns it.'
  set_label(table, label, top)
  
  filech = gtk.FileChooserButton( _("Choose Folder") )
  filech.set_width_chars(15)
  filech.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
  if value:
    filech.set_current_folder(value)
  else:
    filech.set_current_folder(os.path.expanduser('~'))
  table.attach(filech, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, _WIDGET_SPACING)
  return filech

def append_color(table, label, value, top, alpha=False):
  'Adds a color widget to a table and returns it.'
  set_label(table, label, top)
  
  if isinstance(value[0], tuple):
    buttons = []
    cnt = 2
    for v in value:
      button = gtk.ColorButton(gtk.gdk.Color(int(v[0]), int(v[1]), int(v[2])))
      table.attach(button, cnt, cnt+1, top, top+1, gtk.EXPAND|gtk.FILL, 0, _WIDGET_SPACING)
      cnt += 1
      buttons.append(button)
    return buttons
  else:
    button = gtk.ColorButton(gtk.gdk.Color(int(value[0]), int(value[1]),
        int(value[2])))
    table.attach(button, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, _WIDGET_SPACING)
    if(alpha):
      button.set_alpha(int(value[3]))
      button.set_use_alpha(True)
    return button

def append_spinner(table, label, adjustment, top):
  'Adds a spinner widget to a table and returns it.'
  set_label(table, label, top)
  
  spinner = gtk.SpinButton(adjustment, 2.0)
  table.attach(spinner, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, _WIDGET_SPACING)
  return spinner

def append_combo(table, label, options, value, top):
  'Adds a combo widget to a table and returns it.'
  set_label(table, label, top)
  
  combo = gtk.combo_box_new_text()
  for i in range(len(options)):
    combo.append_text(options[i])
    if options[i] == value:
      combo.set_active(i)
  table.attach(combo, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, _WIDGET_SPACING)
  return combo

def append_combo2(table, label, options, value, top):
  '''Adds a combo widget to a table and returns it.
  
  options: a list of tuples containing the stored value as a string and the
  translated string.'''
  set_label(table, label, top)
  
  list = gtk.ListStore(str, str)
  combo = gtk.ComboBox(list)
  cell = gtk.CellRendererText()
  combo.pack_start(cell, True)
  combo.add_attribute(cell, 'text', 1)
  for i in range(len(options)):
    print i, options[i]
    list.append(options[i])
    if options[i][0] == value:
      combo.set_active(i)
  if not value:
    combo.set_active(0)
  table.attach(combo, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, _WIDGET_SPACING)
  return combo

def append_radio(table, label, active, top, group = None):
  'Adds a radio widget to a table and returns it.'
  radio = gtk.RadioButton(group, label)
  radio.set_alignment(0.0, 0.5)
  radio.set_active(active)
  table.attach(radio, 1, 2, top, top+1, gtk.FILL, 0, _LABEL_SPACING)
  return radio

def append_language_combo(table, value, top):
  "Gets the active"
  set_label(table, _('Language Code'), top)
  list = gtk.ListStore(str)
  list.append( ('en',) )
  list.append( ('en_US',) )
  list.append( ('en_GB',) )
  list.append( ('de',) )
  list.append( ('de_DE',) )
  # TODO Get this list from an official place. At least provide the users
  # current language code.
  
  lang = gtk.ComboBoxEntry(list)
  if value:
    lang.child.set_text(value)
  #cell = gtk.CellRendererText()
  #lang.pack_start(cell, True)
  #lang.add_attribute(cell, 'text', 0)
  table.attach(lang, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, _WIDGET_SPACING)
  return lang

def append_section_title(table, title, top):
  'Adds a title for the current section.'
  hbox = gtk.HBox()
  label = gtk.Label()
  label.set_markup("<b>"+title+"</b>")
  label.set_alignment(0.0, 1.0)
  table.attach(label, 0, 4, top, top+1, gtk.FILL, 0, 0)

def set_label(table, label, top):
  'Returns a label for a widget.'
  if isinstance(label, str) and len(label):
    label = gtk.Label(label)
    label.set_alignment(0.0, 0.0)
  if isinstance(label, gtk.Widget):
    table.attach(label, 1, 2, top, top+1, gtk.FILL, gtk.FILL, _LABEL_SPACING)

def treesel_disable_widget(sel, widget):
  'Disable `widget` if a tree selection is empty.'
  widget.set_sensitive(sel.count_selected_rows() > 0)
