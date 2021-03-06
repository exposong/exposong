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
import gtk.gdk
import re
from xml.etree import cElementTree as etree

from exposong.glob import *
from exposong import theme
import exposong.main
import exposong.schedlist
import exposong.presfilter

'''
Abstract classes that create plugin functionality.

These classes should not be referrenced, with the exception of `Slide`.
'''

# Abstract functions should use the following:
# `raise NotImplementedError`


class Presentation:
    '''
    A presentation type to store the text or data for a presentation.
    
    Requires at minimum a title and slides.
    '''
    class Slide:
        '''
        A plain text slide.
    
        Reimplementing this class is optional.
        '''
        pres = None
        id = None
        title = ''
        text = ''
        def __init__(self, pres, value=None):
            pass
        
        def get_title(self, editing=False):
            'Get the title for the slide'
            return self.title
        
        def get_text(self):
            'Get the text for the slide.'
            return self.text
        
        def get_markup(self, editing=False):
            'Get the text for the slide selection.'
            if self.title:
                return "<b>" + self.get_title(editing) + "</b>\n" + self.get_text()
            else:
                return self.get_text()
        
        def get_slide(self):
            '''A list of full screen renderable theme items.
            
            Voids get_body and get_footer from being called.'''
            return NotImplemented
            
        
        def get_body(self):
            'Return a list of renderable theme items.'
            return [theme.Text(self.get_text(), margin=0.04)]
        
        def get_footer(self):
            'Return a list of renderable theme items.'
            return []
        
        def to_node(self, node):
            'Populate the node element'
            raise NotImplementedError
        
        def set_attributes(self, layout):
            'Set attributes on a pango.Layout object.'
            return NotImplemented
        
        def header_text(self):
            'Draw on the header.'
            return NotImplemented
        
        def footer_text(self):
            'Draw text on the footer.'
            return NotImplemented
        
        def body_text(self):
            'Draw text in the center of the screen.'
            return self.get_text()
        
        def get_theme(self):
            'Return the theme for this slide.'
            return None
        
        def copy(self):
            'Create a duplicate of the slide.'
            slide = self.__class__(self.pres)
            slide.text = self.text
            slide.title = self.title
            slide._set_id()
            return slide
            
        def _set_id(self, value = None):
            if etree.iselement(value):
                self.id = value.get("id")
            if not self.id:
                if self.title:
                    self.id = "%s_%s" % (str(self.get_title()).replace(" ","").lower(),
                                         random_string(8))
                else:
                    self.id = random_string(8)
    
    filename = None
    
    def __init__(self, filename=''):
        self._title = ''
        self.slides = []
        if self.__class__ is Presentation:
            raise NotImplementedError("This class cannot be instantiated.")
    
    @classmethod
    def is_type(cls, fl):
        "Test to see if this file is the correct type."
        return False
    
    @staticmethod
    def get_type_name():
        'Return the presentation type name.'
        raise NotImplementedError
    
    @staticmethod
    def get_type():
        'Return the presentation type.'
        raise NotImplementedError
    
    @staticmethod
    def get_icon():
        'Return the pixbuf icon.'
        raise NotImplementedError
    
    @staticmethod
    def pres_weight():
        "Return the presentation type."
        return 100
    
    @staticmethod
    def get_edit_dialog_title():
        return _("New Presentation")
    
    def slide_column(self, col):
        'Sets the column for slidelist.'
        col.clear()
        text_cr = gtk.CellRendererText()
        col.pack_start(text_cr, False)
        col.add_attribute(text_cr, 'markup', 1)
    
    def get_row(self):
        'Gets the data to add to the presentation list.'
        return (self, self.get_title())
    
    def get_title(self):
        'Get the presentation title.'
        return self._title
    
    def get_order(self):
        'Returns the order in which the slides should be presented.'
        order = []
        cnt = 0
        for slide in self.slides:
            order.append(cnt)
            cnt += 1
        return order

    def get_slide_from_order(self, order_value):
        'Gets the slide index.'
        return int(order_value)

    def matches(self, word):
        'Tests to see if a word is in the presentation.'
        if exposong.presfilter.matches(word, self.get_title()):
            exposong.log.debug("Matches presentation title")
            return True
        for s in self.slides:
            if exposong.presfilter.matches(word, s.get_title()):
                exposong.log.debug("Matches slide title")
                return True
            if exposong.presfilter.matches(word, s.get_text()):
                exposong.log.debug("Matches slide text")
                return True
        return False
    
    def edit(self):
        'Run the edit edit_dialog for the presentation.'
        # TODO Slides need to be deep copied so that "Cancel" actually works.
        edit_dialog = gtk.Dialog(_("New Presentation"), exposong.main.main,
                                 gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                 (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                 gtk.STOCK_SAVE, gtk.RESPONSE_ACCEPT))
        edit_dialog.set_default_size(500, 500)
        if(self.get_title()):
            edit_dialog.set_title(_('Editing "%s"') % self.get_title())
        else:
            edit_dialog.set_title(self.get_edit_dialog_title())
        notebook = gtk.Notebook()
        edit_dialog.vbox.pack_start(notebook, True, True, 6)
        
        self._fields = dict()
        
        self._edit_tabs(notebook, edit_dialog)
        
        notebook.show_all()
        
        while True:
            if edit_dialog.run() == gtk.RESPONSE_ACCEPT:
                if self._is_editing_complete(edit_dialog):
                    self._edit_save()
                    self.to_xml()
                    del(self._fields)
                    edit_dialog.destroy()
                    if not self.filename:
                        msg = 'Adding new %s presentation "%s".'
                    else:
                        msg = 'Edited %s presentation "%s".'
                    exposong.log.info(msg, self.get_type(), self.get_title())
                    return True
            else:
                msg = _('Are you sure you want to cancel?')
                dialog = gtk.MessageDialog(edit_dialog, gtk.DIALOG_MODAL,
                                           gtk.MESSAGE_WARNING, gtk.BUTTONS_YES_NO,
                                           msg)
                dialog.set_title( _("Cancel?") )
                resp = dialog.run()
                dialog.destroy()
                if resp == gtk.RESPONSE_YES:
                    del(self._fields)
                    edit_dialog.destroy()  
                    return False
    
    def _edit_tabs(self, notebook, parent):
        'Tabs for the dialog.'
        # TODO: Presentation specific themes.
        pass
    
    def _edit_save(self):
        'Save the fields if the user clicks ok.'
        ## TODO: When renaming, preslist does not resort. The following doesn't work for me.
        for schedlistrow in exposong.schedlist.schedlist.get_model():
            if schedlistrow[0] and schedlistrow[0].builtin:
                schedlistrow[0].resort()
    
    def _is_editing_complete(self, parent):
        "Test to see if all fields have been filled which are required."
        return True
    
    def to_xml(self):
        'Save the data to disk.'
        raise NotImplementedError
    
    def get_slide_list(self, editing=False):
        'Get the slide list.'
        return tuple( (sl, sl.get_markup(editing)) for sl in self.slides)
    
    def get_order_string(self):
        return ""
    
    def get_timer(self):
        'Return the time until we skip to the next slide.'
        return None
    
    def is_timer_looped(self):
        'If this is True, go to the beginning when the timer reaches the end.'
        return False
    
    def get_print_markup(self):
        "Return the presentation markup for printing."
        return NotImplemented
    
    def can_print(self):
        "Return True if printing is available."
        return False
    
    @classmethod
    def _on_pres_new(cls, action):
        "Called when a new presentation was created"
        pres = cls()
        if pres.edit():
            #Add presentation to appropriate builtin schedules
            sched = exposong.schedlist.schedlist.get_active_item()
            if not sched:
                pass
            elif sched.builtin and sched.title != cls.schedule_name():
                # Select the schedule for the presentation type
                for s2 in exposong.schedlist.schedlist.get_model():
                    if s2[0] and s2[0].title == cls.schedule_name():
                        exposong.schedlist.schedlist.get_selection().select_iter(s2.iter)
                        break
            elif not sched.builtin:
                sched.append(pres)
                
            exposong.main.main.library.append(pres)
    
    def on_delete(self):
        'Called when the presentation is deleted.'
        pass

    def on_select(self):
        'Called when the presentation is focused.'
        pass

    def on_deselect(self):
        'Called when the presentation is blurred.'
        pass

class ConvertPresentation:
    """
    A plugin that converts from a legacy format to a new format
    """
    def __init__(self):
        # This class should not be instantiated.
        return NotImplemented
    
    @staticmethod
    def is_type(filename):
        'Should return True if this file should be converted.'
        # Should be defined in subclass
        raise NotImplementedError
    
    @staticmethod
    def convert(filename):
        "Converts the file."
        return NotImplemented


class Schedule:
    '''
    Hooks to add built-in schedules.
    '''
    @classmethod
    def schedule_name(cls):
        'Return the string schedule name.'
        raise NotImplementedError
    
    @classmethod
    def schedule_filter(cls, model, itr):
        "Called on each presentation, and return True if it can be added."
        if model.get_value(itr, 0) != None:
            return model.get_value(itr, 0).presentation.__class__ is cls
        return False


class Screen:
    '''
    Hooks into the presentation screen.
    '''
    def draw(self, surface, priority=1):
        'Draw anywhere on the screen.'
        return NotImplemented

class WrongPresentationType(ValueError):
    '''
    The file read was not a valid file for this type.
    '''
    pass
