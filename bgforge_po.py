#!/usr/bin/env python
# coding: utf-8

version='1.0.0'

import io
import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import datetime
import collections
import polib
from operator import itemgetter
import os
import shutil
import subprocess
from contextlib import contextmanager
import fileinput
import ConfigParser
import csv

valid_extensions = [ 'msg', 'txt', 'sve', 'tra']

file_format = {
  'msg': {
    'pattern':     '{(\d+)}{([^}]*)}{([^}]*)}',
    'dotall':       True,
    'index':        0,
    'value':        2,
    'context':      1,
    'audio':        1,
    'line_format': '{{{}}}{{}}{{{}}}\n',
    'line_format_context': '{{{}}}{{{}}}{{{}}}\n',
  },
  'sve': {
    'pattern':     '(\d+):(.*)',
    'dotall':       False,
    'index':        0,
    'value':        1,
    'line_format': '{}:{}\n',
  },
  'txt': {
    'pattern':     '(\d+):(.*)',
    'dotall':       False,
    'index':        0,
    'value':        1,
    'comment':     'indexed_txt',
    'line_format': '{}:{}\n',
  },
  'tra': {
    'pattern':     '@(\d+)\s*?=\s*?~([^~]*?)~(?:\s)?(?:\[([^]]*)\])?(?:~([^~]*)~)?',
    'dotall':       True,
    'index':        0,
    'value':        1,
    'context':      2,
    'audio':        2,
    'female':       3,
    'line_format': '@{} = ~{}~\n',
    'line_format_context': '@{} = ~{}~ [{}]\n',
  },
}

ini = 'bgforge.ini'
main_ini_section = 'main'
po_dirname = 'po'
po_dir_key = 'po_dir'
tra_dir_key = 'tra_dir'
src_lang_key = 'src_lang'
female_postfix = '_female.csv'

defaults = {
  'encoding': 'cp1252',
  'tra_dir': '.',
  'src_lang': 'english',
}

encodings = {
  'schinese': 'cp936',
  'tchinese': 'cp950',

  'czech': 'cp1250',

  'japanese': 'cp932',

  'korean': 'cp949',

  'polish': 'cp1250',
  'polski': 'cp1250',

  'russian': 'cp1251',
}

dos_encodings = {
#  'czech': 'cp852',

#  'polish': 'cp852',
#  'polski': 'cp852',

  'russian': 'cp866',

#  'french': 'cp850',
#  'francais': 'cp850',

#  'german': 'cp850',
#  'deutsch': 'cp850',

#  'italian': 'cp850',
#  'italiano': 'cp850',

#  'spanish': 'cp850',
#  'espanol': 'cp850',
#  'castilian': 'cp850',
#  'castellano': 'cp850',
}

dos_filenames = [
  'setup.tra',
  'install.tra',
]

utf_filenames = [
  'ee.tra',
]

metadata = {
  'Project-Id-Version': 'PACKAGE VERSION',
  'Report-Msgid-Bugs-To': '',
  'POT-Creation-Date': '1970-1-01 00:00+0000',
  'PO-Revision-Date': 'YEAR-MO-DA HO:MI+ZONE',
  'Last-Translator': 'FULL NAME <EMAIL@ADDRESS>',
  'Language-Team': 'LANGUAGE <LL@li.org>',
  'Language': '',
  'MIME-Version': '1.0',
  'Content-Type': 'text/plain; charset=UTF-8',
  'Content-Transfer-Encoding': '8bit',
  'X-Generator': 'bgforge_po v.{}'.format(version),
}

empty_comment = 'LEAVE empty space in translation'


#file and dir manipulation
#################################
def get_ext(path):
  try:
    ext = path.rsplit('.',1)[1].lower()
  except:
    ext = None
  return ext

def basename(path):
  if path.endswith('/'):
    path = path[:-1]
  return os.path.abspath(path).rsplit('/',1)[1]

def parent_dir(path):
  if path.endswith('/'):
    path = path[:-1]
  return os.path.abspath(path).rsplit('/',1)[0]

