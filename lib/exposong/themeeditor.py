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
import shutil
import random
import pango
import gobject

if __name__ == '__main__': #For testing
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import gui
import theme

from exposong import DATA_PATH, RESOURCE_PATH

BACKGROUND_TYPES = [_("Image"),  _("Color"), _("Gradient"), _("Radial Gradient")]

class ThemeEditor(gtk.Window):
    """
    Provides a simple interface for creating and editing themes
    """
    def __init__(self, parent=None, filename=None):
        gtk.Window.__init__(self)
        self.connect("destroy", self._destroy)
        self.set_transient_for(parent)
        self.set_title(_("ExpoSong Theme Editor"))

        self.__updating = False
        self._do_layout()        
        self._load_theme(filename)
        self.show_all()
    
    def _do_layout(self):
        main_h = gtk.HBox()
        main_v = gtk.VBox()
        
        # Title entry
        title_table = gui.ESTable(1)
        self._title_entry = title_table.attach_entry(_("New Theme"), label=_("Theme Name"))
        main_v.pack_start(title_table, False, False)
        
        notebook = gtk.Notebook()
        main_v.pack_start(notebook, True, True, 5)
        
        ######################
        # Page 1: Background #
        ######################
        self._treeview_bgs = gtk.TreeView()
        self._treeview_bgs.set_reorderable(True)
        
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
        btn.connect('clicked', self._on_bg_image_new)
        toolbar.insert(btn, -1)
        btn = gtk.ToolButton(gtk.stock_lookup('add-background-solid')[0])
        btn.set_tooltip_markup(_("Add a new Solid Color Background"))
        btn.connect('clicked', self._on_bg_solid_new)
        #title_list.get_selection().connect('changed', self._on_delete_bg)
        toolbar.insert(btn, -1)
        btn = gtk.ToolButton(gtk.stock_lookup('add-background-gradient')[0])
        btn.set_tooltip_markup(_("Add a new Gradient Background"))
        btn.connect('clicked', self._on_bg_gradient_new)
        toolbar.insert(btn, -1)
        btn = gtk.ToolButton(gtk.stock_lookup('add-background-radial')[0])
        btn.set_tooltip_markup(_("Add a new Radial Gradient Background"))
        btn.connect('clicked', self._on_bg_radial_new)
        toolbar.insert(btn, -1)
        button = gtk.ToolButton(gtk.STOCK_DELETE)
        button.connect('clicked', self._on_delete_bg)
        #title_list.get_selection().connect('changed',
        #                                   gui.treesel_disable_widget, button)
        toolbar.insert(button, -1)
        
        self._bg_model = gtk.ListStore(gobject.TYPE_PYOBJECT)
        self._column_bgs = gtk.TreeViewColumn(_("Backgrounds"))
        textrend = gtk.CellRendererText()
        self._column_bgs.pack_start(textrend)
        self._column_bgs.set_cell_data_func(textrend, self._bg_get_row_text)
        self._treeview_bgs.append_column(self._column_bgs)
        self._treeview_bgs.set_size_request(90,200)
        self._treeview_bgs.set_model(self._bg_model)
        self._bg_model.connect("rows-reordered", self._on_bgs_reordered)
        self._bg_model.connect("row-changed", self._on_bgs_reordered)
        self._treeview_bgs.get_selection().connect("changed", self._on_bg_changed)
        
        bg_left = gtk.VBox()
        gui.append_comment(bg_left, _("Backgrounds will be drawn starting with the first element in this list moving to the last one."), 0)
        bg_left.pack_start(toolbar, False, True, gui.WIDGET_SPACING)
        scroll = gtk.ScrolledWindow()
        scroll.add(self._treeview_bgs)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        bg_left.pack_start(scroll, True, True, gui.WIDGET_SPACING)
        
        bg_right = gtk.VBox()
        self._bg_edit_table = gui.ESTable(15, row_spacing=10, auto_inc_y=True)
        #TODO: Pack this in a scrollbar - this didn't work very nice.
        #scroll_bg_edit = gtk.ScrolledWindow()
        #scroll_bg_edit.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        #scroll_bg_edit.add_with_viewport(bg_right)
        #bg_right.pack_start(bg_right_top)
        bg_right.pack_start(self._bg_edit_table, True, True, gui.WIDGET_SPACING)
        bg_right.pack_start(self._get_position(), False, False, gui.WIDGET_SPACING)

        bgbox = gtk.HBox()
        bgbox.pack_start(bg_left, False, True, 0)
        bgbox.pack_start(gtk.VSeparator(), False, False, 15)
        bgbox.pack_start(bg_right, True, True, 0)
        notebook.append_page(bgbox, gtk.Label(_("Background")))
        

        ########### Notebook Page 2: Body Text #################################
        self.body_widgets = {}
        body_h = gtk.HBox()
        body_h.pack_start(self._get_section_left(self._on_body_changed, self.body_widgets))
        body_h.pack_start(gtk.VSeparator())
        body_h.pack_start(self._get_section_right(self._on_body_changed, self.body_widgets))
        notebook.append_page(body_h, gtk.Label(_("Body Text")))
       
        ############ Notebook Page 3: Footer Text ##############################
        self.footer_widgets = {}
        footer_h = gtk.HBox()
        footer_h.pack_start(self._get_section_left(self._on_footer_changed, self.footer_widgets))
        footer_h.pack_start(gtk.VSeparator())
        footer_h.pack_start(self._get_section_right(self._on_footer_changed, self.footer_widgets))
        notebook.append_page(footer_h, gtk.Label(_("Footer Text")))
        
        main_h.pack_start(main_v)
        
        ############  Preview  ########################
        table_right = gui.ESTable(3, auto_inc_y=True)
        table_right.attach_section_title(_("Preview"))
        self._preview = gtk.DrawingArea()
        self._preview.set_size_request(300, int(300*0.75))
        self._preview.connect('expose-event', self._expose)
        table_right.attach_widget(self._preview)

        main_h.pack_end(table_right)
        self.add(main_h)
        self.show_all()
    
    def draw(self, *args):
        self._preview.queue_draw()
    
    def _expose(self, widget, event):
        ccontext = widget.window.cairo_create()
        bounds = widget.get_size_request()
        #ccontext.scale(float(400)/bounds[0],
        #                float(300)/bounds[1])
        self._example_slide = _ExampleSlide()
        self.theme.render(ccontext, bounds, self._example_slide)
        return True
    
    def _get_section_left(self, cb, widgets={}):
        "Returns a table with the left part of the section edit controls"
        table = gui.ESTable(8, row_spacing=10, auto_inc_y=True)
        widgets['font_title'] = table.attach_section_title(_("Font"))
        widgets['font_button'] = table.attach_widget(gtk.FontButton(), label=_("Type and Size"))
        widgets['font_button'].connect('font-set', cb)
        widgets['font_comment'] = table.attach_comment(_("Note that the font size might be scaled down if it doesn't fit."))
        widgets['font_color'] = table.attach_widget(gtk.ColorButton(gtk.gdk.Color(0,0,0)), label=_("Color"))
        widgets['font_color'].connect('color-set', cb)
        widgets['alignment_title'] = table.attach_section_title(_("Alignment"))
        widgets['alignment_horizontal'] = table.attach_combo((_("Center"), _("Left"), _("Right")), _("Center"), label=_("Text Alignment"))
        widgets['alignment_horizontal'].connect('changed', cb)
        ## Order for vertical align must be the same as theme.TOP, theme.MIDDLE, theme.BOTTOM
        widgets['alignment_vertical'] = table.attach_combo((_("Top"), _("Middle"), _("Bottom")), _("Middle"), label=_("Vertical Text Alignment"))
        widgets['alignment_vertical'].connect('changed', cb)
        widgets['line_spacing'] = table.attach_spinner(gtk.Adjustment(1.0, 1.0, 3.0, 0.1, 1, 0), 0.0, 1, label=_("Line Spacing"))
        widgets['line_spacing'].connect('value-changed', cb)
        return table
    
    def _get_section_right(self, cb, widgets={}):
        "Returns a table with the right part of the section edit controls"
        table = gui.ESTable(8, 1, row_spacing=10, auto_inc_y=True)
        widgets['shadow_title'] = table.attach_section_title(_("Text Shadow"))
        widgets['shadow_color'] = table.attach_widget(gtk.ColorButton(gtk.gdk.Color(0,0,0)), label=_("Color"))
        widgets['shadow_color'].set_use_alpha(True)
        widgets['shadow_color'].connect('color-set', cb)
        widgets['shadow_x_offset'] = table.attach_spinner(gtk.Adjustment(0.5, -1.0, 1.0, 0.1, 0.5, 0), 0.0, 1, label=_("x-Offset"))
        widgets['shadow_x_offset'].connect('value-changed', cb)
        widgets['shadow_y_offset'] = table.attach_spinner(gtk.Adjustment(0.5, -1.0, 1.0, 0.1, 0.5, 0), 0.0, 1, label=_("y-Offset"))
        widgets['shadow_y_offset'].connect('value-changed', cb)
        widgets['shadow_comment'] = table.attach_comment(_("Shadow offsets are measured \
in percentage of font height. So an offset of 0.5 for point 12 font is 6 points."))
        widgets['outline_title'] = table.attach_section_title(_("Text Outline"))
        widgets['outline_size'] = table.attach_spinner(gtk.Adjustment(1.0, 0.0, 3.0, 1.0, 1.0, 0), label=_("Size (Pixel)"))
        widgets['outline_size'].connect('value-changed', cb)
        widgets['outline_color'] = table.attach_widget(gtk.ColorButton(gtk.gdk.Color(0,0,0)), label=_("Color"))
        widgets['outline_color'].connect('color-set', cb)
        return table
    
    def _on_body_changed(self, *args):
        self._set_changed()
        body = self.theme.get_body()
        body.font = self.body_widgets['font_button'].get_font_name()
        body.color = self.body_widgets['font_color'].get_color().to_string()
        a = self.body_widgets['alignment_horizontal'].get_active_text()
        body.align = theme.get_align_const(a)
        
        a = self.body_widgets['alignment_vertical'].get_active_text()
        body.valign = theme.get_valign_const(a)
        
        body.spacing = self.body_widgets['line_spacing'].get_value()
        body.shadow_color = self.body_widgets['shadow_color'].get_color().to_string()
        body.shadow_opacity = self.body_widgets['shadow_color'].get_alpha()/65535.0
        body.shadow_offset[0] = self.body_widgets['shadow_x_offset'].get_value()
        body.shadow_offset[1] = self.body_widgets['shadow_y_offset'].get_value()
        body.outline_size = self.body_widgets['outline_size'].get_value()
        body.outline_color = self.body_widgets['outline_color'].get_color().to_string()
        
        self.draw()
    
    def _on_footer_changed(self, *args):
        self._set_changed()
        footer = self.theme.get_footer()
        footer.font = self.footer_widgets['font_button'].get_font_name()
        footer.color = self.footer_widgets['font_color'].get_color().to_string()
        a = self.footer_widgets['alignment_horizontal'].get_active()
        footer.align = theme.get_align_const(a)
        
        a = self.footer_widgets['alignment_vertical'].get_active()
        footer.valign = theme.get_valign_const(a)
        
        footer.spacing = self.footer_widgets['line_spacing'].get_value()
        footer.shadow_color = self.footer_widgets['shadow_color'].get_color().to_string()
        footer.shadow_offset[0] = self.footer_widgets['shadow_x_offset'].get_value()
        footer.shadow_offset[1] = self.footer_widgets['shadow_y_offset'].get_value()
        footer.outline_size = self.footer_widgets['outline_size'].get_value()
        footer.outline_color = self.footer_widgets['outline_color'].get_color().to_string()
        
        self.draw()
    
    #######################
    #    Backgrounds      #
    #######################
    def _activate_bg(self, itr):
        selection = self._treeview_bgs.get_selection()
        selection.select_iter(itr)
        self._treeview_bgs.scroll_to_cell(self._bg_model.get_path(itr))
    
    def _on_bg_image_new(self, widget=None):
        fchooser = gtk.FileChooserDialog( _("Add Images"), self,
                gtk.FILE_CHOOSER_ACTION_OPEN,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                gtk.STOCK_ADD, gtk.RESPONSE_ACCEPT) )
        fchooser.set_current_folder(os.path.expanduser("~"))
        filt = gtk.FileFilter()
        filt.set_name( _("Image Types") )
        filt.add_pixbuf_formats()
        fchooser.add_filter(filt)
        if fchooser.run() == gtk.RESPONSE_ACCEPT:
            fchooser.hide()
            img = fchooser.get_filename()
            newpath = os.path.join(DATA_PATH, 'theme', 'res', os.path.basename(img))
            if newpath != img:
                shutil.copy(img, newpath)
            itr = self._bg_model.append((theme.ImageBackground(src=os.path.basename(img)),))
            self._activate_bg(itr)
        fchooser.destroy()
        self.draw()

    def _on_bg_image(self, widget=None):
        table = self._bg_edit_table
        table.foreach(lambda w: table.remove(w))
        table.y = 0
        table.attach_section_title(_("Image Background"))
        self._bg_image_filech = table.attach_filechooser(label=_("Image"))
        self._bg_image_radio_mode_fit = gtk.RadioButton(None, _("Fit"))
        self._bg_image_radio_mode_fit.connect('toggled', self._on_bg_image_changed)
        self._bg_image_radio_mode_fill = gtk.RadioButton(self._bg_image_radio_mode_fit, _("Fill"))
        h = gtk.HBox()
        h.pack_start(self._bg_image_radio_mode_fill)
        h.pack_start(self._bg_image_radio_mode_fit)
        table.attach_widget(h, label=_("Mode"))
        table.show_all()
        self._load_bg_image()
        
    def _load_bg_image(self):
        bg = self._get_active_bg()
        self._bg_image_filech.set_filename(
                os.path.join(DATA_PATH, 'theme', 'res', bg.src))
        if bg.aspect == theme.ASPECT_FILL:
            self._bg_image_radio_mode_fill.set_active(True)
        else:
            self._bg_image_radio_mode_fit.set_active(True)
        self.draw()
    
    def _on_bg_image_changed(self, widget):
        self._set_changed()
        bg = self._get_active_bg()
        if self._bg_image_radio_mode_fill.get_active():
            bg.aspect = theme.ASPECT_FILL
        else:
            bg.aspect = theme.ASPECT_FIT
        self.draw()
    
    def _on_bg_solid_new(self, widget=None):
        itr = self._bg_model.append((theme.ColorBackground(),))
        self._activate_bg(itr)
    
    def _on_bg_solid(self, widget=None):
        table = self._bg_edit_table
        table.y = 0
        table.foreach(lambda w: table.remove(w))
        
        table.attach_section_title(_("Color Background"))
        self._bg_solid_color_button = table.attach_widget(gtk.ColorButton(), label=_("Color"))
        self._bg_solid_color_button.set_use_alpha(True)
        self._bg_solid_color_button.connect('color-set', self._on_bg_solid_changed)
        table.show_all()
        self._load_bg_solid()
    
    def _on_bg_solid_changed(self, *args):
        self._set_changed()
        self._get_active_bg().color = self._bg_solid_color_button.get_color().to_string()
        self._get_active_bg().alpha = self._bg_solid_color_button.get_alpha()/65535.0
        self.draw()
    
    def _load_bg_solid(self):
        bg = self._get_active_bg()
        self._bg_solid_color_button.set_color(gtk.gdk.color_parse(bg.color))
        self._bg_solid_color_button.set_alpha(int(bg.alpha*65535))
    
    def _on_bg_gradient_new(self, widget=None):
        itr = self._bg_model.append((theme.GradientBackground(),))
        self._activate_bg(itr)
    
    def _on_bg_gradient(self, widget=None):
        table = self._bg_edit_table
        table.y = 0
        table.foreach(lambda w: table.remove(w))
        bg = self._get_active_bg()
        
        table.attach_section_title(_("Gradient Background"))
        self._bg_gradient_colors = []
        self._bg_gradient_lengths = []
        loc = 0.1
        if len(bg.stops) == 0:
            for i in range(2):
                self._bg_gradient_add_stop(update=False)
        for i in range(len(bg.stops)):
            self._bg_gradient_colors.append(table.attach_widget(gtk.ColorButton(), label=_("Color %d"%i)))
            self._bg_gradient_colors[i].set_use_alpha(True)
            self._bg_gradient_colors[i].connect('color-set', self._on_bg_gradient_changed)
            self._bg_gradient_lengths.append(table.attach_widget(gtk.HScale(gtk.Adjustment(50,0,100,1,10,0)), label=_("Length")))
            self._bg_gradient_lengths[i].set_digits(0)
            self._bg_gradient_lengths[i].connect('change-value', self._on_bg_gradient_changed)
            table.attach_hseparator()
        add = table.attach_widget(gtk.Button(_("Add Stop"), gtk.STOCK_ADD))
        add.connect('clicked', self._bg_gradient_add_stop)
        
        # TODO Move HScale as helper function to ESTable
        self._bg_gradient_angle = table.attach_widget(gtk.HScale(gtk.Adjustment(0,0,360,1,10,0)), label=_("Angle"))
        self._bg_gradient_angle.set_digits(0)
        self._bg_gradient_angle.connect('change-value', self._on_bg_gradient_changed)
        table.show_all()
        self._load_bg_gradient()
    
    def _bg_gradient_add_stop(self, widget=None, update=True, *args):
        bg = self._get_active_bg()
        if len(bg.stops)>0:
            loc = bg.stops[len(bg.stops)-1].location
        else:
            loc = 0.1
            col = '#fff'
        col = gtk.gdk.Color(random.randint(0,65535),random.randint(0,65535),
                            random.randint(0,65535)).to_string()
        if loc > 0.9:
            loc -= random.uniform(0.1, 0.8)
        elif loc < 0.9 and loc>0.5:
            loc -= random.uniform(0.1, 0.5)
        else:
            loc += random.uniform(0.1, 0.5)
        bg.stops.append(theme.GradientStop(location=loc, color=col))
        if update:
            if type(bg) == theme.GradientBackground:
                self._on_bg_gradient()
            elif type(bg) == theme.RadialGradientBackground:
                self._on_bg_radial()
    
    def _on_bg_gradient_changed(self, *args):
        self._set_changed()
        bg = self._get_active_bg()
        for i in range(len(bg.stops)):
            bg.stops[i].color = self._bg_gradient_colors[i].get_color().to_string()
            bg.stops[i].alpha = self._bg_gradient_colors[i].get_alpha()/65535.0
            bg.stops[i].location = self._bg_gradient_lengths[i].get_value()/100.0
        bg.angle = self._bg_gradient_angle.get_value()
        self.draw()
    
    def _load_bg_gradient(self, widget=None):
        bg = self._get_active_bg()
        for i in range(len(bg.stops)):
            self._bg_gradient_colors[i].set_color(gtk.gdk.color_parse(bg.stops[i].color))
            self._bg_gradient_colors[i].set_alpha(int(bg.stops[i].alpha*65535))
        for i in range(len(bg.stops)):
            self._bg_gradient_lengths[i].set_value(bg.stops[i].location*100)
        self._bg_gradient_angle.set_value(bg.angle)
        self.draw()
    
    def _on_bg_radial_new(self, widget=None):
        itr = self._bg_model.append((theme.RadialGradientBackground(),))
        self._activate_bg(itr)
    
    def _on_bg_radial(self, widget=None):
        table = self._bg_edit_table
        table.y = 0
        table.foreach(lambda w: table.remove(w))
        bg = self._get_active_bg()
        
        table.attach_section_title(_("Radial Background"))
        self._bg_radial_colors = []
        self._bg_radial_lengths = []
        loc = 0.1
        if len(bg.stops) == 0:
            for i in range(2):
                self._bg_gradient_add_stop(update=False)
        for i in range(len(bg.stops)):
            self._bg_radial_colors.append(table.attach_widget(gtk.ColorButton(), label=_("Color %d"%i)))
            self._bg_radial_colors[i].set_use_alpha(True)
            self._bg_radial_colors[i].connect('color-set', self._on_bg_radial_changed)
            self._bg_radial_lengths.append(table.attach_widget(gtk.HScale(gtk.Adjustment(50,0,100,1,10,0)), label=_("Length")))
            self._bg_radial_lengths[i].set_digits(0)
            self._bg_radial_lengths[i].connect('change-value', self._on_bg_radial_changed)
            table.attach_hseparator()
        add = table.attach_widget(gtk.Button(_("Add Stop"), gtk.STOCK_ADD), "")
        add.connect('clicked', self._bg_gradient_add_stop)
        
        self._bg_radial_length = table.attach_widget(gtk.HScale(gtk.Adjustment(1,1,100,1,10,0)), label=_("Overall Length"))
        self._bg_radial_length.set_digits(0)
        self._bg_radial_length.connect('change-value', self._on_bg_radial_changed)
        self._bg_radial_pos_h = table.attach_widget(gtk.HScale(gtk.Adjustment(0,0,100,1,10,0)), label=_("Horizontal Position"))
        self._bg_radial_pos_h.set_digits(0)
        self._bg_radial_pos_h.connect('change-value', self._on_bg_radial_changed)
        self._bg_radial_pos_v = table.attach_widget(gtk.HScale(gtk.Adjustment(0,0,100,1,10,0)), label=_("Vertical Position"))
        self._bg_radial_pos_v.set_digits(0)
        self._bg_radial_pos_v.connect('change-value', self._on_bg_radial_changed)
        
        table.show_all()
        self._load_bg_radial()
    
    def _on_bg_radial_changed(self, *args):
        self._set_changed()
        bg = self._get_active_bg()
        for i in range(len(bg.stops)):
            bg.stops[i].color = self._bg_radial_colors[i].get_color().to_string()
            bg.stops[i].alpha = self._bg_radial_colors[i].get_alpha()/65535.0
            bg.stops[i].location = self._bg_radial_lengths[i].get_value()/100.0
        bg.length = self._bg_radial_length.get_value()/100.0
        bg.cpos[0] = self._bg_radial_pos_h.get_value()/100.0
        bg.cpos[1] = self._bg_radial_pos_v.get_value()/100.0
        self.draw()
    
    def _load_bg_radial(self):
        bg = self._get_active_bg()
        for i in range(len(bg.stops)):
            self._bg_radial_colors[i].set_color(gtk.gdk.color_parse(bg.stops[i].color))
            self._bg_radial_colors[i].set_alpha(int(bg.stops[i].alpha*65535))
        for i in range(len(bg.stops)):
            self._bg_radial_lengths[i].set_value(bg.stops[i].location*100)
        self._bg_radial_length.set_value(bg.length*100)
        self._bg_radial_pos_h.set_value(bg.cpos[0]*100)
        self._bg_radial_pos_v.set_value(bg.cpos[1]*100)
        self.draw()
    
    def _load_bg_position(self):
        bg = self._get_active_bg()
        self.__updating = True
        self._p['lf'].set_value(bg.pos[0])
        self._p['tp'].set_value(bg.pos[1])
        self._p['rt'].set_value(bg.pos[2])
        self._p['bt'].set_value(bg.pos[3])
        self.__updating = False
    
    def _get_active_bg(self):
        (model, iter) = self._treeview_bgs.get_selection().get_selected()
        if iter:
            return model.get_value(iter, 0)
        return None
    
    def _on_bgs_reordered(self, model, path, iter=None, new_order=None):
        #TODO: This doesnt't work. Need to get the order from the treeview.
        self._update_bg_list_from_model()
        self.draw()
    
    def _update_bg_list_from_model(self):
        #self._bg_model.reorder()
        self.theme.backgrounds = []
        for bg in self._bg_model:
            self.theme.backgrounds.append(bg[0])
    
    def _on_bg_changed(self, widget):
        bg = self._get_active_bg()
        if not bg:
            return
        if isinstance(bg, theme.ImageBackground):
            self._on_bg_image()
        elif isinstance(bg, theme.ColorBackground):
            self._on_bg_solid()
        elif isinstance(bg, theme.GradientBackground):
            self._on_bg_gradient()
        elif isinstance(bg, theme.RadialGradientBackground):
            self._on_bg_radial()
        self._load_bg_position()
    
    def _on_delete_bg(self, *args):
        (model, itr) = self._treeview_bgs.get_selection().get_selected()
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
    
    ###########################
    #    Position Expander    #
    ###########################
    def _get_position(self):
        "Return the element positioning settings."
        position = gtk.Expander(_("Element Position"))
        # Positional elements for backgrounds
        table = gui.ESTable(5,2)
        self._p = {}
        
        adjust = gtk.Adjustment(0, 0.0, 1.0, 0.01, 0.10)
        self._p['lf'] = table.attach_spinner(adjust, 0.02, 2, label=_('Left:'))
        self._p['lf'].set_numeric(True)
        self._p['lf'].connect('changed', self._on_change_pos)
        
        adjust = gtk.Adjustment(0, 0.0, 1.0, 0.01, 0.10)
        self._p['rt'] = table.attach_spinner(adjust, 0.02, 2, label=_('Right:'), x=1)
        self._p['rt'].set_numeric(True)
        self._p['rt'].connect('changed', self._on_change_pos)
        
        adjust = gtk.Adjustment(0, 0.0, 1.0, 0.01, 0.10)
        self._p['tp'] = table.attach_spinner(adjust, 0.02, 2, label=_('Top:'), y=1)
        self._p['tp'].set_numeric(True)
        self._p['tp'].connect('changed', self._on_change_pos)
        
        adjust = gtk.Adjustment(0, 0.0, 1.0, 0.01, 0.10)
        self._p['bt'] = table.attach_spinner(adjust, 0.02, 2, label=_('Bottom:'), x=1, y=1)
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
        self.draw()
    
    def _set_changed(self):
        self.changed = True
        if not self.get_title().startswith("*"):
            self.set_title("*%s"%self.get_title())
    
    def _load_theme(self, filenm=None):
        'Loads a theme into the Theme Editor'
        self.theme = theme.Theme(filenm)
        self._title_entry.set_text(self.theme.get_title())
        
        ########################## Backgrounds ################################
        for bg in self.theme.backgrounds:
            self._bg_model.append((bg,))
        
       
        ####################### Sections: Body ################################
        body = self.theme.get_body()
        self.body_widgets['font_button'].set_font_name(body.font)
        self.body_widgets['font_color'].set_color(gtk.gdk.Color(body.color))
        if body.align == theme.CENTER:
            self.body_widgets['alignment_horizontal'].set_active(0)
        elif body.align == theme.LEFT:
            self.body_widgets['alignment_horizontal'].set_active(1)
        elif body.align == theme.RIGHT:
            self.body_widgets['alignment_horizontal'].set_active(2)
        
        if body.valign == theme.MIDDLE:
            self.body_widgets['alignment_vertical'].set_active(0)
        elif body.valign == theme.TOP:
            self.body_widgets['alignment_vertical'].set_active(1)
        elif body.valign == theme.BOTTOM:
            self.body_widgets['alignment_vertical'].set_active(2)
        
        self.body_widgets['line_spacing'].set_value(body.spacing)
        self.body_widgets['shadow_color'].set_color(gtk.gdk.Color(body.shadow_color))
        self.body_widgets['shadow_color'].set_alpha(int(body.shadow_opacity*65535))
        self.body_widgets['shadow_x_offset'].set_value(body.shadow_offset[0])
        self.body_widgets['shadow_y_offset'].set_value(body.shadow_offset[1])
        self.body_widgets['outline_size'].set_value(body.outline_size)
        self.body_widgets['outline_color'].set_color(gtk.gdk.Color(body.outline_color))
        
        ##################### Sections: Footer ################################
        footer = self.theme.get_footer()
        self.footer_widgets['font_button'].set_font_name(footer.font)
        self.footer_widgets['font_color'].set_color(gtk.gdk.Color(footer.color))
        if footer.align == theme.CENTER:
            self.footer_widgets['alignment_horizontal'].set_active(0)
        elif footer.align == theme.LEFT:
            self.footer_widgets['alignment_horizontal'].set_active(1)
        elif footer.align == theme.RIGHT:
            self.footer_widgets['alignment_horizontal'].set_active(2)
        
        if footer.valign == theme.MIDDLE:
            self.footer_widgets['alignment_vertical'].set_active(0)
        elif footer.valign == theme.TOP:
            self.footer_widgets['alignment_vertical'].set_active(1)
        elif footer.valign == theme.BOTTOM:
            self.footer_widgets['alignment_vertical'].set_active(2)
        
        self.footer_widgets['line_spacing'].set_value(footer.spacing)
        self.footer_widgets['shadow_color'].set_color(gtk.gdk.Color(footer.shadow_color))
        self.footer_widgets['shadow_color'].set_alpha(int(body.shadow_opacity*65535))
        self.footer_widgets['shadow_x_offset'].set_value(footer.shadow_offset[0])
        self.footer_widgets['shadow_y_offset'].set_value(footer.shadow_offset[1])
        self.footer_widgets['outline_size'].set_value(footer.outline_size)
        self.footer_widgets['outline_color'].set_color(gtk.gdk.Color(footer.outline_color))
        
    def _destroy(self, widget):
        #self.theme.save()
        global __name__
        self.hide()
        self.destroy()
        if __name__ == "__main__":
            gtk.main_quit()


class _ExampleSlide(object):
    """
    A slide to draw as an example for the theme selection widget.
    """
    def __init__(self):
        object.__init__(self)
        self.body = [
                theme.Text('\n'.join([
                        'Amazing grace, how sweet the sound, ',
                        'That saved a wretch like me! ',
                        'I once was lost, but now I am found, ',
                        'Was blind, but now I see.']),
                    pos=[0.0, 0.0, 1.0, 1.0], margin=10),
                ]
        self.foot = [theme.Text('\n'.join([
                        '"Amazing Grace"',
                        'Text: John Newton',
                        'Copyright &#169;: Public Domain'
        ]))]
    
    def get_body(self):
        return self.body
    
    def get_footer(self):
        return self.foot
    
    def get_slide(self):
        return NotImplemented

if __name__ == "__main__":
    ThemeEditor()
    gtk.main()
