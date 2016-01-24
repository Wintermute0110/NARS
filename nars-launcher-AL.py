#!/usr/bin/python
# XBMC ROM utilities - Advanced Launcher

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
import sys, os
import argparse
import xml.etree.ElementTree as ET

# --- Global variables
__software_version = '0.1.0';
__config_configFileName = 'xru-launcher-AL-config.xml';
__config_logFileName = 'xru-launcher-AL-log.txt';

# --- Config file options global class (like a C struct)
class ConfigFile:
  pass
class ConfigFileFilter:
  pass
configuration = ConfigFile();

# --- Program options (from command line)
__prog_option_log = 0;
__prog_option_log_filename = __config_logFileName;

# -----------------------------------------------------------------------------
# DEBUG functions
# -----------------------------------------------------------------------------
# None in this program

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

  log_level = Log.verb;

# --- Print/log to a specific level  
def pprint(level, print_str):
  global f_log;
  global log_level;

  # --- If file descriptor not open, open it
  if __prog_option_log:
    if f_log == 0:
      f_log = open(__config_logFileName, 'w')

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
# Filesystem interaction functions
# -----------------------------------------------------------------------------
# None in this program

# -----------------------------------------------------------------------------
# Configuration file functions
# -----------------------------------------------------------------------------
def parse_File_Config():
  "Parses configuration file"
  print_info('[Parsing config file]');
  try:
    tree = ET.parse(__config_configFileName);
  except IOError:
    print_error('[ERROR] cannot find file ' + __config_configFileName);
    sys.exit(10);
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
    pprint(Log.error, 'Configuration error. <configFile> tag not found');
    sys.exit(10);

  # --- Parse filters
  for root_child in root:
    if root_child.tag == 'launcher':
      pprint(Log.debug, '<launcher>');
      if 'name' in root_child.attrib:
        filter_class = ConfigFileFilter();
        filter_class.name = root_child.attrib['name'];
        pprint(Log.debug, ' name = ' + filter_class.name);
        destDirFound = 0;
        for filter_child in root_child:
          if filter_child.tag == 'ROMsDest':
            if filter_child.text == None:
              pprint(Log.error, '<ROMsDest> Empty directory name');
              sys.exit(10);
            pprint(Log.debug, ' ROMsDest = ' + filter_child.text);
            destDirFound = 1;
            filter_class.destDir = filter_child.text

          elif filter_child.tag == 'FanartDest':
            if filter_child.text == None:
              pprint(Log.info, '<FanartDest> Empty directory name');
            pprint(Log.debug, ' FanartDest = ' + filter_child.text);
            filter_class.fanartDestDir = filter_child.text

          elif filter_child.tag == 'ThumbsDest':
            if filter_child.text == None:
              pprint(Log.info, '<ThumbsDest> Empty directory name');
            pprint(Log.debug, ' ThumbsDest = ' + filter_child.text);
            filter_class.thumbsDestDir = filter_child.text
            
          else:
            pprint(Log.error, 'Unrecognised tag inside <launcher>');
            sys.exit(10);

        # Check for errors in this
        if not destDirFound:
          pprint(Log.error, 'destination directory not found in config file');
          sys.exit(10);

        # Aggregate filter to configuration main variable
        configFile.launchers_dic[filter_class.name] = filter_class;
      else:
        pprint(Log.error, '<launcher> tag does not have name attribute');
        sys.exit(10);

  pprint(Log.debug, 'AL_config_file = ' + configFile.AL_config_file);

  # --- Check for errors
  return configFile;

# -----------------------------------------------------------------------------
# Misc functions
# -----------------------------------------------------------------------------
# None in this program

