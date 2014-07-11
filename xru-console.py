#!/usr/bin/python
# XBMC ROM utilities - Console ROMs

# Copyright (c) 2014 Wintermute0110 <wintermute0110@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import sys, os, re, shutil
import operator, argparse
import xml.etree.ElementTree as ET

# --- Global variables
__software_version = '0.1.0';
__config_configFileName = 'xru-console-config.xml';
__config_logFileName = 'xru-console-log.txt';

# --- Config file options global class (like a C struct)
class ConfigFile:
  pass
class ConfigFileFilter:
  pass
configuration = ConfigFile();

# --- Program options (from command line)
__prog_option_log = 0;
__prog_option_log_filename = __config_logFileName;
__prog_option_dry_run = 0;
__prog_option_clean_ROMs = 0;
__prog_option_clean_NFO = 0;
__prog_option_clean_ArtWork = 0;
__prog_option_sync = 0;

# -----------------------------------------------------------------------------
# DEBUG functions
# -----------------------------------------------------------------------------
def dumpclean(obj):
  if type(obj) == dict:
    for k, v in obj.items():
      if hasattr(v, '__iter__'):
        print k
        dumpclean(v)
      else:
        print '%s : %s' % (k, v)
  elif type(obj) == list:
    for v in obj:
      if hasattr(v, '__iter__'):
        dumpclean(v)
      else:
        print v
  else:
      print obj

# -----------------------------------------------------------------------------
# Logging functions
# -----------------------------------------------------------------------------
class Log():
  error = 1
  warn = 2
  info = 3
  verb = 4  # Verbose: -v
  vverb = 5 # Very verbose: -vv
  debug = 6 # Debug: -vvv

# ---  Console print and logging
f_log = 0;
log_level = 3;

def change_log_level(level):
  global log_level;

  log_level = level;

# --- Print/log to a specific level  
def pprint(level, print_str):
  global f_log;

  # --- If file descriptor not open, open it
  if __prog_option_log:
    if f_log == 0:
      f_log = open(__prog_option_log_filename, 'w')

  # --- Write to console depending on verbosity
  if level <= log_level:
    print print_str;

  # --- Write to file
  if __prog_option_log:
    if level <= log_level:
      if print_str[-1] != '\n':
        print_str += '\n';
      f_log.write(print_str) # python will convert \n to os.linesep

# --- Some useful function overloads
def print_error(print_str):
  pprint(Log.error, print_str);

def print_warn(print_str):
  pprint(Log.warn, print_str);

def print_info(print_str):
  pprint(Log.info, print_str);

def print_verb(print_str):
  pprint(Log.verb, print_str);

def print_vverb(print_str):
  pprint(Log.vverb, print_str);

def print_debug(print_str):
  pprint(Log.debug, print_str);

# -----------------------------------------------------------------------------
# Filesystem functions
# -----------------------------------------------------------------------------
# Returns:
#  0 - ArtWork file found in sourceDir and copied
#  1 - ArtWork file not found in sourceDir
# NOTE: be careful, maybe artwork should be when copied to match ROM name
#       if artwork was subtituted.
def copy_ArtWork_file(fileName, artName, sourceDir, destDir):
  sourceFullFilename = sourceDir + artName + '.png';
  destFullFilename = destDir + fileName + '.png';

  # Maybe artwork does not exist... Then do nothing
  if not os.path.isfile(sourceFullFilename):
    return 1;

  print_debug(' Copying ' + sourceFullFilename);
  print_debug(' Into    ' + destFullFilename);
  if not __prog_option_dry_run:
    try:
      shutil.copy(sourceFullFilename, destFullFilename)
    except EnvironmentError:
      print_debug("copy_ArtWork_file >> Error happened");

  return 0;

# Returns:
#  0 - ArtWork file found in sourceDir and copied
#  1 - ArtWork file not found in sourceDir
#  2 - ArtWork file found in sourceDir and destDir, same size so not copied
# NOTE: be careful, maybe artwork should be when copied to match ROM name
#       if artwork was subtituted.
def update_ArtWork_file(fileName, artName, sourceDir, destDir):
  sourceFullFilename = sourceDir + artName + '.png';
  destFullFilename = destDir + fileName + '.png';
  
  existsSource = os.path.isfile(sourceFullFilename);
  existsDest = os.path.isfile(destFullFilename);
  # --- Maybe artwork does not exist... Then do nothing
  if not os.path.isfile(sourceFullFilename):
    return 1;

  sizeSource = os.path.getsize(sourceFullFilename);
  if existsDest:
    sizeDest = os.path.getsize(destFullFilename);
  else:
    sizeDest = -1;

  # If sizes are equal Skip copy and return 1
  if sizeSource == sizeDest:
    print_debug(' Updated ' + destFullFilename);
    return 2;

  # destFile does not exist or sizes are different, copy.
  print_debug(' Copying ' + sourceFullFilename);
  print_debug(' Into    ' + destFullFilename);
  if not __prog_option_dry_run:
    try:
      shutil.copy(sourceFullFilename, destFullFilename)
    except EnvironmentError:
      print_debug("update_ArtWork_file >> Error happened");

  return 0

def copy_ROM_file(fileName, sourceDir, destDir):
  sourceFullFilename = sourceDir + fileName;
  destFullFilename = destDir + fileName;

  print_debug(' Copying ' + sourceFullFilename);
  print_debug(' Into    ' + destFullFilename);
  if not __prog_option_dry_run:
    try:
      shutil.copy(sourceFullFilename, destFullFilename)
    except EnvironmentError:
      print_debug("copy_ROM_file >> Error happened");

# Returns:
#  0 - File copied (sizes different)
#  1 - File not copied (updated)
def update_ROM_file(fileName, sourceDir, destDir):
  sourceFullFilename = sourceDir + fileName;
  destFullFilename = destDir + fileName;

  existsSource = os.path.isfile(sourceFullFilename);
  existsDest = os.path.isfile(destFullFilename);
  if not existsSource:
    print_error("Source file not found");
    sys.exit(10);

  sizeSource = os.path.getsize(sourceFullFilename);
  if existsDest:
    sizeDest = os.path.getsize(destFullFilename);
  else:
    sizeDest = -1;

  # If sizes are equal. Skip copy and return 1
  if sizeSource == sizeDest:
    return 1;

  # destFile does not exist or sizes are different, copy.
  print_debug(' Copying ' + sourceFullFilename);
  print_debug(' Into    ' + destFullFilename);
  if not __prog_option_dry_run:
    try:
      shutil.copy(sourceFullFilename, destFullFilename)
    except EnvironmentError:
      print_debug("update_ROM_file >> Error happened");

  return 0;

# This function either succeeds or aborts the program. Check if file exists
# before calling this.
def delete_ROM_file(fileName, dir):
  fullFilename = dir + fileName;

  if not __prog_option_dry_run:
    try:
      os.remove(fullFilename);
    except EnvironmentError:
      print_debug("delete_ROM_file >> Error happened");

def exists_ROM_file(fileName, dir):
  fullFilename = dir + fileName;

  return os.path.isfile(fullFilename);

def haveDir_or_abort(dirName):
  if not os.path.isdir(dirName):
    print_error('\033[31m[ERROR]\033[0m Directory does not exist ' + dirName);
    sys.exit(10);

# -----------------------------------------------------------------------------
def copy_ROM_list(rom_list, sourceDir, destDir):
  print_info('[Copying ROMs into destDir]');

  num_steps = len(rom_list);
  # 0 here prints [0, ..., 99%] instead [1, ..., 100%]
  step = 0;
  num_files = 0;
  num_copied_roms = 0;
  for rom_copy_item in rom_list:
    # --- Update progress
    percentage = 100 * step / num_steps;
    sys.stdout.write('{:3d}% '.format(percentage));

    # --- Copy file (this function succeeds or aborts program)
    romFileName = rom_copy_item + '.zip';
    copy_ROM_file(romFileName, sourceDir, destDir);
    num_copied_roms += 1;
    print_info('<Copied> ' + romFileName);
    sys.stdout.flush();

    # --- Update progress
    step += 1;

  print_info('[Report]');
  print_info('Copied ROMs ' + '{:6d}'.format(num_copied_roms));

