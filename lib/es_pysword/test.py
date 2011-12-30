#!/usr/bin/python
#
##### Bible Verse testing #####
#
# Download KJV version from
# http://www.crosswire.org/sword/modules/ModDisp.jsp?modType=Bibles
# and extract it so that modules/ is in data/sword/. mods.d/ isn't required,
# but it might be used in ExpoSong.

import sys
import os.path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir))

import pysword

## XML Tag Remove
from HTMLParser import HTMLParser

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()
## End XML Tag Remove



module = pysword.ZModule("kjv")

for vs in module.all_verses_in_book("Jude"):
	# Need to remove <note> element and text
	txt = strip_tags(vs[3])
	print "%s %s:%s   %s" % (vs[0].name, vs[1], vs[2], txt)
