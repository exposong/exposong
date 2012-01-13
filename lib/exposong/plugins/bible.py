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
from exposong import gui, theme, splash
from exposong.glob import *
from exposong.plugins import Plugin, _abstract

from es_pysword import pysword, vformat

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

#TODO Move to preferences
bible = pysword.ZModule("kjv")


class Presentation (Plugin, _abstract.Presentation,
                    _abstract.Schedule, exposong._hook.LoadPres):
    """
    Bible Slide Presentations.
    """
    
    class Slide (Plugin, _abstract.Presentation.Slide):
        """
        Bible verse slide.
        """
        def __init__(self, pres, verse='', text=''):
            self.pres = pres
            self.title = verse
            self.text = text
        
        def get_body(self):
            return [theme.Text(self.text, align=theme.CENTER,
                    valign=theme.MIDDLE, margin=0.02)]
        
        def get_footer(self):
            return [theme.Text(self.footer_text(), align=theme.CENTER, 
                    valign=theme.MIDDLE, margin=0.02)]
        
        def footer_text(self):
            # TODO Version and Copyright
            return self.title
    
    def __init__(self, verses=''):
        _abstract.Presentation.__init__(self)
        self._title = verses
    
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
    
    @classmethod
    def load_presentations(cls):
        'Load presentations into the library.'
        # This takes a while, so I limit it to 5 books and verses for now.
        exposong.log.info("Loading Bible presentations")
        splash.splash.incr_total(66)
        for book in bible.books():
            pres = cls(book.name)
            x = 0
            for vs in bible.all_verses_in_book(book):
                x += 1
                pres.slides.append(pres.Slide(pres,
                                              "{0.name} {1}:{2}".format(*vs),
                                              vformat.verse_unescape(vs[3])))
                if x > 2: break
            splash.splash.incr(1)
            yield pres

