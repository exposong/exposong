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
import pango
import gobject

import gui
import theme
#import themeselect
#import screen

BACKGROUND_TYPES = [_("Image"),  _("Color"), _("Gradient"), _("Radial Gradient")]

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
        
        self.__updating = False
        
        filename = "/home/sam/exposong/data/theme/exposong.xml"
        if filename:
            self._load_theme(filename)
        
        self.show_all()
        #self.show()
        
    def _do_layout(self):
        main_h = gtk.HBox()
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
        #bg_top_table = gui.Table(1)
        ##gui.append_section_title(bg_top_table, "Type", 0)
        #type_h = gtk.HBox()
        #self.imageradio = gtk.RadioButton(None, _("Image"))
        #self.imageradio.connect('toggled', self._on_imageradio)
        #type_h.pack_start(self.imageradio)
        #self.solidradio = gtk.RadioButton(self.imageradio, _("Solid"))
        #self.solidradio.connect('toggled', self._on_solidradio)
        #type_h.pack_start(self.solidradio)
        #self.gradientradio = gtk.RadioButton(self.imageradio, _("Gradient"))
        #self.gradientradio.connect('toggled', self._on_gradientradio)
        #type_h.pack_start(self.gradientradio)
        #gui.append_hbox(bg_top_table, _("Type"), type_h, 0)
        #gui.append_separator(bg_top_table, 1)
        
        #self.bg_main_table = gui.Table(2)
        #self._on_imageradio(self.imageradio)
        #
        #tab_bg = gtk.VBox()
        #tab_bg.pack_start(bg_top_table)
        #tab_bg.pack_start(self.bg_main_table)
        
        #gui.append_section_title(bg_left, "Background List", 0)
        
        self.treeview_bgs = gtk.TreeView()
        self.treeview_bgs.set_reorderable(True)
        
        toolbar = gtk.Toolbar()
        button = gtk.ToolButton(gtk.STOCK_ADD)
        #button.connect('clicked', self._on_solid_bg)
        toolbar.insert(button, -1)
        button = gtk.ToolButton(gtk.STOCK_EDIT)
        #button.connect('clicked', self._on_edit_bg)
        #title_list.get_selection().connect('changed', self._on_delete_bg)
        toolbar.insert(button, -1)
        button = gtk.ToolButton(gtk.STOCK_DELETE)
        button.connect('clicked', self._on_delete_bg)
        #title_list.get_selection().connect('changed',
        #                                   gui.treesel_disable_widget, button)
        toolbar.insert(button, -1)
        
        self.bg_model = gtk.ListStore(gobject.TYPE_PYOBJECT)
        column_bgs = gtk.TreeViewColumn(_("Backgrounds"))
        textrend = gtk.CellRendererText()
        column_bgs.pack_start(textrend)
        column_bgs.set_cell_data_func(textrend, self._bg_get_row_text)
        self.treeview_bgs.append_column(column_bgs)
        self.treeview_bgs.set_size_request(100,200)
        self.treeview_bgs.set_model(self.bg_model)
        self.bg_model.connect("rows-reordered", self._on_bgs_reordered)
        self.bg_model.connect("row-changed", self._on_bgs_reordered)
        
        bg_left = gui.Table(10)
        gui.append_comment(bg_left, _("Backgrounds will be drawn starting with the first element in this list moving to the last one."), 0)
        bg_left.attach(toolbar, 1, 2, 1, 1+1, gtk.EXPAND|gtk.FILL, 0, gui.WIDGET_SPACING)
        bg_left.attach(self.treeview_bgs, 1, 2, 2, 2+1, gtk.EXPAND|gtk.FILL, 0, gui.WIDGET_SPACING)
        
        bg_right = gtk.VBox()
        bg_right_top = gui.Table(1)
        self.bg_type_combo = gui.append_combo(bg_right_top, _("Type"), BACKGROUND_TYPES, BACKGROUND_TYPES[0], 0)
        self.bg_type_combo.connect('changed', self._on_bg_type_changed)
        self.bg_right_type_area = gui.Table(15)
        bg_right.pack_start(bg_right_top)
        bg_right.pack_start(self.bg_right_type_area)
        bg_right.pack_start(self._get_position())
        
        self._on_bg_type_changed(self.bg_type_combo)
        
        
        bgbox = gtk.HBox()
        bgbox.pack_start(bg_left)
        bgbox.pack_start(gtk.VSeparator())
        bgbox.pack_start(bg_right)
        notebook.append_page(bgbox, gtk.Label(_("Background")))
        
        
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
        # Order for horizontal align must be the same as theme.TOP, theme.MIDDLE, theme.BOTTOM
        self.body_hor_align = gui.append_combo(body_table_right, "Text Vertical Align",
                (_("Top"), _("Middle"), _("Bottom")), _("Middle"), 2)
        
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
        
        main_h.pack_start(main_v)
        table_right = gui.Table(10)
        gui.append_checkbutton(table_right, "", "Display Example Slide",0)
        
        self.preview = gtk.DrawingArea()
        self.preview.set_size_request(300, int(300*0.75))
        self.preview.connect('expose-event', self._expose)
        self.draw()
        
        gui.append_widget(table_right, "", self.preview, 1)
        
        main_h.pack_start(table_right)
        self.add(main_h)
        self.show_all()
    
    def draw(self):
        self.preview.queue_draw()
    
    def _expose(self, widget, event):
        ccontext = widget.window.cairo_create()
        bounds = widget.get_size_request()
        #ccontext.scale(float(400)/bounds[0],
        #                float(300)/bounds[1])
        _example_slide = _ExampleSlide()
        self.theme.render(ccontext, bounds, _example_slide)
        return True
    
    def _on_bgs_reordered(self, model, path, iter=None, new_order=None):
        self.theme.backgrounds = []
        for bg in model:
            self.theme.backgrounds.append(bg[0])
        self.draw()
        
    def _on_bg_type_changed(self, widget):
        table = self.bg_right_type_area
        table.foreach(lambda w: table.remove(w))
        active = widget.get_active_text()
        if active == BACKGROUND_TYPES[0]: #Image
            self.bg_image_filech = gui.append_file(table,
                    _("Image File"), None, 0)
            h = gtk.HBox()
            self.radio_mode_fill = gtk.RadioButton(None, "Fill Screen")
            self.radio_mode_fit = gtk.RadioButton(self.radio_mode_fill, "Fit to Screen Size")
            h.pack_start(self.radio_mode_fill)
            h.pack_start(self.radio_mode_fit)
            gui.append_hbox(table, "Image Mode", h, 1)
            
        elif active == BACKGROUND_TYPES[1]: #Color
            self.bg_single_color_btn = gui.append_color(table, _("Color"), (0,0,0), 0)
            self.bg_single_color_btn.connect('color-set', self._on_solid_bg_changed)
            
        elif active == BACKGROUND_TYPES[2]: #Gradient
            #gui.append_section_title(table, "Color 1", 1)
            gui.append_color(table, "Color 1", (255,0,0), 1)
            gui.append_hscale(table, "Length", gtk.Adjustment(value=50,
                    lower=0, upper=100, step_incr=1, page_incr=10, page_size=0), 2)
            #gui.append_section_title(table, "Color 2", 4)
            gui.append_color(table, "Color 2", (255,0,0), 3)
            gui.append_hscale(table, "Length", gtk.Adjustment(value=50,
                    lower=0, upper=100, step_incr=1, page_incr=10, page_size=0), 4)
            
            gui.append_hscale(table, "Angle", gtk.Adjustment(value=0, lower=0, upper=360, step_incr=1, page_incr=10, page_size=0), 5)
            
        elif active == BACKGROUND_TYPES[3]: #Radial Gradient
            gui.append_color(table, "Color 1", (255,0,0,255), 1,True)
            gui.append_hscale(table, "Length", gtk.Adjustment(value=50,
                    lower=0, upper=100, step_incr=1, page_incr=10, page_size=0), 2)
            #gui.append_section_title(table, "Color 2", 4)
            gui.append_color(table, "Color 2", (255,0,0,255), 3, True)
            gui.append_hscale(table, "Length", gtk.Adjustment(value=50,
                    lower=0, upper=100, step_incr=1, page_incr=10, page_size=0), 4)
            scale = gtk.HScale(gtk.Adjustment(value=0, lower=0, upper=360, step_incr=1, page_incr=10, page_size=0))
            gui.append_hscale(table, "Overall Length", gtk.Adjustment(value=0, lower=0, upper=100, step_incr=1, page_incr=10, page_size=0), 5)
            gui.append_spinner(table, "Horizontal Position", gtk.Adjustment(value=0, lower=0, upper=100, step_incr=1, page_incr=10, page_size=0),6)
            gui.append_spinner(table, "Vertical Position", gtk.Adjustment(value=0, lower=0, upper=100, step_incr=1, page_incr=10, page_size=0),7)

        table.show_all()
    
    def _gradient_points(self):
        pass
    
    def _on_solid_bg_changed(self, btn, *args):
        #color = btn.get_color()
        (model, iter) = self.treeview_bgs.get_selection().get_selected()
        if iter:
            model.get_value(iter, 0).color = btn.get_color().to_string()
        self.theme.save()
    
    def _on_delete_bg(self, *args):
        pass
    
    def _bg_get_row_text(self, column, cell, model, titer):
        bg = model.get_value(titer, 0)
        cell.set_property('text', bg.get_name())
        #if isinstance(bg, theme.ColorBackground):
        #    cell.set_property('text', _("Color"))
        #elif isinstance(bg, theme.GradientBackground):
        #    cell.set_property('text', _("Gradiant"))
        #elif isinstance(bg, theme.RadialGradientBackground):
        #    cell.set_property('text', _("Radial Gradient"))
        #elif isinstance(bg, theme.ImageBackground):
        #    cell.set_property('text', _("Image"))
    
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
    
    def _get_position(self):
        "Return the element positioning settings."
        position = gtk.Expander(_("Element Position"))
        # Positional elements for backgrounds
        table = gui.ESTable(5,2)
        self._p = {}
        
        adjust = gtk.Adjustment(0, 0.0, 1.0, 0.01, 0.10)
        self._p['lf'] = table.attach_spinner(adjust, 0.02, 2, _('Left:'), 0, 0)
        self._p['lf'].set_numeric(True)
        self._p['lf'].connect('changed', self._on_change_pos)
        
        adjust = gtk.Adjustment(0, 0.0, 1.0, 0.01, 0.10)
        self._p['rt'] = table.attach_spinner(adjust, 0.02, 2, _('Right:'), 1, 0)
        self._p['rt'].set_numeric(True)
        self._p['rt'].connect('changed', self._on_change_pos)
        
        adjust = gtk.Adjustment(0, 0.0, 1.0, 0.01, 0.10)
        self._p['tp'] = table.attach_spinner(adjust, 0.02, 2, _('Top:'), 0, 1)
        self._p['tp'].set_numeric(True)
        self._p['tp'].connect('changed', self._on_change_pos)
        
        adjust = gtk.Adjustment(0, 0.0, 1.0, 0.01, 0.10)
        self._p['bt'] = table.attach_spinner(adjust, 0.02, 2, _('Bottom:'), 1, 1)
        self._p['bt'].set_numeric(True)
        self._p['bt'].connect('changed', self._on_change_pos)
        
        position.add(table)
        return position
    
    def _on_change_pos(self, editable):
        """Update the position on change.
        
        `pos.right` will be updated to be larger than `pos.left`. Same for
        top and bottom."""
        print self.__updating
        if self.__updating:
            return
        
        self.__updating = True
        el = self.get_selected_element()
        if el is False:
            self.__updating = False
            return False
        
        lf = self._p['lf'].get_value()
        rt = self._p['rt'].get_value()
        tp = self._p['tp'].get_value()
        bt = self._p['bt'].get_value()
            
        if rt <= lf:
            if editable == self._p['rt']:
                lf = rt - 0.01
                self._p['lf'].set_value(lf)
            else:
                rt = lf + 0.01
                self._p['rt'].set_value(lf)
        if bt <= tp:
            if editable == self._p['bt']:
                tp = bt - 0.01
                self._p['tp'].set_value(tp)
            else:
                bt = tp + 0.01
                self._p['bt'].set_value(bt)
        el.pos[0] = lf
        el.pos[1] = tp
        el.pos[2] = rt
        el.pos[3] = bt
        self.__updating = False
        self._set_changed()
    
    def get_selected_element(self):
        model, itr = self.treeview_bgs.get_selection().get_selected()
        if itr:
            return model.get_value(itr, 0)
        else:
            return False
    
    def _set_changed(self):
        self.changed = True
        if not self.get_title().startswith("*"):
            self.set_title("*%s"%self.get_title())
    
    def _load_theme(self, filenm):
        'Loads a theme from a file into the Theme Editor'
        self.theme = theme.Theme(filenm)
        self.title_entry.set_text(os.path.basename(self.theme.filename))
        
        #################
        # Backgrounds   #
        #################
        if len(self.theme.backgrounds)>0:
            for bg in self.theme.backgrounds:
                self.bg_model.append((bg,))
            
