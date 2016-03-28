#!/usr/bin/python3

# NARS Advanced ROM Sorting - Console ROMs
# Copyright (c) 2014-2016 Wintermute0110 <wintermute0110@gmail.com>
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
import NARS

# --- Global variables ---
__config_configFileName = 'nars-console-config.xml';
__config_logFileName = 'nars-console-log.txt';

# --- Program options (from command line) ---
__prog_option_log = 0;
__prog_option_log_filename = __config_logFileName;
__prog_option_dry_run = 0;
__prog_option_clean_ROMs = 0;
__prog_option_clean_NFO = 0;
__prog_option_clean_ArtWork = 0;
__prog_option_sync = 0;

# --- Config file options global class (like a C struct) ---
class ConfigFile:
  def __init__(self):
    self.filter_dic = {}

class ConfigFileFilter:
  def __init__(self):
    # By default things are None, which means user didn't wrote them in config
    # file OR no text was written ('', or blanks (spaces, tabs)).
    self.name            = None  # str
    self.shortname       = None  # str
    self.sourceDir       = None
    self.destDir         = None
    self.NoIntro_XML     = None
    self.fanartSourceDir = None
    self.fanartDestDir   = None
    self.thumbsSourceDir = None
    self.thumbsDestDir   = None
    self.filterUpTags    = None
    self.filterDownTags  = None
    self.includeTags     = None
    self.excludeTags     = None

# Global variable with the filter configuration 
configuration = ConfigFile();

# -----------------------------------------------------------------------------
# Configuration file functions
# -----------------------------------------------------------------------------
parse_rjust = 16

# Parses configuration file using ElementTree
# Returns a ConfigFile object
def parse_File_Config():
  NARS.print_info('[Parsing config file]');
  try:
    tree = ET.parse(__config_configFileName)
  except IOError:
    print_error('[ERROR] cannot find file ' + __config_configFileName)
    sys.exit(10)
  root = tree.getroot()

  # --- Configuration object returned ---
  configFile = ConfigFile()

  # --- Parse filters ---
  for root_child in root:
    if root_child.tag == 'collection':
      NARS.print_debug('{collection}')
      # --- Mandatory attributes of <collection> tag ---
      if 'name' not in root_child.attrib:
        NARS.print_error('<collection> tag does not have name attribute')
        sys.exit(10)
      if 'shortname' not in root_child.attrib:
        NARS.print_error('<collection> tag does not have shortname attribute')
        sys.exit(10)

      filter_class = ConfigFileFilter()
      filter_class.name = NARS.strip_string(root_child.attrib['name'])
      filter_class.shortname = NARS.strip_string(root_child.attrib['shortname'])
      NARS.print_debug('Name'.ljust(parse_rjust) + filter_class.name)
      NARS.print_debug('ShortName'.ljust(parse_rjust) + filter_class.shortname)

      # Parse filter (<collection> tags)
      # NOTE If tag is like this <tag></tag> then xml.text is None
      for filter_child in root_child:
        # ~~~ Directories ~~~
        if filter_child.tag == 'ROMsSource':
          string = NARS.strip_string(filter_child.text)
          filter_class.sourceDir = NARS.sanitize_dir_name(string)
          NARS.print_debug('ROMsSource'.ljust(parse_rjust) + filter_class.sourceDir)
        elif filter_child.tag == 'ROMsDest':
          string = NARS.strip_string(filter_child.text)
          filter_class.destDir = NARS.sanitize_dir_name(string) 
          NARS.print_debug('ROMsDest'.ljust(parse_rjust) + filter_class.destDir)          
        elif filter_child.tag == 'FanartSource':
          string = NARS.strip_string(filter_child.text)
          filter_class.fanartSourceDir = NARS.sanitize_dir_name(string)
          NARS.print_debug('FanartSource'.ljust(parse_rjust) + filter_class.fanartSourceDir)
        elif filter_child.tag == 'FanartDest':
          string = NARS.strip_string(filter_child.text)
          filter_class.fanartDestDir = NARS.sanitize_dir_name(string)
          NARS.print_debug('FanartDest'.ljust(parse_rjust) + filter_class.fanartDestDir)
        elif filter_child.tag == 'ThumbsSource':
          string = NARS.strip_string(filter_child.text)
          filter_class.thumbsSourceDir = NARS.sanitize_dir_name(string)
          NARS.print_debug('ThumbsSource'.ljust(parse_rjust) + filter_class.thumbsSourceDir)
        elif filter_child.tag == 'ThumbsDest':
          string = NARS.strip_string(filter_child.text)
          filter_class.thumbsDestDir = NARS.sanitize_dir_name(string)
          NARS.print_debug('ThumbsDest'.ljust(parse_rjust) + filter_class.thumbsDestDir)
        # ~~~ Files ~~~
        elif filter_child.tag == 'NoIntroDat':
          filter_class.NoIntro_XML = NARS.strip_string(filter_child.text)
          NARS.print_debug('NoIntroDat'.ljust(parse_rjust) + filter_class.NoIntro_XML)
        # ~~~ Comma separated strings ~~~
        elif filter_child.tag == 'filterUpTags':
          # Trim comma-separated string
          str = NARS.strip_string(filter_child.text)
          # If string is None then continue
          if str == None: continue
          # Trim each list element separately
          str_list = str.split(",")
          for index, item in enumerate(str_list):
            str_list[index] = NARS.strip_string(item)
          filter_class.filterUpTags = str_list
          NARS.print_debug('filterUpTags'.ljust(parse_rjust) + ', '.join(str_list))
        elif filter_child.tag == 'filterDownTags':
          str = NARS.strip_string(filter_child.text)
          if str == None: continue
          str_list = str.split(",")
          for index, item in enumerate(str_list):
            str_list[index] = NARS.strip_string(item)
          filter_class.filterDownTags = str_list
          NARS.print_debug('filterDownTags'.ljust(parse_rjust) + ', '.join(str_list))
        elif filter_child.tag == 'includeTags':
          str = NARS.strip_string(filter_child.text)
          if str == None: continue
          str_list = str.split(",")
          for index, item in enumerate(str_list):
            str_list[index] = NARS.strip_string(item)
          filter_class.includeTags = str_list
          NARS.print_debug('includeTags'.ljust(parse_rjust) + ', '.join(str_list))
        elif filter_child.tag == 'excludeTags':
          str = NARS.strip_string(filter_child.text)
          if str == None: continue
          str_list = str.split(",")
          for index, item in enumerate(str_list):
            str_list[index] = NARS.strip_string(item)
          filter_class.excludeTags = str_list
          NARS.print_debug('excludeTags'.ljust(parse_rjust) + ', '.join(str_list))
        else:
          print('[ERROR] Unrecognised tag {0} in configuration file'.format(filter_child.tag))
          sys.exit(10)

      # --- Aggregate filter to configuration main variable ---
      configFile.filter_dic[filter_class.shortname] = filter_class

  return configFile