def strip_ext(filename):
  return filename.rsplit('.',1)[0]

def get_dir(path):
  return path.rsplit('/',1)[0]

def create_dir(path):
  if not os.path.isdir(path):
    os.makedirs(path)

#lowercase directory
def lowercase_rename(root_dir,items):
  for item in items:
    old_name=os.path.join(root_dir, item)
    new_name=os.path.join(root_dir, item.lower())
    if new_name != old_name:
      print "renaming {} to {}".format(old_name, new_name)
      os.rename(old_name, new_name)
def lowercase_recursively(dir): #this is the function that is actually used
  for dir_name, subdir_list, file_list in os.walk(dir,topdown=False):
    lowercase_rename(dir_name,file_list)
    lowercase_rename(dir_name,subdir_list)

def get_value(key, filename = ini, ini_section = main_ini_section):
  parser = ConfigParser.SafeConfigParser()
  try:
    parser.read(filename)
    try:
      v = parser.get(ini_section, key)
    except:
      v = defaults[key]
  except:
    v = defaults[key]
  return v

def get_po_dir():
  tra_dir = get_value(tra_dir_key)
  po_dir = tra_dir + '/' + po_dirname
  return po_dir

def get_poify_dir():
  tra_dir = get_value(tra_dir_key)
  src_lang = get_value(src_lang_key)
  poify_dir = tra_dir + '/' + src_lang
  return poify_dir

def dir_or_exit(d):
  if os.path.isdir(d):
    print 'Found directory {}'.format(d)
  else:
    print 'Directory {} does not exist, cannot continue!'.format(d)
    sys.exit(1)

@contextmanager
def cd(newdir):
  prevdir = os.getcwd()
  os.chdir(os.path.expanduser(newdir))
  try:
    yield
  finally:
    os.chdir(prevdir)

def get_enc(po_name,
            po_occurence_name = '',
            encoding_dict = encodings,
            dos_encoding_dict = dos_encodings,
            dos_filename_list = dos_filenames,
            utf_filename_list = utf_filenames):
  encoding = defaults['encoding']
  lang = strip_ext(basename(po_name))
  filename = basename(po_occurence_name)

  if lang in encoding_dict:
    try: encoding = encoding_dict[lang]
    except: pass

  if filename in dos_filenames:
    try: encoding = dos_encoding_dict[lang]
    except: pass

  if filename in utf_filenames:
    try: encoding = 'utf-8'
    except: pass

  utf_name = re.compile('.*_ee.tra$')
  if utf_name.match(filename):
    try: encoding = 'utf-8'
    except: pass

  return encoding

################################


#returns PO file object
def file2po(filepath, encoding = defaults['encoding'], noempty = False):

  trans = TRANSFile(filepath=filepath, is_source=True) #load translations

  po = polib.POFile()
  po.metadata = metadata

  entry_added = 0
  for t in trans:
    index = t['index']
    value = t['value']
    audio = t['audio']
    comment = t['comment']

    # try to find a matching entry first
    dupe = 0
    for e in po:
      if e.msgid == value and e.msgctxt == audio:
        e.occurrences.append((filepath, index))
        dupe = 1
    if dupe == 1:
      dupe = 0
      continue # pass on to the next trans entry

    #no matching msgid + msgctxt, add new entry
    entry = polib.POEntry(
        msgid=value,
        msgstr='',
        occurrences=[(filepath, index),],
        msgctxt = audio,
        comment = comment,
    )
    po.append(entry)

  return(po)




#check if extract file is present in po, exit with error if not
def check_path_in_po(po, path):
  present_files = []
  for entry in po:
    for eo in entry.occurrences:
      present_files.append(eo[0])
  present_files_list = sorted(set(present_files))
  if not path in present_files_list:
    print "{} is not present in selected PO file".format(path)
    print "supply one of present files with --path argument:"
    for pf in present_files_list:
      print pf
    sys.exit(1)

