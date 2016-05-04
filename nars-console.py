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
__config_configFileName = 'nars-console-config.xml'
__config_logFileName = 'nars-console-log.txt'

# --- Program options (from command line) ---
__prog_option_log = 0
__prog_option_log_filename = __config_logFileName
__prog_option_dry_run = 0
__prog_option_clean_ROMs = 0
__prog_option_clean_NFOs = 0
__prog_option_clean_ArtWork = 0
__prog_option_sync = 0

# -----------------------------------------------------------------------------
# Configuration file stuff
# -----------------------------------------------------------------------------
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
    self.sourceDir       = None  # str
    self.destDir         = None  # str
    self.NoIntro_XML     = None  # str
    self.option_NoBIOS   = False # bool
    self.fanartSourceDir = None  # str
    self.fanartDestDir   = None  # str
    self.thumbsSourceDir = None  # str
    self.thumbsDestDir   = None  # str
    self.filterUpTags    = None  # str list
    self.filterDownTags  = None  # str list
    self.includeTags     = None  # str list
    self.excludeTags     = None  # str list

# Parses configuration file using ElementTree
# Returns a ConfigFile object
parse_rjust = 16
def parse_File_Config():
  NARS.print_info('\033[1m[Parsing config file]\033[0m')
  tree = NARS.XML_read_file_ElementTree(__config_configFileName, "Reading configuration XML file")
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
          if filter_child.text is None: continue
          filter_class.sourceDir = NARS.sanitize_dir_name(NARS.strip_string(filter_child.text))
          NARS.print_debug('ROMsSource'.ljust(parse_rjust) + filter_class.sourceDir)
        elif filter_child.tag == 'ROMsDest':
          if filter_child.text is None: continue
          filter_class.destDir = NARS.sanitize_dir_name(NARS.strip_string(filter_child.text)) 
          NARS.print_debug('ROMsDest'.ljust(parse_rjust) + filter_class.destDir)          
        elif filter_child.tag == 'FanartSource':
          if filter_child.text is None: continue
          filter_class.fanartSourceDir = NARS.sanitize_dir_name(NARS.strip_string(filter_child.text))
          NARS.print_debug('FanartSource'.ljust(parse_rjust) + filter_class.fanartSourceDir)
        elif filter_child.tag == 'FanartDest':
          if filter_child.text is None: continue
          filter_class.fanartDestDir = NARS.sanitize_dir_name(NARS.strip_string(filter_child.text))
          NARS.print_debug('FanartDest'.ljust(parse_rjust) + filter_class.fanartDestDir)
        elif filter_child.tag == 'ThumbsSource':
          if filter_child.text is None: continue
          filter_class.thumbsSourceDir = NARS.sanitize_dir_name(NARS.strip_string(filter_child.text))
          NARS.print_debug('ThumbsSource'.ljust(parse_rjust) + filter_class.thumbsSourceDir)
        elif filter_child.tag == 'ThumbsDest':
          if filter_child.text is None: continue
          filter_class.thumbsDestDir = NARS.sanitize_dir_name(NARS.strip_string(filter_child.text))
          NARS.print_debug('ThumbsDest'.ljust(parse_rjust) + filter_class.thumbsDestDir)

        # ~~~ Files ~~~
        elif filter_child.tag == 'NoIntroDat':
          if filter_child.text is None: continue
          filter_class.NoIntro_XML = NARS.strip_string(filter_child.text)
          NARS.print_debug('NoIntroDat'.ljust(parse_rjust) + filter_class.NoIntro_XML)

        # ~~~ Options ~~~
        elif filter_child.tag == 'Options':
          if filter_child.text is None: continue
          # Trim comma-separated string, then trim each element after splitting
          str = NARS.strip_string(filter_child.text)
          str_list = str.split(",")
          for index, item in enumerate(str_list):
            str_list[index] = NARS.strip_string(item)
          NARS.print_debug('Options'.ljust(parse_rjust) + ', '.join(str_list))

          # Parse each option individually
          for index, item in enumerate(str_list):
            if str_list[index] == 'NoBIOS':
              filter_class.option_NoBIOS = True
            else:
              print('[ERROR] On <collection> \'{0}\' in configuration file'.format(filter_class.name))
              print('[ERROR] On tag <{0}>'.format(filter_child.tag))
              print('[ERROR] Unrecognised option \'{0}\''.format(str_list[index]))
              sys.exit(10)

        # ~~~ Comma separated strings ~~~
        elif filter_child.tag == 'filterUpTags':
          # If string is None then continue
          if filter_child.text is None: continue
          # Trim comma-separated string
          str = NARS.strip_string(filter_child.text)
          # Trim each list element separately
          str_list = str.split(",")
          for index, item in enumerate(str_list):
            str_list[index] = NARS.strip_string(item)
          filter_class.filterUpTags = str_list
          NARS.print_debug('filterUpTags'.ljust(parse_rjust) + ', '.join(str_list))
        elif filter_child.tag == 'filterDownTags':
          if filter_child.text is None: continue
          str = NARS.strip_string(filter_child.text)
          str_list = str.split(",")
          for index, item in enumerate(str_list):
            str_list[index] = NARS.strip_string(item)
          filter_class.filterDownTags = str_list
          NARS.print_debug('filterDownTags'.ljust(parse_rjust) + ', '.join(str_list))
        elif filter_child.tag == 'includeTags':
          if filter_child.text is None: continue
          str = NARS.strip_string(filter_child.text)
          str_list = str.split(",")
          for index, item in enumerate(str_list):
            str_list[index] = NARS.strip_string(item)
          filter_class.includeTags = str_list
          NARS.print_debug('includeTags'.ljust(parse_rjust) + ', '.join(str_list))
        elif filter_child.tag == 'excludeTags':
          if filter_child.text is None: continue
          str = NARS.strip_string(filter_child.text)
          str_list = str.split(",")
          for index, item in enumerate(str_list):
            str_list[index] = NARS.strip_string(item)
          filter_class.excludeTags = str_list
          NARS.print_debug('excludeTags'.ljust(parse_rjust) + ', '.join(str_list))
          

        else:
          print('[ERROR] On <collection> \'{0}\' in configuration file'.format(filter_class.name))
          print('[ERROR] Unrecognised tag <{0}>'.format(filter_child.tag))
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
  sourceFullFilename = sourceDir + artName + '.png'
  destFullFilename = destDir + fileName + '.png'

  # Maybe artwork does not exist... Then do nothing
  if not os.path.isfile(sourceFullFilename):
    return 1

  NARS.print_debug('Copying ' + sourceFullFilename)
  NARS.print_debug('Into    ' + destFullFilename)
  if not __prog_option_dry_run:
    try:
      shutil.copy(sourceFullFilename, destFullFilename)
    except EnvironmentError:
      NARS.print_debug("copy_ArtWork_file >> Error happened")

  return 0

# Returns:
#  0 - ArtWork file found in sourceDir and copied
#  1 - ArtWork file not found in sourceDir
#  2 - ArtWork file found in sourceDir and destDir, same size so not copied
# NOTE: be careful, maybe artwork should be when copied to match ROM name
#       if artwork was subtituted.
def update_ArtWork_file(fileName, artName, sourceDir, destDir):
  sourceFullFilename = sourceDir + artName + '.png'
  destFullFilename = destDir + fileName + '.png'
  
  existsSource = os.path.isfile(sourceFullFilename)
  existsDest = os.path.isfile(destFullFilename)
  # --- Maybe artwork does not exist... Then do nothing
  if not os.path.isfile(sourceFullFilename):
    return 1

  sizeSource = os.path.getsize(sourceFullFilename)
  if existsDest:
    sizeDest = os.path.getsize(destFullFilename)
  else:
    sizeDest = -1

  # If sizes are equal Skip copy and return 1
  if sizeSource == sizeDest:
    NARS.print_debug('Updated ' + destFullFilename)
    return 2

  # destFile does not exist or sizes are different, copy.
  NARS.print_debug('Copying ' + sourceFullFilename)
  NARS.print_debug('Into    ' + destFullFilename)
  if not __prog_option_dry_run:
    try:
      shutil.copy(sourceFullFilename, destFullFilename)
    except EnvironmentError:
      NARS.print_debug("update_ArtWork_file >> Error happened")

  return 0

# -----------------------------------------------------------------------------
def copy_ROM_list(rom_list, sourceDir, destDir):
  NARS.print_info('[Copying ROMs into destDir]')

  num_steps = len(rom_list)
  # 0 here prints [0, ..., 99%] instead [1, ..., 100%]
  step = 0
  num_files = 0
  num_copied_roms = 0
  for rom_copy_item in sorted(rom_list):
    # --- Update progress
    percentage = 100 * step / num_steps
    sys.stdout.write('{:5.2f}% '.format(percentage))

    # --- Copy file (this function succeeds or aborts program)
    romFileName = rom_copy_item + '.zip'
    source_path = sourceDir + romFileName
    dest_path = destDir + romFileName
    NARS.copy_file(source_path, dest_path, __prog_option_dry_run)
    num_copied_roms += 1
    NARS.print_info('<Copied> ' + romFileName)
    sys.stdout.flush()

    # --- Update progress
    step += 1

  NARS.print_info('[Report]')
  NARS.print_info('Copied ROMs ' + '{:6d}'.format(num_copied_roms))

