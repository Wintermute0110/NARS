#!/usr/bin/python
# XBMC ROM utilities - MAME version
# Wintermute0110 <wintermute0110@gmail.com>

# MAME XML is written by this file:
#   http://www.mamedev.org/source/src/emu/info.c.html

import sys, os, re, shutil
import operator, argparse
import xml.etree.ElementTree as ET
# ElementTree generated XML files are nasty looking (no end of lines)
# Minidom does a much better job
from xml.dom import minidom

# --- Global variables
__config_configFileName = 'xru-mame-config.xml';

# Config file options global class (like a C struct)
class ConfigFile:
  pass
class ConfigFileFilter:
  pass
configuration = ConfigFile();

# Program options (from command line)
__prog_option_dry_run = 0;
__prog_option_print_report = 0;
__prog_option_generate_NFO = 0;
__prog_option_withArtWork = 0;
__prog_option_cleanROMs = 0;
__prog_option_sync = 0;

# --- Global DEBUG variables
__debug_propertyParsers = 0;
__debug_copy_ROM_file = 0;
__debug_main_ROM_list = 0;
__debug_filtered_ROM_list = 1;

__debug_config_file_parser = 0;
__debug_parse_MAME_XML_reading = 0;
__debug_apply_MAME_filters = 1;

# =============================================================================
# DEBUG functions
# =============================================================================
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

# =============================================================================
# Filesystem interaction functions
# =============================================================================
def copy_ArtWork_file(fileName, sourceDir, destDir):
  if sourceDir[-1] != '/':
    sourceDir = sourceDir + '/';
  if destDir[-1] != '/':
    destDir = destDir + '/';

  sourceFullFilename = sourceDir + fileName;
  destFullFilename = destDir + fileName;
  
  # Maybe artwork does not exist...
  if not os.path.isfile(sourceFullFilename):
    # Then do nothing
    return;

  print '[Copy] ' + fileName;
  if __debug_copy_ROM_file:
    print '  Copying ' + sourceFullFilename;
    print '  Into    ' + destFullFilename;
  
  if not __prog_option_dry_run:
    try:
      shutil.copy(sourceFullFilename, destFullFilename)
    except EnvironmentError:
      print "copy_ROM_file >> Error happened";

def update_ArtWork_file(fileName, sourceDir, destDir):
  if sourceDir[-1] != '/':
    sourceDir = sourceDir + '/';
  if destDir[-1] != '/':
    destDir = destDir + '/';

  sourceFullFilename = sourceDir + fileName;
  destFullFilename = destDir + fileName;
  
  existsSource = os.path.isfile(sourceFullFilename);
  existsDest = os.path.isfile(destFullFilename);
  # Maybe artwork does not exist...
  if not existsSource:
    # Then do nothing
    return 1;

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

# =============================================================================
# Misc functions
# =============================================================================
#
# A class to store the MAME parent/clone main list
#
class ROM:
  # - Constructor. Parses the ROM file name and gets Tags and Base Name (name 
  # with no tags).
  def __init__(self, name):
    self.name = name; 

def trim_list(input_list):
  for index, item in enumerate(input_list):
    input_list[index] = item.strip();

  return input_list;

def parse_File_Config():
  "Parses configuration file"

  print '[Parsing config file]';
  tree = ET.parse(__config_configFileName);
  root = tree.getroot();

  # - This iterates through the collections
  configFile = ConfigFile();

  # --- Main configuration options (default to empty string)
  configFile.MAME_XML = '';
  configFile.MAME_XML_redux = '';
  configFile.Catver = '';
  configFile.NPlayers = '';
  configFile.MergedInfo_XML = '';
  configFile.filter_dic = {};

  # --- Parse general options
  general_tag_found = 0;
  for root_child in root:
    if root_child.tag == 'General':
      general_tag_found = 1;
      for general_child in root_child:
        if general_child.tag == 'MAME_XML':         configFile.MAME_XML = general_child.text;
        elif general_child.tag == 'MAME_XML_redux': configFile.MAME_XML_redux = general_child.text;
        elif general_child.tag == 'Catver':         configFile.Catver = general_child.text;
        elif general_child.tag == 'NPlayers':       configFile.NPlayers = general_child.text;
        elif general_child.tag == 'MergedInfo':     configFile.MergedInfo_XML = general_child.text;
        else:
          print 'Unrecognised tag inside <General>';
          sys.exit(10);
  if not general_tag_found:
    print 'Configuration error. <General> tag not found';
    sys.exit(10);

  # --- Parse filters
  for root_child in root:
    if root_child.tag == 'MAMEFilter':
      if __debug_config_file_parser: print '<MAMEFilter>';
      if 'name' in root_child.attrib:
        filter_class = ConfigFileFilter();
        filter_class.name = root_child.attrib['name'];
        if __debug_config_file_parser: print ' name = ' + filter_class.name;
        sourceDirFound = 0;
        destDirFound = 0;
        for filter_child in root_child:
          if filter_child.tag == 'ROMsSource':
            if __debug_config_file_parser: print ' ROMsSource = ' + filter_child.text;
            sourceDirFound = 1;
            filter_class.sourceDir = filter_child.text

          elif filter_child.tag == 'ROMsDest':
            if __debug_config_file_parser: print ' ROMsDest = ' + filter_child.text;
            destDirFound = 1;
            filter_class.destDir = filter_child.text

          elif filter_child.tag == 'FanartSource':
            if __debug_config_file_parser: print ' FanartSource = ' + filter_child.text;
            sourceDirFound = 1;
            filter_class.fanartSourceDir = filter_child.text

          elif filter_child.tag == 'FanartDest':
            if __debug_config_file_parser: print ' FanartDest = ' + filter_child.text;
            destDirFound = 1;
            filter_class.fanartDestDir = filter_child.text

          elif filter_child.tag == 'ThumbsSource':
            if __debug_config_file_parser: print ' ThumbsSource = ' + filter_child.text;
            sourceDirFound = 1;
            filter_class.thumbsSourceDir = filter_child.text

          elif filter_child.tag == 'ThumbsDest':
            if __debug_config_file_parser: print ' ThumbsDest = ' + filter_child.text;
            destDirFound = 1;
            filter_class.thumbsDestDir = filter_child.text
            
          elif filter_child.tag == 'MainFilter':
            if __debug_config_file_parser: print ' MainFilter = ' + filter_child.text;
            text_string = filter_child.text;
            list = text_string.split(",");
            filter_class.mainFilter = trim_list(list);

          elif filter_child.tag == 'Driver':
            if __debug_config_file_parser: print ' Driver = ' + filter_child.text;
            text_string = filter_child.text;
            list = text_string.split(",");
            filter_class.driver = trim_list(list);

          elif filter_child.tag == 'MachineType':
            if __debug_config_file_parser: print ' MachineType = ' + filter_child.text;
            text_string = filter_child.text;
            list = text_string.split(",");
            filter_class.machineType = trim_list(list);

          elif filter_child.tag == 'Categories':
            if __debug_config_file_parser: print ' Categories = ' + filter_child.text;
            text_string = filter_child.text;
            if text_string != None:
              list = text_string.split(",");
              filter_class.categories = trim_list(list);
            else:
              filter_class.categories = '';
          else:
            print 'Unrecognised tag inside <MAMEFilter>';
            sys.exit(10);

        # Check for errors in this
        if not sourceDirFound:
          print 'source directory not found in config file';
          sys.exit(10);
        if not destDirFound:
          print 'destination directory not found in config file';
          sys.exit(10);

        # Aggregate filter to configuration main variable
        configFile.filter_dic[filter_class.name] = filter_class;
      else:
        print 'MAMEFilter tag does not have name attribute';
        sys.exit(10);

  if __debug_config_file_parser:
    print 'filterUpTags   :', configFile.filterUpTags;
    print '\n';

  # --- Check for errors

  return configFile;

