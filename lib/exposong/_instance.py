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
Prevent multiple instances of ExpoSong.
"""

# http://code.activestate.com/recipes/531824-chat-server-client-using-selectselect/

import gobject
import select
import socket
import sys


TIMEOUT = 0.05

class SingleInstance(object):
    """
    Prevent multiple instances of ExpoSong.
    """
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(0)
        try:
            self.socket.bind(('127.0.0.24', 3890))
        except socket.error:
            print "Another instance is running. Quitting."
            sys.exit(-1)
        #gobject.timeout_add(200, self._listen)
        self.socket.listen(1)
    
    def listen(self):
        "Attempt to detect any attempted communications."
        try:
            inready, outready, exready = select.select([self.socket], [], [], TIMEOUT)
        except socket.error, e:
            return
        
        for s in inready:
            if s == self.socket:
                client, addr = self.socket.accept()
                print 'Received connection %d from %s.' % (client.fileno(), addr)
        
    def send(self):
        "Send something to another instance."
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def __del__(self):
        self.socket.close()

inst = SingleInstance()

import time
for i in range(1000):
    #time.sleep(0.01)
    if i % 50 == 0: print 'x'
    inst.listen()

