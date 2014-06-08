#!/usr/bin/python
# XBMC ROM utilities
# Wintermute0110 <wintermute0110@gmail.com>

import sys, os
import argparse
import xml.etree.ElementTree as ET

# --- Global variables
__software_version = '0.1.0';
__config_configFileName = 'xru-launcher-AL-config.xml';

# --- Config file options global class (like a C struct)
class ConfigFile:
  pass
class ConfigFileFilter:
  pass
configuration = ConfigFile();

# --- Program options (from command line)
# __prog_option_dry_run = 0;

# =============================================================================
__debug_parse_File_Config = 0;
def parse_File_Config():
  "Parses configuration file"

  print '[Parsing config file]';
  tree = ET.parse(__config_configFileName);
  root = tree.getroot();

  # - This iterates through the collections
  configFile = ConfigFile();

  # --- Main configuration options (default to empty string)
  configFile.AL_config_file = '';
  configFile.launchers_dic = {};

  # --- Parse general options
  general_tag_found = 0;
  for root_child in root:
    if root_child.tag == 'configFile':
      general_tag_found = 1;
      configFile.AL_config_file = root_child.text;
  if not general_tag_found:
    print 'Configuration error. <configFile> tag not found';
    sys.exit(10);

  # --- Parse filters
  for root_child in root:
    if root_child.tag == 'launcher':
      if __debug_parse_File_Config: 
        print '<launcher>';
      if 'name' in root_child.attrib:
        filter_class = ConfigFileFilter();
        filter_class.name = root_child.attrib['name'];
        if __debug_parse_File_Config: 
          print ' name = ' + filter_class.name;
        destDirFound = 0;
        for filter_child in root_child:
          if filter_child.tag == 'ROMsDest':
            if filter_child.text == None:
              print '<ROMsDest> Empty directory name';
              sys.exit(10);
            if __debug_parse_File_Config: 
              print ' ROMsDest = ' + filter_child.text;
            destDirFound = 1;
            filter_class.destDir = filter_child.text

          elif filter_child.tag == 'FanartDest':
            if filter_child.text == None:
              print '<FanartDest> Empty directory name';
            if __debug_parse_File_Config: 
              print ' FanartDest = ' + filter_child.text;
            filter_class.fanartDestDir = filter_child.text

          elif filter_child.tag == 'ThumbsDest':
            if filter_child.text == None:
              print '<ThumbsDest> Empty directory name';
            if __debug_parse_File_Config: 
              print ' ThumbsDest = ' + filter_child.text;
            filter_class.thumbsDestDir = filter_child.text
            
          else:
            print 'Unrecognised tag inside <launcher>';
            sys.exit(10);

        # Check for errors in this
        if not destDirFound:
          print 'destination directory not found in config file';
          sys.exit(10);

        # Aggregate filter to configuration main variable
        configFile.launchers_dic[filter_class.name] = filter_class;
      else:
        print '<launcher> tag does not have name attribute';
        sys.exit(10);

  if __debug_parse_File_Config:
    print 'AL_config_file = ', configFile.AL_config_file;

  # --- Check for errors

  return configFile;