def parse_catver_ini():
  "Parses Catver.ini and returns a"
  
  # --- Parse Catver.ini
  # --- Create a histogram with the categories
  print '[Parsing Catver.ini]';
  cat_filename = configuration.Catver;
  print ' Opening ' + cat_filename;
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
        # -Rename some categories
        final_category = main_category;
        if category == 'System / BIOS':
          final_category = 'BIOS';
        elif main_category == 'Electromechanical - PinMAME':
          final_category = 'PinMAME';
        elif main_category == 'Ball & Paddle':
          final_category = 'Ball and Paddle';
        
        # - If there is *Mature* in any category or subcategory, then
        #   the game belongs to the Mature category
        if category.find('*Mature*') >= 0:
          final_category = 'Mature';
        
        # - Create final categories dictionary
        final_categories_dic[game_name] = final_category;
    elif read_status == 2:
      break;
    else:
      print 'Unknown read_status FSM value';
      sys.exit(10);
  f.close();

  return final_categories_dic;

def parse_MAME_merged_XML():
  "Parses a MAME merged XML and creates a parent/clone list"
  filename = configuration.MergedInfo_XML;
  print '[Parsing MAME merged XML]';
  print " Parsing MAME merged XML file '" + filename + "'...";
  tree = ET.parse(filename);
  print ' Done!';
  
  # --- Raw list: literal information from the XML
  rom_raw_dict = {};
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
      romObject = ROM(romName);
      if __debug_parse_MAME_XML_reading:
        print 'game = ' + romName;

      # --- Check game attributes and create variables for filtering
      # Parent or clone
      if 'cloneof' in game_attrib:
        num_clones += 1;
        romObject.cloneof = game_attrib['cloneof'];
        romObject.isclone = 1;
        if __debug_parse_MAME_XML_reading:
          print ' Clone of = ' + game_attrib['cloneof'];
      else:
        num_parents += 1;
        romObject.isclone = 0;

      # Device and Runnable
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
      # In MAME 0.153b, when there is the attribute 'isdevice' there is also 'runnable'
      # Also, if isdevice = yes => runnable = no
      if romObject.isdevice == 1 and romObject.runnable == 1:
        print 'Found a ROM which is device and runnable';
        sys.exit(10);
      if 'isdevice' in game_attrib and 'runnable' not in game_attrib:
        print 'isdevice but NOT runnable';
        sys.exit(10);
      if 'isdevice' not in game_attrib and 'runnable' in game_attrib:
        print 'NOT isdevice but runnable';
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
          romObject.mechanical = 1;
        else:
          romObject.mechanical = 0;
      else:
        romObject.mechanical = 0; # ismechanical defaults to 0

      # Game driver
      if 'sourcefile' in game_attrib:
        # Remove the trail '.c' from driver name
        driverName = game_attrib['sourcefile'];
        driverName = driverName[:-2];
        romObject.sourcefile = driverName;
      else:
        romObject.sourcefile = 'unknown'; # sourcefile (driver) defaults to unknown

      # --- Parse child tags
      for child_game in game_EL:
        if child_game.tag == 'driver':
          driver_attrib = child_game.attrib;
          
          # Driver status is good, imperfect, preliminary
          # prelimiray games don't work or have major emulation problems
          # imperfect games are emulated with some minor issues
          # good games are perfectly emulated
          if 'status' in driver_attrib:
            romObject.driver_status = driver_attrib['status'];
            if __debug_parse_MAME_XML_reading:
              print ' Driver status = ' + driver_attrib['status'];
          else:
            romObject.driver_status = 'unknown';

        elif child_game.tag == 'category':
          romObject.category = child_game.text;
        
        # --- Copy information to generate NFO files
        elif child_game.tag == 'description':
          romObject.description = child_game.text;
        elif child_game.tag == 'year':
          romObject.year = child_game.text;
        elif child_game.tag == 'manufacturer':
          romObject.manufacturer = child_game.text;
        
      # Add new game to the list
      rom_raw_dict[romName] = romObject;
  del tree;
  print ' Total number of games = ' + str(num_games);
  print ' Number of parents = ' + str(num_parents);
  print ' Number of clones = ' + str(num_clones);

  # --- Create a parent-clone list
  # NOTE: a parent/clone hierarchy is not needed for MAME. In the ROM list
  # include a field isClone, so clones can be filtered out or not.
  # However, for NoIntro 1G1R, the parent/clone hierarchy is needed to filter
  # the sourceDir rom list.

  return rom_raw_dict;