def get_Filter_from_Config(filterName):
  "Returns the configuration filter object given the filter name"
  for key in configuration.filter_dic:
    if key == filterName:
      return configuration.filter_dic[key]

  print('[ERROR] get_Filter_from_Config >> filter "' + filterName + '" not found in configuration file')
  sys.exit(20)

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

  NARS.print_debug('Copying ' + sourceFullFilename);
  NARS.print_debug('Into    ' + destFullFilename);
  if not __prog_option_dry_run:
    try:
      shutil.copy(sourceFullFilename, destFullFilename)
    except EnvironmentError:
      NARS.print_debug("copy_ArtWork_file >> Error happened");

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
    NARS.print_debug('Updated ' + destFullFilename);
    return 2;

  # destFile does not exist or sizes are different, copy.
  NARS.print_debug('Copying ' + sourceFullFilename);
  NARS.print_debug('Into    ' + destFullFilename);
  if not __prog_option_dry_run:
    try:
      shutil.copy(sourceFullFilename, destFullFilename)
    except EnvironmentError:
      NARS.print_debug("update_ArtWork_file >> Error happened");

  return 0

# -----------------------------------------------------------------------------
def copy_ROM_list(rom_list, sourceDir, destDir):
  NARS.print_info('[Copying ROMs into destDir]');

  num_steps = len(rom_list);
  # 0 here prints [0, ..., 99%] instead [1, ..., 100%]
  step = 0;
  num_files = 0;
  num_copied_roms = 0;
  for rom_copy_item in sorted(rom_list):
    # --- Update progress
    percentage = 100 * step / num_steps;
    sys.stdout.write('{:5.2f}% '.format(percentage));

    # --- Copy file (this function succeeds or aborts program)
    romFileName = rom_copy_item + '.zip'
    source_path = sourceDir + romFileName
    dest_path = destDir + romFileName
    NARS.copy_file(source_path, dest_path, __prog_option_dry_run)
    num_copied_roms += 1;
    NARS.print_info('<Copied> ' + romFileName);
    sys.stdout.flush();

    # --- Update progress
    step += 1;

  NARS.print_info('[Report]');
  NARS.print_info('Copied ROMs ' + '{:6d}'.format(num_copied_roms));

