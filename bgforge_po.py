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


file_features = {
  'msg': {
    'pattern':     '{(\d+)}{([^}]*)}{([^}]*)}',
    'dotall':       True,
    'index':        0,
    'value':        2,
    'context':      1,
    'line_format': '{{{}}}{{{}}}{{{}}}\n',
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
}

default_encoding='cp1252'
default_width=999999

#file and dir manipulation
#################################
def get_ext(path):
  try:
    ext = path.rsplit('.',1)[1]
  except:
    ext = None
  return ext

def basename(path):
  if path.endswith('/'):
    s = s[:-1]
  return os.path.abspath(path).rsplit('/',1)[1]

def parent_dir(path):
  if path.endswith('/'):
    s = s[:-1]
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
################################



def file2po(input_file,output_file,encoding=default_encoding,width=default_width,noempty=False):
  text = io.open(input_file, 'r', encoding=encoding).read()

  ext = get_ext(input_file)
  ff = file_features[ext.lower()]
  pattern = ff['pattern']
  dotall = ff['dotall']

  if dotall == True:
    found_entries = re.findall(pattern, text, re.DOTALL)
  else:
    found_entries = re.findall(pattern, text)

  po = polib.POFile(wrapwidth=width)
  po.metadata = {
    'Project-Id-Version': 'PACKAGE VERSION',
    'Report-Msgid-Bugs-To': '',
    'POT-Creation-Date': '1970-1-01 00:00+0000',
    'PO-Revision-Date': 'YEAR-MO-DA HO:MI+ZONE',
    'Last-Translator': 'FULL NAME <EMAIL@ADDRESS',
    'Language-Team': 'LANGUAGE <LL@li.org>',
    'Language': '',
    'MIME-Version': '1.0',
    'Content-Type': 'text/plain; charset=UTF-8',
    'Content-Transfer-Encoding': '8bit',
    'X-Generator': 'bgforge_po v.{}'.format(version),
  }

  entry_added = 0
  for e0 in found_entries:
    index = e0[ff['index']]
    value = unicode(e0[ff['value']])

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
        print 'WARN: {} - empty value found, skipping: {{{}}}{{}}{{}}'.format(input_file,index)
        continue
      else:
        value = ' '

    if index == '000': #skip invalid '000' entries
      print 'WARN: {} - invalid entry number found, skipping: {{000}}{{}}{{{}}}'.format(input_file,value)
      continue

    #check for dupe, if found add to occurences
    current_entries = [e1 for e1 in po]
    entry_added = 0
    for e2 in current_entries:
      if e2.msgid == value and e2.msgctxt == context:
        e2.occurrences.append((input_file, index))
        entry_added = 1
        break

    #not dupe, add new entry
    if entry_added == 0:
      entry = polib.POEntry(
        msgid=value,
        msgstr='',
        occurrences=[(input_file, index),],
        msgctxt = context,
        comment = comment,
      )
      po.append(entry)

  po.save(output_file)


#check if extract fie is present in po, exit with error if not
def check_path_in_po(po,path):
  present_files = []
  for entry in po:
    for eo in entry.occurrences:
      present_files.append(eo[0])
  present_files_list = sorted(set(present_files))
  if not path in present_files_list:
    print "{} is not present in {}".format(path,po_file)
    print "supply one of present files with --extract-file argument:"
    for pf in present_files_list:
      print pf
    sys.exit(1)

def po2file(po,output_file,encoding,path): #po is po_file object
  ext = get_ext(output_file)
  ff = file_features[ext.lower()]
  line_format = ff['line_format']

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

        if 'context' in ff: #only add context when defined in file format
          if entry.msgctxt != None:
            context = entry.msgctxt
          else:
            context = ''
          resulting_entries.append([index,value,context])
        else:
          resulting_entries.append([index,value])

  resulting_entries.sort() #because duplicate entries may mess up order
  index_order = ff['index']
  value_order = ff['value']

  lines = []
  if 'context' in ff: #context again
    context_order = ff['context']
    for re in resulting_entries:
      lines.append(line_format.format(re[index_order],re[value_order],re[context_order]))
  else:
    for re in resulting_entries:
      lines.append(line_format.format(re[index_order],re[value_order]))
  file = io.open(output_file, 'w', encoding=encoding)
  for line in lines:
    file.write("%s" % unicode(line))
  file.close()


def file2msgstr(input_file,output_file,path,encoding=default_encoding,width=default_width):

  #get file features
  ext = get_ext(input_file)
  ff = file_features[ext.lower()]
  pattern = ff['pattern']
  dotall = ff['dotall']

  #find entries
  text = io.open(input_file, 'r', encoding=encoding).read()
  if dotall == True:
    found_entries = re.findall(pattern, text, re.DOTALL)
  else:
    found_entries = re.findall(pattern, text)

  #find and add entries to po file
  po = polib.pofile(output_file,wrapwidth=width)
  po_entries = [e for e in po]
  index_order = ff['index']
  value_order = ff['value']
  for e in found_entries:
    index = e[index_order]
    value = unicode(e[value_order])
    for pe in po_entries:
      for eo in pe.occurrences:
        if eo[0] == path and eo[1] == index:
          pe.msgstr = value

  po.save(output_file)


#check if TXT file is indexed
def check_indexed(txt_filename,encoding=default_encoding):
  f = io.open(txt_filename, 'r', encoding=encoding)
  #count non-empty lines
  num_lines = sum(1 for line in f if line.rstrip())
  f.close()

  #count lines that are indexed
  pattern = file_features['txt']['pattern']
  f = io.open(txt_filename, 'r', encoding=encoding)
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