def get_Filter_Config(filterName):
  "Returns the configuration filter object given the filter name"
  for key in configuration.filter_dic:
    if key == filterName:
      return configuration.filter_dic[key];
  
  print 'get_Filter_Config >> filter name not found in configuration file';
  sys.exit(20);

# __debug_apply_MAME_filters
def apply_MAME_filters(mame_xml_dic, filter_config):
  "Apply filters to main parent/clone dictionary"

  print '[Applying MAME filters]';
  
  # --- Default filters: remove crap
  # What is "crap"?
  # a) devices <game isdevice="yes" runnable="no"> 
  #    Question: isdevice = yes implies runnable = no? In MAME 0.153b XML yes!
  mame_filtered_dic = {};
  print '[Default filter, removing devices]';
  filtered_out_games = 0;
  for key in mame_xml_dic:
    romObject = mame_xml_dic[key];
    if romObject.isdevice:
      filtered_out_games += 1;
      continue;
    mame_filtered_dic[key] = mame_xml_dic[key];
  print ' Removed   = ' + str(filtered_out_games) + \
        ' / Remaining = ' + str(len(mame_filtered_dic));

  # --- Apply MainFilter: NoClones
  # This is a special filter, and MUST be done first.
  # Also, remove crap like chips, etc.
  if 'NoClones' in filter_config.mainFilter:
    print '[Filtering out clones]';
    mame_filtered_dic_temp = {};
    filtered_out_games = 0;
    for key in mame_filtered_dic:
      romObject = mame_filtered_dic[key];
      if not romObject.isclone:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
      else:
        filtered_out_games += 1;
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    print ' Removed   = ' + str(filtered_out_games) + \
          ' / Remaining = ' + str(len(mame_filtered_dic));
  else:
    print '[User wants clones]';


  # --- Apply MainFilter: NoSamples
  if 'NoSamples' in filter_config.mainFilter:
    print '[Filtering out games with samples]';
    mame_filtered_dic_temp = {};
    filtered_out_games = 0;
    for key in mame_filtered_dic:
      romObject = mame_filtered_dic[key];
      if romObject.hasSamples:
        filtered_out_games += 1;
      else:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    print ' Removed   = ' + str(filtered_out_games) + \
          ' / Remaining = ' + str(len(mame_filtered_dic));
  else:
    print '[User wants games with samples]';

  # --- Apply MainFilter: NoMechanical
  if 'NoMechanical' in filter_config.mainFilter:
    print '[Filtering out mechanical games]';
    mame_filtered_dic_temp = {};
    filtered_out_games = 0;
    for key in mame_filtered_dic:
      romObject = mame_filtered_dic[key];
      if romObject.mechanical:
        filtered_out_games += 1;
      else:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    print ' Removed   = ' + str(filtered_out_games) + \
          ' / Remaining = ' + str(len(mame_filtered_dic));
  else:
    print '[User wants mechanical games]';

  # --- Apply MainFilter: NoNonworking
  # http://www.mamedev.org/source/src/emu/info.c.html
  # <driver color="good" emulation="good" graphic="good" savestate="supported" sound="good" status="good"/> 
  # /* The status entry is an hint for frontend authors */
  # /* to select working and not working games without */
  # /* the need to know all the other status entries. */
  # /* Games marked as status=good are perfectly emulated, games */
  # /* marked as status=imperfect are emulated with only */
  # /* some minor issues, games marked as status=preliminary */
  # /* don't work or have major emulation problems. */
  if 'NoNonworking' in filter_config.mainFilter:
    print '[Filtering out Non Working games]';
    mame_filtered_dic_temp = {};
    filtered_out_games = 0;
    for key in mame_filtered_dic:
      romObject = mame_filtered_dic[key];
      if romObject.driver_status == 'preliminary':
        filtered_out_games += 1;
      else:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    print ' Removed   = ' + str(filtered_out_games) + \
          ' / Remaining = ' + str(len(mame_filtered_dic));
  else:
    print '[User wants Non Working games]';

  # --- Apply Driver filter
  __debug_apply_MAME_filters_Driver_tag = 0;
  if filter_config.driver is not None and filter_config.driver is not '':
    print '[Filtering Drivers]';
    mame_filtered_dic_temp = {};
    filtered_out_games = 0;
    for key in mame_filtered_dic:
      romObject = mame_filtered_dic[key];
      driverName = romObject.sourcefile;
      if __debug_apply_MAME_filters_Driver_tag:
        print 'Driver name = ' + driverName;
        print 'Filter list = ', filter_config.driver;
      # - Iterate thorugh the list of expressions of the filter
      # - Example: filter_config.driver = ['not cps1', 'not cps2', 'not cps3']
      boolean_list = [];
      for filter_str in filter_config.driver:
        fsub_list = filter_str.split(" ");
        if __debug_apply_MAME_filters_Driver_tag:
          print 'Filter sublist = ', fsub_list;
        if len(fsub_list) == 2:
          if fsub_list[0] == 'not':
            not_operator = 1;
            f_string = fsub_list[1];
          else:
            print 'Logical operator is not "not"';
            sys.exit(10);
        elif len(fsub_list) == 1:
          not_operator = 0;
          f_string = fsub_list[0];
        else:
          print 'Wrong number of tokens in Driver filter string';
          sys.exit(10);

        # Do filter
        if not_operator:
          boolResult = driverName != f_string;
        else:
          boolResult = driverName == f_string;
        boolean_list.append(boolResult);
      if __debug_apply_MAME_filters_Driver_tag:
        print 'Boolean array =', boolean_list
      # Check built in all and any functions
      # Check https://docs.python.org/2/library/functions.html#all
      # If all the items in the boolean_list are true the game is copied (not filtered)
      # If not all items are true, the game is NOT copied (filtered)
      if not all(boolean_list):
        filtered_out_games += 1;
      else:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    print ' Removed   = ' + str(filtered_out_games) + \
          ' / Remaining = ' + str(len(mame_filtered_dic));
    
  # --- Apply Categories filter
  __debug_apply_MAME_filters_Category_tag = 0;
  if hasattr(filter_config, 'categories') and \
             filter_config.categories is not None and \
             filter_config.categories is not '':
    print '[Filtering Categories]';
    mame_filtered_dic_temp = {};
    filtered_out_games = 0;
    for key in mame_filtered_dic:
      romObject = mame_filtered_dic[key];
      category_name = romObject.category;
      if __debug_apply_MAME_filters_Category_tag:
        print '[DEBUG] Category name = ' + category_name;
        print '[DEBUG] Filter list = ', filter_config.categories;
      # - Iterate thorugh the list of expressions of the filter
      boolean_list = [];
      for filter_str in filter_config.categories:
        fsub_list = filter_str.split(" ");
        # Filter name has spaces. Merge list elements 2 to end into
        # element 2
        if len(fsub_list) > 2:
          list_temp = list(fsub_list);
          fsub_list = [];
          fsub_list.append(list_temp[0]);
          fsub_list.append(' '.join(list_temp[1:]));
        if __debug_apply_MAME_filters_Category_tag:
          print '[DEBUG] Filter sublist = ', fsub_list;
        if len(fsub_list) == 2:
          if fsub_list[0] == 'not':
            not_operator = 1;
            f_string = fsub_list[1];
          else:
            print 'Logical operator is not "not"';
            sys.exit(10);
        elif len(fsub_list) == 1:
          not_operator = 0;
          f_string = fsub_list[0];
        else:
          print 'Logical error';
          sys.exit(10);

        # Do filter
        if not_operator: boolResult = category_name != f_string;
        else:            boolResult = category_name == f_string;
        boolean_list.append(boolResult);
      if __debug_apply_MAME_filters_Category_tag:
        print '[DEBUG] Boolean array =', boolean_list
      # If not all items are true, the game is NOT copied (filtered)
      if not all(boolean_list):
        filtered_out_games += 1;
        if __debug_apply_MAME_filters_Category_tag:
          print '[DEBUG] Filtered';
      else:
        mame_filtered_dic_temp[key] = mame_filtered_dic[key];
    mame_filtered_dic = mame_filtered_dic_temp;
    del mame_filtered_dic_temp;
    print ' Removed   = ' + str(filtered_out_games) + \
          ' / Remaining = ' + str(len(mame_filtered_dic));
  else:
    print '[User wants all drivers]';
  
  return mame_filtered_dic;

