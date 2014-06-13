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
__prog_option_delete_NFO = 0;
__prog_option_sync = 0;

# --- Global DEBUG variables
# TODO: debug variables should be where the debug functions are, not here
# Comment them and check when the program fails
__debug_propertyParsers = 0;
__debug_copy_ROM_file = 0;
__debug_main_ROM_list = 0;
__debug_filtered_ROM_list = 0;
__debug_total_filtered_ROM_list = 0;
__debug_config_file_parser = 0;

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

# -----------------------------------------------------------------------------
def copy_ROM_list(rom_list, sourceDir, destDir):
  print_info('[Copying ROMs into destDir]');
  num_steps = len(rom_list);
  # 0 here prints [0, ..., 99%] instead [1, ..., 100%]
  step = 0;

  for rom_copy_item in rom_list:
    # Update progress
    romFileName = rom_copy_item + '.zip';
    percentage = 100 * step / num_steps;
    sys.stdout.write(' {:3d}%'.format(percentage));

    # Copy file (this function succeeds or aborts program)
    copy_ROM_file(romFileName, sourceDir, destDir);
    print_info(' <Copied> ' + romFileName);
    sys.stdout.flush()

    # Update progress
    step += 1;

def update_ROM_list(rom_list, sourceDir, destDir):
  print_info('[Updating ROMs into destDir]');
  num_steps = len(rom_list);
  # 0 here prints [0, ..., 99%] instead [1, ..., 100%]
  step = 0;

  for rom_copy_item in rom_list:
    # Update progress
    romFileName = rom_copy_item + '.zip';
    percentage = 100 * step / num_steps;
    sys.stdout.write(' {:3d}%'.format(percentage));

    # Copy file (this function succeeds or aborts program)
    ret = update_ROM_file(romFileName, sourceDir, destDir);
    if ret == 0:
      print_info(' <Copied > ' + romFileName);
    elif ret == 1:
      print_info(' <Updated> ' + romFileName);
    else:
      print_error('Wrong value returned by update_ROM_file()');
      sys.exit(10);
    sys.stdout.flush()

    # Update progress
    step += 1;

def clean_ROMs_destDir(destDir, rom_copy_dic):
  print_info('[Cleaning ROMs in ROMsDest]');

  # --- Delete ROMs present in destDir not present in the filtered list
  for file in os.listdir(destDir):
    if file.endswith(".zip"):
      basename, ext = os.path.splitext(file); # Remove extension
      if basename not in rom_copy_dic:
        delete_ROM_file(file, destDir);
        print_info(' <Deleted> ' + file);

