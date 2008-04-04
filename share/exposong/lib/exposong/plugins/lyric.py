#! /usr/bin/env python
import gtk
from os.path import join

from exposong import RESOURCE_PATH
from exposong.plugins import ptype

"""
Lyric presentations.
"""
information = {
		'name': "Lyric Presentation",
		'description': __doc__,
		'required': False,
}


class Presentation (ptype.Presentation):
	'''
	Lyric presentation type.
	'''
	capabilities = ptype.Presentation.capabilities + ['menu']
	
	def __init__(self, dom = None, filename = None):
		ptype.Presentation.__init__(self, dom, filename)
		self.type = 'lyric'
	
	def _set_slides(self, dom):
		'Set the slides from xml.'
		slides = dom.getElementsByTagName("slide")
		for sl in slides:
			self.slides.append(Slide(sl))
	
	def merge_menu(self, uimanager):
		factory = gtk.IconFactory()
		factory.add('exposong-lyric',gtk.IconSet(gtk.gdk.pixbuf_new_from_file(
				join(RESOURCE_PATH,'lyric.png')))
		gtk.stock_add(("exposong-lyric",_("Lyric"), None, None, None))
		
		actiongroup = gtk.ActionGroup()
		actiongroup.add_actions(("pres-new-lyric", 'exposong-lyric'))
		uimanager.insert_action_group(actiongroup, -1)
		
		uimanager.add_ui_from_string("""
			<menubar name='MenuBar'>
				<menu action="Presentation">
						<menu action="pres-new">
							<menuitem action='pres-new-lyric' />
						</menu>
				</menu>
			</menubar>
			""")

class Slide (ptype.Slide):
	'''
	A lyric slide for the presentation.
	'''
	def __init__(self, value):
		if(isinstance(value, xml.dom.Node)):
			self.text = get_node_text(value)
			self.title = value.getAttribute("title")
		elif(isinstance(value, str)):
			value = value.strip()
			if(title_re.match(value, endpos=30)):
				(self.title, self.text) = value.split("\n", 1)
			else:
				self.title = ''
				self.text = value

