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

"""
This class will work similarly to a plugin system. Classes will subclass from
the defined classes, and then be automatically called from other classes.

A good example is the menu. The main window will define the menu, but for code
separation, subclasses will define their own menu items.

Thanks to Armin Ronacher for plugin ideas
(http://lucumr.pocoo.org/blogarchive/python-plugin-system).
"""

### Class Definitions ###


class Menu(object):
    '''
    Subclasses of this class can modify the menu.
    '''

    @classmethod
    def merge_menu(cls, uimanager):
        'Merge new values with the uimanager.'
        raise NotImplementedError

    @classmethod
    def unmerge_menu(cls, uimanager):
        'Remove merged items from the menu.'
        raise NotImplementedError

class Toolbar(object):
    '''
    Subclasses of this class can modify the toolbar.
    '''

    @classmethod
    def merge_toolbar(cls, uimanager):
        'Merge new values with the uimanager.'
        raise NotImplementedError

    @classmethod
    def unmerge_menu(cls, uimanager):
        'Remove merged items from the toolbar.'
        raise NotImplementedError

### Internal Functions ###

def get_hooks(class_):
    'Return all classes that hook into `class_`.'
    return [plugin for plugin in class_.__subclasses__()]
