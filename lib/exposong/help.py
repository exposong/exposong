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

import os
import time
import gtk
import webbrowser
import urllib

import exposong.main
import exposong.version
import exposong._hook
from exposong import RESOURCE_PATH, DATA_PATH
from exposong import statusbar, config

class Help(exposong._hook.Menu, object):
    """
    A class to provide help to the user,
    like a Browser help page and an update check
    """
    def __init__(self):
        self.helpfile = os.path.join(DATA_PATH, 'help.html')
    
    def show(self, *args):
        "Show the file in the web browser."
        all_ = self._header() + self._about() + self._schedules() +\
                self._presentations() + self._notifications() +\
                self._backgrounds() + self._shortcuts_table()
        
        f = open(self.helpfile, "w")
        f.write(all_)
        exposong.log.info("Help page generated.")
        f.close()
        webbrowser.open("file:"+urllib.pathname2url(self.helpfile))
        statusbar.statusbar.output(_("Help page opened in Web Browser"))
        exposong.log.info("Help page opened in Web Browser.")
    
    def show_contrib(self, *args):
        "Show the how to contribute page."
        webbrowser.open("http://exposong.org/contribute")
        exposong.log.info("Contribute page opened in Web Browser.")
    
    def check_for_update(self, *args, **kw):
        "Let the user know if a new version is out."
        statusbar.statusbar.output(_("Checking for updates ..."))
        
        (new_version, msg, err) = self._update_available()
        
        if err:
            statusbar.statusbar.output(msg)
            dlg = gtk.MessageDialog(exposong.main.main, 0,
                                    gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, msg)
            dlg.set_title(_("An Error Occurred"))
        elif new_version:
            dlg = gtk.MessageDialog(exposong.main.main, 0, gtk.MESSAGE_WARNING,
                                    gtk.BUTTONS_YES_NO, msg)
            dlg.set_title(_("A New Version is Available"))
        else:
            dlg = gtk.MessageDialog(exposong.main.main, 0,
                                    gtk.MESSAGE_INFO, gtk.BUTTONS_OK, msg)
            dlg.set_title(_("ExpoSong is Up to Date"))
        
        if not err:
            config.config.set("updates", "last_check", str(int(time.time())) )
        
        #Do not show errors when checking automatically
        if 'auto_check' in kw and not new_version:
            return
        
        if dlg.run() == gtk.RESPONSE_YES:
            webbrowser.open("http://exposong.org/download/")
        dlg.destroy()
    
    def _update_available(self):
        'Check exposong.org if an update is available'
        msg = ""
        err = new_version = False
        fl = None
        try:
            fl = urllib.urlopen("http://exposong.org/_current-version/")
            if fl.getcode() != 200:
                err = True
                msg = _("Could not read the website (error code %d).")\
                      % fl.getcode()
            else:
                version = fl.read().strip()
                if version > exposong.version.__version__:
                    new_version = True
                    msg = _("A new version (%s) is available. Would you like \
to be taken to the download page?")% version
                else:
                    new_version = False
                    msg = _("You are using the most recent version.")
        except IOError:
            err = True
            msg = _("Could not connect to %s.") % "exposong.org"
        finally:
            if fl:
                fl.close()
        return (new_version, msg, err)
        
        
    def delete_help_file(self):
        'Deletes the generated help file'
        if os.path.exists(self.helpfile):
            os.remove(self.helpfile)
    
    def _header(self):
        'Returns the html header for the help page'
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
        'Returns the introduction paragraph for the help page'
        about = self._h(_('About')) +\
                self._p(_('ExpoSong is a free, open-source, presentation \
program to assist with worship assemblies. Create lyrics or plain-text slides, \
create schedules, and put up slides on the screen.'))
        return about
    
    def _schedules(self):
        'Returns the schedules paragraph for the help page'
        schedules = self._h(_('Schedules')) +\
                self._p(_('Schedules are used to create an order of presentations.')) +\
                self._p(_('To create a schedule, in the menu, select Schedule-&gt;\
New. Name your schedule, according to the date or event. Add songs to the \
schedule by dragging them from the library onto the schedule.'))
        return schedules
    
    def _presentations(self):
        'Returns the Presentations parapraph of the help page'
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
        'Returns the notifications paragraph of the help page'
        notifications = self._h(_('Notifications')) +\
                self._p(_('You may have a need to notify someone in the audience of \
something, such as a crying baby in the nursury. A notification can be used \
to let them know. The notification can be set using the text box underneath \
the preview screen. Use the buttons right to it to display and remove the \
message.'))
        return notifications
    
    def _backgrounds(self):
        'Returns the backgrounds paragraph of the help page'
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
        'Returns a html table with the shortcuts used in ExpoSong listed'
        # value None means "this is a heading"
        shortcuts = [[_("Screen"), None],
                     [_("Present"), "F5"],
                     [_("Logo Screen"), _("Control-g")],
                     [_("Black Screen"), "b"],
                     [_("Hide"), "Esc"],
                     [_("Slide Movement"), None],
                     [_("Next Slide"), _("Down")],
                     [_("Previous Slide"), _("Up")],
                     [_("Next Slide (Use Order)"), _("Page Down")],
                     [_("Previous Slide (Use Order)"), _("Page Up")],
                     [_("Next Presentation"), _("Control-Page Down")],
                     [_("Previous Presentation"), _("Control-Page Up")],
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
                ('CheckUpdate', None, _("Check for New _Version"), None, None,
                        self.check_for_update),
                ])
        
        uimanager.insert_action_group(cls._actions, -1)
        uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="Help">
                    <menuitem action="UsageGuide" />
                    <menuitem action="Contribute" />
                    <menuitem action="CheckUpdate" />
                </menu>
            </menubar>
            """)

help = Help()
