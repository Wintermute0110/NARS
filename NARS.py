# NARS Advanced ROM Sorting
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
import sys
import os
import re
import shutil

# ElementTree XML parser
import xml.etree.ElementTree as ET

# This is supposed to be much faster than ElementTree
# See http://effbot.org/zone/celementtree.htm
# Tests with list-* commands indicate this 6x faster than ElementTree
# HOWEVER: the reduce command takes AGES checking the dependencies!!!
import xml.etree.cElementTree as cET

# ElementTree generated XML files are nasty looking (no end of lines).
# Minidom does a much better job.
# NOTE minidom is VERY SLOW.
# from xml.dom import minidom

# NOTE SAX API can make the loading of XML much faster and MUCH LESS
#      memory consuming.

# -----------------------------------------------------------------------------
# Global variables
# -----------------------------------------------------------------------------
__software_version = '0.2.0_alpha1';

# -----------------------------------------------------------------------------
# DEBUG functions
# -----------------------------------------------------------------------------
def dumpclean(obj):
  if type(obj) == dict:
    for k, v in obj.items():
      if hasattr(v, '__iter__'):
        print(k)
        dumpclean(v)
      else:
        print('%s : %s' % (k, v))
  elif type(obj) == list:
    for v in obj:
      if hasattr(v, '__iter__'):
        dumpclean(v)
      else:
        print(v)
  else:
      print(obj)

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
f_log = 0;     # Log file descriptor
log_level = 3; # Log level
file_log = 0;  # User wants file log

def init_log_system(__prog_option_log):
  global file_log
  global f_log

  file_log = __prog_option_log

  # --- Open log file descriptor
  if file_log:
    if f_log == 0:
      f_log = open(__prog_option_log_filename, 'w')

def change_log_level(level):
  global log_level;

  log_level = level;

# --- Print/log to a specific level  
def pprint(level, print_str):
  # --- Write to console depending on verbosity
  if level <= log_level:
    print(print_str)

  # --- Write to file
  if file_log:
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
# Filesystem low-level functions
# -----------------------------------------------------------------------------
# This function either succeeds or aborts the program. Check if file exists
# before calling this.
def delete_file(file_path, __prog_option_dry_run):
  if __prog_option_dry_run:
    return
  try:
    os.remove(file_path);
  except EnvironmentError:
    print_info('[WARNING] delete_file >> os.remove {0}'.format(file_path))
    print_info('[WARNING] delete_file >> Exception EnvironmentError triggered')

# Deletes directory CHD_dir, deleting CHD files first, then delete the directory
# using rmdir. Abort if directory is not empty after cleaning CHD files.
# Returns,
# n >= 0  Directory deleted and number of CHD files deleted (maybe 0)
__DEBUG_delete_CHD_directory = 0
def delete_CHD_directory(CHD_dir, __prog_option_dry_run):
  num_deleted_CHD = 0

  CHD_list = [];
  for file in os.listdir(CHD_dir):
    if file.endswith(".chd"):
      CHD_full_path = CHD_dir + '/' + file
      if __DEBUG_delete_CHD_directory: 
        print('CHD_list file {0}'.format(CHD_full_path))
      CHD_list.append(CHD_full_path);

  # Delete all CHD files inside directory
  if __prog_option_dry_run:
    return
  for file in CHD_list:
    try:
      os.remove(file)
      if __DEBUG_delete_CHD_directory: 
        print('Deleted CHD       {0}'.format(file))
    except EnvironmentError:
      print_info('[WARNING] delete_CHD_directory >> os.remove {0}'.format(file))
      print_info('[WARNING] delete_CHD_directory >>  Error happened deleting CHD file')
    num_deleted_CHD += 1
  try:
    os.rmdir(CHD_dir)
    if __DEBUG_delete_CHD_directory: 
      print('Deleted directory {0}'.format(CHD_dir))
  except OSError:
    print_info('[WARNING] delete_CHD_directory >> os.rmdir {0}'.format(CHD_dir))
    print_info('[WARNING] delete_CHD_directory >> Directory not empty after deleting CHD file/s')
    sys.exit(10)

  return num_deleted_CHD

# if dirName is None, that means user did not configured it
def have_dir_or_abort(dirName, infoStr):
  if dirName == None:
    print_error('\033[31m[ERROR]\033[0m Directory ' + infoStr + ' not configured.')
    print_error('\033[31m[ERROR]\033[0m Add tag ' + infoStr + ' to configuration file.')
    sys.exit(10)

  if not os.path.isdir(dirName):
    print_error('\033[31m[ERROR]\033[0m Directory does not exist ' + infoStr + ' = ' + dirName)
    sys.exit(10)