def update_ROM_list(rom_list, sourceDir, destDir):
  NARS.print_info('[Updating ROMs into destDir]')
  
  num_steps = len(rom_list)
  # 0 here prints [0, ..., 99%] instead [1, ..., 100%]
  step = 0
  num_copied_roms = 0
  num_updated_roms = 0
  for rom_copy_item in sorted(rom_list):
    # --- Update progress
    percentage = 100 * step / num_steps

    # --- Copy file (this function succeeds or aborts program)
    romFileName = rom_copy_item + '.zip'
    source_path = sourceDir + romFileName
    dest_path = destDir + romFileName
    ret = NARS.update_file(source_path, dest_path, __prog_option_dry_run)
    if ret == 0:
      # On default verbosity level only report copied files
      sys.stdout.write('{:5.2f}% '.format(percentage))
      num_copied_roms += 1
      NARS.print_info('<Copied > ' + romFileName)
    elif ret == 1:
      if NARS.log_level >= NARS.Log.verb:
        sys.stdout.write('{:5.2f}% '.format(percentage))
      num_updated_roms += 1
      NARS.print_info('<Miss   > ' + romFileName)
    elif ret == 2:
      if NARS.log_level >= NARS.Log.verb:
        sys.stdout.write('{:5.2f}% '.format(percentage))
      num_updated_roms += 1
      NARS.print_verb('<Updated> ' + romFileName)
    elif ret == -1:
      if NARS.log_level >= NARS.Log.verb:
        sys.stdout.write('{:5.2f}% '.format(percentage))
      num_updated_roms += 1
      NARS.print_info('<ERROR  > ' + romFileName)
    else:
      NARS.print_error('[ERROR] update_ROM_list: Wrong value returned by NARS.update_file()')
      sys.exit(10)
    sys.stdout.flush()

    # --- Update progress
    step += 1

  NARS.print_info('[Report]')
  NARS.print_info('Copied ROMs ' + '{:6d}'.format(num_copied_roms))
  NARS.print_info('Updated ROMs ' + '{:5d}'.format(num_updated_roms))

def clean_ROMs_destDir(destDir, rom_copy_dic):
  NARS.print_info('[Cleaning ROMs in ROMsDest]')

  # --- Delete ROMs present in destDir not present in the filtered list
  rom_main_list = []
  for file in os.listdir(destDir):
    if file.endswith(".zip"):
      rom_main_list.append(file)

  num_cleaned_roms = 0
  for file in sorted(rom_main_list):
    basename, ext = os.path.splitext(file) # Remove extension
    if basename not in rom_copy_dic:
      fileName = destDir + file
      NARS.delete_file(fileName, __prog_option_dry_run)
      num_cleaned_roms += 1
      NARS.print_info('<Deleted> ' + file)

  NARS.print_info('Deleted ' + str(num_cleaned_roms) + ' redundant ROMs')

__debug_delete_redundant_NFO = 0
def delete_redundant_NFO(destDir):
  NARS.print_info('[Deleting redundant NFO files]')
  num_deletedNFO_files = 0
  for file in os.listdir(destDir):
    if file.endswith(".nfo"):
      # Chech if there is a corresponding ROM for this NFO file
      thisFileName, thisFileExtension = os.path.splitext(file)
      romFileName_temp = destDir + thisFileName + '.zip'
      if not os.path.isfile(romFileName_temp):
        if __debug_delete_redundant_NFO:
          print('MISSING \'{0}\''.format(romFileName_temp))
        fileName = destDir + file
        NARS.delete_file(fileName, __prog_option_dry_run)
        num_deletedNFO_files += 1
        NARS.print_info('<Deleted NFO> ' + file)
      else:
        if __debug_delete_redundant_NFO:
          print('EXISTS  \'{0}\''.format(romFileName_temp))
  NARS.print_info('Deleted ' + str(num_deletedNFO_files) + ' redundant NFO files')

def copy_ArtWork_files(filter_config, artwork_copy_dic):
  NARS.print_info('[Copying ArtWork]')
  
  # --- Check that directories exist
  fanartSourceDir = filter_config.fanartSourceDir
  fanartDestDir = filter_config.fanartDestDir
  thumbsSourceDir = filter_config.thumbsSourceDir
  thumbsDestDir = filter_config.thumbsDestDir
  NARS.have_dir_or_abort(thumbsSourceDir, 'thumbsSourceDir')
  NARS.have_dir_or_abort(thumbsDestDir, 'thumbsDestDir')
  NARS.have_dir_or_abort(fanartSourceDir, 'fanartSourceDir')
  NARS.have_dir_or_abort(fanartDestDir, 'fanartDestDir')
  
  # --- Copy artwork
  num_steps = len(artwork_copy_dic)
  step = 0
  num_copied_thumbs = 0
  num_missing_thumbs = 0
  num_copied_fanart = 0
  num_missing_fanart = 0
  for rom_baseName in sorted(artwork_copy_dic):
    # --- Update progress ---
    percentage = 100 * step / num_steps

    # --- Thumbs ---
    art_baseName = artwork_copy_dic[rom_baseName]['thumb']
    if art_baseName is not None:
      ret = copy_ArtWork_file(rom_baseName, art_baseName, thumbsSourceDir, thumbsDestDir)
      if ret == 0:
        sys.stdout.write('{:5.2f}% '.format(percentage))
        num_copied_thumbs += 1
        NARS.print_info('<Copied Thumb  > ' + art_baseName)
      elif ret == 1:
        sys.stdout.write('{:5.2f}% '.format(percentage))
        num_missing_thumbs += 1
        NARS.print_info('<Missing Thumb > ' + art_baseName)
      else:
        NARS.print_error('Wrong value returned by copy_ArtWork_file()')
        sys.exit(10)

    # --- Update progress ---
    percentage = 100 * step / num_steps

    # --- Fanart ---
    art_baseName = artwork_copy_dic[rom_baseName]['fanart']
    if art_baseName is not None:
      ret = copy_ArtWork_file(rom_baseName, art_baseName, fanartSourceDir, fanartDestDir)
      if ret == 0:
        sys.stdout.write('{:5.2f}% '.format(percentage))
        num_copied_fanart += 1
        NARS.print_info('<Copied Fanart > ' + art_baseName)
      elif ret == 1:
        sys.stdout.write('{:5.2f}% '.format(percentage))
        num_missing_fanart += 1
        NARS.print_info('<Missing Fanart> ' + art_baseName)
      else:
        print_error('Wrong value returned by copy_ArtWork_file()')
        sys.exit(10)

    # --- Update progress ---
    step += 1

  NARS.print_info('[Report]')
  NARS.print_info('Copied thumbs   {:5d}'.format(num_copied_thumbs))
  NARS.print_info('Missing thumbs  {:5d}'.format(num_missing_thumbs))
  NARS.print_info('Copied fanart   {:5d}'.format(num_copied_fanart))
  NARS.print_info('Missing fanart  {:5d}'.format(num_missing_fanart))

def update_ArtWork_files(filter_config, artwork_copy_dic):
  NARS.print_info('[Updating ArtWork]')
  
  # --- Check that directories exist ---
  thumbsSourceDir = filter_config.thumbsSourceDir
  thumbsDestDir = filter_config.thumbsDestDir
  fanartSourceDir = filter_config.fanartSourceDir
  fanartDestDir = filter_config.fanartDestDir
  NARS.have_dir_or_abort(thumbsSourceDir, 'thumbsSourceDir')
  NARS.have_dir_or_abort(thumbsDestDir, 'thumbsDestDir')
  NARS.have_dir_or_abort(fanartSourceDir, 'fanartSourceDir')
  NARS.have_dir_or_abort(fanartDestDir, 'fanartDestDir')
  
  # --- Copy/update artwork ---
  num_steps = len(artwork_copy_dic)
  step = 0
  num_copied_thumbs = 0
  num_updated_thumbs = 0
  num_missing_thumbs = 0
  num_copied_fanart = 0
  num_updated_fanart = 0
  num_missing_fanart = 0
  for rom_baseName in sorted(artwork_copy_dic):
    # --- Update progress ---
    percentage = 100 * step / num_steps

    # --- Thumbs ---
    art_baseName = artwork_copy_dic[rom_baseName]['thumb']
    if art_baseName is not None:
      ret = update_ArtWork_file(rom_baseName, art_baseName, thumbsSourceDir, thumbsDestDir)
      if ret == 0:
        # On default verbosity level only report copied files
        sys.stdout.write('{:5.2f}% '.format(percentage))
        num_copied_thumbs += 1
        NARS.print_info('<Copied  Thumb > {0} ---> {1}'.format(art_baseName, rom_baseName))
      elif ret == 1:
        # Also report missing artwork
        sys.stdout.write('{:5.2f}% '.format(percentage))
        num_missing_thumbs += 1
        NARS.print_info('<Missing Thumb > {0} ---> {1}'.format(art_baseName, rom_baseName))
      elif ret == 2:
        if NARS.log_level >= NARS.Log.verb:
          sys.stdout.write('{:5.2f}% '.format(percentage))
        num_updated_thumbs += 1
        NARS.print_verb('<Updated Thumb > {0} ---> {1}'.format(art_baseName, rom_baseName))
      else:
        print_error('Wrong value returned by copy_ArtWork_file()')
        sys.exit(10)

    # --- Fanart ---
    art_baseName = artwork_copy_dic[rom_baseName]['fanart']
    if art_baseName is not None:
      ret = update_ArtWork_file(rom_baseName, art_baseName, fanartSourceDir, fanartDestDir)
      if ret == 0:
        # Also report missing artwork
        sys.stdout.write('{:5.2f}% '.format(percentage))
        num_copied_fanart += 1
        NARS.print_info('<Copied  Fanart> {0} ---> {1}'.format(art_baseName, rom_baseName))
      elif ret == 1:
        # Also report missing artwork
        sys.stdout.write('{:5.2f}% '.format(percentage))
        num_missing_fanart += 1
        NARS.print_info('<Missing Fanart> {0} ---> {1}'.format(art_baseName, rom_baseName))
      elif ret == 2:
        if NARS.log_level >= NARS.Log.verb:
          sys.stdout.write('{:5.2f}% '.format(percentage))
        num_updated_fanart += 1
        NARS.print_verb('<Updated Fanart> {0} ---> {1}'.format(art_baseName, rom_baseName))
      else:
        print_error('Wrong value returned by copy_ArtWork_file()')
        sys.exit(10)

    # --- Update progress
    step += 1

  NARS.print_info('[Report]')
  NARS.print_info('Copied thumbs   {:5d}'.format(num_copied_thumbs))
  NARS.print_info('Updated thumbs  {:5d}'.format(num_updated_thumbs))
  NARS.print_info('Missing thumbs  {:5d}'.format(num_missing_thumbs))
  NARS.print_info('Copied fanart   {:5d}'.format(num_copied_fanart))
  NARS.print_info('Updated fanart  {:5d}'.format(num_updated_fanart))
  NARS.print_info('Missing fanart  {:5d}'.format(num_missing_fanart))

