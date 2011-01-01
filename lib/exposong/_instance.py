#
# vim: ts=4 sw=4 expandtab ai:
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

"""
Only allow one instance of ExpoSong, and send signals to the instance.

This class is run on a local port to prevent more than one instance from
opening, and to allow users or other programs to send signals from the command
line (e.g. `exposong --next` will move to the next slide).
"""

# http://code.activestate.com/recipes/531824-chat-server-client-using-selectselect/

import gobject
import gtk
import select
import socket
import sys

import exposong


TIMEOUT = .1

HOST, PORT = ('127.0.0.24', 3890)

class SingleInstance(object):
    """
    Prevent multiple instances of ExpoSong.
    """
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def serve(self):
        try:
            self.socket.bind((HOST, PORT))
        except socket.error:
            raise ExposongInstanceError
        self.socket.listen(2)
        gobject.timeout_add(TIMEOUT*1000, self.listen)
    
    def listen(self):
        "Attempt to detect any attempted communications."
        try:
            inready, n1, n2 = select.select([self.socket], [], [], TIMEOUT)
        except socket.error, e:
            return
        for s in inready:
            if s == self.socket:
                client, addr = self.socket.accept()
                exposong.log.debug('Received connection %d from %s.', client.fileno(), addr)
                data = client.recv(1024)
                while data:
                    self.handle_request(client, data)
                    data = client.recv(1024)
                client.close()
        gobject.timeout_add(TIMEOUT*1000, self.listen)
    
    def handle_request(self, conn, data):
        if data == 'Is ExpoSong?':
            conn.send('Yes')
        else:
            exposong.log.debug("Unknown Data on port.")
    
    
    def send(self):
        "Send something to another instance."
        self.socket.settimeout(TIMEOUT*3)
        self.socket.connect((HOST, PORT))
        self.socket.send('Is ExpoSong?')
        data = self.socket.recv(1024)
        if data == 'Yes':
            msg = _("ExpoSong is already running.")
            dlg = gtk.MessageDialog(type=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK,
                                    message_format=msg)
            dlg.run()
            dlg.destroy()
            return True
        else:
            return False
    
    def __del__(self):
        self.socket.close()


class ExposongInstanceError(Exception):
    pass


# Note: If an application is using the port, and we choose a higher port,
#       ExpoSong will be able to start twice.
inst = SingleInstance()
while True:
    try:
        inst.serve()
        break
    except ExposongInstanceError:
        if inst.send():
            sys.exit(0)
        PORT += 10000
