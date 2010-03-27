#! /usr/bin/env python
#
# Copyright (C) 2008 Fishhookweb.com
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
import re
import os
import os.path
import random, string

"""
Some basic functions that are useful.

This file contains some miscellaneous functions that are useful to all parts of
the program. May contain certain variables as well.
"""

def get_node_text(node):
  'Returns the text of a node (XML DOM Object)'
  if(isinstance(node, str)):
    return node
  rc = ""
  for child in node.childNodes:
    if child.nodeType == node.TEXT_NODE:
      rc = rc + child.data.strip()
  return rc
  
def title_to_filename(title):
  'Returns a filename with letters and underscores only.'
  #TODO May need to translate foreign characters to english, or allow
  # foreign characters in the filename.
  new = ""
  for char in title:
    if char.isalnum():
      new += char.lower()
    elif not new.endswith("_") and char not in "'\",.?":
      new += "_"
  
  return new

def check_filename(title, directory, filename = None):
  '''Gets a filename that is not being used.
  
  If a cur_name is supplied, it checks to see if it
  matches the current filename, or if not, deletes the
  file and returns the new filename.'''
  tfile = title_to_filename(title)
  match = "^"+re.escape(tfile)+"(-[0-9]+)?.xml$"
  if not isinstance(filename, str) or not re.match(match, filename):
    if(filename):
      os.remove(os.path.join(directory, filename))
    filename = find_freefile(tfile+".xml")
  return filename

def find_freefile(fl):
  """Find an open filename.
  
  This makes sure the file doesn't exist, and if it does, add a -1, or -2,
  until the file won't overwrite an existing file. Needs changes to work with
  extensions such as ".tar.gz" which have multiple periods."""
  fl = fl.rpartition(".")
  fl = [fl[0], "", "."+fl[2]]
  if fl[0] == "":
    #If there's not a dot, just add a number to the end.
    fl = [fl[2][1:], "", ""]
  while os.path.exists("".join(fl)):
    try:
      fl[1] = str(int(fl[1])-1)
    except ValueError:
      #The first time, it will be an empty string, so set it manually.
      fl[1] = "-1"
  return "".join(fl)

def random_string(len):
  chars = string.ascii_letters + string.digits
  p = ""
  for i in range(len):
    p += random.choice(chars)
  return p

#TODO Have the ability to list multiple directories with one function call to
# allow the user to have data in more than one place.