# Artwork may be available for some of the parent/clones in the ROM set, but
# not for the filtered ROMs. This function test against alll
#
# Inputs:
# roms_destDir_list list of ROM Base Name in destDir (no extension, no path)
# romMainList_list  list of ROM Base Name (no extension, no path)
#
# Returns a dictionary
#  artwork_copy_dic = { 'romName' : { 'thumb' : 'fileBaseName', 'fanart' : 'fileBaseName'}, ... }
#  romName -> string, ROM filename in destDir with no extension
#  value   -> dictonary having the
#
# The name of the artwork may be different for thumbs an fanarts.
# Checking if artwork was replaced is easy: 
#   if romName is     equal to fileBaseName, it is original artwork.
#   if romName is not equal to fileBaseName, it is substituted artwork.
def optimize_ArtWork_list(roms_destDir_list, romMainList_list, filter_config):
  __debug_optimize_ArtWork = 0

  NARS.print_info('[Optimising ArtWork file list]')
  thumbsSourceDir = filter_config.thumbsSourceDir
  thumbsDestDir   = filter_config.thumbsDestDir
  fanartSourceDir = filter_config.fanartSourceDir
  fanartDestDir   = filter_config.fanartDestDir

  # --- Check that directories exist ---
  if not os.path.isdir(thumbsSourceDir):
    NARS.print_error('thumbsSourceDir not found ' + thumbsSourceDir)
    sys.exit(10)
  if not os.path.isdir(thumbsDestDir):
    NARS.print_error('thumbsDestDir not found ' + thumbsDestDir)
    sys.exit(10)
  if not os.path.isdir(fanartSourceDir):
    NARS.print_error('fanartSourceDir not found ' + fanartSourceDir)
    sys.exit(10)
  if not os.path.isdir(fanartDestDir):
    NARS.print_error('fanartDestDir not found ' + fanartDestDir)
    sys.exit(10)

  # - For every ROM to be copied (filtered) check if ArtWork exists. If not,
  #   try artwork of other ROMs in the parent/clone set.
  artwork_copy_dic = {}
  for rom_copy_item in sorted(roms_destDir_list):
    artworkBaseName = rom_copy_item
    ROMFullName = rom_copy_item + '.zip'
    artwork_copy_dic[rom_copy_item] = { 'thumb': None, 'fanart' : None}
    if __debug_optimize_ArtWork: 
      print('{{Testing ROM}} {0}'.format(ROMFullName))
    
    # --- Check Thumbs ---
    # First check if we have the original artwork
    thumbPath = thumbsSourceDir + artworkBaseName + '.png'
    if __debug_optimize_ArtWork: print('Testing original    thumb  {0}'.format(thumbPath))
    if os.path.isfile(thumbPath):
      if __debug_optimize_ArtWork: print('Found   original    thumb  {0}'.format(thumbPath))
      artwork_copy_dic[rom_copy_item]['thumb'] = rom_copy_item
    else:
      # If not found walk through the pclone list
      # Locate in which pClone object set the destDir ROM is
      file = rom_copy_item + '.zip'
      pclone_list = []
      for pclone_obj in romMainList_list:
        if file in pclone_obj.filenames:
          pclone_list = pclone_obj.filenames
          break
      if len(pclone_list) == 0:
        NARS.print_error('Logical error')
        sys.exit(10)
      # Check if artwork exists for every from of this set
      for pclone_rom_full_name in pclone_list:
        pclone_rom_base_name, ext = os.path.splitext(pclone_rom_full_name)
        thumbPath = thumbsSourceDir + pclone_rom_base_name + '.png'
        if __debug_optimize_ArtWork: print('Testing substituted thumb  {0}'.format(thumbPath))
        if os.path.isfile(thumbPath):
          if __debug_optimize_ArtWork: print('Found   substituted thumb  {0}'.format(thumbPath))
          artwork_copy_dic[rom_copy_item]['thumb'] = pclone_rom_base_name
          break

    # --- Check Fanart ---
    # First check if we have the original artwork
    thumbPath = fanartSourceDir + artworkBaseName + '.png'
    if __debug_optimize_ArtWork: print('Testing original    fanart {0}'.format(thumbPath))
    if os.path.isfile(thumbPath):
      if __debug_optimize_ArtWork: print('Found   original    fanart {0}'.format(thumbPath))
      artwork_copy_dic[rom_copy_item]['fanart'] = rom_copy_item
    else:
      # If not found walk through the pclone list
      # Locate in which pClone object set the destDir ROM is
      file = rom_copy_item + '.zip'
      pclone_list = []
      for pclone_obj in romMainList_list:
        if file in pclone_obj.filenames:
          pclone_list = pclone_obj.filenames
          break
      if len(pclone_list) == 0:
        print_error('Logical error')
        sys.exit(10)
      # Check if artwork exists for every from of this set
      for pclone_rom_full_name in pclone_list:
        pclone_rom_base_name, ext = os.path.splitext(pclone_rom_full_name)
        thumbPath = fanartSourceDir + pclone_rom_base_name + '.png'
        if __debug_optimize_ArtWork: print('Testing substituted fanart {0}'.format(thumbPath))
        if os.path.isfile(thumbPath):
          if __debug_optimize_ArtWork: print('Found   substituted fanart {0}'.format(thumbPath))
          artwork_copy_dic[rom_copy_item]['fanart'] = pclone_rom_base_name
          break

  return artwork_copy_dic

def clean_ArtWork_destDir(filter_config, artwork_copy_dic):
  NARS.print_info('[Cleaning ArtWork]')

  thumbsDestDir = filter_config.thumbsDestDir
  fanartDestDir = filter_config.fanartDestDir
  
  # --- Check that directories exist
  NARS.have_dir_or_abort(thumbsDestDir, 'thumbsDestDir')
  NARS.have_dir_or_abort(fanartDestDir, 'fanartDestDir')

  # --- Delete unknown thumb ---
  thumbs_file_list = []
  for file in os.listdir(thumbsDestDir):
    if file.endswith(".png"):
      thumbs_file_list.append(file)

  num_cleaned_thumbs = 0
  for file in sorted(thumbs_file_list):
    art_baseName, ext = os.path.splitext(file) # Remove extension
    if art_baseName not in artwork_copy_dic:
      num_cleaned_thumbs += 1
      fileName = thumbsDestDir + file
      NARS.delete_file(fileName, __prog_option_dry_run)
      NARS.print_info('<Deleted thumb > ' + file)

  # --- Delete unknown fanart ---
  fanart_file_list = []
  for file in os.listdir(fanartDestDir):
    if file.endswith(".png"):
      fanart_file_list.append(file)

  num_cleaned_fanart = 0
  for file in sorted(fanart_file_list):
    art_baseName, ext = os.path.splitext(file) # Remove extension
    if art_baseName not in artwork_copy_dic:
      num_cleaned_fanart += 1
      fileName = fanartDestDir + file
      NARS.delete_file(fileName, __prog_option_dry_run)
      NARS.print_info(' <Deleted fanart> ' + file)

  # --- Report
  NARS.print_info('Deleted ' + str(num_cleaned_thumbs) + ' redundant thumbs')
  NARS.print_info('Deleted ' + str(num_cleaned_fanart) + ' redundant fanart')

