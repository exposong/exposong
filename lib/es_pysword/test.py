#!/usr/bin/python
#
# vim: ts=4 expandtab ai:
##### Bible Verse testing #####
#
# Download KJV version from
# http://www.crosswire.org/sword/modules/ModDisp.jsp?modType=Bibles
# and extract it so that modules/ is in data/sword/. mods.d/ isn't required,
# but it might be used in ExpoSong.

import re
import sys
import os.path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir))

import pysword
module = pysword.ZModule("kjv")

_html_unescape_table = {
    "&quot;": '"',
    "&apos;": "'",
    "&gt;": ">",
    "&lt;": "<",
    "&amp;": "&",
    }

def verse_unescape(text):
    """Produce entities within text."""
    # TODO We might should respect the <p>
    for html,txt in _html_unescape_table.iteritems():
        text = text.replace(html,txt)
    text = re.sub('<note[^>]*>.*?</note[^>]*?>','',text)
    text = re.sub('</?w\\b[^<]*?>', '', text)
    text = re.sub('</?seg\\b[^<]*?>', '', text)
    text = re.sub('</?divineName\\b[^<]*?>', '', text)
    text = re.sub('</?transChange\\b[^<]*?>', '', text)
    ## Some milestones were of type x-extra-p, so we will replace it with a newline
    text = re.sub('<milestone\\b.*\\bp-extra-p\\b[^<]*?>', '\n', text)
    text = re.sub('<milestone\\b[^<]*?>', '', text)
    text = re.sub('</?q\\b[^<]*?>', '"', text)
    return text.strip()


for vs in module.all_verses_in_chapter("Matthew",5):
	print "%s %s:%s   %s" % (vs[0].name, vs[1], vs[2], verse_unescape(vs[3]))
	#print verse_unescape(vs[3])
	print 

print "\n\n\n"
