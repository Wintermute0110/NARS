#!/usr/bin/python
# XBMC ROM utilities - MAME version
# Wintermute0110 <wintermute0110@gmail.com>

# MAME XML is written by this file:
#   http://www.mamedev.org/source/src/emu/info.c.html

import sys, os, re, shutil
import operator, argparse
# XML parser (ElementTree)
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
  configFile.MergedInfo = '';
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
        elif general_child.tag == 'MergedInfo':     configFile.MergedInfo = general_child.text;
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
          if filter_child.tag == 'source':
            if __debug_config_file_parser: print ' source = ' + filter_child.text;
            sourceDirFound = 1;
            filter_class.sourceDir = filter_child.text

          elif filter_child.tag == 'dest':
            if __debug_config_file_parser: print ' dest = ' + filter_child.text;
            destDirFound = 1;
            filter_class.destDir = filter_child.text
            
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

def parse_MAME_merged_XML():
  "Parses a MAME merged XML and creates a parent/clone list"
  filename = configuration.MergedInfo;
  print '[Parsing MAME merged XML]';
  print "Parsing MAME merged XML file '" + filename + "'...";
  tree = ET.parse(filename);
  print 'Done!';
  
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
        
      # Add new game to the list
      rom_raw_dict[romName] = romObject;
  del tree;
  print 'Total number of games = ' + str(num_games);
  print 'Number of parents = ' + str(num_parents);
  print 'Number of clones = ' + str(num_clones);

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

  print '[apply_MAME_filters]';
  
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
  print ' Removed   = ' + str(filtered_out_games);
  print ' Remaining = ' + str(len(mame_filtered_dic));

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
    print ' Removed   = ' + str(filtered_out_games);
    print ' Remaining = ' + str(len(mame_filtered_dic));
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
    print ' Removed   = ' + str(filtered_out_games);
    print ' Remaining = ' + str(len(mame_filtered_dic));
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
    print ' Removed   = ' + str(filtered_out_games);
    print ' Remaining = ' + str(len(mame_filtered_dic));
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
    print ' Removed   = ' + str(filtered_out_games);
    print ' Remaining = ' + str(len(mame_filtered_dic));
  else:
    print '[User wants Non Working games]';

  # --- Apply Driver filter
  __debug_apply_MAME_filters_Driver_tag = 0;
  if filter_config.driver is not None:
    print '[Filtering drivers]';
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
        list = filter_str.split(" ");
        if __debug_apply_MAME_filters_Driver_tag:
          print 'Filter sublist = ', list;
        if len(list) == 2:
          if list[0] == 'not':
            not_operator = 1;
            f_string = list[1];
          else:
            print 'Logical operator is not "not"';
            sys.exit(10);
        elif len(list) == 1:
          not_operator = 0;
          f_string = list[0];
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
    print ' Removed   = ' + str(filtered_out_games);
    print ' Remaining = ' + str(len(mame_filtered_dic));
  else:
    print '[User wants all drivers]';
  
  sys.exit(0);
  return mame_filtered_dic;

# rom_copy_dic = create_copy_list(mame_filtered_dic, rom_main_list);
def create_copy_list(mame_filtered_dic, rom_main_list):
  "With list of filtered ROMs and list of source ROMs, create list of files to be copied"
  __debug_create_copy_list = 1;

  print '[Creating list of ROMs to be copied/updated]';
  copy_list = [];
  for key_rom_main in rom_main_list:
    rom_name = key_rom_main;
    # If the ROM is in the mame filtered list, then add to the copy list
    if rom_name in mame_filtered_dic:
      copy_list.append(rom_name);
      if __debug_create_copy_list:
        print '[Added ROM] ' + rom_name;

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

  input_filename = "mame-0153b.xml";
  output_filename = "mame-0153b-reduced.xml";
  # input_filename = "mame-test.xml";
  # output_filename = "mame-test-reduced.xml";

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

  print 'Implement me!';
  sys.exit(10);

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

#
# Copy ROMs in destDir
#
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
    reportFileName = 'xru-mame-report.txt';
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

  # If user wants to sync...
  if 0:
    if __prog_option_sync:
      # Delete ROMs present in destDir not present in the filtered list
      for file in os.listdir(destDir):
        if file.endswith(".zip"):
          if file not in mame_filtered_dic:
            delete_ROM_file(file, destDir);
            if __conf_print_report:
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
    Takes MAME XML as input, picks the useful information, and writes and output
    XML with the "useful" information. The reason for doing this is because 
    MAME XML file is huge and takes a long time to process it. After reducing 
    it, all subsequent processing should be much quicker.

 \033[31m make-filters\033[0m
    Takes MAME XML info file, Catver.ini and nplayers.ini, and makes an
    output XML file with all the necessary information for proper game 
    filtering.

 \033[31m list-redux\033[0m
    List every ROM set system defined in the reduced MAME XML information file.
  
 \033[31m list-redux-long\033[0m
    Like list, but also list all the information.

 \033[31m copy <filterName>\033[0m
    Applies ROM filters defined in the configuration file and copies the 
    contents of sourceDir into destDir. This overwrites ROMs in destDir.

 \033[31m update <filterName>\033[0m
    Like copy, but also copies files if file size is different (this saves
    a lot of time, particularly if sourceDir and/or destDir are on a 
    network-mounted filesystem). It also  deletes ROMs in destDir not present 
    in the filtered ROM list.

\033[32mOptions:\033[0m
  \033[35m-h\033[0m, \033[35m--help\033[0m
    Print short command reference

  \033[35m--version\033[0m
    Show version and exit
    
  \033[35m--dryRun\033[0m
    Don't modify destDir at all, just print the operations to be done.

  \033[35m--printReport\033[0m
    Writes a TXT file reporting the operation of the ROM filters and the
    operations performed."""

# =============================================================================
def main(argv):
  # - Command line parser
  parser = argparse.ArgumentParser()
  parser.add_argument("--version", help="print version", action="store_true")
  parser.add_argument("--dryRun", help="don't modify any files", action="store_true")
  parser.add_argument("--printReport", help="print report", action="store_true")
  parser.add_argument("command", help="usage, reduce-XML, make-filters, list-redux, list-redux-long, copy, update")
  parser.add_argument("filterName", help="MAME ROM filter name", nargs='?')
  args = parser.parse_args();
  
  # --- Read configuration file
  global configuration; # Needed to modify global copy of globvar
  configuration = parse_File_Config(); 
  
  # --- Optional arguments
  global __prog_option_dry_run;
  global __prog_option_print_report;
  global __prog_option_sync;

  if args.dryRun:
    __prog_option_dry_run = 1;
  if args.printReport:
    __prog_option_print_report = 1;

  # --- Positional arguments
  if args.command == 'usage':
    do_printHelp();

  elif args.command == 'reduce-XML':
    do_reduce_XML();

  elif args.command == 'make-filters':
    do_make_filters();

  elif args.command == 'list-redux':
    do_list_reduced();
    
  elif args.command == 'list-redux-long':
    do_list_reducedlong();

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