# Make sure directory name is OK.
# a) dirName end with '/'. If not, add it.
def sanitize_dir_name(dirName):
  
  return dirName

# Returns:
#  0  File copied, no error
#  2  Source file missing
# -1  Copy error (exception)
def copy_file(source_path, dest_path, __prog_option_dry_run):
  print_debug('Copying ' + source_path)
  print_debug('Into    ' + dest_path)

  existsSource = os.path.isfile(source_path)
  if not existsSource:
    return 2

  if __prog_option_dry_run:
    return 0
    
  try:
    shutil.copy(source_path, dest_path)
  except EnvironmentError:
    print_info('[WARNING] copy_file >> source_path {0}'.format(source_path))
    print_info('[WARNING] copy_file >> dest_path {0}'.format(dest_path))
    print_info('[WARNING] copy_file >> Exception EnvironmentError triggered')
    return -1

  return 0

# Returns:
#  0  File copied (sizes different)
#  1  File not copied (updated)
#  2  Source file missing
# -1  Copy/Stat error (exception)
def update_file(source_path, dest_path, __prog_option_dry_run):
  print_debug('Updating ' + source_path)
  print_debug('Into     ' + dest_path)

  existsSource = os.path.isfile(source_path)
  existsDest = os.path.isfile(dest_path)
  if not existsSource:
    return 2

  sizeSource = os.path.getsize(source_path)
  if existsDest:
    sizeDest = os.path.getsize(dest_path)
  else:
    sizeDest = -1

  # If sizes are equal. Skip copy and return 1
  if sizeSource == sizeDest:
    return 1

  # destFile does not exist or sizes are different, copy.
  if __prog_option_dry_run:
    return 0

  try:
    shutil.copy(source_path, dest_path)
  except EnvironmentError:
    print_info('[WARNING] update_file >> source_path {0}'.format(source_path))
    print_info('[WARNING] update_file >> dest_path {0}'.format(dest_path))
    print_info('[WARNING] update_file >> Exception EnvironmentError triggered')
    return -1

  return 0

# -----------------------------------------------------------------------------
# Filesystem helper functions
# -----------------------------------------------------------------------------
def copy_ROM_list(rom_list, sourceDir, destDir, __prog_option_sync, __prog_option_dry_run):
  print_info('[Copying ROMs into destDir]');

  num_steps = len(rom_list);
  step = 0 # 0 here prints [0, ..., 99%] instead [1, ..., 100%]
  num_roms = 0
  num_copied_roms = 0
  num_updated_roms = 0
  num_missing_roms = 0
  num_errors = 0
  for rom_copy_item in sorted(rom_list):
    romFileName = rom_copy_item + '.zip'
    source_path = sourceDir + romFileName
    dest_path = destDir + romFileName
    num_roms += 1
    if __prog_option_sync:
      ret = update_file(source_path, dest_path, __prog_option_dry_run)
    else:
      ret = copy_file(source_path, dest_path, __prog_option_dry_run)
    # On default verbosity level only report copied files and errors
    percentage = 100 * step / num_steps
    if ret == 0:
      num_copied_roms += 1;
      sys.stdout.write('{:3.0f}% '.format(percentage));
      print_info('<Copied > ' + romFileName);
    elif ret == 1:
      num_updated_roms += 1;
      if log_level >= Log.verb:
        sys.stdout.write('{:3.0f}% '.format(percentage));
      print_verb('<Updated> ' + romFileName);
    elif ret == 2:
      num_missing_roms += 1;
      sys.stdout.write('{:3.0f}% '.format(percentage));
      print_info('<Missing> ' + romFileName);
    elif ret == -1:
      num_errors += 1;
      sys.stdout.write('{:3.0f}% '.format(percentage));
      print_info('<ERROR  > ' + romFileName);
    else:
      print_error('Wrong value returned by update_ROM_file()')
      sys.exit(10)
    # --- Update progress
    step += 1;

  print_info('[Report]');
  print_info('Total CHDs   ' + '{:4d}'.format(num_roms));
  print_info('Copied CHDs  ' + '{:4d}'.format(num_copied_roms));
  print_info('Update CHDs  ' + '{:4d}'.format(num_updated_roms));
  print_info('Missing CHDs ' + '{:4d}'.format(num_missing_roms));
  print_info('Copy errors  ' + '{:4d}'.format(num_errors));