# -----------------------------------------------------------------------------
# Configuration file functions
# -----------------------------------------------------------------------------
def parse_File_Config():
  "Parses config file"
  print_info('[Parsing config file]');
  try:
    tree = ET.parse(__config_configFileName);
  except IOError:
    pprint_error('[ERROR] cannot find file ' + __config_configFileName);
    sys.exit(10);
  root = tree.getroot();

  # --- Configuration object
  configFile = ConfigFile();
  configFile.filter_dic = {};

  # --- Parse filters
  for root_child in root:
    if root_child.tag == 'collection':
      print_verb('<collection>');
      if 'name' in root_child.attrib:
        # -- Mandatory config file options
        # filter_class.sourceDir = '';
        # filter_class.destDir = '';
        # -- Optional config file options (deafault to empty string)
        # filter_class.filterUpTags = '';
        # filter_class.filterDownTags = '';
        # filter_class.includeTags = '';
        # filter_class.excludeTags = '';
        filter_class = ConfigFileFilter();
        filter_class.name = root_child.attrib['name'];
        filter_class.shortname = root_child.attrib['shortname'];
        print_verb(' name = ' + filter_class.name);
        print_verb(' shortname = ' + filter_class.shortname);
        sourceDirFound = 0;
        destDirFound = 0;
        # - Initialise variables for the ConfigFileFilter object
        #   to avoid None objects later.
        for filter_child in root_child:
          if filter_child.tag == 'source':
            print_verb('Source         : ' + filter_child.text);
            sourceDirFound = 1;
            filter_class.sourceDir = filter_child.text

          elif filter_child.tag == 'dest':
            print_verb('Destination    : ' + filter_child.text);
            destDirFound = 1;
            filter_class.destDir = filter_child.text

          elif filter_child.tag == 'filterUpTags' and \
               filter_child.text is not None:
            print_verb('filterUpTags   : ' + filter_child.text);
            text_string = filter_child.text;
            list = text_string.split(",");
            filter_class.filterUpTags = list;

          elif filter_child.tag == 'filterDownTags' and \
               filter_child.text is not None:
            print_verb('filterDownTags : ' + filter_child.text);
            text_string = filter_child.text;
            list = text_string.split(",");
            filter_class.filterDownTags = list;

          elif filter_child.tag == 'includeTags' and \
               filter_child.text is not None:
            print_verb('includeTags    : ' + filter_child.text);
            text_string = filter_child.text;
            list = text_string.split(",");
            filter_class.includeTags = list;

          elif filter_child.tag == 'excludeTags' and \
               filter_child.text is not None:
            print_verb('excludeTags    : ' + filter_child.text);
            text_string = filter_child.text;
            list = text_string.split(",");
            filter_class.excludeTags = list;

        # - Trim blank spaces on lists
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

        # print_verb('filterUpTags   :' + filter_class.filterUpTags);
        # print_verb('filterDownTags :' + filter_class.filterDownTags);
        # print_verb('includeTags    :' + filter_class.includeTags);
        # print_verb('excludeTags    :' + filter_class.excludeTags);

        # - Check for errors in this filter
        if not sourceDirFound:
          print_error('source directory not found in config file');
          sys.exit(10);
        if not destDirFound:
          print_error('destination directory not found in config file');
          sys.exit(10);

        # - Aggregate filter to configuration main variable
        configFile.filter_dic[filter_class.name] = filter_class;
      else:
        print_error('<collection> tag does not have name attribute');
        sys.exit(10);

  return configFile;

def get_Filter_Config(filterName):
  "Returns the configuration filter object given the filter name"
  for key in configuration.filter_dic:
    if key == filterName:
      return configuration.filter_dic[key];
  
  print_error('get_Filter_Config >> filter ' + filterName + 'not found in configuration file');
  sys.exit(20);

# -----------------------------------------------------------------------------
# Miscellaneous functions
# -----------------------------------------------------------------------------
# A class to store the source directory ROM list
#
class ROM:
  # - Constructor. Parses the ROM file name and gets Tags and Base Name (name 
  # with no tags).
  def __init__(self, romFileName):
    self.romFileName = romFileName;
    self.romTags = self.get_ROM_tags(romFileName);
    self.romBaseName = self.get_ROM_baseName(romFileName);
    self.score = 0;

  # - See extract_ROM_Properties_All() for reference
  def get_ROM_tags(self, romFileName):
    romProperties_raw = [];
    romProperties_raw = re.findall("(\([^\(]*\))", romFileName);
    romProperties_all = [];
    for property in romProperties_raw:
      property = property[1:-1]; # Strip parenthesis
      
      match = re.search(",", property);
      if match:
        subProperties = re.findall("([^\,]*)", property);
        for subPropertie in subProperties:
          if subPropertie:
            subPropertieOK = subPropertie.strip();
            romProperties_all.append(subPropertieOK);
      else:
        romProperties_all.append(property);

    return romProperties_all;

  def get_ROM_baseName(self, romFileName):
    rom_baseName = '';
    regSearch = re.search("[^\(\)]*", romFileName);
    if regSearch == None:
      print 'Logical error';
      sys.exit(10);
    regExp_result = regSearch.group();
    return regExp_result.strip();

  def scoreROM(self, upTag_list, downTag_list):
    self.score = 0;

    # Iterate through the tags, and add/subtract points depending on the list
    # of given tags.
    for tag in self.romTags:
      # Up tags increase score
      for upTag in upTag_list:
        if tag == upTag:
          self.score += 1;
      # Down tags decrease the score
      for downTag in downTag_list:
        if tag == downTag:
          self.score -= 1;

  def isTag(self, tag_list):
    result = 0;

    for tag in self.romTags:
      for testTag in tag_list:
        if tag == testTag:
          result = 1;
          return result;

    return result;

