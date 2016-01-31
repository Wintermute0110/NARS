#!/usr/bin/python3

# NARS Advanced ROM Sorting - MAME
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

# --- Import stuff
import sys, os, re, shutil
import operator, argparse
import NARS

# MAME XML is written by this file:
# http://www.mamedev.org/source/src/emu/info.c.html

# --- Global variables ---
__config_configFileName = 'nars-mame-config.xml';
__config_logFileName = 'nars-mame-log.txt';

# --- Program options (from command line)
__prog_option_log = 0;
__prog_option_log_filename = __config_logFileName;
__prog_option_dry_run = 0;
__prog_option_clean_ROMs = 0;
__prog_option_generate_NFO = 0;
__prog_option_clean_NFO = 0;
__prog_option_clean_ArtWork = 0;
__prog_option_clean_CHD = 0;
__prog_option_sync = 0;

# -----------------------------------------------------------------------------
# Configuration file
# -----------------------------------------------------------------------------
# --- Config file options global class (like a C struct) ---
class ConfigFile:
  pass
class ConfigFileFilter:
  pass
configuration = ConfigFile();

# -----------------------------------------------------------------------------
# Filesystem interaction functions
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

  NARS.print_debug(' Copying ' + sourceFullFilename);
  NARS.print_debug(' Into    ' + destFullFilename);
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
    NARS.print_debug(' Updated ' + destFullFilename);
    return 2;

  # destFile does not exist or sizes are different, copy.
  NARS.print_debug(' Copying ' + sourceFullFilename);
  NARS.print_debug(' Into    ' + destFullFilename);
  if not __prog_option_dry_run:
    try:
      shutil.copy(sourceFullFilename, destFullFilename)
    except EnvironmentError:
      NARS.print_debug("update_ArtWork_file >> Error happened");

  return 0

# Returns:
#  0 no error
# -1 copy error (exception)
def copy_CHD_file(romName, chdName, sourceDir, destDir):
  sourceFullFilename = sourceDir + romName + '/' + chdName;
  destFullFilename = destDir + romName + '/' + chdName;
  chdDestDir = destDir + romName;

  print_debug(' Copying     ' + sourceFullFilename);
  print_debug('      Into        ' + destFullFilename);
  print_debug('      CHD destDir ' + chdDestDir);

  existsSource = os.path.isfile(sourceFullFilename);
  if not existsSource:
    return 2;

  ret = 0;
  if not __prog_option_dry_run:
    # --- Create CHD destination directory if needed
    if not os.path.isdir(chdDestDir):
      os.makedirs(chdDestDir);
    # --- Copy CHD file
    try:
      shutil.copy(sourceFullFilename, destFullFilename)
    except EnvironmentError:
      ret = -1;
      print_debug("copy_CHD_file() >> Error happened when copying file");

  return ret;

# Returns:
#  0 - File copied (sizes different)
#  1 - File not copied (updated)
#  2 - source CHD not found (missing CHD)
# -1 - copy error (exception)
def update_CHD_file(romName, chdName, sourceDir, destDir):
  sourceFullFilename = sourceDir + romName + '/' + chdName;
  destFullFilename = destDir + romName + '/' + chdName;
  chdDestDir = destDir + romName;

  print_debug(' Updating   ' + sourceFullFilename);
  print_debug('      Into        ' + destFullFilename);
  print_debug('      CHD destDir ' + chdDestDir);

  existsSource = os.path.isfile(sourceFullFilename);
  existsDest = os.path.isfile(destFullFilename);
  if not existsSource:
    return 2;

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
    # --- Create CHD destination directory if needed
    if not os.path.isdir(chdDestDir):
      os.makedirs(chdDestDir);
    # --- Copy file
    try:
      shutil.copy(sourceFullFilename, destFullFilename)
    except EnvironmentError:
      print_debug("update_CHD_file >> Error happened");
      return -1;

  return 0;

def haveDir_or_abort(dirName, infoStr = None):
  if infoStr == None:
    if dirName == None:
      print_error('\033[31m[ERROR]\033[0m Directory not configured');
      sys.exit(10);
  else:
    if dirName == None:
      print_error('\033[31m[ERROR]\033[0m Directory ' + infoStr + ' not configured');
      sys.exit(10);

  if not os.path.isdir(dirName):
    print_error('\033[31m[ERROR]\033[0m Directory does not exist ' + dirName);
    sys.exit(10);

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
    sys.stdout.write('{:2.0f}% '.format(percentage));

    # --- Copy file (this function succeeds or aborts program)
    romFileName = rom_copy_item + '.zip';
    NARS.copy_ROM_file(romFileName, sourceDir, destDir, __prog_option_dry_run);
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
    romFileName = rom_copy_item + '.zip';
    ret = NARS.update_ROM_file(romFileName, sourceDir, destDir, __prog_option_dry_run);
    if ret == 0:
      # On default verbosity level only report copied files
      sys.stdout.write('{:3.0f}% '.format(percentage));
      num_copied_roms += 1;
      NARS.print_info('<Copied > ' + romFileName);
    elif ret == 1:
      if NARS.log_level >= NARS.Log.verb:
        sys.stdout.write('{:3.0f}% '.format(percentage));
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

def copy_CHD_dic(chd_dic, sourceDir, destDir):
  NARS.print_info('[Copying CHDs into destDir]');

  # * If user did not configure CHDs source directory then do nothing
  if sourceDir == None or sourceDir == '':
    NARS.print_info('CHD source directory not configured');
    NARS.print_info('Skipping CHD copy');
    return

  if not os.path.exists(sourceDir):
    NARS.print_error('CHD source directory not found ' + sourceDir)
    sys.exit(10);

  # * Copy CHDs
  num_steps = len(chd_dic);
  step = 0; # 0 here prints [0, ..., 99%], 1 prints [1, ..., 100%]
  num_files = 0;
  num_copied_CHDs = 0;
  for chd_copy_key in sorted(chd_dic):
    # --- Update progress
    percentage = 100 * step / num_steps;
    sys.stdout.write('{:3d}% '.format(percentage));

    # --- Copy file (this function succeeds or aborts program)
    chdFileName = chd_dic[chd_copy_key] + '.chd';
    ret = copy_CHD_file(chd_copy_key, chdFileName, sourceDir, destDir);
    if ret == 0:
      num_copied_CHDs += 1;
      print_info('<Copied > ' + chd_copy_key + '/' + chdFileName);
    elif ret == 2:
      print_info('<Missing> ' + chd_copy_key + '/' + chdFileName);
    elif ret == -1:
      print_info('<ERROR  > ' + chd_copy_key + '/' + chdFileName);
    else:
      print_error('Wrong value returned by copy_CHD_file()');
      sys.exit(10);
    sys.stdout.flush();

    # --- Update progress
    step += 1;

  NARS.print_info('[Report]');
  NARS.print_info('Copied CHDs ' + '{:6d}'.format(num_copied_CHDs));

def update_CHD_dic(chd_dic, sourceDir, destDir):
  NARS.print_info('[Updating CHDs into destDir]');

  # * If user did not configure CHDs source directory then do nothing
  if sourceDir == None or sourceDir == '':
    NARS.print_info('CHD source directory not configured');
    NARS.print_info('Skipping CHD copy');
    return

  if not os.path.exists(sourceDir):
    NARS.print_error('CHD source directory not found ' + sourceDir)
    sys.exit(10)

  num_steps = len(chd_dic);
  step = 0; # 0 here prints [0, ..., 99%], 1 prints [1, ..., 100%]
  num_copied_CHDs = 0;
  num_updated_CHDs = 0;
  for chd_copy_key in sorted(chd_dic):
    # --- Update progress
    percentage = 100 * step / num_steps;

    # --- Copy file (this function succeeds or aborts program)
    chdFileName = chd_dic[chd_copy_key] + '.chd';
    ret = update_CHD_file(chd_copy_key, chdFileName, sourceDir, destDir);
    if ret == 0:
      # On default verbosity level only report copied files
      sys.stdout.write('{:3.0f}% '.format(percentage));
      num_copied_CHDs += 1;
      NARS.print_info('<Copied > ' + chd_copy_key + '/' + chdFileName);
    elif ret == 1:
      if log_level >= Log.verb:
        sys.stdout.write('{:3.0f}% '.format(percentage));
      num_updated_CHDs += 1;
      NARS.print_verb('<Updated> ' + chd_copy_key + '/' + chdFileName);
    elif ret == 2:
      sys.stdout.write('{:3.0f}% '.format(percentage));
      NARS.print_info('<Missing> ' + chd_copy_key + '/' + chdFileName);
    elif ret == -1:
      sys.stdout.write('{:3.0f}% '.format(percentage));
      NARS.print_info('<ERROR  > ' + chd_copy_key + '/' + chdFileName);
    else:
      NARS.print_error('Wrong value returned by update_ROM_file()');
      sys.exit(10);
    sys.stdout.flush()

    # --- Update progress
    step += 1;

  NARS.print_info('[Report]');
  NARS.print_info('Copied ROMs ' + '{:6d}'.format(num_copied_CHDs));
  NARS.print_info('Updated ROMs ' + '{:5d}'.format(num_updated_CHDs));

def clean_ROMs_destDir(destDir, rom_copy_dic):
  NARS.print_info('[Cleaning ROMs in ROMsDest]');

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

  NARS.print_info('Deleted ' + str(num_cleaned_roms) + ' redundant ROMs');

def delete_redundant_NFO(destDir):
  NARS.print_info('[Deleting redundant NFO files]');
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
  NARS.print_info('[Copying ArtWork]');
  fanartSourceDir = filter_config.fanartSourceDir;
  fanartDestDir = filter_config.fanartDestDir;
  thumbsSourceDir = filter_config.thumbsSourceDir;
  thumbsDestDir = filter_config.thumbsDestDir;
  
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
    sys.stdout.write('{:3.0f}% '.format(percentage));

    # --- Thumbs
    ret = copy_ArtWork_file(rom_baseName, art_baseName, thumbsSourceDir, thumbsDestDir);
    if ret == 0:
      num_copied_thumbs += 1;
      NARS.print_info('<Copied Thumb  > ' + art_baseName);
    elif ret == 1:
      num_missing_thumbs += 1;
      NARS.print_info('<Missing Thumb > ' + art_baseName);
    else:
      NARS.print_error('Wrong value returned by copy_ArtWork_file()')
      sys.exit(10)

    # --- Update progress
    percentage = 100 * step / num_steps;
    sys.stdout.write('{:3.0f}% '.format(percentage));

    # --- Fanart
    ret = copy_ArtWork_file(rom_baseName, art_baseName, fanartSourceDir, fanartDestDir);
    if ret == 0:
      num_copied_fanart += 1;
      NARS.print_info('<Copied Fanart > ' + art_baseName);
    elif ret == 1:
      num_missing_fanart += 1;
      NARS.print_info('<Missing Fanart> ' + art_baseName);
    else:
      NARS.print_error('Wrong value returned by copy_ArtWork_file()');
      sys.exit(10);

    # --- Update progress
    step += 1;

  NARS.print_info('[Report]');
  NARS.print_info('Copied thumbs ' + '{:6d}'.format(num_copied_thumbs));
  NARS.print_info('Missing thumbs ' + '{:5d}'.format(num_missing_thumbs));
  NARS.print_info('Copied fanart ' + '{:6d}'.format(num_copied_fanart));
  NARS.print_info('Missing fanart ' + '{:5d}'.format(num_missing_fanart));

