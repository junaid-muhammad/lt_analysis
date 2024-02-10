#! /usr/bin/python

#
# Description:
# ================================================================
# Time-stamp: "2024-02-10 16:22:07 trottar"
# ================================================================
#
# Author:  Richard L. Trotta III <trotta@cua.edu>
#
# Copyright (c) trottar
#
import pandas as pd
import numpy as np
import sys, os

################################################################################################################################################
'''
User Inputs
'''
runs_effective_charge = [float(q) for q in sys.argv[1].split(" ")]
runs_effective_charge_uncern = [float(err) for err in sys.argv[2].split(" ")]

print("\n\n\n",runs_effective_charge,"\n\n\n",runs_effective_charge_uncern)

################################################################################################################################################
'''
ltsep package import and pathing definitions
'''
# Import package for cuts
from ltsep import Root

lt=Root(os.path.realpath(__file__))

# Add this to all files for more dynamic pathing
UTILPATH=lt.UTILPATH
LTANAPATH=lt.LTANAPATH

################################################################################################################################################

# Sum of all the effective charge per run
tot_effective_charge = np.sum(runs_effective_charge)

# Normalized uncertainty (converted to %)
tot_effective_charge_uncern = np.sqrt(np.sum([err**2 for err in runs_effective_charge_uncern])/tot_effective_charge**2)*100
        
BashInput=("{}\n{}".format(tot_effective_charge, tot_effective_charge_uncern))
print(BashInput)