#
# Creates the list of ROMs to be copied based on the ordered main ROM list
#
def create_copy_list(romMain_list, filter_config):
  # --- Scan sourceDir to get the list of available ROMs ---
  NARS.print_info('[Scanning sourceDir for ROMs to be copied]')
  sourceDir = filter_config.sourceDir
  sourceDir_rom_list = []
  for file in os.listdir(sourceDir):
    if file.endswith(".zip"):
      sourceDir_rom_list.append(file)

  # For each parent/clone list, pick the first available ROM in sourceDir
  # (if not excluded) to be copied.
  NARS.print_info('[Creating list of ROMs to be copied/updated]')
  rom_copy_list = []
  for mainROM_obj in romMain_list:
    num_pclone_set_files = len(mainROM_obj.filenames)
    for index in range(num_pclone_set_files):
      filename    = mainROM_obj.filenames[index]
      includeFlag = mainROM_obj.include[index]
      if filename in sourceDir_rom_list and includeFlag:
        # If option NoBIOS is ON and the ROM name starts with '[BIOS]' then skip it
        if filter_config.option_NoBIOS and re.search('^\[BIOS\]', filename):
          NARS.print_debug('NoBIOS is ON. Skipping ROM \'{0}\''.format(filename))
          continue

        # Only pick one ROM of the pclone list
        rom_copy_list.append(filename)
        break

  # --- Sort list alphabetically ---
  rom_copy_list_sorted = sorted(rom_copy_list)

  # --- Remove extension of ROM files ---
  rom_copy_list_sorted_basename = []
  for s in rom_copy_list_sorted:
    (name, extension) = os.path.splitext(s)
    rom_copy_list_sorted_basename.append(name)

  return rom_copy_list_sorted_basename

# -----------------------------------------------------------------------------
# Miscellaneous ROM functions
# -----------------------------------------------------------------------------
# Object to store a Parent/Clone ROM set
class PClone:
  pass

class NoIntro_ROM:
  def __init__(self, baseName):
    self.baseName = baseName

class dir_ROM:
  def __init__(self, fileName):
    self.fileName = fileName

def extract_ROM_Properties_Raw(romFileName):
  """Given a ROM file name extracts all the tags and returns a list"""
  __debug_propertyParsers = 0

  romProperties_raw = []
  romProperties_raw = re.findall("(\([^\(]*\))", romFileName)

  # Debug print
  if __debug_propertyParsers:
    print('extract_ROM_Properties_Raw >> Property list')
    print('\n'.join(romProperties_raw))
    print('\n')
  
  return romProperties_raw

def extract_ROM_Tags_All(romFileName):
  """Given a ROM file name extracts all the tags and returns a list. Also parses tags"""
  __debug_propertyParsers = 0

  # Extract Raw properties with parenthesis
  romProperties_raw = []
  romProperties_raw = re.findall("(\([^\(]*\))", romFileName)

  # For every property chech if it has comma(s). If so, reparse the
  # property and create new properties
  romProperties_all = []
  for property in romProperties_raw:
    # Strip parentehsis
    property = property[1:-1]
    if __debug_propertyParsers:
      print('extract_ROM_Properties_All >> Property: ' + property)
    
    match = re.search(",", property)
    if match:
      # Re-parse the string and decompose into new properties
      subProperties = re.findall("([^\,]*)", property)
      for subPropertie in subProperties:
        if __debug_propertyParsers:
          print('extract_ROM_Properties_All >> subProperty: "' + subPropertie + '"')
        # For some reason, this regular expression search returns the matches and
        # also one empty string afterwards...
        # Non empty strings are "true", empty are "false"
        if subPropertie:
          # strip() is equivalent to Perl trim()
          subPropertieOK = subPropertie.strip()
          romProperties_all.append(subPropertieOK)
          if __debug_propertyParsers:
            print('extract_ROM_Properties_All >> Added subProperty: "' + subPropertieOK + '"')
    else:
      romProperties_all.append(property)

  # Debug print
  if __debug_propertyParsers:
    print('extract_ROM_Properties_All >> Property list')
    print('\n'.join(romProperties_all))
    print('\n')
  
  return romProperties_all

def get_ROM_baseName(romFileName):
  """Get baseName from filename (no extension, no tags)"""
  
  regSearch = re.search("[^\(\)]*", romFileName)
  if regSearch is None:
    print('Logical error')
    sys.exit(10)
  regExp_result = regSearch.group()
  
  return regExp_result.strip()

# Given a list of upTags and downTags, numerically score a ROM
# NOTE Either upTag_list or downTag_list may be None (user didn't configure them)
#
# Returns the score [int]
def scoreROM(romTags, upTag_list, downTag_list):
  score = 0

  # Iterate through the tags, and add/subtract points depending on the list
  # of given tags.
  for tag in romTags:
    # ~~~ Up tags increase score ~~~
    if upTag_list is not None:
      # Tags defined first have more score
      tag_score = len(upTag_list)
      for upTag in upTag_list:
        if tag == upTag:
          score += tag_score
        tag_score -= 1

    # ~~~ Down tags decrease the score ~~~
    if downTag_list is not None:
      tag_score = len(downTag_list)
      for downTag in downTag_list:
        if tag == downTag:
          score -= tag_score
        tag_score -= 1

  return score

def isTag(tags, tag_list):
  result = 0

  for tag in tags:
    for testTag in tag_list:
      if tag == testTag:
        result = 1
        return result

  return result

# Extracts tags from filenames and creates a dictionary with them.
#
# Returns a dictionary rom_Tag_dic:
# key   ROM filename 'Super Mario (World) (Rev 1).zip'
# value list of tags ['World', 'Rev 1']
def get_Tag_dic(romMainList_list):
  rom_Tag_dic = {}
  for item in romMainList_list:
    filenames_list = item.filenames
    for filename in filenames_list:
      rom_Tag_dic[filename] = extract_ROM_Tags_All(filename)

  return rom_Tag_dic

# -----------------------------------------------------------------------------
# Main filtering functions
# -----------------------------------------------------------------------------
# Parses a No-Intro XML parent-clone DAT file. Then, it creates a ROM main
# dictionary. The first game in the list PClone.filenames is the parent game
# according to the DAT file, and the rest are the clones in no particular order.
#
# Returns,
#  romMainList = [PClone, PClone, PClone, ...]
#
# PClone object,
#  PClone.filenames  [str list] full game filename (with extension). First one is the parent.
#
def get_NoIntro_Main_PClone_list(filter_config):
  __debug_parse_NoIntro_XML_Config = 0
  
  XML_filename = filter_config.NoIntro_XML
  tree = NARS.XML_read_file_ElementTree(XML_filename, 'Parsing No-Intro XML DAT')

  # --- Raw list: literal information from the XML
  rom_raw_dict = {} # Key is ROM baseName
  root = tree.getroot()
  num_games = 0
  num_parents = 0
  num_clones = 0
  for game_EL in root:
    if game_EL.tag == 'game':
      num_games += 1

      # --- Game attributes ---
      game_attrib = game_EL.attrib
      romName = game_attrib['name']
      romObject = NoIntro_ROM(romName)
      if __debug_parse_NoIntro_XML_Config:
        print('Game     {0}'.format(romName))

      if 'cloneof' in game_attrib:
        num_clones += 1
        romObject.cloneof = game_attrib['cloneof']
        romObject.isclone = 1
        if __debug_parse_NoIntro_XML_Config:
          print('Clone of {0}'.format(game_attrib['cloneof']))
      else:
        num_parents += 1
        romObject.isclone = 0

      # --- Add new game to the list ---
      rom_raw_dict[romName] = romObject
  del tree
  NARS.print_info('Total number of games {:5d}'.format(num_games))
  NARS.print_info('Number of parents     {:5d}'.format(num_parents))
  NARS.print_info('Number of clones      {:5d}'.format(num_clones))

  # --- Create a parent-clone list ---
  rom_pclone_dict = {}
  # Naive algorithm, two passes.
  # First traverse the raw list and make a list of parent games
  for key in rom_raw_dict:
    gameObj = rom_raw_dict[key]
    if not gameObj.isclone:
      rom_object = NoIntro_ROM(key)
      rom_object.hasClones = 0
      rom_pclone_dict[key] = rom_object

  # Second pass: traverse the raw list for clones and assign clone ROMS to 
  # their parents
  num_parents = 0
  num_clones = 0
  for key in rom_raw_dict:
    gameObj = rom_raw_dict[key]
    if gameObj.isclone:
      num_clones += 1
      # Find parent ROM. Raise error if not found
      if gameObj.cloneof in rom_pclone_dict:
        # Add clone ROM to the list of clones
        parentObj = rom_pclone_dict[gameObj.cloneof]
        if not hasattr(parentObj, 'clone_list'):
          parentObj.clone_list = []
          parentObj.hasClones = 1
        parentObj.clone_list.append(key)
      else:
        print('[ERROR] Game "' + key + '"')
        print('[ERROR] Parent "' + gameObj.cloneof + '"')
        print('[ERROR] Parent ROM not found "' + gameObj.cloneof + '"')
        sys.exit(10)
    else:
      num_parents += 1

  # DEBUG: print parent-clone dictionary
  for key in rom_pclone_dict:
    romObj = rom_pclone_dict[key]
    NARS.print_debug("Parent '" + romObj.baseName + "'")
    if romObj.hasClones:
      for clone in romObj.clone_list:
        NARS.print_debug(" Clone '" + clone + "'")

  # --- Create ROM main list ---
  romMainList_list = []
  for key in rom_pclone_dict:
    romNoIntroObj = rom_pclone_dict[key]
    # Create object and add first ROM (parent ROM)
    pclone_obj = PClone()
    pclone_obj.filenames = []
    pclone_obj.filenames.append(romNoIntroObj.baseName + '.zip')   
    # If game has clones add them to the list of filenames
    # NOTE To avoid problems with artwork substitution, make sure the list of
    #      clones is alphabetically sorted, so the output of the program is
    #      always the same for the same input. Otherwise, due to dictionary race
    #      conditions the order of this list may vary from execution to execution, and
    #      that is bad!
    if romNoIntroObj.hasClones:
      # Put clones in temporal list
      clones_list = []
      for clone in romNoIntroObj.clone_list:
        clones_list.append(clone + '.zip')
      # Sort alphabetically
      for clone in sorted(clones_list):
        pclone_obj.filenames.append(clone)

    # Add MainROM to the list
    romMainList_list.append(pclone_obj)

  return romMainList_list