def update_ArtWork_list(filter_config, rom_copy_dic):
  NARS.print_info('[Updating ArtWork]');
  
  thumbsSourceDir = filter_config.thumbsSourceDir;
  thumbsDestDir = filter_config.thumbsDestDir;
  fanartSourceDir = filter_config.fanartSourceDir;
  fanartDestDir = filter_config.fanartDestDir;

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
      sys.stdout.write('{:3.0f}% '.format(percentage));
      num_copied_thumbs += 1;
      NARS.print_info('<Copied  Thumb > ' + art_baseName);
    elif ret == 1:
      # Also report missing artwork
      sys.stdout.write('{:3.0f}% '.format(percentage));
      num_missing_thumbs += 1;
      NARS.print_info('<Missing Thumb > ' + art_baseName);
    elif ret == 2:
      if NARS.log_level >= NARS.Log.verb:
        sys.stdout.write('{:3.0f}% '.format(percentage));
      num_updated_thumbs += 1;
      NARS.print_verb('<Updated Thumb > ' + art_baseName);
    else:
      NARS.print_error('Wrong value returned by copy_ArtWork_file()');
      sys.exit(10)

    # --- Fanart
    ret = update_ArtWork_file(rom_baseName, art_baseName, fanartSourceDir, fanartDestDir);
    if ret == 0:
      # Also report missing artwork
      sys.stdout.write('{:3.0f}% '.format(percentage));
      num_copied_fanart += 1;
      NARS.print_info('<Copied  Fanart> ' + art_baseName);
    elif ret == 1:
      # Also report missing artwork
      sys.stdout.write('{:3d}% '.format(percentage));
      num_missing_fanart += 1;
      NARS.print_info('<Missing Fanart> ' + art_baseName);
    elif ret == 2:
      if NARS.log_level >= NARS.Log.verb:
        sys.stdout.write('{:3.0f}% '.format(percentage));
      num_updated_fanart += 1;
      NARS.print_verb('<Updated Fanart> ' + art_baseName);
    else:
      NARS.print_error('Wrong value returned by copy_ArtWork_file()');
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
  "Parses configuration file"
  NARS.print_info('[Parsing config file]');
  tree = NARS.XML_read_file_ElementTree(__config_configFileName, "Reading configuration XML file")
  root = tree.getroot();

  # --- Configuration object
  configFile = ConfigFile();
  configFile.MAME_XML = '';
  configFile.MAME_XML_redux = '';
  configFile.Catver = '';
  configFile.MergedInfo_XML = '';
  configFile.filter_dic = {};

  # --- Parse general options
  general_tag_found = 0;
  for root_child in root:
    if root_child.tag == 'General':
      general_tag_found = 1;
      for general_child in root_child:
        if general_child.tag == 'MAME_XML':
          configFile.MAME_XML = general_child.text;
        elif general_child.tag == 'MAME_XML_redux':
          configFile.MAME_XML_redux = general_child.text;
        elif general_child.tag == 'Catver':
          configFile.Catver = general_child.text;
        elif general_child.tag == 'Merged_XML':
          configFile.MergedInfo_XML = general_child.text;
        else:
          NARS.print_error('Unrecognised tag "' + general_child.tag + '" inside <General>');
          sys.exit(10);
  if not general_tag_found:
    NARS.print_error('Configuration error. <General> tag not found');
    sys.exit(10);

  # --- Parse filters
  for root_child in root:
    if root_child.tag == 'MAMEFilter':
      NARS.print_debug('<MAMEFilter>');
      if 'name' in root_child.attrib:
        filter_class = ConfigFileFilter();
        filter_class.name = root_child.attrib['name'];
        NARS.print_debug(' name = ' + filter_class.name);

        # By default things are None, which means user didn't
        # wrote them in config file.
        # NOTE if we have the tag but no text is written, then 
        #      filter_child.text will be None. Take this into account.
        filter_class.sourceDir = None;
        filter_class.destDir = None;
        filter_class.destDir_CHD = None;
        filter_class.fanartSourceDir = None;
        filter_class.fanartDestDir = None;
        filter_class.thumbsSourceDir = None;
        filter_class.thumbsDestDir = None;
        filter_class.mainFilter = None;
        filter_class.driver = None;
        filter_class.machineType = None;
        filter_class.categories = None;
        filter_class.controls = None;
        filter_class.buttons_exp = None;
        filter_class.players_exp = None;
        filter_class.year_exp = None;
        filter_class.year_YearExpansion = 0;
        sourceDirFound = 0;
        destDirFound = 0;
        for filter_child in root_child:
          if filter_child.tag == 'ROMsSource':
            NARS.print_debug(' ROMsSource = ' + filter_child.text);
            sourceDirFound = 1;
            # - Make sure all directory names end in slash
            tempDir = filter_child.text;
            if tempDir[-1] != '/': tempDir = tempDir + '/';
            filter_class.sourceDir = tempDir;

          elif filter_child.tag == 'ROMsDest':
            NARS.print_debug(' ROMsDest = ' + filter_child.text);
            destDirFound = 1;
            tempDir = filter_child.text;
            if tempDir[-1] != '/': tempDir = tempDir + '/';
            filter_class.destDir = tempDir;

          elif filter_child.tag == 'CHDsSource':
            NARS.print_debug(' CHDsSource = ' + filter_child.text);
            tempDir = filter_child.text;
            if tempDir[-1] != '/': tempDir = tempDir + '/';
            filter_class.destDir_CHD = tempDir;

          elif filter_child.tag == 'FanartSource':
            NARS.print_debug(' FanartSource = ' + filter_child.text);
            tempDir = filter_child.text;
            if tempDir[-1] != '/': tempDir = tempDir + '/';
            filter_class.fanartSourceDir = tempDir;

          elif filter_child.tag == 'FanartDest':
            NARS.print_debug(' FanartDest = ' + filter_child.text);
            tempDir = filter_child.text;
            if tempDir[-1] != '/': tempDir = tempDir + '/';
            filter_class.fanartDestDir = tempDir;

          elif filter_child.tag == 'ThumbsSource':
            NARS.print_debug(' ThumbsSource = ' + filter_child.text);
            tempDir = filter_child.text;
            if tempDir[-1] != '/': tempDir = tempDir + '/';
            filter_class.thumbsSourceDir = tempDir;

          elif filter_child.tag == 'ThumbsDest':
            NARS.print_debug(' ThumbsDest = ' + filter_child.text);
            tempDir = filter_child.text;
            if tempDir[-1] != '/': tempDir = tempDir + '/';
            filter_class.thumbsDestDir = tempDir;

          elif filter_child.tag == 'MainFilter':
            text_string = filter_child.text;
            if text_string != None:
              NARS.print_debug(' MainFilter = ' + text_string);
              filter_class.mainFilter = trim_list(text_string.split(","));
            else:
              filter_class.mainFilter = '';

          elif filter_child.tag == 'Driver':
            text_string = filter_child.text;
            if text_string != None:
              NARS.print_debug(' Driver = ' + text_string);
              filter_class.driver = text_string;
            else:
              filter_class.driver = '';

          elif filter_child.tag == 'Categories':
            text_string = filter_child.text;
            if text_string != None:
              NARS.print_debug(' Categories = ' + text_string);
              filter_class.categories = text_string;
            else:
              filter_class.categories = '';

          elif filter_child.tag == 'Controls':
            text_string = filter_child.text;
            if text_string != None:
              NARS.print_debug(' Controls = ' + text_string);
              filter_class.controls = text_string;
            else:
              filter_class.controls = '';

          elif filter_child.tag == 'Buttons':
            text_string = filter_child.text;
            if text_string != None:
              NARS.print_debug(' Buttons = ' + text_string);
              filter_class.buttons_exp = text_string;
            else:
              filter_class.buttons_exp = '';

          elif filter_child.tag == 'Players':
            text_string = filter_child.text;
            if text_string != None:
              NARS.print_debug(' Players = ' + text_string);
              filter_class.players_exp = text_string;
            else:
              filter_class.players_exp = '';

          elif filter_child.tag == 'Years':
            text_string = filter_child.text;
            if text_string != None:
              NARS.print_debug(' Years = ' + text_string);
              filter_class.year_exp = text_string;
            else:
              filter_class.year_exp = '';

          elif filter_child.tag == 'YearsOpts':
            text_string = filter_child.text;
            if text_string != None:
              NARS.print_debug(' YearsOpts = ' + text_string);
              yearOpts_list = trim_list(text_string.split(","));
              for option in yearOpts_list:
                # Only one option supported at the moment
                if option == 'YearExpansion':
                  filter_class.year_YearExpansion = 1;
                else:
                  NARS.print_error('Unknown option ' + option + 'inside <YearsOpts>');
                  sys.exit(10);

          else:
            NARS.print_error('Inside <MAMEFilter> unrecognised tag <' + filter_child.tag + '>');
            sys.exit(10);

        # - Check for errors in this filter
        if not sourceDirFound:
          NARS.print_error('ROMsSource directory not found in config file');
          sys.exit(10);
        if not destDirFound:
          NARS.print_error('ROMsDest directory not found in config file');
          sys.exit(10);

        # - Aggregate filter to configuration main variable
        configFile.filter_dic[filter_class.name] = filter_class;
      else:
        NARS.print_error('<MAMEFilter> tag does not have name attribute');
        sys.exit(10);
  
  return configFile;

def get_Filter_Config(filterName):
  "Returns the configuration filter object given the filter name"
  for key in configuration.filter_dic:
    if key == filterName:
      return configuration.filter_dic[key];
  
  NARS.print_error('get_Filter_Config >> filter ' + filterName + ' not found in configuration file');
  sys.exit(20)

# -----------------------------------------------------------------------------
# Misc functions
# -----------------------------------------------------------------------------
# A class to store the MAME parent/clone main list
#
class ROM:
  # Constructor.
  def __init__(self, name):
    self.name = name; 

def add_to_histogram(key, hist_dic):
  if key in hist_dic:
    hist_dic[key] += 1;
  else:
    hist_dic[key] = 1;

  return hist_dic;

def trim_driver_string(driver_str):
  # Check that string does not containg weird characters
  pattern = re.compile(r'\\/,')
  if pattern.findall(driver_str):
    print('Driver string contains weird characters ' + driver_str)
    sys.exit(10)

  # If driver name ends in .c, for example cps1.c, then trim .c
  if driver_str[-2:] == '.c':
    old_driver_str = driver_str;
    driver_str = old_driver_str[:len(old_driver_str)-2]

  return driver_str

def trim_list(input_list):
  for index, item in enumerate(input_list):
    input_list[index] = item.strip();

  return input_list;

# Wildcard expansion range
min_year = 1970;
max_year = 2012;
def trim_year_string(raw_year_text):
  year_text = raw_year_text;

  # --- Remove quotation marks at the end for some games
  if len(year_text) == 5 and year_text[4] == '?':
    # About array slicing, see this page. Does not work like C!
    # http://stackoverflow.com/questions/509211/pythons-slice-notation
    year_text = year_text[0:4];

  # --- Expand wildcards to numerical lists. Currently there are 6 cases
  # Basic expansion: 197?, 198?, 199?, 200?
  if year_text == '197?':
    year_list = [str(x) for x in range(1970, 1979)];
  elif year_text == '198?':
    year_list = [str(x) for x in range(1980, 1989)];
  elif year_text == '199?':
    year_list = [str(x) for x in range(1990, 1999)];
  elif year_text == '200?':
    year_list = [str(x) for x in range(2000, 2009)];
  # Full expansion: ????, 19??, 20??
  elif year_text == '19??':
    year_list = [str(x) for x in range(min_year, 1999)];
  elif year_text == '20??':
    year_list = [str(x) for x in range(2000, max_year)];
  elif year_text == '????':
    year_list = [str(x) for x in range(min_year, max_year)];
  # No expansion
  else:
    year_list = [];
    year_list.append(year_text);

  return year_list;

# Game year information:
#  Accepts a string as input
#  Returns:
#   1 standard game or game with not-verified year (example 1998?)
#   2 game that needs decade expansion (examples 198?, 199?) or
#     full expansion (examples 19??, ????)
def get_game_year_information(year_srt):
  # --- Remove quotation marks at the end for some games
  if len(year_srt) == 5 and year_srt[4] == '?':
    year_srt = year_srt[0:4];

  # --- Get game information
  game_info = 1;
  if year_srt == '197?' or year_srt == '198?' or \
     year_srt == '199?' or year_srt == '200?' or \
     year_srt == '19??' or year_srt == '20??' or \
     year_srt == '????':
    game_info = 2;
  elif not year_srt.isdigit():
    print_error('Unknown MAME year string "' + year_srt + '"');
    sys.exit(10);

  return game_info;

# See http://stackoverflow.com/questions/15929233/writing-a-tokenizer-in-python
# split words
def tokzr_WORD(txt): return re.findall(r'(?ms)\W*(\w+)', txt)

def fix_category_name(main_category, category):
  # Rename some categories
  final_category = main_category;
  if category == 'System / BIOS':
    final_category = 'BIOS';
  elif main_category == 'Electromechanical - PinMAME':
    final_category = 'PinMAME';
  elif main_category == 'Ball & Paddle':
    final_category = 'Ball_and_Paddle';
  elif main_category == 'Misc.':
    final_category = 'Misc';
  elif main_category == 'Mini-Games':
    final_category = 'Mini_Games';
  elif main_category == 'Fruit Machines':
    final_category = 'Fruit_Machines';
  elif main_category == 'Not Classified':
    final_category = 'Not_Classified';

  # New categories from AntoPISA extended catver.ini (after MAME/MESS merge)
  # If there are several words, all of them starting with upper case and
  # separated by spaces, substitute the spaces by underscores to join them
  # Ex: 'Aaa Bbb Ccc' -> 'Aaa_Bbb_Ccc'
  # Lots of MESS categories in AntoPISA extended catver.ini are like that.
  tokens = tokzr_WORD(main_category)
#  print(repr(tokens) + ' ' + str(len(tokens)))
  if len(tokens) > 1:
    s = '_'
#    print(s.join(tokens))
    final_category = s.join(tokens)

  # If there is *Mature* in any category or subcategory, then
  # the game belongs to the Mature category
  if category.find('*Mature*') >= 0 or category.find('* Mature *') >= 0:
    final_category = 'Mature';

  # Regular expression to catch ilegal characters in categories
  # that may make the categories filter parser to fail.
  result = re.search('[^\w_]+', final_category);
  if result is not None:
    NARS.print_error('Ilegal character found in category "' + final_category + '"');
    sys.exit(10);

  return final_category

def parse_catver_ini():
  "Parses Catver.ini and returns a ..."

  # --- Parse Catver.ini
  # --- Create a histogram with the categories
  NARS.print_info('[Parsing Catver.ini]');
  cat_filename = configuration.Catver;
  NARS.print_verb(' Opening ' + cat_filename);
  final_categories_dic = {};
  f = open(cat_filename, 'r');
  # 0 -> Looking for '[Category]' tag
  # 1 -> Reading categories
  # 2 -> Categories finished. STOP
  read_status = 0;
  for cat_line in f:
    stripped_line = cat_line.strip();
    if read_status == 0:
      if stripped_line == '[Category]':
        read_status = 1;
    elif read_status == 1:
      line_list = stripped_line.split("=");
      if len(line_list) == 1:
        read_status = 2;
        continue;
      else:
        game_name = line_list[0];
        category = line_list[1];
        # --- Sub-categories  
        sub_categories = category.split("/");
        main_category = sub_categories[0].strip();
        second_category = sub_categories[0].strip();

        # NOTE: Only use the main category for filtering.
        final_category = fix_category_name(main_category, category);

        # - Create final categories dictionary
        final_categories_dic[game_name] = final_category;
    elif read_status == 2:
      break;
    else:
      print_error('Unknown read_status FSM value');
      sys.exit(10);
  f.close();

  return final_categories_dic;

