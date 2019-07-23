#!/usr/bin/env python3
# coding: utf-8

# this script is needed for shell wrappers

import bgforge_po
import sys

key = sys.argv[1]
value = bgforge_po.get_config(key)
print(value)
