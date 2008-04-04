#! /usr/bin/env python
import gtk
from os.path import join

from exposong import RESOURCE_PATH
from exposong.plugins import ptype

"""
Plain text presentations.
"""
information = {
		'name': "Text Presentation",
		'description': __doc__,
		'required': False,
}

class Presentation (ptype.Presentation):
	'''
	Text presentation type.
	'''
	capabilities = ptype.Presentation.capabilities + ['menu']
	
	def __init__(self, dom = None, filename = None):
		ptype.Presentation.__init__(self, dom, filename)
		self.type = "text"
	
	def merge_menu(self, uimanager):
		factory = gtk.IconFactory()
		factory.add('exposong-text',gtk.IconSet(gtk.gdk.pixbuf_new_from_file(
				join(RESOURCE_PATH,'generic.png'))))
		gtk.stock_add(("exposong-text",_("Text"), None, None, None))
		
		actiongroup = gtk.ActionGroup()
		actiongroup.add_actions(("pres-new-text", 'exposong-text'))
		uimanager.insert_action_group(actiongroup, -1)
		
		uimanager.add_ui_from_string("""
			<menubar name='MenuBar'>
				<menu action="Presentation">
						<menu action="pres-new">
							<menuitem action='pres-new-text' />
						</menu>
				</menu>
			</menubar>
			""")

