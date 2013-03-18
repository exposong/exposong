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
from gi.repository import Gtk
import webbrowser
import urllib, urllib2

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
        self.helpfile = os.path.join(DATA_PATH, '.cache', 'help.html')
    
    def show(self, *args):
        "Show the file in the web browser."
        all_ = self._header() + self._about() + self._presentations() +\
                self._schedules() + self._themes() +\
                self._notifications() + self._shortcuts_table() +\
                self._footer()
        
        f = open(self.helpfile, "w")
        f.write(all_)
        exposong.log.info("Help page generated.")
        f.close()
        webbrowser.open("file:"+urllib.pathname2url(self.helpfile))
        statusbar.statusbar.output(_("Help page opened in Web Browser"))
        exposong.log.info("Help page opened in Web Browser.")
    
    def check_for_update(self, *args, **kw):
        "Let the user know if a new version is out."
        statusbar.statusbar.output(_("Checking for updates ..."))
        
        (new_version, msg, err) = self._update_available()
        
        if err:
            statusbar.statusbar.output(msg)
            dlg = Gtk.MessageDialog(exposong.main.main, 0,
                                    Gtk.MessageType.ERROR, Gtk.ButtonsType.CLOSE, msg)
            dlg.set_title(_("An Error Occurred"))
        elif new_version:
            dlg = Gtk.MessageDialog(exposong.main.main, 0, Gtk.MessageType.WARNING,
                                    Gtk.ButtonsType.YES_NO, msg)
            dialog.set_default_response(Gtk.ResponseType.YES)
            dlg.set_title(_("A New Version is Available"))
        else:
            dlg = Gtk.MessageDialog(exposong.main.main, 0,
                                    Gtk.MessageType.INFO, Gtk.ButtonsType.OK, msg)
            dlg.set_title(_("ExpoSong is Up to Date"))
        
        if not err:
            config.config.set("updates", "last_check", str(int(time.time())) )
        
        #Do not show errors when checking automatically
        if 'auto_check' in kw and not new_version:
            return
        
        if dlg.run() == Gtk.ResponseType.YES:
            webbrowser.open("http://exposong.org/download/")
        dlg.destroy()
    
    def _update_available(self):
        'Check exposong.org if an update is available'
        msg = ""
        err = new_version = False
        fl = None
        try:
            fl = urllib2.urlopen("http://exposong.org/_current-version/", timeout=2)
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
    
    def _header(self):
        'Returns the html header for the help page'
        header = """<html>\n<head>
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
program to assist with worship assemblies. Create lyrics or custom \
presentations, create schedules, and create custom themes.'))
        return about
    
    def _schedules(self):
        'Returns the schedules paragraph for the help page'
        schedules = self._h(_('Schedules')) +\
                self._p(_('Schedules are used to create an order of presentations.')) +\
                self._p(_('To create a schedule, in the menu, select \
File|New|New Schedule. We suggest you name your schedule with the date, along \
with an event description if needed. Add songs to the schedule by dragging \
them onto the schedule, or Edit|Current Presentation|Add to Schedule.'))
        return schedules
    
    def _presentations(self):
        'Returns the Presentations parapraph of the help page'
        presentations = self._h(_('Creating Presentations')) +\
                self._p(_('Presentations are a set of slides to be presented \
on the screen. To create a new presentation, on the menu, select File|New, and \
select New Song or New ExpoSong Presentation.')) +\
            self._p(_('The <b>ExpoSong Presentation</b> is used to create \
general presentations. It can be used for  sermons, announcements, or anything \
other than lyrics. Currently, the only content can be text or images, but other \
media may be available in future releases.')) +\
            self._p(_('The <b>Song</b> presentation type is for song lyrics. The \
slides can be verses, choruses, or other lyrics parts, and can contain indexes \
(such as Verse 1, Verse 2). Songs can contain metadata as well, such as author, \
songbook number, copyright and CCLI number, which may be displayed on the \
screen with the Lyric.')) +\
            self._p(_('Song presentations can also be reordered. Use the verse \
names in quotes and enter them in the order you wish to have separated by \
spaces in the "Order" field, for example: "v1 c v2 b c e"'))
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
    
    def _themes(self):
        'Returns the themes paragraph of the help page.'
        themes = self._h(_('Themes')) +\
                self._p(_('Themes can be created by using File|New|New Theme. \
The first part of a theme is the background. It can consist of images, solid \
colors, and gradient (which is a gradual change from one color to the next).')) +\
                self._p(_('The body and footer text can be moved and modified \
in font name and size, color, alignment, line spacing (from one row to the \
next), the text shadow\'s color and offset, and a text outline size and color.')) +\
                self._p(_('Both backgrounds and body and footer texts can be \
moved to different positions using the form under the preview.')) +\
                self._p(_('Metadata, such as author, copyright, and tags can \
also be added to the theme using the tab. This information will not appear on the screen.')) +\
                self._h(_('Background Tips'), 2) +\
                self._p(_('Presentation backgrounds should generally have a \
soft focus to them, and use a minimal amount of contrast. Backgrounds with hard \
lines, or with many colors make the text difficult to read.'))
        return themes
    
    def _shortcuts_table(self):
        'Returns a html table with the shortcuts used in ExpoSong listed'
        # value None means "this is a heading"
        shortcuts = [[_("Screen"), None],
                     [_("Present"), "F5"],
                     [_("Logo Screen"), _("Ctrl+G")],
                     [_("Black Screen"), "B"],
                     [_("Hide"), "Esc"],
                     [_("Slide Movement"), None],
                     [_("Next Slide"), _("Page Down")],
                     [_("Previous Slide"), _("Page Up")],
                     [_("Next Presentation"), _("Ctrl+Page Down")],
                     [_("Previous Presentation"), _("Ctrl+Page Up")],
                     [_("Other"), None],
                     [_("New Song"), _("Ctrl+N")],
                     [_("Find Presentation"), _("Ctrl+F")],
                     [_("Quit"), _("Ctrl+Q")]
                     ]
        
        table = self._h(_('Shortcut Keys')) + '<table border="2" cellpadding="5">'
        
        for row in shortcuts:
            if not row[1]:
                table += '<tr><th colspan="2">%s</th></tr>'%row[0]
            else:
                table += '<tr><td>%s</td><td>%s</td></tr>'%(row[0], row[1])
        table += '</table>'
        return table
    
    def _footer(self):
        'Returns the html footer for the help page'
        footer = "</div>" # id:content
        footer += "<div id='footer'>\n"
        footer += u"%s \u2013 <a href='http://exposong.org'>%s</a>\n" %\
                  (_("Thank you for your continued support."),
                   _("The Exposong Team"))
        footer += "</div>\n"
        footer += "</body>\n</html>"
        return footer
    
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
        cls._actions = Gtk.ActionGroup('help')
        cls._actions.add_actions([
                ('UsageGuide', None, _("Usage Guide"), None, None, self.show),
                ('CheckUpdate', None, _("Check for New _Version"), None, None,
                        self.check_for_update),
                ])
        
        uimanager.insert_action_group(cls._actions, -1)
        uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="Help">
                    <menuitem action="UsageGuide" />
                    <menuitem action="CheckUpdate" />
                </menu>
            </menubar>
            """)

help = Help()
