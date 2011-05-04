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
Themes define the layout of a presentation screen.

The points will be based on percentages (0.0 - 1.0) to be compatible with all
screen sizes. Colors can be anything parsable by gtk.gdk.color_parse()
[http://library.gnome.org/devel/pygtk/stable/class-gdkcolor.html#function-gdk--color-parse].

Themes will support a flexible background layout system. Images, gradients, and
solid colors can be set for set region. Background images will be stored in
DATA_PATH/themes/bg.

Font size is the pixel height if the screen resolution is 1024x768. The font
will scale up for larger screens.

Shadow offsets are measure in percentage of font height. So an offset of 0.5
for point 12 font is 6 points.

Margins are measured in Pixels.
"""

import cairo
import gobject
import gtk
import gtk.gdk
import math
import operator
import os.path
import pango
from gtk.gdk import pixbuf_new_from_file as pb_new
from xml.etree import cElementTree as etree

from exposong import DATA_PATH

LEFT = pango.ALIGN_LEFT
CENTER = pango.ALIGN_CENTER
RIGHT = pango.ALIGN_RIGHT
TOP = 0
MIDDLE = 1
BOTTOM = 2

ASPECT_FIT = 1
ASPECT_FILL = 2

POS_MAP = {'x1': 0, 'y1': 1, 'x2': 2, 'y2': 3,
            0: 'x1', 1: 'y1', 2: 'x2', 3: 'y2',
            }


class Theme(object):
    """
    A theme item.
    """
    def __init__(self, filename=None, builtin=False):
        "Create a theme."
        self._builtin = builtin
        self.meta = {}
        self.backgrounds = []
        self.body = Section(type_='body', font="Sans 48",
                            pos=[0.0, 0.0, 1.0, 0.8],
                            expand=['header.y1','footer.y2'])
        self.footer = Section(type_='footer', font="Sans 12",
                              pos=[0.0, 0.8, 1.0, 1.0])
        if filename:
            self.filename = os.path.split(filename)[1]
            
            tree = etree.parse(filename)
            self.load(tree)
        else:
            self.filename = filename
    
    def get_footer_pos(self):
        "Return the position where the footer begins."
        if self.footer:
            return self.footer.pos[1]
        return 0.85
    
    def get_footer(self):
        "Return the theme footer."
        return self.footer

    def get_body(self):
        "Return the theme body."
        return self.body
    
    def get_title(self):
        "Return the name of the theme."
        if 'title' in self.meta:
            return self.meta['title']
        elif self.filename:
            return os.path.basename(self.filename).rstrip('.xml').title()
        else:
            return _("Unnamed Theme")
    
    def is_builtin(self):
        "Save/Editable only if not builtin."
        return self._builtin
    
    def load(self, tree):
        "Load the theme from an XML file."
        if isinstance(tree, etree.ElementTree):
            root = tree.getroot()
        else:
            root = tree
        meta = root.find("meta")
        if etree.iselement(meta):
            for el in meta:
                self.meta[el.tag] = el.text
        backgrounds = root.find(u'background')
        for bg in backgrounds.getchildren():
            bgobj = _Background.create_element(bg)
            if bgobj:
                self.backgrounds.append(bgobj)
        body = root.find(u'sections/body')
        if body:
            self.body = Section.from_xml(body)
        foot = root.find(u'sections/footer')
        if foot:
            self.footer = Section.from_xml(foot)
    
    def save(self):
        "Save theme to disk."
        if self.is_builtin():
            raise Exception("Builtin themes cannot be saved.")
        root = self.to_xml()
        tree = etree.ElementTree(root)
        # TODO This is saved in the current local directory.
        filename = os.path.join(DATA_PATH, "theme", self.filename)
        tree.write(filename, encoding='UTF-8')
    
    def to_xml(self):
        "Output the theme to a standardized format."
        root = etree.Element(u'theme')
        meta = etree.Element(u'meta')
        for tag, text in self.meta.iteritems():
            el = etree.Element(tag)
            el.text = text
            meta.append(el)
        root.append(meta)
        backgrounds = etree.Element(u'background')
        for e in self.backgrounds:
            backgrounds.append(e.to_xml())
        root.append(backgrounds)
        
        sections = etree.Element(u'sections')
        sections.append(self.body.to_xml())
        sections.append(self.footer.to_xml())
        root.append(sections)
        return root
    
    def render(self, ccontext, bounds, slide):
        "Render the theme to the screen."
        self.render_color(ccontext, bounds, '#000')
        for bg in self.backgrounds:
            bg.draw(ccontext, bounds)
        if slide:
            cont = slide.get_slide()
            if cont != NotImplemented:
                for t in cont:
                    try:
                        t.draw(ccontext, bounds, self.slide)
                    except AttributeError:
                        self.slide = self.body
                        self.slide.pos = [0.0, 0.0, 1.0, 1.0]
                        t.draw(ccontext, bounds, self.slide)
            else:
                expand = {}
                foots = slide.get_footer()
                for t in foots:
                    t.draw(ccontext, bounds, self.footer)
                if not foots:
                    for k in self.body.expand:
                        k2 = k.split(".")
                        if k2[0] == 'footer':
                            # Expand over the footer if it doesn't exist.
                            expand[k2[1]] = self.footer.pos[POS_MAP[k2[1]]]
                for t in slide.get_body():
                    t.draw(ccontext, bounds, self.body, expand)
    
    @classmethod
    def render_color(cls, ccontext, bounds, color):
        "Render a solid color on the screen."
        clr = gtk.gdk.color_parse(color)
        solid = cairo.SolidPattern(clr.red / 65535.0, clr.green / 65535.0,
                                   clr.blue / 65535.0)
        if len(bounds) == 2:
            ccontext.rectangle(0, 0, *bounds)
        elif len(bounds) == 4:
            ccontext.rectangle(*bounds)
        else:
            raise Exception("`bounds` must have 2 or 4 arguments.")
        ccontext.set_source(solid)
        ccontext.fill()


class _Renderable(object):
    """
    An abstract class for a drawing element.
    
    pos:    This is the position on the screen (0.0, 1.0).
            Example: [0.0, 1.0, 0.8, 1.0]
    rpos:   This is the real position on the screen (actual points).
            Example: [0, 800, 800, 1000]
    """
    def __init__(self, pos=None):
        ""
        if isinstance(pos, list) and len(pos) == 4:
            self.pos = pos
        else:
            self.pos = [0.0, 0.0, 1.0, 1.0]
    
    def parse_xml(self, el):
        "Defines variables based on XML values."
        self.pos = [float(el.get('x1', 0.0)), float(el.get('y1', 0.0)),
                    float(el.get('x2', 1.0)), float(el.get('y2', 1.0))]
    
    def to_xml(self, el):
        "Output to an XML Element."
        el.attrib['x1'] = str(self.pos[0])
        el.attrib['y1'] = str(self.pos[1])
        el.attrib['x2'] = str(self.pos[2])
        el.attrib['y2'] = str(self.pos[3])
    
    def get_pos(self):
        "Return the position."
        return self.pos
    
    def draw(self, ccontext, bounds):
        "Render the background to the context."
        if len(bounds) == 2:
            self.rpos = map(_product, bounds*2, self.get_pos())
        elif len(bounds) == 4:
            self.rpos = map(_product, bounds[-2:]*2, self.get_pos())
            self.rpos[0] += bounds[0]
            self.rpos[1] += bounds[1]
            self.rpos[2] += bounds[0]
            self.rpos[3] += bounds[1]
        else:
            raise Exception("`bounds` must have 2 or 4 elements")


class _Element(object):
    """
    An element in the XML.
    """
    
    @classmethod
    def create_element(cls, el):
        ""
        for c in cls.__subclasses__():
            if c.get_tag() == el.tag:
                return c.from_xml(el)
        return None
    
    @classmethod
    def from_xml(cls, el):
        "Creates an element"
        c = cls()
        c.parse_xml(el)
        return c
    
    @staticmethod
    def get_tag():
        "Return the XML tag name."
        return NotImplemented


class _Background(_Element):
    """
    A background object in the theme.
    """
    def __init__(self, name=_("Background")):
        self.name = name
    
    def parse_xml(self, el):
        "Defines variables based on XML values."
        if el.get('name'):
            self.name = el.get('name')
    
    def to_xml(self, el):
        "Output to an XML Element."
        el.attrib['name'] = self.name
    
    def get_name(self):
        if self.name != None:
            return self.name
        return "haha"

class ColorBackground(_Background, _Renderable):
    """
    A solid color background.
    """
    def __init__(self, color="#fff", alpha=1.0, pos=None, name=_("Color")):
        ""
        _Renderable.__init__(self, pos)
        _Background.__init__(self, name)
        self.color = color
        self.alpha = alpha
    
    def parse_xml(self, el):
        "Defines variables based on XML values."
        _Renderable.parse_xml(self, el)
        _Background.parse_xml(self, el)
        self.color = el.get('color', "#fff")
        self.alpha = float(el.get('opacity', 1.0))
    
    def to_xml(self):
        "Output to an XML Element."
        el = etree.Element(self.get_tag())
        _Renderable.to_xml(self, el)
        _Background.to_xml(self, el)
        el.attrib['color'] = self.color
        el.attrib['opacity'] = str(self.alpha)
        return el
    
    def draw(self, ccontext, bounds):
        "Render the background to the context."
        _Renderable.draw(self, ccontext, bounds)
        
        color = gtk.gdk.color_parse(self.color)
        solid = cairo.SolidPattern(color.red / 65535.0, color.green / 65535.0,
                                   color.blue / 65535.0, self.alpha)
        ccontext.rectangle(*self.rpos[:2] +
                           map(_subtract, self.rpos[2:4], self.rpos[:2]))
        ccontext.set_source(solid)
        ccontext.fill()
    
    @staticmethod
    def get_tag():
        "Return the XML tag name."
        return "solid"


class RadialGradientBackground(_Background, _Renderable):
    """
    A round gradient background.
    
    cpos:   Center point of the circle (from 0.0 to 1.0 within the boundaries).
    length: Radius of the circle.
    """
    def __init__(self, cpos=None, length=1.0, pos=None, name=_("Radial Gradient")):
        ""
        _Renderable.__init__(self, pos)
        _Background.__init__(self, name)
        if cpos != None:
            self.cpos = cpos[:]
        else:
            self.cpos = [0.0, 0.0]
        self.length = length
        self.stops = []
    
    def parse_xml(self, el):
        "Defines variables based on XML values."
        _Renderable.parse_xml(self, el)
        _Background.parse_xml(self, el)
        self.cpos[0] = float(el.get('cx', 1.0))
        self.cpos[1] = float(el.get('cy', 1.0))
        self.length = float(el.get('length', 1.0))
        
        self.stops = []
        for pt in el.getchildren():
            stop = GradientStop()
            stop.parse_xml(pt)
            self.stops.append(stop)
    
    def to_xml(self):
        "Output to an XML Element."
        el = etree.Element(self.get_tag())
        _Renderable.to_xml(self, el)
        _Background.to_xml(self, el)
        el.attrib['cx'] = str(self.cpos[0])
        el.attrib['cy'] = str(self.cpos[1])
        el.attrib['length'] = str(self.length)
        for s in self.stops:
            el.append(s.to_xml())
        return el
    
    def draw(self, ccontext, bounds):
        "Render the background to the context."
        _Renderable.draw(self, ccontext, bounds)
        
        rcpos = [0, 0]
        h = self.rpos[3] - self.rpos[1]
        w = self.rpos[2] - self.rpos[0]
        rcpos[0] = self.rpos[0] + w * self.cpos[0]
        rcpos[1] = self.rpos[1] + h * self.cpos[1]
        length = math.sqrt(math.pow(self.rpos[2] - self.rpos[0], 2) +
                           math.pow(self.rpos[3] - self.rpos[1], 2)) * self.length
        gradient = cairo.RadialGradient(rcpos[0], rcpos[1], 0.0,
                                        rcpos[0], rcpos[1], length)
        for stop in self.stops:
            clr = gtk.gdk.color_parse(stop.color)
            gradient.add_color_stop_rgba(stop.location, clr.red / 65535.0,
                                        clr.green / 65535.0, clr.blue / 65535.0,
                                        stop.alpha)
        ccontext.rectangle(*self.rpos[:2] +
                           map(_subtract, self.rpos[2:4], self.rpos[:2]))
        ccontext.set_source(gradient)
        ccontext.fill()
    
    @staticmethod
    def get_tag():
        "Return the XML tag name."
        return "radial"


class GradientBackground(_Background, _Renderable):
    """
    A gradient background.
    """
    def __init__(self, angle=0, pos=None, name=_("Gradient")):
        ""
        _Renderable.__init__(self, pos)
        _Background.__init__(self, name)
        self.angle = angle
        self.stops = []
    
    def parse_xml(self, el):
        "Defines variables based on XML values."
        _Renderable.parse_xml(self, el)
        _Background.parse_xml(self, el)
        self.angle = float(el.get('angle', 0))
        
        self.stops = []
        for pt in el.getchildren():
            stop = GradientStop()
            stop.parse_xml(pt)
            self.stops.append(stop)
    
    def to_xml(self):
        "Output to an XML Element."
        el = etree.Element(self.get_tag())
        _Renderable.to_xml(self, el)
        _Background.to_xml(self, el)
        el.attrib['angle'] = str(self.angle)
        for s in self.stops:
            el.append(s.to_xml())
        return el
    
    def draw(self, ccontext, bounds):
        "Render the background to the context."
        _Renderable.draw(self, ccontext, bounds)
        
        # Compute the offset of the angle
        cent = [self.rpos[0] / 2 + self.rpos[2] / 2,
                self.rpos[3] / 2 + self.rpos[1] / 2]
        diff = [abs(self.rpos[0] - self.rpos[2])/2,
                abs(self.rpos[1] - self.rpos[3])/2]
        offset = [0, 0]
        angle = self.angle * 2 * math.pi / 360
        if (self.angle + 90) % 360 < 180:
            offset[1] = diff[1]
        else:
            offset[1] = -diff[1]
        offset[0] = offset[1] * math.tan(angle)
        if abs(offset[0]) > diff[0]:
            if self.angle % 360 < 180:
                offset[0] = diff[0]
            else:
                offset[0] = -diff[0]
            offset[1] = offset[0] / math.tan(angle)
        
        gradient = cairo.LinearGradient(*map(_subtract, cent, offset) +
                                        map(_add, cent, offset))
        for stop in self.stops:
            clr = gtk.gdk.color_parse(stop.color)
            gradient.add_color_stop_rgba(stop.location, clr.red / 65535.0,
                                        clr.green / 65535.0, clr.blue / 65535.0,
                                        stop.alpha)
        ccontext.rectangle(*self.rpos[:2] +
                           map(_subtract, self.rpos[2:4], self.rpos[:2]))
        ccontext.set_source(gradient)
        ccontext.fill()
    
    @staticmethod
    def get_tag():
        "Return the XML tag name."
        return "gradient"


class GradientStop(_Element):
    """
    A location with a color in a gradient background.
    """
    def __init__(self, location=0.5, color='#fff', alpha=1.0):
        ""
        self.location = location
        self.color = color
        self.alpha = alpha
    
    def parse_xml(self, el):
        "Define variables based on XML values."
        assert el.tag == 'point'
        if 'stop' in el.attrib:
            self.location = float(el.attrib['stop'])
        if 'color' in el.attrib:
            self.color = el.attrib['color']
        if 'opacity' in el.attrib:
            self.alpha = float(el.attrib['opacity'])
    
    def to_xml(self):
        el = etree.Element("point")
        el.attrib['stop'] = str(self.location)
        el.attrib['color'] = self.color
        el.attrib['opacity'] = str(self.alpha)
        return el


class ImageBackground(_Background, _Renderable):
    """
    An image background.
    
    src:    The image file location, relative to "DATA_PATH/theme/res/".
    aspect: If it is set to "fill", the image is cropped and resized so that the
            rectangle will have no whitespace. If set to "fit", the image will
            be resized inside the box so that the image is not cropped at all.
    """
    def __init__(self, src=None, pos=None, aspect=ASPECT_FILL, name=_("Image")):
        ""
        _Renderable.__init__(self, pos)
        _Background.__init__(self, name)
        self.src = src
        self.aspect = aspect
        self._original = None
        self._cache = {}
    
    def parse_xml(self, el):
        "Defines variables based on XML values."
        _Renderable.parse_xml(self, el)
        _Background.parse_xml(self, el)
        self.src = el.get('src')
        self.aspect = get_aspect_const(el.get('aspect'), ASPECT_FILL)
    
    def to_xml(self):
        "Output to an XML Element."
        el = etree.Element(self.get_tag())
        _Renderable.to_xml(self, el)
        _Background.to_xml(self, el)
        el.attrib['src'] = self.src
        el.attrib['aspect'] = get_aspect_key(self.aspect == ASPECT_FILL)
        return el
    
    def get_filename(self):
        return os.path.join(DATA_PATH, 'theme', 'res', self.src)
    
    def reset_cache(self):
        self._original = None
        self._cache = {}
    
    def load(self, size):
        ""
        if not self._original:
            try:
                self._original = pb_new(self.get_filename())
            except gobject.GError:
                exposong.log.error('Could not find "%s".', self.src)
                return False
        
        size[:] = get_size(self._original, size, self.aspect)
        skey = 'x'.join(map(str, size))
        if skey not in self._cache:
            self._cache[skey] = scale_image(self._original, size, self.aspect)
        return self._cache[skey]
    
    def draw(self, ccontext, bounds):
        "Render the background to the context."
        _Renderable.draw(self, ccontext, bounds)
        
        #ccontext.rectangle(*self.rpos[:2] +
        #                   map(_subtract, self.rpos[2:4], self.rpos[:2]))
        size = map(_subtract, self.rpos[2:4], self.rpos[:2])
        
        img = self.load(size)
        pos = [(self.rpos[0] + self.rpos[2] - size[0])/2,
               (self.rpos[1] + self.rpos[3] - size[1])/2]
        if img:
            ccontext.set_source_pixbuf(img, *pos)
            ccontext.paint()
    
    @staticmethod
    def get_tag():
        "Return the XML tag name."
        return "image"


class Section(_Element):
    """
    A part of the screen with text.
    
    type_:  Can currently be one of "body" or "footer".
    font:   A description according to the format listed at
            http://library.gnome.org/devel/pygtk/stable/class-pangofontdescription.html#constructor-pangofontdescription
            The size will be scaled as if the screen was 1024x768. Larger
            screens will have larger font sizes for consistency among
            setups.
    """
    def __init__(self, type_=None, font="Sans 24", color="#fff", align=CENTER,
                 valign=MIDDLE, spacing=1.0, outline_color=None, outline_size=0,
                 shadow_color=None, shadow_opacity=0.4, shadow_offset=None,
                 pos=None, expand=None):
        _Element.__init__(self)
        assert type_ in (None, 'body', 'footer')
        self.type_ = type_
        if isinstance(pos, list) and len(pos) == 4:
            self.pos = pos
        else:
            self.pos = [0.0, 1.0, 0.0, 1.0]
        if expand:
            self.expand = expand
        else:
            self.expand = []
        
        self.font = font
        self.color = color
        self.spacing = spacing
        self.align = align
        self.valign = valign
        
        self.outline_color = outline_color
        self.outline_size = outline_size
        
        self.shadow_color = shadow_color
        self.shadow_opacity = shadow_opacity
        if shadow_offset:
            self.shadow_offset = shadow_offset
        else:
            self.shadow_offset = [0.1, 0.1]
    
    def parse_xml(self, el):
        "Defines variables based on XML values."
        self.type_ = el.tag
        self.pos = [float(el.get('x1', '0.0')), float(el.get('y1', '0.0')),
                    float(el.get('x2', '1.0')), float(el.get('y2', '1.0'))]
        self.expand = el.get('expand', '').split(',')
        self.font = el.get('font', 'Sans 24')
        self.spacing = float(el.get('spacing', '1.0'))
        align = get_align_const(el.get('align'))
        if align != -1:
            self.align = align
        valign = get_valign_const(el.get('valign'))
        if valign != -1:
            self.valign = valign
        
        el2 = el.find('text')
        if el2 != None:
            self.color = el2.get('color', '#fff')
        el2 = el.find('outline')
        if el2 != None:
            self.outline_color = el2.get('color', None)
            self.outline_size = float(el2.get('size', 1))
        el2 = el.find('shadow')
        if el2 != None:
            self.shadow_color = el2.get('color', '#000')
            self.shadow_opacity = float(el2.get('opacity', 0.4))
            self.shadow_offset = [float(el2.get('offsetx', 0.1)),
                                  float(el2.get('offsety', 0.1))]
    
    def to_xml(self):
        "Output to an XML Element."
        el = etree.Element(self.type_)
        el.attrib['font'] = self.font
        el.attrib['spacing'] = str(self.spacing)
        el.attrib['align'] = get_align_key(self.align)
        el.attrib['align'] = get_valign_key(self.valign)
        el.attrib['x1'] = str(self.pos[0])
        el.attrib['y1'] = str(self.pos[1])
        el.attrib['x2'] = str(self.pos[2])
        el.attrib['y2'] = str(self.pos[3])
        if self.expand:
            el.attrib['expand'] = ','.join(self.expand)
        el2 = etree.Element('text')
        el2.attrib['color'] = self.color
        el.append(el2)
        if self.shadow_color != None:
            el2 = etree.Element('shadow')
            el2.attrib['color'] = self.shadow_color
            el2.attrib['opacity'] = str(self.shadow_opacity)
            el2.attrib['offsetx'] = str(self.shadow_offset[0])
            el2.attrib['offsety'] = str(self.shadow_offset[1])
            el.append(el2)
        if self.outline_color != None:
            el2 = etree.Element('outline')
            el2.attrib['color'] = self.outline_color
            el2.attrib['size'] = str(self.outline_size)
            el.append(el2)
        return el


class _RenderableSection(_Renderable):
    """
    An abstract class defining objects that can be created from presentation types.
    """
    def __init__(self, align=None, valign=None, margin=0, pos=None):
        _Renderable.__init__(self, pos)
        self.align = align
        self.valign = valign
        self.margin = margin
    
    def get_pos(self):
        'Returns the position.'
        if self._section is None:
            return self.pos
        pos = self._section.pos[:]
        for k,v in self._expand.iteritems():
            pos[POS_MAP[k]] = v
        h = pos[3] - pos[1]
        w = pos[2] - pos[0]
        pos[0] += w * self.pos[0]
        pos[1] += h * self.pos[1]
        pos[2] -= w * (1.0 - self.pos[2])
        pos[3] -= h * (1.0 - self.pos[3])
        return pos
    
    def draw(self, ccontext, bounds, section, expand={}):
        "Render to a Cairo Context."
        self._section = section
        self._expand = expand
        _Renderable.draw(self, ccontext, bounds)
        self._section = self._expand = None
        
        self.rpos[0] += self.margin
        self.rpos[1] += self.margin
        self.rpos[2] -= self.margin
        self.rpos[3] -= self.margin
        assert self.rpos[0] < self.rpos[2]
        assert self.rpos[1] < self.rpos[3]

# Text() and Image() classes are to be called by slides 

class Text(_RenderableSection):
    """
    A textual area that will be rendered to the screen.
    
    The text can be formatted according to the Pango Markup Language
    (http://www.pygtk.org/docs/pygtk/pango-markup-language.html).
    """
    def __init__(self, markup, align=None, valign=None, margin=0,
                 pos=None):
        _RenderableSection.__init__(self, align, valign, margin, pos)
        self.markup = markup
    
    def draw(self, ccontext, bounds, section, expand={}):
        "Render to a Cairo Context."
        _RenderableSection.draw(self, ccontext, bounds, section, expand)
        screen_height = (self.rpos[3] + self.margin) / self.pos[3]
        
        layout = ccontext.create_layout()
        layout.set_width(int(self.rpos[2] - self.rpos[0])*pango.SCALE)
        if section.font:
            font_descr = pango.FontDescription(section.font)
        else:
            font_descr = pango.FontDescription("Sans 48")
        font_descr.set_size(int(font_descr.get_size() * screen_height / 768))
        layout.set_font_description(font_descr)
        layout.set_spacing(int((section.spacing - 1.0) * font_descr.get_size()))
        
        if self.align != None:
            layout.set_alignment(self.align)
        elif section.align != None:
            layout.set_alignment(section.align)
        else:
            layout.set_alignment(CENTER)
        
        layout.set_markup(self.markup)
        
        while layout.get_pixel_size()[1] > self.rpos[3] - self.rpos[1]:
            font_descr.set_size(int(font_descr.get_size()*0.95))
            layout.set_spacing(int((section.spacing - 1.0) * font_descr.get_size()))
            layout.set_font_description(font_descr)
        
        if self.valign != None:
            valign = self.valign
        elif section.valign != None:
            valign = section.valign
        else:
            valign = MIDDLE
        
        if valign == TOP:
            top = self.rpos[1]
        elif valign == BOTTOM:
            top = self.rpos[3] - layout.get_pixel_size()[1]
        else: # Default to Middle
            top = self.rpos[1] + (self.rpos[3] - self.rpos[1]) / 2 - \
                  layout.get_pixel_size()[1] / 2
        
        if section.shadow_color:
            clr = gtk.gdk.color_parse(section.shadow_color)
            ccontext.set_source_rgba(clr.red / 65535.0, clr.green / 65535.0,
                                     clr.blue / 65535.0,
                                     section.shadow_opacity * 0.05)
            sz = font_descr.get_size() / pango.SCALE
            center = [self.rpos[0] + sz * section.shadow_offset[0],
                             top + sz * section.shadow_offset[1]]
            for x in range(-2, 3, 1):
                for y in range(-2, 3, 1):
                    ccontext.move_to(center[0]+x, center[1]+y)
                    ccontext.show_layout(layout)
        if section.outline_color:
            clr = gtk.gdk.color_parse(section.outline_color)
            ccontext.set_source_rgb(clr.red / 65535.0, clr.green / 65535.0,
                                    clr.blue / 65535.0)
            offset = int(section.outline_size)
            for x in range(-offset, offset + 1, 1):
                for y in range(-offset, offset + 1, 1):
                    ccontext.move_to(self.rpos[0]+x, top+y)
                    ccontext.show_layout(layout)
        
        clr = gtk.gdk.color_parse(section.color)
        ccontext.set_source_rgba(clr.red / 65535.0, clr.green / 65535.0,
                                 clr.blue / 65535.0, 1.0)
        ccontext.move_to(self.rpos[0], top)
        ccontext.show_layout(layout)


class Image(_RenderableSection):
    """
    An image to be rendered on the screen.
    """
    def __init__(self, src, aspect=ASPECT_FIT, align=None, valign=None,
                 margin=0, pos=None):
        _RenderableSection.__init__(self, align, valign, margin, pos)
        self.src = src
        self.aspect = aspect
        self._original = None
        self._cache = {'x': None}
    
    def load(self, size):
        "Loads an image based on a requested size [width, height]."
        if not self.src or not os.path.isfile(self.src):
            return False
        if not self._original:
            try:
                self._original = pb_new(self.src)
            except gobject.GError:
                exposong.log.error('Could not find "%s".', self.src)
                return False
        
        skey = 'x'.join(map(str, get_size(self._original, size, self.aspect)))
        if skey not in self._cache:
            self._cache[skey] = scale_image(self._original, size, self.aspect)
        return self._cache[skey]
    
    def draw(self, ccontext, bounds, section, expand={}):
        "Render to a Cairo Context."
        _RenderableSection.draw(self, ccontext, bounds, section, expand)
        
        size = map(_subtract, self.rpos[2:4], self.rpos[:2])
        valign = align = None
        
        img = self.load(size)
        if not img:
            return False
        
        if self.valign != None:
            valign = self.valign
        elif section.valign != None:
            valign = section.valign
        
        if valign == TOP:
            top = self.rpos[1]
        elif valign == BOTTOM:
            top = self.rpos[3] - img.get_height()
        else: # Default to Middle
            top = self.rpos[1] + (self.rpos[3] - self.rpos[1]) / 2 - \
                  img.get_height() / 2
        
        if self.align != None:
            align = self.align
        elif section.align != None:
            align = section.align
        
        if align == LEFT:
            left = self.rpos[0]
        elif align == RIGHT:
            left = self.rpos[2] - img.get_width()
        else: # Default to Center
            left = self.rpos[0] + (self.rpos[2] - self.rpos[0]) / 2 - \
                  img.get_width() / 2
        
        if img:
            ccontext.set_source_pixbuf(img, left, top)
            ccontext.paint()
    
    def __deepcopy__(self, memo={}):
        dup = self.__class__(self.src, self.aspect, self.align, self.valign,
                             self.margin, self.pos[:])
        return dup

################################################
## Public Functions to help with manipulating ##
## align, valign, and aspect variables.       ##
################################################

def get_align_const(align, default=None):
    "Get the alignment constant."
    global LEFT, CENTER, RIGHT
    if align in ('left', _('Left'), LEFT):
        return LEFT
    elif align in ('center', _('Center'), CENTER):
        return CENTER
    elif align in ('right', _('Right'), RIGHT):
        return RIGHT
    return default
def get_align_key(align, default=''):
    "Get the alignment XML value."
    global LEFT, CENTER, RIGHT
    if align in ('left', _('Left'), LEFT):
        return 'left'
    elif align in ('center', _('Center'), CENTER):
        return 'center'
    elif align in ('right', _('Right'), RIGHT):
        return 'right'
    return default
def get_align_text(align, default=''):
    "Get the alignment translated value for the UI."
    global LEFT, CENTER, RIGHT
    if align in ('left', _('Left'), LEFT):
        return _('Left')
    elif align in ('center', _('Center'), CENTER):
        return _('Center')
    elif align in ('right', _('Right'), RIGHT):
        return _('Right')
    return default

def get_valign_const(valign, default=None):
    "Get the vertical alignment constant."
    global TOP, MIDDLE, BOTTOM
    if valign in ('top', _('Top'), TOP):
        return TOP
    elif valign in ('middle', _('Middle'), MIDDLE):
        return MIDDLE
    elif valign in ('bottom', _('Bottom'), BOTTOM):
        return BOTTOM
    return default
def get_valign_key(valign, default=''):
    "Get the vertical alignment XML value."
    global TOP, MIDDLE, BOTTOM
    if valign in ('top', _('Top'), TOP):
        return 'top'
    elif valign in ('middle', _('Middle'), MIDDLE):
        return 'middle'
    elif valign in ('bottom', _('Bottom'), BOTTOM):
        return 'bottom'
    return default
def get_valign_text(valign, default=''):
    "Get the alignment translated value for the UI."
    global TOP, MIDDLE, BOTTOM
    if valign in ('top', _('Top'), TOP):
        return _('Top')
    elif valign in ('middle', _('Middle'), MIDDLE):
        return _('Middle')
    elif valign in ('bottom', _('Bottom'), BOTTOM):
        return _('Bottom')
    return default

def get_aspect_const(aspect, default=None):
    "Get the image aspect constant."
    global ASPECT_FIT, ASPECT_FILL
    if aspect in ('fit', _('Fit'), ASPECT_FIT):
        return ASPECT_FIT
    elif aspect in ('fill', _('Fill'), ASPECT_FILL):
        return ASPECT_FILL
    return default
def get_aspect_key(aspect, default=''):
    "Get the image aspect XML value."
    global ASPECT_FIT, ASPECT_FILL
    if aspect in ('fit', _('Fit'), ASPECT_FIT):
        return 'fit'
    elif aspect in ('fill', _('Fill'), ASPECT_FILL):
        return 'fill'
    return default
def get_aspect_text(aspect, default=''):
    "Get the image aspect translated value for UI."
    global ASPECT_FIT, ASPECT_FILL
    if aspect in ('fit', _('Fit'), ASPECT_FIT):
        return _('Fit')
    elif aspect in ('fill', _('Fill'), ASPECT_FILL):
        return _('Fill')
    return default


##########################
#### Helper functions ####

def get_size(pb, size, aspect=None):
    """Gets the size according to the aspect ratio for a resized image."""
    if aspect == ASPECT_FIT:
        w, h = map(int, size)
        scaleW = float(size[0]) / pb.get_width()
        scaleH = float(size[1]) / pb.get_height()
        if scaleH < scaleW:
            scale = scaleH
        else:
            scale = scaleW
        w = int(pb.get_width() * scale)
        h = int(pb.get_height() * scale)
        return map(int, [w, h])
    else:
        return size

def scale_image(pb, size, aspect=None):
    """Scales the pixbuf (pb) to size.
    
    size:   [width, height]
    aspect: Any of the following:
             * None - scales width and height individually
             * ASPECT_FIT - size will be smaller
             * ASPECT_FILL - image will scale up
    """
    npb = None
    if aspect == ASPECT_FIT:
        w, h = map(int, size)
        scaleW = float(size[0]) / pb.get_width()
        scaleH = float(size[1]) / pb.get_height()
        if scaleH < scaleW:
            scale = scaleH
        else:
            scale = scaleW
        w = int(pb.get_width() * scale)
        h = int(pb.get_height() * scale)
        npb = gtk.gdk.Pixbuf(pb.get_colorspace(), pb.get_has_alpha(),
                             pb.get_bits_per_sample(),
                             int(w), int(h))

        pb.scale(npb, 0, 0, w, h, 0, 0, scale, scale,
                 gtk.gdk.INTERP_BILINEAR)
    elif aspect == ASPECT_FILL:
        npb = gtk.gdk.Pixbuf(pb.get_colorspace(), pb.get_has_alpha(),
                             pb.get_bits_per_sample(),
                             int(size[0]), int(size[1]))
        w, h = map(int, size)
        scaleW = float(size[0]) / pb.get_width()
        scaleH = float(size[1]) / pb.get_height()
        if scaleH > scaleW:
            scale = scaleH
        else:
            scale = scaleW
        w = int(pb.get_width() * scale)
        h = int(pb.get_height() * scale)
        
        pb.scale(npb, 0, 0, int(size[0]), int(size[1]), int(size[0] - w) / 2,
                 int(size[1] - h) / 2, scale, scale, gtk.gdk.INTERP_BILINEAR)
    else:
        npb = pb.scale_simple(int(size[0]), int(size[1]),
                              gtk.gdk.INTERP_BILINEAR)
    return npb

def _product(*args):
    "Multiply all arguments."
    return reduce(operator.mul, args)

def _subtract(*args):
    "Subtract a from b."
    return reduce(operator.sub, args[:2])

def _add(*args):
    "Add all arguments."
    return reduce(operator.add, args[:2])

