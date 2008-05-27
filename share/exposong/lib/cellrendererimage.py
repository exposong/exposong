#! /usr/bin/env python
import gtk
import gobject

'''
Cell Renderer for an Image.
'''

class CellRendererImage(gtk.GenericCellRenderer):
  '''
  Renders an image or animated image in a TreeView.
  '''
  __gproperties__ = {
    "image": (gobject.TYPE_OBJECT, "Image",
    "Image", gobject.PARAM_READWRITE),
  }

  def __init__(self):
    self.__gobject_init__()
    self.image = None

  def do_set_property(self, pspec, value):
    ''
    setattr(self, pspec.name, value)

  def do_get_property(self, pspec):
    ''
    return getattr(self, pspec.name)

  def func(self, model, path, iter, (image, tree)):
    ''
    if model.get_value(iter, 0) == image:
      self.redraw = 1
      cell_area = tree.get_cell_area(path, tree.get_column(0))
      tree.queue_draw_area(cell_area.x, cell_area.y, cell_area.width,
          cell_area.height)

  def animation_timeout(self, tree, image):
    'If image is animated.'
    if image.get_storage_type() == gtk.IMAGE_ANIMATION:
      self.redraw = 0
      image.get_data('iter').advance()
      model = tree.get_model()
      model.foreach(self.func, (image, tree))
      if self.redraw:
        gobject.timeout_add(image.get_data('iter').get_delay_time(),
            self.animation_timeout, tree, image)
      else:
        image.set_data('iter', None)

  def on_render(self, window, widget, background_area,cell_area, expose_area, flags):
    'Redraw part of the image.'
    if not self.image:
      return
    pix_rect = gtk.gdk.Rectangle()
    pix_rect.x, pix_rect.y, pix_rect.width, pix_rect.height = \
        self.on_get_size(widget, cell_area)

    pix_rect.x += cell_area.x
    pix_rect.y += cell_area.y
    pix_rect.width  -= 2 * self.get_property("xpad")
    pix_rect.height -= 2 * self.get_property("ypad")

    draw_rect = cell_area.intersect(pix_rect)
    draw_rect = expose_area.intersect(draw_rect)

    if self.image.get_storage_type() == gtk.IMAGE_ANIMATION:

      if not self.image.get_data('iter'):
        animation = self.image.get_animation()
        self.image.set_data('iter', animation.get_iter())
        gobject.timeout_add(self.image.get_data('iter').get_delay_time(),
          self.animation_timeout, widget, self.image)

      pix = self.image.get_data('iter').get_pixbuf()
    elif self.image.get_storage_type() == gtk.IMAGE_PIXBUF:
      pix = self.image.get_pixbuf()
    else:
      return
    window.draw_pixbuf(widget.style.black_gc, pix,
        draw_rect.x-pix_rect.x, draw_rect.y-pix_rect.y, draw_rect.x,
        draw_rect.y+2, draw_rect.width, draw_rect.height,
        gtk.gdk.RGB_DITHER_NONE, 0, 0)

  def on_get_size(self, widget, cell_area):
    'Request a size for the cell.'
    if not self.image:
      return 0, 0, 0, 0
    if self.image.get_storage_type() == gtk.IMAGE_ANIMATION:
      animation = self.image.get_animation()
      pix = animation.get_iter().get_pixbuf()
    elif self.image.get_storage_type() == gtk.IMAGE_PIXBUF:
      pix = self.image.get_pixbuf()
    else:
      return 0, 0, 0, 0
    pixbuf_width  = pix.get_width()
    pixbuf_height = pix.get_height()
    calc_width  = self.get_property("xpad") * 2 + pixbuf_width
    calc_height = self.get_property("ypad") * 2 + pixbuf_height
    x_offset = 0
    y_offset = 0
    if cell_area and pixbuf_width > 0 and pixbuf_height > 0:
      x_offset = self.get_property("xalign") * (cell_area.width -
        calc_width - self.get_property("xpad"))
      y_offset = self.get_property("yalign") * (cell_area.height -
        calc_height - self.get_property("ypad"))
    return x_offset, y_offset, calc_width, calc_height

gobject.type_register(CellRendererImage)