# rom_copy_dic = create_copy_list(mame_filtered_dic, rom_main_list);
def create_copy_list(mame_filtered_dic, rom_main_list):
  "With list of filtered ROMs and list of source ROMs, create list of files to be copied"
  __debug_create_copy_list = 0;

  print '[Creating list of ROMs to be copied/updated]';
  copy_list = [];
  num_added_roms = 0;
  for key_rom_main in rom_main_list:
    rom_name = key_rom_main;
    # If the ROM is in the mame filtered list, then add to the copy list
    if rom_name in mame_filtered_dic:
      copy_list.append(rom_name);
      num_added_roms += 1;
      if __debug_create_copy_list:
        print '[Added ROM] ' + rom_name;
  print ' Added ' + str(num_added_roms) + ' ROMs';
  
  return copy_list;

def get_ROM_main_list(sourceDir):
  "Reads sourceDir and creates a dictionary of ROMs"
  __debug_get_ROM_main_list = 0;
  
  # --- Parse sourceDir ROM list and create main ROM list
  print '[Reading ROMs in source directory]';
  romMainList_dict = {};
  for file in os.listdir(sourceDir):
    if file.endswith(".zip"):
      thisFileName, thisFileExtension = os.path.splitext(file);
      romFileName_temp = thisFileName + '.zip';
      romObject = ROM(thisFileName);
      romObject.filename = file;
      romMainList_dict[thisFileName] = romObject;
      if __debug_get_ROM_main_list:
        print romObject.name;
        print romObject.filename;

  return romMainList_dict;


