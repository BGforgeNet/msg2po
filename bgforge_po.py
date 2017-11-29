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

valid_extensions = [ 'msg', 'txt', 'sve', 'tra']

file_features = {
  'msg': {
    'pattern':     '{(\d+)}{([^}]*)}{([^}]*)}',
    'dotall':       True,
    'index':        0,
    'value':        2,
    'context':      1,
    'line_format': '{{{}}}{{{}}}{{{}}}\n',
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
    'pattern':     '@(\d+)\s*?=\s*?~([^~]*?)~(\s)?(\[([^]]*)\])?',
    'dotall':       True,
    'index':        0,
    'value':        1,
    'context':      4,
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

defaults = {
  'encoding': 'cp1252',
  'width': 78,
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
def file2po(filename, encoding = defaults['encoding'], width = defaults['width'], noempty = False):
  text = io.open(filename, 'r', encoding = encoding).read()

  ext = get_ext(filename)
  ff = file_features[ext]
  pattern = ff['pattern']
  dotall = ff['dotall']

  if dotall == True:
    found_entries = re.findall(pattern, text, re.DOTALL)
  else:
    found_entries = re.findall(pattern, text)

  po = polib.POFile(wrapwidth=width)
  po.metadata = metadata

  entry_added = 0
  seen = []
  dupe = 0
  for e0 in found_entries:
    dupe = 0
    index = e0[ff['index']]
    value = unicode(e0[ff['value']])

    if index == '000' and ext == 'msg' : #skip invalid '000' entries in MSG files
      print 'WARN: {} - invalid entry number found, skipping: {{000}}{{}}{{{}}}'.format(filename,value)
      continue

    index = index.lstrip("0") #handle "0.." entries in tra
    if index == '':
      print index
      index = '0'

    if (filename, index) in seen:
      print "WARN: duplicate string {}:{}, using new value '{}'".format(filename, index, value)
      dupe = 1
    seen.append((filename, index))

    if 'context' in ff:
      context = e0[ff['context']]
    else:
      context = None
    if context == '': #don't need empty context
      context = None

    if 'comment' in ff:
      comment = ff['comment']
    else:
      comment = None

    if value == '': #handle empty lines
      if noempty:
        print 'WARN: {} - empty value found, skipping: {{{}}}{{}}{{}}'.format(filename,index)
        continue
      else:
        value = ' '
        comment = empty_comment

    #remove dupe from occurrences
    if dupe == 1:
      for e2 in po:
        if (filename, index) in e2.occurrences:
          if len(e2.occurrences) == 1:
            po[:] = [e3 for e3 in po if not e3 == e2]
          else:
            e2.occurrences.remove((filename, index))
          dupe = 0
    entry_added = 0
    for e2 in po:
      if e2.msgid == value and e2.msgctxt == context:
        e2.occurrences.append((filename, index))
        entry_added = 1
        break

    #no matching msgid, add new entry
    if entry_added == 0:
        entry = polib.POEntry(
            msgid=value,
            msgstr='',
            occurrences=[(filename, index),],
            msgctxt = context,
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

def po2file(po, output_file, encoding, path): #po is po_file object
  ext = get_ext(output_file)
  ff = file_features[ext]
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
      if eo[0] == path:

        index = int(eo[1]) #need int because later will sort

        if entry.msgstr == '': #if not translated, keep msgid
          value = entry.msgid
        else:
          value = entry.msgstr

        #empty lines detected by comment
        if entry.msgid == ' ' and entry.comment == empty_comment:
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
      lines.append(line_format_context.format(re[0],re[1],re[2]))
    except: #no context
      lines.append(line_format.format(re[0],re[1]))

  file = io.open(output_file, 'w', encoding=encoding)
  for line in lines:
    file.write(line.encode(encoding,'replace').decode(encoding).decode('utf-8'))
  file.close()


def file2msgstr(input_file, po, path, encoding = defaults['encoding'], width = defaults['width']):

  #get file features
  ext = get_ext(input_file)
  ff = file_features[ext]
  pattern = ff['pattern']
  dotall = ff['dotall']

  #find entries
  text = io.open(input_file, 'r', encoding=encoding).read()
  if dotall == True:
    found_entries = re.findall(pattern, text, re.DOTALL)
  else:
    found_entries = re.findall(pattern, text)

  #find and add entries to po file
  po_entries = [e for e in po]
  index_order = ff['index']
  value_order = ff['value']
  entries_dict = collections.OrderedDict()
  for e in po:
    for eo in e.occurrences:
      entries_dict[(eo[0], eo[1])] = e
  for fe in found_entries:
    index = fe[index_order]
    value = unicode(fe[value_order])
    if value != None and value != '':
      if (path, index) in entries_dict:
        e2 = entries_dict[(path, index)]
        if e2.msgstr != None and e2.msgstr != '' and e2.msgstr != value:
          print "WARN: differing msgstr values found for {}\nOverwriting first string with second:\n\"{}\"\n\"{}\"".format(e2.occurrences, e2.msgstr, value)
        e2.msgstr = value
      else:
        print "WARN: no msgid found for {}:{}, skipping string {}".format(path, index, value)
  return po


#check if TXT file is indexed
def check_indexed(txt_filename, encoding = defaults['encoding']):
  f = io.open(txt_filename, 'r', encoding = encoding)
  #count non-empty lines
  num_lines = sum(1 for line in f if line.rstrip())
  f.close()

  #count lines that are indexed
  pattern = file_features['txt']['pattern']
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

def po_make_unique(po, wrapwidth = defaults['width']):
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
  po2 = polib.POFile(wrapwidth=wrapwidth)
  po2.metadata = metadata
  for key, value in entries_dict.items():
    po2.append(value)
  return po2
