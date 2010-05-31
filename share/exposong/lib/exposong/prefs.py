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
import os

from exposong import DATA_PATH
from exposong import SHARED_FILES
from exposong.config import config
import exposong.screen

'''
Dialog for changing settings in ExpoSong.
'''

_LABEL_SPACING = 12
_WIDGET_SPACING = 4

class PrefsDialog(gtk.Dialog):
  '''
  Dialog to configure user preferences.
  '''
  def __init__(self, parent):
    self.widgets = {}
    gtk.Dialog.__init__(self, _("Preferences"), parent, 0,
        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    self.set_default_size(350, 410)
    notebook = gtk.Notebook()
    self.vbox.pack_start(notebook, True, True, 5)
    
    #General Page
    self.table = gtk.Table(8, 2)
    self.table.set_row_spacings(10)
    self.table.set_border_width(10)
    
    #self._append_section_title(_("Places"), 0)
    if config.has_option("general", "data-path"):
      folder = config.get("general", "data-path")
    else:
      folder = DATA_PATH
    g_data = self._append_folder_setting(_("Data folder"), folder, 0)
    g_data.set_tooltip_text(_("The place where all your presentations, \
schedules and background images are stored."))
    
    self._append_section_title(_("Legal"), 1)
    g_ccli = self._append_text_setting("CCLI #", config.get("general","ccli"), 2)
    
    notebook.append_page(self.table, gtk.Label( _("General") ))
    
    #Screen Page
    self.table = gtk.Table(15, 4)
    self.table.set_row_spacings(10)
    self.table.set_border_width(10)
    
    self._append_section_title( _("Font"), 0)
    p_txt = self._append_color_setting( _("Text Color"),
        config.getcolor("screen","text_color"), 1)
    p_shad = self._append_color_setting( _("Text Shadow"),
        config.getcolor("screen","text_shadow"), 2, True)
    p_maxsize = self._append_spinner_setting( _("Max Font Size"),
        gtk.Adjustment(config.getfloat("screen","max_font_size"), 0, 96, 1),
        3)
    
    self._append_section_title( _("Logo"), 5)
    p_logo = self._append_file_setting( _("Image"),
        config.get("screen","logo"), 6)
    p_logo_bg = self._append_color_setting( _("Background"),
        config.getcolor("screen","logo_bg"), 7)
    
    self._append_section_title( _("Notify"), 9)
    p_notify_bg = self._append_color_setting( _("Background"),
        config.getcolor("screen","notify_bg"), 10)
    
    # Monitor Selection
    monitor_name = tuple()
    sel = 0
    screen = parent.get_screen()
    num_monitors = screen.get_n_monitors()
    monitor_name = ( _("Primary"), _("Primary (Bottom-Right)"),
        _("Secondary"), _("Tertiary"), _("Monitor 4") )[0:num_monitors+1]
    monitor_value = ('1', '1h', '2', '3', '4')[0:num_monitors+1]
    if num_monitors == 1:
      sel = monitor_name[1]
    else:
      sel = monitor_name[2]
    
    try:
      if config.get('screen', 'monitor') == '1':
        sel = monitor_name[0]
      if config.get('screen', 'monitor') == '1h':
        sel = monitor_name[1]
      else:
        sel = monitor_name[config.getint('screen', 'monitor')]
    except config.NoOptionError:
      pass
    except IndexError:
      pass
    
    self._append_section_title( _("Position"), 11)
    p_monitor = self._append_combo_setting( _("Monitor"), monitor_name, sel,
        12)
    
    notebook.append_page(self.table, gtk.Label( _("Screen")))
    
    self.show_all()
    if self.run() == gtk.RESPONSE_ACCEPT:
      config.set("general", "ccli", g_ccli.get_text())
      if g_data.get_current_folder() != DATA_PATH:
        config.set("general", "data-path", g_data.get_current_folder())
        dlg = gtk.MessageDialog(self, gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
            _("You will have to restart ExpoSong so that the new data folder \
will be used."))
        dlg.run()
        dlg.destroy()
      
      txtc = p_txt.get_color()
      config.setcolor("screen", "text_color", (txtc.red, txtc.green, txtc.blue))
      txts = p_shad.get_color()
      config.setcolor("screen", "text_shadow", (txts.red, txts.green, txts.blue, p_shad.get_alpha()))
      config.set("screen", "max_font_size", str(p_maxsize.get_value()))
      
      if p_logo.get_filename() != None:
        config.set("screen", "logo", p_logo.get_filename())
      logoc = p_logo_bg.get_color()
      config.setcolor("screen", "logo_bg", (logoc.red, logoc.green, logoc.blue))
      ntfc = p_notify_bg.get_color()
      config.setcolor("screen", "notify_bg", (ntfc.red, ntfc.green, ntfc.blue))
      
      config.set('screen','monitor', monitor_value[p_monitor.get_active()])
      exposong.screen.screen.reposition(parent)
      
      exposong.screen.screen.set_dirty()
      if hasattr(self,"_logo_pbuf"):
        del exposong.screen.screen._logo_pbuf
      exposong.screen.screen.draw()
    
    self.hide()
  
  def _append_section_title(self, title, top):
    'Adds a title for the current section.'
    hbox = gtk.HBox()
    label = gtk.Label()
    label.set_markup("<b>"+title+"</b>")
    label.set_alignment(0.0, 0.5)
    self.table.attach(label, 0, 4, top, top+1, gtk.FILL, 0, 0)
  
  def _append_text_setting(self, label, value, top):
    'Adds a text setting and returns the text widget.'
    self._get_label(label, top)
    
    entry = gtk.Entry(10)
    entry.set_text(value)
    self.table.attach(entry, 2, 4, top, top+1, gtk.FILL, 0, _WIDGET_SPACING)
    return entry
  
  def _append_file_setting(self, label, value, top):
    'Adds a file setting and returns the file widget.'
    self._get_label(label, top)
    
    filech = gtk.FileChooserButton( _("Choose File") )
    filech.set_width_chars(15)
    if value:
      filech.set_filename(value)
    else:
      filech.set_current_folder(os.path.expanduser('~'))
    self.table.attach(filech, 2, 4, top, top+1, gtk.FILL, 0, _WIDGET_SPACING)
    return filech

  def _append_folder_setting(self, label, value, top):
    'Adds a folder setting and returns the folder widget.'
    self._get_label(label, top)
    
    filech = gtk.FileChooserButton( _("Choose Folder") )
    filech.set_width_chars(15)
    filech.set_action(gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
    if value:
      filech.set_current_folder(value)
    else:
      filech.set_current_folder(os.path.expanduser('~'))
    self.table.attach(filech, 2, 4, top, top+1, gtk.FILL, 0, _WIDGET_SPACING)
    return filech
  
  def _append_color_setting(self, label, value, top, alpha=False):
    'Adds a color setting and returns the color widget.'
    self._get_label(label, top)
    
    if isinstance(value[0], tuple):
      buttons = []
      cnt = 2
      for v in value:
        button = gtk.ColorButton(gtk.gdk.Color(int(v[0]), int(v[1]), int(v[2])))
        self.table.attach(button, cnt, cnt+1, top, top+1, gtk.FILL, 0, _WIDGET_SPACING)
        cnt += 1
        buttons.append(button)
      return buttons
    else:
      button = gtk.ColorButton(gtk.gdk.Color(int(value[0]), int(value[1]), int(value[2])))
      self.table.attach(button, 2, 4, top, top+1, gtk.FILL, 0, _WIDGET_SPACING)
      if(alpha):
        button.set_alpha(int(value[3]))
        button.set_use_alpha(True)
      return button
  
  def _append_spinner_setting(self, label, adjustment, top):
    'Adds a spinner setting and returns the spinner widget.'
    self._get_label(label, top)
    
    spinner = gtk.SpinButton(adjustment, 2.0)
    self.table.attach(spinner, 2, 4, top, top+1, gtk.FILL, 0, _WIDGET_SPACING)
    return spinner
  
  def _append_combo_setting(self, label, options, value, top):
    'Adds a combo setting and returns the combo widget.'
    self._get_label(label, top)
    
    combo = gtk.combo_box_new_text()
    for i in range(len(options)):
      combo.append_text(options[i])
      if options[i] == value:
        combo.set_active(i)
    self.table.attach(combo, 2, 4, top, top+1, gtk.FILL, 0, _WIDGET_SPACING)
    return combo
  
  def _append_radio_setting(self, label, active, top, group = None):
    'Adds a radio setting and returns the radio widget.'
    radio = gtk.RadioButton(group, label)
    radio.set_alignment(0.0, 0.5)
    radio.set_active(active)
    self.table.attach(radio, 1, 2, top, top+1, gtk.FILL, 0, _LABEL_SPACING)
    return radio
  
  def _get_label(self, label, top):
    'Returns a label for a widget.'
    if isinstance(label, str) and len(label):
      label = gtk.Label(label)
      label.set_alignment(0.0, 0.5)
    if isinstance(label, gtk.Widget):
      self.table.attach(label, 1, 2, top, top+1, gtk.FILL, 0, _LABEL_SPACING)
  
  def _on_toggle(self, button, target):
    'Enables or disables target if button is set.'
    if isinstance(target, gtk.Widget):
      target.set_sensitive(button.get_active())
    elif isinstance(target, (tuple, list)):
      for t in target:
        self._on_toggle(button, t)

def getGeometryFromRect(_g1):
  return ','.join( map(str, (_g1.x, _g1.y, _g1.width, _g1.height)) )
