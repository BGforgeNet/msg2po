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
    'context':    1,
  },
  'sve': {
    'pattern': '(\d+):(.*)',
    'dotall':   False,
    'index':    0,
    'value':    1,
  },
  'txt': {
    'pattern': '(\d+):(.*)',
    'dotall':   False,
    'index':    0,
    'value':    1,
    'comment':  'indexed_txt',
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
#      print "id is {}, value is {}, context is '{}', context is '{}'".format(e2.msgid, value, e2.msgctxt, context)
#      print 'context = {}'.format(context)
#      print e2.msgctxt
      if e2.msgid == value and e2.msgctxt == context:
#        print 'dupe!'
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
#      if context == None:
#        entry = polib.POEntry(
#          msgid=value,
#          msgstr='',
#          occurrences=[(input_file, index),],
#        )
#      else:
#        entry = polib.POEntry(
#          msgid=value,
#          msgstr='',
#          occurrences=[(input_file, index),],
#          msgctxt = context,
#        )
      po.append(entry)

  po.save(output_file)