#
# CHD_dic = { 'machine_name' : ['chd1', 'chd2', ...], ... }
#
__debug_copy_CHD_dic = 0
def copy_CHD_dic(CHD_dic, sourceDir, destDir, __prog_option_sync, __prog_option_dry_run):
  print_info('[Copying CHDs into destDir]');

  # If user did not configure CHDs source directory then do nothing
  if sourceDir == None or sourceDir == '':
    print_info('CHD source directory not configured');
    print_info('Skipping CHD copy');
    return

  if not os.path.exists(sourceDir):
    print_error('CHD source directory not found ' + sourceDir)
    sys.exit(10);

  # --- Copy CHDs ---
  num_steps = len(CHD_dic);
  step = 0 # 0 here prints [0, ..., 99%], 1 prints [1, ..., 100%]
  num_CHD = 0
  num_copied_CHD = 0
  num_updated_CHD = 0
  num_missing_CHD = 0
  num_errors = 0
  for machine_name in sorted(CHD_dic):
    # Check if CHD directory exists. If not, create it. Abort if creation fails.
    chdSourceDir = sourceDir + machine_name + '/'
    chdDestDir = destDir + machine_name + '/'
    if __debug_copy_CHD_dic: print('CHD dir = {0}\n'.format(chdDestDir))
    if not os.path.isdir(chdDestDir):
      if __debug_copy_CHD_dic: print('Creating CHD dir = {0}\n'.format(chdDestDir))
      os.makedirs(chdDestDir);

    # Iterate over this machine CHD list and copy them. Abort if CHD cannot be
    # copied
    CHD_list = CHD_dic[machine_name]
    for CHD_file in CHD_list:
      chd_file_name = CHD_file + '.chd'
      chd_file_path_source = chd_file_name + chdSourceDir
      chd_file_path_dest = chd_file_name + chdDestDir
      num_CHD += 1
      if __prog_option_sync:
        ret = update_file(chd_file_path_source, chd_file_path_dest, __prog_option_dry_run)
      else:
        ret = copy_file(chd_file_path_source, chd_file_path_dest, __prog_option_dry_run)
      # On default verbosity level only report copied files and errors
      percentage = 100 * step / num_steps
      if ret == 0:
        num_copied_CHD += 1
        sys.stdout.write('{:3.0f}% '.format(percentage))
        print_info('<Copied > ' + machine_name + '/' + chd_file_name)
      elif ret == 1:
        num_updated_CHD += 1
        if log_level >= Log.verb:
          sys.stdout.write('{:3.0f}% '.format(percentage))
        print_verb('<Updated> ' + machine_name + '/' + chd_file_name)
      elif ret == 2:
        num_missing_CHD += 1
        sys.stdout.write('{:3.0f}% '.format(percentage))
        print_info('<Missing> ' + machine_name + '/' + chd_file_name)
      elif ret == -1:
        num_errors += 1
        sys.stdout.write('{:3.0f}% '.format(percentage))
        print_info('<ERROR  > ' + machine_name + '/' + chd_file_name)
      else:
        print_error('Wrong value returned by update_ROM_file()')
        sys.exit(10)
      sys.stdout.flush()
    # --- Update progress
    step += 1;

  print_info('[Report]');
  print_info('Total CHDs   ' + '{:4d}'.format(num_CHD));
  print_info('Copied CHDs  ' + '{:4d}'.format(num_copied_CHD));
  print_info('Update CHDs  ' + '{:4d}'.format(num_updated_CHD));
  print_info('Missing CHDs ' + '{:4d}'.format(num_missing_CHD));
  print_info('Copy errors  ' + '{:4d}'.format(num_errors));

