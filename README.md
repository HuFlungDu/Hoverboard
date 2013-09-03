Clippacloud
===========

Cloud based clipboard syncing with plugabble backends. Currently supports only dropbox, with google drive API in the works, but the plugin system is easy to implement, all you need to do is put some kind of Python module into the plugins folder that has a class called "Backend", this can be a python file, a python package directory, or a shared object file that implements the python API. Anything that can be loaded with Python's import statement can be a plugin. The Backend class must have a property called "name", which is a string representing the plugin's name. It also must implement an API which can be seen in "plugins/dropbox/dropbox.py". Documentation on this API is forthcoming as the API is not yet solidified.

Features
--------
* Cross platform. As a python script utilizing wx, clippacloud can easilly support Windows, Mac, and Linux, without any changes to the code and very few conditionals based on operating system polls.
* Automatic clipboard syncing. Your clipboard is automatically shared between all your systems where clippacloud is running
* Pluggable backends. If you don't have Dropbox, use Google drive. Or write your own plugin. The plugin system is created to be easy to install and write for.
* Not just text. Sync images as well. Copy from The Gimp on Windows, paste to Photoshop on Mac.
* User scriptable configuration. Do whatever you want, this is Python. The program includes a `-c` or `--config` option that, when pointed at a python module, will import that Python module and run it's `init` function. The normal use case for this would be, in the config file, to `import clippacloud.config` and call `clippacloud.config.init` with your config options (currently the only option is `max_size`), but you have full access to the clippacloud code from here. Duck punch your way to better health.

Planned Features
----------------
* More backends. Beyond Google Drive API, hopefully add support for a central server hosted by me and for a generic FTP server.
* File copying. Copy from your file explorer on one PC to your file explorer on another. Trying to find MIME types in wx.
* More specific clipboard backends. wx has pretty weak support for the clipboard, for instance images don't always copy on Linux. Hopefully I can make a generic clipboard that would work better in this regard by using the native Python APIs.

Requirements
------------
* Python 2.7
* wxPython >= 2.8 (On mac, wxPython2.8 will cause the app to have a dock icon. With  >=2.9 cocoa build, the program will use a menubar icon. >=2.9 carbon builds will still use a dock icon. On Win32/Linux this doesn't matter)

License
-------
The Dropbox Core API code included in this repo is licensed under the MIT license, available in the directory. The remainder of the code written by me is released into the public domain, DWTFYW.
