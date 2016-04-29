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
import sys, os, re, shutil
import operator, argparse
import xml.etree.ElementTree as ET
import NARS

# --- Global variables ---
__config_configFileName = 'nars-mame-config.xml'
__config_logFileName    = 'nars-mame-log.txt'

# --- Program options (from command line)
__prog_option_log = 0
__prog_option_log_filename = __config_logFileName
__prog_option_dry_run = 0
__prog_option_clean_ROMs = 0
__prog_option_generate_NFO = 0
__prog_option_clean_NFO = 0
__prog_option_clean_ArtWork = 0
__prog_option_clean_CHD = 0
__prog_option_sync = 0

# -----------------------------------------------------------------------------
# Configuration file stuff
# -----------------------------------------------------------------------------
# --- Config file options global class (like a C struct) ---
class ConfigFile:
  def __init__(self):
    self.MAME_XML       = ''
    self.MAME_XML_redux = ''
    self.MergedInfo_XML = ''
    self.Catver         = ''
    self.Genre          = ''
    self.MachineSwap    = {}
    self.filter_dic     = {}

class ConfigFileFilter:
  def __init__(self):
    # By default things are None, which means user didn't wrote them in config
    # file OR no text was written ('', or blanks (spaces, tabs)).
    self.name              = None
    # Directory names
    self.sourceDir         = None
    self.destDir           = None
    self.sourceDir_CHD     = None
    self.fanartSourceDir   = None
    self.fanartDestDir     = None
    self.thumbsSourceDir   = None
    self.thumbsDestDir     = None
    self.samplesSourceDir  = None
    self.samplesDestDir    = None
    # Filters
    self.includeFilter     = None
    self.excludeFilter     = None
    self.driverFilter      = None
    self.categoriesFilter  = None
    self.displayTypeFilter = None
    self.orientationFilter = None
    self.controlsFilter    = None
    self.buttons_exp       = None
    self.players_exp       = None
    self.year_exp          = None
    # Options
    self.year_YearExpansion_opt = 0
    self.MachineSwap = {}

# Parses configuration file using ElementTree
# Returns a ConfigFile object
parse_rjust = 16
def parse_File_Config():
  NARS.print_info('[Parsing config file]')
  tree = NARS.XML_read_file_ElementTree(__config_configFileName, "Reading configuration XML file")
  root = tree.getroot()

  # --- Configuration object returned ---
  configFile = ConfigFile()

  # --- Parse filters ---
  for root_child in root:
    # === Parse global tags ===
    if root_child.tag == 'MAME_XML':
      configFile.MAME_XML = root_child.text
      NARS.print_debug('MAME_XML       = ' + root_child.text)
    elif root_child.tag == 'MAME_XML_redux':
      configFile.MAME_XML_redux = root_child.text
      NARS.print_debug('MAME_XML_redux = ' + root_child.text)
    elif root_child.tag == 'Merged_XML':
      configFile.MergedInfo_XML = root_child.text
      NARS.print_debug('Merged_XML     = ' + root_child.text)
    elif root_child.tag == 'Catver':
      configFile.Catver = root_child.text
      NARS.print_debug('Catver         = ' + root_child.text)
    elif root_child.tag == 'Genre':
      configFile.Genre = root_child.text
      NARS.print_debug('Genre          = ' + root_child.text)
    elif root_child.tag == 'MachineSwap':
      (name_A, name_B) = parse_tag_MachineSwap(root_child.text)
      configFile.MachineSwap[name_A] = name_B
      NARS.print_debug('MachineSwap    = ' + name_A + " --> " + name_B)

    # === Parse filter ===
    elif root_child.tag == 'MAMEFilter':
      NARS.print_debug('<MAMEFilter>')
      if 'name' not in root_child.attrib:
        NARS.print_error('[ERROR] <MAMEFilter> tag does not have name attribute')
        sys.exit(10)
      NARS.print_debug(' name = ' + root_child.attrib['name'])
      filter_class = ConfigFileFilter()
      filter_class.name = root_child.attrib['name']
      sourceDirFound = 0
      destDirFound = 0
      for filter_child in root_child:
        if filter_child.tag == 'ROMsSource':
          NARS.print_debug(' ROMsSource = ' + filter_child.text)
          sourceDirFound = 1
          filter_class.sourceDir = fix_directory_name(filter_child.text)
        elif filter_child.tag == 'ROMsDest':
          NARS.print_debug(' ROMsDest = ' + filter_child.text)
          destDirFound = 1
          filter_class.destDir = fix_directory_name(filter_child.text)
        elif filter_child.tag == 'CHDsSource':
          NARS.print_debug(' CHDsSource = ' + filter_child.text)
          filter_class.sourceDir_CHD = fix_directory_name(filter_child.text)
        elif filter_child.tag == 'FanartSource':
          NARS.print_debug(' FanartSource = ' + filter_child.text)
          filter_class.fanartSourceDir = fix_directory_name(filter_child.text)
        elif filter_child.tag == 'FanartDest':
          NARS.print_debug(' FanartDest = ' + filter_child.text)
          filter_class.fanartDestDir = fix_directory_name(filter_child.text)
        elif filter_child.tag == 'ThumbsSource':
          NARS.print_debug(' ThumbsSource = ' + filter_child.text)
          filter_class.thumbsSourceDir = fix_directory_name(filter_child.text)
        elif filter_child.tag == 'ThumbsDest':
          NARS.print_debug(' ThumbsDest = ' + filter_child.text)
          filter_class.thumbsDestDir = fix_directory_name(filter_child.text)
        elif filter_child.tag == 'SamplesSource':
          NARS.print_debug(' SamplesSource = ' + filter_child.text)
          filter_class.samplesSourceDir = fix_directory_name(filter_child.text)
        elif filter_child.tag == 'SamplesDest':
          NARS.print_debug(' SamplesDest = ' + filter_child.text)
          filter_class.samplesDestDir = fix_directory_name(filter_child.text)
        elif filter_child.tag == 'Include':
          if filter_child.text is not None:
            NARS.print_debug(' Include = ' + filter_child.text)
            filter_class.includeFilter = trim_list(filter_child.text.split(","))
        elif filter_child.tag == 'Exclude':
          if filter_child.text is not None:
            NARS.print_debug(' Exclude = ' + filter_child.text)
            filter_class.excludeFilter = trim_list(filter_child.text.split(","))
        elif filter_child.tag == 'Driver':
          if filter_child.text is not None:
            NARS.print_debug(' Driver = ' + filter_child.text)
            filter_class.driverFilter = filter_child.text
        elif filter_child.tag == 'Categories':
          if filter_child.text is not None:
            NARS.print_debug(' Categories = ' + filter_child.text)
            filter_class.categoriesFilter = filter_child.text
        elif filter_child.tag == 'DisplayType':
          if filter_child.text is not None:
            NARS.print_debug(' DisplayType = ' + filter_child.text)
            filter_class.displayTypeFilter = filter_child.text
        elif filter_child.tag == 'DisplayOrientation':
          if filter_child.text is not None:
            NARS.print_debug(' DisplayOrientation = ' + filter_child.text)
            filter_class.orientationFilter = filter_child.text
        elif filter_child.tag == 'Controls':
          if filter_child.text is not None:
            NARS.print_debug(' Controls = ' + filter_child.text)
            filter_class.controlsFilter = filter_child.text
        elif filter_child.tag == 'Buttons':
          if filter_child.text is not None:
            NARS.print_debug(' Buttons = ' + filter_child.text)
            filter_class.buttons_exp = filter_child.text
        elif filter_child.tag == 'Players':
          if filter_child.text is not None:
            NARS.print_debug(' Players = ' + filter_child.text)
            filter_class.players_exp = filter_child.text
        elif filter_child.tag == 'Years':
          if filter_child.text is not None:
            NARS.print_debug(' Years = ' + filter_child.text)
            filter_class.year_exp = filter_child.text
        elif filter_child.tag == 'YearsOpts':
          if filter_child.text is not None:
            NARS.print_debug(' YearsOpts = ' + filter_child.text)
            yearOpts_list = trim_list(filter_child.text.split(","))
            for option in yearOpts_list:
              # Only one option supported at the moment
              if option == 'YearExpansion':
                filter_class.year_YearExpansion = 1
              else:
                NARS.print_error('Unknown option ' + option + 'inside <YearsOpts>')
                sys.exit(10)
        elif filter_child.tag == 'MachineSwap':
          (name_A, name_B) = parse_tag_MachineSwap(filter_child.text)
          filter_class.MachineSwap[name_A] = name_B
          NARS.print_debug(' MachineSwap    = ' + name_A + " --> " + name_B)
        else:
          NARS.print_error('[ERROR] Inside <MAMEFilter> named \'{0}\''.format(filter_class.name))
          NARS.print_error('[ERROR] Unrecognised tag <{0}>'.format(filter_child.tag))
          sys.exit(10)
      # --- Check for errors in this filter ---
      if not sourceDirFound:
        NARS.print_error('[ERROR] ROMsSource directory not found in config file')
        sys.exit(10)
      if not destDirFound:
        NARS.print_error('[ERROR] ROMsDest directory not found in config file')
        sys.exit(10)
      # --- Add filter class to configuration dictionary of filters ---
      configFile.filter_dic[filter_class.name] = filter_class
  
  # ~~~ Check for configuration errors ~~~
  if configFile.MAME_XML is None:
    NARS.print_error('[ERROR] <MAME_XML> tag not found or empty.')
    sys.exit(10)
  if configFile.MAME_XML_redux is None:
    NARS.print_error('[ERROR] <MAME_XML_redux> tag not found or empty.')
    sys.exit(10)
  if configFile.MergedInfo_XML is None:
    NARS.print_error('[ERROR] <MergedInfo_XML> tag not found or empty.')
    sys.exit(10)

  return configFile

def get_Filter_from_Config(filterName):
  "Returns the configuration filter object given the filter name"
  for key in configuration.filter_dic:
    if key == filterName:
      return configuration.filter_dic[key]

  NARS.print_error('get_Filter_from_Config >> filter ' + filterName + ' not found in configuration file')
  sys.exit(20)

# -----------------------------------------------------------------------------
# Misc functions
# -----------------------------------------------------------------------------
# A class to store the MAME machine information.
# Machine.name            string  machine name (<machine name="">)
# Machine.cloneof         string  clone name (<machine cloneof="">)
# Machine.isclone         bool
# Machine.isdevice        bool
# Machine.runnable        bool
# Machine.sampleof        string 
# Machine.hasSamples      bool
# Machine.isMechanical    bool
# Machine.isBIOS          bool
# Machine.sourcefile      string
# Machine.driver_status   string
# Machine.category        string
# Machine.buttons         string
# Machine.players         string
# Machine.coins           string
# Machine.hascoins        bool
# Machine.hasROMs         bool
# Machine.control_type    string_list
# Machine.BIOS_depends    string_list
# Machine.device_depends  string_list
# Machine.CHD_depends     string_list
# Machine.description     string
# Machine.year            string
# Machine.manufacturer    string
class Machine:
  def __init__(self):
    # XML Machine attributes
    self.name         = None
    self.cloneof      = None
    self.isClone      = False
    self.isParent     = True
    self.isDevice     = False
    self.isRunnable   = True
    self.isMechanical = False
    self.isBIOS       = False
    self.sampleof     = None
    self.hasSamples   = False
    self.sourcefile   = None
    # XML Machine tags
    self.description       = None   # str
    self.year              = None   # str
    self.manufacturer      = None   # str
    self.driver_status     = None   # str
    self.isWorking         = True   # bool
    self.category          = None   # str
    self.buttons           = 0      # int
    self.players           = 0      # int
    self.coins             = 0      # int
    self.hasCoinSlot       = False  # bool
    self.control_type_list = []     # str list
    # Custom <NARS> attributes
    self.hasROMs           = True   # bool
    self.hasSoftwareLists  = False  # bool
    self.displayType       = None   # str
    self.orientation       = None   # str
    # Custom <NARS> tags
    self.BIOS_depends_list   = []  # str list
    self.device_depends_list = []  # str list
    self.CHD_depends_list    = []  # str list

# Parses machine swaps in configuration filter, like <MachineSwap>tmnt --> tmnt2po</MachineSwap>
# Returns a tuple with the first machine (original name) and the second machine (swapped).
def parse_tag_MachineSwap(tag_text):
  raw_str = re.split('-->', tag_text)
  stripped_tuple = (raw_str[0].strip(), raw_str[1].strip())
  # print(stripped_tuple)
  
  return stripped_tuple

# Adds a trailing '/' to directory names if not already present
def fix_directory_name(dirName_str):
  if dirName_str[-1] != '/':
    dirName_str = dirName_str + '/'
    
  return dirName_str

def add_to_histogram(key, hist_dic):
  if key in hist_dic:
    hist_dic[key] += 1
  else:
    hist_dic[key] = 1

  return hist_dic

# Removes trailing '.c' or '.cpp' from string
#
# Returns the trimmed string
def trim_driver_string(driver_str):
  # Check that string does not containg weird characters
  pattern = re.compile(r'\\/,')
  if pattern.findall(driver_str):
    print('Driver string contains weird characters ' + driver_str)
    sys.exit(10)

  # If driver name ends in .c, for example cps1.c, then trim .c
  if driver_str[-2:] == '.c':
    old_driver_str = driver_str
    driver_str = old_driver_str[:-2]
  # If driver name ends in .cpp, for example cps2.cpp, then trim .cpp
  elif driver_str[-4:] == '.cpp':
    old_driver_str = driver_str
    driver_str = old_driver_str[:-4]

  return driver_str

def trim_list(input_list):
  for index, item in enumerate(input_list):
    input_list[index] = item.strip()

  return input_list

# Wildcard expansion range
min_year = 1970
max_year = 2016
def trim_year_string(raw_year_text):
  year_text = raw_year_text

  # --- Remove quotation marks at the end for some games
  if len(year_text) == 5 and year_text[4] == '?':
    # About array slicing, see this page. Does not work like C!
    # http://stackoverflow.com/questions/509211/pythons-slice-notation
    year_text = year_text[0:4]

  # --- Expand wildcards to numerical lists. Currently there are 6 cases
  # Basic expansion: 197?, 198?, 199?, 200?
  if year_text == '197?':
    year_list = [str(x) for x in range(1970, 1979)]
  elif year_text == '198?':
    year_list = [str(x) for x in range(1980, 1989)]
  elif year_text == '199?':
    year_list = [str(x) for x in range(1990, 1999)]
  elif year_text == '200?':
    year_list = [str(x) for x in range(2000, 2009)]
  # Full expansion: ????, 19??, 20??
  elif year_text == '19??':
    year_list = [str(x) for x in range(min_year, 1999)]
  elif year_text == '20??':
    year_list = [str(x) for x in range(2000, max_year)]
  elif year_text == '????':
    year_list = [str(x) for x in range(min_year, max_year)]
  # No expansion
  else:
    year_list = [year_text]

  return year_list

# Game year information:
# INPUT: takes a string as input
# RETURN: returns and integer,
# 1  standard game or game with not-verified year (example 1998?)
# 2  game that needs decade expansion (examples 198?, 199?) or
#    full expansion (examples 19??, ????)
def get_game_year_information(year_srt):
  # --- Remove quotation marks at the end for some games
  if len(year_srt) == 5 and year_srt[4] == '?':
    year_srt = year_srt[0:4]

  # --- Get game information
  game_info = 1
  if year_srt == '197?' or year_srt == '198?' or \
     year_srt == '199?' or year_srt == '200?' or \
     year_srt == '19??' or year_srt == '20??' or \
     year_srt == '????':
    game_info = 2
  elif not year_srt.isdigit():
    print_error('Unknown MAME year string "' + year_srt + '"')
    sys.exit(10)

  return game_info

# Splits string into words
# See http://stackoverflow.com/questions/15929233/writing-a-tokenizer-in-python
# This should be into NARS module...
def tokzr_WORD(txt):
  return re.findall(r'(?ms)\W*(\w+)', txt)