# =============================================================================
def do_reduce_XML():
  "Short list of MAME XML file"

  input_filename = configuration.MAME_XML;
  output_filename = configuration.MAME_XML_redux;

  # --- Build XML output file ---
  tree_output = ET.ElementTree();
  root_output = a = ET.Element('mame');
  tree_output._setroot(root_output);

  # --- Read MAME XML input file ---
  print '===== Reducing MAME XML file ====';
  print 'NOTE: this will take a looong time...';
  print "Parsing MAME XML file '" + input_filename + "'...";
  tree = ET.parse(input_filename);
  print 'Done!';

  # --- Traverse MAME XML input file ---
  # Root element:
  #
  # <mame build="0.153 (Apr  7 2014)" debug="no" mameconfig="10">
  root = tree.getroot();
  root_output.attrib = root.attrib; # Copy mame attributes in output XML

  # Iterate through mame tag attributes (DEBUG)
  # for key in root.attrib:
  #   print ' game --', key, '->', root.attrib[key];

  # Child elements:
  #
  # <game name="005" sourcefile="segag80r.c" sampleof="005" cloneof="10yard" romof="10yard">
  #   <description>005</description>
  #   <year>1981</year>
  #   <manufacturer>Sega</manufacturer>
  # ...
  #   <input players="2" buttons="1" coins="2" service="yes">
  #     <control type="joy" ways="4"/>
  #   </input>
  # ...
  #   <driver status="imperfect" emulation="good" color="good" sound="imperfect" graphic="good" savestate="unsupported"/>
  # </game>
  # </mame>
  for game_EL in root:
    if game_EL.tag == 'game':
      game_output = ET.SubElement(root_output, 'game');
      game_output.attrib = game_EL.attrib; # Copy game attributes in output XML

      # Iterate through game tag attributes (DEBUG)
      print '[Game]'
      # for key in game_EL.attrib:
      #   print ' game --', key, '->', game_EL.attrib[key];

      # Iterate through the children of a game
      for game_child in game_EL:
        if game_child.tag == 'description':
          print ' description = ' + game_child.text;
          description_output = ET.SubElement(game_output, 'description');
          description_output.text = game_child.text;

        if game_child.tag == 'year':
          print ' year = ' + game_child.text;
          year_output = ET.SubElement(game_output, 'year');
          year_output.text = game_child.text;

        if game_child.tag == 'manufacturer':
          print ' manufacturer = ' + game_child.text;
          manufacturer_output = ET.SubElement(game_output, 'manufacturer');
          manufacturer_output.text = game_child.text;

        if game_child.tag == 'input':
          input_output = ET.SubElement(game_output, 'input');
          input_output.attrib = game_child.attrib; # Copy game attributes in output XML

          # Traverse children
          for input_child in game_child:
            if input_child.tag == 'control':
              control_output = ET.SubElement(input_output, 'control');
              control_output.attrib = input_child.attrib;

        if game_child.tag == 'driver':
          driver_output = ET.SubElement(game_output, 'driver');
          driver_output.attrib = game_child.attrib; # Copy game attributes in output XML

  # --- Write reduced output XML file
  # tree_output.write(output_filename);
  
  # --- To save memory destroy variables now
  del tree;
  
  # --- Pretty print XML output using miniDOM
  # See http://broadcast.oreilly.com/2010/03/pymotw-creating-xml-documents.html
  rough_string = ET.tostring(root_output, 'utf-8');
  reparsed = minidom.parseString(rough_string);
  # print reparsed.toprettyxml(indent="  ")
  del root_output; # Reduce memory consumption

  f = open(output_filename, "w")
  f.write(reparsed.toprettyxml(indent="  "))
  f.close()

def do_make_filters():
  "Make main MAME database ready for filtering"

  mame_redux_filename = configuration.MAME_XML_redux;
  merged_filename = configuration.MergedInfo_XML;
  
  # --- Get categories from Catver.ini
  categories_dic = parse_catver_ini();
  
  # --- Read MAME XML or reduced MAME XML and incorporate categories
  # NOTE: this piece of code is very similar to do_reduce_XML()
  # --- Build XML output file ---
  tree_output = ET.ElementTree();
  root_output = a = ET.Element('mame');
  tree_output._setroot(root_output);

  # --- Read MAME XML input file ---
  print '[Parsing (reduced) MAME XML file]';
  print ' NOTE: this may take a looong time...';
  print " Parsing MAME XML file '" + mame_redux_filename + "'...";
  tree = ET.parse(mame_redux_filename);
  print ' Done!';

  # --- Traverse MAME XML input file ---
  root = tree.getroot();
  root_output.attrib = root.attrib; # Copy mame attributes in output XML
  for game_EL in root:
    if game_EL.tag == 'game':
      game_output = ET.SubElement(root_output, 'game');
      game_output.attrib = game_EL.attrib; # Copy game attributes in output XML

      # --- Iterate through the children of a game
      for game_child in game_EL:
        if game_child.tag == 'description':
          description_output = ET.SubElement(game_output, 'description');
          description_output.text = game_child.text;

        if game_child.tag == 'year':
          year_output = ET.SubElement(game_output, 'year');
          year_output.text = game_child.text;

        if game_child.tag == 'manufacturer':
          manufacturer_output = ET.SubElement(game_output, 'manufacturer');
          manufacturer_output.text = game_child.text;

        if game_child.tag == 'input':
          # --- This information is not used yet. Don't add to the output
          #     file to save some space.
          # input_output = ET.SubElement(game_output, 'input');
          # input_output.attrib = game_child.attrib; # Copy game attributes in output XML

          # Traverse children
          for input_child in game_child:
            if input_child.tag == 'control':
              # --- This information is not used yet. Don't add to the output
              #     file to save some space.
              # control_output = ET.SubElement(input_output, 'control');
              # control_output.attrib = input_child.attrib;
              pass

        if game_child.tag == 'driver':
          driver_output = ET.SubElement(game_output, 'driver');
          # --- From here only attribute 'status' is used
          driver_attrib = {};
          driver_attrib['status'] = game_child.attrib['status'];
          driver_output.attrib = driver_attrib;

      # --- Add category element
      game_name = game_EL.attrib['name'];
      category = 'Unknown';
      if game_name in categories_dic:
        category = categories_dic[game_name];
      else:
        print '[WARNING] Category not found for ' + game_name;
      category_output = ET.SubElement(game_output, 'category');
      category_output.text = category;

  # --- To save memory destroy variables now
  del tree;
  
  # --- Write output file
  print '[Writing output file]';
  print ' ' + merged_filename;
  rough_string = ET.tostring(root_output, 'utf-8');
  reparsed = minidom.parseString(rough_string);
  del root_output; # Reduce memory consumption

  f = open(merged_filename, "w")
  f.write(reparsed.toprettyxml(indent="  "))
  f.close()  