def extract_ROM_Properties_Raw(romFileName):
  "Given a ROM file name extracts all the tags and returns a list"

  romProperties_raw = [];
  romProperties_raw = re.findall("(\([^\(]*\))", romFileName);

  # Debug print
  if __debug_propertyParsers:
    print 'extract_ROM_Properties_Raw >> Property list';
    print '\n'.join(romProperties_raw);
    print '\n'
  
  return romProperties_raw;

def extract_ROM_Properties_All(romFileName):
  "Given a ROM file name extracts all the tags and returns a list. Also parses tags"

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

# -----------------------------------------------------------------------------
# Main body functions
# -----------------------------------------------------------------------------
def do_list():
  "Short list of configuration file"

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
    print_info(' Short name      ' + collection.attrib['shortname']);
    print_info(' Name            ' + collection.attrib['name']);

    # - For every collection, iterate over the elements
    # - This is not very efficient
    for collectionEL in collection:
      if collectionEL.tag == 'source':
        print_verb(' Source          ' + collectionEL.text);
      elif collectionEL.tag == 'dest':
        print_verb(' Destination     ' + collectionEL.text);
      elif collectionEL.tag == 'filterUpTags' and collectionEL.text is not None:
        print_verb(' filterUpTags    ' + collectionEL.text);
      elif collectionEL.tag == 'filterDownTags' and collectionEL.text is not None:
        print_verb(' filterDownTags  ' + collectionEL.text);
      elif collectionEL.tag == 'includeTags' and collectionEL.text is not None:
        print_verb(' includeTags     ' + collectionEL.text);
      elif collectionEL.tag == 'excludeTags' and collectionEL.text is not None:
        print_verb(' excludeTags     ' + collectionEL.text);

    # - Test if element exists by key
    source_EL = collection.find('source');
    if source_EL is not None:
      print_info(' Source          ' + source_EL.text);
    else:
      print_info(' Mandatory <source> directory not found');

def do_list_long(filename):
  "Long list of config file"

  print '===== Long listing of configuration file ====';
  print 'Config file: ' + filename;

  tree = ET.parse(filename);
  root = tree.getroot();

  # - This iterates through the collections
  for collection in root:
    # print collection.tag, collection.attrib;
    print '[ROM Collection] ';
    print '  Short name      ' + collection.attrib['shortname'];
    print '  Name            ' + collection.attrib['name'];

    # - For every collection, iterate over the elements
    # - This is not very efficient
    for collectionEL in collection:
      if collectionEL.tag == 'source':
        print '  Source          ' + collectionEL.text;
      elif collectionEL.tag == 'dest':
        print '  Destination     ' + collectionEL.text;
      elif collectionEL.tag == 'filterUpTags' and collectionEL.text is not None:
        print '  filterUpTags    ' + collectionEL.text;
      elif collectionEL.tag == 'filterDownTags' and collectionEL.text is not None:
        print '  filterDownTags  ' + collectionEL.text;
      elif collectionEL.tag == 'includeTags' and collectionEL.text is not None:
        print '  includeTags     ' + collectionEL.text;
      elif collectionEL.tag == 'excludeTags' and collectionEL.text is not None:
        print '  excludeTags     ' + collectionEL.text;

