#! /usr/bin/env python
#
#	Copyright (C) 2008 Fishhookweb.com
#
#	ExpoSong is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with this program.  If not, see <http://www.gnu.org/licenses/>.
#	---

"""
This provides a base class for the plugin system.
"""

class Plugin(object):
	'''
	Custom plugins should inherit from this class.
	'''
	capabilities = []
	
	def __repr__(self):
		return '<%s %r>' % (
			self.__class__.__name__,
			self.capabilities
		)
	
	def get_version():
		pass
	
	def get_description():
		return ""


def init_plugin_system(cfg):
	'Load plugins dynamically.'
	load_plugins(cfg['plugins'])
	

def load_plugins(plugins):
	'Import plugins.'
	for plugin in plugins:
		__import__("exposong.plugins."+plugin, None, None, [''])


def find_plugins():
	'Return all of the current available plugins.'
	return Plugin.__subclasses__()


def get_plugins_by_capability(classname):
	'Return all plugins that have a super-class in "_abstract.py".'
	result = []
	for plugin in Plugin.__subclasses__():
		if issubclass(plugin, classname):
			result.append(plugin)
	return result

