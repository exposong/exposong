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

"""
This provides a base class for the plugin system.

Thanks to Armin Ronacher for writing most of this code
(http://lucumr.pocoo.org/blogarchive/python-plugin-system).
"""

import os
import sys


class Plugin(object):
    '''
    Custom plugins should inherit from this class.
    '''
    
    @staticmethod
    def get_version():
        '''Return the version number of the plugin.
        Should be in tuple format (e.g. (1,0) for 1.0)'''
        raise NotImplementedError
    
    @staticmethod
    def get_description():
        'Return the description of the plugin.'
        raise NotImplementedError


def init_plugin_system(plugins):
    'Load plugins dynamically.'
    load_plugins()

def load_plugins():
    'Import plugins.'
    if not hasattr(sys, "frozen"):
        for plugin in __all__:
            __import__("exposong.plugins."+plugin, None, None, [''])

def find_plugins():
    'Return all of the current available plugins.'
    return Plugin.__subclasses__()

def get_plugins_by_capability(klass):
    'Return all plugins that inherit from `klass`.'
    result = []
    for plugin in Plugin.__subclasses__():
        if issubclass(plugin, klass):
            result.append(plugin)
    return result


# Have to put this below so that Plugin is defined.

# TODO This is not as automated as it was before, so it needs to be fixed to
# work with cx_Freeze.
if hasattr(sys, "frozen"):
    import exposong.plugins.export_import
    import exposong.plugins.lyric
    import exposong.plugins.pres
    import exposong.plugins.legacy_format_convert
    import exposong.plugins.opensong_convert
    import exposong.plugins.songselect_convert
    __all__ = ["export_import","lyric","pres",
               "legacy_format_convert","opensong_convert","songselect_convert"]
else:
    __all__ = [fnm[:-3] for fnm in os.listdir(__path__[0])
               if fnm.endswith(".py") and not fnm.startswith("_")]