# Used in the filtering functions (do_checkFilter, do_update(), do_checkArtwork(),
# do_update_artwork()), but not in the do_list_*() functions.
#
# Returns a dictionary with key the (unique) ROM name and value a ROM object with
# all the ROM information from the XML.
def parse_MAME_merged_XML():
  "Parses a MAME merged XML and creates a parent/clone list"

  filename = configuration.MergedInfo_XML;
  NARS.print_info('[Parsing MAME merged XML]');
  tree = NARS.XML_read_file_cElementTree(filename, "Parsing merged XML file")

  # --- Raw list: literal information from the XML
  rom_raw_dict = {};
  root = tree.getroot();
  num_games = 0;
  num_parents = 0;
  num_clones = 0;
  for game_EL in root:
    if game_EL.tag == 'machine':
      num_games += 1;

      # --- Game attributes
      game_attrib = game_EL.attrib;
      romName = game_attrib['name'];
      romObject = ROM(romName);
      NARS.print_debug('machine = ' + romName);

      # --- Check game attributes and create variables for filtering
      # Parent or clone
      if 'cloneof' in game_attrib:
        num_clones += 1;
        romObject.cloneof = game_attrib['cloneof'];
        romObject.isclone = 1;
        NARS.print_debug(' Clone of = ' + game_attrib['cloneof']);
      else:
        num_parents += 1;
        romObject.isclone = 0;

      # --- Device and Runnable
      if 'isdevice' in game_attrib:
        if game_attrib['isdevice'] == 'yes':
          romObject.isdevice = 1;
        else:
          romObject.isdevice = 0;
      else:
        romObject.isdevice = 0; # Device defaults to 0

      if 'runnable' in game_attrib:
        if game_attrib['runnable'] == 'no':
          romObject.runnable = 0;
        else:
          romObject.runnable = 1;
      else:
        romObject.runnable = 1; # Runnable defaults to 1

      # Are all devices non runnable?
      # In MAME 0.153b, when there is the attribute 'isdevice' there is also
      # 'runnable'. Also, if isdevice = yes => runnable = no
      if romObject.isdevice == 1 and romObject.runnable == 1:
        NARS.print_error('Found a ROM which is device and runnable');
        sys.exit(10);
      if 'isdevice' in game_attrib and 'runnable' not in game_attrib:
        NARS.print_error('isdevice but NOT runnable');
        sys.exit(10);
      if 'isdevice' not in game_attrib and 'runnable' in game_attrib:
        NARS.print_error('NOT isdevice but runnable');
        sys.exit(10);

      # Samples
      if 'sampleof' in game_attrib:
        romObject.hasSamples = 1;
        romObject.sampleof = game_attrib['sampleof'];
      else:
        romObject.hasSamples = 0; # By default has no samples
        romObject.sampleof = '';

      # Mechanical
      if 'ismechanical' in game_attrib:
        if game_attrib['ismechanical'] == 'yes':
          romObject.isMechanical = 1;
        else:
          romObject.isMechanical = 0;
      else:
        romObject.isMechanical = 0; # isMechanical defaults to 0

      # BIOS
      if 'isbios' in game_attrib:
        if game_attrib['isbios'] == 'yes':
          romObject.isBIOS = 1;
        else:
          romObject.isBIOS = 0;
      else:
        romObject.isBIOS = 0;

      # Game driver
      if 'sourcefile' in game_attrib:
        # Remove the trail '.c' from driver name
        driverName = game_attrib['sourcefile'];
        driverName = driverName[:-2];
        romObject.sourcefile = driverName;
      else:
        # sourcefile (driver) defaults to unknown
        romObject.sourcefile = 'unknown';

      # --- Parse child tags
      romObject.device_depends = [];
      romObject.BIOS_depends = [];
      for child_game in game_EL:
        # - Driver status
        if child_game.tag == 'driver':
          driver_attrib = child_game.attrib;

          # Driver status is good, imperfect, preliminary
          # preliminary games don't work or have major emulation problems
          # imperfect games are emulated with some minor issues
          # good games are perfectly emulated
          if 'status' in driver_attrib:
            romObject.driver_status = driver_attrib['status'];
            NARS.print_debug(' Driver status = ' + driver_attrib['status']);
          else:
            romObject.driver_status = 'unknown';

        # - Category
        elif child_game.tag == 'category':
          romObject.category = child_game.text;

        # - Dependencies
        elif child_game.tag == 'device_depends':
          romObject.device_depends = child_game.text.split(",");
        elif child_game.tag == 'bios_depends':
          romObject.BIOS_depends = child_game.text.split(",");
        elif child_game.tag == 'chd_depends':
          romObject.CHD_depends = child_game.text.split(",");

        # - Controls
        elif child_game.tag == 'input':
          control_attrib = child_game.attrib;
          if 'buttons' in control_attrib:
            romObject.buttons = control_attrib['buttons'];
          else:
            # There are some games with no buttons attribute
            romObject.buttons = '0';

          if 'players' in control_attrib:
            romObject.players = control_attrib['players'];
          else:
            romObject.players = None;

          # - Traverse input node for control child nodes
          # NOTE: a game may have more than one control (joystick, dial, ...)
          romObject.control_type = [];
          for control in child_game:
            if control.tag == 'control':
              if 'type' in control.attrib:
                romObject.control_type.append(control.attrib['type'].title());

          if len(romObject.control_type) < 1:
            romObject.control_type.append('ButtonsOnly');

        # - Copy information to generate NFO files
        elif child_game.tag == 'description':
          romObject.description = child_game.text;
        elif child_game.tag == 'year':
          romObject.year = child_game.text;
        elif child_game.tag == 'manufacturer':
          romObject.manufacturer = child_game.text;

      # Add new game to the list
      rom_raw_dict[romName] = romObject;

  del tree;
  NARS.print_info('Total number of games = ' + str(num_games));
  NARS.print_info('Number of parents = ' + str(num_parents));
  NARS.print_info('Number of clones = ' + str(num_clones));

  # --- Create a parent-clone list
  # NOTE: a parent/clone hierarchy is not needed for MAME. In the ROM list
  # include a field isClone, so clones can be filtered out or not.
  # However, for NoIntro 1G1R, the parent/clone hierarchy is needed to filter
  # the sourceDir rom list.

  return rom_raw_dict;

# Filtering function
#
def apply_MAME_filters(mame_xml_dic, filter_config):
  "Apply filters to main parent/clone dictionary"
  NARS.print_info('[Applying MAME filters]');
  NARS.print_info('NOTE: -vv if you want to see filters in action');

  # --- Default filters: remove crap
  NARS.print_info('<Main filter>');
  mainF_str_offset = 32;
  # What is "crap"?
  # a) devices <game isdevice="yes" runnable="no"> 
  #    Question: isdevice = yes implies runnable = no? In MAME 0.153b XML yes!
  mame_filtered_dic = {};
  filtered_out_games = 0;
  for key in mame_xml_dic:
    romObject = mame_xml_dic[key];
    if romObject.isdevice:
      filtered_out_games += 1;
      NARS.print_vverb('FILTERED ' + key);
      continue;
    mame_filtered_dic[key] = mame_xml_dic[key];
    NARS.print_debug('Included ' + key);
  NARS.print_info('Default filter, removing devices'.ljust(mainF_str_offset) + \
                  ' - Removed = ' + '{:5d}'.format(filtered_out_games) + \
                  ' / Remaining = ' + '{:5d}'.format(len(mame_filtered_dic)));

  # --- Apply MainFilter: NoClones
  # This is a special filter, and MUST be done first.
  # Also, remove crap like chips, etc.
  if 'NoClones' in filter_config.mainFilter:
    mame_filtered_dic_temp = {};
    filtered_out_games = 0;
    for key in mame_filtered_dic:
      romObject = mame_filtered_dic[key];
      if not romObject.isclone:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
        NARS.print_debug('Included ' + key);
      else:
        filtered_out_games += 1;
        NARS.print_vverb('FILTERED ' + key);
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    NARS.print_info('Filtering out clones'.ljust(mainF_str_offset) + \
                    ' - Removed = ' + '{:5d}'.format(filtered_out_games) + \
                    ' / Remaining = ' + '{:5d}'.format(len(mame_filtered_dic)));
  else:
    NARS.print_info('User wants clone ROMs');

  # --- Apply MainFilter: NoSamples
  if 'NoSamples' in filter_config.mainFilter:
    mame_filtered_dic_temp = {};
    filtered_out_games = 0;
    for key in mame_filtered_dic:
      romObject = mame_filtered_dic[key];
      if romObject.hasSamples:
        filtered_out_games += 1;
        NARS.print_vverb('FILTERED ' + key);
      else:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
        NARS.print_debug('Included ' + key);
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    NARS.print_info('Filtering out samples'.ljust(mainF_str_offset) + \
                    ' - Removed = ' + '{:5d}'.format(filtered_out_games) + \
                    ' / Remaining = ' + '{:5d}'.format(len(mame_filtered_dic)));
  else:
    NARS.print_info('User wants games with samples');

  # --- Apply MainFilter: NoMechanical
  if 'NoMechanical' in filter_config.mainFilter:
    mame_filtered_dic_temp = {};
    filtered_out_games = 0;
    for key in mame_filtered_dic:
      romObject = mame_filtered_dic[key];
      if romObject.isMechanical:
        filtered_out_games += 1;
        NARS.print_vverb('FILTERED ' + key);
      else:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
        NARS.print_debug('Included ' + key);
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    NARS.print_info('Filtering out mechanical games'.ljust(mainF_str_offset) + \
                    ' - Removed = ' + '{:5d}'.format(filtered_out_games) + \
                    ' / Remaining = ' + '{:5d}'.format(len(mame_filtered_dic)));
  else:
    NARS.print_info('User wants mechanical games');

  # --- Apply MainFilter: NoBIOS
  if 'NoBIOS' in filter_config.mainFilter:
    mame_filtered_dic_temp = {};
    filtered_out_games = 0;
    for key in mame_filtered_dic:
      romObject = mame_filtered_dic[key];
      if romObject.isBIOS:
        filtered_out_games += 1;
        NARS.print_vverb('FILTERED ' + key);
      else:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
        NARS.print_debug('Included ' + key);
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    NARS.print_info('Filtering out BIOS'.ljust(mainF_str_offset) + \
                    ' - Removed = ' + '{:5d}'.format(filtered_out_games) + \
                    ' / Remaining = ' + '{:5d}'.format(len(mame_filtered_dic)));
  else:
    NARS.print_info('User wants BIOS ROMs');

  # --- Apply MainFilter: NoNonworking
  # http://www.mamedev.org/source/src/emu/info.c.html
  # <driver color="good" emulation="good" graphic="good" 
  #         savestate="supported" sound="good" status="good"/> 
  #
  # /* The status entry is an hint for frontend authors */
  # /* to select working and not working games without */
  # /* the need to know all the other status entries. */
  # /* Games marked as status=good are perfectly emulated, games */
  # /* marked as status=imperfect are emulated with only */
  # /* some minor issues, games marked as status=preliminary */
  # /* don't work or have major emulation problems. */
  if 'NoNonworking' in filter_config.mainFilter:
    mame_filtered_dic_temp = {};
    filtered_out_games = 0;
    for key in mame_filtered_dic:
      romObject = mame_filtered_dic[key];
      if romObject.driver_status == 'preliminary':
        filtered_out_games += 1;
        NARS.print_vverb('FILTERED ' + key);
      else:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
        NARS.print_debug('Included ' + key);
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    NARS.print_info('Filtering out Non-Working games'.ljust(mainF_str_offset) + \
                    ' - Removed = ' + '{:5d}'.format(filtered_out_games) + \
                    ' / Remaining = ' + '{:5d}'.format(len(mame_filtered_dic)));
  else:
    NARS.print_info('User wants Non-Working games');

  # --- Apply Driver filter
  NARS.print_info('<Driver filter>');
  __debug_apply_MAME_filters_Driver_tag = 0;
  if filter_config.driver is not None and filter_config.driver is not '':
    driver_filter_expression = filter_config.driver;
    filtered_out_games = 0;
    mame_filtered_dic_temp = {};
    NARS.print_info('Filter = "' + driver_filter_expression + '"');
    for key in sorted(mame_filtered_dic):
      romObject = mame_filtered_dic[key];
      driver_name_list = []
      driver_str = trim_driver_string(romObject.sourcefile)
      driver_name_list.append(driver_str)
      # --- Update search variable and call parser to evaluate expression
      NARS.set_parser_search_list(driver_name_list)
      boolean_result = NARS.parse_exec(driver_filter_expression);
      # --- Filter ROM or not
      if not boolean_result:
        filtered_out_games += 1;
        NARS.print_vverb('FILTERED ' + key.ljust(8) + ' driver ' + ', '.join(driver_name_list));
      else:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
        NARS.print_debug('Included ' + key.ljust(8) + ' driver ' + ', '.join(driver_name_list));
      # --- DEBUG info
      if __debug_apply_MAME_filters_Driver_tag:
        print('[DEBUG] ----- Game = ' + key + ' -----')
        print('[DEBUG] Driver name list = ', sorted(driver_name_list))
        print('[DEBUG] Filter = "' + driver_filter_expression + '"')
        print('[DEBUG] boolean_result = ' + str(boolean_result))
    # --- Update game list
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    NARS.print_info('Removed = ' + '{:5d}'.format(filtered_out_games) + \
                    ' / Remaining = ' + '{:5d}'.format(len(mame_filtered_dic)));
  else:
    NARS.print_info('User wants all drivers');

  # --- Apply Categories filter
  NARS.print_info('<Categories filter>');
  __debug_apply_MAME_filters_Category_tag = 0;
  if hasattr(filter_config, 'categories') and \
             filter_config.categories is not None and \
             filter_config.categories is not '':
    categories_filter_expression = filter_config.categories;
    mame_filtered_dic_temp = {};
    filtered_out_games = 0;
    NARS.print_info('Filter = "' + categories_filter_expression + '"');
    for key in sorted(mame_filtered_dic):
      romObject = mame_filtered_dic[key];
      categories_type_list = [];
      categories_type_list.append(romObject.category);
      # --- Update search variable and call parser to evaluate expression
      NARS.set_parser_search_list(categories_type_list)
      boolean_result = NARS.parse_exec(categories_filter_expression);
      # --- Filter ROM or not
      if not boolean_result:
        filtered_out_games += 1;
        NARS.print_vverb('FILTERED ' + key.ljust(8) + ' category ' + ', '.join(categories_type_list));
      else:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
        NARS.print_debug('Included ' + key.ljust(8) + ' category ' + ', '.join(categories_type_list));
      # --- DEBUG info
      if __debug_apply_MAME_filters_Category_tag:
        print('[DEBUG] Category list = ', sorted(categories_type_list))
        print('[DEBUG] Filter = "' + categories_filter_expression + '"')
        print('[DEBUG] boolean_result = ' + str(boolean_result))
    # --- Update game list
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    NARS.print_info('Removed = ' + '{:5d}'.format(filtered_out_games) + \
                    ' / Remaining = ' + '{:5d}'.format(len(mame_filtered_dic)));
  else:
    NARS.print_info('User wants all categories');

  # --- Apply Controls filter
  NARS.print_info('<Controls filter>');
  __debug_apply_MAME_filters_Controls_tag = 0;
  if hasattr(filter_config, 'controls') and \
             filter_config.controls is not None and \
             filter_config.controls is not '':
    controls_type_filter_expression = filter_config.controls;
    filtered_out_games = 0;
    mame_filtered_dic_temp = {};
    NARS.print_info('Filter = "' + controls_type_filter_expression + '"');
    for key in sorted(mame_filtered_dic):
      # --- Some games may have two controls, so controls_type_list is a list
      romObject = mame_filtered_dic[key];
      controls_type_list = romObject.control_type;
      # --- Update search variable and call parser to evaluate expression
      NARS.set_parser_search_list(controls_type_list)
      boolean_result = NARS.parse_exec(controls_type_filter_expression);
      # --- Filter ROM or not
      if not boolean_result:
        filtered_out_games += 1;
        NARS.print_vverb('FILTERED ' + key.ljust(8) + ' controls ' + ', '.join(controls_type_list));
      else:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
        NARS.print_debug('Included ' + key.ljust(8) + ' controls ' + ', '.join(controls_type_list));
      # --- DEBUG info
      if __debug_apply_MAME_filters_Controls_tag:
        print('[DEBUG] ----- Game = ' + key + ' -----')
        print('[DEBUG] Control list = ', sorted(controls_type_list))
        print('[DEBUG] Filter = "' + controls_type_filter_expression + '"')
        print('[DEBUG] boolean_result = ' + str(boolean_result))
    # --- Update game list
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    NARS.print_info('Removed = ' + '{:5d}'.format(filtered_out_games) + \
                    ' / Remaining = ' + '{:5d}'.format(len(mame_filtered_dic)));
  else:
    NARS.print_info('User wants all controls');

  # --- Apply Buttons filter
  NARS.print_info('<Buttons filter>');
  __debug_apply_MAME_filters_Buttons_tag = 0;
  if hasattr(filter_config, 'buttons_exp') and \
             filter_config.buttons_exp is not None and \
             filter_config.buttons_exp is not '':
    button_filter_expression = filter_config.buttons_exp;
    mame_filtered_dic_temp = {};
    filtered_out_games = 0;
    NARS.print_info('Filter = "' + button_filter_expression + '"');
    for key in mame_filtered_dic:
      romObject = mame_filtered_dic[key];
      buttons_str = romObject.buttons;
      buttons = int(buttons_str);
      if __debug_apply_MAME_filters_Buttons_tag:
        print('[DEBUG] Buttons number = ' + buttons_str)
        print('[DEBUG] Buttons filter = "' + button_filter_expression + '"')
      boolean_result = eval(button_filter_expression, globals(), locals());

      # If not all items are true, the game is NOT copied (filtered)
      if not boolean_result:
        filtered_out_games += 1;
        NARS.print_vverb('FILTERED ' + key + ' buttons ' + buttons_str);
      else:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
        NARS.print_debug('Included ' + key + ' buttons ' + buttons_str);
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    NARS.print_info('Removed = ' + '{:5d}'.format(filtered_out_games) + \
                    ' / Remaining = ' + '{:5d}'.format(len(mame_filtered_dic)));
  else:
    NARS.print_info('User wants all buttons');

  # --- Apply Players filter
  NARS.print_info('<Players filter>');
  __debug_apply_MAME_filters_Players_tag = 0;
  if hasattr(filter_config, 'players_exp') and \
             filter_config.players_exp is not None and \
             filter_config.players_exp is not '':
    players_filter_expression = filter_config.players_exp;
    mame_filtered_dic_temp = {};
    filtered_out_games = 0;
    NARS.print_info('Filter = "' + players_filter_expression + '"');
    for key in mame_filtered_dic:
      romObject = mame_filtered_dic[key];
      players_str = romObject.players;
      players = int(players_str);
      if __debug_apply_MAME_filters_Players_tag:
        print('[DEBUG] Players number = ' + players_str)
        print('[DEBUG] Players filter = "' + players_filter_expression + '"')
      boolean_result = eval(players_filter_expression, globals(), locals());

      # If not all items are true, the game is NOT copied (filtered)
      if not boolean_result:
        filtered_out_games += 1;
        NARS.print_vverb('FILTERED ' + key + ' players ' + players_str);
      else:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
        NARS.print_debug('Included ' + key + ' players ' + players_str);
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    NARS.print_info('Removed = ' + '{:5d}'.format(filtered_out_games) + \
                    ' / Remaining = ' + '{:5d}'.format(len(mame_filtered_dic)));
  else:
    NARS.print_info('User wants all players');

  # --- Apply Years filter
  NARS.print_info('<Year filter>');
  __debug_apply_MAME_filters_years_tag = 0;
  if hasattr(filter_config, 'year_exp') and \
             filter_config.year_exp is not None and \
             filter_config.year_exp is not '':
    mame_filtered_dic_temp = {};
    filtered_out_games = 0;
    year_filter_expression = filter_config.year_exp;
    year_YearExpansion = filter_config.year_YearExpansion;
    NARS.print_info('Filter = "' + year_filter_expression + '"');
    if year_YearExpansion:
      NARS.print_info('Year expansion activated')
    else:
      NARS.print_info('Year expansion deactivated')
    for key in sorted(mame_filtered_dic):
      romObject = mame_filtered_dic[key];
      # year is a string, convert to int
      year_srt = romObject.year;

      # Game year information:
      #  1 standard game or game with not-verified year (example 1998?)
      #  2 game that needs decade expansion (examples 198?, 199?) or
      #    full expansion (examples 19??, ????)
      game_info = get_game_year_information(year_srt);

      # Game is standard: do filtering
      if game_info == 1:
        # Convert number string to int (supports games like 1997?)
        year_list = trim_year_string(year_srt);
        if len(year_list) != 1:
          NARS.print_error('Logical error filtering year (standard year)');
          sys.exit(10);
        year = int(year_list[0]);
        if __debug_apply_MAME_filters_years_tag:
          print('[DEBUG] Game ' + key.ljust(8) + ' / Year value = ' + str(year) + \
                ' / Filter = "' + year_filter_expression + '"')
        boolean_result = eval(year_filter_expression, globals(), locals());
        # If not all items are true, the game is NOT copied (filtered)
        if not boolean_result:
          filtered_out_games += 1;
          NARS.print_vverb('FILTERED ' + key.ljust(8) + ' year ' + str(year));
        else:
          mame_filtered_dic_temp[key] = mame_filtered_dic[key];
          NARS.print_debug('Included ' + key.ljust(8) + ' year ' + str(year));

      # Game needs expansion. If user activated this option expand wildcars and
      # then do filtering. If option not activated, discard game
      elif game_info == 2:
        if year_YearExpansion:
          year_list = trim_year_string(year_srt);
          if len(year_list) < 2:
            print_error('Logical error filtering year (expanded year)');
            sys.exit(10);
          boolean_list = [];
          for year_str in year_list:
            year = int(year_str);
            if __debug_apply_MAME_filters_years_tag:
              print('[DEBUG] Game ' + key.ljust(8) + ' / Year value = ' + str(year) + \
                    ' / Filter = "' + year_filter_expression + '"')
            boolean_result = eval(year_filter_expression, globals(), locals())
            boolean_list.append(boolean_result);
          # Knowing the boolean results for the wildcard expansion, check if game
          # should be included or not.
          if any(boolean_list):
            mame_filtered_dic_temp[key] = mame_filtered_dic[key];
            print_debug('Included ' + key.ljust(8) + ' year ' + str(year));
          else:
            filtered_out_games += 1;
            NARS.print_vverb('FILTERED ' + key.ljust(8) + ' year ' + str(year));
        else:
          filtered_out_games += 1;
          NARS.print_vverb('FILTERED ' + key.ljust(8) + ' year ' + str(year));
      else:
        NARS.print_error('Wrong result returned by get_game_year_information() = ' + str(game_info));
        sys.exit(10);
    # --- Update list of filtered games
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    NARS.print_info('Removed = ' + '{:5d}'.format(filtered_out_games) + \
               ' / Remaining = ' + '{:5d}'.format(len(mame_filtered_dic)));
  else:
    NARS.print_info('User wants all years');

  # --- ROM dependencies
  # Add ROMs (devices and BIOS) needed for other ROM to work.
  # Traverse the list of filtered games, and check if they have dependencies. If
  # so, add the dependencies to the filtered list.
  NARS.print_info('[Adding ROM dependencies]');
  # NOTE: dictionaries cannot change size during iteration. Create auxiliary list.
  dependencies_ROM_list = {};
  for key in sorted(mame_filtered_dic):
    romObject = mame_filtered_dic[key];
    # - BIOS dependencies
    if len(romObject.BIOS_depends):
      for BIOS_depend in romObject.BIOS_depends:
        if BIOS_depend not in mame_xml_dic:
          NARS.print_error('[ERROR] ROM name not found in mame_xml_dic');
          sys.exit(10);
        # Get ROM object from main, unfiltered dictionary
        BIOS_romObj = mame_xml_dic[BIOS_depend];
        # Only add dependency if not already in filtered list
        if BIOS_depend not in dependencies_ROM_list:
          dependencies_ROM_list[BIOS_depend] = BIOS_romObj;
          NARS.print_info('Game ' + key.ljust(8) + ' depends on BIOS   ' + \
                          BIOS_depend.ljust(11) + ' - Adding  to list');
        else:
          NARS.print_verb('Game ' + key.ljust(8) + ' depends on BIOS   ' + \
                           BIOS_depend.ljust(11) + ' - Already on list');

    # - Device dependencies
    if len(romObject.device_depends):
      for device_depend in romObject.device_depends:
        if device_depend not in mame_xml_dic:
          NARS.print_error('[ERROR] ROM name not found in mame_xml_dic');
          sys.exit(10);
        # Get ROM object from main, unfiltered dictionary
        device_romObj = mame_xml_dic[device_depend];
        # Only add dependency if not already in filtered list
        if device_depend not in dependencies_ROM_list:
          dependencies_ROM_list[device_depend] = device_romObj;
          NARS.print_info('Game ' + key.ljust(8) + ' depends on device ' + \
                          device_depend.ljust(11) + ' - Adding  to list');
        else:
          NARS.print_verb('Game ' + key.ljust(8) + ' depends on device ' + \
                          device_depend.ljust(11) + ' - Already on list');

  for key in dependencies_ROM_list:
    romObject = dependencies_ROM_list[key];
    mame_filtered_dic[key] = romObject;

  return mame_filtered_dic;