def update_ROM_list(rom_list, sourceDir, destDir):
  NARS.print_info('[Updating ROMs into destDir]');
  
  num_steps = len(rom_list);
  # 0 here prints [0, ..., 99%] instead [1, ..., 100%]
  step = 0;
  num_copied_roms = 0;
  num_updated_roms = 0;
  for rom_copy_item in sorted(rom_list):
    # --- Update progress
    percentage = 100 * step / num_steps;

    # --- Copy file (this function succeeds or aborts program)
    romFileName = rom_copy_item + '.zip'
    source_path = sourceDir + romFileName
    dest_path = destDir + romFileName
    ret = NARS.update_file(source_path, dest_path, __prog_option_dry_run)
    if ret == 0:
      # On default verbosity level only report copied files
      sys.stdout.write('{:5.2f}% '.format(percentage));
      num_copied_roms += 1;
      NARS.print_info('<Copied > ' + romFileName);
    elif ret == 1:
      if NARS.log_level >= NARS.Log.verb:
        sys.stdout.write('{:5.2f}% '.format(percentage));
      num_updated_roms += 1;
      NARS.print_verb('<Updated> ' + romFileName);
    else:
      NARS.print_error('Wrong value returned by update_ROM_file()');
      sys.exit(10);
    sys.stdout.flush()

    # --- Update progress
    step += 1;

  NARS.print_info('[Report]');
  NARS.print_info('Copied ROMs ' + '{:6d}'.format(num_copied_roms));
  NARS.print_info('Updated ROMs ' + '{:5d}'.format(num_updated_roms));

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
  NARS.print_info('[Copying ArtWork]')
  fanartSourceDir = filter_config.fanartSourceDir
  fanartDestDir = filter_config.fanartDestDir
  thumbsSourceDir = filter_config.thumbsSourceDir
  thumbsDestDir = filter_config.thumbsDestDir
  
  # --- Check that directories exist
  NARS.have_dir_or_abort(thumbsSourceDir, 'thumbsSourceDir')
  NARS.have_dir_or_abort(thumbsDestDir, 'thumbsDestDir')
  NARS.have_dir_or_abort(fanartSourceDir, 'fanartSourceDir')
  NARS.have_dir_or_abort(fanartDestDir, 'fanartDestDir')
  
  # --- Copy artwork
  num_steps = len(rom_copy_dic)
  step = 0
  num_copied_thumbs = 0
  num_missing_thumbs = 0
  num_copied_fanart = 0
  num_missing_fanart = 0
  for rom_baseName in sorted(rom_copy_dic):
    # --- Get artwork name
    art_baseName = rom_copy_dic[rom_baseName];

    # --- Update progress
    percentage = 100 * step / num_steps
    sys.stdout.write('{:5.2f}% '.format(percentage))

    # --- Thumbs
    ret = copy_ArtWork_file(rom_baseName, art_baseName, thumbsSourceDir, thumbsDestDir)
    if ret == 0:
      num_copied_thumbs += 1;
      NARS.print_info('<Copied Thumb  > ' + art_baseName)
    elif ret == 1:
      num_missing_thumbs += 1;
      NARS.print_info('<Missing Thumb > ' + art_baseName)
    else:
      NARS.print_error('Wrong value returned by copy_ArtWork_file()')
      sys.exit(10)

    # --- Update progress
    percentage = 100 * step / num_steps;
    sys.stdout.write('{:5.2f}% '.format(percentage));

    # --- Fanart
    ret = copy_ArtWork_file(rom_baseName, art_baseName, fanartSourceDir, fanartDestDir);
    if ret == 0:
      num_copied_fanart += 1;
      NARS.print_info('<Copied Fanart > ' + art_baseName);
    elif ret == 1:
      num_missing_fanart += 1;
      NARS.print_info('<Missing Fanart> ' + art_baseName);
    else:
      print_error('Wrong value returned by copy_ArtWork_file()');
      sys.exit(10);

    # --- Update progress
    step += 1;

  NARS.print_info('[Report]');
  NARS.print_info('Copied thumbs ' + '{:6d}'.format(num_copied_thumbs))
  NARS.print_info('Missing thumbs ' + '{:5d}'.format(num_missing_thumbs))
  NARS.print_info('Copied fanart ' + '{:6d}'.format(num_copied_fanart))
  NARS.print_info('Missing fanart ' + '{:5d}'.format(num_missing_fanart))

