# Introduction #

A plugin must inherit from the [Plugin class](http://code.google.com/p/exposong/source/browse/trunk/share/exposong/lib/exposong/plugins/__init__.py).

The method get\_version() should return a tuple containing the version number of the plugin (this isn't necessarily important at the moment, but will be handy for future). Built in plugins will be version 1.0, but may follow ExpoSong's version.

The method get\_description() should return a string description.


# Abstract Classes #

All plugins should inherit from the classes in [\_abstract.py](http://code.google.com/p/exposong/source/browse/trunk/share/exposong/lib/exposong/plugins/_abstract.py) and implement the functions to hook into the program.

## Menu ##

Manipulate the menu items.

  * `merge_menu(uimanager)`: uimanager is a [gtk.UIManager](http://pygtk.org/docs/pygtk/class-gtkuimanager.html). Follow the code in [lyric.py](http://code.google.com/p/exposong/source/browse/trunk/share/exposong/lib/exposong/plugins/lyric.py) in the plugins folder for more help.
  * `unmerge_menu(uimanager)`: If exposong ever can uninstall plugins while running, this will uninstall the menu. Use [remove\_ui](http://pygtk.org/docs/pygtk/class-gtkuimanager.html#method-gtkuimanager--remove-ui) to uninstall menu items.


## Presentation ##

The only method that has to be implemented is init(self, dom, filename), but the method can call the method from the super class after it has been implemented.


### Slide ###

This is a subclass of Presentation, and should only be reimplemented if necessary.


## Schedule ##

Add builtin schedules to the schedule list.

  * `schedule_name()`: return the name as a string.
  * `filter_pres(self, pres)`: return `True` if `pres` is in the list.


## Screen ##

Draw or add text to a part of the screen. Priority will determine the order of being called. Priority less than 0 is for things such as background, where priority of greater than 0 is for text. Higher priority will be drawn on top of lower priorities.

These methods do not have to be overridden, unless they are to be used.

  * `draw(surface, priority=1)`: Draw anywhere on the screen. Example usage: Notifications, images or possibly videos.