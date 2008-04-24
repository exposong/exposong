#! /usr/bin/env python
import gtk
import gtk.gdk
from os.path import join
import xml.dom
import xml.dom.minidom

from exposong.glob import *
from exposong import RESOURCE_PATH
from exposong.plugins import Plugin, _abstract
import exposong.application

"""
Plain text presentations.
"""
information = {
    'name': _("Text Presentation"),
    'description': __doc__,
    'required': False,
}


class Presentation (Plugin, _abstract.Presentation, _abstract.Menu,
    _abstract.Schedule):
  '''
  Text presentation type.
  '''
  
  def __init__(self, dom = None, filename = None):
    _abstract.Presentation.__init__(self, dom, filename)
    self.type = "text"
  
  
  
  def edit(self):
    'Run the edit dialog for the presentation.'
    dialog = gtk.Dialog(_("New Presentation"), exposong.application.main, gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT, gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
    if(self.title):
      dialog.set_title(_("Editing %s") % self.title)
    else:
      dialog.set_title(_("New %s Presentation") % self.type.title())
    notebook = gtk.Notebook()
    dialog.vbox.pack_start(notebook, True, True, 6)
    
    vbox = gtk.VBox()
    vbox.set_border_width(4)
    vbox.set_spacing(7)
    hbox = gtk.HBox()
    
    label = gtk.Label(_("Title:"))
    label.set_alignment(0.5, 0.5)
    hbox.pack_start(label, False, True, 5)
    title = gtk.Entry(45)
    title.set_text(self.title)
    hbox.pack_start(title, True, True)
    
    vbox.pack_start(hbox, False, True)
    
    text = gtk.TextView()
    text.set_wrap_mode(gtk.WRAP_WORD)
    self.set_text_buffer(text.get_buffer())
    text_scroll = gtk.ScrolledWindow()
    text_scroll.add(text)
    text_scroll.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
    text_scroll.set_size_request(300, 200)
    vbox.pack_start(text_scroll, True, True)
    notebook.append_page(vbox, gtk.Label(_("Edit")))
    
    notebook.show_all()
    
    if(dialog.run() == gtk.RESPONSE_ACCEPT):
      bounds = text.get_buffer().get_bounds()
      self.title = title.get_text()
      sval = text.get_buffer().get_text(bounds[0], bounds[1])
      self.slides = []
      for sl in sval.split("\n\n"):
        self.slides.append(self.Slide(sl))
      self.to_xml()
      
      dialog.hide()
      return True
    else:
      dialog.hide()
      return False
  
  @staticmethod
  def get_type():
    'Return the presentation type.'
    return 'text'
  
  @staticmethod
  def get_icon():
    'Return the pixbuf icon.'
    return gtk.gdk.pixbuf_new_from_file(join(RESOURCE_PATH,'text.png'))
  
  def merge_menu(self, uimanager):
    'Merge new values with the uimanager.'
    factory = gtk.IconFactory()
    factory.add('exposong-text',gtk.IconSet(gtk.gdk.pixbuf_new_from_file(
        join(RESOURCE_PATH,'text.png'))))
    factory.add_default()
    gtk.stock_add([("exposong-text",_("_Text"), gtk.gdk.MOD1_MASK, 
        0, "pymserv")])
    
    actiongroup = gtk.ActionGroup('exposong-text')
    actiongroup.add_actions([("pres-new-text", 'exposong-text', None, None,
        None, self._on_pres_new)])
    uimanager.insert_action_group(actiongroup, -1)
    
    self.menu_merge_id = uimanager.add_ui_from_string("""
      <menubar name='MenuBar'>
        <menu action="Presentation">
            <menu action="pres-new">
              <menuitem action='pres-new-text' />
            </menu>
        </menu>
      </menubar>
      """)
  
  def unmerge_menu(self, uimanager):
    'Remove merged items from the menu.'
    uimanager.remove_ui(self.menu_merge_id)
  
  @classmethod
  def schedule_name(cls):
    'Return the string schedule name.'
    return _('Text Presentations')
  
  @classmethod
  def schedule_filter(cls, pres):
    'Called on each presentation, and return True if it can be added.'
    return isinstance(pres, cls)
  
  @staticmethod
  def get_version():
    'Return the version number of the plugin.'
    return (1,0)
  
  @staticmethod
  def get_description():
    'Return the description of the plugin.'
    return "A text presentation type."

