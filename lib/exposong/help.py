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

import os
import webbrowser
import tempfile
from urllib import pathname2url

from exposong import RESOURCE_PATH

def open():
    all = _header() + _about() + _schedules() + _presentations() +\
            _notifications() + _backgrounds() + _shortcuts_table()
    tmp = tempfile.NamedTemporaryFile()
    tmp.write(all)
    tmp.flush()
    webbrowser.open("file:"+pathname2url(tmp.name))
    

def _header():
    header = """<head>
<title>%(title)s</title>
<link rel='stylesheet' href='%(stylepath)s' content='text/css'>
</head>
<body>
<div id='header'>
<h2><img src='%(headerimg)s' alt='' /></h2>
</div>
<div id='content'>"""%\
            {'title'       : _('ExpoSong Help'),
            'stylepath'   : os.path.join(RESOURCE_PATH, 'style.css'),
            'headerimg' : os.path.join(RESOURCE_PATH, 'exposong.png')}
    return header

def _about():
    about = _h(_('About')) +\
            _p(_('ExpoSong is a free, open-source, presentation \
program to assist with worship assemblies. Create lyrics or plain-text slides, \
create schedules, and put up slides on the screen.'))
    return about

def _schedules():
    schedules = _h(_('Schedules')) +\
            _p(_('Schedules are used to create an order of presentations.')) +\
            _p(_('To create a schedule, in the menu, select Schedule-&gt;\
New. Name your schedule, according to the date or event. Add songs to the \
schedule by dragging them from the library onto the schedule.'))
    return schedules

def _presentations():
    presentations = _h(_('Creating Presentations')) +\
            _p(_('Presentations are a set of slides to be presented on the screen. \
To create a new presentation, on the menu, select Presentation-&gt;New, and \
then the appropriate presentation type.')) +\
            _p(_('Add, edit, or delete slides using the toolbar buttons. \
You can drag and drop slides to reorder the slides.')) +\
            _p(_('The <b>text</b> presentation is used to create a non-specific, \
text slide. It can be used for sermons, announcements, or anything else.')) +\
            _p(_('The <b>lyric</b> presentation is for song lyrics. It contains \
slide descriptors, such as "Verse #", "Chorus", "Bridge", or "Refrain", which are \
for the benefit of the presenter. There are some information tabs, and some of \
the data from this area, like author, songbook number, copyright and ccli \
number, are displayed on the bottom of the presentation screen.')) +\
            _p(_('Lyric presentations can also be reordered. Use the verse \
names in brackets and enter them in the order you wish to have in the "Order" \
field, for example: "v1 c v2 b c e"')) +\
            _p(_('The <b>image</b> presentation is used to present images. \
Add multiple images at once by using [shift] or [control] in the add dialog. \
Rearrange images by using drag-and-drop.'))
    return presentations
    
def _notifications():
    notifications = _h(_('Notifications')) +\
            _p(_('You may have a need to notify someone in the audience of \
something, such as a crying baby in the nursury. A notification can be used \
to let them know. The notification can be set using the text box underneath \
the preview screen. Use the buttons right to it to display and remove the \
message.'))
    return notifications

def _backgrounds():
    backgrounds = _h(_('Backgrounds')) +\
            _p(_('The background image for presentations can be a gradient \
or an image file. Change the image by using the controls next to the \
preview screen.')) +\
            _h(_('Background Image Tips'), 2) +\
            _p(_('Background images should generally have a soft focus to them, \
and use a minimal amount of contrast. Backgrounds with hard lines, or with \
many colors make the text difficult to read.'))
    return backgrounds

def _shortcuts_table():
    # value None means "this is a heading"
    shortcuts = [[_("Screen"), None],
                 [_("Present"), "F5"],
                 [_("Logo Screen"), _("Control-g")],
                 [_("Black Screen"), "b"],
                 [_("Hide"), "Esc"],
                 [_("Slide Movement"), None],
                 [_("Next Screen"), _("Down")],
                 [_("Previous Screen"), _("Up")],
                 [_("Next Screen (Use Order)"), _("PageDown")],
                 [_("Previous Screen (Use Order)"), _("PageUp")],
                 [_("Next Presentation"), _("Control-PageDown")],
                 [_("Previous Presentation"), _("Control-PageUp")],
                 [_("Lyrics type"), None],
                 [_("Go to Verse #"), _("1, 2, 3 and so on")],
                 [_("Go to Chorus"), "c"],
                 [_("Other"), None],
                 [_("New Schedule"), _("Ctrl-N")],
                 [_("Find Presentation"), _("Ctrl-F")]
                 ]
    
    table = _h(_('Shortcut Keys')) + '<table border="2" cellpadding="5"'
    
    for row in shortcuts:
        if not row[1]:
            table += '<tr><th colspan="2">%s</th></tr>'%row[0]
        else:
            table += '<tr><td>%s</td><td>%s</td></tr>'%(row[0], row[1])
    table += '</table>'
    return table


def _p(text):
    return "<p>%s</p>\n"%text

def _h(text, level=1):
    return "<h%(level)d>%(text)s</h%(level)d>\n"%{"level":level,
                                                  "text":text}