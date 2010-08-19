# -*- coding: utf-8 -*-
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

import openlyrics
from xml.etree import cElementTree as etree

import exposong.application
import exposong.slidelist
from exposong.glob import *
from exposong import RESOURCE_PATH, DATA_PATH
from exposong.plugins import Plugin, _abstract
from exposong.prefs import config

"""
A converter from Exposong (<= 0.6.2) Lyrics type.
"""
information = {
    'name': _("Exposong Lyrics Converter"),
    'description': __doc__,
    'required': False,
    }

class LyricConvert(_abstract.ConvertPresentation, Plugin):
  """
  Convert from Exposong (<= 0.6.2) Lyrics type to OpenLyrics.
  """
  
  @staticmethod
  def is_type(filename):
    "Should return True if this file should be converted."
    fl = open(filename, 'r')
    match = r'<presentation\b[^>]*\btype=[\'"]lyric[\'"]'
    lncnt = 0
    for ln in fl:
      if lncnt > 2:
        break
      if re.search(match, ln):
        fl.close()
        return True
      lncnt += 1
    fl.close()
    return False
  
  @staticmethod
  def convert(filename):
    "Converts the file."
    tree = etree.parse(filename)
    if isinstance(tree, etree.ElementTree):
      root = tree.getroot()
    else:
      root = tree
    
    song = openlyrics.Song()
    title = root.findall('title')
    if title:
      print "Title: %s" % title[0].text
      song.props.titles.append(openlyrics.Title(title[0].text))
    authors = root.findall('author')
    for author in authors:
      print "Author: %s" % author.text
      if author and author.text:
        song.props.authors.append(openlyrics.Author(author.text,
                                                    author.get("type")))
    copyright = root.findall('copyright')
    if copyright:
      print "Copyright %s:" % copyright[0].text
      song.props.copyright = copyright[0].text
    order = root.findall('order')
    if order:
      print "Order %s:" % order[0].text
      song.props.order = order[0].text
    slides = root.findall('slide')
    for slide in slides:
      print "Verse %s:" % slide.get("title")
      verse = openlyrics.Verse()
      verse.name = slide.get("title")
      lines = openlyrics.Lines()
      lines.lines = [openlyrics.Line(l) for l in slide.text.split('\n')]
      verse.lines = [lines]
      song.verses.append(verse)
    song.write(filename)