def copy_ArtWork_list(filter_config, rom_copy_dic, __prog_option_sync, __prog_option_dry_run):
  print_info('[Copying ArtWork]');
  fanartSourceDir = filter_config.fanartSourceDir;
  fanartDestDir = filter_config.fanartDestDir;
  thumbsSourceDir = filter_config.thumbsSourceDir;
  thumbsDestDir = filter_config.thumbsDestDir;

  # --- Copy artwork
  num_steps = len(rom_copy_dic)
  step = 0
  num_artwork = 0
  num_copied_thumbs = 0
  num_updated_thumbs = 0
  num_missing_thumbs = 0
  num_copied_fanart = 0
  num_updated_fanart = 0
  num_missing_fanart = 0
  for rom_baseName in sorted(rom_copy_dic):
    # --- Get artwork name
    art_baseName = rom_copy_dic[rom_baseName]
    num_artwork += 1

    # --- Thumbs
    thumb_file_path_source = art_baseName + thumbsSourceDir
    thumb_file_path_dest = rom_baseName + thumbsDestDir
    if __prog_option_sync:
      ret = update_file(thumb_file_path_source, thumb_file_path_dest, __prog_option_dry_run)
    else:
      ret = copy_file(thumb_file_path_source, thumb_file_path_dest, __prog_option_dry_run)
    # On default verbosity level only report copied files
    percentage = 100 * step / num_steps;    
    if ret == 0:
      sys.stdout.write('{:3.0f}% '.format(percentage));
      num_copied_thumbs += 1;
      print_info('<Copied  Thumb > ' + art_baseName);
    elif ret == 1:
      sys.stdout.write('{:3.0f}% '.format(percentage));
      num_missing_thumbs += 1;
      print_info('<Missing Thumb > ' + art_baseName);
    elif ret == 2:
      if log_level >= Log.verb:
        sys.stdout.write('{:3.0f}% '.format(percentage));
      num_updated_thumbs += 1
      print_verb('<Updated Thumb > ' + art_baseName)
    elif ret == -1:
      num_errors += 1;
      sys.stdout.write('{:3.0f}% '.format(percentage));
      print_info('<ERROR  > ' + art_baseName);
    else:
      print_error('Wrong value returned by copy_ArtWork_file()');
      sys.exit(10)

    # --- Fanart
    fanart_file_path_source = art_baseName + fanartSourceDir
    fanart_file_path_dest = rom_baseName + fanartDestDir
    if __prog_option_sync:
      ret = update_file(fanart_file_path_source, fanart_file_path_dest, __prog_option_dry_run)
    else:
      ret = copy_file(fanart_file_path_source, fanart_file_path_dest, __prog_option_dry_run)
    # On default verbosity level only report copied files
    if ret == 0:
      sys.stdout.write('{:3.0f}% '.format(percentage))
      num_copied_fanart += 1
      print_info('<Copied  Thumb > ' + art_baseName)
    elif ret == 1:
      sys.stdout.write('{:3.0f}% '.format(percentage))
      num_missing_fanart += 1
      print_info('<Missing Thumb > ' + art_baseName)
    elif ret == 2:
      if log_level >= Log.verb:
        sys.stdout.write('{:3.0f}% '.format(percentage))
      num_updated_fanart += 1
      print_verb('<Updated Thumb > ' + art_baseName)
    elif ret == -1:
      num_errors += 1;
      sys.stdout.write('{:3.0f}% '.format(percentage))
      print_info('<ERROR  > ' + art_baseName)
    else:
      print_error('Wrong value returned by copy_ArtWork_file()')
      sys.exit(10)

    # --- Update progress
    step += 1;

  print_info('[Report]')
  print_info('Artwork files ' + '{:6d}'.format(num_artwork))  
  print_info('Copied thumbs ' + '{:6d}'.format(num_copied_thumbs))
  print_info('Updated thumbs ' + '{:5d}'.format(num_updated_thumbs))
  print_info('Missing thumbs ' + '{:5d}'.format(num_missing_thumbs))
  print_info('Copied fanart ' + '{:6d}'.format(num_copied_fanart))
  print_info('Updated fanart ' + '{:5d}'.format(num_updated_fanart))
  print_info('Missing fanart ' + '{:5d}'.format(num_missing_fanart))

# Delete ROMs present in destDir not present in the filtered list
# 1) Make a list of .zip files in destDir
# 2) Delete all .zip files of games no in the filtered list
def clean_ROMs_destDir(rom_copy_dic, destDir, __prog_option_dry_run):
  print_info('[Cleaning ROMs in ROMsDest]')

  rom_main_list = [];
  for file in os.listdir(destDir):
    if file.endswith(".zip"):
      rom_main_list.append(file);

  num_cleaned_roms = 0;
  for file in sorted(rom_main_list):
    basename, ext = os.path.splitext(file); # Remove extension
    if basename not in rom_copy_dic:
      num_cleaned_roms += 1
      file_path = destDir + file
      delete_file(file_path, __prog_option_dry_run)
      print_info('<Deleted> ' + file);

  print_info('Deleted ' + str(num_cleaned_roms) + ' redundant ROMs')

