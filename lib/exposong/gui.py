# -*- coding: utf-8 -*-
# vim: ts=4 sw=4 expandtab ai:
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
try:
    import gtkspell
except Exception:
    pass
import gobject
import os

_LABEL_SPACING = 12
WIDGET_SPACING = 4
__pb_cache = {}



## New Class ##

class ESTable(gtk.Table):
    """
    This class will assist in laying out widgets in a standardized way.
    """
    def __init__(self, rows=1, cols=1):
        gtk.Table.__init__(self, rows, cols*2)        
        self.set_row_spacings(4)
        self.set_border_width(6)
    
    def _set_options(self, kw):
        'Set default options for attaching.'
        kw.setdefault('xoptions', gtk.EXPAND|gtk.FILL)
        kw.setdefault('yoptions', gtk.FILL)
        kw.setdefault('xpadding', WIDGET_SPACING)
        kw.setdefault('ypadding', 0)
    
    def attach_widget(self, widget, label, x=0, y=0, w=1, h=1, **kw):
        'Add a widget.'
        x1 = x*2
        x2 = x*2+w*2
        y1 = y
        y2 = y+h
        if label:
            self.attach_label(label, x, y, 1, h, internal=True)
            x1 += 1
        
        self._set_options(kw)
        self.attach(widget, x1, x2, y1, y2, **kw)
    
    def attach_spinner(self, adjust, climb_rate=0.0, digits=0, label=None,
                       x=0, y=0, w=1, h=1, **kw):
        'Add a spinner widget.'
        widget = gtk.SpinButton(adjust, climb_rate, digits)
        self.attach_widget(widget, label, x, y, w, h, **kw)
        return widget
    
    def attach_combo(self, options, value, label, x=0, y=0, w=1, h=1, **kw):
        'Adds a combo widget.'
        widget = gtk.combo_box_new_text()
        for i in range(len(options)):
            widget.append_text(options[i])
            if options[i] == value:
                widget.set_active(i)
        self.attach_widget(widget, label, x, y, w, h, **kw)
        return widget
    
    def attach_label(self, label, x=0, y=0, w=1, h=1, **kw):
        'Add a label widget.'
        label2 = gtk.Label(label)
        label2.set_alignment(1.0, 0.0)
        if 'internal' not in kw:
            w *= 2
        else:
            kw.setdefault('xoptions', gtk.FILL)
            del kw['internal']
        self._set_options(kw)
        self.attach(label2, x*2, x*2+w, y, y+h, **kw)
        return label2

def set_active_text(combo, text):
    "A convenience method to select the value matching the given text."
    itr = combo.get_model().get_iter_first()
    while itr:
        if combo.get_model().get_value(itr, 0) == text:
            combo.set_active_iter(itr)
            return True
        itr = combo.get_model().iter_next(itr)
    return False

## Old Methods ##
def Table(rows):
    'Returns a gtk Table.'
    table = gtk.Table(rows, 4)
    table.set_row_spacings(8)
    table.set_border_width(6)
    return table

def append_entry(table, label, value, top, max_len=0):
    'Adds a text entry widget to a table and returns it.'
    set_label(table, label, top)
    
    entry = gtk.Entry(max_len)
    if value:
        entry.set_text(value)
    table.attach(entry, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, WIDGET_SPACING)
    return entry

def append_textview(table, label, value, top):
    'Adds a textview widget to a table and returns it'
    set_label(table, label, top)
    
    textview = gtk.TextView()
    try:
        gtkspell.Spell(textview)
    except Exception:
        pass
    textview.set_size_request(250, 200)
    if value:
        textview.get_buffer().set_text(value)
    scroll = gtk.ScrolledWindow()
    scroll.add(textview)
    scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
    scroll.set_shadow_type(gtk.SHADOW_IN)
    table.attach(scroll, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL,
            gtk.EXPAND|gtk.FILL, WIDGET_SPACING)
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
    table.attach(filech, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, WIDGET_SPACING)
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
    table.attach(filech, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, WIDGET_SPACING)
    return filech

def append_color(table, label, value, top, alpha=False):
    'Adds a color widget to a table and returns it.'
    set_label(table, label, top)
    
    if isinstance(value[0], tuple):
        buttons = []
        cnt = 2
        for v in value:
            button = gtk.ColorButton(gtk.gdk.Color(int(v[0]), int(v[1]), int(v[2])))
            if(alpha):
                button.set_use_alpha(True)
            table.attach(button, cnt, cnt+1, top, top+1, gtk.EXPAND|gtk.FILL, 0, WIDGET_SPACING)
            cnt += 1
            buttons.append(button)
        return buttons
    else:
        button = gtk.ColorButton(gtk.gdk.Color(int(value[0]), int(value[1]),
                                 int(value[2])))
        table.attach(button, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0,
                     WIDGET_SPACING)
        if(alpha):
            button.set_use_alpha(True)
            #button.set_alpha(int(value[3]))
        return button

