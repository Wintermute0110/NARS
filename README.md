NARS Advanced ROM Sorting
=========================

**NARS Advanced ROM Sorting (NARS)** is a set of Python scripts that allows you to filter
your ROM collections to remove unwanted ROMs. If the ROM collections are updated or a new 
version of the emulators installed (which may require some new ROMs to be updated) **NARS** 
is able to synchronise the ROM directories quickly. **NARS** includes two components:

- `nars-console` filters a ROM collection with No-Intro names and copies
the filtered list to the destination directory of your choice. Multiple ROM
collections, each with a different filter, can be configured. Multiple filters
can be configured to the same ROM collection, for example to split the ROMs
into USA, Europe and Japan regions. Also, if artwork is available, it may also
be synchronised.

- `nars-mame` takes the MAME-generated XML game database and merges it
with `Catver.ini`. Then, a set of filters can be defined (for example,
to remove mechanical games or select games that use a lightgun) and filtered
ROMs are copied to different destination directories. It also creates NFO files
with game information for launchers and copies local artwork if available so
offline scrapers can be used.

More information can be found on the [documentation/tutorial](http://wintermute0110.github.io/NARS/).
