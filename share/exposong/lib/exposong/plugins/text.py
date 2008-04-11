#! /usr/bin/env python
import gtk
from os.path import join

from exposong import RESOURCE_PATH
from exposong.plugins import Plugin, _abstract

"""
Plain text presentations.
"""
information = {
		'name': "Text Presentation",
		'description': __doc__,
		'required': False,
}

class Presentation (Plugin, _abstract.Presentation, _abstract.Slide):
	'''
	Text presentation type.
	'''
	
	def __init__(self, dom = None, filename = None):
		_abstract.Presentation.__init__(self, dom, filename)
		self.type = "text"
	
	def merge_menu(self, uimanager):
		'Merge new values with the uimanager.'
		factory = gtk.IconFactory()
		factory.add('exposong-text',gtk.IconSet(gtk.gdk.pixbuf_new_from_file(
				join(RESOURCE_PATH,'generic.png'))))
		gtk.stock_add(("exposong-text",_("Text"), None, None, None))
		
		actiongroup = gtk.ActionGroup()
		actiongroup.add_actions(("pres-new-text", 'exposong-text'))
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