# Delete CHDs in destDir not in the filtered list
# 1) Scan directories in destDir
# 2) Check if directory is a machine name in filtered list.
# 3) If not, deleted directory with contents inside.
__DEBUG_clean_CHDs_destDir = 0
def clean_CHDs_destDir(CHD_dic, destDir):
  print_info('[Cleaning ROMs in ROMsDest]')

  # directories_dic = { 'machine' : 'CHD_destDirectory'}
  directories_dic = {};
  for file in os.listdir(destDir):
    # if __DEBUG_clean_CHDs_destDir: print('listdir entry {0}'.format(file))
    CHD_dir_full_name = destDir + file;
    if os.path.isdir(CHD_dir_full_name):
      if __DEBUG_clean_CHDs_destDir: print('Directory {0}'.format(CHD_dir_full_name))
      directories_dic[file] = CHD_dir_full_name
  
  num_deleted_dirs = 0
  num_deleted_CHD = 0
  for CHD_dir_name in sorted(directories_dic):
    CHD_dir_full_name = directories_dic[CHD_dir_name]
    if CHD_dir_name not in CHD_dic:
      num_CHD = delete_CHD_directory(CHD_dir_full_name, __prog_option_dry_run)
      num_deleted_dirs += 1
      num_deleted_CHD += num_CHD
      print_info('<Deleted> ' + CHD_dir_full_name)
    else:
      if __DEBUG_clean_CHDs_destDir: print('CHD_dir_name {0} in filtered list'.format(CHD_dir_name))

  print_info('Deleted directories  ' + str(num_deleted_dirs))
  print_info('Deleted CHDs         ' + str(num_deleted_CHD))

def clean_NFO_destDir(destDir, __prog_option_dry_run):
  print_info('[Deleting redundant NFO files]');
  num_deletedNFO_files = 0;
  for file in os.listdir(destDir):
    if file.endswith(".nfo"):
      # Chech if there is a corresponding ROM for this NFO file
      thisFileName, thisFileExtension = os.path.splitext(file)
      romFileName_temp = thisFileName + '.zip'
      rom_file_path = destDir + romFileName_temp
      if not os.path.isfile(rom_file_path):
        nfo_file_path = destDir + file
        delete_file(nfo_file_path, __prog_option_dry_run)
        num_deletedNFO_files += 1
        print_info('<Deleted NFO> ' + file)

  print_info('Deleted ' + str(num_deletedNFO_files) + ' redundant NFO files')

def clean_ArtWork_destDir(filter_config, artwork_copy_dic, __prog_option_dry_run):
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
      thumb_file_path_dest = file + thumbsDestDir
      delete_file(thumb_file_path_dest, __prog_option_dry_run);
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
      delete_ROM_file(file, fanartDestDir, __prog_option_dry_run);
      print_info('<Deleted fanart> ' + file);

  # Print eport
  print_info('Deleted ' + str(num_cleaned_thumbs) + ' redundant thumbs');
  print_info('Deleted ' + str(num_cleaned_fanart) + ' redundant fanart');

# -----------------------------------------------------------------------------
# XML functions
# -----------------------------------------------------------------------------
def XML_read_file_ElementTree(filename, infoString):
  """Reads an XML file using Element Tree. Aborst if errors found"""
  print(infoString + " " + filename + "... ", end="")
  sys.stdout.flush()
  try:
    tree = ET.parse(filename)
  except IOError:
    print('\n')
    print('\033[31m[ERROR]\033[0m cannot find file ' + filename)
    sys.exit(10)
  print('done')
  sys.stdout.flush()

  return tree

# Reads merged MAME XML file.
# Returns an ElementTree OR cElementTree object.
def XML_read_file_cElementTree(filename, infoString):
  """Reads merged MAME XML database and returns a [c]ElementTree object"""
  print(infoString + " " + filename + "... ", end="")
  sys.stdout.flush();
  try:
    # -- Use ElementTree
    # tree = ET.parse(filename);
    # -- Use cElementTree. Much faster but extremely slow for the reduce command.
    tree = cET.parse(filename);
  except IOError:
    print('\n')
    print('\033[31m[ERROR]\033[0m cannot find file ' + filename)
    sys.exit(10)
  print('done')
  sys.stdout.flush()

  return tree;