# rom_copy_dic = create_copy_list(mame_filtered_dic, rom_main_list);
def create_copy_list(mame_filtered_dic, rom_main_list):
  "With list of filtered ROMs and list of source ROMs, create list of files to be copied"

  NARS.print_info('[Creating list of ROMs to be copied/updated]');
  copy_list = [];
  num_added_roms = 0;
  if len(rom_main_list) == 0:
    print_info('WARNING: Not found ANY ROM in sourceDir');
    print_info('Check your configuration file');
  else:
    for key_rom_name in mame_filtered_dic:
      # If the ROM is in the mame filtered list, then add to the copy list
      if key_rom_name in rom_main_list:
        copy_list.append(key_rom_name);
        num_added_roms += 1;
        NARS.print_verb('Added ROM ' + key_rom_name);
      else:
        NARS.print_info('Missing ROM ' + key_rom_name);
  NARS.print_info('Added ' + str(num_added_roms) + ' ROMs');

  return copy_list;

def create_copy_CHD_dic(mame_filtered_dic):
  "With list of filtered ROMs and, create list of CHDs to be copied"

  NARS.print_info('[Creating list of CHDs to be copied/updated]');
  CHD_dic = {};
  num_added_CHDs = 0;
  for key in sorted(mame_filtered_dic):
    romObject = mame_filtered_dic[key];
    # - CHD dependencies
    if hasattr(romObject, 'CHD_depends') and (romObject.CHD_depends):
      for CHD_depend in romObject.CHD_depends:
        # CHD names may be different from ROM names
        CHD_dic[key] = CHD_depend;
        num_added_CHDs += 1;
        NARS.print_info('Game ' + key.ljust(8) + ' depends on CHD    ' + \
                        CHD_depend.ljust(11) + ' - Adding  to list');
  NARS.print_info('Added ' + str(num_added_CHDs) + ' CHDs');

  return CHD_dic;

def get_ROM_main_list(sourceDir):
  "Reads sourceDir and creates a dictionary of ROMs"
  __debug_get_ROM_main_list = 0;

  # --- Parse sourceDir ROM list and create main ROM list
  NARS.print_info('[Reading ROMs in source directory]');
  romMainList_dict = {};
  for file in os.listdir(sourceDir):
    if file.endswith(".zip"):
      thisFileName, thisFileExtension = os.path.splitext(file);
      romFileName_temp = thisFileName + '.zip';
      romObject = ROM(thisFileName);
      romObject.filename = file;
      romMainList_dict[thisFileName] = romObject;
      if __debug_get_ROM_main_list:
        print(romObject.name)
        print(romObject.filename)

  return romMainList_dict;

def generate_NFO_files(rom_copy_dic, mame_filtered_dic, destDir):
  "Generates game information files (NFO) in destDir"

  print_info('[Generating NFO files]');
  num_NFO_files = 0;
  for rom_name in sorted(rom_copy_dic):
    romObj = mame_filtered_dic[rom_name];
    # DEBUG: dump romObj
    # print dir(romObj)
    NFO_filename = rom_name + '.nfo';
    NFO_full_filename =  destDir + NFO_filename;

    # --- XML structure
    tree_output = ET.ElementTree();
    root_output = a = ET.Element('game');
    tree_output._setroot(root_output);

    # <title>1944 - The Loop Master</title>
    sub_element = ET.SubElement(root_output, 'title');
    sub_element.text = romObj.description;

    # <platform>MAME</platform>
    sub_element = ET.SubElement(root_output, 'platform');
    sub_element.text = 'MAME';

    # <year>2000</year>
    # NOTE: some devices which are included as dependencies do not have
    # some fields. Write defaults.
    sub_element = ET.SubElement(root_output, 'year');
    if hasattr(romObj, 'year'):
      sub_element.text = romObj.year;
    else:
      print('ROM has no year tag ' + rom_name)
      sub_element.text = '????';

    # <publisher></publisher>
    sub_element = ET.SubElement(root_output, 'publisher');
    if hasattr(romObj, 'manufacturer'):
      sub_element.text = romObj.manufacturer;
    else:
      print('ROM has no publisher tag ' + rom_name)
      sub_element.text = 'Unknown';

    # <genre>Shooter / Flying Vertical</genre>
    sub_element = ET.SubElement(root_output, 'genre');
    if hasattr(romObj, 'category'):
      sub_element.text = romObj.category;
    else:
      print('ROM has no genre tag ' + rom_name)
      sub_element.text = 'Unknown';

    # <plot></plot>
    # Probably need to merge information from history.dat or mameinfo.dat
    # Now, just add some technical information about the game.
    plot_str = 'Name = ' + romObj.name + \
               ' / Driver = ' + romObj.sourcefile;
    if hasattr(romObj, 'buttons'):
      plot_str += ' / Buttons = ' + romObj.buttons;
    if hasattr(romObj, 'players'):
      plot_str += ' / Players = ' + romObj.players;
    if hasattr(romObj, 'control_type'):
      plot_str += ' / Controls = ' + str(romObj.control_type);
    sub_element = ET.SubElement(root_output, 'plot');
    sub_element.text = plot_str;

    # --- Write output file (don't use miniDOM, is sloow)
    # See http://norwied.wordpress.com/2013/08/27/307/
    print_verb('Writing ' + NFO_full_filename);
    indent_ElementTree_XML(root_output);
    tree_output.write(NFO_full_filename, xml_declaration=True, encoding='utf-8', method="xml")
    num_NFO_files += 1;

  print_info('[Report]');
  print_info('Generated ' + str(num_NFO_files) + ' NFO files');