def fix_category_name(main_category, category):
  # Rename some categories
  final_category = main_category
  if category == 'System / BIOS':
    final_category = 'BIOS'
  elif main_category == 'Electromechanical - PinMAME':
    final_category = 'PinMAME'
  elif main_category == 'Ball & Paddle':
    final_category = 'Ball_and_Paddle'
  elif main_category == 'Misc.':
    final_category = 'Misc'
  elif main_category == 'Mini-Games':
    final_category = 'Mini_Games'
  elif main_category == 'Fruit Machines':
    final_category = 'Fruit_Machines'
  elif main_category == 'Not Classified':
    final_category = 'Not_Classified'

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
    final_category = 'Mature'

  # Regular expression to catch ilegal characters in categories
  # that may make the categories filter parser to fail.
  result = re.search('[^\w_]+', final_category)
  if result is not None:
    NARS.print_error('Ilegal character found in category "' + final_category + '"')
    sys.exit(10)

  return final_category

# rom_copy_dic = create_copy_list(mame_filtered_dic, rom_main_list);
def create_copy_list(mame_filtered_dic, rom_main_list):
  """With list of filtered ROMs and list of source ROMs, create list of files to be copied"""

  NARS.print_info('[Creating list of ROMs to be copied/updated]')
  copy_list = []
  num_added_roms = 0
  if len(rom_main_list) == 0:
    print_info('WARNING: Not found ANY ROM in sourceDir')
    print_info('Check your configuration file')
  else:
    for key_rom_name in mame_filtered_dic:
      # If the ROM is in the mame filtered list, then add to the copy list
      if key_rom_name in rom_main_list:
        copy_list.append(key_rom_name)
        num_added_roms += 1
        NARS.print_verb('Added ROM ' + key_rom_name)
      else:
        NARS.print_info('Missing ROM ' + key_rom_name)
  NARS.print_info('Added ' + str(num_added_roms) + ' ROMs')

  return copy_list

# Creates a dictionary of CHDs to be copied. Diccionary key if the machine
# name. Dictionary value is a list of the CHDs belonging to that machine. One
# machine may have more than one CHD. CHD names are generally different from
# machine names.
#
# CHD_dic = { 'machine_name' : ['chd1', 'chd2', ...], ... }
__debug_CHD_list = 1
def create_copy_CHD_dic(mame_filtered_dic):
  """With list of filtered ROMs and, create list of CHDs to be copied"""

  NARS.print_info('[Creating list of CHDs to be copied/updated]')
  CHD_dic = {}
  num_added_CHDs = 0
  for key in sorted(mame_filtered_dic):
    if __debug_CHD_list:
      print('DEBUG: Machine {0}'.format(key))
    romObject = mame_filtered_dic[key]
    # CHD dependencies
    if hasattr(romObject, 'CHD_depends') and (romObject.CHD_depends):
      CHD_list = []
      for CHD_depend in romObject.CHD_depends:
        CHD_list.append(CHD_depend)
        num_added_CHDs += 1
        NARS.print_info('Game ' + key.ljust(8) + ' depends on CHD    ' + \
                        CHD_depend.ljust(30) + ' - Adding  to list')
      CHD_dic[key] = CHD_list      
  NARS.print_info('Added ' + str(num_added_CHDs) + ' CHDs')
  if __debug_CHD_list:
    print('DEBUG: len(CHD_dic) = {0}'.format(len(CHD_dic)))

  return CHD_dic

# This function should be renamed and put into NARS module.
# This function should be refactored. For a file list there is no need to
# use the Machine class!
def get_ROM_main_list(sourceDir):
  """Reads sourceDir and creates a dictionary of ROMs"""
  __debug_get_ROM_main_list = 0

  # --- Parse sourceDir ROM list and create main ROM list
  NARS.print_info('[Reading ROMs in source directory]')
  romMainList_dict = {}
  for file in os.listdir(sourceDir):
    if file.endswith(".zip"):
      thisFileName, thisFileExtension = os.path.splitext(file)
      romFileName_temp = thisFileName + '.zip'
      romObject = Machine()
      romObject.name = thisFileName
      romObject.filename = file
      romMainList_dict[thisFileName] = romObject
      if __debug_get_ROM_main_list:
        print(romObject.name)
        print(romObject.filename)

  return romMainList_dict

def generate_MAME_NFO_files(rom_copy_dic, mame_filtered_dic, destDir, __prog_option_dry_run):
  """Generates game information files (NFO) in destDir"""

  NARS.print_info('[Generating NFO files]')
  if __prog_option_dry_run:
    NARS.print_info('Dry run. Doing nothing.')
    return

  num_NFO_files = 0
  for rom_name in sorted(rom_copy_dic):
    romObj = mame_filtered_dic[rom_name]
    # DEBUG: dump romObj
    # print dir(romObj)
    NFO_filename = rom_name + '.nfo'
    NFO_full_filename =  destDir + NFO_filename

    # --- XML structure
    tree_output = ET.ElementTree()
    root_output = a = ET.Element('game')
    tree_output._setroot(root_output)

    # <title>1944 - The Loop Master</title>
    sub_element = ET.SubElement(root_output, 'title')
    sub_element.text = romObj.description

    # <platform>MAME</platform>
    sub_element = ET.SubElement(root_output, 'platform')
    sub_element.text = 'MAME'

    # <year>2000</year>
    # NOTE: some devices which are included as dependencies do not have
    # some fields. Write defaults.
    sub_element = ET.SubElement(root_output, 'year')
    if hasattr(romObj, 'year'):
      sub_element.text = romObj.year
    else:
      print('ROM has no year tag ' + rom_name)
      sub_element.text = '????'

    # <publisher></publisher>
    sub_element = ET.SubElement(root_output, 'publisher')
    if hasattr(romObj, 'manufacturer'):
      sub_element.text = romObj.manufacturer
    else:
      print('ROM has no publisher tag ' + rom_name)
      sub_element.text = 'Unknown'

    # <genre>Shooter / Flying Vertical</genre>
    sub_element = ET.SubElement(root_output, 'genre')
    if hasattr(romObj, 'category'):
      sub_element.text = romObj.category
    else:
      print('ROM has no genre tag ' + rom_name)
      sub_element.text = 'Unknown'

    # <plot></plot>
    # Probably need to merge information from history.dat or mameinfo.dat
    # Now, just add some technical information about the game.
    plot_str = 'Name = ' + romObj.name + ' | Driver = ' + romObj.sourcefile
    if hasattr(romObj, 'buttons'):
      plot_str += ' | Buttons = {:d}'.format(romObj.buttons)
    if hasattr(romObj, 'players'):
      plot_str += ' | Players = {:d}'.format(romObj.players)
    if hasattr(romObj, 'control_type'):
      plot_str += ' | Controls = ' + str(romObj.control_type)
    sub_element = ET.SubElement(root_output, 'plot')
    sub_element.text = plot_str

    # --- Write output file (don't use miniDOM, is sloow)
    # See http://norwied.wordpress.com/2013/08/27/307/
    NARS.print_verb('Writing ' + NFO_full_filename)
    NARS.indent_ElementTree_XML(root_output)
    tree_output.write(NFO_full_filename, xml_declaration=True, encoding='utf-8', method="xml")
    num_NFO_files += 1

  NARS.print_info('Generated ' + str(num_NFO_files) + ' NFO files')

# -----------------------------------------------------------------------------
# Filtering functions
# -----------------------------------------------------------------------------
mainFilter_str_length = 25

def filter_do_Default(mame_xml_dic):
  # A) Remove devices. Devices are non-runnable always.
  mame_filtered_dic = {}
  filtered_out_games = 0
  for key in mame_xml_dic:
    romObject = mame_xml_dic[key]
    if romObject.isDevice:
      filtered_out_games += 1
      NARS.print_vverb('FILTERED ' + key)
      continue
    mame_filtered_dic[key] = mame_xml_dic[key]
    NARS.print_debug('Included ' + key)
  NARS.print_info('Removing devices'.ljust(mainFilter_str_length) + \
                  'Removed  {:5d} | '.format(filtered_out_games) + \
                  'Remaining  {:5d}'.format(len(mame_filtered_dic)))
  
  return mame_filtered_dic

def filter_do_IncludeExclude(machines_dic, filterControl, fieldName, filterName):
  machines_filtered_dic = {}
  num_included_machines = 0
  filtered_out_games = 0
  for key in machines_dic:
    machineObject = machines_dic[key]
    booleanCondition = getattr(machineObject, fieldName)
    if (filterControl and booleanCondition) or (not filterControl and not booleanCondition):
      # Include Machine
        machines_filtered_dic[key] = machines_dic[key]
        num_included_machines += 1
        NARS.print_debug('Included ' + key)
      
    else:
      # Exclude machine
        filtered_out_games += 1
        NARS.print_vverb('Excluded ' + key)
  NARS.print_info(filterName.ljust(mainFilter_str_length) + \
                  'Removed  {:5d} | '.format(filtered_out_games) + \
                  'Remaining  {:5d}'.format(len(machines_filtered_dic)))

  return machines_filtered_dic

__debug_filter_main_filter = 0
# Main filter. <Include> and <Exclude> tags.
# filterControl 1 Include filter
#               0 Exclude filter
#
def filter_main_filter(machines_dic, filter_config, filterControl):
  if filterControl:
    filter_str_list = filter_config.includeFilter
  else:
    filter_str_list = filter_config.excludeFilter

  if __debug_filter_main_filter:
    print('filter_config = [' + ', '.join(filter_str_list) + ']')

  # ~~~ Do nothing if user did not wrote tag or tag is empty ~~~
  if filter_str_list is None:
    NARS.print_info('Doing nothing')
    return machines_dic

  # ~~~ Traverse list ~~~
  for filter_str in filter_str_list:
    if filter_str == 'Parents':
     machines_dic = filter_do_IncludeExclude(machines_dic, filterControl, 'isParent', 'Parents')
    elif filter_str ==  'Clones':
     machines_dic = filter_do_IncludeExclude(machines_dic, filterControl, 'isClone', 'Clones')
    elif filter_str == 'Mechanical':
     machines_dic = filter_do_IncludeExclude(machines_dic, filterControl, 'isMechanical', 'Mechanical')
    elif filter_str ==  'BIOS':
     machines_dic = filter_do_IncludeExclude(machines_dic, filterControl, 'isBIOS', 'BIOS')
    elif filter_str ==  'Samples':
     machines_dic = filter_do_IncludeExclude(machines_dic, filterControl, 'hasSamples', 'Samples')
    elif filter_str ==  'Working':
     machines_dic = filter_do_IncludeExclude(machines_dic, filterControl, 'isWorking', 'Working')
    elif filter_str ==  'ROMs':
     machines_dic = filter_do_IncludeExclude(machines_dic, filterControl, 'hasROMs', 'ROMs')
    elif filter_str ==  'CoinSlot':
     machines_dic = filter_do_IncludeExclude(machines_dic, filterControl, 'hasCoinSlot', 'CoinSlot')
    elif filter_str ==  'SoftwareLists':
     machines_dic = filter_do_IncludeExclude(machines_dic, filterControl, 'hasSoftwareLists', 'SoftwareLists')
    else:
      if filter_config:
        print('[ERROR] Unrecognised <Include> keyword "{0}"'.format(filter_str))
      else:
        print('[ERROR] Unrecognised <Exclude> keyword "{0}"'.format(filter_str))
      print('[ERROR] Must be: Parents, Clones, Mechanical, BIOS, Samples, Working, ROMs, CoinSlot, SoftwareLists')
      sys.exit(10)

  return machines_dic

__debug_apply_MAME_filters_Driver_tag = 0
def filter_do_Driver_tag(mame_xml_dic, filter_config):
  NARS.print_info('<Driver filter>')
  
  if filter_config.driverFilter is not None:
    driver_filter_expression = filter_config.driverFilter
    filtered_out_games = 0
    machines_filtered_dic = {}
    NARS.print_info('Filter expression "' + driver_filter_expression + '"')
    for key in sorted(mame_xml_dic):
      romObject = mame_xml_dic[key]
      driver_name_list = []
      driver_str = trim_driver_string(romObject.sourcefile)
      driver_name_list.append(driver_str)
      # --- Update search variable and call parser to evaluate expression
      NARS.set_parser_search_list(driver_name_list)
      boolean_result = NARS.parse_exec(driver_filter_expression)
      # --- Filter ROM or not
      if not boolean_result:
        filtered_out_games += 1
        NARS.print_vverb('FILTERED ' + key.ljust(8) + ' driver ' + ', '.join(driver_name_list))
      else:
        machines_filtered_dic[key] = mame_xml_dic[key]
        NARS.print_debug('Included ' + key.ljust(8) + ' driver ' + ', '.join(driver_name_list))
      # --- DEBUG info ---
      if __debug_apply_MAME_filters_Driver_tag:
        print('[DEBUG] ----- Game = ' + key + ' -----')
        print('[DEBUG] Driver name list = ', sorted(driver_name_list))
        print('[DEBUG] Filter = "' + driver_filter_expression + '"')
        print('[DEBUG] boolean_result = ' + str(boolean_result))
    NARS.print_info(' '.ljust(mainFilter_str_length) + \
                    'Removed  {:5d} | '.format(filtered_out_games) + \
                    'Remaining  {:5d}'.format(len(machines_filtered_dic)))
  else:
    NARS.print_info('User wants all drivers')
    return mame_xml_dic

  return machines_filtered_dic

__debug_apply_MAME_filters_Category_tag = 0
def filter_do_Categories_tag(mame_xml_dic, filter_config):
  NARS.print_info('<Categories filter>')

  if filter_config.categoriesFilter is not None:
    categories_filter_expression = filter_config.categoriesFilter
    machines_filtered_dic = {}
    filtered_out_games = 0
    NARS.print_info('Filter expression "' + categories_filter_expression + '"')
    for key in sorted(mame_xml_dic):
      romObject = mame_xml_dic[key]
      categories_type_list = []
      categories_type_list.append(romObject.category)
      # --- Update search variable and call parser to evaluate expression
      NARS.set_parser_search_list(categories_type_list)
      boolean_result = NARS.parse_exec(categories_filter_expression)
      # --- Filter ROM or not
      if not boolean_result:
        filtered_out_games += 1
        NARS.print_vverb('FILTERED ' + key.ljust(8) + ' category ' + ', '.join(categories_type_list))
      else:
        machines_filtered_dic[key] = mame_xml_dic[key]
        NARS.print_debug('Included ' + key.ljust(8) + ' category ' + ', '.join(categories_type_list))
      # --- DEBUG info
      if __debug_apply_MAME_filters_Category_tag:
        print('[DEBUG] Category list = ', sorted(categories_type_list))
        print('[DEBUG] Filter = "' + categories_filter_expression + '"')
        print('[DEBUG] boolean_result = ' + str(boolean_result))
    NARS.print_info(' '.ljust(mainFilter_str_length) + \
                    'Removed  {:5d} | '.format(filtered_out_games) + \
                    'Remaining  {:5d}'.format(len(machines_filtered_dic)))
  else:
    NARS.print_info('User wants all categories')
    return mame_xml_dic

  return machines_filtered_dic