def update_ArtWork_list(filter_config, rom_copy_dic):
  NARS.print_info('[Updating ArtWork]')
  
  thumbsSourceDir = filter_config.thumbsSourceDir
  thumbsDestDir = filter_config.thumbsDestDir
  fanartSourceDir = filter_config.fanartSourceDir
  fanartDestDir = filter_config.fanartDestDir

  # --- Check that directories exist
  NARS.have_dir_or_abort(thumbsSourceDir, 'thumbsSourceDir')
  NARS.have_dir_or_abort(thumbsDestDir, 'thumbsDestDir')
  NARS.have_dir_or_abort(fanartSourceDir, 'fanartSourceDir')
  NARS.have_dir_or_abort(fanartDestDir, 'fanartDestDir')
  
  # --- Copy/update artwork
  num_steps = len(rom_copy_dic)
  step = 0
  num_copied_thumbs = 0
  num_updated_thumbs = 0
  num_missing_thumbs = 0
  num_copied_fanart = 0
  num_updated_fanart = 0
  num_missing_fanart = 0
  for rom_baseName in sorted(rom_copy_dic):
    # --- Update progress
    percentage = 100 * step / num_steps;

    # --- Get artwork name
    art_baseName = rom_copy_dic[rom_baseName];

    # --- Thumbs
    ret = update_ArtWork_file(rom_baseName, art_baseName, thumbsSourceDir, thumbsDestDir);
    if ret == 0:
      # On default verbosity level only report copied files
      sys.stdout.write('{:5.2f}% '.format(percentage));
      num_copied_thumbs += 1;
      NARS.print_info('<Copied  Thumb > ' + art_baseName);
    elif ret == 1:
      # Also report missing artwork
      sys.stdout.write('{:5.2f}% '.format(percentage));
      num_missing_thumbs += 1;
      NARS.print_info('<Missing Thumb > ' + art_baseName);
    elif ret == 2:
      if NARS.log_level >= NARS.Log.verb:
        sys.stdout.write('{:5.2f}% '.format(percentage));
      num_updated_thumbs += 1;
      NARS.print_verb('<Updated Thumb > ' + art_baseName);
    else:
      print_error('Wrong value returned by copy_ArtWork_file()');
      sys.exit(10);

    # --- Fanart
    ret = update_ArtWork_file(rom_baseName, art_baseName, fanartSourceDir, fanartDestDir);
    if ret == 0:
      # Also report missing artwork
      sys.stdout.write('{:5.2f}% '.format(percentage));
      num_copied_fanart += 1;
      NARS.print_info('<Copied  Fanart> ' + art_baseName);
    elif ret == 1:
      # Also report missing artwork
      sys.stdout.write('{:5.2f}% '.format(percentage));
      num_missing_fanart += 1;
      NARS.print_info('<Missing Fanart> ' + art_baseName);
    elif ret == 2:
      if NARS.log_level >= NARS.Log.verb:
        sys.stdout.write('{:5.2f}% '.format(percentage));
      num_updated_fanart += 1;
      NARS.print_verb('<Updated Fanart> ' + art_baseName);
    else:
      print_error('Wrong value returned by copy_ArtWork_file()');
      sys.exit(10);

    # --- Update progress
    step += 1;

  NARS.print_info('[Report]');
  NARS.print_info('Copied thumbs ' + '{:6d}'.format(num_copied_thumbs));
  NARS.print_info('Updated thumbs ' + '{:5d}'.format(num_updated_thumbs));
  NARS.print_info('Missing thumbs ' + '{:5d}'.format(num_missing_thumbs));
  NARS.print_info('Copied fanart ' + '{:6d}'.format(num_copied_fanart));
  NARS.print_info('Updated fanart ' + '{:5d}'.format(num_updated_fanart));
  NARS.print_info('Missing fanart ' + '{:5d}'.format(num_missing_fanart));

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

  NARS.print_info('[Optimising ArtWork file list]');
  thumbsSourceDir = filter_config.thumbsSourceDir;
  thumbsDestDir = filter_config.thumbsDestDir;
  fanartSourceDir = filter_config.fanartSourceDir;
  fanartDestDir = filter_config.fanartDestDir;

  # --- Check that directories exist
  if not os.path.isdir(thumbsSourceDir):
    NARS.print_error('thumbsSourceDir not found ' + thumbsSourceDir);
    sys.exit(10);
  if not os.path.isdir(thumbsDestDir):
    NARS.print_error('thumbsDestDir not found ' + thumbsDestDir);
    sys.exit(10);
  if not os.path.isdir(fanartSourceDir):
    NARS.print_error('fanartSourceDir not found ' + fanartSourceDir);
    sys.exit(10);
  if not os.path.isdir(fanartDestDir):
    NARS.print_error('fanartDestDir not found ' + fanartDestDir);
    sys.exit(10);

  # - For every ROM to be copied (filtered) check if ArtWork exists. If not,
  #   try artwork of other ROMs in the parent/clone set.
  artwork_copy_dic = {};
  for rom_copy_item in rom_copy_list:
    romFileName = rom_copy_item + '.png';
    if __debug_optimize_ArtWork:
      print('<<Testing>> ', romFileName)
    if os.path.isfile(thumbsSourceDir + romFileName):
      if __debug_optimize_ArtWork:
        print(' Added      ', rom_copy_item)
      artwork_copy_dic[rom_copy_item] = rom_copy_item;
    else:
      if __debug_optimize_ArtWork:
        print(' NOT found  ', romFileName)
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
            print(' Added clone', root)
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
    print('extract_ROM_Properties_Raw >> Property list')
    print('\n'.join(romProperties_raw))
    print('\n')
  
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
      print('extract_ROM_Properties_All >> Property: ' + property)
    
    match = re.search(",", property);
    if match:
      # Re-parse the string and decompose into new properties
      subProperties = re.findall("([^\,]*)", property);
      for subPropertie in subProperties:
        if __debug_propertyParsers:
          print('extract_ROM_Properties_All >> subPropertie: "' + subPropertie + '"')
        # For some reason, this regular expresion search returns the matches and
        # also one empty string afterwards...
        # Non empty strings are "true", empty are "false"
        if subPropertie:
          # strip() is equivalent to Perl trim()
          subPropertieOK = subPropertie.strip();
          romProperties_all.append(subPropertieOK);
          if __debug_propertyParsers:
            print('extract_ROM_Properties_All >> Added subPropertie: "' + subPropertieOK + '"')
    else:
      romProperties_all.append(property);

  # Debug print
  if __debug_propertyParsers:
    print('extract_ROM_Properties_All >> Property list')
    print('\n'.join(romProperties_all))
    print('\n')
  
  return romProperties_all;