#        if len(self.theme.backgrounds)>1:
#            print "Only one background can be set with this editor"
#            self.imageradio.set_sensitive(False)
#            self.solidradio.set_sensitive(False)
#            self.gradientradio.set_sensitive(False)
#            self._clear_bg_table()
#            gui.append_section_title(self.bg_main_table, "This theme uses\
#multiple backgrounds which cannot be edited with this editor.\n\
#If you need to change the background, you can edit the theme by hand.\n\
#See <a href='http://code.google.com/p/exposong/wiki/ThemeFormat'>Theme Format</a>", 0)
#        
#        elif len(self.theme.backgrounds) == 1:
#            bg = self.theme.backgrounds[0]
#            if bg.get_tag() == "solid":
#                self.solidradio.set_active(True)
#                self.bg_solid_color.set_color(gtk.gdk.Color(bg.color))
#            elif bg.get_tag() == "gradient":
#                self.gradientradio.set_active(True)
#                self.bg_grad_color1.set_color(gtk.gdk.Color(bg.stops[0].color))
#                self.bg_grad_color2.set_color(gtk.gdk.Color(bg.stops[1].color))
#            elif bg.get_tag() == "img":
#                self.imageradio.set_active(True)
#                self.bg_image_filech.set_filename(bg.get_filename())
#                if bg.aspect == theme.ASPECT_FILL:
#                    self.self.radio_mode_fill.set_active()
#                elif bg.aspect == theme.ASPECT_FIT:
#                    self.radio_mode_fit.set_active(True)
        
        ##################
        # Sections: Body #
        ##################
        body = self.theme.get_body()
        self.body_font_button.set_font_name(body.font)
        self.body_color_button.set_color(gtk.gdk.Color(body.color))
        #TODO: No way to enable/disable shadow
        self.body_shadow_color.set_color(gtk.gdk.Color(body.shadow_color))
        #TODO: Line distance, to be implemented in theme
        
        t = theme.Text("This is an example text")
        # Horizontal Alignment
        for i in range(len(align)):
            if align[i] == align[t.align]:
                self.body_text_align.set_active(i)
        # Vertical Alignment
        self.body_hor_align.set_active(t.valign)
        
        ####################
        # Sections: Footer #
        ####################
        footer = self.theme.get_footer()
        self.footer_font_button.set_font_name(footer.font)
        self.footer_color_button.set_color(gtk.gdk.Color(footer.color))
        
    def _destroy(self, widget):
        #self.theme.save()
        global __name__
        self.hide()
        self.destroy()
        if __name__ == "__main__":
        	gtk.main_quit()

align = {
    pango.ALIGN_LEFT : "Left",
    pango.ALIGN_RIGHT : "Right",
    pango.ALIGN_CENTER : "Center"
}

class _ExampleSlide(object):
    """
    A slide to draw as an example for the theme selection widget.
    """
    def __init__(self):
        object.__init__(self)
        self.body = [
                theme.Text('\n'.join([
                    'Lorem ipsum dolor sit amet, consectetur adipiscing elit.'
                    'Phasellus magna eros, congue vel euismod ut, suscipit nec sapien.'
                    'Vestibulum vel est augue, quis viverra elit.'
                    'Sed quis arcu sit amet dui lobortis accumsan sed eget tellus.'
                    'Sed elit est, suscipit sit amet euismod quis, placerat ac neque.'
                    'Maecenas ac diam porttitor sem porttitor dictum.']),
                    pos=[0.0, 0.0, 1.0, 1.0], margin=10,
                    align=theme.CENTER, valign=theme.MIDDLE),
                ]
        self.foot = []

    def get_body(self):
        return self.body
    
    def get_footer(self):
        return self.foot
    
    def get_slide(self):
        return NotImplemented

if __name__ == "__main__":
    ThemeEditor()
    gtk.main()