def do_list_reduced():
  "Short list of MAME XML file"
  filename = configuration.MAME_XML_redux;
  print '[Short listing of reduced MAME XML]';
  print "Parsing reduced MAME XML file '" + filename + "'...";
  tree = ET.parse(filename);
  print 'Done!';

  # Root element (Reduced MAME XML):
  # <mame build="0.153 (Apr  7 2014)" debug="no" mameconfig="10">
  root = tree.getroot();

  # Child elements (Reduced MAME XML):
  # <game name="005" sourcefile="segag80r.c" sampleof="005" cloneof="10yard" romof="10yard">
  #   <description>005</description>
  #   <year>1981</year>
  #   <manufacturer>Sega</manufacturer>
  #   <input players="2" buttons="1" coins="2" service="yes">
  #     <control type="joy" ways="4"/>
  #   </input>
  #   <driver status="imperfect" emulation="good" color="good" sound="imperfect" graphic="good" savestate="unsupported"/>
  # </game>
  # </mame>
  num_games = 0;
  for game_EL in root:
    if game_EL.tag == 'game':
      num_games += 1;
      # Game attributes
      game_attrib = game_EL.attrib;
      print 'game = ' + game_attrib['name'];

      # Iterate through the children of a game
      for game_child in game_EL:
        if game_child.tag == 'description':
          print ' description = ' + game_child.text;

        if game_child.tag == 'year':
          print ' year = ' + game_child.text;

        if game_child.tag == 'manufacturer':
          print ' manufacturer = ' + game_child.text;
  
  print '\n';
  print 'Number of games = ' + str(num_games);

def do_list_reducedlong():
  "Long list of MAME XML file"
  filename = configuration.MAME_XML_redux;
  print '[Long listing of reduced MAME XML]';
  print "Parsing reduced MAME XML file '" + filename + "'...";
  tree = ET.parse(filename);
  print 'Done!';

  # Root element (Reduced MAME XML):
  root = tree.getroot();

  # Child elements (Reduced MAME XML):
  num_games = 0;
  for game_EL in root:
    if game_EL.tag == 'game':
      num_games += 1;
      # Game attributes
      game_attrib = game_EL.attrib;
      print 'game = ' + game_attrib['name'];

      # Iterate through the children of a game
      for game_child in game_EL:
        if game_child.tag == 'description':
          print ' description = ' + game_child.text;

        if game_child.tag == 'year':
          print ' year = ' + game_child.text;

        if game_child.tag == 'manufacturer':
          print ' manufacturer = ' + game_child.text;
  
  print '\n';
  print 'Number of games = ' + str(num_games);


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

def do_list_categories():
  "Long list of MAME XML file"
  __debug_do_list_categories = 1;
  
  # --- Parse Catver.ini
  # --- Create a histogram with the categories
  print '[List categories from Catver.ini]';
  cat_filename = configuration.Catver;
  print 'Opening ' + cat_filename;
  categories_dic = {};
  main_categories_dic = {};
  final_categories_dic = {};
  f = open(cat_filename, 'r');
  # 0 -> Looking for '[Category]' tag
  # 1 -> Reading categories
  # 2 -> Categories finished. STOP
  read_status = 0;
  for cat_line in f:
    stripped_line = cat_line.strip();
    if __debug_do_list_categories:
      print '"' + stripped_line + '"';
    if read_status == 0:
      if stripped_line == '[Category]':
        if __debug_do_list_categories:
          print 'Found [Category]';
        read_status = 1;
    elif read_status == 1:
      line_list = stripped_line.split("=");
      if len(line_list) == 1:
        read_status = 2;
        continue;
      else:
        if __debug_do_list_categories:
          print line_list;
        category = line_list[1];
        if category in categories_dic:
          categories_dic[category] += 1;
        else:
          categories_dic[category] = 1;
        # --- Sub-categories  
        sub_categories = category.split("/");
        if __debug_do_list_categories:
          print sub_categories;
        main_category = sub_categories[0].strip();
        second_category = sub_categories[0].strip();
        if main_category in main_categories_dic: 
          main_categories_dic[main_category] += 1;
        else:                          
          main_categories_dic[main_category] = 1;
          
        # NOTE: Only use the main category for filtering.
        # -Rename some categories
        final_category = main_category;
        if category == 'System / BIOS':
          final_category = 'BIOS';
        elif main_category == 'Electromechanical - PinMAME':
          final_category = 'PinMAME';
        elif main_category == 'Ball & Paddle':
          final_category = 'Ball and Paddle';
        
        # - If there is *Mature* in any category or subcategory, then
        #   the game belongs to the Mature category
        print category.find('*Mature*')
        if category.find('*Mature*') >= 0:
          final_category = 'Mature';
        
        # - Create final categories dictionary
        if final_category in final_categories_dic: 
          final_categories_dic[final_category] += 1;
        else:                          
          final_categories_dic[final_category] = 1;
    elif read_status == 2:
      break;
    else:
      print 'Unknown read_status FSM value';
      sys.exit(10);
  f.close();

  # http://stackoverflow.com/questions/613183/python-sort-a-dictionary-by-value
  print '[Raw categories]';
  sorted_propertiesDic = sorted(categories_dic.iteritems(), key=operator.itemgetter(1))
  dumpclean(sorted_propertiesDic);
  print '\n';

  print '[Main categories]';
  sorted_propertiesDic = sorted(main_categories_dic.iteritems(), key=operator.itemgetter(1))
  dumpclean(sorted_propertiesDic);
  print '\n';

  print '[Final (used) categories]';
  sorted_propertiesDic = sorted(final_categories_dic.iteritems(), key=operator.itemgetter(1))
  dumpclean(sorted_propertiesDic);