def update_ROM_list(rom_list, sourceDir, destDir):
  print_info('[Updating ROMs into destDir]');
  
  num_steps = len(rom_list);
  # 0 here prints [0, ..., 99%] instead [1, ..., 100%]
  step = 0;
  num_copied_roms = 0;
  num_updated_roms = 0;
  for rom_copy_item in rom_list:
    # --- Update progress
    percentage = 100 * step / num_steps;

    # --- Copy file (this function succeeds or aborts program)
    romFileName = rom_copy_item + '.zip';
    ret = update_ROM_file(romFileName, sourceDir, destDir);
    if ret == 0:
      # On default verbosity level only report copied files
      sys.stdout.write('{:3d}% '.format(percentage));
      num_copied_roms += 1;
      print_info('<Copied > ' + romFileName);
    elif ret == 1:
      if log_level >= Log.verb:
        sys.stdout.write('{:3d}% '.format(percentage));
      num_updated_roms += 1;
      print_verb('<Updated> ' + romFileName);
    else:
      print_error('Wrong value returned by update_ROM_file()');
      sys.exit(10);
    sys.stdout.flush()

    # --- Update progress
    step += 1;

  print_info('[Report]');
  print_info('Copied ROMs ' + '{:6d}'.format(num_copied_roms));
  print_info('Updated ROMs ' + '{:5d}'.format(num_updated_roms));

def clean_ROMs_destDir(destDir, rom_copy_dic):
  print_info('[Cleaning ROMs in ROMsDest]');

  # --- Delete ROMs present in destDir not present in the filtered list
  rom_main_list = [];
  for file in os.listdir(destDir):
    if file.endswith(".zip"):
      rom_main_list.append(file);

  num_cleaned_roms = 0;
  for file in sorted(rom_main_list):
    basename, ext = os.path.splitext(file); # Remove extension
    if basename not in rom_copy_dic:
      num_cleaned_roms += 1;
      delete_ROM_file(file, destDir);
      print_info('<Deleted> ' + file);

  print_info('Deleted ' + str(num_cleaned_roms) + ' redundant ROMs');

def delete_redundant_NFO(destDir):
  print_info('[Deleting redundant NFO files]');
  num_deletedNFO_files = 0;
  for file in os.listdir(destDir):
    if file.endswith(".nfo"):
      # Chech if there is a corresponding ROM for this NFO file
      thisFileName, thisFileExtension = os.path.splitext(file);
      romFileName_temp = thisFileName + '.zip';
      if not exists_ROM_file(romFileName_temp, destDir):
        delete_ROM_file(file, destDir);
        num_deletedNFO_files += 1;
        print_info('<Deleted NFO> ' + file);

  print_info('Deleted ' + str(num_deletedNFO_files) + ' redundant NFO files');

def copy_ArtWork_list(filter_config, rom_copy_dic):
  print_info('[Copying ArtWork]');
  fanartSourceDir = filter_config.fanartSourceDir;
  fanartDestDir = filter_config.fanartDestDir;
  thumbsSourceDir = filter_config.thumbsSourceDir;
  thumbsDestDir = filter_config.thumbsDestDir;
  
  # --- Check that directories exist
  haveDir_or_abort(thumbsSourceDir);
  haveDir_or_abort(thumbsDestDir);
  haveDir_or_abort(fanartSourceDir);
  haveDir_or_abort(fanartDestDir);
  
  # --- Copy artwork
  num_steps = len(rom_copy_dic);
  step = 0;
  num_copied_thumbs = 0;
  num_missing_thumbs = 0;
  num_copied_fanart = 0;
  num_missing_fanart = 0;
  for rom_baseName in sorted(rom_copy_dic):
    # --- Get artwork name
    art_baseName = rom_copy_dic[rom_baseName];

    # --- Update progress
    percentage = 100 * step / num_steps;
    sys.stdout.write('{:3d}% '.format(percentage));

    # --- Thumbs
    ret = copy_ArtWork_file(rom_baseName, art_baseName, thumbsSourceDir, thumbsDestDir);
    if ret == 0:
      num_copied_thumbs += 1;
      print_info('<Copied Thumb  > ' + art_baseName);
    elif ret == 1:
      num_missing_thumbs += 1;
      print_info('<Missing Thumb > ' + art_baseName);
    else:
      print_error('Wrong value returned by copy_ArtWork_file()');
      sys.exit(10);

    # --- Update progress
    percentage = 100 * step / num_steps;
    sys.stdout.write('{:3d}% '.format(percentage));

    # --- Fanart
    ret = copy_ArtWork_file(rom_baseName, art_baseName, fanartSourceDir, fanartDestDir);
    if ret == 0:
      num_copied_fanart += 1;
      print_info('<Copied Fanart > ' + art_baseName);
    elif ret == 1:
      num_missing_fanart += 1;
      print_info('<Missing Fanart> ' + art_baseName);
    else:
      print_error('Wrong value returned by copy_ArtWork_file()');
      sys.exit(10);

    # --- Update progress
    step += 1;

  print_info('[Report]');
  print_info('Copied thumbs ' + '{:6d}'.format(num_copied_thumbs));
  print_info('Missing thumbs ' + '{:5d}'.format(num_missing_thumbs));
  print_info('Copied fanart ' + '{:6d}'.format(num_copied_fanart));
  print_info('Missing fanart ' + '{:5d}'.format(num_missing_fanart));

def update_ArtWork_list(filter_config, rom_copy_dic):
  print_info('[Updating ArtWork]');
  
  thumbsSourceDir = filter_config.thumbsSourceDir;
  thumbsDestDir = filter_config.thumbsDestDir;
  fanartSourceDir = filter_config.fanartSourceDir;
  fanartDestDir = filter_config.fanartDestDir;

  # --- Check that directories exist
  haveDir_or_abort(thumbsSourceDir);
  haveDir_or_abort(thumbsDestDir);
  haveDir_or_abort(fanartSourceDir);
  haveDir_or_abort(fanartDestDir);
  
  # --- Copy/update artwork
  num_steps = len(rom_copy_dic);
  step = 0;
  num_copied_thumbs = 0;
  num_updated_thumbs = 0;
  num_missing_thumbs = 0;
  num_copied_fanart = 0;
  num_updated_fanart = 0;
  num_missing_fanart = 0;
  for rom_baseName in sorted(rom_copy_dic):
    # --- Update progress
    percentage = 100 * step / num_steps;

    # --- Get artwork name
    art_baseName = rom_copy_dic[rom_baseName];

    # --- Thumbs
    ret = update_ArtWork_file(rom_baseName, art_baseName, thumbsSourceDir, thumbsDestDir);
    if ret == 0:
      # On default verbosity level only report copied files
      sys.stdout.write('{:3d}% '.format(percentage));
      num_copied_thumbs += 1;
      print_info('<Copied  Thumb > ' + art_baseName);
    elif ret == 1:
      # Also report missing artwork
      sys.stdout.write('{:3d}% '.format(percentage));
      num_missing_thumbs += 1;
      print_info('<Missing Thumb > ' + art_baseName);
    elif ret == 2:
      if log_level >= Log.verb:
        sys.stdout.write('{:3d}% '.format(percentage));
      num_updated_thumbs += 1;
      print_verb('<Updated Thumb > ' + art_baseName);
    else:
      print_error('Wrong value returned by copy_ArtWork_file()');
      sys.exit(10);

    # --- Fanart
    ret = update_ArtWork_file(rom_baseName, art_baseName, fanartSourceDir, fanartDestDir);
    if ret == 0:
      # Also report missing artwork
      sys.stdout.write('{:3d}% '.format(percentage));
      num_copied_fanart += 1;
      print_info('<Copied  Fanart> ' + art_baseName);
    elif ret == 1:
      # Also report missing artwork
      sys.stdout.write('{:3d}% '.format(percentage));
      num_missing_fanart += 1;
      print_info('<Missing Fanart> ' + art_baseName);
    elif ret == 2:
      if log_level >= Log.verb:
        sys.stdout.write('{:3d}% '.format(percentage));
      num_updated_fanart += 1;
      print_verb('<Updated Fanart> ' + art_baseName);
    else:
      print_error('Wrong value returned by copy_ArtWork_file()');
      sys.exit(10);

    # --- Update progress
    step += 1;

  print_info('[Report]');
  print_info('Copied thumbs ' + '{:6d}'.format(num_copied_thumbs));
  print_info('Updated thumbs ' + '{:5d}'.format(num_updated_thumbs));
  print_info('Missing thumbs ' + '{:5d}'.format(num_missing_thumbs));
  print_info('Copied fanart ' + '{:6d}'.format(num_copied_fanart));
  print_info('Updated fanart ' + '{:5d}'.format(num_updated_fanart));
  print_info('Missing fanart ' + '{:5d}'.format(num_missing_fanart));

