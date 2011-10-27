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

"""
Only allow one instance of ExpoSong, and send signals to the instance.

This class is run on a local port to prevent more than one instance from
opening, and to allow users or other programs to send signals from the command
line (e.g. `exposong --next` will move to the next slide).
"""

# http://code.activestate.com/recipes/531824-chat-server-client-using-selectselect/

import select
import socket
import sys

import exposong
# Imports from ExpoSong classes are done when they are needed, so that loading
# is completed in the correct order.


TIMEOUT = .07

HOST, PORT = ('127.0.0.24', 3890)

class SingleInstance(object):
    """
    Prevent multiple instances of ExpoSong, and send signals to the running instance.
    """
    def __init__(self):
        pass
    def open(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    def close(self):
        self.socket.close()
    def reopen(self):
        self.close()
        self.open()
    
    def serve(self):
        "Open the port, and listen for commands."
        import gobject
        try:
            self.socket.bind((HOST, PORT))
        except socket.error:
            raise ExposongInstanceError
        self.socket.listen(4)
        gobject.timeout_add(int(TIMEOUT*1000), self.listen)
    
    def listen(self):
        "Attempt to detect any attempted communications."
        import gobject
        try:
            inready, n1, n2 = select.select([self.socket], [], [], TIMEOUT)
        except socket.error, e:
            return
        for s in inready:
            if s == self.socket:
                client, addr = self.socket.accept()
                exposong.log.debug('Received connection %d from %s.', client.fileno(), addr)
                try:
                    data = client.recv(1024)
                    while data:
                        self.handle_request(client, data)
                        data = client.recv(1024)
                except socket.error:
                    pass
                client.close()
        gobject.timeout_add(int(TIMEOUT*1000), self.listen)
    
    def handle_request(self, conn, data):
        "Handles received data from listen()."
        if data == 'Is ExpoSong?':
            conn.send('Yes')
        elif data == 'Next':
            import exposong.slidelist
            exposong.slidelist.slidelist.next_slide()
        elif data == 'Prev':
            import exposong.slidelist
            exposong.slidelist.slidelist.prev_slide()
        elif data == 'Show':
            import exposong.screen
            exposong.screen.screen.show()
        elif data == 'Hide':
            import exposong.screen
            exposong.screen.screen.hide()
        elif data == 'Black':
            import exposong.screen
            exposong.screen.screen.to_black()
        elif data == 'Background':
            import exposong.screen
            exposong.screen.screen.to_background()
        elif data == 'Logo':
            import exposong.screen
            exposong.screen.screen.to_logo()
        elif data.startswith('Import '):
            import exposong.plugins.export_import
            filename = data.partition(' ')[2]
            exposong.plugins.export_import.ExportImport.import_file(filename)
        else:
            import exposong
            exposong.log.debug('Unknown Data on port.')
    
    def _send(self, text, recv=False):
        "Send data to a running instance of ExpoSong"
        self.socket.settimeout(TIMEOUT*3)
        self.socket.connect((HOST, PORT))
        self.socket.send(text)
        if recv:
            return self.socket.recv(1024)
    
    def remote(self):
        self.open()
        if exposong.options.import_:
            try:
                self._send('Import %s' % exposong.options.import_)
                return True
            except socket.timeout:
                self.reopen()
        
        try:
            if exposong.options.next:
                self._send('Next')
            elif exposong.options.prev:
                self._send('Prev')
            elif exposong.options.show:
                self._send('Show')
            elif exposong.options.hide:
                self._send('Hide')
            elif exposong.options.black:
                self._send('Black')
            elif exposong.options.background:
                self._send('Background')
            elif exposong.options.logo:
                self._send('Logo')
            else:
                return False
        except socket.timeout:
            self.reopen()
            import gtk
            msg = _('ExpoSong is not running.')
            dlg = gtk.MessageDialog(type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK,
                                    message_format=msg)
            dlg.run()
            dlg.destroy()
        return True
    
    def is_running(self):
        "Send something to another instance."
        import gtk
        self.socket.settimeout(TIMEOUT*3)
        self.socket.connect((HOST, PORT))
        if self._send('Is ExpoSong?', True) != 'Yes':
            return False
        
        msg = _('ExpoSong is already running.')
        dlg = gtk.MessageDialog(type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK,
                                message_format=msg)
        dlg.run()
        dlg.destroy()
        return True
    
    def __del__(self):
        self.socket.close()


class ExposongInstanceError(Exception):
    pass

class ExposongNotRunningError(Exception):
    pass

# Note: If an application is using the port, and we choose a higher port,
#       ExpoSong will be able to start twice.
inst = SingleInstance()
if inst.remote():
    sys.exit(0)
else:
    while True:
        try:
            inst.serve()
            break
        except ExposongInstanceError:
            if inst.is_running():
                sys.exit(0)
            PORT += 10000