# -----------------------------------------------------------------------------
# Main body functions
# -----------------------------------------------------------------------------
def do_list():
  "Checks Advanced Launcher config file for updates"
  pprint(Log.info, '[Listing Advanced Launcher launchers]');
  AL_configFileName = configuration.AL_config_file;
  # Don't log "waiting bar" like messages
  print "Parsing Advanced Launcher configuration file...",;
  try:
    tree = ET.parse(AL_configFileName);
  except IOError:
    print '\n';
    print_error('[ERROR] cannot find file ' + AL_configFileName);
    sys.exit(10);
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
    pprint(Log.info, '<Launcher>');

    # --- Launcher data
    lauch_name = child.find('name');
    lauch_application = child.find('application');
    lauch_args = child.find('args');
    lauch_rompath = child.find('rompath');
    lauch_thumbpath = child.find('thumbpath');
    lauch_fanartpath = child.find('fanartpath');
    lauch_romext = child.find('romext');

    pprint(Log.info, ' lauch_name        = "' + lauch_name.text + '"');
    pprint(Log.info, ' lauch_application = ' + lauch_application.text);
    pprint(Log.info, ' lauch_args        = ' + lauch_args.text);
    pprint(Log.info, ' lauch_rompath     = ' + lauch_rompath.text);
    pprint(Log.info, ' lauch_thumbpath   = ' + lauch_thumbpath.text);
    pprint(Log.info, ' lauch_fanartpath  = ' + lauch_fanartpath.text);
    pprint(Log.info, ' lauch_romext      = ' + lauch_romext.text);

    # --- Traverse the list of roms
    continue;
    roms_list = child.find('roms');
    for child_roms in roms_list:
      rom_name = child_roms.find('name');
      rom_filename = child_roms.find('filename');
      rom_thumb = child_roms.find('thumb');
      rom_fanart = child_roms.find('fanart');

      if rom_name.text is not None:
        pprint(Log.info, ' rom_name     = ' + rom_name.text);
      if rom_filename.text is not None:
        pprint(Log.info, ' rom_filename = ' + rom_filename.text);
      if rom_thumb.text is not None:
        pprint(Log.info, ' rom_thumb    = ' + rom_thumb.text);
      if rom_fanart.text is not None:
        pprint(Log.info, ' rom_fanart   = ' + rom_fanart.text);

def do_list_config():
  "List of this program configuration file"
  pprint(Log.info, '[Listing configuration]');  
  pprint(Log.info, 'Advanced Launcher configuration file');
  pprint(Log.info, ' ' + configuration.AL_config_file);

  for key in configuration.launchers_dic:
    launcher = configuration.launchers_dic[key];
    pprint(Log.info, '<Launcher>');
    pprint(Log.info, ' name          = ' + launcher.name);
    pprint(Log.info, ' destDir       = ' + launcher.destDir);
    pprint(Log.info, ' fanartDestDir = ' + launcher.fanartDestDir);
    pprint(Log.info, ' thumbsDestDir = ' + launcher.thumbsDestDir);
    
