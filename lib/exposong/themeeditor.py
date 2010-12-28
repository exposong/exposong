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
import sys
import os

import gui
import theme
#import screen

class ThemeEditor(gtk.Window):
    """
    Provides a simple interface for creating and editing themes
    """
    def __init__(self, parent=None, filename=None):
        gtk.Window.__init__(self)
        self.connect("destroy", self._destroy)
        self.set_transient_for(parent)
        self.set_title(_("Theme Editor"))
        
        self._do_layout()
        
        if filename:
            self._load_theme(filename)
        
        self.show_all()
        #self.show()
        
    def _do_layout(self):
        main_v = gtk.VBox()
        
        # Title entry
        title_table = gui.Table(1)
        self.title_entry = gui.append_entry(title_table, _("Theme Name"), _("New Theme"), 0)
        main_v.pack_start(title_table)
        
        notebook = gtk.Notebook()
        main_v.pack_start(notebook, True, True, 5)
        
        ######################
        # Page 1: Background #
        ######################
        bg_top_table = gui.Table(1)
        #gui.append_section_title(bg_top_table, "Type", 0)
        type_h = gtk.HBox()
        self.imageradio = gtk.RadioButton(None, _("Image"))
        self.imageradio.connect('toggled', self._on_imageradio)
        type_h.pack_start(self.imageradio)
        self.solidradio = gtk.RadioButton(self.imageradio, _("Solid"))
        self.solidradio.connect('toggled', self._on_solidradio)
        type_h.pack_start(self.solidradio)
        self.gradientradio = gtk.RadioButton(self.imageradio, _("Gradient"))
        self.gradientradio.connect('toggled', self._on_gradientradio)
        type_h.pack_start(self.gradientradio)
        gui.append_hbox(bg_top_table, _("Type"), type_h, 0)
        gui.append_separator(bg_top_table, 1)
        
        self.bg_main_table = gui.Table(2)
        self._on_imageradio(self.imageradio)
        
        tab_bg = gtk.VBox()
        tab_bg.pack_start(bg_top_table)
        tab_bg.pack_start(self.bg_main_table)
        notebook.append_page(tab_bg, gtk.Label(_("Background")))
        
        
        ######################
        # Page 2: Body Text  #
        ######################
        body_h = gtk.HBox()
        body_table_left = gui.Table(5)
        self.body_font_button = gui.append_font_button(body_table_left, _("Font"), "Sans Bold", 0)
        gui.append_comment(body_table_left, _("Font size might be scaled down if it doesn't fit."),1)
        self.body_color_button = gui.append_color(body_table_left, "Color", (255,255,255), 2)
        #self.body_max_font_spinner = gui.append_spinner(body_table_left, "Max. Font Size",
        #        gtk.Adjustment(32, 1, 120, 1, 10, 0), 2)
        self.body_shadow_cb = gui.append_checkbutton(body_table_left, _("Text Shadow"), _("Display Shadow"), 3)
        self.body_shadow_cb.set_active(True)
        self.body_shadow_color = gui.append_color(body_table_left, "", (50,10,100), 4)
        self.body_shadow_cb.connect("toggled", lambda cb:\
                self.body_shadow_color.set_sensitive(self.body_shadow_cb.get_active()))
        body_h.pack_start(body_table_left)
        body_h.pack_start(gtk.VSeparator())
        
        body_table_right = gui.Table(3)
        self.body_line_distance = gui.append_spinner(body_table_right, _("Line Distance"),
                gtk.Adjustment(1, 1, 10, 1, 5, 0), 0)
        self.body_text_align = gui.append_combo(body_table_right, _("Text Align"),
                (_("Center"), _("Left"), _("Right")), _("Center"), 1)
        self.body_hor_align = gui.append_combo(body_table_right, "Text Horizontal Align",
                (_("Top"), _("Bottom"), _("Center")), _("Top"), 2)
        
        body_h.pack_start(body_table_right)
        notebook.append_page(body_h, gtk.Label(_("Body Text")))
       
        #######################
        # Page 3: Footer Text #
        #######################
       
        #footer_h = gtk.HBox()
        footer_table_left = gui.Table(4)
        self.footer_font_button = gui.append_font_button(footer_table_left,
                _("Font"), "Sans 10", 0)
        self.footer_color_button = gui.append_color(footer_table_left, _("Color"),
                (0,0,0), 1)
        self.footer_line_distance = gui.append_spinner(footer_table_left,
                _("Line Distance"), gtk.Adjustment(1, 1, 10, 1, 5, 0), 2)
        self.footer_text_align = gui.append_combo(footer_table_left, _("Text Align"),
                (_("Center"), _("Left"), _("Right")), _("Left"), 3)
        #footer_h.pack_start(footer_table_left)
        #footer_h.pack_start(gtk.VSeparator())
        
        #footer_table_right = gui.Table(4)
        #gui.append_section_title(footer_table_right, "Display Information", 0)
        #gui.append_checkbutton(footer_table_right, "", "Authors", 1)
        #gui.append_checkbutton(footer_table_right, "", "Copyright", 2)
        #gui.append_checkbutton(footer_table_right, "", "Songbook + Nr.", 3)
        #footer_h.pack_start(footer_table_right)
        
        notebook.append_page(footer_table_left, gtk.Label("Footer Text"))
        
        self.add(main_v)
    
    def _clear_bg_table(self):
        for child in self.bg_main_table.get_children():
            self.bg_main_table.remove(child)
    
    def _on_imageradio(self, radio):
        'Image was selected as background type'
        if radio.get_active():
            self._clear_bg_table()
            self.bg_image_filech = gui.append_file(self.bg_main_table,
                    "Image File", None, 0)
            h = gtk.HBox()
            self.radio_mode_fill = gtk.RadioButton(None, "Fill Screen")
            self.radio_mode_fit = gtk.RadioButton(self.radio_mode_fill, "Fit to Screen Size")
            h.pack_start(self.radio_mode_fill)
            h.pack_start(self.radio_mode_fit)
            gui.append_hbox(self.bg_main_table, "Image Mode", h, 1)
            self.bg_main_table.show()
    
    def _on_gradientradio(self, radio):
        'Gradient was selected as background type'
        if radio.get_active():
            self._clear_bg_table()
            hbox = gtk.HBox()
            #self.grad1 = gtk.ColorButton()
            #self.grad2 = gtk.ColorButton()
            #hbox.pack_start(self.grad1, True, True)
            #hbox.pack_start(self.grad2, True, True)
            graddirlist = [u'\u2192', u'\u2198', u'\u2193', u'\u2199']
            (self.bg_grad_color1, self.bg_grad_color2) = gui.append_color(
                    self.bg_main_table, "Colors", ((0,0,0),(0,255,255)), 0)
            gui.append_combo(self.bg_main_table, "", graddirlist, graddirlist[1], 1)
            self.show_all()
    
    def _on_solidradio(self, radio):
        'Solid was selected as background type'
        if radio.get_active():
            self._clear_bg_table()
            self.bg_solid_color = gui.append_color(self.bg_main_table, "Color", (0,0,0), 0)
            self.show_all()
    
    def _load_theme(self, filenm):
        'Loads a theme from a file into the Theme Editor'
        self.theme = theme.Theme(filenm)
        self.title_entry.set_text(os.path.basename(self.theme.filename))
        
        #################
        # Backgrounds   #
        #################
        if len(self.theme.backgrounds)>1:
            print "Only one background can be set with this editor"
            self.imageradio.set_sensitive(False)
            self.solidradio.set_sensitive(False)
            self.gradientradio.set_sensitive(False)
            self._clear_bg_table()
            gui.append_section_title(self.bg_main_table, "This theme uses\
multiple backgrounds which cannot be edited with this editor.\n\
If you need to change the background, you can edit the theme by hand.\n\
See <a href='http://code.google.com/p/exposong/wiki/ThemeFormat'>Theme Format</a>", 0)
        
        elif len(self.theme.backgrounds) == 1:
            bg = self.theme.backgrounds[0]
            if bg.get_tag() == "solid":
                self.solidradio.set_active(True)
                self.bg_solid_color.set_color(gtk.gdk.Color(bg.color))
            elif bg.get_tag() == "gradiant":
                self.gradientradio.set_active(True)
                self.bg_grad_color1.set_color(gtk.gdk.Color(bg.stops[0].color))
                self.bg_grad_color2.set_color(gtk.gdk.Color(bg.stops[1].color))
            elif bg.get_tag() == "img":
                self.imageradio.set_active(True)
                self.bg_image_filech.set_filename(bg.get_filename())
                if bg.aspect == theme.ASPECT_FILL:
                    self.self.radio_mode_fill.set_active()
                elif bg.aspect == theme.ASPECT_FIT:
                    self.radio_mode_fit.set_active(True)
        
        #################
        # Sections      #
        #################
        body = self.theme.get_body()
        self.body_font_button.set_font_name(body.font)
        self.body_color_button.set_color(gtk.gdk.Color(body.color))
        #TODO: No way to enable/disable shadow
        self.body_shadow_color.set_color(gtk.gdk.Color(body.shadow_color))
        #TODO: Line distance, to be implemented in theme
        #TODO: Alignments
        #print body.valign
        
        footer = self.theme.get_footer()
        self.footer_font_button.set_font_name(footer.font)
        self.footer_color_button.set_color(gtk.gdk.Color(footer.color))
        
    def _destroy(self, widget):
        pass


if __name__ == "__main__":
    ThemeEditor()
    gtk.main()
