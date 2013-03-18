#
# vim: ts=4 sw=4 expandtab ai:
#
# Copyright (C) 2008-2011 Exposong.org
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

from gi.repository import Gtk
import sys
import os
import shutil
import random
from gi.repository import GObject

import exposong.theme
import exposong.exampleslide
from exposong import gui
from exposong import DATA_PATH
from exposong.config import config
from exposong.glob import title_to_filename, find_freefile, check_filename

BACKGROUND_TYPES = [_("Image"),  _("Color"), _("Gradient"), _("Radial Gradient")]

class ThemeEditor(Gtk.Window):
    """
    Provides a simple interface for creating and editing themes
    """
    def __init__(self, parent, theme_):
        super(self)
        self.connect("delete_event", self._close)
        self.set_transient_for(parent)
        self.set_title(_("ExpoSong Theme Editor"))
        
        # True when all widgets are filled with values from theme.
        self.__ready = False
        # Used when updating position spinners
        self.__updating = False
        self._do_layout()
        self._load_theme(theme_)
        self.show_all()
    
    def _do_layout(self):
        'Builds the GUI'
        main_h = Gtk.HBox()
        main_v = Gtk.VBox()
        
        # Title entry
        title_table = gui.ESTable(1)
        self._title_entry = title_table.attach_entry(_("New Theme"),
                                                     label=_("Theme Name"))
        main_v.pack_start(title_table, False, False)
        
        self._notebook = Gtk.Notebook()
        self._notebook.connect('switch-page', self._nb_page_changed)
        main_v.pack_start(self._notebook, True, True, 5)
        
        ######################
        # Page 1: Background #
        ######################
        self._treeview_bgs = Gtk.TreeView()
        self._treeview_bgs.set_reorderable(True)
        
        Gtk.stock_add([('add-background-gradient',_('Add Gradient'), Gdk.ModifierType.MOD1_MASK, 0,
                'pymserv'),
                ('add-background-solid',_('Add Solid Color'), Gdk.ModifierType.MOD1_MASK, 0,
                'pymserv'),
                ('add-background-radial',_('Add Radial Gradient'), Gdk.ModifierType.MOD1_MASK, 0,
                'pymserv'),
               ("add-background-image",_('Add Image'), Gdk.ModifierType.MOD1_MASK, 0,
                'pymserv')])
        
        #Background Toolbar
        toolbar = Gtk.Toolbar()
        btn = Gtk.ToolButton(Gtk.stock_lookup('add-background-image')[0])
        btn.set_tooltip_markup(_("Add a new Image Background"))
        btn.connect('clicked', self._on_bg_image_new)
        toolbar.insert(btn, -1)
        btn = Gtk.ToolButton(Gtk.stock_lookup('add-background-solid')[0])
        btn.set_tooltip_markup(_("Add a new Solid Color Background"))
        btn.connect('clicked', self._on_bg_solid_new)
        toolbar.insert(btn, -1)
        btn = Gtk.ToolButton(Gtk.stock_lookup('add-background-gradient')[0])
        btn.set_tooltip_markup(_("Add a new Gradient Background"))
        btn.connect('clicked', self._on_bg_gradient_new)
        toolbar.insert(btn, -1)
        btn = Gtk.ToolButton(Gtk.stock_lookup('add-background-radial')[0])
        btn.set_tooltip_markup(_("Add a new Radial Gradient Background"))
        btn.connect('clicked', self._on_bg_radial_new)
        toolbar.insert(btn, -1)
        button = Gtk.ToolButton(Gtk.STOCK_DELETE)
        button.connect('clicked', self._on_delete_bg)
        toolbar.insert(button, -1)
        
        # Background Treeview Columns
        self._bg_model = Gtk.ListStore(GObject.TYPE_PYOBJECT)
        self._column_bgs = Gtk.TreeViewColumn(_("Backgrounds"))
        textrend = Gtk.CellRendererText()
        self._column_bgs.pack_start(textrend, True, True, 0)
        self._column_bgs.set_cell_data_func(textrend, self._bg_get_row_text)
        colorrend = Gtk.CellRendererText()
        self._column_bgs.pack_start(colorrend, True, True, 0)
        self._column_bgs.set_cell_data_func(colorrend, self._bg_get_row_color)
        self._treeview_bgs.append_column(self._column_bgs)
        self._treeview_bgs.set_size_request(90,200)
        self._treeview_bgs.set_model(self._bg_model)
        self._bg_model.connect("rows-reordered", self._on_bgs_reordered)
        self._bg_model.connect("row-changed", self._on_bgs_reordered)
        self._treeview_bgs.get_selection().connect("changed", self._on_bg_changed)
        
        bg_left = Gtk.VBox()
        gui.append_comment(bg_left, _("Backgrounds will be drawn starting with \
the first element in this list moving to the last one."), 0)
        bg_left.pack_start(toolbar, False, True, gui.WIDGET_SPACING)
        scroll = Gtk.ScrolledWindow()
        scroll.add(self._treeview_bgs)
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        bg_left.pack_start(scroll, True, True, gui.WIDGET_SPACING)
        
        self._bg_edit_table = gui.ESTable(15, row_spacing=10, auto_inc_y=True)
        scroll_bg_edit = Gtk.ScrolledWindow()
        scroll_bg_edit.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll_bg_edit.add_with_viewport(self._bg_edit_table)

        bgbox = Gtk.HBox()
        bgbox.pack_start(bg_left, False, True, 0)
        bgbox.pack_start(Gtk.VSeparator(), False, False, 15)
        bgbox.pack_start(scroll_bg_edit, True, True, 0)
        self._notebook.append_page(bgbox, Gtk.Label(label=_("Background")))
        

        ########### Notebook Page 2: Body Text #################################
        self.body_widgets = {}
        body_h = Gtk.HBox()
        body_h.pack_start(self._get_section_left(self._on_body_changed,
                                                 self.body_widgets))
        body_h.pack_start(Gtk.VSeparator())
        body_h.pack_start(self._get_section_right(self._on_body_changed,
                                                  self.body_widgets))
        self._notebook.append_page(body_h, Gtk.Label(label=_("Body Text")))
       
        ############ Notebook Page 3: Footer Text ##############################
        self.footer_widgets = {}
        footer_h = Gtk.HBox()
        footer_h.pack_start(self._get_section_left(self._on_footer_changed,
                                                   self.footer_widgets))
        footer_h.pack_start(Gtk.VSeparator())
        footer_h.pack_start(self._get_section_right(self._on_footer_changed,
                                                    self.footer_widgets))
        self._notebook.append_page(footer_h, Gtk.Label(label=_("Footer Text")))
        
        table_meta = gui.ESTable(4, auto_inc_y=True)
        #Key names for meta must comply with the keys in the <meta> tag in the theme file
        self._meta = {}
        self._meta['author'] = table_meta.attach_entry("", label=_("Author"))
        self._meta['themeurl'] = table_meta.attach_entry("", label=_("Theme URL"))
        self._meta['copyright'] = table_meta.attach_entry("", label=_("Copyright"))
        self._meta['description'] = table_meta.attach_entry("", label=_("Description"))
        self._meta['tags'] = table_meta.attach_entry("", label=_("Tags"))
        table_meta.attach_comment(_("Separate tags with commas"))
        self._notebook.append_page(table_meta, Gtk.Label(label=_("Metadata")))
        
        main_h.pack_start(main_v, True, True, 0)
        
        ############  Preview  ########################
        table_right = gui.ESTable(3, auto_inc_y=True)
        table_right.attach_section_title(_("Preview"))
        self._preview = Gtk.DrawingArea()
        self._preview.set_size_request(300, int(300*0.75))
        self._preview.connect('expose-event', self._expose)
        table_right.attach_widget(self._preview)
        self._pos_expander = table_right.attach_widget(self._get_position())
        self._pos_expander.set_sensitive(False)
        h = Gtk.HBox()
        btn_revert = Gtk.Button("", Gtk.STOCK_REVERT_TO_SAVED)
        btn_revert.connect('clicked', self._revert_changes)
        btn_save = Gtk.Button("", Gtk.STOCK_SAVE)
        btn_save.connect('clicked', self._save_changes)
        h.pack_start(btn_revert, True, True, 0)
        h.pack_start(btn_save, True, True, 0)
        table_right.attach_hseparator()
        table_right.attach_widget(h)

        main_h.pack_end(table_right, True, True, 0)
        self.add(main_h)
        self.show_all()
        self._set_changed(False)
    
    def draw(self, *args):
        'Called to update the preview widget'
        self._preview.queue_draw()
    
    def _expose(self, widget, event):
        'Renders the preview widget the first time'
        ccontext = widget.get_window().cairo_create()
        bounds = widget.get_size_request()
        #ccontext.scale(float(400)/bounds[0],
        #                float(300)/bounds[1])
        self._example_slide = exposong.exampleslide._ExampleTextSlide()
        self.theme.render(ccontext, bounds, self._example_slide)
        return True
    
    def _get_section_left(self, cb, widgets={}):
        "Returns a table with the left part of the section edit controls"
        table = gui.ESTable(8, row_spacing=10, auto_inc_y=True)
        widgets['font_title'] = table.attach_section_title(_("Font"))
        widgets['font_button'] = table.attach_widget(Gtk.FontButton(),
                                                     label=_("Type and Size"))
        widgets['font_button'].connect('font-set', cb)
        widgets['font_comment'] = table.attach_comment(
            _("Note that the font size might be scaled down if it doesn't fit."))
        widgets['font_color'] = table.attach_widget(Gtk.ColorButton(
                Gdk.Color(0,0,0)), label=_("Color"))
        widgets['font_color'].connect('color-set', cb)
        widgets['alignment_title'] = table.attach_section_title(_("Alignment"))
        widgets['alignment_horizontal'] = table.attach_combo((_("Left"),
                _("Center"), _("Right")), _("Center"), label=_("Text Alignment"))
        widgets['alignment_horizontal'].connect('changed', cb)
        ## Order for vertical align must be theme.TOP, theme.MIDDLE, theme.BOTTOM
        widgets['alignment_vertical'] = table.attach_combo((_("Top"), _("Middle"),
                _("Bottom")), _("Middle"), label=_("Vertical Text Alignment"))
        widgets['alignment_vertical'].connect('changed', cb)
        widgets['line_spacing'] = table.attach_spinner(
            Gtk.Adjustment(1.0, 1.0, 3.0, 0.1, 1, 0), 0.0, 1, label=_("Line Spacing"))
        widgets['line_spacing'].connect('value-changed', cb)
        return table
    
    def _get_section_right(self, cb, widgets={}):
        "Returns a table with the right part of the section edit controls"
        table = gui.ESTable(8, 1, row_spacing=10, auto_inc_y=True)
        widgets['shadow_title'] = table.attach_section_title(_("Text Shadow"))
        widgets['shadow_apply'] = table.attach_checkbutton(_("Apply Shadow"))
        widgets['shadow_apply'].connect('toggled', cb)
        widgets['shadow_color'] = table.attach_widget(
                Gtk.ColorButton(Gdk.Color(0,0,0)), label=_("Color"))
        widgets['shadow_color'].set_use_alpha(True)
        widgets['shadow_color'].connect('color-set', cb)
        widgets['shadow_x_offset'] = table.attach_spinner(
                Gtk.Adjustment(0.5, -1.0, 1.0, 0.1, 0.5, 0), 0.0, 1, label=_("x-Offset"))
        widgets['shadow_x_offset'].connect('value-changed', cb)
        widgets['shadow_y_offset'] = table.attach_spinner(
                Gtk.Adjustment(0.5, -1.0, 1.0, 0.1, 0.5, 0), 0.0, 1, label=_("y-Offset"))
        widgets['shadow_y_offset'].connect('value-changed', cb)
        widgets['shadow_comment'] = table.attach_comment(_("Shadow offsets are measured \
in percentage of font height. So an offset of 0.5 for point 12 font is 6 points."))
        widgets['outline_title'] = table.attach_section_title(_("Text Outline"))
        widgets['outline_size'] = table.attach_spinner(
                Gtk.Adjustment(0.0, 0.0, 3.0, 1.0, 1.0, 0), label=_("Size (Pixel)"))
        widgets['outline_size'].connect('value-changed', cb)
        widgets['outline_color'] = table.attach_widget(
                Gtk.ColorButton(Gdk.Color(0,0,0)), label=_("Color"))
        widgets['outline_color'].connect('color-set', cb)
        return table
    
    def _on_body_changed(self, *args):
        """
        Called when any part of the body section was changed to update
        the theme and the preview
        """
        if not self.__ready: #Only allow when everything is loaded from theme.
            return
        
        self._set_changed()
        body = self.theme.get_body()
        
        body.font = self.body_widgets['font_button'].get_font_name()
        body.color = self.body_widgets['font_color'].get_color().to_string()
        a = self.body_widgets['alignment_horizontal'].get_active_text()
        body.align = exposong.theme.get_align_const(a)
        a = self.body_widgets['alignment_vertical'].get_active_text()
        body.valign = exposong.theme.get_valign_const(a)
        
        body.spacing = self.body_widgets['line_spacing'].get_value()
        if self.body_widgets['shadow_apply'].get_active():
            body.shadow_color = self.body_widgets['shadow_color'].get_color().to_string()
            body.shadow_opacity = round(self.body_widgets['shadow_color'].get_alpha()/65535.0, 1)
            body.shadow_offset[0] = round(self.body_widgets['shadow_x_offset'].get_value(), 1)
            body.shadow_offset[1] = round(self.body_widgets['shadow_y_offset'].get_value(), 1)
            self._on_shadow_widgets_set_sensitive(self.body_widgets, True)
        else:
            body.shadow_color = None
            self._on_shadow_widgets_set_sensitive(self.body_widgets, False)
        body.outline_size = self.body_widgets['outline_size'].get_value()
        body.outline_color = self.body_widgets['outline_color'].get_color().to_string()
        
        self.draw()
    
    def _on_footer_changed(self, *args):
        """
        Called when any part of the footer section was changed to update
        the theme and the preview
        """
        if not self.__ready: #Only allow when everything is loaded from theme
            return
        
        self._set_changed()
        footer = self.theme.get_footer()
        
        footer.font = self.footer_widgets['font_button'].get_font_name()
        footer.color = self.footer_widgets['font_color'].get_color().to_string()
        a = self.footer_widgets['alignment_horizontal'].get_active()
        footer.align = exposong.theme.get_align_const(a)
        a = self.footer_widgets['alignment_vertical'].get_active()
        footer.valign = exposong.theme.get_valign_const(a)
        
        footer.spacing = self.footer_widgets['line_spacing'].get_value()
        if self.footer_widgets['shadow_apply'].get_active():
            footer.shadow_color = self.footer_widgets['shadow_color'].get_color().to_string()
            footer.shadow_opacity = round(self.footer_widgets['shadow_color'].get_alpha()/65535.0, 1)
            footer.shadow_offset[0] = round(self.footer_widgets['shadow_x_offset'].get_value(), 1)
            footer.shadow_offset[1] = round(self.footer_widgets['shadow_y_offset'].get_value(), 1)
            self._on_shadow_widgets_set_sensitive(self.footer_widgets, True)
        else:
            footer.shadow_color = None
            self._on_shadow_widgets_set_sensitive(self.footer_widgets, False)
        footer.outline_size = self.footer_widgets['outline_size'].get_value()
        footer.outline_color = self.footer_widgets['outline_color'].\
                get_color().to_string()
        
        self.draw()
    
    def _on_shadow_widgets_set_sensitive(self, widget_list, sensitive=True):
        'Helper method to enable/disable shadow widget after clicking the shadow checkbox'
        widget_list['shadow_color'].set_sensitive(sensitive)
        widget_list['shadow_x_offset'].set_sensitive(sensitive)
        widget_list['shadow_y_offset'].set_sensitive(sensitive)
    
    #######################
    #    Backgrounds      #
    #######################
    def _activate_bg(self, itr):
        'Activates a background item in the list'
        selection = self._treeview_bgs.get_selection()
        selection.select_iter(itr)
        self._treeview_bgs.scroll_to_cell(self._bg_model.get_path(itr))
    
    def _on_bg_image_new(self, widget=None):
        'Add a new background image'
        self._set_changed()
        fchooser = Gtk.FileChooserDialog( _("Add Images"), self,
                Gtk.FileChooserAction.OPEN,
                (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                Gtk.STOCK_ADD, Gtk.ResponseType.ACCEPT) )
        fchooser.set_current_folder(config.get("open-save-dialogs", "themeeditor-add-bg-image"))
        filt = Gtk.FileFilter()
        filt.set_name( _("Image Types") )
        filt.add_pixbuf_formats()
        fchooser.add_filter(filt)
        if fchooser.run() == Gtk.ResponseType.ACCEPT:
            fchooser.hide()
            img = fchooser.get_filename()
            newpath = os.path.join(DATA_PATH, 'theme', 'res', os.path.basename(img))
            if newpath != img:
                shutil.copy(img, newpath)
            itr = self._bg_model.append(
                (exposong.theme.ImageBackground(src=os.path.basename(img)),))
            self._activate_bg(itr)
            config.set("open-save-dialogs", "themeeditor-add-bg-image", os.path.dirname(img))
        fchooser.destroy()
        self.draw()

    def _on_bg_image(self, widget=None):
        'Create the widgets for editing image backgrounds'
        table = self._bg_edit_table
        table.foreach(lambda w: table.remove(w))
        table.y = 0
        table.attach_section_title(_("Image Background"))
        self._bg_image_filech = table.attach_filechooser(label=_("Image"))
        self._bg_image_filech.connect("file-set", self._on_bg_image_changed)
        self._bg_image_radio_mode_fit = Gtk.RadioButton(None, _("Fit"))
        self._bg_image_radio_mode_fit.connect('toggled', self._on_bg_image_changed)
        self._bg_image_radio_mode_fill = Gtk.RadioButton(
                self._bg_image_radio_mode_fit, _("Fill"))
        h = Gtk.HBox()
        h.pack_start(self._bg_image_radio_mode_fill, True, True, 0)
        h.pack_start(self._bg_image_radio_mode_fit, True, True, 0)
        table.attach_widget(h, label=_("Mode"))
        table.show_all()
        self._load_bg_image()
        
    def _load_bg_image(self):
        'Loads image background settings from the theme'
        bg = self._get_active_bg()
        self._bg_image_filech.set_filename(
                os.path.join(DATA_PATH, 'theme', 'res', bg.src))
        if bg.aspect == exposong.theme.ASPECT_FILL:
            self._bg_image_radio_mode_fill.set_active(True)
        else:
            self._bg_image_radio_mode_fit.set_active(True)
        self.draw()
    
    def _on_bg_image_changed(self, widget):
        """
        Called when any part of the image background widgets changed to
        update the background and the preview
        """
        self._set_changed()
        bg = self._get_active_bg()
        if isinstance(widget, Gtk.FileChooserButton): #New image
            img = widget.get_filename()
            newpath = os.path.join(DATA_PATH, 'theme', 'res', os.path.basename(img))
            if newpath != img:
                shutil.copy(img, newpath)
            bg.src = os.path.basename(img)
            bg.reset_cache()
        if self._bg_image_radio_mode_fill.get_active():
            bg.aspect = exposong.theme.ASPECT_FILL
        else:
            bg.aspect = exposong.theme.ASPECT_FIT
        self.draw()
    
    def _on_bg_solid_new(self, widget=None):
        'Add a new solid color background'
        self._set_changed()
        col = Gdk.Color(random.randint(0,65535),random.randint(0,65535),
                            random.randint(0,65535)).to_string()
        itr = self._bg_model.append((exposong.theme.ColorBackground(color=col),))
        self._activate_bg(itr)
    
    def _on_bg_solid(self, widget=None):
        'Create the widgets for editing solid backgrounds'
        table = self._bg_edit_table
        table.y = 0
        table.foreach(lambda w: table.remove(w))
        
        table.attach_section_title(_("Color Background"))
        self._bg_solid_color_button = table.attach_widget(
                Gtk.ColorButton(), label=_("Color"))
        self._bg_solid_color_button.set_use_alpha(True)
        self._bg_solid_color_button.connect('color-set', self._on_bg_solid_changed)
        table.show_all()
        self._load_bg_solid()
    
    def _on_bg_solid_changed(self, *args):
        """
        Called when any part of the solid background widgets changed to
        update the background and the preview
        """
        self._set_changed()
        self._get_active_bg().color = self._bg_solid_color_button.get_color().to_string()
        self._get_active_bg().alpha = self._bg_solid_color_button.get_alpha()/65535.0
        self.draw()
    
    def _load_bg_solid(self):
        'Loads solid background settings from the theme'
        bg = self._get_active_bg()
        self._bg_solid_color_button.set_color(Gdk.color_parse(bg.color))
        self._bg_solid_color_button.set_alpha(int(bg.alpha*65535))
    
    def _on_bg_gradient_new(self, widget=None):
        'Add a new gradient background'
        self._set_changed()
        itr = self._bg_model.append((exposong.theme.GradientBackground(),))
        self._activate_bg(itr)
    
    def _on_bg_gradient(self, widget=None):
        'Create the widgets for editing gradient backgrounds'
        table = self._bg_edit_table
        table.y = 0
        table.foreach(lambda w: table.remove(w))
        bg = self._get_active_bg()
        
        table.attach_section_title(_("Gradient"))
        self._bg_gradient_colors = []
        self._bg_gradient_lengths = []
        self._bg_gradient_delete_buttons = []
        loc = 0.1
        if len(bg.stops) == 0:
            for i in range(2):
                self._bg_gradient_add_point(update=False)
        for i in range(len(bg.stops)):
            # Color Button
            self._bg_gradient_colors.append(table.attach_widget(
                    Gtk.ColorButton(), label=_("Color %d"%i), yoptions=Gtk.AttachOptions.SHRINK))
            self._bg_gradient_colors[i].set_use_alpha(True)
            self._bg_gradient_colors[i].connect('color-set',
                                                self._on_bg_gradient_changed)
            # Delete Button only when more than two points exist
            if len(bg.stops)>2:
                del_button = Gtk.Button(None)
                img = Gtk.Image()
                img.set_from_stock(Gtk.STOCK_DELETE, Gtk.IconSize.BUTTON)
                del_button.set_image(img)
                del_button.connect('clicked', self._bg_gradient_delete_point, i)
                self._bg_gradient_delete_buttons.append(del_button)
                table.attach(del_button, 2, 3, table.y-1, table.y+1, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.FILL)
            # Position HScale
            self._bg_gradient_lengths.append(table.attach_widget(
                    Gtk.HScale(Gtk.Adjustment(50,0,100,1,10,0)), label=_("Position"), yoptions=Gtk.AttachOptions.SHRINK))
            self._bg_gradient_lengths[i].set_digits(0)
            self._bg_gradient_lengths[i].connect('change-value',
                                                 self._on_bg_gradient_changed)
            table.attach_hseparator(yoptions=Gtk.AttachOptions.SHRINK)
        add = table.attach_widget(Gtk.Button(_("Add Point")))
        add.connect('clicked', self._bg_gradient_add_point)
        
        # TODO Move HScale as helper function to ESTable
        self._bg_gradient_angle = table.attach_widget(Gtk.HScale(
                Gtk.Adjustment(0,0,360,1,10,0)), label=_("Angle"))
        self._bg_gradient_angle.set_digits(0)
        self._bg_gradient_angle.connect('change-value', self._on_bg_gradient_changed)
        table.show_all()
        self._load_bg_gradient()
    
    def _bg_gradient_delete_point(self, button, i):
        'Delete a point from the current gradient background'
        self._get_active_bg().stops.pop(i)
        self._bg_gradient_colors.pop(i)
        self._bg_gradient_delete_buttons.pop(i)
        self._on_bg_gradient()
    
    def _bg_gradient_add_point(self, widget=None, update=True, *args):
        'Adds a new point to the current gradient background'
        self._set_changed()
        bg = self._get_active_bg()
        if len(bg.stops)>0:
            loc = bg.stops[len(bg.stops)-1].location
        else:
            loc = 0.1
            col = '#fff'
        col = Gdk.Color(random.randint(0,65535),random.randint(0,65535),
                            random.randint(0,65535)).to_string()
        if loc > 0.9:
            loc -= random.uniform(0.1, 0.8)
        elif loc < 0.9 and loc > 0.5:
            loc -= random.uniform(0.1, 0.5)
        else:
            loc += random.uniform(0.1, 0.5)
        loc = round(loc, 2)
        bg.stops.append(exposong.theme.GradientStop(location=loc, color=col))
        if update:
            if type(bg) == exposong.theme.GradientBackground:
                self._on_bg_gradient()
            elif type(bg) == exposong.theme.RadialGradientBackground:
                self._on_bg_radial()
    
    def _on_bg_gradient_changed(self, *args):
        """
        Called when any part of the gradient background widgets changed to
        update the background and the preview
        """
        self._set_changed()
        bg = self._get_active_bg()
        for i in range(len(bg.stops)):
            bg.stops[i].color = self._bg_gradient_colors[i].get_color().to_string()
            bg.stops[i].alpha = self._bg_gradient_colors[i].get_alpha()/65535.0
            bg.stops[i].location = self._bg_gradient_lengths[i].get_value()/100.0
        bg.angle = self._bg_gradient_angle.get_value()
        self.draw()
    
    def _load_bg_gradient(self, widget=None):
        'Loads the gradient background settings from the theme'
        bg = self._get_active_bg()
        for i in range(len(bg.stops)):
            self._bg_gradient_colors[i].set_color(Gdk.color_parse(bg.stops[i].color))
            self._bg_gradient_colors[i].set_alpha(int(bg.stops[i].alpha*65535))
        for i in range(len(bg.stops)):
            self._bg_gradient_lengths[i].set_value(bg.stops[i].location*100)
        self._bg_gradient_angle.set_value(bg.angle)
        self.draw()
    
    def _on_bg_radial_new(self, widget=None):
        'Adds a new radial background'
        self._set_changed()
        itr = self._bg_model.append((exposong.theme.RadialGradientBackground(),))
        self._activate_bg(itr)
        
    def _bg_radial_delete_point(self, button, i):
        'Delete a point from the current gradient background'
        self._get_active_bg().stops.pop(i)
        self._bg_radial_colors.pop(i)
        self._bg_radial_delete_buttons.pop(i)
        self._on_bg_radial()
    
    def _on_bg_radial(self, widget=None):
        'Create the widgets for editing radial backgrounds'
        table = self._bg_edit_table
        table.y = 0
        table.foreach(lambda w: table.remove(w))
        bg = self._get_active_bg()
        
        table.attach_section_title(_("Radial Gradient"))
        self._bg_radial_colors = []
        self._bg_radial_lengths = []
        self._bg_radial_delete_buttons = []
        loc = 0.1
        if len(bg.stops) == 0:
            for i in range(2):
                self._bg_gradient_add_point(update=False)
        for i in range(len(bg.stops)):
            # Color Button
            self._bg_radial_colors.append(table.attach_widget(
                    Gtk.ColorButton(), label=_("Color %d")%i,
                                          yoptions=Gtk.AttachOptions.SHRINK))
            self._bg_radial_colors[i].set_use_alpha(True)
            self._bg_radial_colors[i].connect('color-set', self._on_bg_radial_changed)
            # Delete Buttons only if more than two points exits
            if len(bg.stops)>2:
                del_button = Gtk.Button(None)
                img = Gtk.Image()
                img.set_from_stock(Gtk.STOCK_DELETE, Gtk.IconSize.BUTTON)
                del_button.set_image(img)
                del_button.connect('clicked', self._bg_radial_delete_point, i)
                self._bg_radial_delete_buttons.append(del_button)
                table.attach(del_button, 2, 3, table.y-1, table.y+1, xoptions=Gtk.AttachOptions.SHRINK, yoptions=Gtk.AttachOptions.FILL)
            # Position HScale
            self._bg_radial_lengths.append(table.attach_widget(
                    Gtk.HScale(Gtk.Adjustment(50,0,100,1,10,0)), label=_("Position")))
            self._bg_radial_lengths[i].set_digits(0)
            self._bg_radial_lengths[i].connect('change-value', self._on_bg_radial_changed)
            table.attach_hseparator(yoptions=Gtk.AttachOptions.SHRINK)
        add = table.attach_widget(Gtk.Button(_("Add Point")))
        add.connect('clicked', self._bg_gradient_add_point)
        
        # Length HScale 
        self._bg_radial_length = table.attach_widget(
                Gtk.HScale(Gtk.Adjustment(1,1,100,1,10,0)), label=_("Length"))
        self._bg_radial_length.set_digits(0)
        self._bg_radial_length.connect('change-value', self._on_bg_radial_changed)
        self._bg_radial_pos_h = table.attach_widget(
                Gtk.HScale(Gtk.Adjustment(0,0,100,1,10,0)),
                label=_("Horizontal Position"))
        self._bg_radial_pos_h.set_digits(0)
        self._bg_radial_pos_h.connect('change-value', self._on_bg_radial_changed)
        self._bg_radial_pos_v = table.attach_widget(
                Gtk.HScale(Gtk.Adjustment(0,0,100,1,10,0)), label=_("Vertical Position"))
        self._bg_radial_pos_v.set_digits(0)
        self._bg_radial_pos_v.connect('change-value', self._on_bg_radial_changed)
        
        table.show_all()
        self._load_bg_radial()
    
    def _on_bg_radial_changed(self, *args):
        """
        Called when any part of the radial background widgets changed to
        update the background and the preview
        """
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
        'Loads the radial background settings from the theme'
        bg = self._get_active_bg()
        for i in range(len(bg.stops)):
            self._bg_radial_colors[i].set_color(Gdk.color_parse(bg.stops[i].color))
            self._bg_radial_colors[i].set_alpha(int(bg.stops[i].alpha*65535))
        for i in range(len(bg.stops)):
            self._bg_radial_lengths[i].set_value(bg.stops[i].location*100)
        self._bg_radial_length.set_value(bg.length*100)
        self._bg_radial_pos_h.set_value(bg.cpos[0]*100)
        self._bg_radial_pos_v.set_value(bg.cpos[1]*100)
        self.draw()
    
    def _get_active_bg(self):
        'Returns the background of the currently selected item'
        (model, itr) = self._treeview_bgs.get_selection().get_selected()
        if itr:
            return model.get_value(itr, 0)
        return None
    
    def _on_bgs_reordered(self, model, path, itr=None, new_order=None):
        'Called when a background in the list is being dragged to another position'
        GObject.idle_add(self._update_bg_list_from_model)
        self._set_changed()
        GObject.idle_add(self.draw)
    
    def _update_bg_list_from_model(self):
        'Updates the theme background list according to the model'
        self.theme.backgrounds = []
        for bg in self._bg_model:
            self.theme.backgrounds.append(bg[0])
    
    def _on_bg_changed(self, widget):
        'Sets the background edit area to the appropriate widgets'
        bg = self._get_active_bg()
        if not bg:
            self._pos_expander.set_sensitive(False)
            table = self._bg_edit_table
            table.foreach(lambda w: table.remove(w))
            return
        if isinstance(bg, exposong.theme.ImageBackground):
            self._on_bg_image()
        elif isinstance(bg, exposong.theme.ColorBackground):
            self._on_bg_solid()
        elif isinstance(bg, exposong.theme.GradientBackground):
            self._on_bg_gradient()
        elif isinstance(bg, exposong.theme.RadialGradientBackground):
            self._on_bg_radial()
        self._load_bg_position()
    
    def _on_delete_bg(self, *args):
        'Delete a background from the list'
        (model, itr) = self._treeview_bgs.get_selection().get_selected()
        if not itr:
            return False
        msg = _("Are you sure you want to delete this background?")
        dialog = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                   Gtk.MessageType.QUESTION, Gtk.ButtonsType.YES_NO,
                                   msg)
        dialog.set_default_response(Gtk.ResponseType.YES)
        dialog.set_title( _('Delete Background?') )
        resp = dialog.run()
        dialog.hide()
        if resp == Gtk.ResponseType.YES:
            model.remove(itr)
            self._update_bg_list_from_model()
            self.draw()
            self._set_changed(True)
    
    def _bg_get_row_text(self, column, cell, model, titer):
        'Get the background name for the cell'
        bg = model.get_value(titer, 0)
        if isinstance(bg, exposong.theme.ImageBackground):
            cell.set_property('text', "%s: %s"%(bg.get_name(), bg.src))
        else:
            cell.set_property('text', bg.get_name())
    
    def _bg_get_row_color(self, column, cell, model, titer):
        'Get the background color for the cell'
        bg = model.get_value(titer, 0)
        if isinstance(bg, exposong.theme.ColorBackground):
            cell.set_property('cell-background', bg.color)
        elif isinstance(bg, exposong.theme.GradientBackground):
            cell.set_property('cell-background', bg.stops[0].color)
        elif isinstance(bg, exposong.theme.RadialGradientBackground):
            cell.set_property('cell-background', bg.stops[0].color)
        else:
            cell.set_property('cell-background', None)
    
    
    ###########################
    #    Position Expander    #
    ###########################
    def _get_position(self):
        "Return the element positioning settings."
        position = Gtk.Expander(_("Element Position"))
        # Positional elements for backgrounds
        table = gui.ESTable(5,2)
        self._p = {}
        
        adjust = Gtk.Adjustment(0, 0.0, 1.0, 0.01, 0.10)
        self._p['lf'] = table.attach_spinner(adjust, 0.02, 2, label=_('Left:'))
        self._p['lf'].set_numeric(True)
        self._p['lf'].connect('changed', self._on_change_pos)
        
        adjust = Gtk.Adjustment(0, 0.0, 1.0, 0.01, 0.10)
        self._p['rt'] = table.attach_spinner(adjust, 0.02, 2, label=_('Right:'), x=1)
        self._p['rt'].set_numeric(True)
        self._p['rt'].connect('changed', self._on_change_pos)
        
        adjust = Gtk.Adjustment(0, 0.0, 1.0, 0.01, 0.10)
        self._p['tp'] = table.attach_spinner(adjust, 0.02, 2, label=_('Top:'), y=1)
        self._p['tp'].set_numeric(True)
        self._p['tp'].connect('changed', self._on_change_pos)
        
        adjust = Gtk.Adjustment(0, 0.0, 1.0, 0.01, 0.10)
        self._p['bt'] = table.attach_spinner(adjust, 0.02, 2,
                                             label=_('Bottom:'), x=1, y=1)
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
        el = False
        if self._notebook.get_current_page() == 0:
            el = self._get_active_bg()
        elif self._notebook.get_current_page() == 1:
            el = self.theme.get_body()
        elif self._notebook.get_current_page() == 2:
            el = self.theme.get_footer()
        
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
    
    def _nb_page_changed(self, notebook, page, page_num):
        """
        Loads the appropriate values in the position expander
        when the user switches between the notebook tabs
        """
        if not hasattr(self, '_pos_expander'):
            return
        if page_num == 0:
            self._pos_expander.set_label(_("Selected Background Position"))
            if self._get_active_bg():
                self._load_bg_position()
            else:
                self._pos_expander.set_sensitive(False)
        elif page_num == 1:
            self._pos_expander.set_label(_("Body Section Position"))
            self._pos_expander.set_sensitive(True)
            self._load_body_position()
        elif page_num == 2:
            self._pos_expander.set_label(_("Footer Section Position"))
            self._pos_expander.set_sensitive(True)
            self._load_footer_position()
    
    def _load_bg_position(self):
        """
        Sets the values in the position widgets to the position of
        the current background
        """
        bg = self._get_active_bg()
        self._pos_expander.set_sensitive(True)
        self.__updating = True
        self._p['lf'].set_value(bg.pos[0])
        self._p['tp'].set_value(bg.pos[1])
        self._p['rt'].set_value(bg.pos[2])
        self._p['bt'].set_value(bg.pos[3])
        self.__updating = False
    
    def _load_body_position(self):
        """
        Sets the values in the position widgets to the position
        of the body section
        """
        body = self.theme.get_body()
        self.__updating = True
        self._p['lf'].set_value(body.pos[0])
        self._p['tp'].set_value(body.pos[1])
        self._p['rt'].set_value(body.pos[2])
        self._p['bt'].set_value(body.pos[3])
        self.__updating = False
    
    def _load_footer_position(self):
        """
        Sets the values in the position widgets to the position
        of the footer section
        """
        body = self.theme.get_footer()
        self.__updating = True
        self._p['lf'].set_value(body.pos[0])
        self._p['tp'].set_value(body.pos[1])
        self._p['rt'].set_value(body.pos[2])
        self._p['bt'].set_value(body.pos[3])
        self.__updating = False
    
    def _set_changed(self, changed=True):
        'Displays a star (*) in the window title if something has changed'
        self._changed = changed
        if changed:
            if not self.get_title().startswith("*"):
                self.set_title("*%s"%self.get_title())
        else:
            if self.get_title().startswith("*"):
                self.set_title(self.get_title()[1:])
    
    def _load_theme(self, theme):
        'Loads a theme into the Theme Editor'
        if isinstance(theme, exposong.theme.Theme):
            self.theme = theme
        else:
            self.theme = exposong.theme.Theme(theme)
        
        self._title_entry.set_text(self.theme.get_title())
        
        ########################## Backgrounds ################################
        self._bg_model.handler_block_by_func(self._on_bgs_reordered)
        for bg in self.theme.backgrounds:
            self._bg_model.append((bg,))
        self._bg_model.handler_unblock_by_func(self._on_bgs_reordered)
        
        ####################### Sections: Body ################################
        body = self.theme.get_body()
        self.body_widgets['font_button'].set_font_name(body.font)
        self.body_widgets['font_color'].set_color(Gdk.Color(body.color))
        if body.align == exposong.theme.LEFT:
            self.body_widgets['alignment_horizontal'].set_active(0)
        elif body.align == exposong.theme.CENTER:
            self.body_widgets['alignment_horizontal'].set_active(1)
        elif body.align == exposong.theme.RIGHT:
            self.body_widgets['alignment_horizontal'].set_active(2)
        if body.valign:
            self.body_widgets['alignment_vertical'].set_active(body.valign)
        
        self.body_widgets['line_spacing'].set_value(body.spacing)
        if body.shadow_color != None:
            self.body_widgets['shadow_apply'].set_active(True)
        else:
            self._on_shadow_widgets_set_sensitive(self.body_widgets, False)
        self.body_widgets['shadow_color'].set_color(Gdk.Color(body.shadow_color))
        self.body_widgets['shadow_color'].set_alpha(int(body.shadow_opacity*65535))
        self.body_widgets['shadow_x_offset'].set_value(body.shadow_offset[0])
        self.body_widgets['shadow_y_offset'].set_value(body.shadow_offset[1])
        self.body_widgets['outline_size'].set_value(body.outline_size)
        self.body_widgets['outline_color'].set_color(Gdk.Color(body.outline_color))
        
        ##################### Sections: Footer ################################
        footer = self.theme.get_footer()
        self.footer_widgets['font_button'].set_font_name(footer.font)
        self.footer_widgets['font_color'].set_color(Gdk.Color(footer.color))
        if footer.align == exposong.theme.LEFT:
            self.footer_widgets['alignment_horizontal'].set_active(0)
        elif footer.align == exposong.theme.CENTER:
            self.footer_widgets['alignment_horizontal'].set_active(1)
        elif footer.align == exposong.theme.RIGHT:
            self.footer_widgets['alignment_horizontal'].set_active(2)
        if footer.valign:
            self.footer_widgets['alignment_vertical'].set_active(footer.valign)
        
        self.footer_widgets['line_spacing'].set_value(footer.spacing)
        if footer.shadow_color != None:
            self.footer_widgets['shadow_apply'].set_active(True)
        else:
            self._on_shadow_widgets_set_sensitive(self.footer_widgets, False)
        self.footer_widgets['shadow_color'].set_color(Gdk.Color(footer.shadow_color))
        self.footer_widgets['shadow_color'].set_alpha(int(body.shadow_opacity*65535))
        if footer.shadow_offset:
            self.footer_widgets['shadow_x_offset'].set_value(footer.shadow_offset[0])
            self.footer_widgets['shadow_y_offset'].set_value(footer.shadow_offset[1])
        self.footer_widgets['outline_size'].set_value(footer.outline_size)
        self.footer_widgets['outline_color'].set_color(
                Gdk.Color(footer.outline_color))
        
        ##################### Metadata ########################################
        for key, value in self.theme.meta.iteritems():
            if key in self._meta:
                self._meta[key].set_text(value)
        
        self._set_changed(False)
        self.__ready = True
    
    def _revert_changes(self, *args):
        'Reverts all unsaved changes'
        self._bg_model.clear()
        self.theme.revert()
        self._load_theme(self.theme)
        self.draw()
        
    def _save_changes(self, *args):
        """
        Saves the theme to a new file if it didn't exist,
        updates the file according to the theme name if it existed before.
        """
        #Metadata
        for key, value in self._meta.iteritems():
            if value.get_text() != "":
                self.theme.meta[key] = value.get_text()
        name = self._title_entry.get_text()
        self.theme.meta['title'] = name
        if not self.theme.filename:
            self.theme.filename = find_freefile(os.path.join(
                    DATA_PATH, 'theme', title_to_filename(name)+'.xml'))
        else:
            self.theme.filename = check_filename(name, os.path.join(
                    DATA_PATH, 'theme', self.theme.filename))
        self.theme.save()
        self._set_changed(False)
    
    def _close(self, widget, *args):
        'Checks for unsaved changes and closes the Editor'
        if self._changed:
            msg = _("Unsaved Changes will be lost if you close the Editor. \
Do you want to save?")
            dialog = Gtk.MessageDialog(self, Gtk.DialogFlags.MODAL,
                                       Gtk.MessageType.QUESTION, Gtk.ButtonsType.NONE,
                                       msg)
            dialog.set_title( _("Unsaved changes") )
            dialog.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
            dialog.add_button(Gtk.STOCK_NO, Gtk.ResponseType.NO)
            dialog.add_button(Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
            dialog.show_all()
            resp = dialog.run()
            if resp == Gtk.ResponseType.NO:
                self.theme.revert()
            elif resp == Gtk.ResponseType.CANCEL:
                dialog.destroy()
                return True
            elif resp == Gtk.ResponseType.OK:
                self._save_changes()
            dialog.destroy()
        self.destroy()
        global __name__
        if __name__ == "__main__":
            Gtk.main_quit()