# Checks AL configuration file. The following checks are performed
#
def do_check():
  "Checks Advanced Launcher config file for updates"

  print_info('[Checking Advanced Launcher launchers]');
  AL_configFileName = configuration.AL_config_file;
  print "Parsing Advanced Launcher configuration file...",;
  try:
    tree = ET.parse(AL_configFileName);
  except IOError:
    print '\n';
    print_error('[ERROR] cannot find file ' + AL_configFileName);
    sys.exit(10);
  print "done"
  root = tree.getroot();
  categories = root[0];
  launchers = root[1];
  update_launchers_list = [];
  checked_launchers_list = [];
  not_checked_launchers_list = [];
  for child in launchers:
    lauch_name = child.find('name');
    print_info("<Launcher> '" + lauch_name.text + "'");

    # --- Launcher data
    lauch_application = child.find('application');
    lauch_rompath = child.find('rompath');

    pprint(Log.verb, ' lauch_application = ' + lauch_application.text);
    pprint(Log.verb, ' lauch_rompath     = ' + lauch_rompath.text);

    # List of roms
    roms_list = child.find('roms');

    # - Check if the AL path is reachable. If not, check if the user
    #   configured a local path for this launcher. If not, then don't
    #   check this launcher and warn the user.
    AL_rom_path = lauch_rompath.text;
    localPath = AL_rom_path;
    launcher_name = lauch_name.text;
    if not os.path.isdir(localPath):
      pprint(Log.info,  ' Not found AL configuration file ROM path')
      # Locate laucher in config file
      if launcher_name in configuration.launchers_dic:
        pprint(Log.info,  ' Using configured ROM local path for this launcher')
        launcher_conf = configuration.launchers_dic[launcher_name];
        localPath = launcher_conf.destDir;
        if not os.path.isdir(localPath):
          pprint(Log.info,  ' Local ROM path configuration not found');
          pprint(Log.info,  ' Aborting checking this launcher');
          not_checked_launchers_list.append(launcher_name);
          continue;
      else:
        pprint(Log.info,  ' Local ROM path configuration for this launcher not found');
        pprint(Log.info,  ' Aborting checking this launcher');
        not_checked_launchers_list.append(launcher_name);
        continue;
    else:
      pprint(Log.info,  ' Using AL configuration file ROM path');

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

    pprint(Log.info,  ' ' + str(error_AL_not_found_rom) + ' not found ROMs in AL configuration file');
    pprint(Log.info,  ' ' + str(error_AL_missing_rom) + ' missing ROMs in AL configuration file');

    if error_AL_not_found_rom or error_AL_missing_rom:
      update_launchers_list.append(launcher_name);
    else:
      checked_launchers_list.append(launcher_name);

  # --- Report if AL needs update or not
  pprint(Log.info,  '[Report]');
  if len(not_checked_launchers_list) > 0:
    pprint(Log.info,  'The following launchers were not checked');
    for launcher in not_checked_launchers_list:
      pprint(Log.info,  ' ' + launcher);
  else:
    pprint(Log.info,  'All launchers were checked.');

  if len(checked_launchers_list) > 0:
    pprint(Log.info,  'The following launchers were checked and are up to date');
    for launcher in checked_launchers_list:
      pprint(Log.info,  ' ' + launcher);
  else:
    pprint(Log.info,  'No launchers were checked.');

  if len(update_launchers_list) > 0:
    pprint(Log.info,  'Advanced Launcher needs an update for the following launchers');
    for launcher in update_launchers_list:
      pprint(Log.info,  ' ' + launcher);
  else:
    pprint(Log.info,  'All launchers up to date');

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

\033[32mOptions:\033[0m
  \033[35m-h\033[0m, \033[35m--help\033[0m
    Print short command reference

  \033[35m-v\033[0m, \033[35m--verbose\033[0m
    Print more information about what's going on

  \033[35m-l\033[0m, \033[35m--log\033[0m
    Save program output in xru-launcher-AL-log.txt"""

# -----------------------------------------------------------------------------
# main function
# -----------------------------------------------------------------------------
def main(argv):
  print '\033[36mXBMC ROM utilities - Advanced Launcher\033[0m' + \
        ' version ' + __software_version;

  # --- Command line parser
  parser = argparse.ArgumentParser()
  parser.add_argument('-v', '--verbose', help="be verbose", action="count")
  parser.add_argument('-l', '--log', help="log output to default file", \
     action='store_true')
  parser.add_argument('--logto', help="log output to specified file", \
     nargs = 1)
  parser.add_argument("command", help="usage, list, list-config, check", nargs = 1)
  args = parser.parse_args();

  # --- Optional arguments
  global __prog_option_log, __prog_option_log_filename;

  if args.verbose:
    if args.verbose == 1:
      change_log_level(Log.verb);
    elif args.verbose == 2:
      change_log_level(Log.vverb);
    elif args.verbose >= 3:
      change_log_level(Log.debug);
  if args.log:
    __prog_option_log = 1;
  if args.logto:
    __prog_option_log = 1;
    __prog_option_log_filename = args.logto[0];

  # --- Positional arguments that don't require parsing of the config file
  command = args.command[0];
  if command == 'usage':
    do_printHelp();
    sys.exit(0);

  # --- Read configuration file
  global configuration; # Needed to modify global copy of globvar
  configuration = parse_File_Config();

  # --- Positional arguments
  if command == 'list':
    do_list();

  elif command == 'list-config':
    do_list_config();

  elif command == 'check':
    do_check();
    
  else:
    print_error('Unrecognised command');
    sys.exit(1);

  sys.exit(0);

# No idea what's this...
if __name__ == "__main__":
  main(sys.argv[1:])