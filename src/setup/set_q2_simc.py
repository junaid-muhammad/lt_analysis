#! /usr/bin/python

#
# Description:
# ================================================================
# Time-stamp: "2023-09-19 17:40:49 trottar"
# ================================================================
#
# Author:  Richard L. Trotta III <trotta@cua.edu>
#
# Copyright (c) trottar
#
import sys

Q2 = sys.argv[1]

###############################################################################################################################################
# ltsep package import and pathing definitions

# Import package for cuts
from ltsep import Root
# Import package for progress bar
from ltsep import Misc

lt=Root(os.path.realpath(__file__),"Plot_Prod")

# Add this to all files for more dynamic pathing
USER=lt.USER # Grab user info for file finding
HOST=lt.HOST
REPLAYPATH=lt.REPLAYPATH
UTILPATH=lt.UTILPATH
LTANAPATH=lt.LTANAPATH
ANATYPE=lt.ANATYPE
OUTPATH=lt.OUTPATH
CACHEPATH=lt.CACHEPATH

###############################################################################################################################################

# Read the file and store its contents
with open(file_path, 'r') as file:
    lines = file.readlines()

# Find and replace the specific variable definition
for i, line in enumerate(lines):
    if 'q2_set=' in line:
        lines[i] = 'q2_set={}\n'.format(Q2)

# Write the modified content back to the file
with open(file_path, 'w') as file:
    file.writelines(lines)
