# Introduction #

Theme files are XML files which define background and text layout of an ExpoSong screen. The theme may reference external image files. XML format is a well defined internet standard with many [tutorials](http://www.learn-xml-tutorial.com/) available.

If you would like to see a feature added, [submit an issue](http://code.google.com/p/exposong/issues/entry).

# Elements #

### Positioning ###

Positional attributes, are positioned relative to the screen, and are in decimal format.

`x1` is where the left position of the object begins, and `x2` is the right position of the object. A value of `0.0` for `x1` and `x2` is touching the left side of the screen, and `1.0` is touching the right side, with intermediate values moving the object appropriately.

`y1` is the top position of the object, and `y2` is the bottom position of the element. A value of `0.0` for `y1` and `y2` is the top of the screen, and `1.0` is the bottom of the screen.


### Opacity ###

`opacity` is the level of visibility (the opposite of transparency). A value of `0.0` is completely transparent, and a value of `1.0` is visible so that it completely hides the items that are directly below. An intermediate value will adjust the level of visibility accordingly.

Note that images with invisible or partially visible portions will remain as such.

### Colors ###

A `color` can be a given name out of the [X11 Standard Color Names](http://en.wikipedia.org/wiki/X11_color_names), or an HTML like definition (e.g. #0fa, #00ffaa, or #0000ffffaaaa).

For more information, see [the parsing function](http://www.pygtk.org/docs/pygtk/class-gdkcolor.html#function-gdk--color-parse)

### Font ###

A `font` consists of a font family (such as serif, "Times New Roman", and can be a comma separated list: "sans serif,arial"), space-separated font style options (such as "bold italic"), and font size in points. Note that the size might be scaled down if the text does not fit.

## Backgrounds ##

`<background>` is a group of elements that will be drawn on the back of the screen, starting from the first item in the XML and moving to the last item.

All background elements have a [set location](ThemeFormat#Positioning.md).

### Solid ###

A `<solid>` background renders one color to the screen. The user should set the [color](ThemeFormat#Colors.md) attribute. A `<solid>` element also supports  an [opacity](ThemeFormat#Opacity.md) attribute.

Examples
```
<solid color='#a40' x1='0.0' x2='1.0' y1='0.0' x2='1.0' />
<solid color='#blue' opacity='0.6' x1='0.0' x2='1.0' y1='0.0' x2='0.8' />
```

### Gradient ###

A `<gradient>` background renders a gradual change from color to color. A gradient will have an `angle` that begins at the furthest edge of each side of the bounding rectangle. An `angle` of 0 is down, and moves counter-clockwise. The angle restarts every 360 numbers.

A `<gradient>` element contains multiple `<point>` subelements. The position is in decimal, where 0.0 is the starting location, and 1.0 is the end location. The user should set the [color](ThemeFormat#Colors.md) attribute. The `<point>` can also be set partially transparent using the [opacity](ThemeFormat#Opacity.md) attribute.

Example:
```
<gradient angle='45' x1='0.0' x2='1.0' y1='0.845' y2='1.0'>
  <point color='#222' stop='0.0' opacity='0.6' />
  <point color='#000' stop='1.0' opacity='0.0' />
</gradient>
```

### RadialGradient ###

A `<radial>` gradient background is similar to a [Gradient Background](ThemeFormat#Gradient.md), except that it is changes color in a circular pattern. It does not have an angle, but rather a center position (`cx` and `cy`), and a `length`. A `length` of 1.0 is the distance from the top-left corner of the screen to the bottom-right corner. `<points>` have the same definition as [Gradient](ThemeFormat#Gradient.md) `<points>`.

Example:
```
<radial length='0.5' cx='0.5' cy='0.5' x1='0.0' x2='1.0' y1='0.0' y2='1.0'>
  <point color='#222' stop='0.0' opacity='0.6' />
  <point color='#000' stop='1.0' opacity='0.0' />
</radial>
```

### Image ###

An `<image>` background renders an external image file. The `src` attribute defines the image filename located in "DATA\_PATH/theme/res/".

The `aspect` attribute, should be one of "fit", or "fill". If it is set to "fill", the image is cropped and resized so that the rectangle will have no whitespace. If set to "fit", the image will be resized inside the box so that the image is not cropped at all.

Example:
```
<img src='leaves.jpg' x1='0.0' x2='1.0' y1='0.0' y2='0.85' />
```

## Sections ##

`<sections>` define multiple locations on the screen and text formats. Right now the only sections are `<body>` and `<footer>`. The `<body>` is the primary area of the screen, and the `<footer>` contains meta information and is generally below the `<body>` on the screen.

Each section element can have a [font](ThemeFormat#Font.md) attribute that define font face, size, and style. Line `spacing` can also be set, where 1.0 is no space between each line, 2.0 is 1 line height between lines, and so on. Sections should also define [positioning attributes](ThemeFormat#Positioning.md).

Sections have a `<text>` subelement. A `<text>` element should define a `color` attribute ([ThemeFormat#Colors](ThemeFormat#Colors.md)).

Sections can also contain a `<shadow>`, which is a blurred text, slightly offset of the main text. A shadow should define a [color](ThemeFormat#Colors.md) attribute. The offset is a percentage of the height to going right or down. If you set offsetx=-1.0, it will move the shadow the height of 1 character to the left. A shadow also supports the [opacity](ThemeFormat#Opacity.md) attribute.

In addition to a `<shadow>`, a section can have an `<outline>`. An `<outline>` should define a [color](ThemeFormat#Colors.md) attribute. The `<outline>` also supports a `size` attribute in pixels around the text. The size is really only useful up to 2 or 3, anything higher and the user can no longer tell that it is an outline.

# Full Example #

```
<?xml version="1.0" ?>
<theme>
    <background>
        <img src='leaves.jpg' x1='0.0' x2='1.0' y1='0.0' y2='0.85' />
        <gradient angle='90' x1='0.0' x2='1.0' y1='0.845' y2='1.0'>
            <point color='#000' stop='0.0' />
            <point color='#222' stop='0.5' />
            <point color='#000' stop='1.0' />
        </gradient>
        <gradient angle='0' x1='0.0' x2='1.0' y1='0.845' y2='1.0'>
            <point color='#222' stop='0.0' opacity='0.6' />
            <point color='#000' stop='1.0' opacity='0.0' />
        </gradient>
        <solid color='#000' x1='0.0' x2='1.0' y1='0.84' y2='0.85' />
    </background>
    <sections>
        <body font='Verdana 24' x1='0.0' x2='1.0' y1='0.0' y2='0.85'>
            <text color='#fff' />
            <shadow color='#000' opacity='0.5' offsetx='.1' offsety='.1' />
        </body>
        <footer font='Arial 10' x1='0.0' x2='1.0' y1='0.85' y2='1.0'>
            <text color='#fff' />
            <shadow color='#000' opacity='0.8' offsetx='.1' offsety='.1' />
        </footer>
    </sections>
</theme>
```


# Distribution #

Themes will be installed using the "Import -> Schedule Data (.expo)" menu item, so the file will have to conform to ExpoSong library file format. A .expo file is a .tar.gz with the extension changed. It contains the same folder layout as the Data folder. Your file should look something like this, given the example above:

  * leaves.tar.gz
    * theme/
      * leaves.xml
      * res/
        * leaves.jpg

The file must be renamed to leaves.expo.