# =============================================================================
def do_list():
  "Checks Advanced Launcher config file for updates"

  print '[Listing Advanced Launcher launchers]';
  AL_configFileName = configuration.AL_config_file;
  print "Parsing Advanced Launcher configuration file...",;
  tree = ET.parse(AL_configFileName);
  print "done"
  root = tree.getroot();

  # - This iterates through the root element
  # for child in root:
  #   print '[root child]', child.tag;

  # --- Get launchers child
  categories = root[0];
  launchers = root[1];
  # for child in categories:
  #   print '[categories child]', child.tag;
  
  #  <launchers>
  #  <launcher>
  #    <id>c4287c13f40c61b7959b6ee8f1790d34</id>
  #    <name>Game Boy Advance (RetroArch VBA-Next)</name>
  #  ...
  # <roms>
  #      <rom>
  #        <id>6a20ff392783cd64e444c4dd1f43004a</id>
  #        <name>007 - Everything or Nothing</name>
  #        <filename>/path/007 - Everything or Nothing (USA, Europe) (En,Fr,De).zip</filename>
  #        <thumb>/path/thumbs/007 - Everything or Nothing (USA, Europe) (En,Fr,De).jpg</thumb>
  #        <fanart>/path/007 - Everything or Nothing (USA, Europe) (En,Fr,De).jpg</fanart>
  #  ...
  for child in launchers:
    print '<Launcher>';

    # --- Launcher data
    lauch_name = child.find('name');
    lauch_application = child.find('application');
    lauch_args = child.find('args');
    lauch_rompath = child.find('rompath');
    lauch_thumbpath = child.find('thumbpath');
    lauch_fanartpath = child.find('fanartpath');
    lauch_romext = child.find('romext');

    print ' lauch_name        = "' + lauch_name.text + '"';
    print ' lauch_application = ' + lauch_application.text;
    print ' lauch_args        = ' + lauch_args.text;
    print ' lauch_rompath     = ' + lauch_rompath.text;
    print ' lauch_thumbpath   = ' + lauch_thumbpath.text;
    print ' lauch_fanartpath  = ' + lauch_fanartpath.text;
    print ' lauch_romext      = ' + lauch_romext.text;

    # --- Traverse the list of roms
    continue;
    roms_list = child.find('roms');
    for child_roms in roms_list:
      rom_name = child_roms.find('name');
      rom_filename = child_roms.find('filename');
      rom_thumb = child_roms.find('thumb');
      rom_fanart = child_roms.find('fanart');

      if rom_name.text is not None:
        print ' rom_name     = ' + rom_name.text;
      if rom_filename.text is not None:
        print ' rom_filename = ' + rom_filename.text;
      if rom_thumb.text is not None:
        print ' rom_thumb    = ' + rom_thumb.text;
      if rom_fanart.text is not None:
        print ' rom_fanart   = ' + rom_fanart.text;

def do_list_config():
  "List of this program configuration file"
  print '[Listing configuration]';
  
  print 'Advanced Launcher configuration file';
  print ' ' + configuration.AL_config_file;

  for key in configuration.launchers_dic:
    launcher = configuration.launchers_dic[key];
    print '<Launcher>';
    print ' name = ' + launcher.name;
    print ' destDir = ' + launcher.destDir;
    print ' fanartDestDir = ' + launcher.fanartDestDir;
    print ' thumbsDestDir = ' + launcher.thumbsDestDir;
    