def do_taglist(configFile):
  "Documentation of do_taglist() function"

  folderName = configFile.sourceDir;

  # Check if dest directory exists
  if not os.path.isdir(folderName):
    print 'Source directory does not exist'
    print folderName;
    sys.exit(10);

  # Traverse directory, for every file extract properties, and add them to the
  # dictionary.
  propertiesDic = {};
  for file in os.listdir(folderName):
    if file.endswith(".zip"):
      # print file;
      romProperties = extract_ROM_Properties_All(file);
      if len(romProperties) == 0:
        print file + 'Has no tags!';
        sys.exit(10);
      else:
        for property in romProperties:
          if propertiesDic.has_key(property):
            propertiesDic[property] += 1;
          else:
            propertiesDic[property] = 1;

  # http://stackoverflow.com/questions/613183/python-sort-a-dictionary-by-value
  sorted_propertiesDic = sorted(propertiesDic.iteritems(), key=operator.itemgetter(1))

  dumpclean(sorted_propertiesDic);

#
# Update ROMs in destDir
#
def do_update(configFile):
  "Applies filter and updates (copies) ROMs"

  # - Mandatory config file options
  sourceDir = configFile.sourceDir;
  destDir = configFile.destDir;
  # - Optional config file options (deafault to empty string)
  upTag_list = configFile.filterUpTags;
  downTag_list = configFile.filterDownTags;
  includeTag_list = configFile.includeTags;
  excludeTag_list = configFile.excludeTags;

  # User wants to log operations performed to a file
  if __prog_option_print_report:
    reportFileName = 'xru-' + configFile.romSetName + '.txt';
    print '[Writing report into ' + reportFileName + ']';
    report_f = open(reportFileName, 'w');
  
  # Check if dest directory exists
  if not os.path.isdir(sourceDir):
    print 'Source directory does not exist'
    print sourceDir;
    sys.exit(10);

  if not os.path.isdir(destDir):
    print 'Source directory does not exist'
    print destDir;
    sys.exit(10);

  # Parse sourceDir ROM list and extract tags and base names. Create main ROM list
  # Give scores to main ROM list based on filters
  print '[Reading ROMs in source dir]';
  romMainList_dict = {};
  num_ROMs_sourceDir = 0;
  for file in os.listdir(sourceDir):
    if file.endswith(".zip"):
      num_ROMs_sourceDir += 1;
      romObject = ROM(file);
      romObject.scoreROM(upTag_list, downTag_list);
      romMainList_dict[file] = romObject;
  print ' Found', str(num_ROMs_sourceDir), 'ROMs';

  # --- DEBUG main ROM list
  if __debug_main_ROM_list:
    print "========== Main ROM list (with scores) ==========";
    for key in romMainList_dict:
      romObject = romMainList_dict[key];
      print '----- ' + romObject.romFileName + ' ----- '; # ROM file name
      print "  Tags     : " + str(romObject.romTags).translate(None, "'") # Tags
      print "  Base name: '" + romObject.romBaseName + "'"; # Base name
      print "  Score    : " + str(romObject.score); # Score
    print "\n";

  # Pick ROMs with highest scores among ROMs with same Base Name
  # Algol: iterate the main ROM list. Create a dictionary with key the base
  # names and values the ROM file name.
  print '[Filtering ROMs]';
  highScoreUniqueRoms = {};
  highScoreUniqueRoms_scores = {};
  for key in romMainList_dict:
    romObject = romMainList_dict[key];
    key_string = romObject.romBaseName;
    if key_string in highScoreUniqueRoms:
      # Check if current object has highest score than stored one
      scoreCurrent = romObject.score;
      scoreStored = highScoreUniqueRoms_scores[key_string];
      if scoreCurrent > scoreStored:
        highScoreUniqueRoms[key_string] = romObject.romFileName;
        highScoreUniqueRoms_scores[key_string] = romObject.score;
    else:
      highScoreUniqueRoms[key_string] = romObject.romFileName;
      highScoreUniqueRoms_scores[key_string] = romObject.score;

  # --- DEBUG filtered ROM list
  if __debug_filtered_ROM_list:
    print "========== Filtered ROM list ==========";
    for key in highScoreUniqueRoms:
      print key, highScoreUniqueRoms[key], highScoreUniqueRoms_scores[key];
    print "\n";

  # Apply include/exclude filters. Exclude filter is applied first (if a ROM
  # contains a excluded tag remove, unless it also has an included tag)
  uniqueAndFilteredRoms = [];
  for key in highScoreUniqueRoms:
    romFileName = highScoreUniqueRoms[key];
    romObject = romMainList_dict[romFileName];
    has_excluded_tag = romObject.isTag(excludeTag_list);
    has_included_tag = romObject.isTag(includeTag_list);
    includeThisROM = 1;
    if has_excluded_tag and not has_included_tag:
      includeThisROM = 0;

    if includeThisROM:
      uniqueAndFilteredRoms.append(romFileName);
  print ' After filtering there are', str(len(uniqueAndFilteredRoms)), 'ROMs';

  # --- DEBUG filtered ROM list
  if __debug_total_filtered_ROM_list:
    print "========== Total filtered ROM list ==========";
    for romFileName in uniqueAndFilteredRoms:
      print romFileName;
    print "\n";

  # --- Copy filtered files into destDir
  # NOTE: use this function copy_ROM_list(rom_list, sourceDir, destDir):
  # Don't want complex code here!
  if __prog_option_sync: 
    print '[Updating ROMs]';
    num_checked_ROMs = 0;
    num_copied_ROMs = 0;
    for romFileName in uniqueAndFilteredRoms:
      # If we are synchronising, only copy ROMs if size in sourceDir/destDir
      # is different
      retVal = update_ROM_file(romFileName, sourceDir, destDir);
      if retVal: num_checked_ROMs += 1;
      else:      num_copied_ROMs += 1;
      if __prog_option_print_report:
        if retVal:
          report_f.write('[Updated] ' + romFileName + '\n');
        else:
          report_f.write('[Copied] ' + romFileName + '\n');
    print ' Checked', str(num_checked_ROMs), 'ROMs';
    print ' Copied', str(num_copied_ROMs), 'ROMs';
  else: 
    print '[Copying ROMs]';
    num_copied_ROMs = 0;
    for romFileName in uniqueAndFilteredRoms:
      copy_ROM_file(romFileName, sourceDir, destDir);
      num_copied_ROMs += 1;
      if __prog_option_print_report:
        report_f.write('[Copied] ' + romFileName + '\n');
    print ' Copied', str(num_copied_ROMs), 'ROMs';

  # --- Delete NFO files of ROMs not present in the destination directory.
  if __prog_option_delete_NFO:
    print '[Deleting redundant NFO files]';
    num_deletedNFO_files = 0;
    for file in os.listdir(destDir):
      if file.endswith(".nfo"):
        # Chech if there is a corresponding ROM for this NFO file
        thisFileName, thisFileExtension = os.path.splitext(file);
        romFileName_temp = thisFileName + '.zip';
        if not exists_ROM_file(romFileName_temp, destDir):
          delete_ROM_file(file, destDir);
          num_deletedNFO_files += 1;
          if __prog_option_print_report:
            report_f.write('[Deleted NFO] ' + file + '\n');
    print ' Deleted', str(num_deletedNFO_files), 'redundant NFO files';

  # --- Update command deletes redundant ROMs
  if __prog_option_sync:
    print '[Deleting filtered out/redundant ROMs in destination directory]';
    # Delete ROMs present in destDir not present in the filtered list
    num_deletedROMs_files = 0;
    for file in os.listdir(destDir):
      if file.endswith(".zip"):
        if file not in uniqueAndFilteredRoms:
          delete_ROM_file(file, destDir);
          num_deletedROMs_files += 1;
          if __prog_option_print_report:
            report_f.write('[Deleted] ' + file + '\n');
    print ' Deleted', str(num_deletedROMs_files), 'filtered out/redundant ROMs';

  # Close log file
  if __prog_option_print_report:
    report_f.close();