def get_ROM_baseName(romFileName):
  "Get baseName from filename (no extension, no tags)"
  
  rom_baseName = '';
  regSearch = re.search("[^\(\)]*", romFileName);
  if regSearch == None:
    print('Logical error')
    sys.exit(10)
  regExp_result = regSearch.group()
  
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
  """Parses NoInto XML and makes a parent-clone list"""
  __debug_parse_NoIntro_XML_Config = 0;
  
  XML_filename = filter_config.NoIntro_XML;
  tree = NARS.XML_read_file_ElementTree(XML_filename, 'Parsing No-Intro XML DAT')

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
        print('Game = ' + romName)

      if 'cloneof' in game_attrib:
        num_clones += 1;
        romObject.cloneof = game_attrib['cloneof'];
        romObject.isclone = 1;
        if __debug_parse_NoIntro_XML_Config:
          print(' Clone of = ' + game_attrib['cloneof'])
      else:
        num_parents += 1;
        romObject.isclone = 0;

      # Add new game to the list
      rom_raw_dict[romName] = romObject;
  del tree;
  NARS.print_info('Total number of games = ' + str(num_games));
  NARS.print_info('Number of parents = ' + str(num_parents));
  NARS.print_info('Number of clones = ' + str(num_clones));

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
        print('Game "' + key + '"')
        print('Parent "' + gameObj.cloneof + '"')
        print('Parent ROM not found "' + gameObj.cloneof + '"')
        sys.exit(10)
    else:
      num_parents += 1;

  # DEBUG: print parent-clone list
  for key in rom_pclone_dict:
    romObj = rom_pclone_dict[key];
    NARS.print_debug(" <Parent> '" + romObj.baseName + "'");
    if romObj.hasClones:
      for clone in romObj.clone_list:
        NARS.print_debug("  <Clone> '" + clone + "'");

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
  NARS.print_info('[Reading ROMs in source dir]');
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
        print("  ROM       '" + romObject.fileName + "'")
        print("   baseName '" + romObject.baseName + "'")
  NARS.print_info('Found ' + str(num_ROMs_sourceDir) + ' ROMs')
  
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
  NARS.print_info('[Filtering ROMs]');
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
    print("[DEBUG main ROM list scored]")
    for mainROM_obj in romMain_list:
      print(mainROM_obj.filenames)
      print(mainROM_obj.scores)
      print(mainROM_obj.include)

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
  NARS.print_info('[Scanning sourceDir for ROMs to be copied]');
  sourceDir = filter_config.sourceDir;
  rom_main_list = [];
  for file in os.listdir(sourceDir):
    if file.endswith(".zip"):
      rom_main_list.append(file);

  # - From the parent/clone list, pick the first available ROM (and
  #   not excluded) to be copied.
  NARS.print_info('[Creating list of ROMs to be copied/updated]');
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
def do_list_filters():
  "List of configuration file"

  NARS.print_info('[Listing configuration file]')
  tree = NARS.XML_read_file_ElementTree(__config_configFileName, "Parsing configuration XML file")

  # - This iterates through the collections
  root = tree.getroot();
  for collection in root:
    # print collection.tag, collection.attrib;
    NARS.print_info('<ROM Collection>');
    NARS.print_info('Short name      ' + collection.attrib['shortname']);
    NARS.print_info('Name            ' + collection.attrib['name']);

    # - For every collection, iterate over the elements
    # - This is not very efficient
    for collectionEL in collection:
      if collectionEL.tag == 'source':
        NARS.print_verb('Source          ' + collectionEL.text);
      elif collectionEL.tag == 'dest':
        NARS.print_verb('Destination     ' + collectionEL.text);
      elif collectionEL.tag == 'filterUpTags' and collectionEL.text is not None:
        NARS.print_verb('filterUpTags    ' + collectionEL.text);
      elif collectionEL.tag == 'filterDownTags' and collectionEL.text is not None:
        NARS.print_verb('filterDownTags  ' + collectionEL.text);
      elif collectionEL.tag == 'includeTags' and collectionEL.text is not None:
        NARS.print_verb('includeTags     ' + collectionEL.text);
      elif collectionEL.tag == 'excludeTags' and collectionEL.text is not None:
        NARS.print_verb('excludeTags     ' + collectionEL.text);
      elif collectionEL.tag == 'NoIntroDat' and collectionEL.text is not None:
        NARS.print_info('NoIntroDat      ' + collectionEL.text);

    # Test if all mandatory elements are there
    # TODO finish this

def do_list_nointro(filterName):
  "List of NoIntro XML file"
  NARS.print_info('[Listing No-Intro XML DAT]');
  NARS.print_info('Filter name: ' + filterName);
  filter_config = get_Filter_Config(filterName);
  filename = filter_config.NoIntro_XML;
  tree = NARS.XML_read_file_ElementTree(filename, "Parsing No-Intro XML DAT file ")

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
    NARS.print_info('<game> ' + game);
  NARS.print_info('Number of games in No-Intro XML DAT = ' + str(num_games));

