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

import gtk

import exposong._hook
from exposong import RESOURCE_PATH, DATA_PATH
from exposong import gui, theme
from exposong.glob import *
from exposong.plugins import Plugin, _abstract

"""
Bible Slide Presentations.
"""
information = {
        'name': _("Bible Verses"),
        'description': __doc__,
        'required': False,
}
type_icon = gtk.gdk.pixbuf_new_from_file_at_size(
        os.path.join(RESOURCE_PATH, 'icons', 'pres-bible.png'), 20, 14)

class Presentation (Plugin, _abstract.Presentation,
                    _abstract.Schedule):
    """
    Bible Slide Presentations.
    """
    
    class Slide (Plugin, _abstract.Presentation.Slide):
        """
        Bible verse slide.
        """
        def __init__(self, pres, verse='', text=''):
            self.pres = pres
            self.verse = verse
            self.text = text
        
        def get_body(self):
            return self.text
        
        def get_footer(self):
            # TODO Version and Copyright
            return self.verse
    
    def __init__(self, verses=''):
        self.verses = verses
    
    @classmethod
    def is_type(cls, fl):
        "Test to see if this file is the correct type."
        return False
    
    @staticmethod
    def get_type_name():
        return information['name']
    
    @staticmethod
    def get_type():
        "Return the presentation type."
        return 'bible'
    
    @staticmethod
    def get_icon():
        "Return the pixbuf icon."
        return type_icon
    
    @staticmethod
    def pres_weight():
        "Return the presentation type."
        return 30
    
    @classmethod
    def schedule_name(cls):
        "Return the string schedule name."
        return _('Bible Verses')


