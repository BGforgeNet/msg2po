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

# extensions recognized by file2po, etc
valid_extensions = [ 'msg', 'txt', 'sve', 'tra']


# supported file formats
# pattern is used to parse original files
# line_format to write to translated files
# index, value, context, female - order of these tokens in pattern
# dotall - whether file entries are multiline
file_format = {
  'msg': {
    'pattern':      '{(\d+)}{([^}]*)}{([^}]*)}',
    'dotall':       True,
    'index':        0,
    'value':        2,
    'context':      1,
    'line_format':  {
      'default':      '{{{index}}}{{}}{{{value}}}\n',
      'context':      '{{{index}}}{{{context}}}{{{value}}}\n',
      'female':       'separate',
    },
  },
  'sve': {
    'pattern':      '(\d+):(.*)',
    'dotall':       False,
    'index':        0,
    'value':        1,
    'line_format':  {
      'default':    '{index}:{value}\n',
      'female':     'separate',
    },
  },
  'txt': {
    'pattern':      '(\d+):(.*)',
    'dotall':       False,
    'index':        0,
    'value':        1,
    'comment':      'indexed_txt',
    'line_format':  {
      'default':      '{index}:{value}\n',
      'female':       'separate',
    },
  },
  'tra': {
    'pattern':      '@(\d+)\s*?=\s*?~([^~]*?)~(?:\s)?(?:\[([^]]*)\])?(?:~([^~]*)~)?',
    'dotall':       True,
    'index':        0,
    'value':        1,
    'context':      2,
    'female':       3,
    'line_format':  {
      'default':      '@{index} = ~{value}~\n',
      'context':      '@{index} = ~{value}~ [{context}]\n',
      'female':       '@{index} = ~{value}~ ~{female}~\n',
    },
  },
}

ini = 'bgforge.ini'
main_ini_section = 'main'
po_dirname = 'po'
po_dir_key = 'po_dir'
tra_dir_key = 'tra_dir'
src_lang_key = 'src_lang'
female_suffix = '_female.csv'
female_dir_suffix = '_female'

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

#used for determining empty strings, which are invalid by PO spec
empty_comment = 'LEAVE empty space in translation'

lowercase_exclude = ['.git', '.svn', '.hg', 'README.md']

#file and dir manipulation
#################################
def get_ext(path):
  try:
    ext = path.rsplit('.',1)[1].lower()
  except:
    ext = None
  return ext

def basename(path):
  if path.endswith(os.sep):
    path = path[:-1]
  return os.path.abspath(path).rsplit(os.sep,1)[1]

def parent_dir(path):
  if path.endswith(os.sep):
    path = path[:-1]
  return os.path.abspath(path).rsplit(os.sep,1)[0]

def strip_ext(filename):
  return filename.rsplit('.',1)[0]

def get_dir(path):
  return path.rsplit(os.sep,1)[0]

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
  for dir_name, subdir_list, file_list in os.walk(dir, topdown = False):
    subdir_list[:] = [d for d in subdir_list if d not in lowercase_exclude]
    for sd in subdir_list:
      for dname, sdir_list, file_list in os.walk(sd, topdown = False):
        lowercase_rename(dir_name,file_list)
        lowercase_rename(dir_name,sdir_list)
  children = os.listdir(dir)
  children[:] = [c for c in children if c not in lowercase_exclude]
  for c in children:
    new_c = c.lower()
    if c != new_c:
      print "renaming {} to {}".format(c, new_c)
      os.rename(c, new_c)

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
  po_dir = os.path.join(tra_dir, po_dirname)
  return po_dir

def get_poify_dir():
  tra_dir = get_value(tra_dir_key)
  src_lang = get_value(src_lang_key)
  poify_dir = os.path.join(tra_dir, src_lang)
  return poify_dir

def dir_or_exit(d):
  if os.path.isdir(d):
    print 'Found directory {}'.format(d)
  else:
    print 'Directory {} does not exist, cannot continue!'.format(d)
    sys.exit(1)

#returns list of extensions for which a separate female package should be prepared
def separate_file_formats():
  extensions = []
  for ff in file_format:
    if ("female" in file_format[ff]["line_format"]
      and file_format[ff]["line_format"]["female"] == "separate"):
      extensions.append(ff)
  return extensions

# check if need to make female package
def need_female_package(file_list):
  need_female = False
  ext_list = separate_file_formats()
  for f in file_list:
    ext=get_ext(f)
    if ext in ext_list:
      need_female = True
      break
  return need_female

@contextmanager
def cd(newdir):
  prevdir = os.getcwd()
  os.chdir(os.path.expanduser(newdir))
  try:
    yield
  finally:
    os.chdir(prevdir)