# -----------------------------------------------------------------------------
# Main body functions
# -----------------------------------------------------------------------------
# IMPLEMENT ME SAX API can make the loading of XML much faster and MUCH LESS
#              memory consuming.
#
# Dependency implementation: there are 3 types of dependencies: 
# a) game that depends on a device and the device has a ROM.
# b) game depends on a BIOS.
# c) game depends on a CHD
#
# Example of a device with a ROM ----------------------------------------------
#  <game name="qsound" sourcefile="src/emu/sound/qsound.c" isdevice="yes" runnable="no">
#    <description>Q-Sound</description>
#    <rom name="qsound.bin" size="8192" crc="" sha1="" status="baddump" region="qsound" offset="0"/>
#    <chip type="cpu" tag=":qsound" name="DSP16" clock="4000000"/>
#    <sound channels="0"/>
#  </game>
#
# Example of a game that uses a device (with a ROM):
#  <game name="dino" sourcefile="cps1.c">
#    <description>Cadillacs and Dinosaurs (World 930201)</description>
#    <year>1993</year>
#    <manufacturer>Capcom</manufacturer>
#    ...
#    <device_ref name="qsound"/>
#    <device_ref name="dsp16"/>
#    ...
#    <driver status="good" emulation="good" color="good" sound="good" graphic="good" savestate="supported"/>
#  </game>
#
# Example of a game that uses a BIOS:
#  <game name="mslug" sourcefile="neogeo.c" romof="neogeo">
#    <description>Metal Slug - Super Vehicle-001</description>
#    <year>1996</year>
#    <manufacturer>Nazca</manufacturer>
#    <biosset name="euro" description="Europe MVS (Ver. 2)" default="yes"/>
#    <biosset name="euro-s1" description="Europe MVS (Ver. 1)"/>
#    ...
#    <rom name="sp-s2.sp1" merge="sp-s2.sp1" bios="euro" size="131072" crc="" sha1="" region="mainbios" offset="0"/>
#    <rom name="sp-s.sp1" merge="sp-s.sp1" bios="euro-s1" size="131072" crc="" sha1="" region="mainbios" offset="0"/>
#    ...
#  </game>
#
# Example of a BIOS game ------------------------------------------------------
#  <game name="neogeo" sourcefile="neogeo.c" isbios="yes">
#    <description>Neo-Geo</description>
#    <year>1990</year>
#    <manufacturer>SNK</manufacturer>
#    <biosset name="euro" description="Europe MVS (Ver. 2)" default="yes"/>
#    <biosset name="euro-s1" description="Europe MVS (Ver. 1)"/>
#    ...
#    <rom name="sp-s2.sp1" bios="euro" size="131072" crc="" sha1="" region="mainbios" offset="0"/>
#    <rom name="sp-s.sp1" bios="euro-s1" size="131072" crc="" sha1="" region="mainbios" offset="0"/>
#    ...
#  </game>
#
# Example of a CHD game -------------------------------------------------------
# See http://www.mameworld.info/easyemu/mameguide/mameguide-roms.html
# Some games with CHDs:
#  99bottles cdrom
#  area51mx ide:0:hdd:image
#  astron laserdisc
#  astron laserdisc
#  atronic cdrom
#  av2mj1bb vhs
#  av2mj2rg vhs
#  gdt-0010c gdrom
#
# Some games have a disk entry and no <device><extension name="chd"...
#  <disk name="astron" status="nodump" region="laserdisc" index="0" writable="no"/>
#  <disk name="atronic" sha1="" region="cdrom" index="0" writable="no" optional="yes"/>
#  <disk name="gdt-0010c" sha1="" status="baddump" region="gdrom" index="0" writable="no"/>
#
#  <game name="carnevil" sourcefile="seattle.c">
#    <description>CarnEvil (v1.0.3)</description>
#    <year>1998</year>
#    <manufacturer>Midway Games</manufacturer>
#    <disk name="carnevil" sha1="" region="ide:0:hdd:image" index="0" writable="yes"/>
#    ...
#    <driver status="good" emulation="good" color="good" sound="good" graphic="good" savestate="supported"/>
#    <device type="harddisk" tag="ide:0:hdd:image">
#      <instance name="harddisk" briefname="hard"/>
#      <extension name="chd"/>
#      <extension name="hd"/>
#    </device>
#  </game>
#
# Dependencies implementation -------------------------------------------------
# To solve a) games that depend on a device that has a ROM:
#   1) Traverse MAME XML and make a list of devices that have a ROM. A device has
#      a ROM if there is a ROM tag inside the game object.
#   2) Traverse MAME XML for games that are not devices. For every game, iterate
#      over the <device_ref> list and check if "name" attribute is on the devices
#      with ROM list. If found make a dependency (device_depends).
#
# To solve b) games that depend on a BIOS:
#   Maybe the <game> attribute "romof" can be used to resolve BIOS dependencies!
#
#   However, "cloneof" games also have "romof" field, for example
#    <game name="005" sourcefile="segag80r.c" sampleof="005" cloneof="10yard" romof="10yard">
#
#   What if a game is a clone and depends on a BIOS? For example
#    <game name="mslug3" sourcefile="neogeo.c" romof="neogeo">
#    <game name="mslug3b6" sourcefile="neogeo.c" cloneof="mslug3" romof="mslug3">
#
#   1) Traverse MAME XML and make a list of BIOSes.
#   2) Traverse MAME XML for standard games (no bios, no device) and check:
#      a) game has "romof" attribute and not "cloneof" attribute, add a
#         bios_depends dependency.
#      b) game has a "romof" attribute and a "cloneof" attribute. In this case,
#         the parent game should be checked for a) case.
#
# To solve c) games that depend on CHD:
#   A game has a CHD if it has a <disk> entry, and this entry has an attribute
#   sha1 with checksum
#
__debug_do_reduce_XML_dependencies = 0;
def do_reduce_XML():
  "Short list of MAME XML file (Experimental)"

  NARS.print_info('[Reducing MAME XML game database]');
  input_filename = configuration.MAME_XML;
  output_filename = configuration.MAME_XML_redux;

  # --- Build XML output file ---
  tree_output = ET.ElementTree();
  root_output = ET.Element('mame');
  tree_output._setroot(root_output);

  # --- Read MAME XML input file ---
  NARS.print_info('Reading MAME XML game database...');
  NARS.print_info('NOTE: this will take a looong time...');
  tree = NARS.XML_read_file(input_filename, "Parsing MAME XML file");

  # --- Dependencies variables
  device_rom_list = [];
  bios_list = [];
  chd_list = [];

  # --- Traverse MAME XML input file ---
  # Root element:
  # <mame build="0.153 (Apr  7 2014)" debug="no" mameconfig="10">
  root = tree.getroot();
  root_output.attrib = root.attrib; # Copy mame attributes in output XML

  # Child elements we want to keep in the reduced XML:
  # NOTE since the mergue of MAME and MESS, <game> has been substituded by
  #      <machine>
  # <machine name="005" 
  #          sourcefile="segag80r.c" 
  #          sampleof="005" 
  #          cloneof="10yard" romof="10yard">
  #   <description>005</description>
  #   <year>1981</year>
  #   <manufacturer>Sega</manufacturer>
  # ...
  #   <display tag="screen" type="raster" rotate="270" width="256" height="224" refresh="59.998138" pixclock="5156000" htotal="328" hbend="0" hbstart="256" vtotal="262" vbend="0" vbstart="224" />
  # ...
  #   <input players="2" buttons="1" coins="2" service="yes">
  #     <control type="joy" ways="4"/>
  #   </input>
  # ...
  #   <driver status="imperfect" emulation="good" color="good" sound="imperfect" graphic="good" savestate="unsupported"/>
  # </machine>
  NARS.print_info('[Reducing MAME XML database]');
  for machine_EL in root:
    isdevice_flag = 0;
    if machine_EL.tag == 'machine':
      NARS.print_verb('[Machine]');
      game_output = ET.SubElement(root_output, 'machine');
      # Copy machine attributes in output XML
      game_output.attrib = machine_EL.attrib;

      # Put BIOSes in the list
      if 'isbios' in game_output.attrib:
        bios_list.append(game_output.attrib['name']);

      if 'isdevice' in game_output.attrib:
        isdevice_flag = 1;

      # --- Iterate through machine tag attributes (DEBUG)
      # for key in machine_EL.attrib:
      #   print ' machine --', key, '->', machine_EL.attrib[key];

      # --- Iterate through the children of a machine
      for machine_child in machine_EL:
        if machine_child.tag == 'description':
          NARS.print_verb(' description = ' + machine_child.text);
          description_output = ET.SubElement(game_output, 'description');
          description_output.text = machine_child.text;

        if machine_child.tag == 'year':
          NARS.print_verb(' year = ' + machine_child.text);
          year_output = ET.SubElement(game_output, 'year');
          year_output.text = machine_child.text;

        if machine_child.tag == 'manufacturer':
          NARS.print_verb(' manufacturer = ' + machine_child.text);
          manufacturer_output = ET.SubElement(game_output, 'manufacturer');
          manufacturer_output.text = machine_child.text;

        if machine_child.tag == 'input':
          input_output = ET.SubElement(game_output, 'input');
          input_output.attrib = machine_child.attrib; # Copy machine attributes in output XML

          # Traverse children
          for input_child in machine_child:
            if input_child.tag == 'control':
              control_output = ET.SubElement(input_output, 'control');
              control_output.attrib = input_child.attrib;

        if machine_child.tag == 'driver':
          driver_output = ET.SubElement(game_output, 'driver');
          driver_output.attrib = machine_child.attrib; # Copy game attributes in output XML

        # --- CHDs (disks)
        if machine_child.tag == 'disk':
          # print machine_child.attrib['name'], machine_child.attrib['region'];
          if 'name' in machine_child.attrib and 'sha1' in machine_child.attrib:
            chd_list.append(machine_child.attrib['name']);

        # --- List of devices with ROMs
        if isdevice_flag:
          if machine_child.tag == 'rom':
            device_rom_list.append(game_output.attrib['name']);

  if __debug_do_reduce_XML_dependencies:
    # --- Print list of BIOSes
    print('[List of BIOSes]')
    for biosName in bios_list:
      print(biosName)

    # --- Print list of devices with ROM
    print('[List of devices with ROMs]')
    for deviceName in device_rom_list:
      print(deviceName)

    # --- Print list of ROMs with CHD
    print('[List of game with disks]')
    for chdName in chd_list:
      print(chdName)

  # --- Make list of dependencies
  device_depends_dic = {};
  parent_bios_depends_dic = {};
  chd_depends_dic = {};
  NARS.print_info('[Checking ROM dependencies (1st pass)]');
  for game_EL in root:
    if game_EL.tag == 'game':
      if 'romof' in game_EL.attrib:
        # --- Case a)
        if 'cloneof' not in game_EL.attrib:
          parent_bios_depends_dic[game_EL.attrib['name']] = game_EL.attrib['romof'];
          if __debug_do_reduce_XML_dependencies:
            print('game = ' + game_EL.attrib['name'] + ' BIOS depends on ' + game_EL.attrib['romof'])
        # --- Case b) Parent should be checked
        else:
          # print 'game = ' + game_EL.attrib['name'] + ' is a clone a parent must be checked for BIOS dependencies';
          pass

      # --- Check for device dependencies
      # --- Check for CHD dependencies
      device_depends = [];
      for game_child in game_EL:
        if game_child.tag == 'device_ref':
          if 'name' in game_child.attrib:
            # --- Check if this is in the list of devices with ROMs
            if game_child.attrib['name'] in device_rom_list:
              if __debug_do_reduce_XML_dependencies:
                print('game = ' + game_EL.attrib['name'] + ' device depends on ' + game_child.attrib['name'])
              # --- Insert a device dependency in a list
              device_depends.append(game_child.attrib['name']);
          else:
            print_error('device_ref has no name attribute!');
            sys.exit(10);
        # CHDs
        elif game_child.tag == 'disk':
          if 'sha1' in game_child.attrib:
            # CAREFUL: disk name (CHD) is not necessary the same as the ROM name
            # If a game has more than 1 disk, this will produce a key error.
            chd_depends_dic[game_EL.attrib['name']] = game_child.attrib['name'];

      # --- If device dependency list is not empty, insert a <device_depends>
      #     tag.
      if len(device_depends) > 0:
        device_depends_dic[game_EL.attrib['name']] = device_depends;

  NARS.print_info('[Checking ROM dependencies (2nd pass)]')
  bios_depends_dic = {};
  for game_EL in root:
    if game_EL.tag == 'game':
      if 'romof' in game_EL.attrib:
        # --- Case a)
        if 'cloneof' not in game_EL.attrib:
          bios_depends_dic[game_EL.attrib['name']] = game_EL.attrib['romof'];
          if __debug_do_reduce_XML_dependencies:
            print('game = ' + game_EL.attrib['name'] + ' BIOS depends on ' + game_EL.attrib['romof'])
        # --- Case b) Parent should be checked
        else:
          # If parent is in this list then clone has a BIOS dependence
          if game_EL.attrib['cloneof'] in parent_bios_depends_dic:
            bios_depends_dic[game_EL.attrib['name']] = parent_bios_depends_dic[game_EL.attrib['cloneof']];
            if __debug_do_reduce_XML_dependencies:
              print('game = ' + game_EL.attrib['name'] + ' is a clone that BIOS depends on ' + \
                    parent_bios_depends_dic[game_EL.attrib['cloneof']])

  # --- To save memory destroy variables now
  del tree;
  del root;

  # --- Incorporate dependencies into output XML
  NARS.print_info('[Merging ROM dependencies in output XML]')
  for game_EL in root_output:
    if game_EL.tag == 'game':
      game_name = game_EL.attrib['name'];
      if game_name in bios_depends_dic:
        # values of bios_depends_dic are strings
        bios_depends_tag = ET.SubElement(game_EL, 'bios_depends');
        bios_depends_tag.text = bios_depends_dic[game_name];

      if game_name in device_depends_dic:
        # values of device_depends_dic are lists
        # There may be duplicate devices in the list (game has two devices of
        # the same kind). Remove duplicates to improve later processing.
        # http://stackoverflow.com/questions/7961363/python-removing-duplicates-in-lists
        device_depends_tag = ET.SubElement(game_EL, 'device_depends');
        device_depends_tag.text = ",".join(set(device_depends_dic[game_name]));

      if game_name in chd_depends_dic:
        # values of bios_depends_dic are strings
        chd_depends_tag = ET.SubElement(game_EL, 'chd_depends');
        chd_depends_tag.text = chd_depends_dic[game_name];

  # --- Pretty print XML output using miniDOM
  # See http://broadcast.oreilly.com/2010/03/pymotw-creating-xml-documents.html
  # NOTE this approach works well but is very slooow
  if 0:
    NARS.print_info('[Building reduced output XML file]');
    rough_string = ET.tostring(root_output, 'utf-8');
    reparsed = minidom.parseString(rough_string);
    del root_output; # Reduce memory consumption
    NARS.print_info('Writing reduced XML file ' + output_filename);
    f = open(output_filename, "w")
    f.write(reparsed.toprettyxml(indent=" "))
    f.close()

  # --- Write output file (don't use miniDOM, is sloow)
  # See http://norwied.wordpress.com/2013/08/27/307/
  NARS.print_info('[Writing output file]');
  NARS.print_info('Writing reduced XML file ' + output_filename);
  indent_ElementTree_XML(root_output);
  tree_output.write(output_filename, xml_declaration=True, encoding='utf-8', method="xml")

