#!/usr/bin/python
# vim: ts=4 expandtab ai:
#
# This was written to format bible texts for ExpoSong.

import re

_html_unescape_table = {
    "&quot;": '"',
    "&apos;": "'",
    "&gt;": ">",
    "&lt;": "<",
    "&amp;": "&",
    }

def verse_unescape(text):
    """Produce entities within text."""
    for html,txt in _html_unescape_table.iteritems():
        text = text.replace(html,txt)
    # Remove non-biblical texts
    text = re.sub('<note[^>]*>.*?</note[^>]*?>','',text)
    text = re.sub('<title[^>]*>.*?</title[^>]*?>','',text)

    # Respect paragraphs. We only care about adding it after a closing
    # paragraph.
    text = re.sub('</p>', '\n\n', text)

    # These are part of poetry formatting, but we might not care.
    #text = re.sub('</l>', '\n\n', text)
    #text = re.sub('<lb\\b.*\\bx-secondLine\\b[^>]*?>', '\n', text)

    ## Milestone type x-extra-p looks like a paragraph, so we will make it so
    text = re.sub('<milestone\\b.*\\bp-extra-p\\b[^>]*?>', '\n\n', text)
    # Quotes
    text = re.sub('</?q\\b[^>]*?>', '"', text)
    
    # Ignore other 
    text = re.sub('<[^>]+?>', '', text)
    return text.strip()

