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

from exposong import DATA_PATH

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
        
        filename = os.path.join(DATA_PATH, 'theme', 'exposong.xml')
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
        
        gtk.stock_add([('add-background-gradient',_('Add Gradient'), gtk.gdk.MOD1_MASK, 0,
                'pymserv'),
                ('add-background-solid',_('Add Solid Color'), gtk.gdk.MOD1_MASK, 0,
                'pymserv'),
                ('add-background-radial',_('Add Radial Gradient'), gtk.gdk.MOD1_MASK, 0,
                'pymserv'),
               ("add-background-image",_('Add Image'), gtk.gdk.MOD1_MASK, 0,
                'pymserv')])
        
        toolbar = gtk.Toolbar()
        btn = gtk.ToolButton(gtk.stock_lookup('add-background-image')[0])
        btn.set_tooltip_markup(_("Add a new Image Background"))
        btn.connect('clicked', self._on_bg_image)
        toolbar.insert(btn, -1)
        btn = gtk.ToolButton(gtk.stock_lookup('add-background-solid')[0])
        btn.set_tooltip_markup(_("Add a new Solid Color Background"))
        btn.connect('clicked', self._on_bg_solid)
        #title_list.get_selection().connect('changed', self._on_delete_bg)
        toolbar.insert(btn, -1)
        btn = gtk.ToolButton(gtk.stock_lookup('add-background-gradient')[0])
        btn.set_tooltip_markup(_("Add a new gradient Background"))
        btn.connect('clicked', self._on_bg_gradient)
        toolbar.insert(btn, -1)
        btn = gtk.ToolButton(gtk.stock_lookup('add-background-radial')[0])
        btn.set_tooltip_markup(_("Add a new Radial Gradient Background"))
        btn.connect('clicked', self._on_bg_radial_gradient)
        toolbar.insert(btn, -1)
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
        self.treeview_bgs.set_size_request(90,200)
        self.treeview_bgs.set_model(self.bg_model)
        self.bg_model.connect("rows-reordered", self._on_bgs_reordered)
        self.bg_model.connect("row-changed", self._on_bgs_reordered)
        self.treeview_bgs.get_selection().connect("changed", self._on_bg_changed)
        
        bg_left = gui.Table(10)
        gui.append_comment(bg_left, _("Backgrounds will be drawn starting with the first element in this list moving to the last one."), 0)
        bg_left.attach(toolbar, 1, 2, 1, 1+1, gtk.EXPAND|gtk.FILL, 0, gui.WIDGET_SPACING)
        bg_left.attach(self.treeview_bgs, 1, 2, 2, 2+1, gtk.EXPAND|gtk.FILL, 0, gui.WIDGET_SPACING)
        
        bg_right = gtk.VBox()
        #bg_right_top = gui.Table(1)
        #self.bg_type_combo = gui.append_combo(bg_right_top, _("Type"), BACKGROUND_TYPES, BACKGROUND_TYPES[0], 0)
        #self.bg_type_combo.connect('changed', self._on_bg_type_changed)
        self.bg_right_type_area = gui.Table(15)
        #bg_right.pack_start(bg_right_top)
        bg_right.pack_start(self.bg_right_type_area)
        bg_right.pack_start(self._get_position())
        
        #self._on_bg_type_changed(self.bg_type_combo)
        
        
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
        
        ###############
        ### Preview ###
        ###############
        table_right = gui.Table(10)
        gui.append_checkbutton(table_right, "", "Display Example Slide",0)
        
        self.preview = gtk.DrawingArea()
        self.preview.set_size_request(300, int(300*0.75))
        self.preview.connect('expose-event', self._expose)
        self.draw()
        
        gui.append_widget(table_right, "", self.preview, 1)
        
        main_h.pack_end(table_right)
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
    
    #######################
    # Loading Backgrounds #
    #######################
    def _on_bg_image(self, widget=None):
        table = self.bg_right_type_area
        table.resize(4,4)
        table.foreach(lambda w: table.remove(w))
        gui.append_section_title(table, _("Image Background"),0)
        self.bg_image_filech = gui.append_file(table, _("File"), None, 1)
        
        self.bg_image_radio_mode_fill = gtk.RadioButton(None, "Fill Screen")
        self.bg_image_radio_mode_fit = gtk.RadioButton(self.bg_image_radio_mode_fill, "Fit to Screen Size")
        table.attach(self.bg_image_radio_mode_fill, 1, 4, 2, 2+1, gtk.EXPAND|gtk.FILL, 0, gui.WIDGET_SPACING)
        table.attach(self.bg_image_radio_mode_fit, 1, 4, 3, 3+1, gtk.EXPAND|gtk.FILL, 0, gui.WIDGET_SPACING)
        table.show_all()
        
    def _load_bg_image(self):
        bg = self._get_active_bg()
        self.bg_image_filech.set_filename(
                os.path.join(DATA_PATH, 'theme', 'res', bg.src))
        if bg.aspect == theme.ASPECT_FILL:
            self.bg_image_radio_mode_fill.set_active(True)
        else:
            self.bg_image_radio_mode_fit.set_active(True)
        
    def _on_bg_solid(self, widget=None):
        table = self.bg_right_type_area
        table.resize(1,4)
        table.foreach(lambda w: table.remove(w))
        self.bg_solid_color_btn = gui.append_color(table, _("Color"), (0,0,0), 0, alpha=True)
        self.bg_solid_color_btn.connect('color-set', self._on_solid_bg_changed)
        self.bg_solid_color_btn.show()
        #table.show_all()
    
    def _load_bg_solid(self):
        bg = self._get_active_bg()
        self.bg_solid_color_btn.set_color(gtk.gdk.color_parse(bg.color))
        self.bg_solid_color_btn.set_alpha(int(bg.alpha*65535))
        
    def _on_bg_gradient(self, widget=None):
        table = self.bg_right_type_area
        table.resize(6,4)
        table.foreach(lambda w: table.remove(w))
        #gui.append_section_title(table, "Color 1", 1)
        self.bg_gradient_color1 = gui.append_color(table, "Color 1", (255,0,0,255), 1, alpha=True)
        self.bg_gradient_length1 = gui.append_hscale(table, "Length", gtk.Adjustment(value=50,
                lower=0, upper=100, step_incr=1, page_incr=10, page_size=0), 2)
        #gui.append_section_title(table, "Color 2", 4)
        self.bg_gradient_color2 = gui.append_color(table, "Color 2", (255,0,0,255), 3, alpha=True)
        self.bg_gradient_length2 = gui.append_hscale(table, "Length", gtk.Adjustment(value=50,
                lower=0, upper=100, step_incr=1, page_incr=10, page_size=0), 4)
        
        self.bg_gradient_angle = gui.append_hscale(table, "Angle", gtk.Adjustment(value=0, lower=0,
                        upper=360, step_incr=1, page_incr=10, page_size=0), 5)
        table.show_all()
    
    def _load_bg_gradient(self):
        bg = self._get_active_bg()
        if len(bg.stops) > 2:
            pass #TODO: Dialog
        
        self.bg_gradient_color1.set_color(gtk.gdk.color_parse(bg.stops[0].color))
        self.bg_gradient_color1.set_alpha(int(bg.stops[0].alpha*65535))
        self.bg_gradient_length1.set_value(bg.stops[0].location*100)
        self.bg_gradient_color2.set_color(gtk.gdk.color_parse(bg.stops[1].color))
        self.bg_gradient_color2.set_alpha(int(bg.stops[1].alpha*65535))
        self.bg_gradient_length2.set_value(bg.stops[1].location*100)
        self.bg_gradient_angle.set_value(bg.angle)
    
    def _on_bg_radial_gradient(self, widget=None):
        table = self.bg_right_type_area
        table.resize(8,4)
        table.foreach(lambda w: table.remove(w))
        self._bg_radial_color1 = gui.append_color(table, "Color 1", (255,0,0,255), 1,True)
        self._bg_radial_length1 = gui.append_hscale(table, "Length", gtk.Adjustment(value=50,
                lower=0, upper=100, step_incr=1, page_incr=10, page_size=0), 2)
        #gui.append_section_title(table, "Color 2", 4)
        self._bg_radial_color2 = gui.append_color(table, "Color 2", (255,0,0,255), 3, True)
        self._bg_radial_length2 = gui.append_hscale(table, "Length", gtk.Adjustment(value=50,
                lower=0, upper=100, step_incr=1, page_incr=10, page_size=0), 4)
        #scale = gtk.HScale(gtk.Adjustment(value=0, lower=0, upper=360, step_incr=1, page_incr=10, page_size=0))
        gui.append_hscale(table, "Overall Length", gtk.Adjustment(value=0, lower=0, upper=100, step_incr=1, page_incr=10, page_size=0), 5)
        gui.append_spinner(table, "Horizontal Position", gtk.Adjustment(value=0, lower=0, upper=100, step_incr=1, page_incr=10, page_size=0),6)
        gui.append_spinner(table, "Vertical Position", gtk.Adjustment(value=0, lower=0, upper=100, step_incr=1, page_incr=10, page_size=0),7)
        table.show_all()
    
    def _load_bg_radial_gradient(self):
        pass
    
    def _load_bg_position(self):
        bg = self._get_active_bg()
        self._p['lf'].set_value(bg.pos[0])
        self._p['rt'].set_value(bg.pos[2])
        self._p['tp'].set_value(bg.pos[1])
        self._p['bt'].set_value(bg.pos[3])
    
    def _get_active_bg(self):
        (model, iter) = self.treeview_bgs.get_selection().get_selected()
        if iter:
            return model.get_value(iter, 0)
        return None
    
    def _on_bgs_reordered(self, model, path, iter=None, new_order=None):
        self._update_bg_list_from_model()
        self.draw()
    
    def _update_bg_list_from_model(self):
        self.theme.backgrounds = []
        for bg in self.bg_model:
            self.theme.backgrounds.append(bg[0])
    
    def _on_bg_changed(self, widget):
        bg = self._get_active_bg()
        if not bg:
            return
        if isinstance(bg, theme.ImageBackground):
            self._on_bg_image()
            self._load_bg_image()
        elif isinstance(bg, theme.ColorBackground):
            self._on_bg_solid()
            self._load_bg_solid()
        elif isinstance(bg, theme.GradientBackground):
            self._on_bg_gradient()
            self._load_bg_gradient()
        elif isinstance(bg, theme.RadialGradientBackground):
            self._on_bg_radial_gradient()
            self._load_bg_radial_gradient()
        self._load_bg_position()
    
    def _on_solid_bg_changed(self, btn, *args):
        #color = btn.get_color()
        (model, iter) = self.treeview_bgs.get_selection().get_selected()
        if iter:
            model.get_value(iter, 0).color = btn.get_color().to_string()
        self.theme.save()
    
    def _on_delete_bg(self, *args):
        (model, itr) = self.treeview_bgs.get_selection().get_selected()
        if not itr:
            return False
        msg = _("Are you sure you want to delete this background?")
        dialog = gtk.MessageDialog(self, gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                                   msg)
        dialog.set_title( _('Delete Background?') )
        resp = dialog.run()
        dialog.hide()
        if resp == gtk.RESPONSE_YES:
            model.remove(itr)
            self._update_bg_list_from_model()
            self.draw()
    
    def _bg_get_row_text(self, column, cell, model, titer):
        bg = model.get_value(titer, 0)
        cell.set_property('text', bg.get_name())
    
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
        if self.__updating:
            return
        
        self.__updating = True
        el = self._get_active_bg()
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
    
    def _set_changed(self):
        self.changed = True
        if not self.get_title().startswith("*"):
            self.set_title("*%s"%self.get_title())
    
    def _load_theme(self, filenm):
        'Loads a theme from a file into the Theme Editor'
        self.theme = theme.Theme(filenm)
        self.title_entry.set_text(self.theme.get_title())
        
        #################
        # Backgrounds   #
        for bg in self.theme.backgrounds:
            self.bg_model.append((bg,))
        
        ##################
        # Sections: Body #
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