def do_merge():
  """Merges main MAME database ready for filtering"""

  NARS.print_info('[Building merged MAME filter database]')
  mame_redux_filename = configuration.MAME_XML_redux
  merged_filename = configuration.MergedInfo_XML

  # --- Get categories from Catver.ini
  categories_dic = parse_catver_ini();

  # --- Read MAME XML or reduced MAME XML and incorporate categories
  # NOTE: this piece of code is very similar to do_reduce_XML()
  # --- Build XML output file ---
  tree_output = ET.ElementTree();
  root_output = ET.Element('mame');
  tree_output._setroot(root_output);
  NARS.print_info('[Parsing (reduced) MAME XML file]');
  tree = NARS.XML_read_file_cElementTree(mame_redux_filename, "Reading merged XML file")
  
  # --- Traverse MAME XML input file ---
  NARS.print_info('[Merging MAME XML and categories]');
  root = tree.getroot();
  root_output.attrib = root.attrib; # Copy mame attributes in output XML
  num_no_category = 0
  for machine_EL in root:
    if machine_EL.tag == 'machine':
      machine_output = ET.SubElement(root_output, 'machine');
      # Copy machine attributes in output XML
      machine_output.attrib = machine_EL.attrib;

      # --- Iterate through the children of a machine
      for machine_child in machine_EL:
        if machine_child.tag == 'description':
          description_output = ET.SubElement(machine_output, 'description');
          description_output.text = machine_child.text;

        if machine_child.tag == 'year':
          year_output = ET.SubElement(machine_output, 'year');
          year_output.text = machine_child.text;

        if machine_child.tag == 'manufacturer':
          manufacturer_output = ET.SubElement(machine_output, 'manufacturer');
          manufacturer_output.text = machine_child.text;

        if machine_child.tag == 'input':
          # --- This information is not used yet. Don't add to the output
          #     file to save some space.
          input_output = ET.SubElement(machine_output, 'input');
          input_output.attrib = machine_child.attrib; # Copy game attributes in output XML

          # Traverse children
          for input_child in machine_child:
            if input_child.tag == 'control':
              # --- This information is not used yet. Don't add to the output
              #     file to save some space.
              control_output = ET.SubElement(input_output, 'control');
              control_output.attrib = input_child.attrib;

        if machine_child.tag == 'driver':
          driver_output = ET.SubElement(machine_output, 'driver');
          # --- From here only attribute 'status' is used
          driver_attrib = {};
          driver_attrib['status'] = machine_child.attrib['status'];
          driver_output.attrib = driver_attrib;

        # --- Dependencies
        if machine_child.tag == 'device_depends':
          device_depends_output = ET.SubElement(machine_output, 'device_depends');
          device_depends_output.text = machine_child.text;

        if machine_child.tag == 'bios_depends':
          bios_depends_output = ET.SubElement(machine_output, 'bios_depends');
          bios_depends_output.text = machine_child.text;

        if machine_child.tag == 'chd_depends':
          chd_depends_output = ET.SubElement(machine_output, 'chd_depends');
          chd_depends_output.text = machine_child.text;

      # --- Add category element
      game_name = machine_EL.attrib['name'];
      category = 'Unknown';
      if game_name in categories_dic:
        category = categories_dic[game_name];
      else:
        NARS.print_warn('[WARNING] Category not found for game ' + game_name);
        num_no_category += 1
      category_output = ET.SubElement(machine_output, 'category');
      category_output.text = category;
  NARS.print_info('[Report]');
  NARS.print_info('Machines without category  ' + str(num_no_category));

  # --- To save memory destroy variables now
  del tree;

  # --- Write output file (don't use miniDOM, is sloow)
  # See http://norwied.wordpress.com/2013/08/27/307/
  NARS.print_info('[Writing output file]');
  NARS.print_info('Output file ' + merged_filename);
  NARS.indent_ElementTree_XML(root_output);
  tree_output.write(merged_filename, xml_declaration=True, encoding='utf-8', method="xml")

def do_list_merged():
  "Short list of MAME XML file"

  NARS.print_info('[List reduced MAME XML]');
  filename = configuration.MergedInfo_XML;
  tree = NARS.XML_read_file_cElementTree(filename, "Parsing merged XML file")

  # Root element (Reduced MAME XML):
  root = tree.getroot();

  # Child elements (Reduced MAME XML):
  num_games = 0;
  num_clones = 0;
  num_samples = 0;
  num_devices = 0;
  num_BIOS = 0;
  num_norunnable = 0;
  for machine_EL in root:
    if machine_EL.tag == 'machine':
      num_games += 1;
      # Machine attributes
      machine_attrib = machine_EL.attrib;
      NARS.print_info(machine_attrib['name']);

      # Machine attributes
      if 'sourcefile' in machine_attrib:
        NARS.print_info('-         driver   ' + machine_attrib['sourcefile']);
      if 'sampleof' in machine_attrib:
        num_samples += 1;
        NARS.print_info('-       sampleof   ' + machine_attrib['sampleof']);
      if 'cloneof' in machine_attrib:
        num_clones += 1;
        NARS.print_info('-        cloneof   ' + machine_attrib['cloneof']);
      if 'isdevice' in machine_attrib:
        num_devices += 1;
        NARS.print_info('-       isdevice   ' + machine_attrib['isdevice']);
      if 'isbios' in machine_attrib:
        num_BIOS += 1;
        NARS.print_info('-         isbios   ' + machine_attrib['isbios']);
      if 'runnable' in machine_attrib:
        if machine_attrib['runnable'] == 'yes':
          print('Found a machine with runnable="yes" attribute! Exiting...')
          sys.exit(10)
        else:
          num_norunnable += 1;
        NARS.print_info('-       runnable   ' + machine_attrib['runnable']);
        

      # Iterate through the children of a machine
      for machine_child in machine_EL:
        if machine_child.tag == 'description':
          NARS.print_info('--   description   ' + machine_child.text);
        elif machine_child.tag == 'year':
          NARS.print_info('--          year   ' + machine_child.text);
        elif machine_child.tag == 'manufacturer':
          NARS.print_info('--  manufacturer   ' + machine_child.text);
        elif machine_child.tag == 'driver':
          NARS.print_info('-- driver status   ' + machine_child.attrib['status']);
        elif machine_child.tag == 'category':
          NARS.print_info('--      category   ' + machine_child.text);
#    else:
#      NARS.print_info('Machine tag = ' + machine_EL.tag)

  NARS.print_info('[Report]');
  NARS.print_info('Number of machines     ' + str(num_games))
  NARS.print_info('Number of clones       ' + str(num_clones))
  NARS.print_info('Number of arcades      ' + str(-1))
  NARS.print_info('Number of non-arcades  ' + str(-1))
  NARS.print_info('Machines with samples  ' + str(num_samples))
  NARS.print_info('Machines with CHDs     ' + str(-1))
  NARS.print_info('Number of devices      ' + str(num_devices))
  NARS.print_info('Number of BIOS         ' + str(num_BIOS))
  NARS.print_info('Machines non-runnable  ' + str(num_norunnable))

def do_list_categories():
  "Parses Catver.ini and prints the categories and how many games for each"

  __debug_do_list_categories = 0;
  NARS.print_info('[Listing categories from Catver.ini]');

  # --- Create a histogram with the available categories based only in Catver.ini
  cat_filename = configuration.Catver;
  NARS.print_info('Parsing ' + cat_filename);
  categories_dic = {};
  main_categories_dic = {};
  final_categories_dic = {};
  f = open(cat_filename, 'r');
  # 0 -> Looking for '[Category]' tag
  # 1 -> Reading categories
  # 2 -> Categories finished. STOP
  read_status = 0;
  NARS.print_info('[Making categories histogram]');
  for cat_line in f:
    stripped_line = cat_line.strip();
    if __debug_do_list_categories:
      print('"' + stripped_line + '"')
    if read_status == 0:
      if stripped_line == '[Category]':
        if __debug_do_list_categories:
          print('Found [Category]')
        read_status = 1;
    elif read_status == 1:
      line_list = stripped_line.split("=");
      if len(line_list) == 1:
        read_status = 2;
        continue;
      else:
        if __debug_do_list_categories:
          print(line_list)
        category = line_list[1];
        if category in categories_dic:
          categories_dic[category] += 1;
        else:
          categories_dic[category] = 1;
        # --- Sub-categories  
        sub_categories = category.split("/");
        if __debug_do_list_categories:
          print(sub_categories)
        main_category = sub_categories[0].strip();
        second_category = sub_categories[0].strip();
        if main_category in main_categories_dic: 
          main_categories_dic[main_category] += 1;
        else:
          main_categories_dic[main_category] = 1;

        # NOTE Only use the main category for filtering.
        final_category = fix_category_name(main_category, category);

        # Create final categories dictionary
        if final_category in final_categories_dic: 
          final_categories_dic[final_category] += 1;
        else:
          final_categories_dic[final_category] = 1;
    elif read_status == 2:
      break;
    else:
      print_error('Unknown read_status FSM value');
      sys.exit(10);
  f.close();

  # --- Only print if very verbose
  if NARS.log_level >= NARS.Log.vverb:
    # Want to sort categories_dic['category'] = integer by the integer
    # Sorting dictionaries, see
    # http://stackoverflow.com/questions/613183/python-sort-a-dictionary-by-value
    # This is only valid in Python 2
#    sorted_propertiesDic = sorted(categories_dic.iteritems(), key=operator.itemgetter(1))
    # This works on Python 3
    sorted_histo = ((k, categories_dic[k]) for k in sorted(categories_dic, key=categories_dic.get, reverse=False))
    # - DEBUG object dump
    # dumpclean(sorted_propertiesDic);
    # - Better print (only print if verbose)
    NARS.print_vverb('[Raw categories]');
    for k, v in sorted_histo:
      NARS.print_verb('{:6d}'.format(v) + '  ' + k);

  # --- Only print if verbose
  if NARS.log_level >= NARS.Log.verb:
    sorted_histo = ((k, main_categories_dic[k]) for k in sorted(main_categories_dic, key=main_categories_dic.get, reverse=False))
    NARS.print_verb('[Main categories]');
    for k, v in sorted_histo:
      NARS.print_verb('{:6d}'.format(v) + '  ' + k);

  # --- By default only list final categories
  sorted_histo = ((k, final_categories_dic[k]) for k in sorted(final_categories_dic, key=final_categories_dic.get, reverse=False))
  NARS.print_info('[Final (used) categories]');
  num_categories = 0
  for k, v in sorted_histo:
    NARS.print_info('{:6d}'.format(v) + '  ' + k);
    num_categories += 1
  NARS.print_info('[Report]');
  NARS.print_info('Number of categories  ' + str(num_categories))

def do_list_drivers():    
  "Parses merged XML database and makes driver histogram and statistics"

  NARS.print_info('[Listing MAME drivers]');
  NARS.print_info('NOTE: clones are not included');
  NARS.print_info('NOTE: mechanical are not included');
  NARS.print_info('NOTE: devices are not included');

  filename = configuration.MergedInfo_XML;
  tree = NARS.XML_read_file_cElementTree(filename, "Reading merged XML file")

  # Do histogram
  drivers_histo_dic = {};
  root = tree.getroot();
  for machine_EL in root:
    if machine_EL.tag == 'machine':
      machine_attrib = machine_EL.attrib;
      # If machine is a clone don't include it in the histogram
      if 'cloneof' in machine_attrib:
        continue;
      # - If machine is mechanical don't include it
      if 'ismechanical' in machine_attrib:
        continue;
      # - If machine is device don't include it
      if 'isdevice' in machine_attrib:
        continue;

      # --- Histogram
      if 'sourcefile' in machine_attrib:
        driver_name = machine_attrib['sourcefile'];
      else:
        driver_name = '__unknown__';
      if driver_name in drivers_histo_dic: 
        drivers_histo_dic[driver_name] += 1;
      else:
        drivers_histo_dic[driver_name] = 1;

  # --- Print histogram
  # Valid in Python 2
#  sorted_histo = sorted(drivers_histo_dic.iteritems(), key=operator.itemgetter(1))
  # Valid in Python 3
  sorted_histo = ((k, drivers_histo_dic[k]) for k in sorted(drivers_histo_dic, key=drivers_histo_dic.get, reverse=False))
  NARS.print_info('[Final (used) drivers]');
  num_drivers = 0
  for k, v in sorted_histo:
    NARS.print_info('{:4d}'.format(v) + '  ' + k);
    num_drivers += 1

  NARS.print_info('[Report]');
  NARS.print_info('Number of drivers  ' + str(num_drivers))