# See http://norwied.wordpress.com/2013/08/27/307/
def indent_ElementTree_XML(elem, level=0):
  i = "\n" + level*" "
  if len(elem):
    if not elem.text or not elem.text.strip():
      elem.text = i + " "
    if not elem.tail or not elem.tail.strip():
      elem.tail = i
    for elem in elem:
      indent_ElementTree_XML(elem, level+1)
    if not elem.tail or not elem.tail.strip():
      elem.tail = i
  else:
    if level and (not elem.tail or not elem.tail.strip()):
      elem.tail = i

# -----------------------------------------------------------------------------
# Search engine and parser
# -----------------------------------------------------------------------------
# --- Global variables for parser ---
def set_parser_search_list(search_list):
  global parser_search_list;
  
  parser_search_list = search_list;

# --- Token objects ---
class literal_token:
  def __init__(self, value):
    self.value = value
    self.id = "STRING"
  def nud(self):
    return self
  # --- Actual implementation
  def exec_token(self):
    global parser_search_list;

    return self.value in parser_search_list;

def advance(id = None):
  global token
  if id and token.id != id:
    raise SyntaxError("Expected %r" % id)
  token = next()

class operator_open_par_token:
  lbp = 0
  def __init__(self):
    self.id = "OP ("
  def nud(self):
    expr = expression()
    advance("OP )")
    return expr

class operator_close_par_token:
  lbp = 0
  def __init__(self):
    self.id = "OP )"

class operator_not_token:
  lbp = 50
  def __init__(self):
    self.id = "OP NOT";
  def nud(self):
    self.first = expression(50)
    return self
  # --- Actual implementation
  def exec_token(self):
    return not self.first.exec_token();

class operator_and_token:
  lbp = 10
  def __init__(self):
    self.id = "OP AND";
  def led(self, left):
    self.first = left
    self.second = expression(10)
    return self
  # --- Actual implementation
  def exec_token(self):
    return self.first.exec_token() and self.second.exec_token();

class operator_or_token:
  lbp = 10
  def __init__(self):
    self.id = "OP OR";
  def led(self, left):
    self.first = left
    self.second = expression(10)
    return self
  # --- Actual implementation
  def exec_token(self):
    return self.first.exec_token() or self.second.exec_token();

class end_token:
  lbp = 0
  def __init__(self):
    self.id = "END TOKEN";

# ----------------------------------------------------------------------------
# Tokenizer
# ----------------------------------------------------------------------------
# jeffknupp.com/blog/2013/04/07/improve-your-python-yield-and-generators-explained/
#
# - If the body of the function contains a 'yield', then the function becames
#   a generator function. Generator functions create generator iterators, also
#   named "generators". Just remember that a generator is a special type of 
#   iterator.
#   To be considered an iterator, generators must define a few methods, one of 
#   which is __next__(). To get the next value from a generator, we use the 
#   same built-in function as for iterators: next().
def tokenize(program):
  # \s* -> Matches any number of blanks [ \t\n\r\f\v].
  # (?:...) -> A non-capturing version of regular parentheses.
  # \b -> Matches the empty string, but only at the beginning or end of a word.
  for operator, string in re.findall("\s*(?:(and|or|not|\(|\))|([\w_]+))", program):
    # print 'Tokenize >> Program -> "' + program + \
    #       '", String -> "' + string + '", Operator -> "' + operator + '"\n';
    if string:
      yield literal_token(string)
    elif operator == "and":
      yield operator_and_token()
    elif operator == "or":
      yield operator_or_token()
    elif operator == "not":
      yield operator_not_token()
    elif operator == "(":
      yield operator_open_par_token()
    elif operator == ")":
      yield operator_close_par_token()
    else:
      raise SyntaxError("Unknown operator: %r" % operator)
  yield end_token()

# ----------------------------------------------------------------------------
# Parser
# Inspired by http://effbot.org/zone/simple-top-down-parsing.htm
# ----------------------------------------------------------------------------
def expression(rbp = 0):
  global token
  t = token
  token = next()
  left = t.nud()
  while rbp < token.lbp:
    t = token
    token = next()
    left = t.led(left)
  return left

def expression_exec(rbp = 0):
  global token
  t = token
  token = next()
  left = t.nud()
  while rbp < token.lbp:
    t = token
    token = next()
    left = t.led(left)
  return left.exec_token()

def parse_exec(program):
  global token, next
  next = tokenize(program).__next__
  token = next()
  return expression_exec()
