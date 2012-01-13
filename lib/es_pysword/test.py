#!/usr/bin/python
#
# vim: ts=4 expandtab ai:
##### Bible Verse testing #####
#
# Download KJV version from
# http://www.crosswire.org/sword/modules/ModDisp.jsp?modType=Bibles
# and extract it so that modules/ is in data/sword/. mods.d/ isn't required,
# but it might be used in ExpoSong.

import sys
import os.path

import vformat

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir))

import pysword
module = pysword.ZModule("kjv")

def test_verse_retrieve():
    chapter = ""
    for vs in module.all_verses_in_book("Genesis"):
        if vs[1] != chapter:
            chapter = vs[1]
            print vs[1]
    	x = ( "%s %s:%s   %s" % (vs[0].name, vs[1], vs[2], vformat.verse_unescape(vs[3])))
    #print "\n\n".join(vss)
    #print "\n\n\n"

def test_book_gen():
    print "\n".join(repr(m) for m in module)

test_verse_retrieve()
