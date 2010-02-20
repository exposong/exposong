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
import imp
import os.path

from exposong import SHARED_FILES
import exposong.screen

'''
Configures program usage for ExpoSong.
'''
class Prefs:
  '''
  Manages user preferences.
  '''
  def __init__(self):
    self.cfg = {'general.ccli': '',
        'pres.max_font_size': 56,
        'pres.bg': ((0, 13107, 19660), (0, 26214, 39321)),
        'pres.bg_angle': u'\u2198',
        'pres.text_color': (65535, 65535, 65535),
        'pres.text_shadow': (0, 0, 0, 26214),
        'pres.logo': SHARED_FILES+"/res/exposong-white.png",
        'pres.logo_bg': (65535, 43690, 4369),
        'pres.notify_bg': (65535, 0, 0),
        }
    self.load()
  
  def __getitem__(self, key):
    'Return a preference.'
    if key in self.cfg:
      return self.cfg[key]
    raise KeyError, _('Could not find key: %s') % key
  
  def __setitem__(self, key, value):
    'Set a preference.'
    if value == None:
      self.__delitem__(key)
    else:
      self.cfg[key] = value
  
  def __delitem__(self, key):
    'Deletes a preference.'
    self.cfg[key] = None
  
  def load(self):
    'Load preferences from file.'
    try:
      config = imp.load_source('config', os.path.expanduser('~/.exposong_cfg.py'))
    except IOError:
      return False
    for k,v in self.cfg.iteritems():
      ksp = k.split(".")
      if hasattr(config, ksp[0]) and hasattr(getattr(config, ksp[0]), ksp[1]):
        self.cfg[k] = getattr(getattr(config, ksp[0]), ksp[1])
      
  def save(self):
    'Save preferences to file.'
    cfile = file(os.path.expanduser('~/.exposong_cfg.py'), 'w')
    
    cnt = 0
    cfile.write('class Cfg:\n\tpass\n\n')
    
    for key in set(k.split('.')[0] for k in self.cfg.keys()):
      cfile.write(key+" = Cfg()\n")
    cfile.write("\n\n")
    
    for key, value in self.cfg.iteritems():
      ln = key+' = '+repr(value)+'\n'
      cfile.write(ln)
    
    cfile.close()
  
  def dialog(self, parent):
    'Show the preferences dialog.'
    PrefsDialog(parent, self)

LABEL_SPACING = 12
WIDGET_SPACING = 4

class PrefsDialog(gtk.Dialog):
  '''
  Dialog to configure user preferences.
  '''
  def __init__(self, parent, config):
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
    
    self._append_section_title(_("Legal"), 0)
    g_ccli = self._append_text_setting("CCLI #", config['general.ccli'], 1)
    
    notebook.append_page(self.table, gtk.Label( _("General") ))
    
    #Presentation Page
    self.table = gtk.Table(15, 4)
    self.table.set_row_spacings(10)
    self.table.set_border_width(10)
    
    self._append_section_title( _("Font"), 0)
    p_txt = self._append_color_setting( _("Text Color"), config['pres.text_color'], 1)
    p_shad = self._append_color_setting( _("Text Shadow"), config['pres.text_shadow'], 2, True)
    p_maxsize = self._append_spinner_setting( _("Max Font Size"), gtk.Adjustment(config['pres.max_font_size'], 0, 96, 1), 3)
    
    self._append_section_title( _("Logo"), 5)
    p_logo = self._append_file_setting( _("Image"), config['pres.logo'], 6)
    p_logo_bg = self._append_color_setting( _("Background"), config['pres.logo_bg'], 7)
    
    self._append_section_title( _("Notify"), 9)
    p_notify_bg = self._append_color_setting( _("Background"), config['pres.notify_bg'], 10)
    
    notebook.append_page(self.table, gtk.Label( _("Presentation")))
    
    self.show_all()
    if self.run() == gtk.RESPONSE_ACCEPT:
      config['general.ccli'] = g_ccli.get_text()
      
      txtc = p_txt.get_color()
      config['pres.text_color'] = (txtc.red, txtc.green, txtc.blue)
      txts = p_shad.get_color()
      config['pres.text_shadow'] = (txts.red, txts.green, txts.blue, p_shad.get_alpha())
      config['pres.max_font_size'] = p_maxsize.get_value()
      
      config['pres.logo'] = p_logo.get_filename()
      logoc = p_logo_bg.get_color()
      config['pres.logo_bg'] = (logoc.red, logoc.green, logoc.blue)
      ntfc = p_notify_bg.get_color()
      config['pres.notify_bg'] = (ntfc.red, ntfc.green, ntfc.blue)
      
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
    self.table.attach(entry, 2, 4, top, top+1, gtk.FILL, 0, WIDGET_SPACING)
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
    self.table.attach(filech, 2, 4, top, top+1, gtk.FILL, 0, WIDGET_SPACING)
    return filech
  
  def _append_color_setting(self, label, value, top, alpha=False):
    'Adds a color setting and returns the color widget.'
    self._get_label(label, top)
    
    if isinstance(value[0], tuple):
      buttons = []
      cnt = 2
      for v in value:
        button = gtk.ColorButton(gtk.gdk.Color(int(v[0]), int(v[1]), int(v[2])))
        self.table.attach(button, cnt, cnt+1, top, top+1, gtk.FILL, 0, WIDGET_SPACING)
        cnt += 1
        buttons.append(button)
      return buttons
    else:
      button = gtk.ColorButton(gtk.gdk.Color(int(value[0]), int(value[1]), int(value[2])))
      self.table.attach(button, 2, 4, top, top+1, gtk.FILL, 0, WIDGET_SPACING)
      if(alpha):
        button.set_alpha(int(value[3]))
        button.set_use_alpha(True)
      return button
  
  def _append_spinner_setting(self, label, adjustment, top):
    'Adds a spinner setting and returns the spinner widget.'
    self._get_label(label, top)
    
    spinner = gtk.SpinButton(adjustment, 2.0)
    self.table.attach(spinner, 2, 4, top, top+1, gtk.FILL, 0, WIDGET_SPACING)
    return spinner
  
  def _append_combo_setting(self, label, options, value, top):
    'Adds a combo setting and returns the combo widget.'
    self._get_label(label, top)
    
    combo = gtk.combo_box_new_text()
    for i in range(len(options)):
      combo.append_text(options[i])
      if isinstance(value, str) and options[i] == value:
        combo.set_active(i)
    self.table.attach(combo, 2, 4, top, top+1, gtk.FILL, 0, WIDGET_SPACING)
    return combo
  
  def _append_radio_setting(self, label, active, top, group = None):
    'Adds a radio setting and returns the radio widget.'
    radio = gtk.RadioButton(group, label)
    radio.set_alignment(0.0, 0.5)
    radio.set_active(active)
    self.table.attach(radio, 1, 2, top, top+1, gtk.FILL, 0, LABEL_SPACING)
    return radio
  
  def _get_label(self, label, top):
    'Returns a label for a widget.'
    if isinstance(label, str) and len(label):
      label = gtk.Label(label)
      label.set_alignment(0.0, 0.5)
    if isinstance(label, gtk.Widget):
      self.table.attach(label, 1, 2, top, top+1, gtk.FILL, 0, LABEL_SPACING)
  
  def _on_toggle(self, button, target):
    'Enables or disables target if button is set.'
    if isinstance(target, gtk.Widget):
      target.set_sensitive(button.get_active())
    elif isinstance(target, (tuple, list)):
      for t in target:
        self._on_toggle(button, t)

config = Prefs()