def get_directory_Main_PClone_list(filter_config):
  """Reads a directory and creates a unique ROM parent/clone list"""
  __debug_sourceDir_ROM_scanner = 0
  
  # --- Read all files in sourceDir ---
  NARS.print_info('[Reading ROMs in source dir]')
  sourceDir = filter_config.sourceDir
  romMainList_dict = {}
  num_ROMs_sourceDir = 0
  for file in os.listdir(sourceDir):
    if file.endswith(".zip"):
      num_ROMs_sourceDir += 1
      romObject = dir_ROM(file)
      romObject.baseName = get_ROM_baseName(file)
      romMainList_dict[file] = romObject
      if __debug_sourceDir_ROM_scanner:
        print("  ROM       '" + romObject.fileName + "'")
        print("   baseName '" + romObject.baseName + "'")
  NARS.print_info('Found ' + str(num_ROMs_sourceDir) + ' ROMs')
  
  # --- Create a parent/clone list based on the baseName of the ROM ---
  pclone_ROM_dict = {}  # Key is ROM basename
  for key in romMainList_dict:
    baseName = romMainList_dict[key].baseName
    fileName = romMainList_dict[key].fileName
    # If baseName exists, add this ROM to that
    if baseName in pclone_ROM_dict:
      pclone_ROM_dict[baseName].append(fileName)
    # If not, create a new entry
    else:
      filenames = []
      filenames.append(fileName)
      pclone_ROM_dict[baseName] = filenames
  
  # --- Create ROM main list ---
  # NOTE To avoid problems with artwork substitution, make sure the list of
  #      clones is alphabetically sorted, so the output of the program is
  #      always the same for the same input. Otherwise, due to dictionary race
  #      conditions the order of this list may vary from execution to execution, and
  #      that is bad!
  romMainList_list = []
  for key in pclone_ROM_dict:
    # Create object and add first ROM (parent ROM)
    mainROM = PClone()
    mainROM.filenames = sorted(pclone_ROM_dict[key])
    # Add PClone object to the list
    romMainList_list.append(mainROM) 

  return romMainList_list

#
# Create a data structure of the form,
# [ 
#   [score1, file1, parent1, include1, ... ],
#   [score2, file2, parent2, include2, ... ], 
#   ...
# ]
# Then, this matrix can be reorded first by second column and then by first column (keeping order
# of the previously ordered second column) using lamba expressions.
#
def get_set_double_sorted(PClone_obj):

  # --- Create the list of lists ---
  ROM_list_list = [ ]
  for i in range(len(PClone_obj.filenames)):
    ROM_list_list.append( (PClone_obj.scores[i], PClone_obj.filenames[i], PClone_obj.parent[i], PClone_obj.include[i]) )
  # print(ROM_list_list)

  # --- Sort list of list by two rows ---
  # See http://stackoverflow.com/questions/5212870/sorting-a-python-list-by-two-criteria
  ROM_list_list.sort(key = lambda row:  row[1])
  ROM_list_list.sort(key = lambda row: -row[0]) # - means inverse sorting
  # print(ROM_list_list)

  # --- Convert back ---
  PClone_obj_out = PClone()
  PClone_obj_out.setName   =  PClone_obj.setName
  PClone_obj_out.scores    = [row[0] for row in ROM_list_list]
  PClone_obj_out.filenames = [row[1] for row in ROM_list_list]
  PClone_obj_out.parent    = [row[2] for row in ROM_list_list]
  PClone_obj_out.include   = [row[3] for row in ROM_list_list]

  return PClone_obj_out

# Score and filter the main ROM list.
#
# Returns,
#  romMain_list = [PClone, PClone, PClone, ...]
#  PClone.setName   [str]
#  PClone.filenames [str list]
#  PClone.scores    [int list]
#  PClone.include   [int list]
#  PClone.parent    [int list]
#
def get_Scores_and_Filter(romMain_list, rom_Tag_dic, filter_config):
  NARS.print_info('[Scoring and filtering ROMs]')
  __debug_main_ROM_list = 0

  upTag_list      = filter_config.filterUpTags
  downTag_list    = filter_config.filterDownTags
  includeTag_list = filter_config.includeTags
  excludeTag_list = filter_config.excludeTags

  # --- Add ROM scores to ROM main list ---
  for mainROM_obj in romMain_list:
    scores_list = []
    for filename in mainROM_obj.filenames:
      tags = rom_Tag_dic[filename]
      ROM_score = scoreROM(tags, upTag_list, downTag_list)
      scores_list.append(ROM_score)
    mainROM_obj.scores = scores_list

  # --- Add include/exclude filters to ROM main list ---
  for mainROM_obj in romMain_list:
    include_list = []
    for filename in mainROM_obj.filenames:
      tags = rom_Tag_dic[filename]
      # NOTE includeTag_list/excludeTag_list may be None (user didn't configure them)
      isTag_include = None
      isTag_exclude = None
      if includeTag_list is not None:  isTag_include = isTag(tags, includeTag_list)
      if excludeTag_list is not None:  isTag_exclude = isTag(tags, excludeTag_list)
      # Filtering cases,
      #  A) <includeTags>     empty | <excludeTags>     empty --> Include all ROMs
      #  B) <includeTags>     empty | <excludeTags> NON empty --> Exclude ROM with excludeTags only
      #  C) <includeTags> NON empty | <excludeTags>     empty --> Include all ROMs
      #  D) <includeTags> NON empty | <excludeTags> NON empty --> Exclude ROM if not includeTags and excludeTags
      #                                                           Include ROM if includeTags regardless of excludeTags
      # By default do not exclude ROMs
      includeThisROM = 1
      if isTag_include is None and isTag_exclude is not None:
        if isTag_exclude: 
          includeThisROM = 0
      elif isTag_include is not None and isTag_exclude is not None:
        if not isTag_include and isTag_exclude: 
          includeThisROM = 0
      include_list.append(includeThisROM)
    mainROM_obj.include = include_list

  # --- Add parent/clone flag ---
  # The parent ROM in the set is the first in the list, but would be good to know which
  # is the parent ROM after reordering.
  for mainROM_obj in romMain_list:
    parent_list = [0] * len(mainROM_obj.filenames)
    parent_list[0] = 1
    mainROM_obj.parent = parent_list

  # --- DEBUG: print main ROM list with scores and include flags ---
  if __debug_main_ROM_list:
    print("[DEBUG PClone ROM set object scored]")
    for mainROM_obj in romMain_list:
      print(mainROM_obj.filenames)
      print(mainROM_obj.scores)
      print(mainROM_obj.include)
      print(mainROM_obj.parent)

  # Order lists of the MainROM object based on scores and include flags.
  # Don't remove excluded ROMs because they may be useful to copy
  # artwork (for example, the use has artwork for an excluded ROM
  # belonging to the same set as the first ROM).
  #
  # GH Issue #2 If a parent and a clone receive the same score, then select
  #             the parent ROM and not the clone.
  romMain_list_sorted = []
  romSetName_list = []
  for ROM_obj in romMain_list:
    # --- Add setName field ---
    # The set name is the stripped name of the first ROM in the unsorted
    # This is compatible with both No-Intro and directory listings
    ParentROM_fileName = ROM_obj.filenames[0]
    thisFileName, thisFileExtension = os.path.splitext(ParentROM_fileName)
    stripped_ROM_name = get_ROM_baseName(thisFileName)
    ROM_obj.setName = stripped_ROM_name

    # --- Reorder PClone set object lists ---
    # sorted_idx = [i[0] for i in sorted(enumerate(ROM_obj.scores), key=lambda x:x[1])]
    # sorted_idx.reverse()
    # ROM_sorted = PClone()
    # ROM_sorted.setName   =  ROM_obj.setName
    # ROM_sorted.filenames = [ROM_obj.filenames[i] for i in sorted_idx]
    # ROM_sorted.scores    = [ROM_obj.scores[i]    for i in sorted_idx]
    # ROM_sorted.include   = [ROM_obj.include[i]   for i in sorted_idx]
    # ROM_sorted.parent    = [ROM_obj.parent[i]    for i in sorted_idx]

    # Problem  There is a random behaviour: if there are several ROMs with same score their position
    #          in the sorted list is random and changes on every execution of the program. This has
    #          bad consequences specially for artwork substitution but also have observed the issue
    #          when updating ROMs.
    # Solution Traverse the list of sorted ROMs. If there are several ROMs with same score that
    #          subgroup must be ordered alphabetically.
    # NOTE     This function implements the Solution and also orders by scores, making the original
    #          code to sort the PClone set unnecesary.
    ROM_sorted = get_set_double_sorted(ROM_obj)

    # Issue #2
    # Check if parent has maximum score OR parent has same score as one or several clones.
    # If the latter, put the parent first.
    top_scored_ROM_list = []
    maximum_score = ROM_sorted.scores[0]
    for i in range(len(ROM_sorted.filenames)):
      if ROM_sorted.scores[i] >= maximum_score:
        top_scored_ROM_list.append(ROM_sorted.filenames[i])
      else:
        break
    if ParentROM_fileName in top_scored_ROM_list and ParentROM_fileName != top_scored_ROM_list[0]:
      # Swap first element with parent
      parent_index = ROM_sorted.filenames.index(ParentROM_fileName)
      ROM_sorted.filenames[parent_index], ROM_sorted.filenames[0] = ROM_sorted.filenames[0], ROM_sorted.filenames[parent_index]
      ROM_sorted.scores[parent_index], ROM_sorted.scores[0]       = ROM_sorted.scores[0], ROM_sorted.scores[parent_index]
      ROM_sorted.include[parent_index], ROM_sorted.include[0]     = ROM_sorted.include[0], ROM_sorted.include[parent_index]
      ROM_sorted.parent[parent_index], ROM_sorted.parent[0]       = ROM_sorted.parent[0], ROM_sorted.parent[parent_index]

    # --- Insert reordered MainROM into ordered list ---
    romMain_list_sorted.append(ROM_sorted)
    romSetName_list.append(stripped_ROM_name)
  romMain_list = romMain_list_sorted

  # --- Finally, sort romMain_list list by ROMset name for nice listings ---
  sorted_idx = [i[0] for i in sorted(enumerate(romSetName_list), key=lambda x:x[1])]
  romMain_list_sorted = []
  romMain_list_sorted = [romMain_list[i] for i in sorted_idx]
  romMain_list = romMain_list_sorted

  return romMain_list

