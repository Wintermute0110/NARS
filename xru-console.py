#!/usr/bin/python
# XBMC ROM utilities
# Wintermute0110 <wintermute0110@gmail.com>

import sys, os, re, shutil
import operator, argparse
import xml.etree.ElementTree as ET

# --- Global variables
__software_version = '0.1.0';
__config_configFileName = 'xru-config.xml';

# --- Program options (from command line)
__prog_option_dry_run = 0;
__prog_option_delete_NFO = 0;
__prog_option_print_report = 0;
__prog_option_sync = 0;

# --- Global DEBUG variables
__debug_propertyParsers = 0;
__debug_copy_ROM_file = 0;
__debug_main_ROM_list = 0;
__debug_filtered_ROM_list = 0;
__debug_total_filtered_ROM_list = 0;
__debug_config_file_parser = 0;

# =============================================================================
#
# Config file options
#
class ConfigFile:
  pass

#
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

# =============================================================================
def copy_ROM_file(fileName, sourceDir, destDir):
  if sourceDir[-1] != '/':
    sourceDir = sourceDir + '/';
  if destDir[-1] != '/':
    destDir = destDir + '/';

  sourceFullFilename = sourceDir + fileName;
  destFullFilename = destDir + fileName;
  
  print '[Copy] ' + fileName;
  if __debug_copy_ROM_file:
    print '  Copying ' + sourceFullFilename;
    print '  Into    ' + destFullFilename;
  
  if not __prog_option_dry_run:
    try:
      shutil.copy(sourceFullFilename, destFullFilename)
    except EnvironmentError:
      print "copy_ROM_file >> Error happened";

def update_ROM_file(fileName, sourceDir, destDir):
  if sourceDir[-1] != '/':
    sourceDir = sourceDir + '/';
  if destDir[-1] != '/':
    destDir = destDir + '/';

  sourceFullFilename = sourceDir + fileName;
  destFullFilename = destDir + fileName;
  
  existsSource = os.path.isfile(sourceFullFilename);
  existsDest = os.path.isfile(destFullFilename);
  if not existsSource:
    print "Source file not found";
    sys.exit(10);

  sizeSource = os.path.getsize(sourceFullFilename);
  if existsDest:
    sizeDest = os.path.getsize(destFullFilename);
  else:
    sizeDest = -1;

  # If sizes are equal
  if sizeSource == sizeDest:
    # Skip copy and return 1
    return 1;

  # destFile does not exist or sizes are different, copy.
  print '[Copy] ' + fileName;
  if __debug_copy_ROM_file:
    print '  Copying ' + sourceFullFilename;
    print '  Into    ' + destFullFilename;
  
  if not __prog_option_dry_run:
    try:
      shutil.copy(sourceFullFilename, destFullFilename)
    except EnvironmentError:
      print "copy_ROM_file >> Error happened";

  return 0

def delete_ROM_file(fileName, dir):
  if dir[-1] != '/':
    dir = dir + '/';

  fullFilename = dir + fileName;
  print '[Delete] ' + fileName;

  if not __prog_option_dry_run:
    try:
      os.remove(fullFilename);
    except EnvironmentError:
      print "delete_ROM_file >> Error happened";

def exists_ROM_file(fileName, dir):
  if dir[-1] != '/':
    dir = dir + '/';

  fullFilename = dir + fileName;

  return os.path.isfile(fullFilename);

def parse_File_Config(romSetName):
  "Parses config file"

  tree = ET.parse(__config_configFileName);
  root = tree.getroot();

  # - This iterates through the collections
  configFile = ConfigFile();
  configFile.romSetName = romSetName;

  # Mandatory config file options
  configFile.sourceDir = '';
  configFile.destDir = '';
  # Optional config file options (deafault to empty string)
  configFile.filterUpTags = '';
  configFile.filterDownTags = '';
  configFile.includeTags = '';
  configFile.excludeTags = '';

  systemNameFound = 0;
  sourceDirFound = 0;
  destDirFound = 0;
  print '[' + romSetName + ']';
  for collection in root:
    if collection.attrib['shortname'] == romSetName:
      systemNameFound = 1;
      for collectionEL in collection:
        if collectionEL.tag == 'source':
          print 'Source         : ' + collectionEL.text;
          sourceDirFound = 1;
          configFile.sourceDir = collectionEL.text

        elif collectionEL.tag == 'dest':
          print 'Destination    : ' + collectionEL.text;
          destDirFound = 1;
          configFile.destDir = collectionEL.text

        elif collectionEL.tag == 'filterUpTags' and collectionEL.text is not None:
          print 'filterUpTags   : ' + collectionEL.text;
          text_string = collectionEL.text;
          list = text_string.split(",");
          configFile.filterUpTags = list;

        elif collectionEL.tag == 'filterDownTags' and collectionEL.text is not None:
          print 'filterDownTags : ' + collectionEL.text;
          text_string = collectionEL.text;
          list = text_string.split(",");
          configFile.filterDownTags = list;

        elif collectionEL.tag == 'includeTags' and collectionEL.text is not None:
          print 'includeTags    : ' + collectionEL.text;
          text_string = collectionEL.text;
          list = text_string.split(",");
          configFile.includeTags = list;

        elif collectionEL.tag == 'excludeTags' and collectionEL.text is not None:
          print 'excludeTags    : ' + collectionEL.text;
          text_string = collectionEL.text;
          list = text_string.split(",");
          configFile.excludeTags = list;

  # --- Trim blank spaces on lists
  if configFile.filterUpTags is not None:
    for index, item in enumerate(configFile.filterUpTags):
      configFile.filterUpTags[index] = item.strip();

  if configFile.filterDownTags is not None:
    for index, item in enumerate(configFile.filterDownTags):
      configFile.filterDownTags[index] = item.strip();

  if configFile.includeTags is not None:
    for index, item in enumerate(configFile.includeTags):
      configFile.includeTags[index] = item.strip();

  if configFile.excludeTags is not None:
    for index, item in enumerate(configFile.excludeTags):
      configFile.excludeTags[index] = item.strip();

  if __debug_config_file_parser:
    print 'filterUpTags   :', configFile.filterUpTags;
    print 'filterDownTags :', configFile.filterDownTags;
    print 'includeTags    :', configFile.includeTags;
    print 'excludeTags    :', configFile.excludeTags;

  # --- Check for errors
  if not systemNameFound:
    print 'romSetName not found in config file';
    sys.exit(10);

  if not sourceDirFound:
    print 'source directory not found in config file';
    sys.exit(10);

  if not destDirFound:
    print 'destination directory not found in config file';
    sys.exit(10);

  return configFile;
          
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