# Artwork may be available for some of the parent/clones in the ROM set, but
# not for the filtered ROMs. This function test this and makes a list of the
# available artwork that approximates the filtered ROM list.
#
# Returns a dictionary
#  artwork_copy_dic
#   key   -> string, ROM filename in destDir with no extension
#   value -> string, Artwork filename to be copied, no extension
#
# The name of the artwork file should be the same for thumbs an fanarts. To get
# the actual filename, add the graphical extension (.png).
# Checking if artwork was replaced is easy: if key is equal to value, it was not
# replaced. Otherwise, it was replaced.
def optimize_ArtWork_list(rom_copy_list, romMainList_list, filter_config):
  "Write me"
  __debug_optimize_ArtWork = 0;

  print_info('[Optimising ArtWork file list]');
  thumbsSourceDir = filter_config.thumbsSourceDir;
  thumbsDestDir = filter_config.thumbsDestDir;
  fanartSourceDir = filter_config.fanartSourceDir;
  fanartDestDir = filter_config.fanartDestDir;

  # --- Check that directories exist
  if not os.path.isdir(thumbsSourceDir):
    print_error('thumbsSourceDir not found ' + thumbsSourceDir);
    sys.exit(10);
  if not os.path.isdir(thumbsDestDir):
    print_error('thumbsDestDir not found ' + thumbsDestDir);
    sys.exit(10);
  if not os.path.isdir(fanartSourceDir):
    print_error('fanartSourceDir not found ' + fanartSourceDir);
    sys.exit(10);
  if not os.path.isdir(fanartDestDir):
    print_error('fanartDestDir not found ' + fanartDestDir);
    sys.exit(10);

  # - For every ROM to be copied (filtered) check if ArtWork exists. If not,
  #   try artwork of other ROMs in the parent/clone set.
  artwork_copy_dic = {};
  for rom_copy_item in rom_copy_list:
    romFileName = rom_copy_item + '.png';
    if __debug_optimize_ArtWork:
      print '<<Testing>> ', romFileName;
    if os.path.isfile(thumbsSourceDir + romFileName):
      if __debug_optimize_ArtWork:
        print ' Added      ', rom_copy_item;
      artwork_copy_dic[rom_copy_item] = rom_copy_item;
    else:
      if __debug_optimize_ArtWork:
        print ' NOT found  ', romFileName;
      # - Brute force check
      file = rom_copy_item + '.zip';
      pclone_list = [];
      for item in romMainList_list:
        filenames_list = item.filenames;
        if file in filenames_list:
          pclone_list = filenames_list;
          break;
      if len(pclone_list) == 0:
        print_error('Logical error');
        sys.exit(10);
      # - Check if artwork exists for this set
      for file in pclone_list:
        root, ext = os.path.splitext(file);
        if os.path.isfile(thumbsSourceDir + root + '.png'):
          if __debug_optimize_ArtWork:
            print ' Added clone', root;
          artwork_copy_dic[rom_copy_item] = root;
          break;
  
  return artwork_copy_dic;

def clean_ArtWork_destDir(filter_config, artwork_copy_dic):
  print_info('[Cleaning ArtWork]');

  thumbsDestDir = filter_config.thumbsDestDir;
  fanartDestDir = filter_config.fanartDestDir;
  
  # --- Check that directories exist
  haveDir_or_abort(thumbsDestDir);
  haveDir_or_abort(thumbsDestDir);

  # --- Delete unknown thumbs
  thumbs_file_list = [];
  for file in os.listdir(thumbsDestDir):
    if file.endswith(".png"):
      thumbs_file_list.append(file);

  num_cleaned_thumbs = 0;
  for file in sorted(thumbs_file_list):
    art_baseName, ext = os.path.splitext(file); # Remove extension
    if art_baseName not in artwork_copy_dic:
      num_cleaned_thumbs += 1;
      delete_ROM_file(file, thumbsDestDir);
      print_info('<Deleted thumb > ' + file);

  # --- Delete unknown fanart
  fanart_file_list = [];
  for file in os.listdir(fanartDestDir):
    if file.endswith(".png"):
      fanart_file_list.append(file);

  num_cleaned_fanart = 0;
  for file in sorted(fanart_file_list):
    art_baseName, ext = os.path.splitext(file); # Remove extension
    if art_baseName not in artwork_copy_dic:
      num_cleaned_fanart += 1;
      delete_ROM_file(file, fanartDestDir);
      print_info(' <Deleted fanart> ' + file);

  # --- Report
  print_info('Deleted ' + str(num_cleaned_thumbs) + ' redundant thumbs');
  print_info('Deleted ' + str(num_cleaned_fanart) + ' redundant fanart');