def get_enc(po_name,
            po_occurrence_name = '',
            encoding_dict = encodings,
            dos_encoding_dict = dos_encodings,
            dos_filename_list = dos_filenames,
            utf_filename_list = utf_filenames):
  encoding = defaults['encoding']
  lang = strip_ext(basename(po_name))
  filename = basename(po_occurrence_name)

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

  trans = TRANSFile(filepath=filepath, is_source=True, encoding = encoding) #load translations

  po = polib.POFile()
  po.metadata = metadata

  entry_added = 0
  for t in trans:
    index = t['index']
    value = t['value']
    context = t['context']
    comment = t['comment']

    # try to find a matching entry first
    dupe = 0
    for e in po:
      if e.msgid == value and e.msgctxt == context:
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
        msgctxt = context,
        comment = comment,
    )
    po.append(entry)

  return(po)


#check if extract file is present in po, exit with error if not
def check_path_in_po(po, path):
  present_files = set()
  for entry in po:
    for eo in entry.occurrences:
      present_files.add(eo[0])
  present_files_list = sorted(set(present_files))
  if not path in present_files_list:
    print "{} is not present in selected PO file".format(path)
    print "supply one of present files with --path argument:"
    for pf in present_files_list:
      print pf
    sys.exit(1)

# return dict of dicts mapping filepaths to entries/occurrences where they are present
# {} file_path: {unit_index: entry_index, unit2_index: entry2_index, ...},  }
# entry_index is index in PO file (list)
def get_po_occurrence_map(po):
  ocmap = {}
  i = 0
  for entry in po:
    for eo in entry.occurrences:
      if eo[0] in ocmap:
        ocmap[eo[0]][int(eo[1])]= i
      else:
        ocmap[eo[0]] = {int(eo[1]): i}
    i = i + 1
  return ocmap

#extract and write to disk a single file from EPO object
#epo is EPO object
#output_file is path relative to dst_dir
#dst_dir is actually dst language. Used only in unpoify
def po2file(epo, output_file, encoding, occurrence_path, dst_dir = None, newline='\r\n', occurrence_map=None):
  if occurrence_map is None: #when extracting single file with po2tra/po2msg, etc
    #check if file is present in po, exit if not
    check_path_in_po(epo.po, occurrence_path)
    occurrence_map = get_po_occurrence_map(epo.po)

  #create parent directory
  create_dir(get_dir(output_file))

  ext = get_ext(output_file)
  ff = file_format[ext]
  line_format = ff['line_format']

  po = epo.po

  context = ''
  resulting_entries = []
  for i in occurrence_map[occurrence_path]:
    entry = po[occurrence_map[occurrence_path][i]]
    index = i
    if entry.msgstr == '': #if not translated, keep msgid
      value = entry.msgid
    else:
      value = entry.msgstr

    #empty lines detected by comment
    if entry.comment == empty_comment:
      value = ''

    #context
    context = entry.msgctxt
    #female strings
    if entry.msgid in epo.female_strings:
      female = epo.female_strings[entry.msgid]
    else:
      female = None

    resulting_entries.append({'index': index, 'value': value, 'female': female, 'context': context})

  # combined occurrences may mess up order, restoring
  resulting_entries = sorted(resulting_entries, key=lambda k: k['index'])

  lines = []
  lines_female = []

  for re in resulting_entries:
    #get line format
    lfrm = get_line_format(re, ext)

    #add line to common/male package
    lines.append(lfrm.format(index=re['index'], value=re['value'], context=re['context'], female=re['female']))

    # add string to female package if needed
    if 'female' in line_format and line_format['female'] == 'separate':
      if re['female'] is not None:
        lines_female.append(lfrm.format(index=re['index'], value=re['female'], context=re['context']))
      else:
        lines_female.append(lfrm.format(index=re['index'], value=re['value'], context=re['context']))

  #write main package
  file = io.open(output_file, 'w', encoding=encoding, newline=newline)
  for line in lines:
    file.write(line.encode(encoding,'replace').decode(encoding).decode('utf-8'))
  file.close()

  #separate female translation bundle if needed
  female_done = False
  if ('female' in line_format and line_format['female'] == 'separate' 
    and dst_dir is not None and lines_female != lines):
    female_file = output_file.replace(dst_dir + os.sep, dst_dir + female_dir_suffix + os.sep)
    create_dir(get_dir(female_file)) #create dir if not exists
    print 'Also extracting female counterpart into {}'.format(female_file)
    file2 = io.open(female_file, 'w', encoding=encoding, newline=newline)
    for line in lines_female:
      file2.write(line.encode(encoding,'replace').decode(encoding).decode('utf-8'))
    file2.close()
    female_done = True

  return female_done

#takes translation entry in format {'index': index, 'value': value, 'female': female, 'context': context}
#and file extension
#returns corresponding string with placeholders from line_format
def get_line_format(e, ext):
  ff = file_format[ext]
  line_format = ff['line_format']
  if e['context'] is not None: #entry with context
    lfrm = line_format['context']
  elif 'female' in e and e['female'] is not None and 'female' in line_format and line_format['female'] != 'separate': #format with native support for female strings
    lfrm = line_format['female']
  else: #no context and no female, or format without native support for female strings
    lfrm = line_format['default']
  return lfrm