# See http://mamedev.org/source/src/emu/info.c.html, line 784
__debug_do_list_controls = 0;
def do_list_controls():
  "Parses merged XML database and makes a controls histogram"

  NARS.print_info('[Listing MAME controls]');
  NARS.print_info('NOTE: clones are not included');
  NARS.print_info('NOTE: mechanical are not included');
  NARS.print_info('NOTE: devices are not included');

  # filename = configuration.MergedInfo_XML;
  filename = configuration.MAME_XML_redux
  tree = NARS.XML_read_file_cElementTree(filename, "Reading merged XML file")

  # --- Histogram data
  input_buttons_dic = {};
  input_players_dic = {};
  input_control_type_dic = {};
  input_control_type_join_dic = {};
  input_control_ways_dic = {};

  # --- Do histogram
  root = tree.getroot();
  for game_EL in root:
    if game_EL.tag == 'machine':
      game_attrib = game_EL.attrib;

      # - If game is a clone don't include it in the histogram
      if 'cloneof' in game_attrib:
        continue;
      # - If game is mechanical don't include it
      if 'ismechanical' in game_attrib:
        continue;
      # - If game is device don't include it
      if 'isdevice' in game_attrib:
        continue;

      game_name = game_attrib['name']
      if __debug_do_list_controls:
        print('game = ' + game_name);

      # --- Histogram of controls
      for child_game_EL in game_EL:
        # --- Input tag found
        if child_game_EL.tag == 'input':
          game_input_EL = child_game_EL;

          # --- Input attributes
          if 'buttons' in game_input_EL.attrib:
            if __debug_do_list_controls:
              print(' buttons = ' + game_input_EL.attrib['buttons']);
            input_buttons_dic = add_to_histogram(game_input_EL.attrib['buttons'], input_buttons_dic);
          else:
            if __debug_do_list_controls:
              print(' no buttons');
            input_buttons_dic = add_to_histogram('0', input_buttons_dic);

          if 'coins' in game_input_EL.attrib:
            if __debug_do_list_controls:
              print(' coins = ' + game_input_EL.attrib['coins']);

          if 'players' in game_input_EL.attrib:
            if __debug_do_list_controls:
              print(' players = ' + game_input_EL.attrib['players']);
            input_players_dic = add_to_histogram(game_input_EL.attrib['players'], input_players_dic);
          else:
            if __debug_do_list_controls:
              print(' no players')
            input_buttons_dic = add_to_histogram('no players tag', input_buttons_dic);

          if 'tilt' in game_input_EL.attrib:
            if __debug_do_list_controls:
              print(' tilt = ' + game_input_EL.attrib['tilt'])

          # --- Iterate children
          control_child_found = 0;
          control_type_list = [];
          for child in game_input_EL:
            control_child_found = 1;
            if __debug_do_list_controls:
              print(' Children = ' + child.tag)

            if 'type' in child.attrib:
              if __debug_do_list_controls:
                print('  type = ' + child.attrib['type'])
              input_control_type_dic = add_to_histogram(child.attrib['type'].title(), input_control_type_dic);
              control_type_list.append(child.attrib['type']);

            if 'ways' in child.attrib:
              if __debug_do_list_controls:
                print('  ways = ' + child.attrib['ways'])
              input_control_ways_dic = add_to_histogram(child.attrib['ways'], input_control_ways_dic);

            if 'ways2' in child.attrib:
              if __debug_do_list_controls:
                print('  ways2 = ' + child.attrib['ways2'])

            if 'ways3' in child.attrib:
              if __debug_do_list_controls:
                print('  ways3 = ' + child.attrib['ways3'])

          text_not_found = 'ButtonsOnly';
          if len(control_type_list) < 1:
            control_type_list.append(text_not_found);
          input_control_type_join_dic = add_to_histogram(', '.join(sorted(control_type_list)), input_control_type_join_dic);

          # --- If no additional controls, only buttons???
          if not control_child_found:
            if text_not_found in input_control_type_dic:
              input_control_type_dic[text_not_found] += 1;
            else:                          
              input_control_type_dic[text_not_found] = 1;

  NARS.print_info('[Input - control - type histogram (per game)]')
  sorted_histo = ((k, input_control_type_join_dic[k]) for k in sorted(input_control_type_join_dic, key=input_control_type_join_dic.get, reverse=False))
  for k, v in sorted_histo:
    NARS.print_info('{:5d}'.format(v) + '  ' + k)
  print(' ')

  NARS.print_info('[Input - buttons histogram]')
  sorted_histo = ((k, input_buttons_dic[k]) for k in sorted(input_buttons_dic, key=input_buttons_dic.get, reverse=False))
  for k, v in sorted_histo:
    if len(k) == 1:
      NARS.print_info('{:5d}'.format(v) + '   ' + k + ' button/s')
    elif len(k) == 2:
      NARS.print_info('{:5d}'.format(v) + '  ' + k + ' button/s')
    else:
      print('len(buttons) error')
      sys.exit(10)
  print(' ')

  NARS.print_info('[Input - players histogram]')
  sorted_histo = ((k, input_players_dic[k]) for k in sorted(input_players_dic, key=input_players_dic.get, reverse=False))
  for k, v in sorted_histo:
    NARS.print_info('{:5d}'.format(v) + '  ' + k + ' players')
  print(' ')

  NARS.print_info('[Input - control - type histogram]')
  sorted_histo = ((k, input_control_type_dic[k]) for k in sorted(input_control_type_dic, key=input_control_type_dic.get, reverse=False))
  for k, v in sorted_histo:
    NARS.print_info('{:5d}'.format(v) + '  ' + k)

def do_list_years():
  "Parses merged XML database and makes a controls histogram"

  NARS.print_info('[Listing MAME controls]');
  NARS.print_info('NOTE: clones are not included');
  NARS.print_info('NOTE: mechanical are not included');
  NARS.print_info('NOTE: devices are not included');

  # filename = configuration.MergedInfo_XML;
  filename = configuration.MAME_XML_redux
  tree = NARS.XML_read_file_cElementTree(filename, "Reading merged XML file")

  # --- Histogram data
  years_dic = {};
  raw_years_dic = {};

  # --- Do histogram
  root = tree.getroot();
  for game_EL in root:
    if game_EL.tag == 'machine':
      game_attrib = game_EL.attrib;

      # - Remove crap
      if 'cloneof' in game_attrib:
        continue;
      if 'isdevice' in game_attrib:
        continue;
      if 'ismechanical' in game_attrib:
        continue;

      # - Game name
      game_name = game_attrib['name']

      # --- Histogram of years
      has_year = 0;
      for child_game_EL in game_EL:
        if child_game_EL.tag == 'year':
          has_year = 1;
          game_year_EL = child_game_EL;
          raw_year_text = game_year_EL.text;
          # Remove quotation marks from some years
          # Expand wildcards to numerical lists. Currently there are 6 cases
          year_list = trim_year_string(raw_year_text);

          # --- Make histogram
          for number in year_list:
            years_dic = add_to_histogram(number, years_dic);
          raw_years_dic = add_to_histogram(raw_year_text, raw_years_dic);

      if not has_year:
        years_dic = add_to_histogram('no year', years_dic);
        raw_years_dic = add_to_histogram('no year', raw_years_dic);

  NARS.print_info('[Release year histogram (raw)]');
  sorted_histo = ((k, raw_years_dic[k]) for k in sorted(raw_years_dic, key=raw_years_dic.get, reverse=False))
  for k, v in sorted_histo:
    NARS.print_info('{:5d}'.format(v) + '  ' + k)
  print(' ')

  NARS.print_info('[Release year histogram (trimmed)]');
  sorted_histo = ((k, years_dic[k]) for k in sorted(years_dic, key=years_dic.get, reverse=False))
  for k, v in sorted_histo:
    NARS.print_info('{:5d}'.format(v) + '  ' + k)

# ----------------------------------------------------------------------------
def do_list_filters():
  """List of configuration file"""

  NARS.print_info('[Listing configuration file]')
  tree = NARS.XML_read_file_ElementTree(__config_configFileName, "Parsing configuration XML file")

  # Iterate over XML root object
  root = tree.getroot();
  for root_child in root:
    if root_child.tag == 'General':
      NARS.print_info('<General configuration>')
      # Iterate through children nodes
      for root_child_node in root_child:
        if root_child_node.tag == 'MAME_XML':
          NARS.print_info('MAME_XML        ' + root_child_node.text)
        elif root_child_node.tag == 'MAME_XML_redux':
          NARS.print_info('MAME_XML_redux  ' + root_child_node.text)
        elif root_child_node.tag == 'Catver':
          NARS.print_info('Catver          ' + root_child_node.text)
        elif root_child_node.tag == 'Merged_XML':
          NARS.print_info('Merged_XML      ' + root_child_node.text)
    elif root_child.tag == 'MAMEFilter':
      NARS.print_info('<MAME filter>')
      NARS.print_info('Name        ' + root_child.attrib['name'])
      for root_child_node in root_child:
        if root_child_node.tag == 'ROMsSource':
          NARS.print_info('ROMsSource  ' + root_child_node.text);
        elif root_child_node.tag == 'ROMsDest':
          NARS.print_info('ROMsDest    ' + root_child_node.text);
    else:
      print('Tag with wrong name ' + root_child.tag)
      sys.exit(10)

# ----------------------------------------------------------------------------
def do_checkFilter(filterName):
  "Applies filter and copies ROMs into destination directory"

  NARS.print_info('[Checking filter]');
  NARS.print_info('Filter name = ' + filterName);

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_Config(filterName);
  sourceDir = filter_config.sourceDir;
  destDir = filter_config.destDir;

  # --- Check for errors, missing paths, etc...
  NARS.have_dir_or_abort(sourceDir);
  NARS.have_dir_or_abort(destDir);

  # --- Get MAME parent/clone dictionary --------------------------------------
  mame_xml_dic = parse_MAME_merged_XML();

  # --- Create main ROM list in sourceDir -------------------------------------
  rom_main_list = get_ROM_main_list(sourceDir);

  # --- Apply filter and create list of files to be copied --------------------
  mame_filtered_dic = apply_MAME_filters(mame_xml_dic, filter_config);

  # --- Print list in alphabetical order
  NARS.print_info('[Filtered game list]');
  missing_roms = 0;
  have_roms = 0;
  for key_main in sorted(mame_filtered_dic):
    romObject = mame_filtered_dic[key_main];

    # --- Check if file exists (maybe it does not exist for No-Intro lists)
    sourceFullFilename = sourceDir + romObject.name + '.zip';
    haveFlag = 'Have ROM';
    if not os.path.isfile(sourceFullFilename):
      missing_roms += 1;
      haveFlag = 'Missing ROM';
    else:
      have_roms += 1;

    # --- Print
    NARS.print_info("<Game> " + romObject.name.ljust(8) + ' - ' + \
                    haveFlag.ljust(11) + ' - ' + romObject.description + ' ');

  NARS.print_info('[Report]');
  NARS.print_info('Number of filtered ROMs = ' + str(len(mame_filtered_dic)));
  NARS.print_info('Number of have ROMs = ' + str(have_roms));
  NARS.print_info('Number of missing ROMs = ' + str(missing_roms));

# ----------------------------------------------------------------------------
# Copy ROMs in destDir
def do_update(filterName):
  "Applies filter and copies ROMs into destination directory"

  NARS.print_info('[Copy/Update ROMs]');
  NARS.print_info('Filter name = ' + filterName);

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_Config(filterName);
  sourceDir = filter_config.sourceDir;
  destDir = filter_config.destDir;

  # --- Check for errors, missing paths, etc...
  NARS.have_dir_or_abort(sourceDir);
  NARS.have_dir_or_abort(destDir);

  # --- Get MAME parent/clone dictionary --------------------------------------
  mame_xml_dic = parse_MAME_merged_XML();

  # --- Create main ROM list in sourceDir -------------------------------------
  rom_main_list = get_ROM_main_list(sourceDir);

  # --- Apply filter and create list of files to be copied --------------------
  mame_filtered_dic = apply_MAME_filters(mame_xml_dic, filter_config);
  rom_copy_list = create_copy_list(mame_filtered_dic, rom_main_list);

  # --- Copy ROMs into destDir ------------------------------------------------
  if __prog_option_sync:
    update_ROM_list(rom_copy_list, sourceDir, destDir);
  else:
    copy_ROM_list(rom_copy_list, sourceDir, destDir);

  # If --cleanROMs is on then delete unknown files.
  if __prog_option_clean_ROMs:
    clean_ROMs_destDir(destDir, rom_copy_list);

  # --- Generate NFO XML files with information for launchers
  if __prog_option_generate_NFO:
    generate_NFO_files(rom_copy_list, mame_filtered_dic, destDir);

  # --- Delete NFO files of ROMs not present in the destination directory.
  if __prog_option_clean_NFO:
    delete_redundant_NFO(destDir);

# ----------------------------------------------------------------------------
def do_check_CHD(filterName):
  "Applies filter and copies ROMs into destination directory"

  NARS.print_info('[Checking CHDs]');
  NARS.print_info('Filter name = ' + filterName);

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_Config(filterName);
  sourceDir = filter_config.sourceDir;
  destDir = filter_config.destDir;
  sourceDir_CHD = filter_config.destDir_CHD;

  # --- Check for errors, missing paths, etc...
  NARS.have_dir_or_abort(sourceDir);
  NARS.have_dir_or_abort(destDir);
  NARS.have_dir_or_abort(sourceDir_CHD);

  # --- Get MAME parent/clone dictionary --------------------------------------
  mame_xml_dic = parse_MAME_merged_XML();

  # --- Create main ROM list in sourceDir -------------------------------------
  rom_main_list = get_ROM_main_list(sourceDir);

  # --- Apply filter and create list of files to be copied --------------------
  mame_filtered_dic = apply_MAME_filters(mame_xml_dic, filter_config);

  # --- Create list of CHDs and samples needed --------------------------------
  CHD_dic = create_copy_CHD_dic(mame_filtered_dic);
  # samples_list = create_copy_samples_list(mame_filtered_dic);

  # --- Print list in alphabetical order
  NARS.print_info('[Filtered game list]');
  missing_roms = 0;
  have_roms = 0;
  for key_main in sorted(mame_filtered_dic):
    romObject = mame_filtered_dic[key_main];

    # --- Check if CHD exists (maybe it does not exist for No-Intro lists)
    sourceFullFilename = sourceDir + romObject.name + '.zip';
    haveFlag = 'Have ROM';
    if not os.path.isfile(sourceFullFilename):
      missing_roms += 1;
      haveFlag = 'Missing ROM';
    else:
      have_roms += 1;

    # --- Print
    NARS.print_info("<Game> " + romObject.name.ljust(8) + ' - ' + \
                    haveFlag.ljust(11) + ' - ' + romObject.description + ' ');

  NARS.print_info('[Report]');
  NARS.print_info('Number of filtered ROMs = ' + str(len(mame_filtered_dic)));
  NARS.print_info('Number of have ROMs = ' + str(have_roms));
  NARS.print_info('Number of missing ROMs = ' + str(missing_roms));