# =============================================================================
def do_list(filename):
  "Short list of config file"

  print '===== Short listing of configuration file ====';
  print 'Config file: ' + filename;

  tree = ET.parse(filename);
  root = tree.getroot();

  # - This iterates through the collections
  for collection in root:
    # print collection.tag, collection.attrib;
    print '[ROM Collection] ';
    print '  Short name   ' + collection.attrib['shortname'];
    print '  Name         ' + collection.attrib['name'];

    # - Test if element exists by key
    source_EL = collection.find('source');
    if source_EL is not None:
      print '  Source       ' + source_EL.text;
    else:
      print 'Mandatory <source> directory not found';

    dest_EL = collection.find('dest');
    if dest_EL is not None:
      print '  Destination  ' + dest_EL.text;
    else:
      print 'Mandatory <dest> directory not found';

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
usage: xru.py [options] <command> [romSetName]

Commands:
  usage
    Print usage information (this text)

  list
    List every ROM set system defined in the configuration file and some basic
    information.
  
  list-long
    Like list, but also list all the information and filters.

  taglist
    Scan the source directory and reports the total number of ROM files, all the
    tags found, and the number of ROMs that have each tag. It also display 
    tagless ROMs.

  copy
    Applies ROM filters defined in the configuration file and copies the 
    contents of sourceDir into destDir. This overwrites ROMs in destDir.

  update
    Like update, but also delete ROMs in destDir not present in the filtered
    ROM list.

Options:
  -h, --help
    Print short command reference

  --version
    Show version and exit
    
  --dryRun
    Don't modify destDir at all, just print the operations to be done.
    
  --deleteNFO
    Delete NFO files of ROMs not present in the destination directory.

  --printReport
    Writes a TXT file reporting the operation of the ROM filters and the
    operations performed."""

# =============================================================================
def main(argv):
  print '\033[36mXBMC ROM utilities - Advanced Launcher\033[0m' + \
        ' version ' + __software_version;

  # - Command line parser
  parser = argparse.ArgumentParser()
  parser.add_argument("--version", help="print version", action="store_true")
  parser.add_argument("--dryRun", help="don't modify any files", action="store_true")
  parser.add_argument("--deleteNFO", help="delete NFO files of filtered ROMs", action="store_true")
  parser.add_argument("--printReport", help="print report", action="store_true")
  parser.add_argument("command", help="usage, list, list-long, taglist, copy, update")
  parser.add_argument("romSetName", help="ROM collection name", nargs='?')
  args = parser.parse_args();
  
  # --- Optional arguments
  # Needed to modify global copy of globvar
  global __prog_option_dry_run, __prog_option_delete_NFO, __prog_option_print_report;
  global __prog_option_sync;

  if args.dryRun:
    __prog_option_dry_run = 1;
  if args.deleteNFO:
    __prog_option_delete_NFO = 1;
  if args.printReport:
    __prog_option_print_report = 1;

  # --- Positional arguments
  if args.command == 'usage':
    do_printHelp();

  elif args.command == 'list':
    do_list(__config_configFileName);
    
  elif args.command == 'list-long':
    do_list_long(__config_configFileName);
    
  elif args.command == 'taglist':
    if args.romSetName == None:
      print 'romSetName required';
      sys.exit(10);
    configFile = parse_File_Config(args.romSetName);
    do_taglist(configFile);

  elif args.command == 'copy':
    if args.romSetName == None:
      print 'romSetName required';
      sys.exit(10);
    configFile = parse_File_Config(args.romSetName);
    do_update(configFile);

  elif args.command == 'update':
    __prog_option_sync = 1;
    if args.romSetName == None:
      print 'romSetName required';
      sys.exit(10);
    configFile = parse_File_Config(args.romSetName);
    do_update(configFile);  

  else:
    print 'Unrecognised command';

  sys.exit(0);

# No idea what's this...
if __name__ == "__main__":
  main(sys.argv[1:])