def copycreate(src_file, dst_file):
  dirname = os.path.dirname(dst_file)
  if not os.path.exists(dirname):
    os.makedirs(dirname)
  shutil.copyfile(src_file, dst_file)


#returns PO file object
def file2msgstr(input_file, epo, path, encoding = defaults['encoding']):
  trans = TRANSFile(filepath=input_file, encoding=encoding) #load translations

  # map entries to occurrences for faster access, part 1
  entries_dict = collections.OrderedDict()
  po = epo.po
  for e in po:
    for eo in e.occurrences:
      entries_dict[(eo[0], eo[1])] = e

  for t in trans:
    index = t['index']
    value = t['value']
    context = t['context']
    female = t['female']

    if value is not None and value != '':
      if (path, index) in entries_dict:
        # map entries to occurrences for faster access, part 2
        e2 = entries_dict[(path, index)]
        if e2.msgstr is not None and e2.msgstr != '' and e2.msgstr != value:
          print "WARN: different translations found for {}. Replacing first string with second:\n      {}\n      {}".format(e2.occurrences, e2.msgstr, value)

        if e2.msgid == value:
          print "WARN: string and translation are the same for {}. Using it regardless:\n      {}".format(e2.occurrences, e2.msgid)
        e2.msgstr = value

        e2.msgctxt = context

        if female is not None:
          epo.female_strings[e2.msgid] = female

      else:
        print "WARN: no msgid found for {}:{}, skipping string\n      {}".format(path, index, value)
  return epo


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
      if ext is not None:
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

      if e.comment is not None:
        if e0.comment is None:
          e0.comment = e.comment
        elif e0.comment != e.comment:
          e0.comment = e0.comment + '; ' + e.comment

      if e.tcomment is not None:
        if e0.tcomment is None:
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
    context
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
        print 'WARN: {} - invalid entry number found, skipping:\n     {{000}}{{}}{{{}}}'.format(filepath,entry['value'])
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

      # context
      try:
        entry['context'] = line[self.fformat['context']]
      except:
        entry['context'] = None
      if entry['context'] == '':
        entry['context'] = None

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
        print "WARN: duplicate string definition found {}:{}, using new value:\n      {}".format(filepath, entry['index'], entry['value'])
        self[:] = [entry if x['index'] == entry['index'] else x for x in self]
        continue
      else:
        seen.append(index)

      # produce the final list of strings
      if entry['value'] is not None and entry['value'] != '':
        self.append(entry)

class EPOFile(polib.POFile):
  '''
  Extended PO file class, also reading from and writing to _female.csv
  '''
  def __init__(self, *args):
    po = args[0]
    self.csv = po + female_suffix
    self.female_strings = {}
    if po:
      self.po = polib.pofile(po)
      if os.path.isfile(self.csv):
        self.load_csv()
    else:
      self.po = polib.POFile()

  def save(self, output_file):
    self.po.save(output_file)
    self.save_csv()

  def save_csv(self):
    with io.open(self.csv, 'wb') as csvfile:
      writer = csv.writer(csvfile)
      writer.writerows(self.female_strings.items())

  def load_csv(self):
    with io.open(self.csv, 'r', encoding = 'utf-8') as csvfile:
      reader = csv.reader(csvfile)
      for row in reader:
        self.female_strings[row[0]] = row[1]

def epofile(f):
  '''
  Returns EPOFile object
  '''
  epo = EPOFile(f)
  return epo


def clean_female_csv(po_path):
  '''
  Removes strings not present in PO file from corresponding female csv
  '''
  csv_path = po_path + female_suffix

  if os.path.isfile(csv_path):

    print "Found female CSV {}, cleaning stale strings".format(csv_path)
    po = polib.pofile(po_path)
    msgid_dict = {}
    for e in po:
      msgid_dict[e.msgid] = e.msgstr

    female_strings = collections.OrderedDict()
    with io.open(csv_path, 'r', encoding = 'utf-8') as csvfile:
      reader = csv.reader(csvfile)
      for row in reader:
        if row[0] in female_strings and row[1] != female_strings[row[0]]:
          print "Dupe", row[0], '+', row[1], '+', female_strings[row[0]]
        else:
          female_strings[row[0]] = row[1]

    new_female_strings = collections.OrderedDict()
    for f in female_strings:
      if f in msgid_dict and female_strings[f] != msgid_dict[f]:
        new_female_strings[f] = female_strings[f]

    with io.open(csv_path, 'wb') as csvfile:
      writer = csv.writer(csvfile)
      writer.writerows(new_female_strings.items())