# ----------------------------------------------------------------------------
# Copy ROMs in destDir
def do_update_CHD(filterName):
  "Applies filter and copies ROMs into destination directory"

  NARS.print_info('[Copy/Update CHDs]');
  NARS.print_info('Filter name = ' + filterName);

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_Config(filterName);
  sourceDir = filter_config.sourceDir;
  destDir = filter_config.destDir;
  sourceDir_CHD = filter_config.destDir_CHD;

  # --- Check for errors, missing paths, etc...
  NARS.have_dir_or_abort(sourceDir);
  NARS.have_dir_or_abort(destDir);
  NARS.have_dir_or_abort(sourceDir_CHD);

  # --- Get MAME parent/clone dictionary --------------------------------------
  mame_xml_dic = parse_MAME_merged_XML();

  # --- Create main ROM list in sourceDir -------------------------------------
  rom_main_list = get_ROM_main_list(sourceDir);

  # --- Apply filter and create list of files to be copied --------------------
  mame_filtered_dic = apply_MAME_filters(mame_xml_dic, filter_config);
  rom_copy_list = create_copy_list(mame_filtered_dic, rom_main_list);

  # --- Create list of CHDs and samples needed --------------------------------
  CHD_dic = create_copy_CHD_dic(mame_filtered_dic);
  # samples_list = create_copy_samples_list(mame_filtered_dic);

  # --- Copy CHDs into destDir ------------------------------------------------
  if __prog_option_sync:
    update_CHD_dic(CHD_dic, sourceDir_CHD, destDir);
  else:
    copy_CHD_dic(CHD_dic, sourceDir_CHD, destDir);

  # If --cleanCHDs is on then delete unknown CHD and directories.
  if __prog_option_clean_CHD:
    clean_CHDs_destDir(destDir, CHD_dic);

# ----------------------------------------------------------------------------
def do_check_Artwork(filterName):
  "Checks for missing artwork and prints a report"

  NARS.print_info('[Check-ArtWork]');
  NARS.print_info('Filter name = ' + filterName);

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_Config(filterName);
  destDir = filter_config.destDir;
  thumbsSourceDir = filter_config.thumbsSourceDir;
  fanartSourceDir = filter_config.fanartSourceDir;

  # --- Check for errors, missing paths, etc...
  NARS.have_dir_or_abort(destDir);
  NARS.have_dir_or_abort(thumbsSourceDir);
  NARS.have_dir_or_abort(fanartSourceDir);

  # --- Create a list of ROMs in destDir
  roms_destDir_list = [];
  for file in os.listdir(destDir):
    if file.endswith(".zip"):
      thisFileName, thisFileExtension = os.path.splitext(file);
      roms_destDir_list.append(thisFileName);

  # --- Get MAME parent/clone dictionary --------------------------------------
  mame_xml_dic = parse_MAME_merged_XML();

  # --- Apply filter and create list of files to be copied --------------------
  mame_filtered_dic = apply_MAME_filters(mame_xml_dic, filter_config);
  rom_copy_list = create_copy_list(mame_filtered_dic, roms_destDir_list);
  
  # --- Mimic the behaviour of optimize_ArtWork_list() in xru-console
  # Crate a dictionary where key and value are the same (no artwork
  # substitution in xru-mame).
  artwork_copy_dic = {};
  for rom in rom_copy_list:
    artwork_copy_dic[rom] = rom;

  # --- Print list in alphabetical order
  NARS.print_info('[Artwork report]');
  num_original = 0;
  num_replaced = 0;
  num_have_thumbs = 0;
  num_missing_thumbs = 0;
  num_have_fanart = 0;
  num_missing_fanart = 0;
  for rom_baseName in sorted(roms_destDir_list):
    NARS.print_info("Game        " + rom_baseName + ".zip");    
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

  NARS.print_info('[Report]')
  NARS.print_info('Number of ROMs in destDir  = ' + str(len(roms_destDir_list)));
  NARS.print_info('Number of ArtWork found    = ' + str(len(artwork_copy_dic)));
  NARS.print_info('Number of original ArtWork = ' + str(num_original));
  NARS.print_info('Number of replaced ArtWork = ' + str(num_replaced));
  NARS.print_info('Number of have Thumbs    = ' + str(num_have_thumbs));
  NARS.print_info('Number of missing Thumbs = ' + str(num_missing_thumbs));
  NARS.print_info('Number of have Fanart    = ' + str(num_have_fanart));
  NARS.print_info('Number of missing Fanart = ' + str(num_missing_fanart));

# ----------------------------------------------------------------------------
def do_update_Artwork(filterName):
  "Reads ROM destDir and copies Artwork"

  NARS.print_info('[Updating/copying ArtWork]');
  NARS.print_info('Filter name = ' + filterName);

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_Config(filterName);
  destDir = filter_config.destDir;
  thumbsSourceDir = filter_config.thumbsSourceDir;
  fanartSourceDir = filter_config.fanartSourceDir;
  thumbsDestDir = filter_config.thumbsDestDir;
  fanartDestDir = filter_config.fanartDestDir;

  # --- Check for errors, missing paths, etc...
  NARS.have_dir_or_abort(destDir);
  NARS.have_dir_or_abort(thumbsSourceDir);
  NARS.have_dir_or_abort(fanartSourceDir);
  NARS.have_dir_or_abort(thumbsDestDir);
  NARS.have_dir_or_abort(fanartDestDir);

  # --- Create a list of ROMs in destDir
  roms_destDir_list = [];
  for file in os.listdir(destDir):
    if file.endswith(".zip"):
      thisFileName, thisFileExtension = os.path.splitext(file);
      roms_destDir_list.append(thisFileName);

  # --- Get MAME parent/clone dictionary --------------------------------------
  mame_xml_dic = parse_MAME_merged_XML();

  # --- Apply filter and create list of files to be copied --------------------
  mame_filtered_dic = apply_MAME_filters(mame_xml_dic, filter_config);
  rom_copy_list = create_copy_list(mame_filtered_dic, roms_destDir_list);

  # --- Mimic the behaviour of optimize_ArtWork_list() in xru-console
  # Crate a dictionary where key and value are the same (no artwork
  # substitution in xru-mame).
  artwork_copy_dic = {};
  for rom in rom_copy_list:
    artwork_copy_dic[rom] = rom;

  # --- Copy artwork    
  if __prog_option_sync:
    update_ArtWork_list(filter_config, artwork_copy_dic);
  else:
    copy_ArtWork_list(filter_config, artwork_copy_dic);

  # --- If --cleanArtWork is on then delete unknown files.
  if __prog_option_clean_ArtWork:
    clean_ArtWork_destDir(filter_config, artwork_copy_dic);

def do_printHelp():
  print("""\033[32mUsage: nars-mame.py [options] <command> [filter]\033[0m

\033[32mCommands:\033[0m
\033[31musage\033[0m                   Print usage information (this text)
\033[31mreduce-XML\033[0m              Takes MAME XML as input and writes an stripped XML.
\033[31mmerge-XML\033[0m               Takes MAME XML (reduced) info file and Catver.ini a mergued XML.
\033[31mlist-merged\033[0m             List every ROM set system in the merged MAME XML.
\033[31mlist-categories\033[0m         Reads Catver.ini and makes a histogram of the categories.
\033[31mlist-drivers\033[0m            Reads merged XML database and prints a histogram of the drivers.
\033[31mlist-controls\033[0m           Reads merged XML database and prints a histogram of the game controls.
\033[31mlist-years\033[0m              Reads merged XML database and prints a histogram of the game release year.
\033[31mlist-filters\033[0m            List filters defined in configuration file.
\033[31mcheck <filter>\033[0m          Applies filters and checks you source directory for have and missing ROMs.
\033[31mcopy <filter>\033[0m           Applies ROM filters and copies sourceDir into destDir.
\033[31mupdate <filter>\033[0m         Like copy, but only copies files if file size is different.
\033[31mcheck-chd <filter>\033[0m      Applies filters and checks you source directory for have and missing CHDs.
\033[31mcopy-chd <filter>\033[0m       WRITE ME.
\033[31mupdate-chd <filter>\033[0m     WRITE ME.
\033[31mcheck-artwork <filter>\033[0m  Checks if you have the artwork.
\033[31mcopy-artwork <filter>\033[0m   Copies artwork to destination
\033[31mupdate-artwork <filter>\033[0m Like copy-artwork, but also delete unknown images in artwork destination.

\033[32mOptions:\033[0m
\033[35m-h\033[0m, \033[35m--help\033[0m        Print short command reference
\033[35m-v\033[0m, \033[35m--verbose\033[0m     Print more information about what's going on
\033[35m-l\033[0m, \033[35m--log\033[0m         Save program output in xru-mame-log.txt.
\033[35m--logto\033[0m \033[31m[logName]\033[0m Save program output in the file you specify.
\033[35m--dryRun\033[0m          Don't modify destDir at all, just print the operations to be done.
\033[35m--cleanROMs\033[0m       Deletes ROMs in destDir not present in the filtered ROM list.
\033[35m--generateNFO\033[0m     Generates NFO files with game information for the launchers.
\033[35m--cleanNFO\033[0m        Deletes ROMs in destDir not present in the filtered ROM list.
\033[35m--cleanArtWork\033[0m    Deletes unknown Artowork in destination directories.
\033[35m--cleanCHD\033[0m        Deletes unknown CHDs in destination directory.""")

# -----------------------------------------------------------------------------
# main function
# -----------------------------------------------------------------------------
def main(argv):
  print('\033[36mNARS Advanced ROM Sorting - MAME edition\033[0m' + \
        ' version ' + NARS.__software_version)

  # --- Command line parser
  parser = argparse.ArgumentParser()
  parser.add_argument('-v', '--verbose', help="be verbose", action="count")
  parser.add_argument('-l', '--log', help="log output to default file", action='store_true')
  parser.add_argument('--logto', help="log output to specified file", nargs = 1)
  parser.add_argument('--dryRun', help="don't modify any files", action="store_true")
  parser.add_argument('--cleanROMs', help="clean destDir of unknown ROMs", action="store_true")
  parser.add_argument('--generateNFO', help="generate NFO files", action="store_true")
  parser.add_argument('--cleanNFO', help="clean redundant NFO files", action="store_true")
  parser.add_argument('--cleanArtWork', help="clean unknown ArtWork", action="store_true")
  parser.add_argument('--cleanCHD', help="clean unknown CHDs", action="store_true")
  parser.add_argument('command', \
     help="usage, reduce-XML, merge, list-merged, \
           list-categories, list-drivers, list-controls, list-years,\
           list-filters, check, copy, update \
           check-chd, copy-chd, update-chd \
           check-artwork, copy-artwork, update-artwork", nargs = 1)
  parser.add_argument("filterName", help="MAME ROM filter name", nargs = '?')
  args = parser.parse_args();

  # --- Optional arguments
  global __prog_option_log, __prog_option_log_filename;
  global __prog_option_dry_run;
  global __prog_option_clean_ROMs;
  global __prog_option_generate_NFO;
  global __prog_option_clean_NFO;
  global __prog_option_clean_ArtWork;
  global __prog_option_clean_CHD;
  global __prog_option_sync;

  if args.verbose:
    if args.verbose == 1:   NARS.change_log_level(NARS.Log.verb);
    elif args.verbose == 2: NARS.change_log_level(NARS.Log.vverb);
    elif args.verbose >= 3: NARS.change_log_level(NARS.Log.debug);
  if args.log:
    __prog_option_log = 1;
  if args.logto:
    __prog_option_log = 1;
    __prog_option_log_filename = args.logto[0];
  if args.dryRun:       __prog_option_dry_run = 1;
  if args.cleanROMs:    __prog_option_clean_ROMs = 1;
  if args.generateNFO:  __prog_option_generate_NFO = 1;
  if args.cleanNFO:     __prog_option_clean_NFO = 1;
  if args.cleanArtWork: __prog_option_clean_ArtWork = 1;
  if args.cleanCHD:     __prog_option_clean_CHD = 1;

  # --- Positional arguments that don't require parsing of the config file
  command = args.command[0];
  if command == 'usage':
    do_printHelp();
    sys.exit(0);

  # --- Read configuration file
  global configuration; # Needed to modify global copy of globvar
  configuration = parse_File_Config();

  # --- Positional arguments that don't require a filterName
  if command == 'reduce-XML':
    do_reduce_XML()

  elif command == 'merge-XML':
    do_merge()

  elif command == 'list-merged':
    do_list_merged()

  elif command == 'list-categories':
    do_list_categories()

  elif command == 'list-drivers':
    do_list_drivers();

  elif command == 'list-controls':
    do_list_controls();

  elif command == 'list-years':
    do_list_years();

  elif command == 'list-filters':
    do_list_filters()

  elif command == 'check':
    if args.filterName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m filterName required')
      sys.exit(10)
    do_checkFilter(args.filterName)

  elif command == 'copy':
    if args.filterName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m filterName required')
      sys.exit(10)
    do_update(args.filterName)

  elif command == 'update':
    if args.filterName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m filterName required')
      sys.exit(10)
    __prog_option_sync = 1
    do_update(args.filterName); 

  elif command == 'check-chd':
    if args.filterName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m filterName required')
      sys.exit(10)
    do_check_CHD(args.filterName)

  elif command == 'copy-chd':
    if args.filterName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m filterName required')
      sys.exit(10)
    do_update_CHD(args.filterName)

  elif command == 'update-chd':
    if args.filterName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m filterName required')
      sys.exit(10)
    __prog_option_sync = 1
    do_update_CHD(args.filterName)

  elif command == 'check-artwork':
    if args.filterName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m filterName required')
      sys.exit(10)
    do_check_Artwork(args.filterName)

  elif command == 'copy-artwork':
    if args.filterName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m filterName required')
      sys.exit(10)
    do_update_Artwork(args.filterName)

  elif command == 'update-artwork':
    if args.filterName == None:
      NARS.print_error('\033[31m[ERROR]\033[0m filterName required')
      sys.exit(10)
    __prog_option_sync = 1
    do_update_Artwork(args.filterName)

  else:
    NARS.print_error('Unrecognised command: ' + command)
    sys.exit(1)

  sys.exit(0)

# Execute main function if script called from command line (not imported 
# as module)
if __name__ == "__main__":
  main(sys.argv[1:])
