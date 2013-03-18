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

from gi.repository import Gtk
import os.path
from xml.etree import cElementTree as etree

from exposong import DATA_PATH
from exposong import preslist
from exposong.glob import get_node_text, check_filename
import exposong.plugins._abstract


class Schedule:
    '''
    Schedule of presentations.
    Can be built-in or user-defined.
    '''
    def __init__(self, title="", filename = None, builtin = True, model = None):
        'Initialize the Schedule.'
        self.title = title
        if model == None:
            self._model = Gtk.ListStore(*preslist.PresList.get_model_args())
        else:
            self._model = model
        
        if filename == None:
            self.filename = os.path.join(DATA_PATH, "sched")
        else:
            self.filename = filename

        self._model.builtin = builtin
        if builtin:
            mod = self.get_model(True)
            mod.set_sort_func(0, self._column_sort)
            mod.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        else:
            if filename:
                exposong.log.info('Adding custom schedule "%s".',
                                  os.path.basename(filename))
            else:
                exposong.log.info('Adding custom schedule "%s".',
                                  title)
    
    def load(self, dom, library):
        'Loads from an xml file.'
        self.clear()
        self._model.builtin = False
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
                    self.get_model(True).append(ScheduleItem(pres, comment).get_row())
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
        if not self.is_builtin():
            exposong.log.info('Adding %s presentation "%s" to schedule "%s".',
                              pres.get_type(), pres.get_title(), self.title)
        if isinstance(pres, ScheduleItem):
            sched = ScheduleItem(pres.presentation, comment)
        else:
            sched = ScheduleItem(pres, comment)
        self.get_model(True).append(sched.get_row())
    
    def append_action(self, action):
        'Add the selected presentation to the schedule (from a Menu button).'
        model, itr = preslist.preslist.get_selection().get_selected()
        pres = model.get_value(itr, 0)
        self.append(pres)
    
    def remove(self, itr):
        'Remove a presentation from a schedule.'
        self.get_model(True).remove(itr)
    
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
    
    def get_model(self, getliststore=False):
        'Return the filtered ListModel'
        mod = self._model
        if getliststore and not isinstance(mod, Gtk.ListStore):
            mod = mod.get_model()
        return mod
    
    def is_builtin(self):
        return self._model.builtin
    
    def is_reorderable(self):
        'Checks to see if the list should be reorderable.'
        return not self.is_builtin()
    
    def find(self, filename):
        'Searches the schedule for the matching filename.'
        itr = self.get_iter_first()
        while itr:
            item = self.get_value(itr, 0)
            if os.path.basename(item.filename) == filename:
                return item.presentation
            itr = self.iter_next(itr)
    
    def finditer(self, filename):
        'Searches the schedule for the matching filename.'
        itr = self.get_iter_first()
        while itr:
            item = self.get_value(itr, 0)
            if os.path.basename(item.filename) == filename:
                return itr
            itr = self.iter_next(itr)
    
    def resort(self):
        'Force the model to resort'
        if self.is_builtin():
            self.get_model(True).set_sort_func(0, self._column_sort)
    
    @staticmethod
    def _column_sort(treemodel, iter1, iter2):
        c1 = treemodel.get_value(iter1,0).get_title()
        c2 = treemodel.get_value(iter2,0).get_title()
        if c1 < c2:
            return -1
        if c1 > c2:
            return 1
        return 0
    
    #Call model functions
    def __getattr__(self, name):
        'Get the attribute from the model if possible.'
        if hasattr(self._model, name):
            return getattr(self._model, name)
        if isinstance(self._model, Gtk.TreeModelFilter):
            if hasattr(self._model.get_model(), name):
                return getattr(self._model.get_model(), name)

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