def do_printHelp():
  print """
\033[32mUsage: xru-console.py [options] <command> [romSetName]\033[0m

\033[32mCommands:\033[0m
 \033[31m usage\033[0m
    Print usage information (this text)

 \033[31m list\033[0m
    List every ROM set system defined in the configuration file and some basic
    information. Use \033[35m--verbose\033[0m to get more information.

 \033[31m taglist\033[0m
    Scan the source directory and reports the total number of ROM files, all the
    tags found, and the number of ROMs that have each tag. It also display 
    tagless ROMs.

 \033[31m copy\033[0m
    Applies ROM filters defined in the configuration file and copies the 
    contents of sourceDir into destDir. This overwrites ROMs in destDir.

 \033[31m update\033[0m
    Like update, but also delete ROMs in destDir not present in the filtered
    ROM list.

\033[32mOptions:
  \033[35m-h\033[0m, \033[35m--help\033[0m
    Print short command reference
    
  \033[35m-v\033[0m, \033[35m--verbose\033[0m
    Print more information about what's going on

  \033[35m-l\033[0m, \033[35m--log\033[0m
    Save program output in xru-console-log.txt

  \033[35m--dryRun\033[0m
    Don't modify destDir at all, just print the operations to be done.

  \033[35m--deleteNFO\033[0m
    Delete NFO files of ROMs not present in the destination directory.

  \033[35m--printReport\033[0m
    Writes a TXT file reporting the operation of the ROM filters and the
    operations performed."""