# -----------------------------------------------------------------------------
# Configuration file functions
# -----------------------------------------------------------------------------
def parse_File_Config():
  "Parses config file"
  print_info('[Parsing config file]');
  try:
    tree = ET.parse(__config_configFileName);
  except IOError:
    print_error('[ERROR] cannot find file ' + __config_configFileName);
    sys.exit(10);
  root = tree.getroot();

  # --- Configuration object
  configFile = ConfigFile();
  configFile.filter_dic = {};

  # --- Parse filters
  for root_child in root:
    if root_child.tag == 'collection':
      print_debug('<collection>');
      if 'name' in root_child.attrib:
        filter_class = ConfigFileFilter();
        
        # -- Mandatory config file options
        filter_class.name = root_child.attrib['name'];
        filter_class.shortname = root_child.attrib['shortname'];
        print_debug(' name           = ' + filter_class.name);
        print_debug(' shortname      = ' + filter_class.shortname);
        sourceDirFound = 0;
        destDirFound = 0;

        # - Optional config file options (deafault to empty string)
        # NOTE: missing values from config file must be initialised to None
        filter_class.fanartSourceDir = None;
        filter_class.fanartDestDir = None;
        filter_class.thumbsSourceDir = None;
        filter_class.thumbsDestDir = None;
        filter_class.filterUpTags = None;
        filter_class.filterDownTags = None;
        filter_class.includeTags = None;
        filter_class.excludeTags = None;
        filter_class.NoIntro_XML = None;
        
        # - Initialise variables for the ConfigFileFilter object
        #   to avoid None objects later.
        for filter_child in root_child:
          if filter_child.tag == 'ROMsSource':
            print_debug('ROMsSource    = ' + filter_child.text);
            sourceDirFound = 1;
            tempDir = filter_child.text;
            if tempDir[-1] != '/': tempDir = tempDir + '/';
            filter_class.sourceDir = tempDir;

          elif filter_child.tag == 'ROMsDest':
            print_debug('ROMsDest      = ' + filter_child.text);
            destDirFound = 1;
            tempDir = filter_child.text;
            if tempDir[-1] != '/': tempDir = tempDir + '/';
            filter_class.destDir = tempDir;

          elif filter_child.tag == 'FanartSource':
            print_debug('FanartSource = ' + filter_child.text);
            tempDir = filter_child.text;
            if tempDir[-1] != '/': tempDir = tempDir + '/';
            filter_class.fanartSourceDir = tempDir;

          elif filter_child.tag == 'FanartDest':
            print_debug('FanartDest = ' + filter_child.text);
            tempDir = filter_child.text;
            if tempDir[-1] != '/': tempDir = tempDir + '/';
            filter_class.fanartDestDir = tempDir;

          elif filter_child.tag == 'ThumbsSource':
            print_debug('ThumbsSource = ' + filter_child.text);
            tempDir = filter_child.text;
            if tempDir[-1] != '/': tempDir = tempDir + '/';
            filter_class.thumbsSourceDir = tempDir;

          elif filter_child.tag == 'ThumbsDest':
            print_debug('ThumbsDest = ' + filter_child.text);
            tempDir = filter_child.text;
            if tempDir[-1] != '/': tempDir = tempDir + '/';
            filter_class.thumbsDestDir = tempDir;

          elif filter_child.tag == 'filterUpTags' and \
               filter_child.text is not None:
            print_debug('filterUpTags   = ' + filter_child.text);
            text_string = filter_child.text;
            list = text_string.split(",");
            filter_class.filterUpTags = list;

          elif filter_child.tag == 'filterDownTags' and \
               filter_child.text is not None:
            print_debug('filterDownTags = ' + filter_child.text);
            text_string = filter_child.text;
            list = text_string.split(",");
            filter_class.filterDownTags = list;

          elif filter_child.tag == 'includeTags' and \
               filter_child.text is not None:
            print_debug('includeTags    = ' + filter_child.text);
            text_string = filter_child.text;
            list = text_string.split(",");
            filter_class.includeTags = list;

          elif filter_child.tag == 'excludeTags' and \
               filter_child.text is not None:
            print_debug('excludeTags    = ' + filter_child.text);
            text_string = filter_child.text;
            list = text_string.split(",");
            filter_class.excludeTags = list;

          elif filter_child.tag == 'NoIntroDat' and \
               filter_child.text is not None:
            print_debug('NoIntroDat    = ' + filter_child.text);
            filter_class.NoIntro_XML = filter_child.text;

        # - Trim blank spaces on filter lists
        if filter_class.filterUpTags is not None:
          for index, item in enumerate(filter_class.filterUpTags):
            filter_class.filterUpTags[index] = item.strip();

        if filter_class.filterDownTags is not None:
          for index, item in enumerate(filter_class.filterDownTags):
            filter_class.filterDownTags[index] = item.strip();

        if filter_class.includeTags is not None:
          for index, item in enumerate(filter_class.includeTags):
            filter_class.includeTags[index] = item.strip();

        if filter_class.excludeTags is not None:
          for index, item in enumerate(filter_class.excludeTags):
            filter_class.excludeTags[index] = item.strip();

        # - Check for errors in this filter
        if not sourceDirFound:
          print_error('source directory not found in config file');
          sys.exit(10);
        if not destDirFound:
          print_error('destination directory not found in config file');
          sys.exit(10);

        # - Aggregate filter to configuration main variable
        configFile.filter_dic[filter_class.shortname] = filter_class;
      else:
        print_error('<collection> tag does not have name attribute');
        sys.exit(10);

  return configFile;

def get_Filter_Config(filterName):
  "Returns the configuration filter object given the filter name"
  for key in configuration.filter_dic:
    if key == filterName:
      return configuration.filter_dic[key];

  print_error('get_Filter_Config >> filter ' + filterName + ' not found in configuration file');
  sys.exit(20);

# -----------------------------------------------------------------------------
# Miscellaneous ArtWork functions
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# Miscellaneous ROM functions
# -----------------------------------------------------------------------------
class MainROM:
  pass

class NoIntro_ROM:
  def __init__(self, baseName):
    self.baseName = baseName;

class dir_ROM:
  def __init__(self, fileName):
    self.fileName = fileName;

def extract_ROM_Properties_Raw(romFileName):
  "Given a ROM file name extracts all the tags and returns a list"
  __debug_propertyParsers = 0;

  romProperties_raw = [];
  romProperties_raw = re.findall("(\([^\(]*\))", romFileName);

  # Debug print
  if __debug_propertyParsers:
    print 'extract_ROM_Properties_Raw >> Property list';
    print '\n'.join(romProperties_raw);
    print '\n'
  
  return romProperties_raw;

def extract_ROM_Tags_All(romFileName):
  "Given a ROM file name extracts all the tags and returns a list. Also parses tags"
  __debug_propertyParsers = 0;

  # Extract Raw properties with parenthesis
  romProperties_raw = [];
  romProperties_raw = re.findall("(\([^\(]*\))", romFileName);

  # For every property chech if it has comma(s). If so, reparse the
  # property and create new properties
  romProperties_all = [];
  for property in romProperties_raw:
    # Strip parentehsis
    property = property[1:-1];
    if __debug_propertyParsers:
      print 'extract_ROM_Properties_All >> Property: ' + property;
    
    match = re.search(",", property);
    if match:
      # Re-parse the string and decompose into new properties
      subProperties = re.findall("([^\,]*)", property);
      for subPropertie in subProperties:
        if __debug_propertyParsers:
          print 'extract_ROM_Properties_All >> subPropertie: "' + subPropertie + '"';
        # For some reason, this regular expresion search returns the matches and
        # also one empty string afterwards...
        # Non empty strings are "true", empty are "false"
        if subPropertie:
          # strip() is equivalent to Perl trim()
          subPropertieOK = subPropertie.strip();
          romProperties_all.append(subPropertieOK);
          if __debug_propertyParsers:
            print 'extract_ROM_Properties_All >> Added subPropertie: "' + subPropertieOK + '"';
    else:
      romProperties_all.append(property);

  # Debug print
  if __debug_propertyParsers:
    print 'extract_ROM_Properties_All >> Property list';
    print '\n'.join(romProperties_all);
    print '\n'
  
  return romProperties_all;

def get_ROM_baseName(romFileName):
  "Get baseName from filename (no extension, no tags)"
  
  rom_baseName = '';
  regSearch = re.search("[^\(\)]*", romFileName);
  if regSearch == None:
    print 'Logical error';
    sys.exit(10);
  regExp_result = regSearch.group();
  
  return regExp_result.strip();
  
def scoreROM(romTags, upTag_list, downTag_list):
  score = 0;

  # Iterate through the tags, and add/subtract points depending on the list
  # of given tags.
  for tag in romTags:
    # - Up tags increase score
    #   Tags defined first have more score
    tag_score = len(upTag_list);
    for upTag in upTag_list:
      if tag == upTag:
        score += tag_score;
      tag_score -= 1;
    # - Down tags decrease the score
    tag_score = len(downTag_list);
    for downTag in downTag_list:
      if tag == downTag:
        score -= tag_score;
      tag_score -= 1;

  return score;

def isTag(tags, tag_list):
  result = 0;

  for tag in tags:
    for testTag in tag_list:
      if tag == testTag:
        result = 1;
        return result;

  return result;

