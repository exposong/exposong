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
This file contains one or more generic slides to display as examples in the
interface.
"""

import exposong.theme

class _ExampleTextSlide(object):
    """
    A slide to draw as an example for the preview widget.
    """
    def __init__(self):
        object.__init__(self)
        self.id = '_example'
        self.body = [
                exposong.theme.Text('\n'.join([
                        "Amazing grace, how sweet the sound",
                        "That sav'd a wretch like me!",
                        "I once was lost, but now am found",
                        "Was blind, but now I see."]),
                    margin=0.04),
                ]
        self.foot = [exposong.theme.Text('\n'.join([
                        '"Amazing Grace"',
                        _('Written by: %s') % 'John Newton',
                        _('Copyright: %s') % 'Public Domain']),
                    margin=0.04)
                ]
    
    def get_body(self):
        "Returns the slide body text."
        return self.body
    
    def get_footer(self):
        "Returns the slide footer text."
        return self.foot
    
    def get_slide(self):
        return NotImplemented

# Add image or other example slides if needed.