__debug_apply_MAME_filters_displayType = 0
def filter_do_displayType_tag(mame_xml_dic, filter_config):
  NARS.print_info('<Display type filter>')

  if filter_config.displayTypeFilter is not None:
    displayType_filter_expression = filter_config.displayTypeFilter
    machines_filtered_dic = {}
    filtered_out_games = 0
    NARS.print_info('Filter expression "' + displayType_filter_expression + '"')
    for key in sorted(mame_xml_dic):
      romObject = mame_xml_dic[key]
      displayType_list = [romObject.displayType]
      NARS.set_parser_search_list(displayType_list)
      boolean_result = NARS.parse_exec(displayType_filter_expression)
      if not boolean_result:
        filtered_out_games += 1
        NARS.print_vverb('FILTERED ' + key.ljust(8) + ' display type ' + ', '.join(displayType_list))
      else:
        machines_filtered_dic[key] = mame_xml_dic[key]
        NARS.print_debug('Included ' + key.ljust(8) + ' display type ' + ', '.join(displayType_list))
      if __debug_apply_MAME_filters_displayType:
        print('[DEBUG] Machine {0}'.format(romObject.name))
        print('[DEBUG] DisplayType list = ', sorted(displayType_list))
        print('[DEBUG] Filter = "' + displayType_filter_expression + '"')
        print('[DEBUG] boolean_result = ' + str(boolean_result))
    NARS.print_info(' '.ljust(mainFilter_str_length) + \
                    'Removed  {:5d} | '.format(filtered_out_games) + \
                    'Remaining  {:5d}'.format(len(machines_filtered_dic)))
  else:
    NARS.print_info('User wants all categories')
    return mame_xml_dic

  return machines_filtered_dic

__debug_apply_MAME_filters_Orientation_tag = 0
def filter_do_Orientation_tag(mame_xml_dic, filter_config):
  NARS.print_info('<Orientation filter>')

  if filter_config.orientationFilter is not None:
    orientation_filter_expression = filter_config.orientationFilter
    machines_filtered_dic = {}
    filtered_out_games = 0
    NARS.print_info('Filter expression "' + orientation_filter_expression + '"')
    for key in sorted(mame_xml_dic):
      romObject = mame_xml_dic[key]
      orientation_type_list = []
      orientation_type_list.append(romObject.orientation)
      # --- Update search variable and call parser to evaluate expression ---
      NARS.set_parser_search_list(orientation_type_list)
      boolean_result = NARS.parse_exec(orientation_filter_expression)
      # --- Filter ROM or not ---
      if not boolean_result:
        filtered_out_games += 1
        NARS.print_vverb('FILTERED ' + key.ljust(8) + ' orientation ' + ', '.join(orientation_type_list))
      else:
        machines_filtered_dic[key] = mame_xml_dic[key]
        NARS.print_debug('Included ' + key.ljust(8) + ' orientation ' + ', '.join(orientation_type_list))
      # --- DEBUG info ---
      if __debug_apply_MAME_filters_Orientation_tag:
        print('[DEBUG] Machine {0}'.format(romObject.name))
        print('[DEBUG] Orientation list = ', sorted(orientation_type_list))
        print('[DEBUG] Filter = "' + orientation_filter_expression + '"')
        print('[DEBUG] boolean_result = ' + str(boolean_result))
    NARS.print_info(' '.ljust(mainFilter_str_length) + \
                    'Removed  {:5d} | '.format(filtered_out_games) + \
                    'Remaining  {:5d}'.format(len(machines_filtered_dic)))
  else:
    NARS.print_info('User wants all display orientations')
    return mame_xml_dic

  return machines_filtered_dic

__debug_apply_MAME_filters_Controls_tag = 0
def filter_do_Controls_tag(mame_xml_dic, filter_config):
  NARS.print_info('<Controls filter>')

  if filter_config.controlsFilter is not None:
    controls_type_filter_expression = filter_config.controlsFilter
    filtered_out_games = 0
    machines_filtered_dic = {}
    NARS.print_info('Filter expression "' + controls_type_filter_expression + '"')
    for key in sorted(mame_xml_dic):
      # --- Some games may have two controls, so controls_type_list is a list
      romObject = mame_xml_dic[key]
      controls_type_list = romObject.control_type
      # --- Update search variable and call parser to evaluate expression
      NARS.set_parser_search_list(controls_type_list)
      boolean_result = NARS.parse_exec(controls_type_filter_expression)
      # --- Filter ROM or not
      if not boolean_result:
        filtered_out_games += 1
        NARS.print_vverb('FILTERED ' + key.ljust(8) + ' controls ' + ', '.join(controls_type_list))
      else:
        machines_filtered_dic[key] = mame_xml_dic[key]
        NARS.print_debug('Included ' + key.ljust(8) + ' controls ' + ', '.join(controls_type_list))
      # --- DEBUG info ---
      if __debug_apply_MAME_filters_Controls_tag:
        print('[DEBUG] ----- Game = ' + key + ' -----')
        print('[DEBUG] Control list = ', sorted(controls_type_list))
        print('[DEBUG] Filter = "' + controls_type_filter_expression + '"')
        print('[DEBUG] boolean_result = ' + str(boolean_result))
    NARS.print_info(' '.ljust(mainFilter_str_length) + \
                    'Removed  {:5d} | '.format(filtered_out_games) + \
                    'Remaining  {:5d}'.format(len(machines_filtered_dic)))
  else:
    NARS.print_info('User wants all controls')
    return mame_xml_dic

  return machines_filtered_dic

__debug_apply_MAME_filters_Buttons_tag = 0
def filter_do_Buttons_tag(mame_xml_dic, filter_config):
  NARS.print_info('<Buttons filter>')

  if filter_config.buttons_exp is not None:
    button_filter_expression = filter_config.buttons_exp
    machines_filtered_dic = {}
    filtered_out_games = 0
    NARS.print_info('Filter expression "' + button_filter_expression + '"')
    for key in mame_xml_dic:
      romObject = mame_xml_dic[key]
      buttons_str = romObject.buttons
      buttons = int(buttons_str)
      if __debug_apply_MAME_filters_Buttons_tag:
        print('[DEBUG] Buttons number = ' + buttons_str)
        print('[DEBUG] Buttons filter = "' + button_filter_expression + '"')
      boolean_result = eval(button_filter_expression, globals(), locals())

      # If not all items are true, the game is NOT copied (filtered)
      if not boolean_result:
        filtered_out_games += 1
        NARS.print_vverb('FILTERED ' + key + ' buttons ' + buttons_str)
      else:
        machines_filtered_dic[key] = mame_xml_dic[key]
        NARS.print_debug('Included ' + key + ' buttons ' + buttons_str)
    NARS.print_info(' '.ljust(mainFilter_str_length) + \
                    'Removed  {:5d} | '.format(filtered_out_games) + \
                    'Remaining  {:5d}'.format(len(machines_filtered_dic)))
  else:
    NARS.print_info('User wants all buttons')
    return mame_xml_dic

  return machines_filtered_dic

__debug_apply_MAME_filters_Players_tag = 0
def filter_do_Players_tag(mame_xml_dic, filter_config):
  NARS.print_info('<Players filter>')

  if filter_config.players_exp is not None:
    players_filter_expression = filter_config.players_exp
    machines_filtered_dic = {}
    filtered_out_games = 0
    NARS.print_info('Filter expression "' + players_filter_expression + '"')
    for key in mame_xml_dic:
      romObject = mame_xml_dic[key]
      players_str = romObject.players
      players = int(players_str)
      if __debug_apply_MAME_filters_Players_tag:
        print('[DEBUG] Players number = ' + players_str)
        print('[DEBUG] Players filter = "' + players_filter_expression + '"')
      boolean_result = eval(players_filter_expression, globals(), locals())

      # If not all items are true, the game is NOT copied (filtered)
      if not boolean_result:
        filtered_out_games += 1
        NARS.print_vverb('FILTERED ' + key + ' players ' + players_str)
      else:
        machines_filtered_dic[key] = mame_xml_dic[key]
        NARS.print_debug('Included ' + key + ' players ' + players_str)
    NARS.print_info(' '.ljust(mainFilter_str_length) + \
                    'Removed  {:5d} | '.format(filtered_out_games) + \
                    'Remaining  {:5d}'.format(len(mame_filtered_dic)))
  else:
    NARS.print_info('User wants all players')
    return mame_xml_dic

  return machines_filtered_dic

__debug_apply_MAME_filters_years_tag = 0
def filter_do_Years_tag(mame_xml_dic, filter_config):
  NARS.print_info('<Year filter>')
  year_YearExpansion = filter_config.year_YearExpansion_opt
  if year_YearExpansion:
    NARS.print_info('Year expansion activated')
  else:
    NARS.print_info('Year expansion deactivated')

  if filter_config.year_exp is not None:
    machines_filtered_dic = {}
    filtered_out_games = 0
    year_filter_expression = filter_config.year_exp
    NARS.print_info('Filter expression "' + year_filter_expression + '"')    
    for key in sorted(mame_xml_dic):
      romObject = mame_xml_dic[key]
      # year is a string, convert to int
      year_srt = romObject.year
      # Game year information:
      #  1 standard game or game with not-verified year (example 1998?)
      #  2 game that needs decade expansion (examples 198?, 199?) or
      #    full expansion (examples 19??, ????)
      game_info = get_game_year_information(year_srt)

      # Game is standard (no ? or strange characters): do filtering
      if game_info == 1:
        # Convert number string to int (supports games like 1997?)
        year_list = trim_year_string(year_srt)
        if len(year_list) != 1:
          NARS.print_error('Logical error filtering year (standard year)')
          sys.exit(10)
        year = int(year_list[0])
        if __debug_apply_MAME_filters_years_tag:
          print('[DEBUG] Game ' + key.ljust(8) + ' / Year value = ' + str(year) +
                ' / Filter = "' + year_filter_expression + '"')
        boolean_result = eval(year_filter_expression, globals(), locals())
        # If not all items are true, the game is NOT copied (filtered)
        if not boolean_result:
          filtered_out_games += 1
          NARS.print_vverb('FILTERED ' + key.ljust(8) + ' year ' + str(year))
        else:
          machines_filtered_dic[key] = mame_xml_dic[key]
          NARS.print_debug('Included ' + key.ljust(8) + ' year ' + str(year))

      # Game needs expansion. If user activated this option expand wildcars and
      # then do filtering. If option not activated, discard game
      elif game_info == 2:
        if year_YearExpansion:
          year_list = trim_year_string(year_srt)
          if len(year_list) < 2:
            print('Logical error filtering year (expanded year)')
            sys.exit(10)
          boolean_list = []
          for year_str in year_list:
            year = int(year_str)
            if __debug_apply_MAME_filters_years_tag:
              print('[DEBUG] Game ' + key.ljust(8) + ' / Year value = ' + str(year) +
                    ' / Filter = "' + year_filter_expression + '"')
            boolean_result = eval(year_filter_expression, globals(), locals())
            boolean_list.append(boolean_result)
          # Knowing the boolean results for the wildcard expansion, check if game
          # should be included or not.
          if any(boolean_list):
            machines_filtered_dic[key] = mame_xml_dic[key]
            NARS.print_debug('Included ' + key.ljust(8) + ' year ' + str(year))
          else:
            filtered_out_games += 1
            NARS.print_vverb('FILTERED ' + key.ljust(8) + ' year ' + str(year))
        else:
          filtered_out_games += 1
          NARS.print_vverb('FILTERED ' + key.ljust(8) + ' year ' + str(year))
      else:
        NARS.print_error('Wrong result returned by get_game_year_information() = ' + str(game_info))
        sys.exit(10)
    NARS.print_info(' '.ljust(mainFilter_str_length) + \
                    'Removed  {:5d} | '.format(filtered_out_games) + \
                    'Remaining  {:5d}'.format(len(machines_filtered_dic)))
  else:
    NARS.print_info('User wants all years')
    return mame_xml_dic

  return machines_filtered_dic

def filter_do_substitute_machines(mame_xml_dic):
  
  return mame_xml_dic

# Add ROMs (devices and BIOS) needed for other ROM to work.
# Traverse the list of filtered games, and check if they have dependencies. If
# so, add the dependencies to the filtered list.
def filter_resolve_device_and_BIOS_dependencies(mame_filtered_dic, mame_dic):
  NARS.print_info('<Adding ROM dependencies (BIOS and devices with ROMs)>')
  # NOTE: dictionaries cannot change size during iteration. Create auxiliary list.
  dependencies_ROM_list = {}
  for key in sorted(mame_filtered_dic):
    romObject = mame_filtered_dic[key]
    # --- BIOS dependencies ---
    if len(romObject.BIOS_depends_list):
      for BIOS_depend in romObject.BIOS_depends_list:
        if BIOS_depend not in mame_dic:
          NARS.print_error('[ERROR] Machine "{0}"'.format(romObject.name))
          NARS.print_error('[ERROR] BIOS dependency "{0}" not found in mame_dic'.format(BIOS_depend))
          sys.exit(10)
        # Get ROM object from main, unfiltered dictionary
        BIOS_romObj = mame_dic[BIOS_depend]
        # Only add dependency if not already in filtered list
        if BIOS_depend not in dependencies_ROM_list:
          dependencies_ROM_list[BIOS_depend] = BIOS_romObj
          NARS.print_info('Game ' + key.ljust(8) + ' depends on BIOS   ' + \
                          BIOS_depend.ljust(11) + ' - Adding  to list')
        else:
          NARS.print_vverb('Game ' + key.ljust(8) + ' depends on BIOS   ' + \
                           BIOS_depend.ljust(11) + ' - Already on list')

    # --- Device dependencies ---
    if len(romObject.device_depends_list):
      for device_depend in romObject.device_depends_list:
        if device_depend not in mame_dic:
          NARS.print_error('[ERROR] Machine "{0}"'.format(romObject.name))
          NARS.print_error('[ERROR] Device dependency "{0}" not found in mame_dic'.format(device_depend))
          sys.exit(10)
        device_romObj = mame_dic[device_depend]
        if device_depend not in dependencies_ROM_list:
          dependencies_ROM_list[device_depend] = device_romObj
          NARS.print_info('Game ' + key.ljust(8) + ' depends on device ' + \
                          device_depend.ljust(11) + ' - Adding  to list')
        else:
          NARS.print_vverb('Game ' + key.ljust(8) + ' depends on device ' + \
                           device_depend.ljust(11) + ' - Already on list')

  for key in dependencies_ROM_list:
    romObject = dependencies_ROM_list[key]
    mame_filtered_dic[key] = romObject
  
  return mame_filtered_dic

# Main filtering function. Apply filters to main parent/clone dictionary.
def filter_MAME_machines(mame_dic, filter_config):
  NARS.print_info('[Applying MAME filters]')
  NARS.print_info('NOTE: -vv if you want to see filters in action')
  
  # ~~~~~ Main filter: Include and Exclude ~~~~~~
  NARS.print_info('<Default filter>')
  mame_filtered_dic = filter_do_Default(mame_dic)
  NARS.print_info('<Include filter>')
  mame_filtered_dic = filter_main_filter(mame_filtered_dic, filter_config, 1)
  NARS.print_info('<Exclude filter>')
  mame_filtered_dic = filter_main_filter(mame_filtered_dic, filter_config, 0)

  # ~~~~~ Secondary filters ~~~~~~  
  mame_filtered_dic = filter_do_Driver_tag     (mame_filtered_dic, filter_config)
  mame_filtered_dic = filter_do_Categories_tag (mame_filtered_dic, filter_config)
  mame_filtered_dic = filter_do_displayType_tag(mame_filtered_dic, filter_config)
  mame_filtered_dic = filter_do_Orientation_tag(mame_filtered_dic, filter_config)
  mame_filtered_dic = filter_do_Controls_tag   (mame_filtered_dic, filter_config)
  mame_filtered_dic = filter_do_Buttons_tag    (mame_filtered_dic, filter_config)
  mame_filtered_dic = filter_do_Players_tag    (mame_filtered_dic, filter_config)
  mame_filtered_dic = filter_do_Years_tag      (mame_filtered_dic, filter_config)

  # ~~~~~ Global ROM substitution ~~~~~
  
  # ~~~~~ Local ROM substitution ~~~~~

  # ~~~~~ ROM dependencies ~~~~~
  mame_filtered_dic = filter_resolve_device_and_BIOS_dependencies(mame_filtered_dic, mame_dic)

  return mame_filtered_dic