#
# Checks AL configuration file. The following checks are performed
#
# a) ...
#
def do_check():
  "Checks Advanced Launcher config file for updates"

  print '[Listing Advanced Launcher launchers]';
  AL_configFileName = configuration.AL_config_file;
  print "Parsing Advanced Launcher configuration file...",;
  tree = ET.parse(AL_configFileName);
  print "done"
  root = tree.getroot();
  categories = root[0];
  launchers = root[1];
  update_launchers_list = [];
  not_checked_launchers_list = [];
  for child in launchers:
    print '<Launcher>';
    
    # --- Launcher data
    lauch_name = child.find('name');
    lauch_application = child.find('application');
    lauch_rompath = child.find('rompath');

    print ' lauch_name = "' + lauch_name.text + '"';
    # print ' lauch_application = ' + lauch_application.text;
    # print ' lauch_rompath     = ' + lauch_rompath.text;

    # --- Only do Genesis to DEBUG
    # if lauch_name.text != 'Genesis (Mednafen)':
    #   continue;

    # List of roms
    roms_list = child.find('roms');

    # - Check if the AL path is reachable. If not, check if the user
    #   configured a local path for this launcher. If not, then don't
    #   check this launcher and warn the user.
    AL_rom_path = lauch_rompath.text;
    localPath = AL_rom_path;
    launcher_name = lauch_name.text;
    if not os.path.isdir(localPath):
      print ' Not found AL configuration file ROM path'
      # Locate laucher in config file
      if launcher_name in configuration.launchers_dic:
        print ' Using configured ROM local path for this launcher'
        launcher_conf = configuration.launchers_dic[launcher_name];
        localPath = launcher_conf.destDir;
        if not os.path.isdir(localPath):
          print ' Local ROM path configuration not found';
          print ' Aborting checking this launcher';
          not_checked_launchers_list.append(launcher_name);
          continue;
      else:
        print ' Local ROM path configuration for this launcher not found'; 
        print ' Aborting checking this launcher';
        not_checked_launchers_list.append(launcher_name);
        continue;
    else:
      print ' Using AL configuration file ROM path';

    # - Traverse the list of roms and check
    launcher_ROM_list = [];
    error_AL_not_found_rom = 0;
    for child_roms in roms_list:
      rom_name = child_roms.find('name');
      rom_filename = child_roms.find('filename');
      rom_thumb = child_roms.find('thumb');
      rom_fanart = child_roms.find('fanart');

      # Check that file exists
      (head, tail) = os.path.split(rom_filename.text);
      launcher_ROM_list.append(tail);
      fullFilename = localPath + tail;
      if not os.path.isfile(fullFilename):
        error_AL_not_found_rom += 1;
    
    # - Now, traverse the list of ROMs in the rompath for this launcher, and
    #   check that the ROM exists in AL configuration
    error_AL_missing_rom = 0;
    for file in os.listdir(localPath):
      if file.endswith(".zip"):
        # print 'File = ' + file;
        (head, tail) = os.path.split(rom_filename.text);
        if tail not in launcher_ROM_list:
          error_AL_missing_rom += 1;

    print ' ' + str(error_AL_not_found_rom) + ' not found ROMs in AL configuration file';
    print ' ' + str(error_AL_missing_rom) + ' missing ROMs in AL configuration file';

    if error_AL_not_found_rom or error_AL_missing_rom:
      update_launchers_list.append(launcher_name);

  # --- Report if AL needs update or not
  print '[Report]';
  if len(not_checked_launchers_list) > 0:
    print 'The following launchers were not checked';
    for launcher in not_checked_launchers_list:
      print ' ' + launcher;
  else:
    print 'All launchers were checked.';

  if len(update_launchers_list) > 0:
    print 'Advanced Launcher needs an update for the following launchers';
    for launcher in update_launchers_list:
      print ' ' + launcher;
  else:
    print 'All launchers up to date';

def do_printHelp():
  print """
\033[32mUsage: xru-launcher-AL.py [options] <command>\033[0m

\033[32mCommands:\033[0m
 \033[31m usage\033[0m
    Print usage information (this text)

 \033[31m list\033[0m
    List every launcher found in Advanced Launcher configuration file.

 \033[31m list-config\033[0m
    List every launcher found in the configuration file.

 \033[31m check\033[0m
    Checks the Advanced Launcher configuration file and compares against the
    ROM folders. It reports if Advanced Launcher should rescan the ROM list.
  
\033[32mOptions:
  \033[35m-h\033[0m, \033[35m--help\033[0m
    Print short command reference"""

# =============================================================================
def main(argv):
  print '\033[36mXBMC ROM utilities - Advanced Launcher\033[0m' + \
        ' version ' + __software_version;

  # - Command line parser
  parser = argparse.ArgumentParser()
  parser.add_argument("command", help="usage, list, list-config, check")
  args = parser.parse_args();
  
  # --- Optional arguments

  # --- Positional arguments that don't require parsing of the config file
  if args.command == 'usage':
    do_printHelp();
    sys.exit(0);

  # --- Read configuration file
  global configuration; # Needed to modify global copy of globvar
  configuration = parse_File_Config(); 

  # --- Positional arguments
  if args.command == 'list':
    do_list();

  elif args.command == 'list-config':
    do_list_config();

  elif args.command == 'check':
    do_check();
    
  else:
    print 'Unrecognised command';

  sys.exit(0);

# No idea what's this...
if __name__ == "__main__":
  main(sys.argv[1:])