# Parses a No-Intro DAT and creates an object with the XML information
# Then, it creates a ROM main dictionary
#  romMainList [list of ROMMain objects]
# ROMMain object
#  ROMMain.filenames [list] full game filename (with extension)
#
# The first game in the list is the parent game according to the DAT,
# and the rest are the clones in no particular order.
def get_NoIntro_Main_list(filter_config):
  "Parses NoInto XML and makes a parent-clone list"
  __debug_parse_NoIntro_XML_Config = 0;
  
  filename = filter_config.NoIntro_XML;
  print_info('Parsing No-Intro XML DAT');
  print "Parsing No-Intro XML file " + filename + "...",;
  sys.stdout.flush();
  try:
    tree = ET.parse(filename);
  except IOError:
    print '\n';
    print_error('[ERROR] cannot find file ' + filename);
    sys.exit(10);
  print ' done';

  # --- Raw list: literal information from the XML
  rom_raw_dict = {}; # Key is ROM baseName
  root = tree.getroot();
  num_games = 0;
  num_parents = 0;
  num_clones = 0;
  for game_EL in root:
    if game_EL.tag == 'game':
      num_games += 1;

      # --- Game attributes
      game_attrib = game_EL.attrib;
      romName = game_attrib['name'];
      romObject = NoIntro_ROM(romName);
      if __debug_parse_NoIntro_XML_Config:
        print 'Game = ' + romName;

      if 'cloneof' in game_attrib:
        num_clones += 1;
        romObject.cloneof = game_attrib['cloneof'];
        romObject.isclone = 1;
        if __debug_parse_NoIntro_XML_Config:
          print ' Clone of = ' + game_attrib['cloneof'];
      else:
        num_parents += 1;
        romObject.isclone = 0;

      # Add new game to the list
      rom_raw_dict[romName] = romObject;
  del tree;
  print_info('Total number of games = ' + str(num_games));
  print_info('Number of parents = ' + str(num_parents));
  print_info('Number of clones = ' + str(num_clones));

  # --- Create a parent-clone list
  rom_pclone_dict = {};
  # Naive algorithm, two passes.
  # First traverse the raw list and make a list of parent games
  for key in rom_raw_dict:
    gameObj = rom_raw_dict[key];
    if not gameObj.isclone:
      romObject = NoIntro_ROM(key);
      romObject.hasClones = 0;
      rom_pclone_dict[key] = romObject;

  # Second pass: traverse the raw list for clones and assign clone ROMS to 
  # their parents
  num_parents = 0;
  num_clones = 0;
  for key in rom_raw_dict:
    gameObj = rom_raw_dict[key];
    if gameObj.isclone:
      num_clones += 1;
      # Find parent ROM. Raise error if not found
      if gameObj.cloneof in rom_pclone_dict:
        # Add clone ROM to the list of clones
        parentObj = rom_pclone_dict[gameObj.cloneof];
        if not hasattr(parentObj, 'clone_list'):
          parentObj.clone_list = [];
          parentObj.hasClones = 1;
        parentObj.clone_list.append(key);
      else:
        print 'Game "' + key + '"';
        print 'Parent "' + gameObj.cloneof + '"';
        print 'Parent ROM not found "' + gameObj.cloneof + '"';
        sys.exit(10);
    else:
      num_parents += 1;

  # DEBUG: print parent-clone list
  for key in rom_pclone_dict:
    romObj = rom_pclone_dict[key];
    print_debug(" <Parent> '" + romObj.baseName + "'");
    if romObj.hasClones:
      for clone in romObj.clone_list:
        print_debug("  <Clone> '" + clone + "'");

  # --- Create ROM main list
  romMainList_list = [];
  for key in rom_pclone_dict:
    romNoIntroObj = rom_pclone_dict[key];
    # - Create object and add first ROM (parent ROM)
    mainROM = MainROM();
    mainROM.filenames = [];
    mainROM.filenames.append(romNoIntroObj.baseName + '.zip');    
    # - If game has clones add them to the list of filenames
    if romNoIntroObj.hasClones:
      for clone in romNoIntroObj.clone_list:
        mainROM.filenames.append(clone + '.zip');    
    # - Add MainROM to the list
    romMainList_list.append(mainROM);

  return romMainList_list;

def get_directory_Main_list(filter_config):
  "Reads a directory and creates a unique ROM parent/clone list"
  __debug_sourceDir_ROM_scanner = 0;
  
  # --- Read all files in sourceDir
  print_info('[Reading ROMs in source dir]');
  sourceDir = filter_config.sourceDir;
  romMainList_dict = {};
  num_ROMs_sourceDir = 0;
  for file in os.listdir(sourceDir):
    if file.endswith(".zip"):
      num_ROMs_sourceDir += 1;
      romObject = dir_ROM(file);
      romObject.baseName = get_ROM_baseName(file);
      romMainList_dict[file] = romObject;
      if __debug_sourceDir_ROM_scanner:
        print "  ROM       '" + romObject.fileName + "'";
        print "   baseName '" + romObject.baseName + "'";
  print_info('Found ' + str(num_ROMs_sourceDir) + ' ROMs');
  
  # --- Create a parent/clone list based on the baseName of the ROM
  pclone_ROM_dict = {}; # Key is ROM basename
  for key in romMainList_dict:
    baseName = romMainList_dict[key].baseName;
    fileName = romMainList_dict[key].fileName;
    # If baseName exists, add this ROM to that
    if baseName in pclone_ROM_dict:
      pclone_ROM_dict[baseName].append(fileName);
    # If not, create a new entry
    else:
      filenames = [];
      filenames.append(fileName);
      pclone_ROM_dict[baseName] = filenames;
  
  # --- Create ROM main list
  romMainList_list = [];
  for key in pclone_ROM_dict:
    # - Create object and add first ROM (parent ROM)
    mainROM = MainROM();
    mainROM.filenames = pclone_ROM_dict[key];
    # - Add MainROM to the list
    romMainList_list.append(mainROM);   

  return romMainList_list;

# returns rom_Tag_dic
#  key = ROM filename 'Super Mario (World) (Rev 1).zip'
#  elements = list of tags ['World', 'Rev 1']
def get_Tag_list(romMainList_list):
  "Extracts tags from filenames and creates a dictionary with them"

  rom_Tag_dic = {};
  for item in romMainList_list:
    filenames_list = item.filenames;
    for filename in filenames_list:
      rom_Tag_dic[filename] = extract_ROM_Tags_All(filename);
   
  return rom_Tag_dic;

def get_Scores_and_Filter(romMain_list, rom_Tag_dic, filter_config):
  "Score and filter the main ROM list"
  print_info('[Filtering ROMs]');
  __debug_main_ROM_list = 0;

  upTag_list = filter_config.filterUpTags;
  downTag_list = filter_config.filterDownTags;
  includeTag_list = filter_config.includeTags;
  excludeTag_list = filter_config.excludeTags;

  # --- Add ROM scores to ROM main list
  for mainROM_obj in romMain_list:
    scores_list = [];
    for filename in mainROM_obj.filenames:
      tags = rom_Tag_dic[filename];
      ROM_score = scoreROM(tags, upTag_list, downTag_list);
      scores_list.append(ROM_score);
    mainROM_obj.scores = scores_list;

  # --- Add include/exclude filters to ROM main list
  for mainROM_obj in romMain_list:
    include_list = [];
    for filename in mainROM_obj.filenames:
      tags = rom_Tag_dic[filename];
      has_excluded_tag = isTag(tags, excludeTag_list);
      has_included_tag = isTag(tags, includeTag_list);
      includeThisROM = 1;
      if has_excluded_tag and not has_included_tag:
        includeThisROM = 0;
      include_list.append(includeThisROM);
    mainROM_obj.include = include_list;

  # --- DEBUG: print main ROM list wiht scores and include flags
  if __debug_main_ROM_list:
    print "[DEBUG main ROM list scored]";
    for mainROM_obj in romMain_list:
      print mainROM_obj.filenames;
      print mainROM_obj.scores;
      print mainROM_obj.include;

  # - Order the main List based on scores and include flags
  #   Don't remove excluded ROMs because they may be useful to copy
  #   artwork (for example, the use has artwork for an excluded ROM
  #   belonging to the same set as the first ROM).
  romMain_list_sorted = [];
  romSetName_list = [];
  for mainROM_obj in romMain_list:
    # --- Get a list with the indices of the sorted list
    sorted_idx = [i[0] for i in sorted(enumerate(mainROM_obj.scores), key=lambda x:x[1])];
    sorted_idx.reverse();

    # --- List comprehension
    mainROM_sorted = MainROM();
    mainROM_sorted.filenames = [mainROM_obj.filenames[i] for i in sorted_idx];
    mainROM_sorted.scores = [mainROM_obj.scores[i] for i in sorted_idx];
    mainROM_sorted.include = [mainROM_obj.include[i] for i in sorted_idx];
    # - Set name is the stripped name of the first ROM
    #   This is compatible with both No-Intro and directory listings
    setFileName = mainROM_sorted.filenames[0];
    thisFileName, thisFileExtension = os.path.splitext(setFileName);
    stripped_ROM_name = get_ROM_baseName(thisFileName);
    mainROM_sorted.setName = stripped_ROM_name;
    romMain_list_sorted.append(mainROM_sorted);
    romSetName_list.append(stripped_ROM_name);
  romMain_list = romMain_list_sorted;

  # --- Finally, sort the list by ROM set name for nice listings
  sorted_idx = [i[0] for i in sorted(enumerate(romSetName_list), key=lambda x:x[1])];
  romMain_list_sorted = [];
  romMain_list_sorted = [romMain_list[i] for i in sorted_idx];
  romMain_list = romMain_list_sorted;

  return romMain_list;