# -----------------------------------------------------------------------------
# Parse Catver.ini and MAME reduced XML file
# -----------------------------------------------------------------------------
def parse_catver_ini():
  """Parses Catver.ini and returns a ..."""

  # --- Parse Catver.ini and create a histogram with the categories ---
  NARS.print_info('[Parsing Catver.ini]')
  cat_filename = configuration.Catver
  NARS.print_verb(' Opening ' + cat_filename)
  final_categories_dic = {}
  f = open(cat_filename, 'r')
  # 0 -> Looking for '[Category]' tag
  # 1 -> Reading categories
  # 2 -> Categories finished. STOP
  read_status = 0
  for cat_line in f:
    stripped_line = cat_line.strip()
    if read_status == 0:
      if stripped_line == '[Category]':
        read_status = 1
    elif read_status == 1:
      line_list = stripped_line.split("=")
      if len(line_list) == 1:
        read_status = 2
        continue
      else:
        game_name = line_list[0]
        category = line_list[1]
        # --- Sub-categories ---
        sub_categories = category.split("/")
        main_category = sub_categories[0].strip()
        second_category = sub_categories[0].strip()

        # NOTE: Only use the main category for filtering.
        final_category = fix_category_name(main_category, category)

        # - Create final categories dictionary
        final_categories_dic[game_name] = final_category
    elif read_status == 2:
      break
    else:
      print_error('Unknown read_status FSM value')
      sys.exit(10)
  f.close()

  return final_categories_dic

# Used in the filtering functions (do_checkFilter, do_update(), do_checkArtwork(),
# do_update_artwork()), but not in the do_list_*() functions.
#
# Returns dictionary machine_dict with key the Machine name and value a Machine object.
def parse_MAME_merged_XML():
  """Parses a MAME merged XML and creates a parent/clone list"""

  filename = configuration.MergedInfo_XML
  NARS.print_info('[Parsing MAME merged XML]')
  tree = NARS.XML_read_file_cElementTree(filename, "Parsing merged XML file")

  # --- Raw list: literal information from the XML
  machine_dict = {}
  root = tree.getroot()
  num_games = 0
  num_parents = 0
  num_clones = 0
  for game_EL in root:
    # Skip non machine tags, if any
    if game_EL.tag != 'machine':
      continue

    # Create Machine object and fill default values. Code has to change only
    # non-default ones, and will be more compact.
    num_games += 1
    machineObj = Machine()
    game_attrib = game_EL.attrib
    machineObj.name = game_attrib['name']
    NARS.print_debug('machine = ' + game_attrib['name'])

    # ~~~~~ Check game attributes and create variables for filtering ~~~~~
    # --- Parent or clone (isClone defaults False) ---
    if 'cloneof' in game_attrib:
      num_clones += 1
      machineObj.isClone = True
      machineObj.isParent = False
      machineObj.cloneof = game_attrib['cloneof']
      NARS.print_debug(' Clone of = ' + game_attrib['cloneof'])
    else:
      num_parents += 1

    # --- Device and Runnable (isDevice defaults False, isRunnable defaults True) ---
    if 'isdevice' in game_attrib and game_attrib['isdevice'] == 'yes':
      machineObj.isDevice = True

    if 'runnable' in game_attrib and game_attrib['runnable'] == 'no':
      machineObj.isRunnable = False

    # --- Mechanical (isMechanical defaults False) ---
    if 'ismechanical' in game_attrib and game_attrib['ismechanical'] == 'yes':
      machineObj.isMechanical = True

    # --- BIOS (isBIOS defaults False) ---
    if 'isbios' in game_attrib and game_attrib['isbios'] == 'yes':
      machineObj.isBIOS = True

    # --- Samples (isSamples defaults False) ---
    if 'sampleof' in game_attrib:
      machineObj.sampleof = game_attrib['sampleof']
      machineObj.hasSamples = True

    # --- Game driver ---
    if 'sourcefile' in game_attrib:
      # Remove the trailing '.c' or '.cpp' from driver name
      machineObj.sourcefile = trim_driver_string(game_attrib['sourcefile'])

    # ~~~~~ Parse machine child tags ~~~~~
    for child_game in game_EL:
      # --- information to generate NFO files ---
      if child_game.tag == 'description':
        machineObj.description = child_game.text
      elif child_game.tag == 'year':
        machineObj.year = child_game.text
      elif child_game.tag == 'manufacturer':
        machineObj.manufacturer = child_game.text    

      # --- Driver status ---
      elif child_game.tag == 'driver':
        driver_attrib = child_game.attrib

        # Driver status is good, imperfect, preliminary
        # preliminary games don't work or have major emulation problems
        # imperfect games are emulated with some minor issues
        # good games are perfectly emulated
        if 'status' in driver_attrib:
          machineObj.driver_status = driver_attrib['status']
          NARS.print_debug(' Driver status = ' + machineObj.driver_status)
          if machineObj.driver_status == 'good' or machineObj.driver_status == 'imperfect':
            machineObj.isWorking = True
          elif machineObj.driver_status == 'preliminary':
            machineObj.isWorking = False
          else:
            print('Unknown <driver> status {0} (machine {1}'.format(machineObj.driver_status, machineObj.name))
            sys.exit(10)
        else:
          machineObj.driver_status = 'unknown'

      # --- Category ---
      elif child_game.tag == 'category':
        machineObj.category = child_game.text

      # --- Controls ---
      elif child_game.tag == 'input':
        control_attrib = child_game.attrib
        # buttons defaults to 0
        if 'buttons' in control_attrib:
          machineObj.buttons = int(control_attrib['buttons'])

        # players defaults to 0
        if 'players' in control_attrib:
          machineObj.players = int(control_attrib['players'])

        # coins defaults to 0. hasCoinSlot defaults to False
        if 'coins' in control_attrib:
          machineObj.coins = int(control_attrib['coins'])
          if machineObj.coins > 0:
            machineObj.hasCoinSlot = True

        # A game may have more than one control (joystick, dial, ...)
        for control in child_game:
          if control.tag == 'control':
            if 'type' in control.attrib:
              machineObj.control_type_list.append(control.attrib['type'].title())
        if len(machineObj.control_type_list) < 1:
          machineObj.control_type_list.append('ButtonsOnly')

      # --- <NARS> custom tag (attributes and sub-tags) ---
      elif child_game.tag == 'NARS':
        # --- <NARS> attributes ---
        nars_attrib = child_game.attrib
        # hasROMs defaults to True
        if 'hasROMs' in nars_attrib:
          if nars_attrib['hasROMs'] == 'no':
            machineObj.hasROMs = False
        else:
          print('[ERROR] Not found <NARS hasROMs=... > (Machine {0})\n'.format(machineObj.name))
          sys.exit(10)

        # hasSoftwareLists defaults to False
        if 'hasSoftwareLists' in nars_attrib:
          if nars_attrib['hasSoftwareLists'] == 'yes':
            machineObj.hasSoftwareLists = True
        else:
          print('[ERROR] Not found <NARS hasSoftwareLists=... > (Machine {0})\n'.format(machineObj.name))
          sys.exit(10)

        if 'displayType' in nars_attrib:
          machineObj.displayType = nars_attrib['displayType']
        else:
          print('[ERROR] Not found <NARS displayType=... > (Machine {0})\n'.format(machineObj.name))
          sys.exit(10)

        if 'orientation' in nars_attrib:
          machineObj.orientation = nars_attrib['orientation']
        else:
          print('[ERROR] Not found <NARS orientation=... > (Machine {0})\n'.format(machineObj.name))
          sys.exit(10)

        # --- <NARS> tags ---
        for NARS_tag in child_game:
          if NARS_tag.tag == 'BIOS':
            machineObj.BIOS_depends_list.append(NARS_tag.text)
          elif NARS_tag.tag == 'Device':
            machineObj.device_depends_list.append(NARS_tag.text)
          elif NARS_tag.tag == 'CHD':
            machineObj.CHD_depends_list.append(NARS_tag.text)

    # --- Add new game to the list ---
    machine_dict[game_attrib['name']] = machineObj

  NARS.print_info('Number of machines  ' + str(num_games))
  NARS.print_info('Number of parents   ' + str(num_parents))
  NARS.print_info('Number of clones    ' + str(num_clones))

  return machine_dict

