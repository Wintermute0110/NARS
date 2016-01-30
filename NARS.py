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

# * ElementTree XML parser
import xml.etree.ElementTree as ET

# * This is supposed to be much faster than ElementTree
#   See http://effbot.org/zone/celementtree.htm
#   Tests with list-* commands indicate this 6x faster than ElementTree
#   HOWEVER: the reduce command takes AGES checking the dependencies!!!
import xml.etree.cElementTree as cET

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

def have_dir_or_abort(dirName):
  if not os.path.isdir(dirName):
    print_error('\033[31m[ERROR]\033[0m Directory does not exist ' + dirName);
    sys.exit(10);

# -----------------------------------------------------------------------------
# Filesystem helper functions
# -----------------------------------------------------------------------------
def copy_ROM_file(fileName, sourceDir, destDir, __prog_option_dry_run):
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
def update_ROM_file(fileName, sourceDir, destDir, __prog_option_dry_run):
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