#
# Gets main PClone ROM list, either using a No-Intro DAT or guessing by the ROMs in sourceDir
#
def get_PClone_main_list(filter_config):
  if filter_config.NoIntro_XML is None:
    NARS.print_info('Using directory listing')
    romMainList_list = get_directory_Main_PClone_list(filter_config)
  else:
    NARS.print_info('Using No-Intro parent/clone DAT')
    romMainList_list = get_NoIntro_Main_PClone_list(filter_config)

  return romMainList_list

def filter_ROMs(filter_config):
  # --- Obtain main parent/clone list, either based on DAT file or sourceDir filelist ---
  romMainList_list = get_PClone_main_list(filter_config)

  # --- Get tag list for every rom ---
  rom_Tag_dic = get_Tag_dic(romMainList_list)

  # Calculate scores based on filters and reorder the main
  # list with higher scores first. Also applies exclude/include filters.
  romMainList_list = get_Scores_and_Filter(romMainList_list, rom_Tag_dic, filter_config)

  return romMainList_list

# -----------------------------------------------------------------------------
# Main body functions
# -----------------------------------------------------------------------------
list_ljust = 16
def do_list_filters():
  NARS.print_info('\033[1m[Listing configuration file]\033[0m')
  tree = NARS.XML_read_file_ElementTree(__config_configFileName, "Parsing configuration XML file")

  # --- This iterates through the collections ---
  root = tree.getroot()
  for collection in root:
    # print collection.tag, collection.attrib;
    NARS.print_info('\033[93m{ROM Collection}\033[0m')
    NARS.print_info('Short name'.ljust(list_ljust) + collection.attrib['shortname'])
    NARS.print_info('Name'.ljust(list_ljust) + collection.attrib['name'])

    # --- For every collection, iterate over the elements ---
    for collectionEL in collection:
      if collectionEL.tag == 'source':
        NARS.print_verb('Source'.ljust(list_ljust) + collectionEL.text)
      elif collectionEL.tag == 'dest':
        NARS.print_verb('Destination'.ljust(list_ljust) + collectionEL.text)
      elif collectionEL.tag == 'NoIntroDat' and collectionEL.text is not None:
        NARS.print_info('NoIntroDat'.ljust(list_ljust) + collectionEL.text)
      elif collectionEL.tag == 'filterUpTags' and collectionEL.text is not None:
        NARS.print_verb('filterUpTags'.ljust(list_ljust) + collectionEL.text)
      elif collectionEL.tag == 'filterDownTags' and collectionEL.text is not None:
        NARS.print_verb('filterDownTags'.ljust(list_ljust) + collectionEL.text)
      elif collectionEL.tag == 'includeTags' and collectionEL.text is not None:
        NARS.print_verb('includeTags'.ljust(list_ljust) + collectionEL.text)
      elif collectionEL.tag == 'excludeTags' and collectionEL.text is not None:
        NARS.print_verb('excludeTags'.ljust(list_ljust) + collectionEL.text)

    # Test if all mandatory elements are there

def do_list_nointro(filter_name):
  """List of NoIntro XML file"""

  NARS.print_info('\033[1m[Listing No-Intro XML DAT]\033[0m')
  NARS.print_info("Filter name '{:}'".format(filter_name))
  filter_config = get_Filter_from_Config(filter_name)
  filename = filter_config.NoIntro_XML
  if filename is None:
    print('\033[31m[ERROR]\033[0m Filter "{0}", No-Intro DAT not configured!'.format(filter_name))
    sys.exit(10)

  # Read No-Intro XML Parent-Clone DAT
  tree = NARS.XML_read_file_ElementTree(filename, "Parsing No-Intro XML DAT file ")
  root = tree.getroot()

  # ~~~ First pass to compute maximum string lengths and statistics ~~~
  num_games = 0
  num_parents = 0
  num_clones = 0
  max_game_str_length = 0
  for game_EL in root:
    if game_EL.tag != 'game':
      continue
    num_games += 1
    # --- Game attributes ---
    if 'cloneof' in game_EL.attrib:  num_clones += 1
    else:                            num_parents += 1
    if len(game_EL.attrib['name']) > max_game_str_length:
      max_game_str_length = len(game_EL.attrib['name'])

  # ~~~ Second pass print information ~~~
  for game_EL in root:
    if game_EL.tag != 'game':
      continue
    name = game_EL.attrib['name']
    if 'cloneof' in game_EL.attrib:
      game_kind = 'Clone'
    else:
      game_kind = 'Parent'
    # ~~~ Tags ~~~
    region_str = ''
    for game_child in game_EL:
      if game_child.tag == 'release':
        if 'region' in game_child.attrib:
          region_str = game_child.attrib['region']
    # ~~~ Print ~~~
    if game_kind == 'Parent':
      NARS.print_info('\033[100m{:>6}  {:<{ljustNum}} {:}\033[0m'.format(
        game_kind, game_EL.attrib['name'],  region_str, ljustNum=max_game_str_length))
    else:
      NARS.print_info('{:>6}  {:<{ljustNum}} {:}'.format(
        game_kind, game_EL.attrib['name'], region_str, ljustNum=max_game_str_length))

  NARS.print_info('[Report]')
  NARS.print_info('Number of games   {:5d}'.format(num_games))
  NARS.print_info('Number of parents {:5d}'.format(num_parents))
  NARS.print_info('Number of clones  {:5d}'.format(num_clones))
  if num_games != num_parents + num_clones:
    NARS.print_error('[ERROR] num_games != num_parents + num_clones')
    sys.exit(10)

def do_check_nointro(filter_name):
  """Checks ROMs in sourceDir against NoIntro XML file"""

  NARS.print_info('[Checking ROMs against No-Intro XML DAT]')
  NARS.print_info("Filter name '{:}'".format(filter_name))
  filter_config = get_Filter_from_Config(filter_name)

  # --- Get parameters and check for errors
  sourceDir = filter_config.sourceDir
  NARS.have_dir_or_abort(sourceDir, 'sourceDir')

  # --- Load No-Intro DAT
  XML_filename = filter_config.NoIntro_XML
  if XML_filename is None:
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
  NARS.print_info('[Scanning ROMs in sourceDir]')
  have_roms = 0
  unknown_roms = 0
  file_list = []
  for file in os.listdir(sourceDir):
    file_list.append(file)
  for file in sorted(file_list):
    if file.endswith(".zip"):
      if file in nointro_roms:
        have_roms += 1
        NARS.print_verb('\033[32m{   Have ROM}\033[0m  ' + file)
      else:
        unknown_roms += 1
        NARS.print_info('\033[33m{Unknown ROM}\033[0m  ' + file)

  # Check how many ROMs we have in the DAT not in sourceDir
  missing_roms = 0
  for game in sorted(nointro_roms):
    filename = sourceDir + game
    if not os.path.isfile(filename):
      NARS.print_info('\033[31m{Missing ROM}\033[0m  ' + game)
      missing_roms += 1

  NARS.print_info('[Report]')
  NARS.print_info('Files in sourceDir  {:5d}'.format(len(file_list)))
  NARS.print_info('Games in DAT        {:5d}'.format(num_games))
  NARS.print_info('Have ROMs           {:5d}'.format(have_roms))
  NARS.print_info('Missing ROMs        {:5d}'.format(missing_roms))
  NARS.print_info('Unknown ROMs        {:5d}'.format(unknown_roms))

