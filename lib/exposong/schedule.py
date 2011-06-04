#
# vim: ts=4 sw=4 expandtab ai:
#
# Copyright (C) 2008-2010 Exposong.org
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
import os.path
from xml.etree import cElementTree as etree

from exposong import DATA_PATH
from exposong import preslist
from exposong.glob import get_node_text, check_filename
import exposong.plugins._abstract


class Schedule(gtk.ListStore):
    '''
    Schedule of presentations.
    Can be built-in (ES Presentations, Lyric Presentations) or user-defined.
    '''
    def __init__(self, title="", filename = None, builtin = True, filter_func = None):
        gtk.ListStore.__init__(self, *preslist.PresList.get_model_args())
        self.title = title
        if filename == None:
            self.filename = os.path.join(DATA_PATH, "sched")
        else:
            self.filename = filename
        self.builtin = builtin
        if builtin:
            self.get_model().set_sort_func(0, self._column_sort)
            self.get_model().set_sort_column_id(0, gtk.SORT_ASCENDING)
        else:
            if filename:
                exposong.log.info('Adding custom schedule "%s".',
                                  os.path.basename(filename))
            else:
                exposong.log.info('Adding custom schedule "%s".',
                                  title)
        self.filter_func = filter_func
    
    def load(self, dom, library):
        'Loads from an xml file.'
        self.clear()
        self.builtin = False
        self.title = get_node_text(dom.findall("title")[0])
        for presNode in dom.findall("presentation"):
            filenm = ""
            comment = ""
            
            try:
                filenm = os.path.split(get_node_text(presNode.find("file")))[1]
            except IndexError:
                exposong.log.warning('Missing filename for presentation in schedule "%s"',
                                     self.title)
                continue
            
            try:
                comment = get_node_text(presNode.find("comment"))
            except IndexError:
                pass
            
            if filenm:
                pres = library.find(filename=filenm)
                if pres:
                    gtk.ListStore.append(self, ScheduleItem(pres, comment).get_row())
                    exposong.log.info('Adding %s presentation "%s" to schedule "%s".',
                                      pres.get_type(), pres.get_title(), self.title)
                else:
                    exposong.log.warning('Missing presentation file "%s" in schedule "%s".',
                                         filenm, self.title)
            
    def save(self):
        'Write schedule to disk.'
        self.filename = check_filename(self.title, self.filename)
        root = etree.Element("schedule")
        root.attrib["created"] = "0"
        root.attrib["modified"] = "0"
        node = etree.Element("title")
        node.text = self.title
        root.append(node)
        
        itr = self.get_iter_first()
        while itr:
            item = self.get_value(itr, 0)
            
            node = etree.Element("presentation")
            node2 = etree.Element("file")
            node2.text = item.filename
            node.append(node2)
            node2 = etree.Element("comment")
            node2.text = item.comment
            node.append(node2)
            root.append(node)
            itr = self.iter_next(itr)
        dom = etree.ElementTree(root)
        dom.write(self.filename, encoding=u'UTF-8')
    
    def append(self, pres, comment = ""):
        'Add a presentation to the schedule.'
        if callable(self.filter_func) and not self.filter_func(pres):
            return False
        if not self.builtin:
            exposong.log.info('Adding %s presentation "%s" to schedule "%s".',
                              pres.get_type(), pres.get_title(), self.title)
        if isinstance(pres, ScheduleItem):
            sched = ScheduleItem(pres.presentation, comment)
        else:
            sched = ScheduleItem(pres, comment)
        gtk.ListStore.append(self, sched.get_row())
    
    def append_action(self, action):
        'Add the selected presentation to the schedule (from a Menu button).'
        model, itr = preslist.preslist.get_selection().get_selected()
        pres = model.get_value(itr, 0)
        self.append(pres)
    
    def remove(self, itr):
        'Remove a presentation from a schedule.'
        gtk.ListStore.remove(self, itr)
    
    def remove_if(self, presentation):
        'Searches and removes a presentation if it matches.'
        itr = self.get_iter_first()
        ret = False
        while itr:
            item = self.get_value(itr, 0)
            if item.presentation == presentation:
                itr2 = self.iter_next(itr)
                self.remove(itr)
                itr = itr2
                ret = True
            else:
                itr = self.iter_next(itr)
        return ret
    
    def set_model(self, model):
        'Filter all presentations.'
        gtk.ListStore = model
    
    def get_model(self):
        'Return the filtered ListModel'
        return self
    
    def is_reorderable(self):
        'Checks to see if the list should be reorderable.'
        return not self.builtin
    
    def find(self, filename):
        'Searches the schedule for the matching filename.'
        itr = self.get_iter_first()
        while itr:
            item = self.get_value(itr, 0)
            if os.path.split(item.filename)[1] == filename:
                return item.presentation
            itr = self.iter_next(itr)
    
    def resort(self):
        'Force the model to resort'
        if self.builtin:
            self.get_model().set_sort_func(0, self._column_sort)
    
    @staticmethod
    def _column_sort(treemodel, iter1, iter2):
        c1 = treemodel.get_value(iter1,0).get_title()
        c2 = treemodel.get_value(iter2,0).get_title()
        if c1 < c2:
            return -1
        if c1 > c2:
            return 1
        return 0

class ScheduleItem:
    '''
    An item for a schedule, including a presentation and a comment.
    '''
    def __init__(self, presentation, comment):
        assert(isinstance(presentation, exposong.plugins._abstract.Presentation))
        self.presentation = presentation
        self.comment = comment
    
    def __getattr__(self, name):
        'Get the attribute from the presentation if possible.'
        if hasattr(self.presentation, name):
            return getattr(self.presentation, name)
        raise AttributeError
    
    def get_row(self):
        'Get a row to put into the presentation list.'
        return (self,)