def create_copy_list(romMain_list, filter_config):
  "Creates the list of ROMs to be copied based on the ordered main ROM list"

  # --- Scan sourceDir to get the list of available ROMs
  print_info('[Scanning sourceDir for ROMs to be copied]');
  sourceDir = filter_config.sourceDir;
  rom_main_list = [];
  for file in os.listdir(sourceDir):
    if file.endswith(".zip"):
      rom_main_list.append(file);

  # - From the parent/clone list, pick the first available ROM (and
  #   not excluded) to be copied.
  print_info('[Creating list of ROMs to be copied/updated]');
  rom_copy_list = [];
  for mainROM_obj in romMain_list:
    num_set_files = len(mainROM_obj.filenames);
    for index in range(num_set_files):
      filename = mainROM_obj.filenames[index];
      includeFlag = mainROM_obj.include[index];
      if filename in rom_main_list and includeFlag:
        rom_copy_list.append(filename);
        # Only pick first ROM of the list available
        break;
  
  # --- Sort list alphabetically
  rom_copy_list_sorted = sorted(rom_copy_list);
  
  # --- Remove extension
  rom_copy_list_sorted_basename = [];
  for s in rom_copy_list_sorted:
    (name, extension) = os.path.splitext(s);
    rom_copy_list_sorted_basename.append(name);

  return rom_copy_list_sorted_basename;

# -----------------------------------------------------------------------------
# Main body functions
# -----------------------------------------------------------------------------
def do_list():
  "List of configuration file"

  print_info('[Listing configuration file]');
  print "Parsing configuration XML file " + __config_configFileName + "...",;
  sys.stdout.flush();
  try:
    tree = ET.parse(__config_configFileName);
  except IOError:
    print '\n';
    print_error('[ERROR] cannot find file ' + __config_configFileName);
    sys.exit(10);
  print 'done';

  # - This iterates through the collections
  root = tree.getroot();
  for collection in root:
    # print collection.tag, collection.attrib;
    print_info('<ROM Collection>');
    print_info('Short name      ' + collection.attrib['shortname']);
    print_info('Name            ' + collection.attrib['name']);

    # - For every collection, iterate over the elements
    # - This is not very efficient
    for collectionEL in collection:
      if collectionEL.tag == 'source':
        print_verb('Source          ' + collectionEL.text);
      elif collectionEL.tag == 'dest':
        print_verb('Destination     ' + collectionEL.text);
      elif collectionEL.tag == 'filterUpTags' and collectionEL.text is not None:
        print_verb('filterUpTags    ' + collectionEL.text);
      elif collectionEL.tag == 'filterDownTags' and collectionEL.text is not None:
        print_verb('filterDownTags  ' + collectionEL.text);
      elif collectionEL.tag == 'includeTags' and collectionEL.text is not None:
        print_verb('includeTags     ' + collectionEL.text);
      elif collectionEL.tag == 'excludeTags' and collectionEL.text is not None:
        print_verb('excludeTags     ' + collectionEL.text);
      elif collectionEL.tag == 'NoIntroDat' and collectionEL.text is not None:
        print_info('NoIntroDat      ' + collectionEL.text);

    # - Test if all mandatory elements are there
    # TODO: finish this

def do_list_nointro(filterName):
  "List of NoIntro XML file"
  print_info('[Listing No-Intro XML DAT]');
  print_info('Filter name = ' + filterName);
  filter_config = get_Filter_Config(filterName);
  filename = filter_config.NoIntro_XML;
  print_info('Parsing No-Intro XML DAT');
  print "Parsing No-Intro XML file " + filename + "...",;
  sys.stdout.flush();
  try:
    tree = ET.parse(filename);
  except IOError:
    print '\n';
    print_error('[ERROR] cannot find file ' + filename);
    sys.exit(10);
  print ' done';

  # Child elements (NoIntro pclone XML)
  # Create a list containing game name
  num_games = 0;
  root = tree.getroot();
  gameList = [];
  for game_EL in root:
    if game_EL.tag == 'game':
      num_games += 1;
      # --- Game attributes
      game_attrib = game_EL.attrib;
      # print '<game> ' + game_attrib['name'];
      gameList.append(game_attrib['name']);

      # --- Iterate through the children of a game
      # for game_child in game_EL:
      #   if game_child.tag == 'description':
      #     print '  <desc> ' + game_child.text;

  # Print game list in alphabetical order
  for game in sorted(gameList):
    print_info('<game> ' + game);
  print_info('Number of games in No-Intro XML DAT = ' + str(num_games));

def do_check_nointro(filterName):
  "List of NoIntro XML file"

  print_info('[Checking ROMs with No-Intro XML DAT]');
  print_info('Filter name = ' + filterName);
  filter_config = get_Filter_Config(filterName);
  filename = filter_config.NoIntro_XML;
  
  # --- Get parameters and check for errors
  sourceDir = filter_config.sourceDir;
  haveDir_or_abort(sourceDir);

  # Load No-Intro DAT
  if filename == None:
    print_error('[ERROR] No-Intro XML DAT not configured for this filer.');
    exit(10);
  print_info('Parsing No-Intro XML DAT');
  print "Parsing " + filename + "...",;
  sys.stdout.flush();
  try:
    tree = ET.parse(filename);
  except IOError:
    print '\n';
    print_error('\033[31m[ERROR]\033[0m cannot find file ' + filename);
    sys.exit(10);
  print ' done';
  
  # Child elements (NoIntro pclone XML):
  nointro_roms = [];
  num_games = 0;
  root = tree.getroot();
  for game_EL in root:
    if game_EL.tag == 'game':
      num_games += 1;
      # Game attributes
      game_attrib = game_EL.attrib;
      nointro_roms.append(game_attrib['name'] + '.zip');

  # Check how many ROMs we have in sourceDir and the DAT
  print_info('[Scanning ROMs in sourceDir]');
  have_roms = 0;
  unknown_roms = 0;
  file_list = [];
  for file in os.listdir(sourceDir):
    file_list.append(file);
  for file in sorted(file_list):
    if file.endswith(".zip"):
      if file in nointro_roms:
        have_roms += 1;
        print_vverb('<Have ROM  > ' + file);
      else:
        unknown_roms += 1;
        print_verb('<Unknown ROM> ' + file);

  # Check how many ROMs we have in the DAT not in sourceDir
  missing_roms = 0;  
  for game in sorted(nointro_roms):
    filename = sourceDir + game;
    if not os.path.isfile(filename):
      print_verb('<Missing ROM> ' + game);
      missing_roms += 1;

  print_info('[Report]');
  print_info('Games in DAT = ' + str(num_games));
  print_info('Have ROMs    = ' + str(have_roms));
  print_info('Missing ROMs = ' + str(missing_roms));
  print_info('Unknown ROMs = ' + str(unknown_roms));

def do_taglist(filterName):
  "Makes a histograms of the tags"

  print_info('[Listing tags]');
  print_info('Filter name = ' + filterName);
  filter_config = get_Filter_Config(filterName);
  sourceDir = filter_config.sourceDir;

  # Check if dest directory exists
  haveDir_or_abort(sourceDir);

  # Traverse directory, for every file extract properties, and add them to the
  # dictionary.
  propertiesDic = {};
  for file in os.listdir(sourceDir):
    if file.endswith(".zip"):
      romProperties = extract_ROM_Tags_All(file);
      if len(romProperties) == 0:
        print_error(file + 'Has no tags!');
        sys.exit(10);
      else:
        for property in romProperties:
          if propertiesDic.has_key(property):
            propertiesDic[property] += 1;
          else:
            propertiesDic[property] = 1;

  # http://stackoverflow.com/questions/613183/python-sort-a-dictionary-by-value
  sorted_propertiesDic = sorted(propertiesDic.iteritems(), key=operator.itemgetter(1))
  print_info('[Tag histogram]');
  for key in sorted_propertiesDic:
    print_info('{:6d}'.format(key[1]) + '  ' + key[0]);