def do_check_nointro(filterName):
  """Checks ROMs in sourceDir against NoIntro XML file"""

  NARS.print_info('[Checking ROMs against No-Intro XML DAT]')
  NARS.print_info('Filter name = ' + filterName)
  filter_config = get_Filter_Config(filterName)

  # --- Get parameters and check for errors
  sourceDir = filter_config.sourceDir
  NARS.have_dir_or_abort(sourceDir, 'sourceDir')

  # --- Load No-Intro DAT
  XML_filename = filter_config.NoIntro_XML
  if XML_filename == None:
    print_error('[ERROR] No-Intro XML DAT not configured for this filer.')
    sys.exit(10)
  tree = NARS.XML_read_file_ElementTree(XML_filename, "Parsing No-Intro XML DAT file ")

  # Child elements (NoIntro pclone XML):
  nointro_roms = []
  num_games = 0
  root = tree.getroot()
  for game_EL in root:
    if game_EL.tag == 'game':
      num_games += 1
      # Game attributes
      game_attrib = game_EL.attrib
      nointro_roms.append(game_attrib['name'] + '.zip')

  # Check how many ROMs we have in sourceDir and the DAT
  NARS.print_info('[Scanning ROMs in sourceDir]');
  have_roms = 0;
  unknown_roms = 0;
  file_list = [];
  for file in os.listdir(sourceDir):
    file_list.append(file);
  for file in sorted(file_list):
    if file.endswith(".zip"):
      if file in nointro_roms:
        have_roms += 1;
        NARS.print_vverb('<Have ROM  > ' + file);
      else:
        unknown_roms += 1;
        NARS.print_verb('<Unknown ROM> ' + file);

  # Check how many ROMs we have in the DAT not in sourceDir
  missing_roms = 0;  
  for game in sorted(nointro_roms):
    filename = sourceDir + game;
    if not os.path.isfile(filename):
      NARS.print_verb('<Missing ROM> ' + game);
      missing_roms += 1;

  NARS.print_info('[Report]');
  NARS.print_info('Files in sourceDir: ' + str(len(file_list)));
  NARS.print_info('Games in DAT      : ' + str(num_games));
  NARS.print_info('Have ROMs         : ' + str(have_roms));
  NARS.print_info('Missing ROMs      : ' + str(missing_roms));
  NARS.print_info('Unknown ROMs      : ' + str(unknown_roms));

def do_taglist(filterName):
  """Makes a histograms of the tags of the ROMs in sourceDir"""

  NARS.print_info('[Listing tags]');
  NARS.print_info('Filter name = ' + filterName);
  filter_config = get_Filter_Config(filterName);
  sourceDir = filter_config.sourceDir;

  # Check if dest directory exists
  NARS.have_dir_or_abort(sourceDir, 'sourceDir');

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
          if property in propertiesDic:
            propertiesDic[property] += 1;
          else:
            propertiesDic[property] = 1;

  # Works for Python 2
  # http://stackoverflow.com/questions/613183/python-sort-a-dictionary-by-value
  # sorted_propertiesDic = sorted(propertiesDic.iteritems(), key=operator.itemgetter(1))
  # This works on Python 3
  sorted_propertiesDic = ((k, propertiesDic[k]) for k in sorted(propertiesDic, key=propertiesDic.get, reverse=False))
    
  NARS.print_info('[Tag histogram]');
  for key in sorted_propertiesDic:
    NARS.print_info('{:6d}'.format(key[1]) + '  ' + key[0]);

# ----------------------------------------------------------------------------
def do_checkFilter(filterName):
  """Applies filter and prints filtered parent/clone list"""

  NARS.print_info('[Check-filter ROM]');
  NARS.print_info('Filter name = ' + filterName);

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_Config(filterName);
  sourceDir = filter_config.sourceDir;

  # --- Check for errors, missing paths, etc...
  NARS.have_dir_or_abort(sourceDir, 'sourceDir');

  # --- Obtain main parent/clone list, either based on DAT or filelist
  if filter_config.NoIntro_XML == None:
    NARS.print_info('Using directory listing');
    romMainList_list = get_directory_Main_list(filter_config);
  else:
    NARS.print_info('Using No-Intro parent/clone DAT');
    romMainList_list = get_NoIntro_Main_list(filter_config);

  # --- Get tag list for every rom
  rom_Tag_dic = get_Tag_list(romMainList_list);
  
  # --- Calculate scores based on filters and reorder the main
  #     list with higher scores first. Also applies exclude/include filters.
  romMainList_list = get_Scores_and_Filter(romMainList_list, rom_Tag_dic, filter_config);

  # --- Print list in alphabetical order
  NARS.print_info("[List of scored parent/clone ROM sets]")
  index_main = 0;
  for index_main in range(len(romMainList_list)):
    romObject = romMainList_list[index_main];
    NARS.print_info("<ROM set> " + romObject.setName);
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
      NARS.print_info('  ' + '{:2d} '.format(romObject.scores[index]) + \
                      '[' + excludeFlag + haveFlag + '] ' + \
                      romObject.filenames[index]);

