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

import copy
import gtk
try:
    import gtkspell
except Exception:
    pass
import gobject
import os, os.path
import pango
import re
import shutil
from xml.etree import cElementTree as etree
from xml.sax.saxutils import escape, unescape

import exposong.main
import exposong.themeselect
import exposong._hook
import undobuffer
from exposong import RESOURCE_PATH, DATA_PATH
from exposong import gui, theme
from exposong.glob import *
from exposong.plugins import Plugin, _abstract

IMAGE_PATH = os.path.join(DATA_PATH, 'pres', 'res')

"""
Plain text presentations.
"""
information = {
        'name': _("ExpoSong Presentation"),
        'description': __doc__,
        'required': False,
}
type_icon = gtk.gdk.pixbuf_new_from_file_at_size(
        os.path.join(RESOURCE_PATH, 'icons', 'pres-exposong.png'), 20, 14)

class Presentation (Plugin, _abstract.Presentation, exposong._hook.Menu,
                    exposong._hook.Toolbar, _abstract.Schedule):
    """
    ExpoSong presentation type.
    """
    
    class Slide (Plugin, _abstract.Presentation.Slide):
        """
        A text slide.
        """
        def __init__(self, pres, value=None):
            self.pres = pres
            self._content = []
            self.title = ''
            self._theme = None
            if etree.iselement(value):
                self.title = value.get("title", '')
                self._theme = value.get("theme", '')
                for el in value:
                    k = {}
                    k['margin'] = int(el.get('margin', 0))
                    k['pos'] = [0,0,0,0]
                    k['pos'][0] = float(el.get('x1', 0.0))
                    k['pos'][1] = float(el.get('y1', 0.0))
                    k['pos'][2] = float(el.get('x2', 1.0))
                    k['pos'][3] = float(el.get('y2', 1.0))
                    align = theme.get_align_const(el.get('align'))
                    if align != -1:
                        k['align'] = align
                    valign = theme.get_valign_const(el.get('valign'))
                    if valign != -1:
                        k['valign'] = valign
                    if el.tag == 'text':
                        k['markup'] = unescape(element_contents(el, True))
                        self._content.append(theme.Text(**k))
                    elif el.tag == 'image':
                        if el.get('src'):
                            k['src'] = os.path.join(IMAGE_PATH, el.get('src'))
                        else:
                            k['src'] = ''
                        k['aspect'] = theme.get_aspect_const(el.get('aspect'),
                                                             theme.ASPECT_FIT)
                        
                        self._content.append(theme.Image(**k))
            
            self._set_id(value)
            _abstract.Presentation.Slide.__init__(self, pres, value)
        
        def get_theme(self):
            'Return the theme for this slide.'
            if self._theme:
                for thm in exposong.themeselect.themeselect.get_model():
                    if self._theme == os.path.split(thm[0])[1]:
                        return thm[1]
                else:
                    exposong.log.warning('Custom theme "%s" not found.' % 
                                         self._theme)
            return None
        
        def _edit_window(self, parent):
            'Open the Slide Edit Dialog'
            ret = 0
            editor = SlideEdit(parent, self)
            while True:
                ans = editor.run()
                if ans == gtk.RESPONSE_ACCEPT:
                    if editor.changed:
                        self.title = editor.get_slide_title()
                        self._content = editor.slide_content
                        ret = 1
                elif ans == gtk.RESPONSE_APPLY: #Close and new
                    if editor.changed:
                        self.title = editor.get_slide_title()
                        self._content = editor.slide_content
                    ret = 2
                return ret
        
        def get_body(self):
            return self._content
        
        def to_node(self, node):
            'Populate the XML element.'
            if self.title:
                node.set('title', self.title)
            if self._theme:
                node.set('theme', self._theme)
            for c in self._content:
                if isinstance(c, theme.Text):
                    txt = escape(c.markup)
                    node2 = etree.fromstring('<text>%s</text>' % txt)
                elif isinstance(c, theme.Image):
                    node2 = etree.Element('image')
                    
                    # TODO make sure moving the file works correctly.
                    fpath, fname = os.path.split(c.src)
                    if not os.path.isdir(IMAGE_PATH):
                        os.makedirs(IMAGE_PATH)
                    if os.path.abspath(IMAGE_PATH) != os.path.abspath(fpath):
                        newfile = find_freefile(os.path.join(IMAGE_PATH, fname))
                        try:
                            shutil.copyfile(c.src, newfile)
                            c.src = newfile
                        except IOError:
                            exposong.log.error("Could not move file to DATA_PATH/theme/res/%s"
                                               % newfile)
                    node2.set('src', fname)
                    node2.set('aspect', theme.get_aspect_key(c.aspect))
                else:
                    continue
                
                node2.set('x1', str(c.pos[0]))
                node2.set('y1', str(c.pos[1]))
                node2.set('x2', str(c.pos[2]))
                node2.set('y2', str(c.pos[3]))
                
                node2.set('align', theme.get_align_key(c.align))
                node2.set('valign', theme.get_valign_key(c.valign))
                node2.set('margin', str(c.margin))
                node2.tail = '\n  '
                node.append(node2)
                node.text = '\n  '
        
        def copy(self):
            'Create a duplicate of the slide.'
            slide = _abstract.Presentation.Slide.copy(self)
            slide._theme = self._theme
            slide._content = copy.deepcopy(self._content)
            return slide
        
        @staticmethod
        def get_version():
            "Return the version number of the plugin."
            return (1,0)
    
        @staticmethod
        def get_description():
            "Return the description of the plugin."
            return "A lyric presentation type."
    
    def __init__(self, filename=''):
        self.filename = filename
        self._meta = {}
        self.slides = []
        self._title = ''
        self._timer = None
        self._timer_loop = False
        
        if filename:
            fl = open(filename, 'r')
            if not self.is_type(fl):
                fl.close()
                raise _abstract.WrongPresentationType
            fl.close()
            
            dom = None
            try:
                dom = etree.parse(filename)
                root = dom.getroot()
            except IOError, details:
                exposong.log.error('Could not open presentation "%s": %s',
                                   filename, details)
            else:
                for el in root.find("meta"):
                    if el.tag == 'title':
                        self._title = el.text
                    elif el.tag == 'timer':
                        self._timer = int(el.get("time"))
                        self._timer_loop = bool(el.get("loop", False))
                    else:
                        self._meta[el.tag] = el.text
                slides = root.findall("slides/slide")
                for sl in slides:
                    self.slides.append(self.Slide(self, sl))
        
        # TODO Order
        self._order = []
    
    def to_xml(self):
        'Save the data to disk.'
        if self.filename:
            self.filename = check_filename(self.get_title(), self.filename)
        else:
            self.filename = check_filename(self.get_title(),
                                           os.path.join(DATA_PATH, "pres"))
        
        root = etree.Element("presentation")
        root.text = "\n"
        
        meta = etree.Element("meta")
        meta.text = meta.tail = "\n"
        node = etree.Element("title")
        node.text = self.get_title()
        node.tail = "\n"
        meta.append(node)
        
        if self._timer:
            node = etree.Element("timer")
            node.attrib['time'] = str(self._timer)
            if self._timer_loop:
                node.attrib['loop'] = "1"
            node.tail = "\n"
            meta.append(node)
        
        for k, v in self._meta.iteritems():
            node = etree.Element(k)
            node.text = v
            node.tail = "\n"
            meta.append(node)
        root.append(meta)
        
        slides = etree.Element("slides")
        slides.text = slides.tail = "\n"
        for s in self.slides:
            node = etree.Element("slide")
            s.to_node(node)
            node.tail = '\n'
            slides.append(node)
        root.append(slides)
        doc = etree.ElementTree(root)
        outfile = open(self.filename, 'w')
        doc.write(outfile, encoding=u'UTF-8')
    
    # GUI
    
    def _edit_tabs(self, notebook, parent):
        "Tabs for the dialog."
        vbox = gtk.VBox()
        vbox.set_border_width(4)
        vbox.set_spacing(7)
        hbox = gtk.HBox()
        
        label = gtk.Label(_("Title:"))
        label.set_alignment(0.5, 0.5)
        hbox.pack_start(label, False, True, 5)
        
        self._fields['title'] = gtk.Entry(45)
        self._fields['title'].set_text(self.get_title())
        hbox.pack_start(self._fields['title'], True, True)
        vbox.pack_start(hbox, False, True)
        
        self._fields['slides'] = gtk.ListStore(gobject.TYPE_PYOBJECT, str)
        # Add the slides
        for sl in self.get_slide_list(True):
            self._fields['slides'].append(sl)
        self._fields['slides'].connect("row-changed", self._on_slide_added)
        
        self._slide_list = gtk.TreeView(self._fields['slides'])
        self._slide_list.set_enable_search(False)
        self._slide_list.set_reorderable(True)
        # Double click to edit
        self._slide_list.connect("row-activated", self._slide_dlg, True)
        col = gtk.TreeViewColumn( _("Slide") )
        col.set_resizable(False)
        self.slide_column(col)
        self._slide_list.append_column(col)
        
        toolbar = gtk.Toolbar()
        btn = gtk.MenuToolButton(gtk.STOCK_ADD)
        btn.connect('clicked', gui.edit_treeview_row_btn, self._slide_list,
                    self._slide_dlg)
        # Template types
        btn.set_menu(self._get_predefined_slides_menu())
        toolbar.insert(btn, -1)
        btn = gtk.ToolButton(gtk.STOCK_EDIT)
        btn.connect('clicked', gui.edit_treeview_row_btn, self._slide_list,
                    self._slide_dlg, True)
        toolbar.insert(btn, -1)
        btn = gtk.ToolButton(gtk.STOCK_DELETE)
        btn.connect("clicked", self._on_slide_delete, self._slide_list, parent)
        toolbar.insert(btn, -1)
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        
        vbox.pack_start(toolbar, False, True)
        
        scroll = gtk.ScrolledWindow()
        scroll.add(self._slide_list)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.set_size_request(400, 250)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        vbox.pack_start(scroll, True, True)
        
        vbox.show_all()
        notebook.insert_page(vbox, gtk.Label(_("Edit")), 0)
        self._fields['title'].grab_focus()
        
        # TODO Ordering Lists
        #vbox = gtk.VBox()
        #notebook.insert_page(vbox, gtk.Label(_("Order")), 1)
        
        # Meta information
        vbox = gtk.VBox()
        
        tree = gtk.TreeView()
        self._fields['meta'] = gtk.ListStore(str, str)
        for k,v in self._meta.iteritems():
            self._fields['meta'].append((k,v))
        tree.set_model(self._fields['meta'])
        tree.connect('row-activated', self._meta_dlg, True)
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Name'))
        col.pack_start(cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 0)
        tree.append_column(col)
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn( _('Value'))
        col.pack_start(cell)
        col.set_resizable(True)
        col.add_attribute(cell, 'text', 1)
        tree.append_column(col)
        scroll = gtk.ScrolledWindow()
        scroll.add(tree)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.set_size_request(400, 250)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        #Toolbar
        toolbar = gtk.Toolbar()
        button = gtk.ToolButton(gtk.STOCK_ADD)
        button.connect('clicked', gui.edit_treeview_row_btn, tree,
                       self._meta_dlg)
        toolbar.insert(button, -1)
        button = gtk.ToolButton(gtk.STOCK_EDIT)
        button.connect('clicked', gui.edit_treeview_row_btn, tree,
                       self._meta_dlg, True)
        tree.get_selection().connect('changed', gui.treesel_disable_widget,
                                     button)
        toolbar.insert(button, -1)
        button = gtk.ToolButton(gtk.STOCK_DELETE)
        button.connect('clicked', gui.del_treeview_row, tree)
        tree.get_selection().connect('changed', gui.treesel_disable_widget,
                                     button)
        toolbar.insert(button, -1)
        vbox.pack_start(toolbar, False, True)
        tree.get_selection().emit('changed')
        
        vbox.pack_start(scroll, True, True)
        notebook.append_page(vbox, gtk.Label(_('Information')))
        
        timer = gtk.VBox()
        timer.set_border_width(8)
        timer.set_spacing(7)
        
        # Might be used later if more things get on this tab
        #label = gtk.Label()
        #label.set_markup(_("<b>Timer</b>"))
        #label.set_alignment(0.0, 0.5)
        #timer.pack_start(label, False)
        
        self._fields['timer_on'] = gtk.CheckButton(_("Use Timer"))
        self._fields['timer_on'].set_active(self._timer is not None)
        self._fields['timer_on'].connect("toggled",
                lambda chk: self._fields['timer'].set_sensitive(chk.get_active()))
        self._fields['timer_on'].connect("toggled",
                lambda chk: self._fields['timer_loop'].set_sensitive(chk.get_active()))
        self._fields['timer_on'].connect("toggled",
                lambda chk: self._fields['timer_seconds'].set_sensitive(chk.get_active()))
        timer.pack_start(self._fields['timer_on'], False)
        
        self._fields['timer_seconds'] = gtk.Label(_("Seconds Per Slide"))
        self._fields['timer_seconds'].set_sensitive(self._timer is not None)
        hbox = gtk.HBox()
        hbox.set_spacing(18)
        hbox.pack_start(self._fields['timer_seconds'], False, False)
        
        adjust = gtk.Adjustment(1, 1, 25, 1, 3, 0)
        self._fields['timer'] = gtk.SpinButton(adjust, 1, 0)
        self._fields['timer'].set_sensitive(self._timer is not None)
        if isinstance(self._timer, (int, float)):
            self._fields['timer'].set_value(self._timer)
        hbox.pack_start(self._fields['timer'], False, False)
        timer.pack_start(hbox, False)
        
        self._fields['timer_loop'] = gtk.CheckButton(_("Loop Slides"))
        self._fields['timer_loop'].set_active(self._timer_loop)
        self._fields['timer_loop'].set_sensitive(self._timer is not None)
        timer.pack_start(self._fields['timer_loop'], False, False)
        
        notebook.append_page(timer, gtk.Label( _("Timer") ))
        
        _abstract.Presentation._edit_tabs(self, notebook, parent)
    
    def _meta_dlg(self, treeview, path, col, edit=False):
        "Add or edit a meta element."
        dialog = gtk.Dialog(_("Presentation Information"),
                            treeview.get_toplevel(),
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                            (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                            gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        table = gui.ESTable(2, auto_inc_y=True)
        dialog.vbox.pack_start(table, True, True)
        
        model = treeview.get_model()
        key = val = None
        if edit:
            itr = model.get_iter(path)
            if model.get_value(itr,0):
                dialog.set_title( _('Editing "%s"') % model.get_value(itr,0) )
            key = model.get_value(itr,0)
            val = model.get_value(itr,1)
        key_entry = table.attach_entry(key, label=_('Name:'))
        val_entry = table.attach_entry(val, label=_('Value:'))
        dialog.vbox.show_all()
        
        while True:
            if dialog.run() == gtk.RESPONSE_ACCEPT:
                if not key_entry.get_text():
                    info_dialog = gtk.MessageDialog(treeview.get_toplevel(),
                                                    gtk.DIALOG_DESTROY_WITH_PARENT,
                                                    gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
                                                    _("Please enter a Key."))
                    info_dialog.run()
                    info_dialog.destroy()
                else:
                    if edit:
                        model.set_value(itr, 0, key_entry.get_text())
                        model.set_value(itr, 1, val_entry.get_text())
                    else:
                        model.append((key_entry.get_text(), val_entry.get_text()))
                    dialog.hide()
                    return True
            else:
                dialog.hide()
                return False
        dialog.destroy()
    
    def _edit_save(self):
        "Save the fields if the user clicks ok."
        self._title = self._fields['title'].get_text()
        itr = self._fields['slides'].get_iter_first()
        self.slides = []
        while itr:
            self.slides.append(self._fields['slides'].get_value(itr,0))
            itr = self._fields['slides'].iter_next(itr)
        
        # Meta
        self._meta = {}
        for row in self._fields['meta']:
            self._meta[row[0]] = row[1]
        
        # Timer
        if self._fields['timer_on'].get_active():
            self._timer = self._fields['timer'].get_value_as_int()
            self._timer_loop = self._fields['timer_loop'].get_active()
        else:
            self._timer = None
        
        _abstract.Presentation._edit_save(self)
    
    def _is_editing_complete(self, parent):
        "Test to see if all fields have been filled which are required."
        if self._fields['title'].get_text() == "":
            info_dialog = gtk.MessageDialog(parent,
                                            gtk.DIALOG_DESTROY_WITH_PARENT,
                                            gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
                                            _("Please enter a Title."))
            info_dialog.run()
            info_dialog.destroy()
            return False
        if len(self._fields['slides']) == 0:
            msg = _('The presentation must have at least one slide.')
            info_dialog = gtk.MessageDialog(parent,
                                            gtk.DIALOG_DESTROY_WITH_PARENT,
                                            gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
                                            msg)
            info_dialog.run()
            info_dialog.destroy()
            return False
        return _abstract.Presentation._is_editing_complete(self, parent)
    
    def _slide_dlg(self, treeview, path, col, edit=False):
        "Create a dialog for a new slide."
        model = treeview.get_model()
        if edit:
            itr = model.get_iter(path)
            if not itr:
                return False
            # Edit on a copy, so Cancel will work.
            sl = model.get_value(itr, 0).copy()
            old_title = sl.title
        else:
            sl = self.Slide(self, None)
        
        ans = sl._edit_window(treeview.get_toplevel())
        if ans:
            if edit:
                if len(old_title) == 0 or old_title != sl.title:
                    sl._set_id()
                model.set(itr, 0, sl, 1, sl.get_markup(True))
            else:
                sl._set_id()
                model.append( (sl, sl.get_markup(True)) )
        if ans == 2:
            self._slide_dlg(treeview, None, None)
    
    def _on_slide_added(self, model, path, iter):
        self._slide_list.set_cursor(path)
        
    def _on_slide_delete(self, btn, treeview, parent):
        'Remove the selected slide.'
        (model, itr) = treeview.get_selection().get_selected()
        if not itr:
            return False
        msg = _('Are you sure you want to delete this slide? This cannot be undone.')
        dialog = gtk.MessageDialog(exposong.main.main, gtk.DIALOG_MODAL,
                                   gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
                                   msg)
        dialog.set_title( _('Delete Slide?') )
        resp = dialog.run()
        dialog.hide()
        if resp == gtk.RESPONSE_YES:
            model.remove(itr)

    ## Predefined Slide Types
    
    def _get_predefined_slides_menu(self):
        "Returns a menu of predefined slide types."
        menu = gtk.Menu()
        
        #Text Types
        action = gtk.Action('add-text-slide', _('Text Slide'),
                            _('Create a slide with text only.'), None)
        action.connect('activate', self._on_add_text_slide)
        menu.append(action.create_menu_item())
        
        menu.append(gtk.SeparatorMenuItem())
        
        #Image Types
        action = gtk.Action('add-image-slide', _('Image Slide'),
                            _('Create a slide with an image only.'), None)
        action.connect('activate', self._on_add_image_slide)
        menu.append(action.create_menu_item())
        
        action = gtk.Action('add-image-caption-slide',
                            _('Image Slide With Caption'),
                            _('Create an image slide with a caption.'), None)
        action.connect('activate', self._on_add_image_caption_slide)
        menu.append(action.create_menu_item())
        
        menu.append(gtk.SeparatorMenuItem())
        
        action = gtk.Action('bulk-add-image-slide', _('Multiple Image Slides'),
                            _('Add multiple image slides from image files.'),
                            None)
        action.connect('activate', self._on_add_bulk_image_slide)
        menu.append(action.create_menu_item())
        
        return menu
    
    def _on_add_text_slide(self, action):
        "Add a simple text slide."
        sl = self.Slide(self, None)
        sl._content = [theme.Text("")]
        
        ans = sl._edit_window(self._fields['title'].get_toplevel())
        if ans:
            sl._set_id()
            self._fields['slides'].append( (sl, sl.get_markup(True)) )
        if ans == 2:
            self._on_add_text_slide(action)
    
    def _on_add_image_slide(self, action):
        "Add a single image slide."
        sl = self.Slide(self, None)
        sl._content = [theme.Image(None)]
        
        ans = sl._edit_window(self._fields['title'].get_toplevel())
        if ans:
            sl._set_id()
            self._fields['slides'].append( (sl, sl.get_markup(True)) )
        if ans == 2:
            self._on_add_image_slide(action)
    
    def _on_add_image_caption_slide(self, action):
        "Add an image slide with a caption."
        sl = self.Slide(self, None)
        sl._content = [theme.Image(None, pos=[0.0, 0.0, 1.0, 0.85]),
                       theme.Text('', pos=[0.0, 0.85, 1.0, 1.0])]
        
        ans = sl._edit_window(self._fields['title'].get_toplevel())
        if ans:
            sl._set_id()
            self._fields['slides'].append( (sl, sl.get_markup(True)) )
        if ans == 2:
            self._on_add_image_caption_slide(action)
    
    def _on_add_bulk_image_slide(self, action):
        "Add multiple images from the filesystem."
        fchooser = gtk.FileChooserDialog( _("Add Images"),
                self._fields['title'].get_toplevel(),
                gtk.FILE_CHOOSER_ACTION_OPEN,
                (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                gtk.STOCK_ADD, gtk.RESPONSE_ACCEPT) )
        fchooser.set_current_folder(os.path.expanduser("~"))
        fchooser.set_select_multiple(True)
        progress = gtk.ProgressBar()
        fchooser.set_extra_widget(progress)
        
        filt = gtk.FileFilter()
        filt.set_name( _("Image Types") )
        filt.add_pixbuf_formats()
        fchooser.add_filter(filt)
        preview = gtk.Image()
        fchooser.set_preview_widget(preview)
        fchooser.connect("update-preview", gui.filechooser_preview, preview)
        if fchooser.run() == gtk.RESPONSE_ACCEPT:
            files = fchooser.get_filenames()
            for fl in files:
                sl = self.Slide(self)
                sl.title = _("Image: %s" % os.path.split(fl)[1])
                sl._content = [theme.Image(fl)]
                sl._set_id()
                self._fields['slides'].append( (sl, sl.get_markup(True)) )
                progress.set_fraction(progress.get_fraction() + 1.0/len(files))
                #It may be better to use generator statements here.
                #http://faq.pygtk.org/index.py?req=show&file=faq23.020.htp
                #This makes the progressbar change.
                while gtk.events_pending():
                    gtk.main_iteration()
            
        fchooser.destroy()
    
    ## Order
    
    def get_order(self):
        "Returns the order in which the slides should be presented."
        if len(self._order) > 0:
            return tuple(self.get_slide_from_order(n) for n in self._order)
        else:
            return _abstract.Presentation.get_order(self)

    def get_slide_from_order(self, order_value):
        "Gets the slide index."
        i = 0
        for sl in self.slides:
            if(sl.id == order_value):
                return i
            i += 1
        return -1
    
    ## Timer
    
    def get_timer(self):
        'Return the time until we skip to the next slide.'
        return self._timer
    
    def is_timer_looped(self):
        'If this is True, go to the beginning when the timer reaches the end.'
        return self._timer_loop
    
    ## Slidelist view
    
    def slide_column(self, col):
        'Sets the column for slidelist.'
        col.clear()
        cr = exposong.themeselect.CellRendererTheme()
        cr.height = 100
        cr.can_cache = False
        for thm in exposong.themeselect.themeselect.get_model():
            if '_builtin_black' == thm[0]:
                cr.theme = thm[1]
        col.pack_start(cr, False)
        col.add_attribute(cr, 'slide', 0)
    
    def get_row(self):
        'Gets the data to add to the presentation list.'
        return (self, self.get_title())
    
    ## Printing
    
    def get_print_markup(self):
        "Return the presentation markup for printing."
        markup = "<span face='sans' weight='bold' size='large'>%s</span>"\
                 % self.get_title()
        markup += "\n\n\n"
        for slide in self.get_slide_list():
            markup += "<span weight='bold' face='sans' size='%%(fontsize)d'>%s</span>\n"\
                      % slide[0].get_title()
            markup += "<span face='sans' size='%%(fontsize)d'>%s</span>\n\n" % slide[0].get_text()
        
        return markup
    
    def can_print(self):
        "Return True if printing is available."
        return True
    
    @classmethod
    def is_type(cls, fl):
        "Test to see if this file is the correct type."
        match = r'<presentation\b'
        lncnt = 0
        for ln in fl:
            if lncnt > 2:
                break
            if re.search(match, ln):
                    return True
            lncnt += 1
        return False
    
    @staticmethod
    def get_type_name():
        return information['name']
    
    @staticmethod
    def get_type():
        "Return the presentation type."
        return 'text'
    
    @staticmethod
    def get_icon():
        "Return the pixbuf icon."
        return type_icon
    
    @classmethod
    def merge_menu(cls, uimanager):
        "Merge new values with the uimanager."
        gtk.stock_add([('pres-exposong',_('_ExpoSong Presentation'),
                        gtk.gdk.MOD1_MASK, 0, 'pymserv')])
        
        actiongroup = gtk.ActionGroup('exposong-pres')
        actiongroup.add_actions([('pres-new-exposong', 'pres-exposong-new',
                None, None, _("New ExpoSong Presentation"), cls._on_pres_new)])
        uimanager.insert_action_group(actiongroup, -1)
        
        cls.menu_merge_id = uimanager.add_ui_from_string("""
            <menubar name='MenuBar'>
                <menu action='Presentation'>
                        <menu action='pres-new'>
                            <menuitem action='pres-new-exposong' />
                        </menu>
                </menu>
            </menubar>
            """)
    
    @classmethod
    def unmerge_menu(cls, uimanager):
        "Remove merged items from the menu."
        uimanager.remove_ui(cls.menu_merge_id)
    
    @classmethod
    def merge_toolbar(cls, uimanager):
        'Merge new values with the uimanager'
        cls.tb_merge_id = uimanager.add_ui_from_string("""
            <toolbar name='Toolbar'>
                <placeholder name="pres-new-exposong">
                    <toolitem action='pres-new-exposong' />
                </placeholder>
            </toolbar>
            """)
    
    @classmethod
    def unmerge_toolbar(cls, uimanager):
        'Remove merged items from the toolbar.'
        uimanager.remove_ui(cls.tb_merge_id)
    
    @classmethod
    def schedule_name(cls):
        "Return the string schedule name."
        return _('ExpoSong Presentations')
    
    @classmethod
    def schedule_filter(cls, pres):
        "Called on each presentation, and return True if it can be added."
        return pres.__class__ is cls
    
    @staticmethod
    def get_version():
        "Return the version number of the plugin."
        return (1,0)
    
    @staticmethod
    def get_description():
        "Return the description of the plugin."
        return 'A text presentation type.'


class SlideEdit(gtk.Dialog):
    """Create a new window for editing a single slide.
         Contains a title field, a toolbar and a TextView.
    """
    def __init__(self, parent, slide):
        gtk.Dialog.__init__(self, _("Editing Slide"), parent,
                            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT)
        
        # Slide Elements
        lstore = gtk.ListStore(gobject.TYPE_PYOBJECT)
        self._tree = gtk.TreeView(lstore)
        for e in slide._content:
            lstore.append((e,))
        col = gtk.TreeViewColumn( _("Slide Element") )
        text = gtk.CellRendererText()
        text.set_property("ellipsize", pango.ELLIPSIZE_END)
        col.pack_start(text, True)
        col.set_cell_data_func(text, self._set_slide_row_text)
        self._tree.append_column(col)
        self._tree.set_headers_clickable(False)
        self._tree.get_selection().select_path((0,))
        
        self.set_border_width(4)
        self.vbox.set_spacing(7)
        
        cancelbutton = self.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT)
        cancelbutton.connect("clicked", self._quit_without_save)
        newbutton = self.add_button(_("Save and New"), gtk.RESPONSE_APPLY)
        newimg = gtk.Image()
        newimg.set_from_stock(gtk.STOCK_NEW, gtk.ICON_SIZE_BUTTON)
        newbutton.set_image(newimg)
        newbutton.connect("clicked", self._quit_with_save)
        okbutton = self.add_button(gtk.STOCK_OK, gtk.RESPONSE_ACCEPT)
        okbutton.connect("clicked", self._quit_with_save)
        
        hbox = gtk.HBox()
        hbox.set_spacing(7)
        vbox = gtk.VBox()
        vbox.set_spacing(7)
        
        self.connect("delete-event", self._quit_without_save)
        
        self.slide_title = slide.title
        self.slide_content = slide._content
        self.changed = False
        
        # Title
        vbox.pack_start(self._get_title_box(), False, True)
        
        # Toolbar
        gtk.stock_add([('add-text',_('Add Text'), gtk.gdk.MOD1_MASK, 0,
                        'pymserv'),
                       ("add-image",_('Add Image'), gtk.gdk.MOD1_MASK, 0,
                        'pymserv')])
        toolbar = gtk.Toolbar()
        button = gtk.ToolButton(gtk.stock_lookup('add-text')[0])
        button.set_tooltip_markup(_('Add a new text element.'))
        button.connect('clicked', self._add_text, self._tree)
        toolbar.insert(button, -1)
        button = gtk.ToolButton(gtk.stock_lookup('add-image')[0])
        button.set_tooltip_markup(_('Add a new image element.'))
        button.connect('clicked', self._add_image, self._tree)
        toolbar.insert(button, -1)
        button = gtk.ToolButton(gtk.STOCK_DELETE)
        button.connect('clicked', self._delete_row, self._tree)
        self._tree.get_selection().connect('changed',
                                           gui.treesel_disable_widget, button)
        toolbar.insert(button, -1)
        vbox.pack_start(toolbar, False, True)
        
        
        self._tree.get_selection().connect("changed", self._element_changed)
        
        scroll = gtk.ScrolledWindow()
        scroll.add(self._tree)
        scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scroll.set_size_request(280, 250)
        scroll.set_shadow_type(gtk.SHADOW_IN)
        vbox.pack_start(scroll, True, True)
        hbox.pack_start(vbox, False, True)
        
        # This will contain an editor for a `theme._RenderableSection`
        # It will load when an item is selected from the left.
        self._ctbl = gui.ESTable(4,1)
        
        hbox.pack_start(self._ctbl, True, True)
        
        self.vbox.pack_start(hbox, True, True)
        self.vbox.show_all()
        self._tree.get_selection().emit("changed")
    
    def get_slide_title(self):
        "Returns the title of the edited slide."
        return self.slide_title
    
    def _get_title_value(self):
        "Returns the title value in the entry field."
        return self._title_entry.get_text()
    
    def _get_title_box(self):
        "Gets the title entry field."
        hbox = gtk.HBox()
        self._title_label = gtk.Label(_('Title:'))
        self._title_label.set_alignment(0.5,0.5)
        hbox.pack_start(self._title_label, False, True)
        
        self._title_entry = gtk.Entry()
        self._title_entry.set_text(self.slide_title)
        hbox.pack_start(self._title_entry, True, True)
        return hbox
    
    def _get_position(self):
        "Return the element positioning settings."
        el = self.get_selected_element()
        if el is False:
            return
        
        position = gtk.Expander(_("Element Position"))
        # Positional elements that are in all `theme._RenderableSection`s.
        table = gui.ESTable(5, 2)
        self._p = {}
        
        help_ = gtk.image_new_from_stock(gtk.STOCK_HELP, gtk.ICON_SIZE_BUTTON)
        helppos = _("Positions are relative, with values between 0 and 1. \
A value of 0 is on the far left or top, and a value of 1 is on the far right or bottom.")
        help_.set_tooltip_text(helppos)
        table.attach_widget(help_, None, x=2, y=0)
        
        adjust = gtk.Adjustment(el.pos[0], 0.0, 1.0, 0.01, 0.10)
        self._p['lf'] = table.attach_spinner(adjust, 0.02, 2, label=_('Left:'))
        self._p['lf'].set_numeric(True)
        self._p['lf'].connect('changed', self._on_change_pos)
        
        adjust = gtk.Adjustment(el.pos[2], 0.0, 1.0, 0.01, 0.10)
        self._p['rt'] = table.attach_spinner(adjust, 0.02, 2, label=_('Right:'), x=1)
        self._p['rt'].set_numeric(True)
        self._p['rt'].connect('changed', self._on_change_pos)
        
        adjust = gtk.Adjustment(el.pos[1], 0.0, 1.0, 0.01, 0.10)
        self._p['tp'] = table.attach_spinner(adjust, 0.02, 2, label=_('Top:'), y=1)
        self._p['tp'].set_numeric(True)
        self._p['tp'].connect('changed', self._on_change_pos)
        
        adjust = gtk.Adjustment(el.pos[3], 0.0, 1.0, 0.01, 0.10)
        self._p['bt'] = table.attach_spinner(adjust, 0.02, 2, label=_('Bottom:'),
                                             x=1, y=1)
        self._p['bt'].set_numeric(True)
        self._p['bt'].connect('changed', self._on_change_pos)
        
        adjust = gtk.Adjustment(el.margin, 0, 40, 1, 5)
        self._p['mg'] = table.attach_spinner(adjust, 1, 0, label=_('Margin:'),
                                             y=2, w=2)
        self._p['mg'].set_numeric(True)
        self._p['mg'].connect('changed', self._on_change_mg)
        
        self._p['al'] = table.attach_combo(map(theme.get_align_text, (theme.LEFT,
                                           theme.CENTER, theme.RIGHT)),
                                           None, label=_('Alignment:'), y=3, w=2)
        gui.set_active_text(self._p['al'], theme.get_align_text(el.align))
        self._p['al'].connect('changed', self._on_change_al)
        
        self._p['va'] = table.attach_combo(map(theme.get_valign_text, (theme.TOP,
                                           theme.MIDDLE, theme.BOTTOM)),
                                           None, label=_('Vertical Alignment:'),
                                           y=4, w=2)
        gui.set_active_text(self._p['va'], theme.get_valign_text(el.valign))
        self._p['va'].connect('changed', self._on_change_va)
        
        position.add(table)
        return position
    
    def _element_changed(self, sel):
        "Sets the editing area when the selection changes."
        self.__updating = True
        self._ctbl.foreach(lambda w: self._ctbl.remove(w))
        el = self.get_selected_element()
        
        if el is False:
            st = _("Select or add an item from the left to edit.")
            label = self._ctbl.attach_label(st, h=4,
                                            xoptions=gtk.EXPAND|gtk.FILL,
                                            yoptions=gtk.EXPAND|gtk.FILL)
            label.set_line_wrap(True)
            label.set_alignment(0.5, 0.5)
        elif isinstance(el, theme.Text):
            buffer_ = undobuffer.UndoableBuffer()
            
            # Toolbar
            toolbar = gtk.Toolbar()
            undo = gtk.ToolButton(gtk.STOCK_UNDO)
            undo.connect('clicked', self._undo, buffer_)
            undo.set_sensitive(False)
            toolbar.insert(undo, -1)
            redo = gtk.ToolButton(gtk.STOCK_REDO)
            redo.connect('clicked', self._redo, buffer_)
            redo.set_sensitive(False)
            toolbar.insert(redo, -1)
            self._ctbl.attach_widget(toolbar,
                                     yoptions=gtk.FILL)
            
            text = gtk.TextView()
            text.set_wrap_mode(gtk.WRAP_NONE)
            buffer_.begin_not_undoable_action()
            
            buffer_.set_text(el.markup)
            buffer_.end_not_undoable_action()
            buffer_.set_modified(False)
            buffer_.connect("changed", self._on_text_buffer_changed, undo, redo)
            text.set_buffer(buffer_)
            
            try:
                gtkspell.Spell(text)
            except Exception:
                pass
            scroll = gtk.ScrolledWindow()
            scroll.add(text)
            scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            scroll.set_size_request(250, -1)
            scroll.set_shadow_type(gtk.SHADOW_IN)
            self._ctbl.attach_widget(scroll, y=1, h=3,
                                     yoptions=gtk.FILL|gtk.EXPAND)
        elif isinstance(el, theme.Image):
            fc = gtk.FileChooserButton("Select Image")
            fc.set_size_request(250, -1)
            fc.set_action(gtk.FILE_CHOOSER_ACTION_OPEN)
            if el.src:
                fc.set_filename(el.src)
            
            filt = gtk.FileFilter()
            filt.add_pixbuf_formats()
            fc.set_filter(filt)
            
            preview = gtk.Image()
            fc.set_preview_widget(preview)
            fc.connect("update-preview", gui.filechooser_preview, preview)
            fc.connect("file-set", self._on_image_changed)
            self._ctbl.attach_widget(fc)
            
            self._image_preview = gtk.Image()
            self._ctbl.attach_widget(self._image_preview, y=1)
            gui.update_image_preview(self._image_preview, el.src)
            
            options = map(theme.get_aspect_text,
                          (theme.ASPECT_FIT, theme.ASPECT_FILL))
            aspect = self._ctbl.attach_combo(options, None, y=2,
                                             label=_('Resize to:'))
            gui.set_active_text(aspect, theme.get_aspect_text(el.aspect))
            aspect.connect('changed', self._on_change_aspect)
        
        if el is not False:
            self._ctbl.attach_widget(self._get_position(), y=6)
            # TODO Custom Theme
        self._ctbl.show_all()
        self.__updating = False
    
    def _on_text_buffer_changed(self, buffer_, undo, redo):
        "The TextBuffer changed."
        undo.set_sensitive(buffer_.can_undo)
        redo.set_sensitive(buffer_.can_redo)
        el = self.get_selected_element()
        el.markup = buffer_.get_text(buffer_.get_start_iter(),
                                      buffer_.get_end_iter())
        self._set_changed()
    
    def _on_image_changed(self, filechooser):
        "The user chose another image."
        el = self.get_selected_element()
        el.src = filechooser.get_filename()
        gui.update_image_preview(self._image_preview, el.src)
        self._set_changed()
    
    def _on_change_pos(self, editable):
        """Update the position on change.
        
        `pos.right` will be updated to be larger than `pos.left`. Same for
        top and bottom."""
        if self.__updating:
            return
        self.__updating = True
        el = self.get_selected_element()
        if el is False:
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
    
    def _on_change_mg(self, editable):
        "Update the margin on change."
        if self.__updating:
            return
        el = self.get_selected_element()
        if el is False: return False
        el.margin = int(editable.get_value())
        self._set_changed()
    
    def _on_change_al(self, combobox):
        "Update the alignment on change."
        if self.__updating:
            return
        el = self.get_selected_element()
        
        el.align = theme.get_align_const(combobox.get_active_text())
        self._set_changed()
    
    def _on_change_va(self, combobox):
        "Update the vertical alignment on change."
        if self.__updating:
            return
        el = self.get_selected_element()
        
        el.valign = theme.get_valign_const(combobox.get_active_text())
        self._set_changed()
    
    def _on_change_aspect(self, combobox):
        "Update the image's resize setting on change."
        if self.__updating:
            return
        el = self.get_selected_element()
        
        el.aspect = theme.get_aspect_const(combobox.get_active_text())
        self._set_changed()
    
    def get_selected_element(self):
        "Get the selected item in the list."
        model, itr = self._tree.get_selection().get_selected()
        if itr:
            return model.get_value(itr, 0)
        else:
            return False
    
    def _set_changed(self):
        "Set the slide to changed."
        self.changed = True
        if not self.get_title().startswith("*"):
            self.set_title("*%s"%self.get_title())
    
    def _add_image(self, button, tree):
        "Add an image element to the slide."
        img = theme.Image(None)
        itr = tree.get_model().append((img,))
        tree.get_selection().select_iter(itr)
        self._set_changed()
    
    def _add_text(self, button, tree):
        "Add a text element to the slide."
        txt = theme.Text('')
        itr = tree.get_model().append((txt,))
        tree.get_selection().select_iter(itr)
        self._set_changed()
    
    def _delete_row(self, button, tree):
        "Remove the selected element."
        gui.del_treeview_row(button, tree)
        self._set_changed()
    
    def _undo(self, button, buffer_):
        "Undo a text buffer change."
        if buffer_:
            buffer_.undo()
    
    def _redo(self, button, buffer_):
        "Redo a text buffer change."
        if buffer_:
            buffer_.redo()
    
    def _set_slide_row_text(self, column, cell, model, titer):
        "Returns the title of the current presentation."
        rend = model.get_value(titer, 0)
        if isinstance(rend, theme.Text):
            text = pango.parse_markup(rend.markup)[1]
            cell.set_property('text', "Text: %s" % re.sub('\s+',' ',text))
        elif isinstance(rend, theme.Image):
            if rend.src:
                text = os.path.split(rend.src)[1]
            else:
                text = "(No File Set)"
            cell.set_property('text', "Image: %s" % text)
    
    def _quit_with_save(self, event, *args):
        "The user chose to save the slide."
        if self._get_title_value() == "":
            info_dialog = gtk.MessageDialog(self,
                    gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR,
                    gtk.BUTTONS_OK, _("Please enter a Title."))
            info_dialog.run()
            info_dialog.destroy()
            self._title_entry.grab_focus()
            return False
        for itm in self._tree.get_model():
            itr = itm.iter
            if isinstance(itm[0], theme.Image) and not itm[0].src:
                info_dialog = gtk.MessageDialog(self,
                        gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR,
                        gtk.BUTTONS_OK, _("The image's source was not set."))
                info_dialog.run()
                info_dialog.destroy()
                self._tree.get_selection().select_iter(itr)
                return False
            if isinstance(itm[0], theme.Text) and not itm[0].markup:
                info_dialog = gtk.MessageDialog(self,
                        gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR,
                        gtk.BUTTONS_OK, _("The text must have a value."))
                info_dialog.run()
                info_dialog.destroy()
                self._tree.get_selection().select_iter(itr)
                return False
        self._save()
        self.destroy()
    
    def _quit_without_save(self, event, *args):
        "The user chose not to save the slide."
        if self._ok_to_continue():
            self.destroy()
    
    def _save(self):
        "Save the slide elements."
        self.slide_title = self._get_title_value()
        self.slide_content = [row[0] for row in self._tree.get_model()]
        self.changed = True
    
    def _ok_to_continue(self):
        "Let the user know that there are changes."
        if self.changed:
            msg = _('Unsaved Changes exist. Do you want to continue without saving?')
            dlg = gtk.MessageDialog(self, gtk.DIALOG_MODAL,
                    gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, msg)
            resp = dlg.run()
            dlg.destroy()
            if resp == gtk.RESPONSE_NO:
                return False
        self.changed = False
        return True

