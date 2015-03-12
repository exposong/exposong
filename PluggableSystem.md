Please see PluginMethods for the current status of available methods. All plugins should implement classes in [\_abstract.py](http://code.google.com/p/exposong/source/browse/trunk/share/exposong/lib/exposong/plugins/_abstract.py).

Feel free to modify this page if you have the ability to, or comments may be added to the bottom.


# Discussion #

I've made an attempt to extend the presentation types to have a more appropriate editor, and I don't think it's feasible without first look into making a plugin/extension system available.

Since I'm doing the program in an object-oriented fashion, I'm thinking the best way to do this is with object inheritance. Multiple classes can be created as a base, and creating a plugin is just a matter of creating classes and overwriting the functions that need to be overwritten.

I can take some of the ideas I have in ptype/init.py for the presentation type, but I'd like it to be pluggable in more places than just presentation type.


# Uses #

Of course, presentation types will be plugins.

Because it would be useful to have video backgrounds in the future, all other background rendering should probably be in a plugin as well. It might be good to move a good majority of all presentation rendering to a plugin, because different presentation types will need different items displayed (lyrics will need ccli, author, etc), and maybe even completely different layouts. I would still assume that we need the basic rendering left in the core though.

Any file import from other formats will be a plugin, and maybe even importing/exporting the full library.


# Requirements #

  * There will need to be a method to add items to the menu. (See [add\_ui\_from\_string](http://www.pygtk.org/docs/pygtk/class-gtkuimanager.html#method-gtkuimanager--add-ui-from-string) and [remove\_ui](http://www.pygtk.org/docs/pygtk/class-gtkuimanager.html#method-gtkuimanager--remove-ui))
  * The presentation screen needs to be modifiable. A foreseeable problem is overlapping text. If two plugins want to add something to the left footer, how do we keep one from writing on top of the other. Some text will need to overlap, such as on-screen notifications.


# Available References #
[Python Plugin System](http://lucumr.pocoo.org/blogarchive/python-plugin-system)