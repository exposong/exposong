To keep the code standard, all code submitted should follow these guidelines.

## Identifiers ##

  * Identifiers should be as short as possible, but still descriptive of it's purpose. These rules do not apply to built-in methods, such as `__init__`.
  * Class names should be CamelCase. No underscore character is to be used to separate the words. (e.g. `ScheduleList`)
  * Constants should be upper case (e.g. `MY_CONSTANT`).
  * Functions and variables should be lowercase with underscores (e.g. `presentation_preview`, `create_menu()`).
    * Functions should be a verb phrase. (e.g. `show()`, `set_var(var)`, `get_var()`).
    * Variables should be nouns. (e.g. `title`, `notebook`, `file_manager`).
  * Private methods and variables of a class should be prefixed with an underscores. If a method or class variable needs to be concealed completely, [two underscores](http://docs.python.org/ref/id-classes.html) can be used.

## Indentation and Multi-Line Statements ##

  * To indent code, use two spaces. Code blocks (such as under an if statement) should be two more spaces than the previous code block.
  * Lines should not extend past the 80 character mark if possible. Statements extended over multiple lines should have 4 spaces in addition to the indent.

## Compound Statements ##

Compound Statements are if-then statements, for statements, while statements, and so on.

  * The expression following the "if", "for", "while", etc, should not be wrapped in parenthesis. Example:
```
if x > 5:
    print x
```

## Documentation Strings ##

Built-in support for documentation in python is really good, and ExpoSong needs to make use of it.

Class documentation should be a multi-line string. Functions should have a single line string, unless more is required. [ReStructuredText](http://docutils.sourceforge.net/rst.html) should be used in documentation.

---

A lot of ideas and phrasing were taken from [TextPress Documentation](http://dev.pocoo.org/projects/textpress/browser/docs/extend/styleguide.txt).