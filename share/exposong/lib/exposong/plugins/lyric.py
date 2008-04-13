#! /usr/bin/env python
import gtk
import gtk.gdk
from os.path import join
import xml.dom
import xml.dom.minidom

from exposong.glob import *
from exposong import RESOURCE_PATH
from exposong.plugins import Plugin, _abstract

"""
Lyric presentations.
"""
information = {
		'name': "Lyric Presentation",
		'description': __doc__,
		'required': False,
}


class Presentation (Plugin, _abstract.Presentation, _abstract.Menu):
	'''
	Lyric presentation type.
	'''
	
	def __init__(self, dom = None, filename = None):
		_abstract.Presentation.__init__(self, dom, filename)
		self.type = 'lyric'
	
	@staticmethod
	def get_type():
		'Return the presentation type.'
		return 'lyric'
	
	@staticmethod
	def get_icon():
		'Return the pixbuf icon.'
		return gtk.gdk.pixbuf_new_from_file(join(RESOURCE_PATH,'lyric.png'))
	
	def _set_slides(self, dom):
		'Set the slides from xml.'
		slides = dom.getElementsByTagName("slide")
		for sl in slides:
			self.slides.append(Slide(sl))
	
	def merge_menu(self, uimanager):
		'Merge new values with the uimanager.'
		factory = gtk.IconFactory()
		factory.add('exposong-lyric',gtk.IconSet(gtk.gdk.pixbuf_new_from_file(
				join(RESOURCE_PATH,'lyric.png'))))
		factory.add_default()
		gtk.stock_add([("exposong-lyric",_("_Lyric"), gtk.gdk.MOD1_MASK, 
				0, "pymserv")])
		
		actiongroup = gtk.ActionGroup('exposong-lyric')
		actiongroup.add_actions([("pres-new-lyric", 'exposong-lyric', None, None,
				None, self._on_pres_new)])
		uimanager.insert_action_group(actiongroup, -1)
		
		self.menu_merge_id = uimanager.add_ui_from_string("""
			<menubar name='MenuBar'>
				<menu action="Presentation">
						<menu action="pres-new">
							<menuitem action='pres-new-lyric' />
						</menu>
				</menu>
			</menubar>
			""")
	
	def unmerge_menu(self, uimanager):
		'Remove merged items from the menu.'
		uimanager.remove_ui(self.menu_merge_id)


class Slide (Plugin, _abstract.Slide):
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
	
	@staticmethod
	def get_version():
		'Return the version number of the plugin.'
		return (1,0)
	
	@staticmethod
	def get_description():
		'Return the description of the plugin.'
		return "A lyric presentation type."

