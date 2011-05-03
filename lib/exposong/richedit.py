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
import pango
#import undobuffer

# TODO Move clipboard to main.py
_display = gtk.gdk.display_manager_get().get_default_display()
_clipboard = gtk.Clipboard(_display, "CLIPBOARD")
del _display

class Editor(gtk.VBox):
    """
    Provides a rich text editing widget that will allow output to pango markup
    language.
    """
    def __init__(self):
        gtk.VBox.__init__(self)

        #TODO UndoableBuffer is not compatible with formatted entry.
        #self.buffer_ = undobuffer.UndoableBuffer()
        self.buffer_ = gtk.TextBuffer()
        self.editor = gtk.TextView(self.buffer_)
        self._create_tags()

        scroll = gtk.ScrolledWindow()
        scroll.add(self.editor)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.ui = self._generate_ui()
        self.toolbar2 = self.ui.get_widget("/toolbar_format")

        self.pack_start(self.toolbar2, False)
        self.pack_start(scroll, True, True)
    
    def _create_tags(self):
        "Creates tags that can be used for the editor."
        self.buffer_.create_tag("bold", weight=pango.WEIGHT_BOLD)
        self.buffer_.create_tag("italic", style=pango.STYLE_ITALIC)
        self.buffer_.create_tag("underline", underline=pango.UNDERLINE_SINGLE)
        self.buffer_.create_tag("strikethrough", strikethrough=True)
        self.buffer_.create_tag("smaller", scale=pango.SCALE_SMALL)
        self.buffer_.create_tag("larger", scale=pango.SCALE_LARGE)
    
    def _generate_ui(self):
        "Generates the toolbar."
        ui_def = """
        <ui>
            <toolbar name="toolbar_format">
                <toolitem action="bold" />
                <toolitem action="italic" />
                <toolitem action="underline" />
                <toolitem action="strikethrough" />
                <toolitem action="smaller" />
                <toolitem action="larger" />
                <separator />
                <!--<toolitem action="undo" />
                <toolitem action="redo" />-->
                <separator />
                <toolitem action="cut" />
                <toolitem action="copy" />
                <toolitem action="paste" />
            </toolbar>
        </ui>
        """

        actions = gtk.ActionGroup("Actions")
        actions.add_actions([
            #("undo", gtk.STOCK_UNDO, _("_Undo"), None, None, self.on_undo),
            #("redo", gtk.STOCK_REDO, _("_Redo"), None, None, self.on_redo),

            ("cut", gtk.STOCK_CUT, _("_Cut"), None, None, self.on_cut),
            ("copy", gtk.STOCK_COPY, _("_Copy"), None, None, self.on_copy),
            ("paste", gtk.STOCK_PASTE, _("_Paste"), None, None, self.on_paste),

            ("bold", gtk.STOCK_BOLD, _("_Bold"), "<ctrl>B", None, self.on_action),
            ("italic", gtk.STOCK_ITALIC, _("_Italic"), "<ctrl>I", None, self.on_action),
            ("underline", gtk.STOCK_UNDERLINE, _("_Underline"), "<ctrl>U", None, self.on_action),
            ("strikethrough", gtk.STOCK_STRIKETHROUGH, _("Strike Through"), None, None, self.on_action),
            ("smaller", None, _("Smaller"), None, None, self.on_size),
            ("larger", None, _("Larger"), None, None, self.on_size),

            #("font", gtk.STOCK_SELECT_FONT, _("Select _Font"), "<ctrl>F", None, self.on_select_font),
            #("color", gtk.STOCK_SELECT_COLOR, _("Select _Color"), None, None, self.on_select_color),
        ])

        ui = gtk.UIManager()
        ui.insert_action_group(actions)
        ui.add_ui_from_string(ui_def)
        return ui

    def on_action(self, action):
        "Apply the action to the selected text."
        tag = self.buffer_.get_tag_table().lookup(action.get_name())
        start, end = self.buffer_.get_selection_bounds()
        itr = start.copy()
        # This commented code would see if all the text had the format, and
        # not just the start and end. It seemed to only work part of the time
        # though:
        #if start.has_tag(tag) and (not itr.forward_to_tag_toggle(tag) or end <= itr):
        if start.has_tag(tag) and (end.has_tag(tag) or end.ends_tag(tag)):
            self.buffer_.remove_tag(tag, start, end)
        else:
            self.buffer_.remove_tag(tag, start, end)
            self.buffer_.apply_tag(tag, start, end)

    def on_size(self, action):
        "Apply the action to the selected text."
        tag = self.buffer_.get_tag_table().lookup(action.get_name())
        print action.get_name(),
        if action.get_name() == 'smaller':
            other = self.buffer_.get_tag_table().lookup('larger')
        else:
            other = self.buffer_.get_tag_table().lookup('smaller')
        start, end = self.buffer_.get_selection_bounds()
        itr = start.copy()
        while itr and itr.compare(end) < 0:
            t = itr.copy()
            itr.forward_char()
            if t.has_tag(other):
                if not t.has_tag(tag):
                    print 'r',
                    self.buffer_.remove_tag(other, t, itr)
            elif not t.has_tag(tag):
                print 'a',
                self.buffer_.apply_tag(tag, t, itr)
        print 

    def on_copy(self, action):
        global _clipboard
        self.buffer_.copy_clipboard(_clipboard)

    def on_cut(self, action):
        global _clipboard
        self.buffer_.cut_clipboard(_clipboard, self.editor.get_editable())

    def on_paste(self, action):
        global _clipboard
        self.buffer_.paste_clipboard(_clipboard, None,
                                     self.editor.get_editable())

    def on_undo(self, action):
        "Revert a change."
        self.buffer_.undo()

    def on_redo(self, action):
        "Redo a change."
        self.buffer_.redo()

    def on_select_font(self, action):
        dialog = gtk.FontSelectionDialog("Select a font")
        if dialog.run() == gtk.RESPONSE_OK:
            fname, fsize = dialog.fontsel.get_family().get_name(), dialog.fontsel.get_size()
            #self.editor.execute_script("document.execCommand('fontname', null, '%s');" % fname)
            #self.editor.execute_script("document.execCommand('fontsize', null, '%s');" % fsize)
        dialog.destroy()

    def on_select_color(self, action):
        dialog = gtk.ColorSelectionDialog("Select Color")
        if dialog.run() == gtk.RESPONSE_OK:
            gc = str(dialog.colorsel.get_current_color())
            color = "#" + "".join([gc[1:3], gc[5:7], gc[9:11]])
            #self.editor.execute_script("document.execCommand('forecolor', null, '%s');" % color)
        dialog.destroy()

    @staticmethod
    def tag_to_markup(tag, open_=True):
        conv = {'bold': 'b',
                'italic': 'i',
                'underline': 'u',
                'strikethrough': 's',
                'smaller': 'small',
                'larger': 'big'}
        name = tag.get_property('name')
        if name in conv:
            if open_:
                return "<%s>" % conv[name]
            else:
                return "</%s>" % conv[name].split(" ")[0]
        return ""

    def get_markup(self):
        itr = self.buffer_.get_start_iter()
        outlist = []
        while itr and not itr.is_end():
            for tag in itr.get_toggled_tags(True):
                outlist.append(self.tag_to_markup(tag))
            outlist.append(itr.get_char())
            for tag in itr.get_toggled_tags(False):
                outlist.append(self.tag_to_markup(tag, False))
            itr.forward_char()
        return "".join(outlist)

## TODO Remove code below after done testing.

class ExampleEditor(gtk.Window):
    def __init__(self):
        gtk.Window.__init__(self)
        self.set_title("Example Editor")
        self.connect("destroy", gtk.main_quit)
        self.resize(500, 500)
        self.filename = None
        vbox = gtk.VBox()

        self.editor = Editor()
        self.add_accel_group(self.editor.ui.get_accel_group())
        vbox.pack_start(self.editor, True, True)

        btn = gtk.Button("Show Source")
        btn.connect('clicked', self._on_show_source)
        vbox.pack_start(btn, False, True)
        self.add(vbox)

    def _on_show_source(self, btn):
        print '-'*15
        print self.editor.get_markup()

try:
    _
except:
    def _(x): return x


if __name__ == "__main__":
    print 'running'
    e = ExampleEditor()
    e.show_all()
    gtk.main()