#extract and write to disk a single file from PO object
def po2file(po, output_file, encoding, occurence_path, newline='\r\n'):
  ext = get_ext(output_file)
  ff = file_format[ext]
  line_format = ff['line_format']
  try: #if context is present in file format
    line_format_context = ff['line_format_context']
    context_order = ff['context']
  except:
    pass

  context = ''
  resulting_entries = []
  for entry in po:
    for eo in entry.occurrences:
      if eo[0] == occurence_path:

        index = int(eo[1]) #need int because later will sort

        if entry.msgstr == '': #if not translated, keep msgid
          value = entry.msgid
        else:
          value = entry.msgstr

        #empty lines detected by comment
        if entry.comment == empty_comment:
          value = ''

        if entry.msgctxt != None:
          context = entry.msgctxt
          resulting_entries.append([index,value,context])
        else:
          resulting_entries.append([index,value])

  resulting_entries.sort() #because duplicate entries may mess up order
  index_order = ff['index']
  value_order = ff['value']

  lines = []
  for re in resulting_entries:
    try: #if context exists
      lines.append(line_format_context.format(re[index_order],re[value_order],re[context_order]))
    except: #no context
      lines.append(line_format.format(re[0],re[1]))

  file = io.open(output_file, 'w', encoding=encoding, newline=newline)
  for line in lines:
    file.write(line.encode(encoding,'replace').decode(encoding).decode('utf-8'))
  file.close()


#returns PO file object
def file2msgstr(input_file, po, path, encoding = defaults['encoding']):
  trans = TRANSFile(filepath=input_file, encoding=encoding) #load translations
  female_strings = []

  # map entries to occurences for faster access, part 1
  entries_dict = collections.OrderedDict()
  for e in po:
    for eo in e.occurrences:
      entries_dict[(eo[0], eo[1])] = e

  for t in trans:
    index = t['index']
    value = t['value']
    audio = t['audio']
    female = t['female']

    if value != None and value != '':
      if (path, index) in entries_dict:
        # map entries to occurences for faster access, part 2
        e2 = entries_dict[(path, index)]
        if e2.msgstr != None and e2.msgstr != '' and e2.msgstr != value:
          print "WARN: differing msgstr values found for {}\nOverwriting first string with second:\n\"{}\"\n\"{}\"".format(e2.occurrences, e2.msgstr, value)

#        e2.msgstr = value # temp if
        if e2.msgid != value:
          e2.msgstr = value

        e2.msgctxt = audio

        if female != None:
          female_strings.append([e2.msgid, female])

      else:
        print "WARN: no msgid found for {}:{}, skipping string {}".format(path, index, value)
#  for f in female_strings:
#    print f
  return po


#check if TXT file is indexed
def check_indexed(txt_filename, encoding = defaults['encoding']):
  f = io.open(txt_filename, 'r', encoding = encoding)
  #count non-empty lines
  num_lines = sum(1 for line in f if line.rstrip())
  f.close()

  #count lines that are indexed
  pattern = file_format['txt']['pattern']
  f = io.open(txt_filename, 'r', encoding = encoding)
  text = f.read()
  indexed_lines = re.findall(pattern, text)
  num_indexed_lines = len(indexed_lines)
  f.close()
  if num_lines == num_indexed_lines:
    return True
  else:
    return False

#find valid file extensions
def find_valid_extenstions(dir):
  ext_list={}
  for dir_name, subdir_list, file_list in os.walk(dir,topdown=False):
    for file_name in file_list:
      ext=bgforge_po.get_ext(file_name)
      if not ext == None:
        ext_list[ext] = 1
  for ext, value in ext_list.items():
    #skip po and pot
    if ext == 'po':
      del ext_list['po']
      continue
    if ext == 'pot':
      del ext_list['pot']
      continue
    #check if tool is in PATH
    po_tool=ext + '2po'
    try:
      subprocess.call([po_tool, "-h"],stdout=devnull, stderr=devnull)
    except OSError as err:
      print "{} is not in PATH, skipping {} files".format(po_tool,ext)
      del ext_list[ext]
  return ext_list

#strip # #-#-#-#-# stuff from file
def strip_msgcat_comments(filename):
  for line in fileinput.input(filename, inplace = True):
    if not re.search('^#$',line) and not re.search('^# #-#-#-#-#.*',line):
      print line