def do_taglist(filter_name):
  """Makes a histograms of the tags of the ROMs in sourceDir"""

  NARS.print_info('[Listing tags]')
  NARS.print_info("Filter name '{:}'".format(filter_name))
  filter_config = get_Filter_from_Config(filter_name)
  source_dir = filter_config.sourceDir
  NARS.have_dir_or_abort(source_dir, 'sourceDir')
  NARS.print_info("Source directory '{:}'".format(source_dir))

  # Traverse directory, for every file extract properties, and add them to the
  # dictionary.
  properties_dic = {}
  for file in os.listdir(source_dir):
    if file.endswith(".zip"):
      rom_props = extract_ROM_Tags_All(file)
      if len(rom_props) == 0:
        print_error(file + 'Has no tags!')
        sys.exit(10)
      else:
        for property in rom_props:
          if property in properties_dic:
            properties_dic[property] += 1
          else:
            properties_dic[property] = 1

  # Works for Python 2
  # http://stackoverflow.com/questions/613183/python-sort-a-dictionary-by-value
  # sorted_propertiesDic = sorted(propertiesDic.iteritems(), key=operator.itemgetter(1))
  # This works on Python 3
  sorted_properties_dic = ((k, properties_dic[k]) for k in sorted(properties_dic, key=properties_dic.get, reverse=False))
    
  NARS.print_info('[Tag histogram]')
  for key in sorted_properties_dic:
    NARS.print_info('{:6d}'.format(key[1]) + '  ' + key[0])

#
# Applies filter and prints filtered parent/clone list, ROMs you have, etc., in a
# nice format.
#
def do_check(filter_name):
  NARS.print_info('[Check-filter ROM]')
  NARS.print_info("Filter name '{:}'".format(filter_name))
  filter_config = get_Filter_from_Config(filter_name)

  # --- Filter ROMs ---
  romMainList_list = filter_ROMs(filter_config)

  # --- Get maximum width of ROM set names for nice printing ---
  max_ROMSetName_width = 1
  for index_main in range(len(romMainList_list)):
    if len(romMainList_list[index_main].setName) > max_ROMSetName_width:
      max_ROMSetName_width = len(romMainList_list[index_main].setName)

  # --- Print list in alphabetical order ---
  num_parents = 0
  num_clones = 0
  num_roms = 0
  num_have_roms = 0
  num_miss_roms = 0
  num_include_roms = 0
  num_exclude_roms = 0
  NARS.have_dir_or_abort(filter_config.sourceDir, 'sourceDir')
  NARS.print_info("[List of scored parent/clone ROM sets]")
  for index_main in range(len(romMainList_list)):
    rom_object = romMainList_list[index_main]
    for index in range(len(rom_object.filenames)):
      # Check if file exists (maybe it does not exist for No-Intro lists)
      sourceFullFilename = filter_config.sourceDir + rom_object.filenames[index]
      fullROMFilename = os.path.isfile(sourceFullFilename)
      num_roms += 1
      if index == 0: copyFlag = '\033[32mCOPY\033[0m'
      else:          copyFlag = '    '

      if not os.path.isfile(sourceFullFilename):
        haveFlag = '\033[31mMISS\033[0m'
        num_miss_roms += 1
      else:
        haveFlag = '\033[32mHAVE\033[0m'
        num_have_roms += 1

      if rom_object.include[index] == 0:
        excludeFlag = '\033[31mEXC\033[0m'
        num_exclude_roms += 1
      else:
        excludeFlag = '\033[32mINC\033[0m'
        num_include_roms += 1

      if rom_object.parent[index] == 0:
        parentFlag = 'CLO'
        num_clones += 1
      else:
        parentFlag = '\033[35mPAR\033[0m'
        num_parents += 1
      # --- Print ---
      # ~ Compact way ~
#      if index == 0:
#        NARS.print_info('\033[100m{0}\033[0m'.format(rom_object.setName.ljust(max_ROMSetName_width)) +
#                        ' {:3d} '.format(rom_object.scores[index]) +
#                        haveFlag + ' ' +  excludeFlag + ' ' + parentFlag + ' ' + copyFlag + '  ' +
#                        rom_object.filenames[index])
#      else:
#        NARS.print_info(' '.rjust(max_ROMSetName_width) +
#                        ' {:3d} '.format(rom_object.scores[index]) +
#                        haveFlag + ' ' +  excludeFlag + ' ' + parentFlag + ' ' + copyFlag + '  ' +
#                        rom_object.filenames[index])
      # ~ Wide way ~
      if index == 0:
        NARS.print_info('\033[7m{0}\033[0m'.format(rom_object.setName))
      NARS.print_info(' {:3d} '.format(rom_object.scores[index]) +
                      haveFlag + ' ' +  excludeFlag + ' ' + parentFlag + ' ' + copyFlag + '  ' +
                      rom_object.filenames[index])

  NARS.print_info('[Report]')
  NARS.print_info('Parents  {:5d}'.format(num_parents))
  NARS.print_info('Clones   {:5d}'.format(num_clones))
  NARS.print_info('ROMs     {:5d}'.format(num_roms))
  NARS.print_info('Have     {:5d}'.format(num_have_roms))
  NARS.print_info('Miss     {:5d}'.format(num_miss_roms))
  NARS.print_info('Include  {:5d}'.format(num_include_roms))
  NARS.print_info('Exclude  {:5d}'.format(num_exclude_roms))

def do_update(filter_name):
  """Applies filter and updates (copies) ROMs"""

  NARS.print_info('[Copy/Update ROMs]')
  NARS.print_info("Filter name '{:}'".format(filter_name))
  filter_config = get_Filter_from_Config(filter_name)
  sourceDir = filter_config.sourceDir
  destDir   = filter_config.destDir
  NARS.have_dir_or_abort(sourceDir, 'sourceDir')
  NARS.have_dir_or_abort(destDir, 'destDir')
  NARS.print_info("Source directory      '{:}'".format(sourceDir))
  NARS.print_info("Destination directory '{:}'".format(destDir))

  # --- Filter ROMs ---
  romMainList_list = filter_ROMs(filter_config)

  # Make a list of files to be copied, depending on ROMS present in
  # sourceDir. Takes into account the ROM scores and the
  # exclude/include filters.
  rom_copy_list = create_copy_list(romMainList_list, filter_config)

  # --- Copy/Update ROMs into destDir
  if __prog_option_sync:
    update_ROM_list(rom_copy_list, sourceDir, destDir)
  else:
    copy_ROM_list(rom_copy_list, sourceDir, destDir) 

  # --- If --cleanROMs is on then delete unknown files.
  if __prog_option_clean_ROMs:
    clean_ROMs_destDir(destDir, rom_copy_list)

  # --- Delete NFO files of ROMs not present in the destination directory.
  if __prog_option_clean_NFOs:
    delete_redundant_NFO(destDir)

def do_checkArtwork(filter_name):
  """Checks for missing artwork and prints a report"""

  NARS.print_info('[Check-ArtWork]')
  NARS.print_info("Filter name '{:}'".format(filter_name))

  # --- Get configuration for the selected filter and check for errors ---
  filter_config = get_Filter_from_Config(filter_name)
  source_dir = filter_config.sourceDir
  destDir = filter_config.destDir
  thumbsSourceDir = filter_config.thumbsSourceDir
  fanartSourceDir = filter_config.fanartSourceDir
  NARS.have_dir_or_abort(source_dir, 'sourceDir')
  NARS.have_dir_or_abort(destDir, 'destDir')
  NARS.have_dir_or_abort(thumbsSourceDir, 'thumbsSourceDir')
  NARS.have_dir_or_abort(fanartSourceDir, 'fanartSourceDir')
  NARS.print_info("Source directory        '{:}'".format(source_dir))
  NARS.print_info("Destination directory   '{:}'".format(destDir))
  NARS.print_info("Thumbs Source directory '{:}'".format(thumbsSourceDir))
  NARS.print_info("Fanart Source directory '{:}'".format(fanartSourceDir))

  # --- Obtain main parent/clone list, either based on DAT or filelist ---
  romMainList_list = get_PClone_main_list(filter_config)

  # --- Create a list of ROMs in destDir ---
  roms_destDir_list = []
  for file in os.listdir(destDir):
    if file.endswith(".zip"):
      thisFileName, thisFileExtension = os.path.splitext(file)
      roms_destDir_list.append(thisFileName)

  # --- Replace missing artwork for alternative artwork in the parent/clone set ---
  artwork_copy_dic = optimize_ArtWork_list(roms_destDir_list, romMainList_list, filter_config)

  # --- Print list in alphabetical order ---
  NARS.print_info('[Artwork report]')
  num_original_thumbs = 0
  num_subst_thumbs    = 0
  num_missing_thumbs  = 0
  num_original_fanart = 0
  num_subst_fanart    = 0
  num_missing_fanart  = 0
  for rom_base_name in sorted(roms_destDir_list):
    NARS.print_info('\033[7m{0}\033[0m'.format(rom_base_name + ".zip"))
    artwork_dic = artwork_copy_dic[rom_base_name]

    # --- Check thumb ---
    if artwork_dic['thumb'] is None:
      thumb_flag = '\033[31mMISS\033[0m          THUMB '
      artwork_name = ''
      num_missing_thumbs += 1
    else:
      artwork_name = artwork_dic['thumb'] + '.png'
      if artwork_dic['thumb'] == rom_base_name:
        thumb_flag = '\033[32mHAVE ORIGINAL\033[0m THUMB '
        num_original_thumbs += 1
      else:
        thumb_flag = '\033[32mHAVE\033[0m SUBST    THUMB '
        num_subst_thumbs += 1
    NARS.print_info('{0}  {1}'.format(thumb_flag, artwork_name))

    # --- Check fanart ---
    if artwork_dic['fanart'] is None:
      thumb_flag = '\033[31mMISS\033[0m          FANART'
      artwork_name = ''
      num_missing_fanart += 1
    else:
      artwork_name = artwork_dic['fanart'] + '.png'
      if artwork_dic['fanart'] == rom_base_name:
        thumb_flag = '\033[32mHAVE ORIGINAL\033[0m FANART'
        num_original_fanart += 1
      else:
        thumb_flag = '\033[32mHAVE\033[0m SUBST    FANART'
        num_subst_fanart += 1
    NARS.print_info('{0}  {1}'.format(thumb_flag, artwork_name))

  NARS.print_info('[Report]')
  NARS.print_info('ROMs in destDir  {:5d}'.format(len(roms_destDir_list)))
  NARS.print_info('Have    Thumbs   {:5d} (Original {:5d}  Subst {:5d})'.format(num_original_thumbs + num_subst_thumbs,
                                                                                num_original_thumbs, num_subst_thumbs))
  NARS.print_info('Missing Thumbs   {:5d}'.format(num_missing_thumbs))
  NARS.print_info('Have    Fanart   {:5d} (Original {:5d}  Subst {:5d})'.format(num_original_fanart + num_subst_fanart,
                                                                                num_original_fanart, num_subst_fanart))
  NARS.print_info('Missing Fanart   {:5d}'.format(num_missing_fanart))

