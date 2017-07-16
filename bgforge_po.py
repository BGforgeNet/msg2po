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


#get file extenstion
def get_ext(name):
  try:
    ext = name.rsplit('.',1)[1]
  except:
    ext = None
  return ext


def file2po(input_file,output_file,encoding='cp1252',width=999999,noempty=False):
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
def check_path_in_po(po_file,path):
  po = polib.pofile(po_file)
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

def po2file(input_file,output_file,encoding,extract_file):
  ext = get_ext(output_file)
  ff = file_features[ext.lower()]
  line_format = ff['line_format']

  check_path_in_po(input_file,extract_file) #exit if not found

  po = polib.pofile(input_file)
  context = ''
  resulting_entries = []
  for entry in po:
    for eo in entry.occurrences:
      if eo[0] == extract_file:

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