def po_make_unique(po):
  entries_dict = collections.OrderedDict()
  for e in po:
    if (e.msgid, e.msgctxt) in entries_dict:

      e0 = entries_dict[(e.msgid, e.msgctxt)]
      e0.occurrences.extend(e.occurrences)

      if e.comment != None:
        if e0.comment == None:
          e0.comment = e.comment
        elif e0.comment != e.comment:
          e0.comment = e0.comment + '; ' + e.comment

      if e.tcomment != None:
        if e0.tcomment == None:
          e0.tcomment = e.tcomment
        elif e0.tcomment != e.tcomment:
          e0.tcomment = e0.tcomment + '; ' + e.tcomment

      for f in e.flags:
        if not f in e0.flags:
          e0.flags.append(f)

      if e.previous_msgctxt and not e0.previous_msgctxt:
        e0.previous_msgctxt = e.previous_msgctxt
      if e.previous_msgid and not e0.previous_msgid:
        e0.previous_msgid = e.previous_msgid
      if e.previous_msgid_plural and not e0.previous_msgid_plural:
        e0.previous_msgid_plural = e.previous_msgid_plural

    else:
      entries_dict[(e.msgid, e.msgctxt)] = e
  po2 = polib.POFile()
  po2.metadata = metadata
  for key, value in entries_dict.items():
    po2.append(value)
  return po2

class TRANSFile(list):
  '''
  Common translation class, holding translation entries as a list of dictionaries
  entry format:
    index
    value
    audio
    female
    comment
  All set to None if not present
  '''
  def __init__(self, *args, **kwargs):
    list.__init__(self)
    # the opened file handle
    filepath = kwargs.get('filepath', None)
    is_source = kwargs.get('is_source', False) #distinguish source TRAs to allow empty comment to be set on empty strings
    # the file encoding
    encoding = kwargs.get('encoding', defaults['encoding'])
    fext = get_ext(filepath)

    text = io.open(filepath, 'r', encoding = encoding).read()

    self.fformat = file_format[fext]
    pattern = self.fformat['pattern']
    dotall = self.fformat['dotall']
    try: # comment for all entries in file
      self.comment = self.fformat['comment']
    except:
      pass

    if dotall == True:
      lines = re.findall(pattern, text, re.DOTALL)
    else:
      lines = re.findall(pattern, text)

    # protection again duplicate indexes, part 1
    seen = []

    for line in lines:
      entry = {}

      # index and value
      index = line[self.fformat['index']]
      entry['value'] = unicode(line[self.fformat['value']])

      # skip invalid '000' entries in MSG files
      if fext == 'msg' and index == '000':
        print 'WARN: {} - invalid entry number found, skipping: {{000}}{{}}{{{}}}'.format(filepath,entry['value'])
        continue

      entry['index'] = line[self.fformat['index']]

      # comment
      # 1. generic comment for all entries in file
      try:
        entry['comment'] = self.fformat['comment']
      except:
        entry['comment'] = None
      # 2. handle empty lines in source files
      if entry['value'] == '':
        if is_source == True:
          entry['value'] = ' '
          entry['comment'] = empty_comment

      # audio
      try:
        entry['audio'] = line[self.fformat['audio']]
      except:
        entry['audio'] = None
      if entry['audio'] == '':
        entry['audio'] = None

      # female
      entry['female'] = None #default
      if fext == 'tra': # TRA file specific
        try:
          entry['female'] = unicode(line[self.fformat['female']])
        except:
          pass
        if entry['female'] == '':
          entry['female'] = None

      # protection against duplicate indexes, part 2
      if (entry['index']) in seen:
        print "WARN: duplicate string {}:{}, using new value '{}'".format(filepath, entry['index'], entry['value'])
        self[:] = [entry if x['index'] == entry['index'] else x for x in self]
        continue
      else:
        seen.append(index)

      # produce the final list of strings
      if entry['value'] != None and entry['value'] != '':
        self.append(entry)