def append_spinner(table, label, adjustment, top):
    'Adds a spinner widget to a table and returns it.'
    set_label(table, label, top)
    
    spinner = gtk.SpinButton(adjustment, 2.0)
    table.attach(spinner, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, WIDGET_SPACING)
    return spinner

def append_combo(table, label, options, value, top):
    'Adds a combo widget to a table and returns it.'
    set_label(table, label, top)
    
    combo = gtk.combo_box_new_text()
    for i in range(len(options)):
        combo.append_text(options[i])
        if options[i] == value:
            combo.set_active(i)
    table.attach(combo, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, WIDGET_SPACING)
    return combo

def append_combo_entry(table, label, options, value, top):
    'Adds a combo widget to a table and returns it.'
    set_label(table, label, top)
    
    combo = gtk.combo_box_entry_new_text()
    for i in range(len(options)):
        combo.append_text(options[i])
    if value:
        combo.child.set_text(value)
    table.attach(combo, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, WIDGET_SPACING)
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
        list.append(options[i])
        if options[i][0] == value:
            combo.set_active(i)
    if not value:
        combo.set_active(0)
    table.attach(combo, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, WIDGET_SPACING)
    return combo

def append_radio(table, label, active, top, group=None):
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
    table.attach(lang, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, WIDGET_SPACING)
    return lang

def append_checkbutton(table, label, buttonlabel, top):
    set_label(table, label, top)
    cb = gtk.CheckButton(buttonlabel)
    table.attach(cb, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, WIDGET_SPACING)
    return cb

def append_font_button(table, label, fontname, top):
    set_label(table, label, top)
    fb = gtk.FontButton(fontname)
    table.attach(fb, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, WIDGET_SPACING)
    return fb

def append_hscale(table, label, adjustment, top):
    set_label(table, label, top)
    s = gtk.HScale(adjustment)
    table.attach(s, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, WIDGET_SPACING)
    return s

def append_hbox(table, label, hbox, top):
    'Adds a HBox widget to a table and returns it.'
    set_label(table, label, top)
    table.attach(hbox, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, WIDGET_SPACING)
    return hbox

def append_widget(table, label, widget, top):
    'Adds any gtk.Widget to a table and returns it'
    set_label(table, label, top)
    table.attach(widget, 2, 4, top, top+1, gtk.EXPAND|gtk.FILL, 0, WIDGET_SPACING)

def append_section_title(table, title, top):
    'Adds a title for the current section.'
    label = gtk.Label()
    label.set_markup("<b>"+title+"</b>")
    label.set_alignment(0.0, 1.0)
    table.attach(label, 0, 4, top, top+1, gtk.FILL, 0, 0)

def append_comment(table, title, top):
    label = gtk.Label()
    label.set_markup("<i><small>"+title+"</small></i>")
    label.set_line_wrap(True)
    label.set_alignment(0.0, 1.0)
    table.attach(label, 0, 4, top, top+1, gtk.EXPAND, 0, 0)

def append_separator(table, top):
    table.attach(gtk.HSeparator(), 0, 4, top, top+1, gtk.FILL, 0, 0)

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


def del_treeview_row(button, treeview):
    "Remove the selected row from a treeview."
    (model, itr) = treeview.get_selection().get_selected()
    if itr:
        model.remove(itr)

def edit_treeview_row_btn(btn, treeview, func, edit=False):
    "Add or edit a meta element."
    path = None
    col = None
    if edit:
        (model, itr) = treeview.get_selection().get_selected()
        path = model.get_path(itr)
    func(treeview, path, col, edit)

def filechooser_preview(file_chooser, preview):
    "Updates `preview` gtk.Image widget with the currently selected file."
    global __pb_cache
    filename = file_chooser.get_preview_filename()
    try:
        if filename not in __pb_cache:
            __pb_cache[filename] = gtk.gdk.pixbuf_new_from_file_at_size(filename,
                                                                        256, 256)
        preview.set_from_pixbuf(__pb_cache[filename])
        have_preview = True
    except:
        have_preview = False
    file_chooser.set_preview_widget_active(have_preview)

def update_image_preview(preview, filename):
    "Updates `preview` gtk.Image widget with the currently selected file."
    global __pb_cache
    if not filename:
        return False
    try:
        if filename not in __pb_cache:
            __pb_cache[filename] = gtk.gdk.pixbuf_new_from_file_at_size(filename,
                                                                        256, 256)
        preview.set_from_pixbuf(__pb_cache[filename])
    except:
        pass
