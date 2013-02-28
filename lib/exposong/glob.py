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


def element_contents(element, respect_whitespace=False):
    '''
    Get a string representation of an XML Element, excluding the tag of the
    element itself.
    '''
    s = u""
    if element.text:
        if not respect_whitespace:
            s += re.sub('\s+', ' ', element.text)
        else:
            s += element.text
    for sub in element.getchildren():
        # Strip the namespace
        if sub.tag.partition("}")[2]:
            tag = sub.tag.partition("}")[2]
        else:
            tag = sub.tag
        subtag = ' '.join((tag,) + tuple('%s="%s"' % i for i in sub.items()))
        subtext = element_contents(sub, respect_whitespace)
        if subtext:
            s += '<%(tag)s>%(text)s</%(tag)s>' % \
                    {"tag": subtag, 'text': subtext}
        else:
            s += "<%(tag)s />" % {'tag': subtag}
        if sub.tail:
            if not respect_whitespace:
                s += re.sub('\s+', ' ', sub.tail)
            else:
                s += sub.tail
    return unicode(s.strip())

def get_node_text(element, respect_whitespace=False):
    'Returns the text of a node (ElementTree.Element Object)'
    if(isinstance(element, str)):
        return element
    if not element.text:
        return ''
    if respect_whitespace == 2:
        return element.text
    if respect_whitespace:
        # Leave whitespace in the middle alone.
        return element.text.strip()
    return re.sub('\s+', ' ', element.text.strip())

def title_to_filename(title):
    """
    Returns a filename with chars removed which are not allowed as filename
    http://en.wikipedia.org/wiki/File_name#Reserved_characters_and_words
    """
    filename = ""
    for char in title:
        if char not in "\/:<>\"|?*%+":
            filename += char
    
    return filename

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
    root, ext = os.path.splitext(filename)
    n = ''
    while os.path.exists("".join([root, n, ext])):
        try:
            n = str(int(n)-1)
        except ValueError:
            #The first time, it will be an empty string, so set it manually.
            n = "-1"
    return "".join([root, n, ext])


def random_string(length):
    "Return a random string with `lenght` characters"
    chars = string.ascii_letters + string.digits
    p = ""
    for i in range(length):
        p += random.choice(chars)
    return p

#TODO Have the ability to list multiple directories with one function call to
# allow the user to have data in more than one place.