def do_update_artwork(filter_name):
  NARS.print_info('[Updating/copying ArtWork]')
  NARS.print_info("Filter name '{:}'".format(filter_name))

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_from_Config(filter_name)
  source_dir = filter_config.sourceDir
  dest_dir = filter_config.destDir
  thumbs_source_dir = filter_config.thumbsSourceDir
  fanart_source_dir = filter_config.fanartSourceDir
  thumbs_dest_dir = filter_config.thumbsDestDir
  fanart_dest_dir = filter_config.fanartDestDir
  NARS.have_dir_or_abort(source_dir, 'source_dir')
  NARS.have_dir_or_abort(dest_dir, 'dest_dir')
  NARS.have_dir_or_abort(thumbs_source_dir, 'thumbs_source_dir')
  NARS.have_dir_or_abort(fanart_source_dir, 'fanart_source_dir')
  NARS.have_dir_or_abort(thumbs_dest_dir, 'thumbs_dest_dir')
  NARS.have_dir_or_abort(fanart_dest_dir, 'fanart_dest_dir')
  NARS.print_info("Source directory             '{:}'".format(source_dir))
  NARS.print_info("Destination directory        '{:}'".format(dest_dir))
  NARS.print_info("Thumbs Source directory      '{:}'".format(thumbs_source_dir))
  NARS.print_info("Fanart Source directory      '{:}'".format(fanart_source_dir))
  NARS.print_info("Thumbs Destination directory '{:}'".format(thumbs_dest_dir))
  NARS.print_info("Fanart Destination directory '{:}'".format(fanart_dest_dir))

  # --- Obtain main parent/clone list, either based on DAT or filelist ---
  romMainList_list = get_PClone_main_list(filter_config)

  # --- Create a list of ROMs in dest_dir ---
  roms_destDir_list = []
  for file in os.listdir(dest_dir):
    if file.endswith(".zip"):
      thisFileName, thisFileExtension = os.path.splitext(file)
      roms_destDir_list.append(thisFileName)

  # --- Replace missing artwork for alternative artwork in the parent/clone set ---
  artwork_copy_dic = optimize_ArtWork_list(roms_destDir_list, romMainList_list, filter_config)

  # --- Copy artwork ---
  if __prog_option_sync:
    update_ArtWork_files(filter_config, artwork_copy_dic)
  else:
    copy_ArtWork_files(filter_config, artwork_copy_dic)

  # --- If --cleanArtWork is on then delete unknown files. ---
  if __prog_option_clean_ArtWork:
    clean_ArtWork_destDir(filter_config, artwork_copy_dic)

def do_printHelp():
  print("""\033[32mUsage: nars-console.py [options] <command> [romSetName]\033[0m

\033[32mCommands:\033[0m
\033[31musage\033[0m                    Print usage information (this text)
\033[31mlist\033[0m                     List every filter defined in the configuration file.
\033[31mlist-nointro <filter>\033[0m    List every ROM set system defined in the No-Intro DAT file.
\033[31mcheck-nointro <filter>\033[0m   Checks the ROMs you have and reports missing ROMs.
\033[31mlist-tags <filter>\033[0m       Scan the source directory and reports the tags found.
\033[31mcheck <filter>\033[0m           Applies ROM filters and prints a list of the scored ROMs.
\033[31mcopy <filter>\033[0m            Applies ROM filters defined and copies ROMS from sourceDir into destDir.
\033[31mupdate <filter>\033[0m          Like copy, but also delete unneeded ROMs in destDir.
\033[31mcheck-artwork  <filter>\033[0m  Reads the ROMs in destDir, checks if you have the corresponding artwork. 
\033[31mcopy-artwork   <filter>\033[0m  Reads the ROMs in destDir and tries to copy the artwork to destDir.
\033[31mupdate-artwork <filter>\033[0m  Like copy-artwork, but also delete unknown images in artwork destDir.

\033[32mOptions:
\033[35m-h\033[0m, \033[35m--help\033[0m               Print short command reference.
\033[35m-v\033[0m, \033[35m--verbose\033[0m            Print more information about what's going on.
\033[35m-l\033[0m, \033[35m--log\033[0m                Save program output in xru-console-log.txt.
\033[35m--logto\033[0m \033[31m[logName]\033[0m        Save program output in the file you specify.
\033[35m--dryRun\033[0m                 Don't modify destDir at all, just print the operations to be done.
\033[35m--cleanROMs\033[0m              Deletes ROMs in destDir not present in the filtered ROM list.
\033[35m--cleanNFOs\033[0m              Deletes redundant NFO files in destination directory.
\033[35m--cleanArtWork\033[0m           Deletes unknown artwork in destination.""")

# -----------------------------------------------------------------------------
# main function
# -----------------------------------------------------------------------------
print('\033[36mNARS Advanced ROM Sorting - Console No-Intro ROMs\033[0m' +
      ' version ' + NARS.__software_version)

# --- Command line parser
parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', help="be verbose", action="count")
parser.add_argument('-l', '--log', help="log output to default file", action='store_true')
parser.add_argument('--logto', help="log output to specified file", nargs = 1)
parser.add_argument('--dryRun', help="don't modify any files", action="store_true")
parser.add_argument('--cleanROMs', help="clean destDir of unknown ROMs", action="store_true")
parser.add_argument('--cleanNFOs', help="clean redundant NFO files", action="store_true")
parser.add_argument('--cleanArtWork', help="clean unknown ArtWork", action="store_true")
parser.add_argument('command',
   help="usage, list, list-nointro, check-nointro, list-tags, \
         check, copy, update \
         check-artwork, copy-artwork, update-artwork", nargs = 1)
parser.add_argument("filterName", help="ROM collection name", nargs='?')
args = parser.parse_args()

# --- Optional arguments ---
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
  __prog_option_log = 1
if args.logto:
  __prog_option_log = 1
  __prog_option_log_filename = args.logto[0]
if args.dryRun:       __prog_option_dry_run = 1
if args.cleanROMs:    __prog_option_clean_ROMs = 1
if args.cleanNFOs:     __prog_option_clean_NFOs = 1
if args.cleanArtWork: __prog_option_clean_ArtWork = 1

# --- Positional arguments that don't require parsing of the config file ---
command = args.command[0]
if command == 'usage':
  do_printHelp()
  sys.exit(0)

# --- Check arguments that require a filterName ---
if command == 'list-nointro' or command == 'check-nointro' or \
   command == 'list-tags' or \
   command == 'check' or command == 'copy' or command == 'update' or \
   command == 'check-artwork' or command == 'copy-artwork' or command == 'update-artwork':
  if args.filterName is None:
    print('\033[31m[ERROR]\033[0m Command "{0}" requires a filter name'.format(command))
    sys.exit(10)

# --- Read configuration file ---
configuration = parse_File_Config()

# --- Positional arguments that don't require a filterName
if command == 'list':
  do_list_filters()
elif command == 'list-nointro':
  do_list_nointro(args.filterName)
elif command == 'check-nointro':
  do_check_nointro(args.filterName)
elif command == 'list-tags':
  do_taglist(args.filterName)
elif command == 'check':
  do_check(args.filterName)
elif command == 'copy':
  do_update(args.filterName)
elif command == 'update':
  __prog_option_sync = 1
  do_update(args.filterName)
elif command == 'check-artwork':
  do_checkArtwork(args.filterName)
elif command == 'copy-artwork':
  do_update_artwork(args.filterName)
elif command == 'update-artwork':
  __prog_option_sync = 1
  do_update_artwork(args.filterName)
else:
  print('\033[31m[ERROR]\033[0m Unrecognised command "{0}"'.format(command))
  sys.exit(1)

# Bye bye
sys.exit(0)
