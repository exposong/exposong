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

import re
import os
import os.path
import random
import string
import unicodedata

"""
Some basic functions that are useful.

This file contains some miscellaneous functions that are useful to all parts of
the program. May contain certain variables as well.
"""

def get_node_text(node, respect_whitespace=False):
    'Returns the text of a node (XML DOM Object)'
    if(isinstance(node, str)):
        return node
    rc = []
    for child in node.childNodes:
        if child.nodeType == node.TEXT_NODE:
            rc.append(child.data)
    if respect_whitespace:
        return "".join(rc).strip()
    else:
        return re.sub('\s+',' ',"".join(rc).strip())
    
def title_to_filename(title):
    """
    Returns a filename with letters and underscores only.
    Non-ascii-characters are translated to its ascii-equivalent
    """
    title = unicodedata.normalize('NFD', unicode(title)).encode('ascii', 'ignore')
    
    new = ""
    for char in title:
        if char.isalnum():
            new += char
        elif not new.endswith("_") and char not in "'\",.?":
            new += "_"
            
    return new

def check_filename(title, filepath):
    '''
    Checks title to match with file.
    Deletes file if not and returns the new filename
    If filepath is a directory, it will return the complete filepath
    '''
    title_filename = title_to_filename(title)

    if title_filename == os.path.basename(filepath):
        return filepath
    elif os.path.isdir(filepath):
        new_path = os.path.join(filepath, find_freefile(title_filename))
    elif os.path.isfile(filepath): #title does not match
        os.remove(filepath)
        new_path = os.path.join(os.path.dirname(filepath),
                                find_freefile(title_filename))
    else:
        raise ValueError('Could not find file "%s"' % filepath)

    if not new_path.endswith(".xml"):
        new_path += ".xml"

    return new_path 

def find_freefile(filename):
    """
    Find an open filename.
    
    This makes sure the file doesn't exist, and if it does, add a -1, or -2,
    until the file won't overwrite an existing file. Needs changes to work with
    extensions such as ".tar.gz" which have multiple periods.
    """
    root,ext = os.path.splitext(filename)
    n = ''
    while os.path.exists("".join([root,n,ext])):
        try:
            n = str(int(n)-1)
        except ValueError:
            #The first time, it will be an empty string, so set it manually.
            n = "-1"
    return "".join([root,n,ext])

def random_string(len):
    chars = string.ascii_letters + string.digits
    p = ""
    for i in range(len):
        p += random.choice(chars)
    return p

#TODO Have the ability to list multiple directories with one function call to
# allow the user to have data in more than one place.