# -----------------------------------------------------------------------------
# Copy ROMs in destDir
def do_copy_ROMs(filterName):
  "Applies filter and copies ROMs into destination directory"

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_Config(filterName);
  sourceDir = filter_config.sourceDir;
  destDir = filter_config.destDir;
  # Check if source/dir exists
  if not os.path.isdir(sourceDir):
    print 'Source directory does not exist'
    print sourceDir;
    sys.exit(10);

  if not os.path.isdir(destDir):
    print 'Source directory does not exist'
    print destDir;
    sys.exit(10);

  # --- User wants to log operations performed to a file
  if __prog_option_print_report:
    reportFileName = 'xru-mame-report-' +  filter_config.name + '.txt';
    print 'Writing report into ' + reportFileName + '\n';
    report_f = open(reportFileName, 'w');

  # --- Get MAME parent/clone dictionary --------------------------------------
  mame_xml_dic = parse_MAME_merged_XML();

  # --- Create main ROM list in sourceDir -------------------------------------
  rom_main_list = get_ROM_main_list(sourceDir);

  # --- Apply filter and create list of files to be copied --------------------
  mame_filtered_dic = apply_MAME_filters(mame_xml_dic, filter_config);
  rom_copy_dic = create_copy_list(mame_filtered_dic, rom_main_list);

  # --- Copy ROMs into destDir ------------------------------------------------
  for rom_copy_item in rom_copy_dic:
    romFileName = rom_copy_item + '.zip';
    # If we are synchronising, only copy ROMs if size in sourceDir/destDir
    # is different
    if __prog_option_sync:
      retVal = update_ROM_file(romFileName, sourceDir, destDir);
      if __prog_option_print_report:
        if retVal:
          report_f.write('[Updated] ' + romFileName + '\n');
        else:
          report_f.write('[Copied] ' + romFileName + '\n');
    else:
      copy_ROM_file(romFileName, sourceDir, destDir);
      if __prog_option_print_report:
        report_f.write('[Copied] ' + romFileName + '\n');

  # Generate NFO XML files with information for launchers
  if __prog_option_generate_NFO:
    __debug_generate_NFO_files = 0;
    print '[Generating NFO files]';
    for rom_name in rom_copy_dic:
      romObj = mame_filtered_dic[rom_name];
      NFO_filename = rom_name + '.nfo';
      if destDir[-1] != '/': destDir = destDir + '/';
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
      sub_element = ET.SubElement(root_output, 'year');
      sub_element.text = romObj.year;

      # <publisher></publisher>
      sub_element = ET.SubElement(root_output, 'publisher');
      sub_element.text = romObj.manufacturer;
      
      # <genre>Shooter / Flying Vertical</genre>
      sub_element = ET.SubElement(root_output, 'genre');
      sub_element.text = romObj.category;

      # <plot></plot>
      # Probably need to merge information from history.dat or
      # mameinfo.dat
      sub_element = ET.SubElement(root_output, 'plot');
      sub_element.text = '';

      # --- Write output file
      rough_string = ET.tostring(root_output, 'utf-8');
      reparsed = minidom.parseString(rough_string);
      if __debug_generate_NFO_files:
        print '[DEBUG] Writing ' + NFO_full_filename;
      f = open(NFO_full_filename, "w")
      f.write(reparsed.toprettyxml(indent="  "))
      f.close()  
 
  # Artwork should be copied
  if __prog_option_withArtWork:
    print '[Copy/Update ArtWork]';
    fanartSourceDir = filter_config.fanartSourceDir;
    fanartDestDir = filter_config.fanartDestDir;
    thumbsSourceDir = filter_config.thumbsSourceDir;
    thumbsDestDir = filter_config.thumbsDestDir;
    for rom_copy_item in rom_copy_dic:
      romFileName = rom_copy_item + '.png';
      # If we are synchronising, only copy ROMs if size in sourceDir/destDir
      # is different
      if __prog_option_sync:
        retVal = update_ArtWork_file(romFileName, fanartSourceDir, fanartDestDir);
        if __prog_option_print_report:
          if retVal:
            report_f.write('[Updated] ' + romFileName + '\n');
          else:
            report_f.write('[Copied] ' + romFileName + '\n');
            
        retVal = update_ArtWork_file(romFileName, thumbsSourceDir, thumbsDestDir);
        if __prog_option_print_report:
          if retVal:
            report_f.write('[Updated] ' + romFileName + '\n');
          else:
            report_f.write('[Copied] ' + romFileName + '\n');            
      else:
        copy_ArtWork_file(romFileName, fanartSourceDir, fanartDestDir);
        if __prog_option_print_report:
          report_f.write('[Copied] ' + romFileName + '\n');

        copy_ArtWork_file(romFileName, thumbsSourceDir, thumbsDestDir);
        if __prog_option_print_report:
          report_f.write('[Copied] ' + romFileName + '\n');

  # If sync is on then delete unknown files.
  # Maybe this should be an option rather than a command...
  if __prog_option_cleanROMs:
    print '[Cleaning ROMs in ROMsDest]';
    # Delete ROMs present in destDir not present in the filtered list
    for file in os.listdir(destDir):
      if file.endswith(".zip"):
        basename, ext = os.path.splitext(file); # Remove extension
        if basename not in rom_copy_dic:
          delete_ROM_file(file, destDir);
          if __prog_option_print_report:
            report_f.write('[Deleted] ' + file + '\n');

  # Close log file
  if __prog_option_print_report:
    report_f.close();