# ----------------------------------------------------------------------------
# Update ROMs in destDir
def do_update(filterName):
  "Applies filter and updates (copies) ROMs"
  NARS.print_info('[Copy/Update ROMs]')
  NARS.print_info('Filter name: ' + filterName)

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_Config(filterName)
  sourceDir = filter_config.sourceDir
  destDir = filter_config.destDir

  # --- Check for errors, missing paths, etc...
  NARS.print_info('Source directory     : ' + sourceDir)
  NARS.print_info('Destination directory: ' + destDir)
  NARS.have_dir_or_abort(sourceDir, 'sourceDir')
  NARS.have_dir_or_abort(destDir, 'destDir')

  # --- Obtain main parent/clone list, either based on DAT or filelist
  if filter_config.NoIntro_XML == None:
    NARS.print_info('Using directory listing');
    romMainList_list = get_directory_Main_list(filter_config);
  else:
    NARS.print_info('Using No-Intro parent/clone DAT');
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

  NARS.print_info('[Check-ArtWork]');
  NARS.print_info('Filter name = ' + filterName);

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_Config(filterName);
  destDir = filter_config.destDir;
  thumbsSourceDir = filter_config.thumbsSourceDir;
  fanartSourceDir = filter_config.fanartSourceDir;

  # --- Check for errors, missing paths, etc...
  NARS.have_dir_or_abort(destDir, 'destDir');
  NARS.have_dir_or_abort(thumbsSourceDir, 'thumbsSourceDir');
  NARS.have_dir_or_abort(fanartSourceDir, 'fanartSourceDir');

  # --- Create a list of ROMs in destDir
  roms_destDir_list = [];
  for file in os.listdir(destDir):
    if file.endswith(".zip"):
      thisFileName, thisFileExtension = os.path.splitext(file);
      roms_destDir_list.append(thisFileName);

  # --- Obtain main parent/clone list, either based on DAT or filelist
  if filter_config.NoIntro_XML == None:
    NARS.print_info('Using directory listing');
    romMainList_list = get_directory_Main_list(filter_config);
  else:
    NARS.print_info('Using No-Intro parent/clone DAT');
    romMainList_list = get_NoIntro_Main_list(filter_config);

  # --- Replace missing artwork for alternative artwork in the parent/clone set
  artwork_copy_dic = optimize_ArtWork_list(roms_destDir_list, romMainList_list, filter_config);

  # --- Print list in alphabetical order
  NARS.print_info('[Artwork report]');
  num_original = 0;
  num_replaced = 0;
  num_have_thumbs = 0;
  num_missing_thumbs = 0;
  num_have_fanart = 0;
  num_missing_fanart = 0;
  for rom_baseName in sorted(roms_destDir_list):
    NARS.print_info("<<  ROM  >> " + rom_baseName + ".zip");    
    if rom_baseName not in artwork_copy_dic:
      print(' Not found')
    else:
      art_baseName = artwork_copy_dic[rom_baseName];
      
      # --- Check if artwork exist
      thumb_Source_fullFileName = thumbsSourceDir + art_baseName + '.png';
      fanart_Source_fullFileName = fanartSourceDir + art_baseName + '.png';

      # - Has artwork been replaced?
      if rom_baseName != art_baseName:
        num_replaced += 1;
        print(' Replaced   ' + art_baseName)
      else:
        num_original += 1;
        print(' Original   ' + art_baseName)

      # - Have thumb
      if not os.path.isfile(thumb_Source_fullFileName):
        num_missing_thumbs += 1;
        print(' Missing T  ' + art_baseName + '.png')
      else:
        num_have_thumbs += 1;
        print(' Have T     ' + art_baseName + '.png')

      # - Have fanart
      if not os.path.isfile(fanart_Source_fullFileName):
        num_missing_fanart += 1;
        print(' Missing F  ' + art_baseName + '.png')
      else:
        num_have_fanart += 1;
        print(' Have F     ' + art_baseName + '.png')

  NARS.print_info('Number of ROMs in destDir  = ' + str(len(roms_destDir_list)));
  NARS.print_info('Number of ArtWork found    = ' + str(len(artwork_copy_dic)));
  NARS.print_info('Number of original ArtWork = ' + str(num_original));
  NARS.print_info('Number of replaced ArtWork = ' + str(num_replaced));
  NARS.print_info('Number of have Thumbs    = ' + str(num_have_thumbs));
  NARS.print_info('Number of missing Thumbs = ' + str(num_missing_thumbs));
  NARS.print_info('Number of have Fanart    = ' + str(num_have_fanart));
  NARS.print_info('Number of missing Fanart = ' + str(num_missing_fanart));

