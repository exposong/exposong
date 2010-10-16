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
import gtk
import webbrowser
from urllib import pathname2url

import exposong._hook
from exposong import RESOURCE_PATH, DATA_PATH
from exposong import statusbar

class Help(exposong._hook.Menu, object):
    
    def __init__(self):
        self.helpfile = os.path.join(DATA_PATH, 'help.html')
    
    def show(self, *args):
        "Show the file in the web browser."
        all = self._header() + self._about() + self._schedules() +\
                self._presentations() + self._notifications() +\
                self._backgrounds() + self._shortcuts_table()
        
        f = open(self.helpfile, "w")
        f.write(all)
        exposong.log.info("Help page generated.")
        f.close()
        webbrowser.open("file:"+pathname2url(self.helpfile))
        statusbar.statusbar.output(_("Help page opened in Web Browser"))
        exposong.log.info("Help page opened in Web Browser.")
    
    def show_contrib(self, *args):
        "Show the how to contribute page."
        webbrowser.open("http://exposong.org/contribute")
        exposong.log.info("Contribute page opened in Web Browser.")
    
    def delete_help_file(self):
        'Delete the generated help file'
        if os.path.exists(self.helpfile):
            os.remove(self.helpfile)
    
    def _header(self):
        header = """<head>
    <title>%(title)s</title>
    <meta http-equiv="content-type" content="text-html; charset=utf-8">
    <link rel='stylesheet' href='%(stylepath)s' content='text/css'>
    </head>
    <body>
    <div id='header'>
    <h2><img src='%(headerimg)s' alt='' /></h2>
    </div>
    <div id='content'>"""%\
                {'title':_('ExpoSong Help'),
                'stylepath':os.path.join(RESOURCE_PATH, 'style.css'),
                'headerimg':os.path.join(RESOURCE_PATH, 'exposong.png')}
        return header
    
    def _about(self):
        about = self._h(_('About')) +\
                self._p(_('ExpoSong is a free, open-source, presentation \
    program to assist with worship assemblies. Create lyrics or plain-text slides, \
    create schedules, and put up slides on the screen.'))
        return about
    
    def _schedules(self):
        schedules = self._h(_('Schedules')) +\
                self._p(_('Schedules are used to create an order of presentations.')) +\
                self._p(_('To create a schedule, in the menu, select Schedule-&gt;\
    New. Name your schedule, according to the date or event. Add songs to the \
    schedule by dragging them from the library onto the schedule.'))
        return schedules
    
    def _presentations(self):
        presentations = self._h(_('Creating Presentations')) +\
                self._p(_('Presentations are a set of slides to be presented on the screen. \
    To create a new presentation, on the menu, select Presentation-&gt;New, and \
    then the appropriate presentation type.')) +\
                self._p(_('Add, edit, or delete slides using the toolbar buttons. \
    In a schedule, you can drag and drop slides to reorder the slides.')) +\
                self._p(_('The <b>text</b> presentation is used to create a non-specific, \
    text slide. It can be used for sermons, announcements, or anything else.')) +\
                self._p(_('The <b>lyric</b> presentation is for song lyrics. It contains \
    slide descriptors, such as "Verse #", "Chorus", "Bridge", or "Refrain", which are \
    for the benefit of the presenter. There are some information tabs, and some of \
    the data from this area, like author, songbook number, copyright and ccli \
    number, are displayed on the bottom of the presentation screen.')) +\
                self._p(_('Lyric presentations can also be reordered. Use the verse \
    names in brackets and enter them in the order you wish to have in the "Order" \
    field, for example: "v1 c v2 b c e"')) +\
                self._p(_('The <b>image</b> presentation is used to present images. \
    Add multiple images at once by using [shift] or [control] in the add dialog. \
    Rearrange images by using drag-and-drop.'))
        return presentations
        
    def _notifications(self):
        notifications = self._h(_('Notifications')) +\
                self._p(_('You may have a need to notify someone in the audience of \
    something, such as a crying baby in the nursury. A notification can be used \
    to let them know. The notification can be set using the text box underneath \
    the preview screen. Use the buttons right to it to display and remove the \
    message.'))
        return notifications
    
    def _backgrounds(self):
        backgrounds = self._h(_('Backgrounds')) +\
                self._p(_('The background image for presentations can be a gradient \
    or an image file. Change the image by using the controls next to the \
    preview screen.')) +\
                self._h(_('Background Image Tips'), 2) +\
                self._p(_('Background images should generally have a soft focus to them, \
    and use a minimal amount of contrast. Backgrounds with hard lines, or with \
    many colors make the text difficult to read.'))
        return backgrounds
    
    def _shortcuts_table(self):
        # value None means "this is a heading"
        shortcuts = [[_("Screen"), None],
                     [_("Present"), "F5"],
                     [_("Logo Screen"), _("Control-g")],
                     [_("Black Screen"), "b"],
                     [_("Hide"), "Esc"],
                     [_("Slide Movement"), None],
                     [_("Next Screen"), _("Down")],
                     [_("Previous Screen"), _("Up")],
                     [_("Next Screen (Use Order)"), _("Page Down")],
                     [_("Previous Screen (Use Order)"), _("Page Up")],
                     [_("Next Presentation"), _("Control-Page Down")],
                     [_("Previous Presentation"), _("Control-Page Up")],
                     [_("Lyrics type"), None],
                     [_("Go to Verse #"), _("1, 2, 3 and so on")],
                     [_("Go to Chorus"), "c"],
                     [_("Other"), None],
                     [_("New Schedule"), _("Ctrl-N")],
                     [_("Find Presentation"), _("Ctrl-F")]]
        
        table = self._h(_('Shortcut Keys')) + '<table border="2" cellpadding="5"'
        
        for row in shortcuts:
            if not row[1]:
                table += '<tr><th colspan="2">%s</th></tr>'%row[0]
            else:
                table += '<tr><td>%s</td><td>%s</td></tr>'%(row[0], row[1])
        table += '</table>'
        return table
    
    
    def _p(self, text):
        'Wrap text in HTML <p> element'
        return "<p>%s</p>\n"%text
    
    def _h(self, text, level=1):
        'Wrap text in HTML header element with the specified level'
        return "<h%(level)d>%(text)s</h%(level)d>\n"%{"level":level,
                                                      "text":text}
    
    @classmethod
    def merge_menu(cls, uimanager):
        'Merge new values with the uimanager.'
        self = exposong.help.help
        cls._actions = gtk.ActionGroup('help')
        cls._actions.add_actions([
                ('UsageGuide', None, _("Usage Guide"), None, None, self.show),
                ('Contribute', None, _("Contribute"), None, None,
                        self.show_contrib),
                ])
        
        uimanager.insert_action_group(cls._actions, -1)
        uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="Help">
                    <menuitem action="UsageGuide" />
                    <menuitem action="Contribute" />
                </menu>
            </menubar>
            """)

help = Help()
