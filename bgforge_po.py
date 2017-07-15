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


file_features = {
  'msg': {
    'pattern': '{(\d+)}{([^}]*)}{([^}]*)}',
    'dotall':   True,
    'index':    0,
    'value':    2,
    'extra':    1,
  }
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
    if e0[ff['extra']] != None:
      extra = e0[ff['extra']]
    if extra == '':
      extra = None #used later for comparing e2.comment

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
    for e2 in current_entries:
      entry_added = 0
      if e2.msgid == value and e2.comment == extra:
        e2.occurrences.append((input_file, index))
        entry_added = 1
        break

    #not dupe, add new entry
    if entry_added == 0:
      if not extra == None: #only use context where it's necessary
        entry = polib.POEntry(
          msgid=value,
          msgstr='',
          occurrences=[(input_file, index),],
          comment = extra,
        )
      else:
        entry = polib.POEntry(
          msgid=value,
          msgstr='',
          occurrences=[(input_file, index),],
        )
      po.append(entry)

  po.save(output_file)
