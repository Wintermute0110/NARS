XBMC-rom-utils
==============

**XBMC ROM utilities (XRU)** is a set of Python scripts that allows you to filter 
your ROM collections to be used with the XBMC launcher plugins like *Advanced 
Launcher*, *ROM Collection Browser*, or any other front-end. If the ROM 
collections are updated or a new version of the emulators installed (which may 
require some new ROMs to be updated) **XRU** is able to synchronise the XBMC 
launchers with the new ROMs quickly and effectively.

**XRU** includes three programs

- `xru-console` filters a ROM collection with No-Intro naming conventions and copies 
the filtered list to the destination directory of your choice. Multiple ROM collections, 
each with a different filter, can be configured. Multiple filters can be
configured to the same ROM collection, for example to split the ROMs into
regions. Also, if artwork is available, it may also be synchronised.

- `xru-mame` takes the MAME-generated XML game database and merges it 
with `Catver.ini`. Then, a set of filters can be defined (for example, 
to remove mechanical games) so filtered ROMs are copied to different 
destination directories. It also creates NFO files with game information 
for launchers and copies local artwork if available.

- `xru-launcher-AL` parses XBMC's *Advanced Launcher* configuration file and scans your 
ROM launchers for missing ROMs. It prints a report with the launchers you have to update.

More information can be found on the 
[documentation](http://wintermute0110.github.io/XBMC-rom-utils/).

**This software is still being developed!** Be aware of the dragons.