# -----------------------------------------------------------------------------
# main function
# -----------------------------------------------------------------------------
def main(argv):
  print '\033[36mXBMC ROM utilities - Console ROMs\033[0m' + \
        ' version ' + __software_version;

  # --- Command line parser
  parser = argparse.ArgumentParser()
  parser.add_argument('-v', '--verbose', help="print version", action="store_true")
  parser.add_argument("--log", help="print version", action="store_true")
  parser.add_argument("--dryRun", help="don't modify any files", action="store_true")
  parser.add_argument("--deleteNFO", help="delete NFO files of filtered ROMs", action="store_true")
  parser.add_argument("--printReport", help="print report", action="store_true")
  parser.add_argument("command", help="usage, list, taglist, copy, update")
  parser.add_argument("romSetName", help="ROM collection name", nargs='?')
  args = parser.parse_args();

  # --- Optional arguments
  # Needed to modify global copy of globvar
  global __prog_option_verbose, __prog_option_log;
  global __prog_option_dry_run, __prog_option_delete_NFO;
  global __prog_option_sync;

  if args.verbose:
    __prog_option_verbose = 1;
    change_log_level(Log.verb);
  if args.log:
    __prog_option_log = 1;
  if args.dryRun:
    __prog_option_dry_run = 1;
  if args.deleteNFO:
    __prog_option_delete_NFO = 1;
  if args.printReport:
    __prog_option_print_report = 1;

  # --- Positional arguments that don't require parsing of the config file
  if args.command == 'usage':
    do_printHelp();
    sys.exit(0);

  # --- Read configuration file
  global configuration;
  configuration = parse_File_Config();

  # --- Positional arguments
  # TODO: merge list and list-long into one function, list. list-long
  # is list with --verbose switch.
  if args.command == 'list':
    do_list();
    
  elif args.command == 'list-long':
    do_list_long();
    
  elif args.command == 'taglist':
    if args.romSetName == None:
      print 'romSetName required';
      sys.exit(10);
    do_taglist(configFile);

  elif args.command == 'copy':
    if args.romSetName == None:
      print 'romSetName required';
      sys.exit(10);
    do_update(configFile);

  elif args.command == 'update':
    __prog_option_sync = 1;
    if args.romSetName == None:
      print 'romSetName required';
      sys.exit(10);
    do_update(configFile);  

  else:
    pprint(Log.error, 'Unrecognised command');

  sys.exit(0);

# No idea what's this...
if __name__ == "__main__":
  main(sys.argv[1:])