def do_checkFilter(filterName):
  "Applies filter and prints filtered parent/clone list"

  print_info('[Check-filter ROM]');
  print_info('Filter name = ' + filterName);

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_Config(filterName);
  sourceDir = filter_config.sourceDir;

  # --- Check for errors, missing paths, etc...
  haveDir_or_abort(sourceDir);

  # --- Obtain main parent/clone list, either based on DAT or filelist
  if filter_config.NoIntro_XML == None:
    print_info('Using directory listing');
    romMainList_list = get_directory_Main_list(filter_config);
  else:
    print_info('Using No-Intro parent/clone DAT');
    romMainList_list = get_NoIntro_Main_list(filter_config);

  # --- Get tag list for every rom
  rom_Tag_dic = get_Tag_list(romMainList_list);
  
  # --- Calculate scores based on filters and reorder the main
  #     list with higher scores first. Also applies exclude/include filters.
  romMainList_list = get_Scores_and_Filter(romMainList_list, rom_Tag_dic, filter_config);

  # --- Print list in alphabetical order
  index_main = 0;
  for index_main in range(len(romMainList_list)):
    romObject = romMainList_list[index_main];
    print_info("<ROM set> " + romObject.setName);
    for index in range(len(romObject.filenames)):
      # --- Check if file exists (maybe it does not exist for No-Intro lists)
      sourceFullFilename = sourceDir + romObject.filenames[index];
      fullROMFilename = os.path.isfile(sourceFullFilename);
      haveFlag = 'H';
      if not os.path.isfile(sourceFullFilename):
        haveFlag = 'M';
      excludeFlag = 'I';
      if romObject.include[index] == 0:
        excludeFlag = 'E';

      # --- Print
      print_info('  ' + '{:2d} '.format(romObject.scores[index]) + \
                 '[' + excludeFlag + haveFlag + '] ' + \
                 romObject.filenames[index]);

# ----------------------------------------------------------------------------
# Update ROMs in destDir
def do_update(filterName):
  "Applies filter and updates (copies) ROMs"
  print_info('[Copy/Update ROMs]');
  print_info('Filter name = ' + filterName);

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_Config(filterName);
  sourceDir = filter_config.sourceDir;
  destDir = filter_config.destDir;

  # --- Check for errors, missing paths, etc...
  haveDir_or_abort(sourceDir);
  haveDir_or_abort(destDir);

  # --- Obtain main parent/clone list, either based on DAT or filelist
  if filter_config.NoIntro_XML == None:
    print_info('Using directory listing');
    romMainList_list = get_directory_Main_list(filter_config);
  else:
    print_info('Using No-Intro parent/clone DAT');
    romMainList_list = get_NoIntro_Main_list(filter_config);

  # --- Get tag list for every ROM
  rom_Tag_dic = get_Tag_list(romMainList_list);
  
  # --- Calculate scores based on filters and reorder the main
  #     list with higher scores first. Also applies exclude/include filters.
  romMainList_list = get_Scores_and_Filter(romMainList_list, rom_Tag_dic, filter_config);

  # --- Make a list of files to be copied, depending on ROMS present in
  #     sourceDir. Takes into account the ROM scores and the
  #     exclude/include filters.
  rom_copy_list = create_copy_list(romMainList_list, filter_config);
  
  # --- Copy/Update ROMs into destDir
  if __prog_option_sync:
    update_ROM_list(rom_copy_list, sourceDir, destDir);
  else:
    copy_ROM_list(rom_copy_list, sourceDir, destDir);  

  # --- If --cleanROMs is on then delete unknown files.
  if __prog_option_clean_ROMs:
    clean_ROMs_destDir(destDir, rom_copy_list);

  # --- Delete NFO files of ROMs not present in the destination directory.
  if __prog_option_clean_NFO:
    delete_redundant_NFO(destDir);

# ----------------------------------------------------------------------------
def do_checkArtwork(filterName):
  "Checks for missing artwork and prints a report"

  print_info('[Check-ArtWork]');
  print_info('Filter name = ' + filterName);

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_Config(filterName);
  destDir = filter_config.destDir;
  thumbsSourceDir = filter_config.thumbsSourceDir;
  fanartSourceDir = filter_config.fanartSourceDir;

  # --- Check for errors, missing paths, etc...
  haveDir_or_abort(destDir);
  haveDir_or_abort(thumbsSourceDir);
  haveDir_or_abort(fanartSourceDir);

  # --- Create a list of ROMs in destDir
  roms_destDir_list = [];
  for file in os.listdir(destDir):
    if file.endswith(".zip"):
      thisFileName, thisFileExtension = os.path.splitext(file);
      roms_destDir_list.append(thisFileName);

  # --- Obtain main parent/clone list, either based on DAT or filelist
  if filter_config.NoIntro_XML == None:
    print_info('Using directory listing');
    romMainList_list = get_directory_Main_list(filter_config);
  else:
    print_info('Using No-Intro parent/clone DAT');
    romMainList_list = get_NoIntro_Main_list(filter_config);

  # --- Replace missing artwork for alternative artwork in the parent/clone set
  artwork_copy_dic = optimize_ArtWork_list(roms_destDir_list, romMainList_list, filter_config);

  # --- Print list in alphabetical order
  print_info('[Artwork report]');
  num_original = 0;
  num_replaced = 0;
  num_have_thumbs = 0;
  num_missing_thumbs = 0;
  num_have_fanart = 0;
  num_missing_fanart = 0;
  for rom_baseName in sorted(roms_destDir_list):
    print_info("<<  ROM  >> " + rom_baseName + ".zip");    
    if rom_baseName not in artwork_copy_dic:
      print ' Not found';
    else:
      art_baseName = artwork_copy_dic[rom_baseName];
      
      # --- Check if artwork exist
      thumb_Source_fullFileName = thumbsSourceDir + art_baseName + '.png';
      fanart_Source_fullFileName = fanartSourceDir + art_baseName + '.png';

      # - Has artwork been replaced?
      if rom_baseName != art_baseName:
        num_original += 1;
        print ' Replaced   ' + art_baseName;
      else:
        num_replaced += 1;
        print ' Original   ' + art_baseName;

      # - Have thumb
      if not os.path.isfile(thumb_Source_fullFileName):
        num_missing_thumbs += 1;
        print ' Missing T  ' + art_baseName + '.png';
      else:
        num_have_thumbs += 1;
        print ' Have T     ' + art_baseName + '.png';

      # - Have fanart
      if not os.path.isfile(fanart_Source_fullFileName):
        num_missing_fanart += 1;
        print ' Missing F  ' + art_baseName + '.png';
      else:
        num_have_fanart += 1;
        print ' Have F     ' + art_baseName + '.png';

  print_info('Number of ROMs in destDir  = ' + str(len(roms_destDir_list)));
  print_info('Number of ArtWork found    = ' + str(len(artwork_copy_dic)));
  print_info('Number of original ArtWork = ' + str(num_original));
  print_info('Number of replaced ArtWork = ' + str(num_replaced));
  print_info('Number of have Thumbs    = ' + str(num_have_thumbs));
  print_info('Number of missing Thumbs = ' + str(num_missing_thumbs));
  print_info('Number of have Fanart    = ' + str(num_have_fanart));
  print_info('Number of missing Fanart = ' + str(num_missing_fanart));

