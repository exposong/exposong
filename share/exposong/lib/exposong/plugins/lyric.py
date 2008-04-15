#! /usr/bin/env python
import gtk
import gtk.gdk
from os.path import join
import xml.dom
import xml.dom.minidom
import pango
import re

from exposong.glob import *
from exposong import RESOURCE_PATH
from exposong.plugins import Plugin, _abstract

"""
Lyric presentations.
"""
information = {
		'name': _("Lyric Presentation"),
		'description': __doc__,
		'required': False,
}

title_re = re.compile("(chorus|refrain|verse|bridge)", re.I)


class Presentation (Plugin, _abstract.Presentation, _abstract.Menu,
		_abstract.Schedule):
	'''
	Lyric presentation type.
	'''
	class Slide (Plugin, _abstract.Presentation.Slide):
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
	
	def set_text_buffer(self, tbuf):
		'Sets the value of a text buffer.'
		it1 = tbuf.get_start_iter()
		titleTag = tbuf.create_tag("titleTag", weight=pango.WEIGHT_BOLD, background="orange")

		for sl in self.slides:
				if(hasattr(sl, 'title') and len(sl.title) > 0):
						tbuf.insert_with_tags(it1, sl.title, titleTag)
						tbuf.insert(it1, "\n")
				tbuf.insert(it1, sl.get_text())
				if(sl is not self.slides[len(self.slides)-1]):
						tbuf.insert(it1, "\n\n")

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
	
	@classmethod
	def schedule_name(cls):
		'Return the string schedule name.'
		return _('Lyric Presentations')
	
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
		return "A lyric presentation type."