def do_printHelp():
  print """\033[36mXBMC ROM utility - MAME version\033[0m

This program is design to take a full collection of MAME ROMs and some 
information files, filters this list to remove unwanted games, and updates the
ROMs in a destination dir with this filtered-list. 

Optionally, for launcher plugins, it generates a set of NFO files with game 
information and copies artwork to the appropriate directory.

For XBMC Advanced Launcher plugin, the configuration file is checked and reports
if updated are needed.

\033[32mUsage: xru-mame.py [options] <command> [filterName]\033[0m

\033[32mCommands:\033[0m
 \033[31m usage\033[0m
    Print usage information (this text)

 \033[31m reduce-XML\033[0m
    Takes MAME XML as input, picks the useful information, and writes an 
    stripped XML with only meaningful information. The reason for doing this
    is because MAME XML file is huge and takes a long time to process it. After
    reducing it, all subsequent processing should be much quicker.

 \033[31m make-filters\033[0m
    Takes MAME XML info file and Catver.ini and makes an output XML file with
    all the necessary information for proper game filtering.

 \033[31m list-redux\033[0m
    List every ROM set system defined in the reduced MAME XML information file.
  
 \033[31m list-redux-long\033[0m
    Like list, but also list all the information.

 \033[31m list-categories\033[0m
    Reads Catver.ini and makes a histogram of the categories (prints all available
    categories and tells how many ROMs every category has).

 \033[31m copy <filterName>\033[0m
    Applies ROM filters defined in the configuration file and copies the 
    contents of sourceDir into destDir. This overwrites ROMs in destDir.

 \033[31m update <filterName>\033[0m
    Like copy, but only copies files if file size is different (this saves
    a lot of time, particularly if sourceDir and/or destDir are on a 
    network-mounted filesystem).

\033[32mOptions:\033[0m
  \033[35m-h\033[0m, \033[35m--help\033[0m
    Print short command reference

  \033[35m--version\033[0m
    Show version and exit
    
  \033[35m--dryRun\033[0m
    Don't modify destDir at all, just print the operations to be done.

  \033[35m--printReport\033[0m
    Writes a TXT file reporting the operation of the ROM filters and the
    operations performed.
    
   \033[35m--generateNFO\033[0m
    Generates NFO files with game information for the launchers.

   \033[35m--withArtWork\033[0m
    Copies/Updates art work: fanart and thumbs for the launchers.
    
   \033[35m--cleanROMs\033[0m
    Deletes ROMs in destDir not present in the filtered ROM list."""

# =============================================================================
def main(argv):
  # - Command line parser
  parser = argparse.ArgumentParser() 
  parser.add_argument("--version", help="print version", action="store_true")
  parser.add_argument("--dryRun", help="don't modify any files", action="store_true")
  parser.add_argument("--printReport", help="print report", action="store_true")
  parser.add_argument("--generateNFO", help="generate NFO files", action="store_true")
  parser.add_argument("--withArtWork", help="copy/update artwork", action="store_true")
  parser.add_argument("--cleanROMs", help="clean destDir of unknown ROMs", action="store_true")
  parser.add_argument("command", help="usage, reduce-XML, make-filters, list-redux, list-redux-long, list-categories, copy, update")
  parser.add_argument("filterName", help="MAME ROM filter name", nargs='?')
  args = parser.parse_args();
  
  # --- Optional arguments
  global __prog_option_dry_run;
  global __prog_option_print_report;
  global __prog_option_generate_NFO;
  global __prog_option_withArtWork;
  global __prog_option_cleanROMs;
  global __prog_option_sync;

  if args.dryRun:      __prog_option_dry_run = 1;
  if args.printReport: __prog_option_print_report = 1;
  if args.generateNFO: __prog_option_generate_NFO = 1;
  if args.withArtWork: __prog_option_withArtWork = 1;
  if args.cleanROMs:   __prog_option_cleanROMs = 1;

  # --- Positional arguments that don't require parsing of the config file
  if args.command == 'usage':
    do_printHelp();
    sys.exit(0);

  # --- Read configuration file
  global configuration; # Needed to modify global copy of globvar
  configuration = parse_File_Config(); 

  # --- Positional arguments that required the configuration file
  if args.command == 'reduce-XML':
    do_reduce_XML();

  elif args.command == 'make-filters':
    do_make_filters();

  elif args.command == 'list-redux':
    do_list_reduced();
    
  elif args.command == 'list-redux-long':
    do_list_reducedlong();

  elif args.command == 'list-categories':
    do_list_categories();

  elif args.command == 'copy':
    if args.filterName == None:
      print 'filterName required';
      sys.exit(10);
    do_copy_ROMs(args.filterName);

  elif args.command == 'update':
    __prog_option_sync = 1;
    if args.filterName == None:
      print 'filterName required';
      sys.exit(10);
    do_copy_ROMs(args.filterName);  

  else:
    print 'Unrecognised command';
    sys.exit(1);

  sys.exit(0);

# No idea what's this...
if __name__ == "__main__":
  main(sys.argv[1:])