# ----------------------------------------------------------------------------
def do_update_artwork(filterName):
  "Reads ROM destDir and copies Artwork"

  print_info('[Updating/copying ArtWork]');
  print_info('Filter name = ' + filterName);

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_Config(filterName);
  destDir = filter_config.destDir;
  thumbsSourceDir = filter_config.thumbsSourceDir;
  fanartSourceDir = filter_config.fanartSourceDir;

  # --- Check for errors, missing paths, etc...
  haveDir_or_abort(destDir);
  haveDir_or_abort(thumbsSourceDir);
  haveDir_or_abort(fanartSourceDir);

  # --- Create a list of ROMs in destDir
  roms_destDir_list = [];
  for file in os.listdir(destDir):
    if file.endswith(".zip"):
      thisFileName, thisFileExtension = os.path.splitext(file);
      roms_destDir_list.append(thisFileName);

  # --- Obtain main parent/clone list, either based on DAT or filelist
  if filter_config.NoIntro_XML == None:
    print_info('Using directory listing');
    romMainList_list = get_directory_Main_list(filter_config);
  else:
    print_info('Using No-Intro parent/clone DAT');
    romMainList_list = get_NoIntro_Main_list(filter_config);

  # --- Replace missing artwork for alternative artwork in the parent/clone set
  artwork_copy_dic = optimize_ArtWork_list(roms_destDir_list, romMainList_list, filter_config);

  # --- Copy artwork    
  if __prog_option_sync:
    update_ArtWork_list(filter_config, artwork_copy_dic);
  else:
    copy_ArtWork_list(filter_config, artwork_copy_dic);

  # --- If --cleanArtWork is on then delete unknown files.
  if __prog_option_clean_ArtWork:
    clean_ArtWork_destDir(filter_config, artwork_copy_dic);

def do_printHelp():
  print """
\033[32mUsage: xru-console.py [options] <command> [romSetName]\033[0m

\033[32mCommands:\033[0m
 \033[31m usage\033[0m
    Print usage information (this text)

 \033[31m list\033[0m
    List every ROM set system defined in the configuration file and some basic
    information. Use \033[35m--verbose\033[0m to get more information.

 \033[31m list-nointro <filterName>\033[0m
    List every ROM set system defined in the No-Intro DAT file.

 \033[31m check-nointro <filterName>\033[0m
    Scans the source directory and reads No-Intro XML data file. Checks if you
    have all the ROMs and reports the number of missing ROMs.

 \033[31m list-tags <filterName>\033[0m
    Scan the source directory and reports the total number of ROM files, all the
    tags found, and the number of ROMs that have each tag. It also display 
    tagless ROMs.

 \033[31m check-filter <filterName>\033[0m
    Applies ROM filters defined in the configuration file and prints a list of
    the scored ROMs. If a No-Intro DAT is configure for this filter it will be
    used.

 \033[31m copy <filterName>\033[0m
    Applies ROM filters defined in the configuration file and copies the 
    contents of sourceDir into destDir. This overwrites ROMs in destDir. No
    files will be removed on destDir.

 \033[31m update <filterName>\033[0m
    Like copy, but also delete ROMs in destDir not present in the filtered
    ROM list. Also, ROMs having same size in sourceDir and destDir will not be
    copied.

 \033[31m check-artwork <filterName>\033[0m
    Reads the ROMs in destDir, checks if you have the corresponding artwork 
    files, and prints a report.

 \033[31m copy-artwork <filterName>\033[0m
    Reads the ROMs in destDir and tries to copy the artwork to destination
    directory. If No-Intro DAT is available, missing artwork

 \033[31m update-artwork <filterName>\033[0m
    Like copy-artwork, but also delete unknown images in artwork destination
    directories. Artwork files having same size in sourceDir and destDir will 
    not be copied.

\033[32mOptions:
  \033[35m-h\033[0m, \033[35m--help\033[0m  Print short command reference.
  \033[35m-v\033[0m, \033[35m--verbose\033[0m  Print more information about what's going on.
  \033[35m-l\033[0m, \033[35m--log\033[0m  Save program output in xru-console-log.txt.
  \033[35m--logto\033[0m \033[31m[logName]\033[0m  Save program output in the file you specify.
  \033[35m--dryRun\033[0m  Don't modify destDir at all, just print the operations to be done.
  \033[35m--cleanROMs\033[0m  Deletes ROMs in destDir not present in the filtered ROM list.
  \033[35m--cleanNFO\033[0m  Deletes redundant NFO files in destination directory.
  \033[35m--cleanArtWork\033[0m  Deletes unknown artwork in destination."""

# -----------------------------------------------------------------------------
# main function
# -----------------------------------------------------------------------------
def main(argv):
  print '\033[36mXBMC ROM utilities - Console ROMs\033[0m' + \
        ' version ' + __software_version;

  # --- Command line parser
  parser = argparse.ArgumentParser()
  parser.add_argument('-v', '--verbose', help="be verbose", action="count")
  parser.add_argument('-l', '--log', help="log output to default file", \
     action='store_true')
  parser.add_argument('--logto', help="log output to specified file", \
     nargs = 1)
  parser.add_argument("--dryRun", help="don't modify any files", \
     action="store_true")
  parser.add_argument("--cleanROMs", help="clean destDir of unknown ROMs", \
     action="store_true")
  parser.add_argument("--cleanNFO", help="clean redundant NFO files", \
     action="store_true")
  parser.add_argument("--cleanArtWork", help="clean unknown ArtWork", \
     action="store_true")
  parser.add_argument("command", \
     help="usage, list, list-nointro, check-nointro, list-tags, \
           check-filter, copy, update \
           check-artwork, copy-artwork, update-artwork", nargs = 1)
  parser.add_argument("romSetName", help="ROM collection name", nargs='?')
  args = parser.parse_args();

  # --- Optional arguments
  # Needed to modify global copy of globvar
  global __prog_option_log, __prog_option_log_filename;
  global __prog_option_dry_run;
  global __prog_option_clean_ROMs;
  global __prog_option_clean_NFO;
  global __prog_option_clean_ArtWork;
  global __prog_option_sync; # 1 update, 0 copies

  if args.verbose:
    if args.verbose == 1:
      change_log_level(Log.verb);
    elif args.verbose == 2:
      change_log_level(Log.vverb);
    elif args.verbose >= 3:
      change_log_level(Log.debug);
  if args.log:
    __prog_option_log = 1;
  if args.logto:
    __prog_option_log = 1;
    __prog_option_log_filename = args.logto[0];
  if args.dryRun:       __prog_option_dry_run = 1;
  if args.cleanROMs:    __prog_option_clean_ROMs = 1;
  if args.cleanNFO:     __prog_option_clean_NFO = 1;
  if args.cleanArtWork: __prog_option_clean_ArtWork = 1;

  # --- Positional arguments that don't require parsing of the config file
  command = args.command[0];
  if command == 'usage':
    do_printHelp();
    sys.exit(0);

  # --- Read configuration file
  global configuration;
  configuration = parse_File_Config();

  # --- Positional arguments that don't require a romSetName
  if command == 'list':
    do_list();
    sys.exit(0);

  # --- Positional arguments that require a romSetName
  if args.romSetName == None:
    print_error('\033[31m[ERROR]\033[0m romSetName required');
    sys.exit(10);

  if command == 'list-nointro':
    do_list_nointro(args.romSetName);

  elif command == 'check-nointro':
    do_check_nointro(args.romSetName);

  elif command == 'list-tags':
    do_taglist(args.romSetName);

  elif command == 'check-filter':
    do_checkFilter(args.romSetName);

  elif command == 'copy':
    do_update(args.romSetName);

  elif command == 'update':
    __prog_option_sync = 1;
    do_update(args.romSetName);  

  elif command == 'check-artwork':
    do_checkArtwork(args.romSetName);

  elif command == 'copy-artwork':
    do_update_artwork(args.romSetName);

  elif command == 'update-artwork':
    __prog_option_sync = 1;
    do_update_artwork(args.romSetName);  

  else:
    print_error('Unrecognised command');
    sys.exit(1);

  sys.exit(0);

# No idea what's this...
if __name__ == "__main__":
  main(sys.argv[1:])
