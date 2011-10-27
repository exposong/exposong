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

import filecmp
import gtk
import os
import os.path
import shutil
import tempfile
import tarfile
import difflib

from exposong_openlyrics import openlyrics

import exposong.main
import exposong.schedlist
import exposong.theme
from exposong import DATA_PATH
from exposong.plugins import Plugin
from exposong.glob import find_freefile, title_to_filename
from exposong.config import config

"""
Adds functionality to move schedules, or a full library to another exposong
instance.
"""

information = {
    'name': _("Export/Import Functions"),
    'description': __doc__,
    'required': False,
}

FILE_EXT = ".expo"
_FILTER = gtk.FileFilter()
_FILTER.set_name("ExpoSong Archive")
_FILTER.add_pattern("*.expo")
_FILTER.add_pattern("*.tar.gz")

class ExportImport(Plugin, exposong._hook.Menu):
    '''
    Export or Import from file.
    
    A .expo file is a tar.gz file, with the following format:
        sched/ - folder contains all schedule xml files.
        pres/ - folder containing all presentation files.
    '''
    def __init__(self):
        pass
    
    @classmethod
    def export_song(cls, *args):
        'Export a Song'
        pres = exposong.preslist.preslist.get_active_item()
        
        dlg = gtk.FileChooserDialog(_("Export Current Song"),
                                    exposong.main.main,
                                    gtk.FILE_CHOOSER_ACTION_SAVE,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        dlg.set_do_overwrite_confirmation(True)
        dlg.set_current_folder(config.get("open-save-dialogs", "export-song"))
        dlg.set_current_name(os.path.basename(pres.filename))
        if dlg.run() == gtk.RESPONSE_ACCEPT:
            os.chdir(DATA_PATH)
            fname = dlg.get_filename()
            if not fname.endswith(".xml"):
                fname += ".xml"
            exposong.log.info('Exporting presentation "%s" to "%s".',
                              pres.get_title(), fname)
            shutil.copy(pres.filename, fname)
            config.set("open-save-dialogs", "export-song", os.path.dirname(fname))
        dlg.destroy()
    
    @classmethod
    def export_sched(cls, *args):
        'Export a single schedule with belonging presentations to file.'
        sched = exposong.schedlist.schedlist.get_active_item()
        if not sched:
            return False
        dlg = gtk.FileChooserDialog(_("Export Current Schedule"),
                                    exposong.main.main,
                                    gtk.FILE_CHOOSER_ACTION_SAVE,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        dlg.add_filter(_FILTER)
        dlg.set_do_overwrite_confirmation(True)
        dlg.set_current_folder(config.get("open-save-dialogs", "export-sched"))
        dlg.set_current_name(os.path.basename(title_to_filename(sched.title))+".expo")
        if dlg.run() == gtk.RESPONSE_ACCEPT:
            os.chdir(DATA_PATH)
            fname = dlg.get_filename()
            if not fname.endswith(".expo"):
                fname += ".expo"
            exposong.log.info('Exporting schedule "%s" to "%s".',
                              sched.title, fname)
            tar = tarfile.open(fname, "w:gz")
            for item in cls._get_sched_list():
                tar.add(item[0], item[1])
            tar.close()
            config.set("open-save-dialogs", "export-sched", os.path.dirname(fname))
        dlg.destroy()
        
    @classmethod
    def _get_sched_list(cls, *args):
        'Returns a list with a single schedule and belonging presentations'
        exposong.main.main._save_schedules()
        sched = exposong.schedlist.schedlist.get_active_item()
        sched_list = []
        sched_list.append((os.path.join(DATA_PATH, "sched", sched.filename),
                           os.path.join("sched",
                           os.path.basename(sched.filename))))
        itr = sched.get_iter_first()
        while itr:
            fn = os.path.basename(sched.get_value(itr, 0).filename)
            sched_list.append((os.path.join(DATA_PATH, "pres", fn),
                               os.path.join("pres", fn)))
            if sched.get_value(itr, 0).get_type() == 'exposong':
                for slide in sched.get_value(itr, 0).slides:
                    for c in slide._content:
                        if c.__class__ != exposong.theme.Image: continue
                        fn = os.path.basename(c.src)
                        sched_list.append((os.path.join(DATA_PATH, "pres/res",
                                                        fn),
                                           os.path.join("pres/res", fn)))
            itr = sched.iter_next(itr)
        return sched_list
    
    @classmethod
    def export_lib(cls, *args):
        'Export the full library to tar-compressed file.'
        dlg = gtk.FileChooserDialog(_("Export Library"), exposong.main.main,
                                    gtk.FILE_CHOOSER_ACTION_SAVE,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        dlg.add_filter(_FILTER)
        dlg.set_do_overwrite_confirmation(True)
        dlg.set_current_name(_("exposong_library.expo"))
        dlg.set_current_folder(config.get("open-save-dialogs", "export-lib"))
        if dlg.run() == gtk.RESPONSE_ACCEPT:
            fname = dlg.get_filename()
            if not fname.endswith(".expo"):
                fname += ".expo"
            exposong.log.info('Exporting library to "%s".', fname)
            tar = tarfile.open(fname, "w:gz")
            for item in cls._get_library_list():
                tar.add(item[0], item[1])
            tar.close()
            config.set("open-save-dialogs", "export-lib", os.path.dirname(fname))
        dlg.destroy()
        
    @classmethod
    def _get_library_list(cls, *args):
        'Returns a list with all items in pres, presentation resources,\
        and sched folder'
        #Make sure schedules are up to date.
        exposong.main.main._save_schedules() 
        library = exposong.main.main.library
        itr = library.get_iter_first()
        lib_list = []
        while itr:
            fn = library.get_value(itr, 0).filename
            lib_list.append((fn, os.path.join("pres", os.path.split(fn)[1])))
            if library.get_value(itr, 0).get_type() == 'exposong':
                for slide in library.get_value(itr, 0).slides:
                    for c in slide._content:
                        if c.__class__ != exposong.theme.Image: continue
                        fn = os.path.basename(c.src)
                        lib_list.append((os.path.join(DATA_PATH, "pres/res",
                                                      fn),
                                         os.path.join("pres/res", fn)))
            itr = library.iter_next(itr)
        model = exposong.schedlist.schedlist.get_model()
        itr = model.iter_children(exposong.schedlist.schedlist.custom_schedules)
        while itr:
            fn = model.get_value(itr, 0).filename
            lib_list.append((fn, os.path.join("sched", os.path.split(fn)[1])))
            itr = model.iter_next(itr)
        return lib_list
    
    @classmethod
    def export_theme(cls, *args):
        'Export the active theme to tar-compressed file'
        cur_theme = exposong.themeselect.themeselect.get_active()
        
        dlg = gtk.FileChooserDialog(_("Export Theme"), exposong.main.main,
                                    gtk.FILE_CHOOSER_ACTION_SAVE,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        dlg.add_filter(_FILTER)
        dlg.set_do_overwrite_confirmation(True)
        dlg.set_current_folder(config.get("open-save-dialogs", "export-theme"))
        dlg.set_current_name(_("theme_%s.expo")%title_to_filename(
                                        os.path.basename(cur_theme.get_title())))
        if dlg.run() == gtk.RESPONSE_ACCEPT:
            fname = dlg.get_filename()
            if not fname.endswith(".expo"):
                fname += ".expo"
            exposong.log.info('Exporting theme "%s" to "%s".',
                              cur_theme.get_title(), fname)
            tar = tarfile.open(fname, "w:gz")
            
            tar.add(os.path.join(DATA_PATH, 'theme', cur_theme.filename),
                    os.path.join('theme', cur_theme.filename))
            for bg in cur_theme.backgrounds:
                if isinstance(bg, exposong.theme.ImageBackground):
                    tar.add(os.path.join(DATA_PATH, 'theme', 'res', bg.src),
                            os.path.join('theme', 'res', bg.src))
            tar.close()
            config.set("open-save-dialogs", "export-theme", os.path.dirname(fname))
        dlg.destroy()
    
    @classmethod
    def import_song_dialog(cls, *args):
        'Import OpenLyrics Song(s)'
        dlg = gtk.FileChooserDialog(_("Import Song(s) (OpenLyrics Format)"), exposong.main.main,
                                    gtk.FILE_CHOOSER_ACTION_OPEN,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        _FILTER = gtk.FileFilter()
        _FILTER.set_name("OpenLyrics Song")
        _FILTER.add_pattern("*.xml")
        dlg.add_filter(_FILTER)
        dlg.set_select_multiple(True)
        dlg.set_current_folder(config.get("open-save-dialogs", "import-song"))
        if dlg.run() == gtk.RESPONSE_ACCEPT:
            dlg.hide()
            files = dlg.get_filenames()
            for f in files:
                newpath = os.path.join(DATA_PATH, "pres", os.path.basename(f))
                if os.path.exists(newpath):
                    if filecmp.cmp(f, newpath):
                        pass #Skip if they are the same.
                    else:
                        cls.check_import_song(f)
                else:
                    cls.check_import_song(f)
            config.set("open-save-dialogs", "import-song", os.path.dirname(f))
        dlg.destroy()
    
    @classmethod
    def check_import_song(cls, filename):
        '''Creates a Song of the given filename and checks author and titles for
        similarities. Asks the user which song to keep when similarities are detected'''
        new_song = openlyrics.Song(filename)
        
        library = exposong.main.main.library
        itr = library.get_iter_first()
        
        # Highest author and title similaritiy for all songs
        max_author_sim = 0.0
        max_title_sim = 0.0
        most_similar_song = None
        
        ## This iterates over every song in library and gets the similarity for each author and title.
        ## If title and author both have a high similarity in one Song, than it is set as `most_similar_song`.
        while itr:
            pres = library.get_value(itr, 0)
            if pres.get_type() == "song":
                cur_title_sim = cls.get_similarity([x.text for x in pres.song.props.titles],
                                                   [x.text for x in new_song.props.titles])
                cur_author_sim = cls.get_similarity([x.name for x in pres.song.props.authors],
                                                    [x.name for x in new_song.props.authors])
                
                if cur_author_sim>max_author_sim and cur_title_sim>max_title_sim:
                    max_author_sim = cur_author_sim
                    max_title_sim = cur_title_sim
                    most_similar_song = pres
                    
                exposong.log.debug('Similarity between file "%s" and presentation "%s" is %d%%.',
                                   filename, pres.filename,
                                   (cur_author_sim+cur_title_sim)/200)
            itr = library.iter_next(itr)
        #TODO: Check 60 percent limit
        #TODO: Add checkbox to content area to keep the choice for all songs.
        #TODO: Add expander to dialog to show differences between songs
        if most_similar_song and (max_author_sim+max_title_sim)/2 > 0.6:
            msg = _('The Song "%(new_song)s" has similarities with this existing Song from your library: "%(existing_song)s" .\
What do you want to do?'%{'new_song':new_song.props.titles[0].text, 'existing_song':most_similar_song.song.props.titles[0].text})
            dlg = gtk.MessageDialog(type=gtk.MESSAGE_QUESTION,
                    buttons=gtk.BUTTONS_NONE,
                    message_format=msg)
            btn = dlg.add_button(_("Replace existing Song"), 0)
            btn.connect("clicked", cls._import_replace_existing_song, most_similar_song.filename, filename)
            btn = dlg.add_button(_("Keep existing Song"), 1)
            btn.connect("clicked", cls._import_keep_existing_song)
            btn = dlg.add_button(_("Keep both Songs"), 2)
            btn.connect("clicked", cls._import_keep_both_songs, filename)
            
            dlg.run()
            dlg.destroy()
        else:
            cls._import_keep_both_songs(None, filename)
    
    @classmethod
    def _import_replace_existing_song(cls, widget, existing, new):
        os.remove(existing)
        shutil.copy(new, os.path.join(DATA_PATH, "pres", os.path.basename(new)))
        presrm = exposong.main.main.library.finditer(filename=os.path.basename(existing))
        if presrm: exposong.main.main.library.remove(presrm)
        exposong.main.main.load_pres(os.path.basename(new))
        #TODO: Remove existing presentation from preslist and schedules
        
        # Add to Custom Schedules
        model = exposong.schedlist.schedlist.get_model()
        itr = model.iter_children(exposong.schedlist.schedlist.custom_schedules)
        while itr:
            sched = model.get_value(itr, 0)
            scheditem = exposong.schedule.ScheduleItem(pres, "")
            presrm = sched.finditer(os.path.basename(existing))
            sched.insert_before(presrm, scheditem.get_row())
            if presrm: sched.remove(presrm)
            itr = model.iter_next(itr)
        
    
    @classmethod
    def _import_keep_existing_song(cls, widget):
        pass
    
    @classmethod
    def _import_keep_both_songs(cls, widget, new_song_fn):
        dest = find_freefile(os.path.join(DATA_PATH, "pres", os.path.basename(new_song_fn)))
        shutil.copy(new_song_fn, dest)
        exposong.main.main.load_pres(os.path.basename(dest))
    
    @classmethod
    def get_similarity(self, s1, s2):
        "Returns a ratio (between 0 and 1) between s1 and s2."
        # We are testing both objects together, because there is no use if they
        # are of different types.
        if isinstance(s1, str) and isinstance(s2, str):
            s1 = s1.lower()
            s2 = s2.lower()
        elif isinstance(s1, list) and isinstance(s2, list):
            s1 = [x.lower() for x in sorted(s1)]
            s2 = [x.lower() for x in sorted(s2)]
        return difflib.SequenceMatcher(a=s1, b=s2).ratio()
    
    @classmethod
    def import_dialog(cls, *args):
        'Import a schedule, backgrounds or library.'
        dlg = gtk.FileChooserDialog(_("Import"), exposong.main.main,
                                    gtk.FILE_CHOOSER_ACTION_OPEN,
                                    (gtk.STOCK_CANCEL, gtk.RESPONSE_REJECT,
                                    gtk.STOCK_OK, gtk.RESPONSE_ACCEPT))
        dlg.add_filter(_FILTER)
        dlg.set_current_folder(config.get("open-save-dialogs", "import-expo"))
        if dlg.run() == gtk.RESPONSE_ACCEPT:
            dlg.hide()
            cls.import_file(dlg.get_filename())
            config.set("open-save-dialogs", "import-expo", os.path.dirname(dlg.get_filename()))
        dlg.destroy()
    
    @classmethod
    def import_file(cls, filename):
        'Import anything that has been exported before (.expo file)'
        exposong.log.info("Importing %s", filename)
        tar = tarfile.open(unicode(filename), "r:gz")
        # Make a temporary directory so that no files are overwritten.
        tmpdir = tempfile.mkdtemp(os.path.split(filename)[1].rstrip(".expo"))
        tar.extractall(tmpdir)
        tar.close()
        
        ### Presentation Images ###
        imgs2rename = []
        if os.path.isdir(os.path.join(tmpdir, "pres/res")):
            for nm in os.listdir(os.path.join(tmpdir,"pres/res")):
                exposong.log.debug("  Presentation Image: %s", nm)
                if not os.path.exists(os.path.join(DATA_PATH, "pres/res", nm)):
                    shutil.move(os.path.join(tmpdir, "pres/res", nm),
                                os.path.join(DATA_PATH, "pres/res", nm))
                elif filecmp.cmp(os.path.join(tmpdir, "pres/res", nm),
                                 os.path.join(DATA_PATH, "pres/res", nm)):
                    pass # Skip if they are the same.
                else:
                    nm2 = find_freefile(os.path.join(DATA_PATH, "pres/res", nm))
                    shutil.move(os.path.join(tmpdir, "pres/res", nm), 
                                os.path.join(DATA_PATH, "pres/res", nm2))
                    imgs2rename.append((nm,nm2.rpartition(os.sep)[2]))
        
        ### Presentations ###
        pres2rename = []
        if os.path.isdir(os.path.join(tmpdir, "pres")):
            for nm in os.listdir(os.path.join(tmpdir,"pres")):
                exposong.log.debug("  Presentation: %s", nm)
                if not os.path.isfile(os.path.join(tmpdir,"pres",nm)):
                    continue
                # Rename Images
                if len(imgs2rename) > 0:
                    infl = open(os.path.join(tmpdir,"pres",nm),"r")
                    outfl = open(os.path.join(tmpdir,"pres",nm+".1"),"w")
                    for ln in infl:
                        for img in imgs2rename:
                            ln = re.subn(r"\b"+img[0]+r"\b",img[1],ln)[0]
                        outfl.write(ln)
                    infl.close()
                    outfl.close()
                    shutil.move(os.path.join(tmpdir,"pres",nm+".1"),
                                os.path.join(tmpdir,"pres",nm))
                
                if os.path.isfile(os.path.join(DATA_PATH, "pres", nm)):
                    if filecmp.cmp(os.path.join(tmpdir, "pres", nm),
                                   os.path.join(DATA_PATH, "pres", nm)):
                        pass #Skip if they are the same.
                else:
                    cls.check_import_song(os.path.join(tmpdir, "pres", nm))
                # Do we need to test if images have changed before skipping?
        
        ### Schedules ###
        if os.path.isdir(os.path.join(tmpdir, "sched")):
            for nm in os.listdir(os.path.join(tmpdir,"sched")):
                exposong.log.debug("  Schedule: %s", nm)
                # Rename presentations
                if len(pres2rename) > 0:
                    infl = open(os.path.join(tmpdir,"sched",nm),"r")
                    outfl = open(os.path.join(tmpdir,"sched",nm+".1"),"w")
                    for ln in infl:
                        for pres in pres2rename:
                            ln = re.subn(r"\b"+pres[0]+r"\b",pres[1],ln)[0]
                        outfl.write(ln)
                    infl.close()
                    outfl.close()
                    shutil.move(os.path.join(tmpdir,"sched",nm+".1"),
                                os.path.join(tmpdir,"sched",nm))
                
                if not os.path.exists(os.path.join(DATA_PATH, "sched", nm)):
                    shutil.move(os.path.join(tmpdir, "sched", nm),
                                os.path.join(DATA_PATH, "sched", nm))
                    exposong.main.main.load_sched(nm)
                elif filecmp.cmp(os.path.join(tmpdir, "sched", nm),
                                 os.path.join(DATA_PATH, "sched", nm)):
                    pass #Skip if they are the same.
                    # Do we need to test if presentations have changed?
                else:
                    nm2 = find_freefile(os.path.join(DATA_PATH, "sched", nm))
                    nm2 = nm2.rpartition(os.sep)[2]
                    shutil.move(os.path.join(tmpdir, "sched", nm),
                                os.path.join(DATA_PATH, "sched", nm2))
                    
                    exposong.main.main.load_sched(nm2)
        
        ### Theme Backgrounds ###
        imgs2rename = []
        if os.path.isdir(os.path.join(tmpdir,'theme/res')):
            for nm in os.listdir(os.path.join(tmpdir,'theme/res')):
                if not os.path.isfile(os.path.join(tmpdir, "theme/res", nm)):
                    continue
                exposong.log.debug("  Theme Image: %s", nm)
                if not os.path.exists(os.path.join(DATA_PATH, "theme/res", nm)):
                    shutil.move(os.path.join(tmpdir, "theme/res", nm),
                                os.path.join(DATA_PATH, "theme/res", nm))
                elif filecmp.cmp(os.path.join(tmpdir, "theme/res", nm),
                                 os.path.join(DATA_PATH, "theme/res", nm)):
                    pass # Skip if they are the same.
                else:
                    nm2 = find_freefile(os.path.join(DATA_PATH, "pres/res", nm))
                    shutil.move(os.path.join(tmpdir, "pres/res", nm), 
                                os.path.join(DATA_PATH, "pres/res", nm2))
                    imgs2rename.append((nm,nm2.rpartition(os.sep)[2]))
        
        ### Themes ###
        if os.path.isdir(os.path.join(tmpdir, "theme")):
            for nm in os.listdir(os.path.join(tmpdir,"theme")):
                if not os.path.isfile(os.path.join(tmpdir, "theme", nm)):
                    continue
                exposong.log.debug("  Theme: %s", nm)
                # Rename background images
                if len(imgs2rename) > 0:
                    infl = open(os.path.join(tmpdir,"theme",nm),"r")
                    outfl = open(os.path.join(tmpdir,"theme",nm+".1"),"w")
                    for ln in infl:
                        for img in imgs2rename:
                            ln = re.subn(r"\b"+img[0]+r"\b",img[1],ln)[0]
                        outfl.write(ln)
                    infl.close()
                    outfl.close()
                    shutil.move(os.path.join(tmpdir,"theme",nm+".1"),
                                os.path.join(tmpdir,"theme",nm))
                
                if not os.path.exists(os.path.join(DATA_PATH, "theme", nm)):
                    shutil.move(os.path.join(tmpdir, "theme", nm),
                                os.path.join(DATA_PATH, "theme", nm))
                    exposong.themeselect.themeselect.append(
                            os.path.join(DATA_PATH, "theme", nm))
                elif filecmp.cmp(os.path.join(tmpdir, "theme", nm),
                                 os.path.join(DATA_PATH, "theme", nm)):
                    pass #Skip if they are the same.
                    # Do we need to test if presentations have changed?
                else:
                    nm2 = find_freefile(os.path.join(DATA_PATH, "theme", nm))
                    nm2 = nm2.rpartition(os.sep)[2]
                    shutil.move(os.path.join(tmpdir, "theme", nm),
                                os.path.join(DATA_PATH, "theme", nm2))
                    exposong.themeselect.themeselect.append(
                            os.path.join(DATA_PATH, "theme", nm2))
    
    @classmethod
    def merge_menu(cls, uimanager):
        'Merge new values with the uimanager.'
        actiongroup = gtk.ActionGroup('export-import')
        actiongroup.add_actions([('import-expo', None,
                        _("_ExpoSong Data (.expo)..."), None,
                        _("Import a schedule, presentations or backgrounds"),
                        cls.import_dialog),
                ('import-song', None, _("ExpoSong Song (OpenLyrics Format)"),
                        None, None, cls.import_song_dialog),
                ('export-song', None, _("Current _Song"),
                        None, None, cls.export_song),
                ('export-sched', None,
                        _("_Current Schedule with Presentations..."),
                        None, None, cls.export_sched),
                ('export-lib', None, _("Whole _Library..."), None,
                        None, cls.export_lib),
                ('export-theme', None, _("Current _Theme..."), None,
                        None, cls.export_theme)
                ])
        
        action = actiongroup.get_action('export-theme')
        exposong.themeselect.themeselect.connect('changed',
                                                    cls()._export_theme_active,
                                                    action)
        action = actiongroup.get_action('export-song')
        exposong.preslist.preslist.get_selection().connect('changed',
                                                    cls()._export_song_active,
                                                    action)
        uimanager.insert_action_group(actiongroup, -1)
        
        #Had to use position='top' to put them above "Quit"
        cls.menu_merge_id = uimanager.add_ui_from_string("""
            <menubar name="MenuBar">
                <menu action="File">
                    <menu action='file-import'>
                        <menuitem action="import-expo" position="top" />
                        <menuitem action="import-song" position="top" />
                    </menu>
                    <menu action="file-export">
                        <menuitem action="export-song" />
                        <menuitem action="export-lib" />
                        <menuitem action="export-sched" />
                        <menuitem action="export-theme" />
                    </menu>
                </menu>
            </menubar>
            """)
    
    @classmethod
    def unmerge_menu(cls, uimanager):
        'Remove merged items from the menu.'
        uimanager.remove_ui(cls.menu_merge_id)
        
    @staticmethod
    def _export_theme_active(sel, action):
        "See wheter exporting is available for the selected theme."
        if sel.get_active():
            if not sel.get_active().is_builtin():
                action.set_sensitive(True)
                return
        action.set_sensitive(False)
    
    @staticmethod
    def _export_song_active(sel, action):
        "See whether exporting is available for the selected Song"
        if sel.count_selected_rows() > 0:
            (model, itr) = sel.get_selected()
            pres = model.get_value(itr, 0)
            if pres.get_type() == 'song':
                action.set_sensitive(True)
                return
        action.set_sensitive(False)