# -----------------------------------------------------------------------------
# MAME XML is written by this file:
# http://www.mamedev.org/source/src/emu/info.c.html
# -----------------------------------------------------------------------------
# DEVICES
# -----------------------------------------------------------------------------
# RULE All device machines (isdevice="yes") are no runnable (runnable="no")
#
# Example of a device with a ROM ----------------------------------------------
# <machine name="qsound" sourcefile="src/emu/sound/qsound.c" isdevice="yes" runnable="no">
#   <description>Q-Sound</description>
#   <rom name="qsound.bin" size="8192" crc="" sha1="" status="baddump" region="qsound" offset="0"/>
#   <chip type="cpu" tag=":qsound" name="DSP16" clock="4000000"/>
#   <sound channels="0"/>
# </machine>
#
# Example of a game that uses a device that has a ROM -------------------------
# <machine name="dino" sourcefile="cps1.c">
#   <description>Cadillacs and Dinosaurs (World 930201)</description>
#   <year>1993</year>
#   <manufacturer>Capcom</manufacturer>
#   ...
#   <device_ref name="qsound"/>
#   <device_ref name="dsp16"/>
#   ...
#   <driver status="good" .../>
# </machine>
#
# -----------------------------------------------------------------------------
# BIOS
# -----------------------------------------------------------------------------
# Is there a difference between arcade BIOS and computer BIOS?
#
# Example of a BIOS game ------------------------------------------------------
# <machine name="neogeo" sourcefile="neogeo.c" isbios="yes">
#   <description>Neo-Geo</description>
#   <year>1990</year>
#   <manufacturer>SNK</manufacturer>
#   <biosset name="euro" description="Europe MVS (Ver. 2)" default="yes"/>
#   <biosset name="euro-s1" description="Europe MVS (Ver. 1)"/>
#   ...
#   <rom name="sp-s2.sp1" bios="euro" size="131072" crc="" sha1="" region="mainbios" offset="0"/>
#   <rom name="sp-s.sp1" bios="euro-s1" size="131072" crc="" sha1="" region="mainbios" offset="0"/>
#   ...
# </machine>
#
# Example of a game that uses a BIOS ------------------------------------------
# <machine name="mslug" sourcefile="neogeo.c" romof="neogeo">
#   <description>Metal Slug - Super Vehicle-001</description>
#   <year>1996</year>
#   <manufacturer>Nazca</manufacturer>
#   <biosset name="euro" description="Europe MVS (Ver. 2)" default="yes"/>
#   <biosset name="euro-s1" description="Europe MVS (Ver. 1)"/>
#   ...
#   <rom name="sp-s2.sp1" merge="sp-s2.sp1" bios="euro" size="131072" crc="" sha1="" region="mainbios" offset="0"/>
#   <rom name="sp-s.sp1" merge="sp-s.sp1" bios="euro-s1" size="131072" crc="" sha1="" region="mainbios" offset="0"/>
#   ...
# </machine>
#
# Example of mess machine with a BIOS (segacd) --------------------------------
#
# -----------------------------------------------------------------------------
# CHDs
# -----------------------------------------------------------------------------
# To see how to place CHDs into MAME ROM directory, see
# http://www.mameworld.info/easyemu/mameguide/mameguide-roms.html
#
# Some arcade machines with CHDs:
#  99bottles cdrom
#  area51mx  ide:0:hdd:image
#  astron    laserdisc
#  atronic   cdrom
#  av2mj2rg  vhs
#  avalnc13 gdrom
#
# Some machines have a <disk> tag only:
#  99bottles <disk name="99bottles" sha1="..." region="cdrom" .../>
#  atronic <disk name="atronic" sha1="..." region="cdrom" ./>
#  avalnc13 <disk name="gdt-0010c" sha1="..." region="gdrom" .../>
#  astron <disk name="astron" status="nodump" region="laserdisc" .../>
#
# Other machines have a <disk> tag and a <device> tag
#  carnevil
#
# Example of a CHD machine ----------------------------------------------------
# <machine name="carnevil" sourcefile="seattle.c">
#   <description>CarnEvil (v1.0.3)</description>
#   <year>1998</year>
#   <manufacturer>Midway Games</manufacturer>
#   <disk name="carnevil" sha1="" region="ide:0:hdd:image" index="0" writable="yes"/>
#   ...
#   <driver status="good" .../>
#   <device type="harddisk" tag="ide:0:hdd:image">
#     <instance name="harddisk" briefname="hard"/>
#     <extension name="chd"/>
#     <extension name="hd"/>
#   </device>
# </machine>
#
# -----------------------------------------------------------------------------
# MESS machines
# -----------------------------------------------------------------------------
# Since version 0.162 MESS was integrated in to MAME. The MAME XML list now has
# arcade machines plus MESS console/computer machines information.
#  Type A: $ mame <machine>
#  Type B: $ mame <machine> <media> <game>
# Most Type B MESS machines can be run with a Type A command. In that case, the
# BIOS is run with no media loaded, for example: $ mame segacd, $ mame sms.
# If a Type B MESS machine is run and requires a cartridge or other media, MAME
# starts and the graphical interface asks for it. For example: $ mame 32x.
#
# Differentiating arcade (type a) from non-arcade (type b) is quite challenging,
# and MAME developers do not want this differentiation to be clear. Tip by
# Haze: most arcade machines have a coin slot. Most MESS stuff don't.
#
# Example of a non-arcade machine with software list --------------------------
# <machine name="genesis" sourcefile="megadriv.cpp">
#   <description>Genesis (USA, NTSC)</description>
#   <year>1989</year>
#   <manufacturer>Sega</manufacturer>
#   ...
#   <device_ref name="software_list"/>
#   ...
#   <device type="cartridge" tag="mdslot" mandatory="1" interface="megadriv_cart">
#     <instance name="cartridge" briefname="cart"/>
#     <extension name="smd"/>
#     <extension name="bin"/>
#     <extension name="md"/>
#     <extension name="gen"/>
#   </device>
#   <slot name="mdslot">
#   </slot>
#  <softwarelist name="megadriv" status="original" />
# </machine>
#
# Example of a non-arcade machine without software list or BIOS ROM -----------
# <machine name="pdp1" sourcefile="pdp1.cpp">
#   <description>PDP-1</description>
#   <year>1961</year>
#   <manufacturer>Digital Equipment Corporation</manufacturer>
#   ...
#   <input players="2" buttons="3">
#     <control type="joy" ways="2"/>
#     <control type="trackball" minimum="0" maximum="255" sensitivity="100"/>
#     <control type="keyboard"/>
#   </input>
#   ...
#   <driver status="good" .../>
#   <device type="punchtape" tag="readt">
#     <instance name="punchtape1" briefname="ptap1"/>
#     <extension name="tap"/>
#     <extension name="rim"/>
#   </device>
#   ...
# </machine>
#
# Parent MESS machine with BIOS -----------------------------------------------
# See also segacd2. A clone of segacd is megacd.
# <machine name="segacd" sourcefile="megadriv.cpp">
#   <description>Sega CD (USA, NTSC)</description>
#   <year>1992</year>
#   <manufacturer>Sega</manufacturer>
#   <rom name="mpr-15045b.bin" size="131072" crc="c6d10268" sha1="..." .../>
#   ...
#   <device_ref name="software_list"/>
#   ...
#   <device type="cdrom" tag="cdrom" interface="scd_cdrom">
#     <instance name="cdrom" briefname="cdrm"/>
#     <extension name="chd"/>
#     ...
#     <extension name="iso"/>
#   </device>
#   <softwarelist name="segacd" status="original" />
# </machine>
#
# -----------------------------------------------------------------------------
# Checks and warnings
# -----------------------------------------------------------------------------
# Checks (program stops if triggered):
# A) All device machines (isdevice="yes") are no runnable (runnable="no")
#
# Warnings (program does not stop if triggered):
# A) Warn if machine depends on more than 1 device with ROMs.
# B) Warn if machine depends on mora than 1 CHD.
#
# -----------------------------------------------------------------------------
# Dependencies implementation
# -----------------------------------------------------------------------------
# There are 3 types of dependencies: 
#   a) machine that depends on a device and the device has a ROM.
#   b) machine depends on a BIOS.
#   c) machine depends on a CHD
#
# To solve a) games that depend on a device that has a ROM --------------------
# Algorithm:
# 1) Traverse MAME XML and make a list of devices that have a ROM.
#    A device is defined as a <machine> with isdevice="yes" attribute.
#    A device has a ROM if there is a <rom> tag inside the machine object.
# 2) Traverse MAME XML for games that are not devices (isdevice="yes" or no
#    attribute).
#    For every non-device machine, iterate over the <device_ref name="example"> 
#    tags and check if device "name" attribute is on the list of devices
#    that have a ROM. 
#    If found, make a device dependency (device_depends).
#
# To solve b) games that depend on a BIOS -------------------------------------
# Maybe the <machine> attribute "romof" can be used to resolve BIOS dependencies.
# However, "cloneof" games also have "romof" field, for example
#  <machine name="005" sourcefile="segag80r.c" sampleof="005" cloneof="10yard" romof="10yard">
#
# What if a machine is a clone and depends on a BIOS? For example
#  <machine name="mslug3" sourcefile="neogeo.c" romof="neogeo">
#  <machine name="mslug3b6" sourcefile="neogeo.c" cloneof="mslug3" romof="mslug3">
#
# NOTE BIOS dependencies are unique.
#
# Algorithm:
# 1) Traverse MAME XML and make a list of BIOS machines.
#    A BIOS machines has the attribute <machine isbios="yes">
# 2) Traverse MAME XML for standard games (no bios, no device) and check:
#   a) machine has "romof" attribute and not "cloneof" attribute.
#      Add a dependency bios_depends.
#   b) machine has a "romof" attribute and a "cloneof" attribute.
#      In this case, the parent machine should be checked for a) case.
#
# To solve c) games that depend on CHD ----------------------------------------
# Algorithm:
# 1) A machine has a CHD dependency chd_depends if it has a <disk> entry, 
#    and this entry has an attribute sha1 with checksum. Note that one machine
#    may depend on several CHDs.
#
# -----------------------------------------------------------------------------
# Separating arcade and non-arcade stuff
# -----------------------------------------------------------------------------
# Nothing implemented at the moment, since many MESS machines can be run as
# Type A machines (example: $ mame segacd) and all the BIOS ROMs are in the
# PD torrent 'MAME ROMs'.
#
# -----------------------------------------------------------------------------
# Tags created by NARS to be used by the filters
# -----------------------------------------------------------------------------
# <NARS hasROMs="yes|no" hasSoftwareLists="yes|no" orientation="Horizontal|Vertical">
#  <BIOS>bios1</BIOS>
#  <Device>device1</Device>
#  <Device>device1</Device>
#  <CHD>chd1</CHD>
#  <CHD>chd2</CHD>
# </NARS>
__debug_do_reduce_XML_dependencies = 0
def do_reduce_XML():
  """Strip out unused MAME XML information, and add ROM/CHD dependencies"""

  NARS.print_info('[Reducing MAME XML machine database]')
  input_filename = configuration.MAME_XML
  output_filename = configuration.MAME_XML_redux

  # --- Build XML output file ---
  tree_output = ET.ElementTree()
  root_output = ET.Element('mame')
  tree_output._setroot(root_output)

  # --- Read MAME XML input file ---
  NARS.print_info('Reading MAME XML game database...')
  NARS.print_info('NOTE: this will take a looong time...')
  tree_input = NARS.XML_read_file_ElementTree(input_filename, "Parsing MAME XML file")

  # Several lists of machines.
  # Checking if a list has an element is SLOW. This lists will be transformed
  # into sets for quicker access. List can have repeated elements, sets have unique 
  # elements. Sets and dictionaries use hashing, list do not use hashing.
  # See http://stackoverflow.com/questions/513882/python-list-vs-dict-for-look-up-table
  machine_isBIOS_list = []            # machines that are BIOS
  machine_isDevice_with_ROM_list = [] # machines that are devices and have ROMs
  machine_with_CHD_list = []          # machines that have CHDs
  machine_with_ROM_list = []          # machines that have ROMs
  machine_with_SoftList_list = []     # machines that have one or more software lists
  machine_displayType_dic = {}        # key = machine_name : value = "Raster|Vector|LCD|Unknown"
  machine_orientation_dic = {}        # key = machine_name : value = "Vertical|Horizontal"

  # NOTE All the MAME XML checks must be done here, and not when the reduced XML is loaded.
  #      Loading the reduced XML must be as quick as possible.


  # --- Traverse MAME XML input file ---
  # Root element:
  # <mame build="0.153 (Apr  7 2014)" debug="no" mameconfig="10">
  root_input = tree_input.getroot()
  root_output.attrib = root_input.attrib  # Copy mame attributes in output XML

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
  #   <display tag="screen" type="raster" rotate="270" width="256" height="224" .../>
  # ...
  #   <input players="2" buttons="1" coins="2" service="yes">
  #     <control type="joy" ways="4"/>
  #   </input>
  # ...
  #   <driver status="imperfect" .../>
  # </machine>
  NARS.print_info('[Reducing MAME XML database]')
  for machine_EL in root_input:
    flag_isDevice = 0
    flag_isRunnable = 1
    if machine_EL.tag == 'machine':
      NARS.print_verb('[Machine]')
      machine_name = machine_EL.attrib['name']

      # Copy all machine attributes in output XML
      machine_output = ET.SubElement(root_output, 'machine')
      machine_output.attrib = machine_EL.attrib
      machine_attrib = machine_output.attrib

      # Put BIOSes and devices in the list
      if 'isbios' in machine_attrib and machine_attrib['isbios'] == 'yes':
        machine_isBIOS_list.append(machine_name)
      if 'isdevice' in machine_attrib and machine_attrib['isdevice'] == 'yes':
        flag_isDevice = 1
      if 'runnable' in machine_attrib and machine_attrib['runnable'] == 'no':
        flag_isRunnable = 0

      # --- Attribute consistence test ---
      # Test A) Are all devices non runnable?
      if flag_isDevice == 1 and flag_isRunnable == 1:
        NARS.print_error('[ERROR] Found a machine which is device and runnable (machine = {0})'.format(machine_name))
        sys.exit(10)
      if 'isdevice' in machine_attrib and 'runnable' not in machine_attrib:
        NARS.print_error('[ERROR] isdevice attribute but NOT runnable attribute (machine = {0})'.format(machine_name))
        sys.exit(10)
      if 'isdevice' not in machine_attrib and 'runnable' in machine_attrib:
        NARS.print_error('[ERROR] NOT isdevice attribute but runnable attribute (machine = {0})'.format(machine_name))
        sys.exit(10)

      # --- Iterate through machine tag attributes (DEBUG) ---
      # for key in machine_EL.attrib:
      #   print ' machine --', key, '->', machine_EL.attrib[key];

      # --- Iterate through the children tags of a machine, and copy the ones we want to
      #     keep into the output XML.
      for machine_child in machine_EL:
        if machine_child.tag == 'description':
          NARS.print_verb(' description = ' + machine_child.text)
          description_output = ET.SubElement(machine_output, 'description')
          description_output.text = machine_child.text

        if machine_child.tag == 'year':
          NARS.print_verb(' year = ' + machine_child.text)
          year_output = ET.SubElement(machine_output, 'year')
          year_output.text = machine_child.text

        if machine_child.tag == 'manufacturer':
          NARS.print_verb(' manufacturer = ' + machine_child.text)
          manufacturer_output = ET.SubElement(machine_output, 'manufacturer')
          manufacturer_output.text = machine_child.text

        # ~~~ Check machine display information ~~~
        if machine_child.tag == 'display':
          # Display type
          # <!ATTLIST display type (raster|vector|lcd|unknown) #REQUIRED>
          if 'type' in machine_child.attrib:
            type_attrib = machine_child.attrib['type']
            if type_attrib == 'raster':
              machine_displayType_dic[machine_name] = 'Raster'
            elif type_attrib == 'vector':
              machine_displayType_dic[machine_name] = 'Vector'
            elif type_attrib == 'lcd':
              machine_displayType_dic[machine_name] = 'LCD'
            elif type_attrib == 'unknown':
              machine_displayType_dic[machine_name] = 'Unknown'
            else:
              print(machine_child.attrib)
              print('Machine "{0}" Unknown type = {1}\n'.format(machine_name, machine_child.attrib['type']))
              sys.exit(10)
          else:
            print(machine_child.attrib)
            print('Machine "{0}" <display> has no "type" attribute\n'.format(machine_name))
            sys.exit(10)
          
          # Check machine orientation
          # <!ATTLIST display rotate (0|90|180|270) #REQUIRED>
          if 'rotate' in machine_child.attrib:
            rotate_attrib = machine_child.attrib['rotate']
            if rotate_attrib == '0':
              machine_orientation_dic[machine_name] = 'Horizontal'
            elif rotate_attrib == '90':
              machine_orientation_dic[machine_name] = 'Vertical'
            elif rotate_attrib == '180':
              machine_orientation_dic[machine_name] = 'Horizontal'
            elif rotate_attrib == '270':
              machine_orientation_dic[machine_name] = 'Vertical'
            else:
              print(machine_child.attrib)
              print('Machine "{0}" Unknown rotate = {1}\n'.format(machine_name, machine_child.attrib['rotate']))
              sys.exit(10)
          else:
            print(machine_child.attrib)
            print('Machine "{0}" <display> has no "rotate" attribute\n'.format(machine_name))
            sys.exit(10)

        if machine_child.tag == 'input':
          input_output = ET.SubElement(machine_output, 'input')
          input_output.attrib = machine_child.attrib
          # Traverse <input> children and copy <control> tags
          for input_child in machine_child:
            if input_child.tag == 'control':
              control_output = ET.SubElement(input_output, 'control')
              control_output.attrib = input_child.attrib

        # From tag <driver> only copy attribute status, discard the rest to save
        # space in output XML.
        if machine_child.tag == 'driver':
          if 'status' in machine_child.attrib:
            driver_output = ET.SubElement(machine_output, 'driver')
            driver_output.attrib['status'] = machine_child.attrib['status']
          else:
            print('Machine "{0}" <driver> has no "status" attribute\n'.format(machine_name))
            sys.exit(10)

        # --- CHDs (disk) list ---
        if machine_child.tag == 'disk' and 'name' in machine_child.attrib and \
           'sha1' in machine_child.attrib:
          machine_with_CHD_list.append(machine_name)

        # --- List of devices with ROMs ---
        if flag_isDevice and machine_child.tag == 'rom':
          machine_isDevice_with_ROM_list.append(machine_name)
            
        # --- List of machines with ROMs ---
        if machine_child.tag == 'rom':
          machine_with_ROM_list.append(machine_name)
        
        # --- List of machines with Software Lists ---
        if machine_child.tag == 'softwarelist':
          machine_with_SoftList_list.append(machine_name)

  # Transform lists into sets for quick membership testing. See comments above.
  machine_isBIOS_set = set(machine_isBIOS_list)
  machine_isDevice_with_ROM_set = set(machine_isDevice_with_ROM_list)
  machine_with_CHD_set = set(machine_with_CHD_list)
  machine_with_ROM_set = set(machine_with_ROM_list)
  machine_with_SoftList_set = set(machine_with_SoftList_list)

  # --- Make list of dependencies ---
  # Dependencies can be more than 1. Also, quick indexing by name is required
  # so use a dictionary or a set.
  # depends_dic = { machine_name : [device/bios/chd, device/bios/chd, ...], 
  #                 machine_name : [device/bios/chd, device/bios/chd, ...], 
  #                 ...
  #               }
  Device_depends_dic = {}
  CHD_depends_dic = {}
  parent_bios_depends_dic = {}
  NARS.print_info('[Checking ROM dependencies (1st pass)]')
  for machine_EL in root_input:
    if machine_EL.tag == 'machine':
      machine_name = machine_EL.attrib['name']
      if 'romof' in machine_EL.attrib:
        # BIOS depends case a)
        if 'cloneof' not in machine_EL.attrib:
          parent_bios_depends_dic[machine_name] = machine_EL.attrib['romof']
          if __debug_do_reduce_XML_dependencies:
            print('machine ' + '{:>12}'.format(machine_name) + ' BIOS depends on ' +
                  machine_EL.attrib['romof'] + ' (1st pass)')
        # BIOS depends Case b) Parent should be checked
        else:
          # print 'game = ' + machine_name + ' is a clone and parent must be checked for BIOS dependencies';
          pass

      # Machine child tags
      # --- Check for device with ROMs dependencies and CHD dependencies ---
      # BIOS dependencies are unique. However, device and CHD with dependencies
      # can be multiple. Create lists with all the dependencies, and then insert
      # that list into the dictionary as value.
      device_depends_list = []
      CHD_depends_list = []
      for game_child in machine_EL:
        # Check for devices
        if game_child.tag == 'device_ref':
          if 'name' in game_child.attrib:
            device_ref_name = game_child.attrib['name']
            # Check if device this is in the list of devices with ROMs
            if device_ref_name in machine_isDevice_with_ROM_set:
              if __debug_do_reduce_XML_dependencies:
                print('machine ' + '{:>12}'.format(machine_name) +
                      ' device depends on ' + device_ref_name)
              device_depends_list.append(device_ref_name)
          else:
            print_error('device_ref has no name attribute!')
            sys.exit(10)
        # Check for CHDs
        elif game_child.tag == 'disk':
          if 'sha1' in game_child.attrib:
            chd_name = game_child.attrib['name']
            if __debug_do_reduce_XML_dependencies:
              print('machine ' + '{:>12}'.format(machine_name) +
                    ' depends on CHD ' + chd_name)
            CHD_depends_list.append(chd_name)

      # If device dependency list is not empty, insert a new entry in the
      # dictionary of dependencies.
      num_device_depends = len(device_depends_list)
      num_CHD_depends = len(CHD_depends_list)
      if num_device_depends > 0:
        Device_depends_dic[machine_name] = device_depends_list
      if num_CHD_depends > 0:
        CHD_depends_dic[machine_name] = CHD_depends_list
      if __debug_do_reduce_XML_dependencies:
        if num_device_depends > 1:
          print('machine ' + '{:>12}'.format(machine_name) + ' depends on ' +
                str(num_device_depends) + ' devices with ROM')
        if num_CHD_depends > 1:
          print('machine ' + '{:>12}'.format(machine_name) + ' depends on ' +
                str(num_CHD_depends) + ' CHDs')
    else:
      print('Found a no <machine> tag ' + machine_EL.tag)
      sys.exit(10)

  BIOS_depends_dic = {}
  NARS.print_info('[Checking ROM dependencies (2nd pass)]')
  for machine_EL in root_input:
    if machine_EL.tag == 'machine':
      machine_name = machine_EL.attrib['name']
      if 'romof' in machine_EL.attrib:
        chd_depends_list = []
        # BIOS depends case a)
        if 'cloneof' not in machine_EL.attrib:
          chd_depends_list.append(machine_EL.attrib['romof'])
          BIOS_depends_dic[machine_name] = chd_depends_list
          if __debug_do_reduce_XML_dependencies:
            print('machine = ' + '{:>12}'.format(machine_name) +
                  ' BIOS depends on ' + machine_EL.attrib['romof'])
        # BIOS depends case b) Parent should be checked
        else:
          # If parent is in this list then clone has a BIOS dependence
          if machine_EL.attrib['cloneof'] in parent_bios_depends_dic:
            chd_depends_list.append(parent_bios_depends_dic[machine_EL.attrib['cloneof']])
            BIOS_depends_dic[machine_name] = chd_depends_list
            if __debug_do_reduce_XML_dependencies:
              print('machine = ' + '{:>12}'.format(machine_name) +
                    ' is a clone that BIOS depends on ' + chd_depends_list[0])
    else:
      print('Found a no <machine> tag ' + machine_EL.tag)
      sys.exit(10)

  # --- To save memory destroy variables now
  del tree_input
  del root_input

  # --- Incorporate dependencies into output XML ---
  NARS.print_info('[Merging ROM dependencies in output XML]')
  for machine_EL in root_output:
    if machine_EL.tag == 'machine':
      machine_name = machine_EL.attrib['name']
      has_BIOS_dep     = machine_name in BIOS_depends_dic
      has_devices_dep  = machine_name in Device_depends_dic
      has_CHDs_dep     = machine_name in CHD_depends_dic
      has_ROMs         = machine_name in machine_with_ROM_set
      has_CHDs         = machine_name in machine_with_CHD_set
      hasSoftwareLists = machine_name in machine_with_SoftList_list
      # Create tag <NARS>
      NARS_element = ET.SubElement(machine_EL, 'NARS')
      
      # <NARS hasROMs="yes|no" hasSoftwareLists="yes|no" displayType="Raster|Vector|LCD|Unknown" 
      #       orientation="Horizontal|Vertical">
      if has_ROMs or has_CHDs:
        NARS_element.attrib['hasROMs'] = "yes"
      else:
        NARS_element.attrib['hasROMs'] = "no"
      if hasSoftwareLists:
        NARS_element.attrib['hasSoftwareLists'] = "yes"
      else:
        NARS_element.attrib['hasSoftwareLists'] = "no"

      # mechanical/device machines do not have <display> tag. Set orientation to Unknown
      if machine_name in machine_displayType_dic:
        NARS_element.attrib['displayType'] = machine_displayType_dic[machine_name]  
      else:
        NARS_element.attrib['displayType'] = 'Unknown'

      # mechanical/device machines do not have <display> tag. Set orientation to Unknown
      if machine_name in machine_orientation_dic:
        NARS_element.attrib['orientation'] = machine_orientation_dic[machine_name]  
      else:
        NARS_element.attrib['orientation'] = 'Unknown'

      # <NARS> tags: <BIOS>, <Device>, <CHD>
      if has_BIOS_dep:
        # values of BIOS_depends_dic are list of strings, even if only 1 element
        bios_list = BIOS_depends_dic[machine_name]
        if len(bios_list) > 1:
          print('[ERROR] Machine ' + '{:>12}'.format(machine_name) + ' depends on more than 1 BIOS')
          sys.exit(10)
        for bios_name in bios_list:
          bios_depends_tag = ET.SubElement(NARS_element, 'BIOS')
          bios_depends_tag.text = bios_name

      if has_devices_dep:
        devices_list = Device_depends_dic[machine_name]
        devices_set = set(devices_list)
        for device_unique_name in devices_set:
          device_depends_tag = ET.SubElement(NARS_element, 'Device')
          device_depends_tag.text = device_unique_name

      if has_CHDs_dep:
        CHD_list = CHD_depends_dic[machine_name]
        CHD_set = set(CHD_list)
        if len(CHD_set) != len(CHD_list):
          print('[WARNING] machine ' + '{:>12}'.format(machine_name) +
                ' len(CHD_set) != len(CHD_list)')
        for CHD_unique_name in CHD_set:
          CHD_depends_tag = ET.SubElement(NARS_element, 'CHD')
          CHD_depends_tag.text = CHD_unique_name
    else:
      print('Found a no <machine> tag ' + machine_EL.tag)
      sys.exit(10)

  # --- Pretty print XML output using miniDOM
  # See http://broadcast.oreilly.com/2010/03/pymotw-creating-xml-documents.html
  # NOTE this approach works well but is very slooow
  if 0:
    NARS.print_info('[Building reduced output XML file]')
    rough_string = ET.tostring(root_output, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    del root_output  # Reduce memory consumption
    NARS.print_info('Writing reduced XML file ' + output_filename)
    f = open(output_filename, "w")
    f.write(reparsed.toprettyxml(indent=" "))
    f.close()

  # --- Write output file (don't use miniDOM, is sloow)
  # See http://norwied.wordpress.com/2013/08/27/307/
  NARS.print_info('[Writing output file]')
  NARS.print_info('Writing reduced XML file ' + output_filename)
  NARS.indent_ElementTree_XML(root_output)
  tree_output.write(output_filename, xml_declaration=True, encoding='utf-8', method="xml")

def do_merge():
  """Merges main MAME database ready for filtering"""

  NARS.print_info('[Building merged MAME filter database]')
  mame_redux_filename = configuration.MAME_XML_redux
  merged_filename = configuration.MergedInfo_XML

  # --- Get categories from Catver.ini
  categories_dic = parse_catver_ini()

  # --- Read MAME XML or reduced MAME XML and incorporate categories
  # NOTE: this piece of code is very similar to do_reduce_XML()
  # --- Build XML output file ---
  tree_output = ET.ElementTree()
  root_output = ET.Element('mame')
  tree_output._setroot(root_output)
  NARS.print_info('[Parsing (reduced) MAME XML file]')
  tree_input = NARS.XML_read_file_cElementTree(mame_redux_filename, "Reading merged XML file")
  
  # --- Traverse MAME XML input file ---
  NARS.print_info('[Merging MAME XML and categories]')
  root_input = tree_input.getroot()
  root_output.attrib = root_input.attrib # Copy mame attributes in output XML
  num_no_category = 0
  for machine_EL in root_input:
    if machine_EL.tag == 'machine':
      machine_output = ET.SubElement(root_output, 'machine')
      # --- Copy machine attributes in output XML ---
      machine_output.attrib = machine_EL.attrib

      # --- Iterate through the children of a machine
      for machine_child in machine_EL:
        if machine_child.tag == 'description':
          description_output = ET.SubElement(machine_output, 'description')
          description_output.text = machine_child.text

        if machine_child.tag == 'year':
          year_output = ET.SubElement(machine_output, 'year')
          year_output.text = machine_child.text

        if machine_child.tag == 'manufacturer':
          manufacturer_output = ET.SubElement(machine_output, 'manufacturer')
          manufacturer_output.text = machine_child.text

        if machine_child.tag == 'input':
          input_output = ET.SubElement(machine_output, 'input')
          input_output.attrib = machine_child.attrib
          # Traverse children
          for input_child in machine_child:
            if input_child.tag == 'control':
              control_output = ET.SubElement(input_output, 'control')
              control_output.attrib = input_child.attrib

        if machine_child.tag == 'driver':
          driver_output = ET.SubElement(machine_output, 'driver')
          driver_output.attrib = machine_child.attrib

        # Dependencies
        if machine_child.tag == 'NARS':
          NARS_output = ET.SubElement(machine_output, 'NARS')
          # Copy <NARS> attributes in output XML
          NARS_output.attrib = machine_child.attrib
          # Traverse children
          for NARS_child in machine_child:
            if NARS_child.tag == 'BIOS':
              device_depends_output = ET.SubElement(NARS_output, 'BIOS')
              device_depends_output.text = NARS_child.text
            if NARS_child.tag == 'Device':
              bios_depends_output = ET.SubElement(NARS_output, 'Device')
              bios_depends_output.text = NARS_child.text
            if NARS_child.tag == 'CHD':
              chd_depends_output = ET.SubElement(NARS_output, 'CHD')
              chd_depends_output.text = NARS_child.text

      # --- Add category element ---
      machine_name = machine_EL.attrib['name']
      category = 'Unknown'
      if machine_name in categories_dic:
        category = categories_dic[machine_name]
      else:
        NARS.print_warn('[WARNING] Category not found for machine ' + machine_name)
        num_no_category += 1
      category_output = ET.SubElement(machine_output, 'category')
      category_output.text = category

  # To save memory destroy input variables now
  del tree_input
  del root_input

  # --- Write output file (don't use miniDOM, is sloooow)
  # See http://norwied.wordpress.com/2013/08/27/307/
  NARS.print_info('[Writing output file]')
  NARS.print_info('Output file ' + merged_filename)
  NARS.indent_ElementTree_XML(root_output)
  tree_output.write(merged_filename, xml_declaration=True, encoding='utf-8', method="xml")

  # Print report
  NARS.print_info('[Report]')
  NARS.print_info('Machines without category  ' + str(num_no_category))
  NARS.print_info('NOTE Machines with no category are assigned to cateogory Unknown')

def do_list_merged():
  """Short list of MAME XML file"""

  NARS.print_info('[List reduced MAME XML]')
  filename = configuration.MergedInfo_XML
  tree = NARS.XML_read_file_cElementTree(filename, "Parsing merged XML file")

  # Root element (Reduced MAME XML):
  root = tree.getroot()

  # Child elements (Reduced MAME XML):
  num_machines = 0
  num_clones = 0  
  num_ROMs = 0
  num_no_ROMs = 0
  num_CHD = 0
  num_coin_slot = 0  
  num_samples = 0
  num_mechanical = 0
  num_devices = 0
  num_norunnable = 0
  num_BIOS = 0
  for machine_EL in root:
    if machine_EL.tag == 'machine':
      num_machines += 1
      machine_attrib = machine_EL.attrib
      NARS.print_info(machine_attrib['name'])
      # --- Machine attributes ---
      if 'cloneof' in machine_attrib:
        num_clones += 1
        NARS.print_info('-        cloneof   ' + machine_attrib['cloneof'])
      if 'sourcefile' in machine_attrib:
        NARS.print_info('-         driver   ' + machine_attrib['sourcefile'])
      if 'sampleof' in machine_attrib:
        num_samples += 1
        NARS.print_info('-       sampleof   ' + machine_attrib['sampleof'])
      # yes/no attributes (which have default value in the DTD)
      if 'ismechanical' in machine_attrib and machine_attrib['ismechanical'] == 'yes':
        num_mechanical += 1
        NARS.print_info('-   ismechanical   ' + machine_attrib['ismechanical'])
      if 'isbios' in machine_attrib and machine_attrib['isbios'] == 'yes':
        num_BIOS += 1
        NARS.print_info('-         isbios   ' + machine_attrib['isbios'])
      if 'isdevice' in machine_attrib and machine_attrib['isdevice'] == 'yes':
        num_devices += 1
        NARS.print_info('-       isdevice   ' + machine_attrib['isdevice'])
      if 'runnable' in machine_attrib and machine_attrib['runnable'] == 'no':
        num_norunnable += 1
        NARS.print_info('-       runnable   ' + machine_attrib['runnable'])

      # Iterate through the children of a machine
      for machine_child in machine_EL:
        if machine_child.tag == 'description':
          NARS.print_info('--   description   ' + machine_child.text)
        elif machine_child.tag == 'year':
          NARS.print_info('--          year   ' + machine_child.text)
        elif machine_child.tag == 'manufacturer':
          NARS.print_info('--  manufacturer   ' + machine_child.text)
        elif machine_child.tag == 'driver':
          NARS.print_info('-- driver status   ' + machine_child.attrib['status'])
        elif machine_child.tag == 'category':
          NARS.print_info('--      category   ' + machine_child.text)
        elif machine_child.tag == 'input':
          if 'coins' in machine_child.attrib:
            print(machine_child.attrib['coins'])
            num_coins = int(machine_child.attrib['coins'])
            if num_coins > 0:
              num_coin_slot += 1

      # --- NARS custom tags ---
      NARS_element = machine_EL.find('NARS')
      if NARS_element is not None:
        # NARS attributes
        if 'hasROM' in NARS_element.attrib:
          if NARS_element.attrib['hasROM'] == 'yes':
            num_ROMs += 1
          else:
            num_no_ROMs += 1
        # NARS child tags
        CHD_element = NARS_element.find('CHD')
        if CHD_element is not None:
          num_CHD += 1

  NARS.print_info('[Report]')
  NARS.print_info('Number of machines      {0:6d}'.format(num_machines))
  NARS.print_info('Number of clones        {0:6d}'.format(num_clones))
  NARS.print_info('Machines with ROMs      {0:6d}'.format(num_ROMs))
  NARS.print_info('Machines without ROMs   {0:6d}'.format(num_no_ROMs))
  NARS.print_info('Machines with CHDs      {0:6d}'.format(num_CHD))
  NARS.print_info('Machines with coin slot {0:6d}'.format(num_coin_slot))
  NARS.print_info('Machines with samples   {0:6d}'.format(num_samples))
  NARS.print_info('Mechanical machines     {0:6d}'.format(num_mechanical))
  NARS.print_info('Number of BIOS          {0:6d}'.format(num_BIOS))
  NARS.print_info('Number of devices       {0:6d}'.format(num_devices))
  NARS.print_info('Non-runnable machines   {0:6d}'.format(num_norunnable))

def do_list_categories():
  """Parses Catver.ini and prints the categories and how many games for each"""

  __debug_do_list_categories = 0
  NARS.print_info('[Listing categories from Catver.ini]')

  # --- Create a histogram with the available categories based only in Catver.ini
  cat_filename = configuration.Catver
  NARS.print_info('Parsing ' + cat_filename)
  categories_dic = {}
  main_categories_dic = {}
  final_categories_dic = {}
  f = open(cat_filename, 'r')
  # 0 -> Looking for '[Category]' tag
  # 1 -> Reading categories
  # 2 -> Categories finished. STOP
  read_status = 0
  NARS.print_info('[Making categories histogram]')
  for cat_line in f:
    stripped_line = cat_line.strip()
    if __debug_do_list_categories:
      print('"' + stripped_line + '"')
    if read_status == 0:
      if stripped_line == '[Category]':
        if __debug_do_list_categories:
          print('Found [Category]')
        read_status = 1
    elif read_status == 1:
      line_list = stripped_line.split("=")
      if len(line_list) == 1:
        read_status = 2
        continue
      else:
        if __debug_do_list_categories:
          print(line_list)
        category = line_list[1]
        if category in categories_dic:
          categories_dic[category] += 1
        else:
          categories_dic[category] = 1
        # --- Sub-categories  
        sub_categories = category.split("/")
        if __debug_do_list_categories:
          print(sub_categories)
        main_category = sub_categories[0].strip()
        second_category = sub_categories[0].strip()
        if main_category in main_categories_dic: 
          main_categories_dic[main_category] += 1
        else:
          main_categories_dic[main_category] = 1

        # NOTE Only use the main category for filtering.
        final_category = fix_category_name(main_category, category)

        # Create final categories dictionary
        if final_category in final_categories_dic: 
          final_categories_dic[final_category] += 1
        else:
          final_categories_dic[final_category] = 1
    elif read_status == 2:
      break
    else:
      print_error('Unknown read_status FSM value')
      sys.exit(10)
  f.close()

  # --- Only print if very verbose ---
  if NARS.log_level >= NARS.Log.vverb:
    # Want to sort categories_dic['category'] = integer by the integer
    # Sorting dictionaries, see
    # http://stackoverflow.com/questions/613183/python-sort-a-dictionary-by-value
    # This is only valid in Python 2
#    sorted_propertiesDic = sorted(categories_dic.iteritems(), key=operator.itemgetter(1))
    # This works on Python 3
    sorted_histo = ((k, categories_dic[k]) for k in sorted(categories_dic, key=categories_dic.get, reverse=False))
    # ~~~ DEBUG object dump ~~~
    # dumpclean(sorted_propertiesDic);
    # ~~~ Print if verbose ~~~
    NARS.print_vverb('[Raw categories]')
    for k, v in sorted_histo:
      NARS.print_verb('{:6d}'.format(v) + '  ' + k)

  # ~~~ Only print if verbose ~~~
  if NARS.log_level >= NARS.Log.verb:
    sorted_histo = ((k, main_categories_dic[k]) for k in sorted(main_categories_dic, key=main_categories_dic.get, reverse=False))
    NARS.print_verb('[Main categories]')
    for k, v in sorted_histo:
      NARS.print_verb('{:6d}'.format(v) + '  ' + k)

  # ~~~ By default only list final categories ~~~
  sorted_histo = ((k, final_categories_dic[k]) for k in sorted(final_categories_dic, key=final_categories_dic.get, reverse=False))
  NARS.print_info('[Final (used) categories]')
  num_categories = 0
  for k, v in sorted_histo:
    NARS.print_info('{:6d}'.format(v) + '  ' + k)
    num_categories += 1
  NARS.print_info('[Report]')
  NARS.print_info('Number of categories  ' + str(num_categories))

__debug_do_list_drivers = 0
def do_list_drivers():    
  """Parses merged XML database and makes driver histogram and statistics"""

  NARS.print_info('[Listing MAME drivers]')
  NARS.print_info('NOTE: clones are not included')
  NARS.print_info('NOTE: mechanical are not included')
  NARS.print_info('NOTE: devices are not included')

  filename = configuration.MergedInfo_XML
  tree = NARS.XML_read_file_cElementTree(filename, "Reading merged XML file")

  # --- Do histogram ---
  drivers_histo_dic = {}
  root = tree.getroot()
  for machine_EL in root:
    if machine_EL.tag == 'machine':
      machine_attrib = machine_EL.attrib
      if __debug_do_list_drivers:
        print('Machine {0}'.format(machine_EL.attrib['name']))
      # If machine is a clone don't include it in the histogram
      if 'cloneof' in machine_attrib:
        continue
      # If machine is mechanical don't include it
      if 'ismechanical' in machine_attrib and machine_attrib['ismechanical'] == 'yes':
        continue
      # If machine is device don't include it
      if 'isdevice' in machine_attrib and machine_attrib['isdevice'] == 'yes':
        continue
      # --- Histogram ---
      if 'sourcefile' in machine_attrib:
        driver_name = trim_driver_string(machine_attrib['sourcefile'])
      else:
        driver_name = '__unknown__'
      if __debug_do_list_drivers:
        print(' driver {0}'.format(driver_name))        
      if driver_name in drivers_histo_dic: 
        drivers_histo_dic[driver_name] += 1
      else:
        drivers_histo_dic[driver_name] = 1

  # --- Print histogram ---
  # Valid in Python 2
#  sorted_histo = sorted(drivers_histo_dic.iteritems(), key=operator.itemgetter(1))
  # Valid in Python 3
  sorted_histo = ((k, drivers_histo_dic[k]) for k in sorted(drivers_histo_dic, key=drivers_histo_dic.get, reverse=False))
  NARS.print_info('[Driver histogram]')
  num_drivers = 0
  for k, v in sorted_histo:
    NARS.print_info('{:4d}'.format(v) + '  ' + k)
    num_drivers += 1

  NARS.print_info('[Report]')
  NARS.print_info('Number of drivers {:5d}'.format(num_drivers))

# See http://mamedev.org/source/src/emu/info.c.html, line 784
__debug_do_list_controls = 0
def do_list_controls():
  """Parses merged XML database and makes a controls histogram"""

  NARS.print_info('[Listing MAME controls]')
  NARS.print_info('NOTE: clones are not included')
  NARS.print_info('NOTE: mechanical are not included')
  NARS.print_info('NOTE: devices are not included')

  # filename = configuration.MergedInfo_XML;
  filename = configuration.MAME_XML_redux
  tree = NARS.XML_read_file_cElementTree(filename, "Reading merged XML file")

  # --- Histogram data
  input_buttons_dic = {}
  input_players_dic = {}
  input_control_type_dic = {}
  input_control_type_join_dic = {}
  input_control_ways_dic = {}

  # --- Do histogram ---
  root = tree.getroot()
  for game_EL in root:
    if game_EL.tag == 'machine':
      machine_attrib = game_EL.attrib

      # If machine is a clone don't include it in the histogram
      if 'cloneof' in machine_attrib:
        continue
      # If machine is mechanical don't include it
      if 'ismechanical' in machine_attrib and machine_attrib['ismechanical'] == 'yes':
        continue
      # If machine is device don't include it
      if 'isdevice' in machine_attrib and machine_attrib['isdevice'] == 'yes':
        continue

      game_name = machine_attrib['name']
      if __debug_do_list_controls:
        print('game = ' + game_name)

      # --- Histogram of controls
      for child_game_EL in game_EL:
        # --- Input tag found
        if child_game_EL.tag == 'input':
          game_input_EL = child_game_EL

          # --- Input attributes
          if 'buttons' in game_input_EL.attrib:
            if __debug_do_list_controls:
              print(' buttons = ' + game_input_EL.attrib['buttons'])
            input_buttons_dic = add_to_histogram(game_input_EL.attrib['buttons'], input_buttons_dic)
          else:
            if __debug_do_list_controls:
              print(' no buttons')
            input_buttons_dic = add_to_histogram('0', input_buttons_dic)

          if 'coins' in game_input_EL.attrib:
            if __debug_do_list_controls:
              print(' coins = ' + game_input_EL.attrib['coins'])

          if 'players' in game_input_EL.attrib:
            if __debug_do_list_controls:
              print(' players = ' + game_input_EL.attrib['players'])
            input_players_dic = add_to_histogram(game_input_EL.attrib['players'], input_players_dic)
          else:
            if __debug_do_list_controls:
              print(' no players')
            input_buttons_dic = add_to_histogram('no players tag', input_buttons_dic)

          if 'tilt' in game_input_EL.attrib:
            if __debug_do_list_controls:
              print(' tilt = ' + game_input_EL.attrib['tilt'])

          # --- Iterate children
          control_child_found = 0
          control_type_list = []
          for child in game_input_EL:
            control_child_found = 1
            if __debug_do_list_controls:
              print(' Children = ' + child.tag)

            if 'type' in child.attrib:
              if __debug_do_list_controls:
                print('  type = ' + child.attrib['type'])
              input_control_type_dic = add_to_histogram(child.attrib['type'].title(), input_control_type_dic)
              control_type_list.append(child.attrib['type'])

            if 'ways' in child.attrib:
              if __debug_do_list_controls:
                print('  ways = ' + child.attrib['ways'])
              input_control_ways_dic = add_to_histogram(child.attrib['ways'], input_control_ways_dic)

            if 'ways2' in child.attrib:
              if __debug_do_list_controls:
                print('  ways2 = ' + child.attrib['ways2'])

            if 'ways3' in child.attrib:
              if __debug_do_list_controls:
                print('  ways3 = ' + child.attrib['ways3'])

          text_not_found = 'ButtonsOnly'
          if len(control_type_list) < 1:
            control_type_list.append(text_not_found)
          input_control_type_join_dic = add_to_histogram(', '.join(sorted(control_type_list)), input_control_type_join_dic)

          # --- If no additional controls, only buttons???
          if not control_child_found:
            if text_not_found in input_control_type_dic:
              input_control_type_dic[text_not_found] += 1
            else:                          
              input_control_type_dic[text_not_found] = 1

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
  """Parses merged XML database and makes a controls histogram"""

  NARS.print_info('[Listing MAME controls]')
  NARS.print_info('NOTE: clones are not included')
  NARS.print_info('NOTE: mechanical are not included')
  NARS.print_info('NOTE: devices are not included')

  # filename = configuration.MergedInfo_XML;
  filename = configuration.MAME_XML_redux
  tree = NARS.XML_read_file_cElementTree(filename, "Reading merged XML file")

  # --- Histogram data
  years_dic = {}
  raw_years_dic = {}

  # --- Do histogram
  root = tree.getroot()
  for game_EL in root:
    if game_EL.tag == 'machine':
      machine_attrib = game_EL.attrib

      # If machine is a clone don't include it in the histogram
      if 'cloneof' in machine_attrib:
        continue
      # If machine is mechanical don't include it
      if 'ismechanical' in machine_attrib and machine_attrib['ismechanical'] == 'yes':
        continue
      # If machine is device don't include it
      if 'isdevice' in machine_attrib and machine_attrib['isdevice'] == 'yes':
        continue

      # - Game name
      game_name = machine_attrib['name']

      # --- Histogram of years
      has_year = 0
      for child_game_EL in game_EL:
        if child_game_EL.tag == 'year':
          has_year = 1
          game_year_EL = child_game_EL
          raw_year_text = game_year_EL.text
          # Remove quotation marks from some years
          # Expand wildcards to numerical lists. Currently there are 6 cases
          year_list = trim_year_string(raw_year_text)

          # --- Make histogram
          for number in year_list:
            years_dic = add_to_histogram(number, years_dic)
          raw_years_dic = add_to_histogram(raw_year_text, raw_years_dic)

      if not has_year:
        years_dic = add_to_histogram('no year', years_dic)
        raw_years_dic = add_to_histogram('no year', raw_years_dic)

  NARS.print_info('[Release year histogram (raw)]')
  sorted_histo = ((k, raw_years_dic[k]) for k in sorted(raw_years_dic, key=raw_years_dic.get, reverse=False))
  for k, v in sorted_histo:
    NARS.print_info('{:5d}'.format(v) + '  ' + k)
  print(' ')

  NARS.print_info('[Release year histogram (trimmed)]')
  sorted_histo = ((k, years_dic[k]) for k in sorted(years_dic, key=years_dic.get, reverse=False))
  for k, v in sorted_histo:
    NARS.print_info('{:5d}'.format(v) + '  ' + k)

#
# Prints all information about a particular machine.
#
def do_query(machineName):
  NARS.print_info('[Query MAME reduced XML]')
  NARS.print_info('Machine = ' + machineName)

  # --- Get MAME parent/clone dictionary --------------------------------------
  mame_dic = parse_MAME_merged_XML()

  # ~~~ Print information ~~~
  NARS.print_info('[Machine information]')
  if machineName in mame_dic:
    machine = mame_dic[machineName]
    NARS.print_info('Name                 {0}'.format(machine.name))
    NARS.print_info('Clone of             {0}'.format(machine.cloneof))
    NARS.print_info('isClone              {0}'.format(machine.isClone))
    NARS.print_info('isParent             {0}'.format(machine.isParent))
    NARS.print_info('isDevice             {0}'.format(machine.isDevice))
    NARS.print_info('isRunnable           {0}'.format(machine.isRunnable))
    NARS.print_info('isMechanical         {0}'.format(machine.isMechanical))
    NARS.print_info('isBIOS               {0}'.format(machine.isBIOS))
    NARS.print_info('Sample of            {0}'.format(machine.sampleof))
    NARS.print_info('hasSamples           {0}'.format(machine.hasSamples))
    NARS.print_info('sourcefile           {0}'.format(machine.sourcefile))
    NARS.print_info('---')
    NARS.print_info('Description          {0}'.format(machine.description))
    NARS.print_info('year                 {0}'.format(machine.year))
    NARS.print_info('manufacturer         {0}'.format(machine.manufacturer))
    NARS.print_info('driver_status        {0}'.format(machine.driver_status))
    NARS.print_info('isWorking            {0}'.format(machine.isWorking))
    NARS.print_info('category             {0}'.format(machine.category))
    NARS.print_info('buttons              {0}'.format(machine.buttons))
    NARS.print_info('players              {0}'.format(machine.players))
    NARS.print_info('coins                {0}'.format(machine.coins))
    NARS.print_info('hasCoinSlot          {0}'.format(machine.hasCoinSlot))
    NARS.print_info('control_type_list    {0}'.format(machine.control_type_list))
    NARS.print_info('---')
    NARS.print_info('hasROMs              {0}'.format(machine.hasROMs))
    NARS.print_info('hasSoftwareLists     {0}'.format(machine.hasSoftwareLists))
    NARS.print_info('displayType          {0}'.format(machine.displayType))
    NARS.print_info('orientation          {0}'.format(machine.orientation))
    NARS.print_info('BIOS_depends_list    {0}'.format(machine.BIOS_depends_list))
    NARS.print_info('device_depends_list  {0}'.format(machine.device_depends_list))
    NARS.print_info('CHD_depends_list     {0}'.format(machine.CHD_depends_list))
  else:
    print('Machine \'{0}\' not found'.format(machineName))
    sys.exit(10)

# ----------------------------------------------------------------------------
def do_list_filters():
  """List of configuration file"""

  NARS.print_info('[Listing configuration file]')
  tree = NARS.XML_read_file_ElementTree(__config_configFileName, "Parsing configuration XML file")

  # Iterate over XML root object
  root = tree.getroot()
  for root_child in root:
    if root_child.tag == 'MAME_XML':
      NARS.print_info('MAME_XML        ' + root_child.text)
    elif root_child.tag == 'MAME_XML_redux':
      NARS.print_info('MAME_XML_redux  ' + root_child.text)
    elif root_child.tag == 'Catver':
      NARS.print_info('Catver          ' + root_child.text)
    elif root_child.tag == 'Merged_XML':
      NARS.print_info('Merged_XML      ' + root_child.text)
    elif root_child.tag == 'MachineSwap':
      NARS.print_info('MachineSwap     ' + root_child.text)
    elif root_child.tag == 'MAMEFilter':
      NARS.print_info('<MAME filter>')
      NARS.print_info('Name        ' + root_child.attrib['name'])
      for root_child_node in root_child:
        if root_child_node.tag == 'ROMsSource':
          NARS.print_info('ROMsSource  ' + root_child_node.text)
        elif root_child_node.tag == 'ROMsDest':
          NARS.print_info('ROMsDest    ' + root_child_node.text)
    else:
      print('Tag with wrong name ' + root_child.tag)
      sys.exit(10)

# ----------------------------------------------------------------------------
def do_check(filterName):
  """Applies filter and copies ROMs into destination directory"""

  NARS.print_info('[Checking filter]')
  NARS.print_info('Filter name = ' + filterName)

  # --- Get configuration for the selected filter and check for errors ---
  filter_config = get_Filter_from_Config(filterName)
  NARS.have_dir_or_abort(filter_config.sourceDir, 'ROMsSource')
  NARS.have_dir_or_abort(filter_config.sourceDir_CHD, 'CHDsSource')
  NARS.have_dir_or_abort(filter_config.destDir, 'ROMsDest')

  # --- Get MAME parent/clone dictionary --------------------------------------
  mame_dic = parse_MAME_merged_XML()

  # --- Create main ROM list in sourceDir -------------------------------------
  rom_main_list = get_ROM_main_list(filter_config.sourceDir)

  # --- Apply filter and create list of files to be copied --------------------
  mame_filtered_dic = filter_MAME_machines(mame_dic, filter_config)

  # --- Print list in alphabetical order ---
  NARS.print_info('[Filtered machine list]')
  missing_roms = 0
  have_roms = 0
  missing_CHD = have_CHD = 0
  have_CHD = 0
  num_CHD = 0
  for key_main in sorted(mame_filtered_dic):
    romObject = mame_filtered_dic[key_main]

    # --- Check if ROM file exists ---
    sourceFullFilename = filter_config.sourceDir + romObject.name + '.zip'
    if not os.path.isfile(sourceFullFilename):
      missing_roms += 1
      flag_str = 'Missing ROM'
    else:
      have_roms += 1
      flag_str = 'Have ROM'
    fileName = romObject.name + '.zip'
    NARS.print_info("<Machine> " + romObject.name.ljust(12) + flag_str.rjust(12) + '  ' +
                    fileName.rjust(25) + '  ' + romObject.description)

    # --- Check if CHD exists ---
    for CHD_file in romObject.CHD_depends_list:
      num_CHD += 1
      CHD_FullFilename = filter_config.sourceDir_CHD + '/' +  romObject.name + '/' + CHD_file + '.chd'
      CHD_Filename = romObject.name + '/' + CHD_file + '.chd'
      if not os.path.isfile(CHD_FullFilename):
        missing_CHD += 1
        flag_str = 'Missing CHD'
      else:
        have_CHD += 1
        flag_str = 'Have CHD'
      NARS.print_info("<Machine> " + romObject.name.ljust(12) + flag_str.rjust(12) + '  ' +
                      CHD_Filename.rjust(25) + '  ' + romObject.description)

  NARS.print_info('[Report]')
  NARS.print_info('ROMs          {0:6d}'.format(len(mame_dic)))
  NARS.print_info('Filtered ROMs {0:6d}'.format(len(mame_filtered_dic)))
  NARS.print_info('Have ROMs     {0:6d}'.format(have_roms))
  NARS.print_info('Missing ROMs  {0:6d}'.format(missing_roms))
  NARS.print_info('Total CHDs    {0:6d}'.format(num_CHD))
  NARS.print_info('Have CHDs     {0:6d}'.format(have_CHD))
  NARS.print_info('Missing CHDs  {0:6d}'.format(missing_CHD))

# ----------------------------------------------------------------------------
# Copy ROMs in destDir
def do_update(filterName):
  """Applies filter and copies ROMs into destination directory"""

  NARS.print_info('[Copy/Update ROMs]')
  NARS.print_info('Filter name = ' + filterName)

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_from_Config(filterName)
  sourceDir = filter_config.sourceDir
  destDir = filter_config.destDir

  # --- Check for errors, missing paths, etc...
  NARS.have_dir_or_abort(sourceDir, 'ROMsSource')
  NARS.have_dir_or_abort(destDir, 'ROMsDest')

  # --- Get MAME parent/clone dictionary --------------------------------------
  mame_xml_dic = parse_MAME_merged_XML()

  # --- Create main ROM list in sourceDir -------------------------------------
  rom_main_list = get_ROM_main_list(sourceDir)

  # --- Apply filter and create list of files to be copied --------------------
  mame_filtered_dic = filter_MAME_machines(mame_xml_dic, filter_config)
  rom_copy_list = create_copy_list(mame_filtered_dic, rom_main_list)

  # --- Copy/Update ROMs into destDir -----------------------------------------
  NARS.copy_ROM_list(rom_copy_list, sourceDir, destDir, __prog_option_sync, __prog_option_dry_run)

  # If --cleanROMs is on then delete unknown files.
  if __prog_option_clean_ROMs:
    NARS.clean_ROMs_destDir(rom_copy_list, destDir, __prog_option_dry_run)

  # --- Generate NFO XML files with information for launchers
  if __prog_option_generate_NFO:
    generate_MAME_NFO_files(rom_copy_list, mame_filtered_dic, destDir, __prog_option_dry_run)

  # --- Delete NFO files of ROMs not present in the destination directory.
  if __prog_option_clean_NFO:
    NARS.clean_NFO_destDir(destDir, __prog_option_dry_run)

# ----------------------------------------------------------------------------
# Copy ROMs in destDir
def do_update_CHD(filterName):
  """Applies filter and copies ROMs into destination directory"""

  NARS.print_info('[Copy/Update CHDs]')
  NARS.print_info('Filter name = ' + filterName)

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_from_Config(filterName)
  sourceDir = filter_config.sourceDir
  destDir = filter_config.destDir
  sourceDir_CHD = filter_config.sourceDir_CHD

  # --- Check for errors, missing paths, etc...
  NARS.have_dir_or_abort(sourceDir, 'sourceDir')
  NARS.have_dir_or_abort(sourceDir_CHD, 'sourceDir_CHD')
  NARS.have_dir_or_abort(destDir, 'destDir')

  # --- Get MAME parent/clone dictionary --------------------------------------
  mame_xml_dic = parse_MAME_merged_XML()

  # --- Create main ROM list in sourceDir -------------------------------------
  rom_main_list = get_ROM_main_list(sourceDir)

  # --- Apply filter and create list of files to be copied --------------------
  mame_filtered_dic = filter_MAME_machines(mame_xml_dic, filter_config)
  rom_copy_list = create_copy_list(mame_filtered_dic, rom_main_list)

  # --- Create list of CHDs and samples needed --------------------------------
  CHD_dic = create_copy_CHD_dic(mame_filtered_dic)

  # --- Copy/Update CHDs into destDir -----------------------------------------
  NARS.copy_CHD_dic(CHD_dic, sourceDir_CHD, destDir, __prog_option_sync, __prog_option_dry_run)

  # If --cleanCHDs is on then delete unknown CHD and directories.
  if __prog_option_clean_CHD:
    NARS.clean_CHDs_destDir(CHD_dic, destDir, __prog_option_dry_run)

# ----------------------------------------------------------------------------
def do_check_Artwork(filterName):
  """Checks for missing artwork and prints a report"""

  NARS.print_info('[Check-ArtWork]')
  NARS.print_info('Filter name = ' + filterName)

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_from_Config(filterName)
  destDir = filter_config.destDir
  thumbsSourceDir = filter_config.thumbsSourceDir
  fanartSourceDir = filter_config.fanartSourceDir

  # --- Check for errors, missing paths, etc...
  NARS.have_dir_or_abort(destDir, 'ROMsDest')
  NARS.have_dir_or_abort(thumbsSourceDir, 'ThumbsSource')
  NARS.have_dir_or_abort(fanartSourceDir, 'FanartSource')

  # --- Create a list of ROMs in destDir
  roms_destDir_list = []
  for file in os.listdir(destDir):
    if file.endswith(".zip"):
      thisFileName, thisFileExtension = os.path.splitext(file)
      roms_destDir_list.append(thisFileName)

  # --- Get MAME parent/clone dictionary --------------------------------------
  mame_xml_dic = parse_MAME_merged_XML()

  # --- Apply filter and create list of files to be copied --------------------
  mame_filtered_dic = filter_MAME_machines(mame_xml_dic, filter_config)
  rom_copy_list = create_copy_list(mame_filtered_dic, roms_destDir_list)
  
  # --- Mimic the behaviour of optimize_ArtWork_list() in xru-console
  # Crate a dictionary where key and value are the same (no artwork
  # substitution in xru-mame).
  artwork_copy_dic = {}
  for rom in rom_copy_list:
    artwork_copy_dic[rom] = rom

  # --- Print list in alphabetical order
  NARS.print_info('[Artwork report]')
  num_original = 0
  num_replaced = 0
  num_have_thumbs = 0
  num_missing_thumbs = 0
  num_have_fanart = 0
  num_missing_fanart = 0
  for rom_baseName in sorted(roms_destDir_list):
    NARS.print_info("Game        " + rom_baseName + ".zip")
    if rom_baseName not in artwork_copy_dic:
      print(' Not found')
    else:
      art_baseName = artwork_copy_dic[rom_baseName]

      # --- Check if artwork exist
      thumb_Source_fullFileName = thumbsSourceDir + art_baseName + '.png'
      fanart_Source_fullFileName = fanartSourceDir + art_baseName + '.png'

      # - Has artwork been replaced?
      if rom_baseName != art_baseName:
        num_replaced += 1
        print(' Replaced   ' + art_baseName)
      else:
        num_original += 1
        print(' Original   ' + art_baseName)

      # - Have thumb
      if not os.path.isfile(thumb_Source_fullFileName):
        num_missing_thumbs += 1
        print(' Missing T  ' + art_baseName + '.png')
      else:
        num_have_thumbs += 1
        print(' Have T     ' + art_baseName + '.png')

      # - Have fanart
      if not os.path.isfile(fanart_Source_fullFileName):
        num_missing_fanart += 1
        print(' Missing F  ' + art_baseName + '.png')
      else:
        num_have_fanart += 1
        print(' Have F     ' + art_baseName + '.png')

  NARS.print_info('[Report]')
  NARS.print_info('Number of ROMs in destDir  = ' + str(len(roms_destDir_list)))
  NARS.print_info('Number of ArtWork found    = ' + str(len(artwork_copy_dic)))
  NARS.print_info('Number of original ArtWork = ' + str(num_original))
  NARS.print_info('Number of replaced ArtWork = ' + str(num_replaced))
  NARS.print_info('Number of have Thumbs    = ' + str(num_have_thumbs))
  NARS.print_info('Number of missing Thumbs = ' + str(num_missing_thumbs))
  NARS.print_info('Number of have Fanart    = ' + str(num_have_fanart))
  NARS.print_info('Number of missing Fanart = ' + str(num_missing_fanart))

# ----------------------------------------------------------------------------
def do_update_Artwork(filterName):
  """Reads ROM destDir and copies Artwork"""

  NARS.print_info('[Updating/copying ArtWork]')
  NARS.print_info('Filter name = ' + filterName)

  # --- Get configuration for the selected filter and check for errors
  filter_config = get_Filter_from_Config(filterName)
  destDir = filter_config.destDir
  thumbsSourceDir = filter_config.thumbsSourceDir
  fanartSourceDir = filter_config.fanartSourceDir
  thumbsDestDir = filter_config.thumbsDestDir
  fanartDestDir = filter_config.fanartDestDir

  # --- Check for errors, missing paths, etc...
  NARS.have_dir_or_abort(destDir, 'ROMsDest')
  NARS.have_dir_or_abort(thumbsSourceDir, 'ThumbsSource')
  NARS.have_dir_or_abort(fanartSourceDir, 'FanartSource')
  NARS.have_dir_or_abort(thumbsDestDir, 'ThumbsDest')
  NARS.have_dir_or_abort(fanartDestDir, 'FanartDest')

  # --- Create a list of ROMs in destDir
  roms_destDir_list = []
  for file in os.listdir(destDir):
    if file.endswith(".zip"):
      thisFileName, thisFileExtension = os.path.splitext(file)
      roms_destDir_list.append(thisFileName)

  # --- Get MAME parent/clone dictionary --------------------------------------
  mame_xml_dic = parse_MAME_merged_XML()

  # --- Apply filter and create list of files to be copied --------------------
  mame_filtered_dic = filter_MAME_machines(mame_xml_dic, filter_config)
  rom_copy_list = create_copy_list(mame_filtered_dic, roms_destDir_list)

  # --- Mimic the behaviour of optimize_ArtWork_list() in xru-console
  # Crate a dictionary where key and value are the same (no artwork
  # substitution in xru-mame).
  artwork_copy_dic = {}
  for rom in rom_copy_list:
    artwork_copy_dic[rom] = rom

  # --- Copy/Update artwork    
  NARS.copy_ArtWork_list(filter_config, artwork_copy_dic, __prog_option_sync, __prog_option_dry_run)

  # --- If --cleanArtWork is on then delete unknown files.
  if __prog_option_clean_ArtWork:
    NARS.clean_ArtWork_destDir(filter_config, artwork_copy_dic, __prog_option_dry_run)

def do_printHelp():
  print("""\033[32mUsage: nars-mame.py [options] <command> [filter]\033[0m

\033[32mCommands:\033[0m
\033[31musage\033[0m                     Print usage information (this text)
\033[31mreduce-XML\033[0m                Takes MAME XML as input and writes an stripped XML.
\033[31mmerge-XML\033[0m                 Takes MAME XML (reduced) info file and Catver.ini a mergued XML.
\033[31mlist-merged\033[0m               List every ROM set system in the merged MAME XML.
\033[31mlist-categories\033[0m           Reads Catver.ini and makes a histogram of the categories.
\033[31mlist-drivers\033[0m              Reads merged XML database and prints a histogram of the drivers.
\033[31mlist-controls\033[0m             Reads merged XML database and prints a histogram of the game controls.
\033[31mlist-years\033[0m                Reads merged XML database and prints a histogram of the game release year.
\033[31mquery <machine>\033[0m           Prints information about a machine.
\033[31mlist\033[0m                      List filters defined in configuration file.
\033[31mdiff <filterA> <filterB>\033[0m  Compares filter A and filter B and print differences.
\033[31mcheck <filter>\033[0m            Applies filter and checks you source directory for Have and Missing ROMs.
\033[31mcopy <filter>\033[0m             Applies filter and copies sourceDir ROMs into destDir.
\033[31mupdate <filter>\033[0m           Like copy, but only copies files if file size is different.
\033[31mcopy-chd <filter>\033[0m         Applies filter and copies sourceDir CHDs into destDir.
\033[31mupdate-chd <filter>\033[0m       Like copy-chd, but only copies files if CHD size is different.
\033[31mcheck-artwork <filter>\033[0m    Checks for Have and Missing artwork.
\033[31mcopy-artwork <filter>\033[0m     Copies artwork to destination
\033[31mupdate-artwork <filter>\033[0m   Like copy-artwork, but also delete unknown images in artwork destination???

\033[32mOptions:\033[0m
\033[35m-h\033[0m, \033[35m--help\033[0m                Print short command reference
\033[35m-v\033[0m, \033[35m--verbose\033[0m             Print more information about what's going on
\033[35m-l\033[0m, \033[35m--log\033[0m                 Save program output in xru-mame-log.txt.
\033[35m--logto\033[0m \033[31m[logName]\033[0m         Save program output in the file you specify.
\033[35m--dryRun\033[0m                  Don't modify destDir at all, just print the operations to be done.
\033[35m--cleanROMs\033[0m               Deletes ROMs in destDir not present in the filtered ROM list.
\033[35m--generateNFO\033[0m             Generates NFO files with game information for the launchers.
\033[35m--cleanNFO\033[0m                Deletes ROMs in destDir not present in the filtered ROM list.
\033[35m--cleanCHD\033[0m                Deletes unknown CHDs in destination directory.
\033[35m--cleanArtWork\033[0m            Deletes unknown Artowork in destination directories.""")

# -----------------------------------------------------------------------------
# main function
# -----------------------------------------------------------------------------
print('\033[36mNARS Advanced ROM Sorting - MAME edition\033[0m' +
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
parser.add_argument('command',
    help="usage, reduce-XML, merge, list-merged, \
          list-categories, list-drivers, list-controls, list-years,\
          query, list, check, copy, update \
          copy-chd, update-chd \
          check-artwork, copy-artwork, update-artwork", nargs = 1)
parser.add_argument("filterName", help="MAME ROM filter name", nargs = '?')
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
if args.generateNFO:  __prog_option_generate_NFO = 1
if args.cleanNFO:     __prog_option_clean_NFO = 1
if args.cleanArtWork: __prog_option_clean_ArtWork = 1
if args.cleanCHD:     __prog_option_clean_CHD = 1

# --- Positional arguments that don't require parsing of the config file ---
command = args.command[0]
if command == 'usage':
  do_printHelp()
  sys.exit(0)

# --- Check arguments that require a filterName ---
if command == 'query' or \
   command == 'check' or command == 'copy' or command == 'update' or \
   command == 'copy-chd' or command == 'update-chd' or \
   command == 'check-artwork' or command == 'copy-artwork' or command == 'update-artwork':
  if args.filterName is None:
    print('\033[31m[ERROR]\033[0m Command "{0}" requires a filter name'.format(command))
    sys.exit(10)

# --- Read configuration file ---
configuration = parse_File_Config()

# --- Positional arguments that don't require a filterName ---
if command == 'reduce-XML':
  do_reduce_XML()
elif command == 'merge-XML':
  do_merge()
elif command == 'list-merged':
  do_list_merged()
elif command == 'list-categories':
  do_list_categories()
elif command == 'list-drivers':
  do_list_drivers()
elif command == 'list-controls':
  do_list_controls()
elif command == 'list-years':
  do_list_years()
elif command == 'query':
  do_query(args.filterName)
elif command == 'list':
  do_list_filters()
elif command == 'check':
  do_check(args.filterName)
elif command == 'copy':
  do_update(args.filterName)
elif command == 'update':
  __prog_option_sync = 1
  do_update(args.filterName)
elif command == 'copy-chd':
  do_update_CHD(args.filterName)
elif command == 'update-chd':
  __prog_option_sync = 1
  do_update_CHD(args.filterName)
elif command == 'check-artwork':
  do_check_Artwork(args.filterName)
elif command == 'copy-artwork':
  do_update_Artwork(args.filterName)
elif command == 'update-artwork':
  __prog_option_sync = 1
  do_update_Artwork(args.filterName)
else:
  print('\033[31m[ERROR]\033[0m Unrecognised command "{0}"'.format(command))
  sys.exit(1)

# Bye bye
sys.exit(0)