# ----------------------------------------------------------------------------
def do_update_artwork(filterName):
  "Reads ROM destDir and copies Artwork"

  NARS.print_info('[Updating/copying ArtWork]');
  NARS.print_info('Filter name = ' + filterName);

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_Config(filterName);
  destDir = filter_config.destDir;
  thumbsSourceDir = filter_config.thumbsSourceDir;
  fanartSourceDir = filter_config.fanartSourceDir;

  # --- Check for errors, missing paths, etc...
  NARS.have_dir_or_abort(destDir, 'destDir');
  NARS.have_dir_or_abort(thumbsSourceDir, 'thumbsSourceDir');
  NARS.have_dir_or_abort(fanartSourceDir, 'fanartSourceDir');

  # --- Create a list of ROMs in destDir
  roms_destDir_list = [];
  for file in os.listdir(destDir):
    if file.endswith(".zip"):
      thisFileName, thisFileExtension = os.path.splitext(file);
      roms_destDir_list.append(thisFileName);

  # --- Obtain main parent/clone list, either based on DAT or filelist
  if filter_config.NoIntro_XML == None:
    NARS.print_info('Using directory listing');
    romMainList_list = get_directory_Main_list(filter_config);
  else:
    NARS.print_info('Using No-Intro parent/clone DAT');
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
  print("""\033[32mUsage: nars-console.py [options] <command> [romSetName]\033[0m

\033[32mCommands:\033[0m
\033[31musage\033[0m                   Print usage information (this text)
\033[31mlist-filters\033[0m            List every filter defined in the configuration file.
\033[31mlist-nointro <filter>\033[0m   List every ROM set system defined in the No-Intro DAT file.
\033[31mcheck-nointro <filter>\033[0m  Checks the ROMs you have and reports missing ROMs.
\033[31mlist-tags <filter>\033[0m      Scan the source directory and reports the tags found.
\033[31mcheck <filter>\033[0m          Applies ROM filters and prints a list of the scored ROMs.
\033[31mcopy <filter>\033[0m           Applies ROM filters defined and copies ROMS from sourceDir into destDir.
\033[31mupdate <filter>\033[0m         Like copy, but also delete unneeded ROMs in destDir.
\033[31mcheck-artwork <filter>\033[0m  Reads the ROMs in destDir, checks if you have the corresponding artwork. 
\033[31mcopy-artwork <filter>\033[0m   Reads the ROMs in destDir and tries to copy the artwork to destDir.
\033[31mupdate-artwork <filter>\033[0m Like copy-artwork, but also delete unknown images in artwork destDir.

\033[32mOptions:
\033[35m-h\033[0m, \033[35m--help\033[0m         Print short command reference.
\033[35m-v\033[0m, \033[35m--verbose\033[0m      Print more information about what's going on.
\033[35m-l\033[0m, \033[35m--log\033[0m          Save program output in xru-console-log.txt.
\033[35m--logto\033[0m \033[31m[logName]\033[0m  Save program output in the file you specify.
\033[35m--dryRun\033[0m           Don't modify destDir at all, just print the operations to be done.
\033[35m--cleanROMs\033[0m        Deletes ROMs in destDir not present in the filtered ROM list.
\033[35m--cleanNFO\033[0m         Deletes redundant NFO files in destination directory.
\033[35m--cleanArtWork\033[0m     Deletes unknown artwork in destination.""")

# -----------------------------------------------------------------------------
# main function
# -----------------------------------------------------------------------------
def main(argv):
  print('\033[36mNARS Advanced ROM Sorting - Console ROMs\033[0m' + \
        ' version ' + NARS.__software_version)

  # --- Command line parser
  parser = argparse.ArgumentParser()
  parser.add_argument('-v', '--verbose', help="be verbose", action="count")
  parser.add_argument('-l', '--log', help="log output to default file", action='store_true')
  parser.add_argument('--logto', help="log output to specified file", nargs = 1)
  parser.add_argument('--dryRun', help="don't modify any files", action="store_true")
  parser.add_argument('--cleanROMs', help="clean destDir of unknown ROMs", action="store_true")
  parser.add_argument('--cleanNFO', help="clean redundant NFO files", action="store_true")
  parser.add_argument('--cleanArtWork', help="clean unknown ArtWork", action="store_true")
  parser.add_argument('command', \
     help="usage, list-filters, list-nointro, check-nointro, list-tags, \
           check, copy, update \
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
      NARS.change_log_level(NARS.Log.verb)
      NARS.print_info('Verbosity level set to VERBOSE')
    elif args.verbose == 2: 
      NARS.change_log_level(NARS.Log.vverb)
      NARS.print_info('Verbosity level set to VERY VERBOSE')
    elif args.verbose >= 3: 
      NARS.change_log_level(NARS.Log.debug)
      NARS.print_info('Verbosity level set to DEBUG')
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
  if command == 'list-filters':
    do_list_filters()

  elif command == 'list-nointro':
    if args.romSetName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m romSetName required')
      sys.exit(10)
    do_list_nointro(args.romSetName)

  elif command == 'check-nointro':
    if args.romSetName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m romSetName required')
      sys.exit(10)
    do_check_nointro(args.romSetName)

  elif command == 'list-tags':
    if args.romSetName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m romSetName required')
      sys.exit(10)
    do_taglist(args.romSetName)

  elif command == 'check':
    if args.romSetName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m romSetName required')
      sys.exit(10)
    do_checkFilter(args.romSetName)

  elif command == 'copy':
    if args.romSetName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m romSetName required')
      sys.exit(10)
    do_update(args.romSetName)

  elif command == 'update':
    if args.romSetName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m romSetName required')
      sys.exit(10)
    __prog_option_sync = 1
    do_update(args.romSetName)

  elif command == 'check-artwork':
    if args.romSetName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m romSetName required')
      sys.exit(10)
    do_checkArtwork(args.romSetName)

  elif command == 'copy-artwork':
    if args.romSetName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m romSetName required')
      sys.exit(10)
    do_update_artwork(args.romSetName)

  elif command == 'update-artwork':
    if args.romSetName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m romSetName required')
      sys.exit(10)
    __prog_option_sync = 1
    do_update_artwork(args.romSetName)

  else:
    NARS.print_error('Unrecognised command ' + command)
    sys.exit(1)

  sys.exit(0)

# Execute main function if script called from command line (not imported 
# as module)
if __name__ == "__main__":
  main(sys.argv[1:])
