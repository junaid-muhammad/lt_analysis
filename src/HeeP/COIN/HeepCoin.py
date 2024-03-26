#! /usr/bin/python

#
# Description:
# ================================================================
# Time-stamp: "2024-03-26 12:16:53 trottar"
# ================================================================
#
# Author:  Richard L. Trotta III <trotta@cua.edu>
#
# Copyright (c) trottar
#

###################################################################################################################################################

# Import relevant packages
import uproot as up
import numpy as np
import root_numpy as rnp
import pandas as pd
import root_pandas as rpd
import ROOT
import scipy
import scipy.integrate as integrate
import matplotlib.pyplot as plt
import sys, math, os, subprocess
import array
from ROOT import TCanvas, TH1D, TH2D, gStyle, gPad, TPaveText, TArc, TGraphErrors, TGraphPolar, TFile, TLegend, TMultiGraph, TLine
from ROOT import kBlack, kCyan, kRed, kGreen, kMagenta
from functools import reduce

##################################################################################################################################################

# Check the number of arguments provided to the script
if len(sys.argv)-1!=16:
    print("!!!!! ERROR !!!!!\n Expected 16 arguments\n Usage is with - KIN OutDATAFilename.root data_charge data_charge_err data_efficiency data_error_efficiency OutDUMMYFilename.root dummy_charge dummy_charge_err dummy_efficiency data_error_efficiency InSIMCFilename OutFullAnalysisFilename efficiency_table_filename \n!!!!! ERROR !!!!!")
    sys.exit(1)

##################################################################################################################################################

DEBUG = False # Flag for no cut plots


# Input params
heep_kinematics = sys.argv[1]
InDATAFilename = sys.argv[2]
data_charge = float(sys.argv[3])
data_charge_err = float(sys.argv[4])
InData_efficiency = sys.argv[5]
InData_error_efficiency = sys.argv[6]
data_runNums = sys.argv[7]
InDUMMYFilename = sys.argv[8]
dummy_charge = float(sys.argv[9])
dummy_charge_err = float(sys.argv[10])
InDummy_efficiency = sys.argv[11]
InDummy_error_efficiency = sys.argv[12]
dummy_runNums = sys.argv[13]
InSIMCFilename = sys.argv[14]
OutFilename = sys.argv[15]
efficiency_table = sys.argv[16]

###############################################################################################################################################
# Define total efficiency vs run number plots

InData_efficiency = np.array([float(x) for x in InData_efficiency.split(' ')])
InData_error_efficiency = np.array([float(x) for x in InData_error_efficiency.split(' ')])
data_runNums = np.array([int(x) for x in data_runNums.split(' ')])
G_data_eff = TGraphErrors(len(InData_efficiency), \
                          np.array([float(x) for x in data_runNums]), \
                          InData_efficiency, \
                          np.array([0]*len(InData_error_efficiency)), \
                          InData_error_efficiency*InData_efficiency)
G_data_eff.SetName("G_data_eff")    

InDummy_efficiency = np.array([float(x) for x in InDummy_efficiency.split(' ')])
InDummy_error_efficiency = np.array([float(x) for x in InDummy_error_efficiency.split(' ')])
dummy_runNums = np.array([int(x) for x in dummy_runNums.split(' ')])
G_dummy_eff = TGraphErrors(len(InDummy_efficiency), \
                          np.array([float(x) for x in dummy_runNums]), \
                          InDummy_efficiency, \
                          np.array([0]*len(InDummy_error_efficiency)), \
                          InDummy_error_efficiency*InDummy_efficiency)
G_dummy_eff.SetName("G_dummy_eff")    

###############################################################################################################################################
ROOT.gROOT.SetBatch(ROOT.kTRUE) # Set ROOT to batch mode explicitly, does not splash anything to screen
###############################################################################################################################################

'''
ltsep package import and pathing definitions
'''

# Import package for cuts
from ltsep import Root

lt=Root(os.path.realpath(__file__),"Plot_SimcCoin")

# Add this to all files for more dynamic pathing
USER=lt.USER # Grab user info for file finding
HOST=lt.HOST
REPLAYPATH=lt.REPLAYPATH
UTILPATH=lt.UTILPATH
LTANAPATH=lt.LTANAPATH
ANATYPE=lt.ANATYPE
OUTPATH=lt.OUTPATH

rootFile = OUTPATH+"/"+InDATAFilename
rootFile_DUMMY = OUTPATH+"/"+InDUMMYFilename
rootFile_SIMC = OUTPATH+"/"+InSIMCFilename

foutname = OUTPATH+"/" + OutFilename + ".root"
fouttxt  = OUTPATH+"/" + OutFilename + ".txt"
outputpdf  = OUTPATH+"/" + OutFilename + ".pdf"

###############################################################################################################################################

# Grabs simc number of events and normalizaton factor
simc_hist = "%s/OUTPUT/Analysis/HeeP/%s" % (LTANAPATH,InSIMCFilename.replace('.root','.hist'))

f_simc = open(simc_hist)
for line in f_simc:
    print(line)
    if "Ncontribute" in line:
        val = line.split("=")
        simc_nevents = int(val[1])
    if "normfac" in line:
        val = line.split("=")
        simc_normfactor = float(val[1])
if 'simc_nevents' and 'simc_normfactor' in locals():
    print('\n\nsimc_nevents = ',simc_nevents,'\nsimc_normfactor = ',simc_normfactor,'\n\n')
    print('\n\ndata_charge = {:.4f} +/- {:.4f}'.format(data_charge, data_charge_err),'\ndummy_charge = {:.4f} +/- {:.4f}'.format(dummy_charge, dummy_charge_err),'\n\n')
else:
    print("ERROR: Invalid simc hist file %s" % simc_hist)
    sys.exit(1)
f_simc.close()

###############################################################################################################################################

'''
# Grab windows for random subtraction

if "10p6" in heep_kinematics:
    runNum = 4827 # First run number of 10p6 coin heep setting
if "8p2" in heep_kinematics:
    runNum = 7974 # First run number of 8p2 coin heep setting
if "6p2" in heep_kinematics:
    runNum = 7866 # First run number of 6p2 coin heep setting
if "4p9" in heep_kinematics:
    runNum = 6881 # First run number of 4p9 coin heep setting
if "3p8" in heep_kinematics:
    runNum = 6634 # First run number of 3p8 coin heep setting        

try:
    runNum
except:
    print("ERROR: No valid run number for this setting!")
    sys.exit(1)

# Section for grabing Prompt/Random selection parameters from PARAM file
PARAMPATH = "%s/DB/PARAM" % UTILPATH
print("Running as %s on %s, hallc_replay_lt path assumed as %s" % (USER[1], HOST[1], LTANAPATH))
TimingCutFile = "%s/Timing_Parameters.csv" % PARAMPATH # This should match the param file actually being used!
TimingCutf = open(TimingCutFile)
try:
    TimingCutFile
except NameError:
    print("!!!!! ERRROR !!!!!\n One (or more) of the cut files not found!\n!!!!! ERRORR !!!!!")
    sys.exit(2)
print("Reading timing cuts from %s" % TimingCutFile)
PromptWindow = [0, 0]
RandomWindows = [0, 0, 0, 0]
linenum = 0 # Count line number we're on
TempPar = -1 # To check later
for line in TimingCutf: # Read all lines in the cut file
    linenum += 1 # Add one to line number at start of loop
    if(linenum > 1): # Skip first line
        line = line.partition('#')[0] # Treat anything after a # as a comment and ignore it
        line = line.rstrip()
        array = line.split(",") # Convert line into an array, anything after a comma is a new entry 
        if(int(runNum) in range (int(array[0]), int(array[1])+1)): # Check if run number for file is within any of the ranges specified in the cut file
            TempPar += 2 # If run number is in range, set to non -1 value
            BunchSpacing = float(array[2])
            CoinOffset = float(array[3]) # Coin offset value
            nSkip = float(array[4]) # Number of random windows skipped 
            nWindows = float(array[5]) # Total number of random windows
            PromptPeak = float(array[6]) # Pion CT prompt peak positon 
TimingCutf.close() # After scanning all lines in file, close file

if(TempPar == -1): # If value is still -1, run number provided din't match any ranges specified so exit 
    print("!!!!! ERROR !!!!!\n Run number specified does not fall within a set of runs for which cuts are defined in %s\n!!!!! ERROR !!!!!" % TimingCutFile)
    sys.exit(3)
elif(TempPar > 1):
    print("!!! WARNING!!! Run number was found within the range of two (or more) line entries of %s !!! WARNING !!!" % TimingCutFile)
    print("The last matching entry will be treated as the input, you should ensure this is what you want")

# From our values from the file, reconstruct our windows 
PromptWindow[0] = PromptPeak - (BunchSpacing/2) - CoinOffset
PromptWindow[1] = PromptPeak + (BunchSpacing/2) + CoinOffset
RandomWindows[0] = PromptPeak - (BunchSpacing/2) - CoinOffset - (nSkip*BunchSpacing) - ((nWindows/2)*BunchSpacing)
RandomWindows[1] = PromptPeak - (BunchSpacing/2) - CoinOffset - (nSkip*BunchSpacing)
RandomWindows[2] = PromptPeak + (BunchSpacing/2) + CoinOffset + (nSkip*BunchSpacing)
RandomWindows[3] = PromptPeak + (BunchSpacing/2) + CoinOffset + (nSkip*BunchSpacing) + ((nWindows/2)*BunchSpacing)

'''

################################################################################################################################################
# Grabs PID cut string
'''
log_hist = "%s/log/Analysed_COIN_%s.log" % (LTANAPATH,data_runNums.split(' ')[0])
f_log = open(log_hist)
for line in f_log:
    if "coin_ep_cut_prompt_noRF_pid" in line:
        log_entry = next(f_log)
if 'log_entry' in locals():
    print('\n\nPID Cuts = ',log_entry,'\n\n')
else:
    print("ERROR: Invalid log file %s" % log_hist)
    sys.exit(0)
f_log.close()
'''
################################################################################################################################################
# Define root file trees of interest

InFile_DATA = ROOT.TFile.Open(rootFile, "OPEN")
InFile_DUMMY = ROOT.TFile.Open(rootFile_DUMMY, "OPEN")
InFile_SIMC = ROOT.TFile.Open(rootFile_SIMC, "READ")

TBRANCH_DATA  = InFile_DATA.Get("Cut_Proton_Events_All")
TBRANCH_DATA_nocut  = InFile_DATA.Get("Uncut_Proton_Events")
TBRANCH_DATA_nopid  = InFile_DATA.Get("Cut_Proton_Events_nopid")
nEntries_TBRANCH_DATA  = TBRANCH_DATA.GetEntries()
TBRANCH_DUMMY  = InFile_DUMMY.Get("Cut_Proton_Events_All")
TBRANCH_DUMMY_nocut  = InFile_DUMMY.Get("Uncut_Proton_Events")
TBRANCH_DUMMY_nopid  = InFile_DUMMY.Get("Cut_Proton_Events_nopid")
nEntries_TBRANCH_DUMMY  = TBRANCH_DUMMY.GetEntries()
TBRANCH_SIMC  = InFile_SIMC.Get("h10")
nEntries_TBRANCH_SIMC  = TBRANCH_SIMC.GetEntries()

################################################################################################################################################
# Plot definitions

H_hsdelta_DATA  = ROOT.TH1D("H_hsdelta_DATA","HMS Delta", 200, -20.0, 20.0)
H_hsdelta_DATA_nocut  = ROOT.TH1D("H_hsdelta_DATA_nocut","HMS Delta", 200, -20.0, 20.0)
H_hsdelta_DATA_nopid  = ROOT.TH1D("H_hsdelta_DATA_nopid","HMS Delta", 200, -20.0, 20.0)
#H_hsdelta_DATA_rand  = ROOT.TH1D("H_hsdelta_DATA_rand","HMS Delta", 200, -20.0, 20.0)
H_hsdelta_DUMMY  = ROOT.TH1D("H_hsdelta_DUMMY","HMS Delta", 200, -20.0, 20.0)
H_hsdelta_DUMMY_nocut  = ROOT.TH1D("H_hsdelta_DUMMY_nocut","HMS Delta", 200, -20.0, 20.0)
H_hsdelta_DUMMY_nopid  = ROOT.TH1D("H_hsdelta_DUMMY_nopid","HMS Delta", 200, -20.0, 20.0)
#H_hsdelta_DUMMY_rand  = ROOT.TH1D("H_hsdelta_DUMMY_rand","HMS Delta", 200, -20.0, 20.0)
H_hsdelta_SIMC  = ROOT.TH1D("H_hsdelta_SIMC","HMS Delta", 200, -20.0, 20.0)

H_hsxptar_DATA  = ROOT.TH1D("H_hsxptar_DATA","HMS xptar", 200, -0.1, 0.1)
H_hsxptar_DATA_nocut  = ROOT.TH1D("H_hsxptar_DATA_nocut","HMS xptar", 200, -0.1, 0.1)
H_hsxptar_DATA_nopid  = ROOT.TH1D("H_hsxptar_DATA_nopid","HMS xptar", 200, -0.1, 0.1)
#H_hsxptar_DATA_rand  = ROOT.TH1D("H_hsxptar_DATA_rand","HMS xptar", 200, -0.1, 0.1)
H_hsxptar_DUMMY  = ROOT.TH1D("H_hsxptar_DUMMY","HMS xptar", 200, -0.1, 0.1)
H_hsxptar_DUMMY_nocut  = ROOT.TH1D("H_hsxptar_DUMMY_nocut","HMS xptar", 200, -0.1, 0.1)
H_hsxptar_DUMMY_nopid  = ROOT.TH1D("H_hsxptar_DUMMY_nopid","HMS xptar", 200, -0.1, 0.1)
#H_hsxptar_DUMMY_rand  = ROOT.TH1D("H_hsxptar_DUMMY_rand","HMS xptar", 200, -0.1, 0.1)
H_hsxptar_SIMC  = ROOT.TH1D("H_hsxptar_SIMC","HMS xptar", 200, -0.1, 0.1)

H_hsyptar_DATA  = ROOT.TH1D("H_hsyptar_DATA","HMS yptar", 200, -0.1, 0.1)
H_hsyptar_DATA_nocut  = ROOT.TH1D("H_hsyptar_DATA_nocut","HMS yptar", 200, -0.1, 0.1)
H_hsyptar_DATA_nopid  = ROOT.TH1D("H_hsyptar_DATA_nopid","HMS yptar", 200, -0.1, 0.1)
#H_hsyptar_DATA_rand  = ROOT.TH1D("H_hsyptar_DATA_rand","HMS yptar", 200, -0.1, 0.1)
H_hsyptar_DUMMY  = ROOT.TH1D("H_hsyptar_DUMMY","HMS yptar", 200, -0.1, 0.1)
H_hsyptar_DUMMY_nocut  = ROOT.TH1D("H_hsyptar_DUMMY_nocut","HMS yptar", 200, -0.1, 0.1)
H_hsyptar_DUMMY_nopid  = ROOT.TH1D("H_hsyptar_DUMMY_nopid","HMS yptar", 200, -0.1, 0.1)
#H_hsyptar_DUMMY_rand  = ROOT.TH1D("H_hsyptar_DUMMY_rand","HMS yptar", 200, -0.1, 0.1)
H_hsyptar_SIMC  = ROOT.TH1D("H_hsyptar_SIMC","HMS yptar", 200, -0.1, 0.1)

H_ssxfp_DATA    = ROOT.TH1D("H_ssxfp_DATA","SHMS xfp", 200, -25.0, 25.0)
H_ssxfp_DATA_nocut    = ROOT.TH1D("H_ssxfp_DATA_nocut","SHMS xfp", 200, -25.0, 25.0)
H_ssxfp_DATA_nopid    = ROOT.TH1D("H_ssxfp_DATA_nopid","SHMS xfp", 200, -25.0, 25.0)
#H_ssxfp_DATA_rand    = ROOT.TH1D("H_ssxfp_DATA_rand","SHMS xfp", 200, -25.0, 25.0)
H_ssxfp_DUMMY    = ROOT.TH1D("H_ssxfp_DUMMY","SHMS xfp", 200, -25.0, 25.0)
H_ssxfp_DUMMY_nocut    = ROOT.TH1D("H_ssxfp_DUMMY_nocut","SHMS xfp", 200, -25.0, 25.0)
H_ssxfp_DUMMY_nopid    = ROOT.TH1D("H_ssxfp_DUMMY_nopid","SHMS xfp", 200, -25.0, 25.0)
#H_ssxfp_DUMMY_rand    = ROOT.TH1D("H_ssxfp_DUMMY_rand","SHMS xfp", 200, -25.0, 25.0)
H_ssxfp_SIMC    = ROOT.TH1D("H_ssxfp_SIMC","SHMS xfp", 200, -25.0, 25.0)

H_ssyfp_DATA    = ROOT.TH1D("H_ssyfp_DATA","SHMS yfp", 200, -25.0, 25.0)
H_ssyfp_DATA_nocut    = ROOT.TH1D("H_ssyfp_DATA_nocut","SHMS yfp", 200, -25.0, 25.0)
H_ssyfp_DATA_nopid    = ROOT.TH1D("H_ssyfp_DATA_nopid","SHMS yfp", 200, -25.0, 25.0)
#H_ssyfp_DATA_rand    = ROOT.TH1D("H_ssyfp_DATA_rand","SHMS yfp", 200, -25.0, 25.0)
H_ssyfp_DUMMY    = ROOT.TH1D("H_ssyfp_DUMMY","SHMS yfp", 200, -25.0, 25.0)
H_ssyfp_DUMMY_nocut    = ROOT.TH1D("H_ssyfp_DUMMY_nocut","SHMS yfp", 200, -25.0, 25.0)
H_ssyfp_DUMMY_nopid    = ROOT.TH1D("H_ssyfp_DUMMY_nopid","SHMS yfp", 200, -25.0, 25.0)
#H_ssyfp_DUMMY_rand    = ROOT.TH1D("H_ssyfp_DUMMY_rand","SHMS yfp", 200, -25.0, 25.0)
H_ssyfp_SIMC    = ROOT.TH1D("H_ssyfp_SIMC","SHMS yfp", 200, -25.0, 25.0)

H_ssxpfp_DATA   = ROOT.TH1D("H_ssxpfp_DATA","SHMS xpfp", 200, -0.09, 0.09)
H_ssxpfp_DATA_nocut   = ROOT.TH1D("H_ssxpfp_DATA_nocut","SHMS xpfp", 200, -0.09, 0.09)
H_ssxpfp_DATA_nopid   = ROOT.TH1D("H_ssxpfp_DATA_nopid","SHMS xpfp", 200, -0.09, 0.09)
#H_ssxpfp_DATA_rand   = ROOT.TH1D("H_ssxpfp_DATA_rand","SHMS xpfp", 200, -0.09, 0.09)
H_ssxpfp_DUMMY   = ROOT.TH1D("H_ssxpfp_DUMMY","SHMS xpfp", 200, -0.09, 0.09)
H_ssxpfp_DUMMY_nocut   = ROOT.TH1D("H_ssxpfp_DUMMY_nocut","SHMS xpfp", 200, -0.09, 0.09)
H_ssxpfp_DUMMY_nopid   = ROOT.TH1D("H_ssxpfp_DUMMY_nopid","SHMS xpfp", 200, -0.09, 0.09)
#H_ssxpfp_DUMMY_rand   = ROOT.TH1D("H_ssxpfp_DUMMY_rand","SHMS xpfp", 200, -0.09, 0.09)
H_ssxpfp_SIMC   = ROOT.TH1D("H_ssxpfp_SIMC","SHMS xpfp", 200, -0.09, 0.09)

H_ssypfp_DATA   = ROOT.TH1D("H_ssypfp_DATA","SHMS ypfp", 200, -0.05, 0.04)
H_ssypfp_DATA_nocut   = ROOT.TH1D("H_ssypfp_DATA_nocut","SHMS ypfp", 200, -0.05, 0.04)
H_ssypfp_DATA_nopid   = ROOT.TH1D("H_ssypfp_DATA_nopid","SHMS ypfp", 200, -0.05, 0.04)
#H_ssypfp_DATA_rand   = ROOT.TH1D("H_ssypfp_DATA_rand","SHMS ypfp", 200, -0.05, 0.04)
H_ssypfp_DUMMY   = ROOT.TH1D("H_ssypfp_DUMMY","SHMS ypfp", 200, -0.05, 0.04)
H_ssypfp_DUMMY_nocut   = ROOT.TH1D("H_ssypfp_DUMMY_nocut","SHMS ypfp", 200, -0.05, 0.04)
H_ssypfp_DUMMY_nopid   = ROOT.TH1D("H_ssypfp_DUMMY_nopid","SHMS ypfp", 200, -0.05, 0.04)
#H_ssypfp_DUMMY_rand   = ROOT.TH1D("H_ssypfp_DUMMY_rand","SHMS ypfp", 200, -0.05, 0.04)
H_ssypfp_SIMC   = ROOT.TH1D("H_ssypfp_SIMC","SHMS ypfp", 200, -0.05, 0.04)

H_hsxfp_DATA    = ROOT.TH1D("H_hsxfp_DATA","HMS xfp", 200, -40.0, 40.0)
H_hsxfp_DATA_nocut    = ROOT.TH1D("H_hsxfp_DATA_nocut","HMS xfp", 200, -40.0, 40.0)
H_hsxfp_DATA_nopid    = ROOT.TH1D("H_hsxfp_DATA_nopid","HMS xfp", 200, -40.0, 40.0)
#H_hsxfp_DATA_rand    = ROOT.TH1D("H_hsxfp_DATA_rand","HMS xfp", 200, -40.0, 40.0)
H_hsxfp_DUMMY    = ROOT.TH1D("H_hsxfp_DUMMY","HMS xfp", 200, -40.0, 40.0)
H_hsxfp_DUMMY_nocut    = ROOT.TH1D("H_hsxfp_DUMMY_nocut","HMS xfp", 200, -40.0, 40.0)
H_hsxfp_DUMMY_nopid    = ROOT.TH1D("H_hsxfp_DUMMY_nopid","HMS xfp", 200, -40.0, 40.0)
#H_hsxfp_DUMMY_rand    = ROOT.TH1D("H_hsxfp_DUMMY_rand","HMS xfp", 200, -40.0, 40.0)
H_hsxfp_SIMC    = ROOT.TH1D("H_hsxfp_SIMC","HMS xfp", 200, -40.0, 40.0)

H_hsyfp_DATA    = ROOT.TH1D("H_hsyfp_DATA","HMS yfp", 200, -20.0, 20.0)
H_hsyfp_DATA_nocut    = ROOT.TH1D("H_hsyfp_DATA_nocut","HMS yfp", 200, -20.0, 20.0)
H_hsyfp_DATA_nopid    = ROOT.TH1D("H_hsyfp_DATA_nopid","HMS yfp", 200, -20.0, 20.0)
#H_hsyfp_DATA_rand    = ROOT.TH1D("H_hsyfp_DATA_rand","HMS yfp", 200, -20.0, 20.0)
H_hsyfp_DUMMY    = ROOT.TH1D("H_hsyfp_DUMMY","HMS yfp", 200, -20.0, 20.0)
H_hsyfp_DUMMY_nocut    = ROOT.TH1D("H_hsyfp_DUMMY_nocut","HMS yfp", 200, -20.0, 20.0)
H_hsyfp_DUMMY_nopid    = ROOT.TH1D("H_hsyfp_DUMMY_nopid","HMS yfp", 200, -20.0, 20.0)
#H_hsyfp_DUMMY_rand    = ROOT.TH1D("H_hsyfp_DUMMY_rand","HMS yfp", 200, -20.0, 20.0)
H_hsyfp_SIMC    = ROOT.TH1D("H_hsyfp_SIMC","HMS yfp", 200, -20.0, 20.0)

H_hsxpfp_DATA   = ROOT.TH1D("H_hsxpfp_DATA","HMS xpfp", 200, -0.09, 0.05)
H_hsxpfp_DATA_nocut   = ROOT.TH1D("H_hsxpfp_DATA_nocut","HMS xpfp", 200, -0.09, 0.05)
H_hsxpfp_DATA_nopid   = ROOT.TH1D("H_hsxpfp_DATA_nopid","HMS xpfp", 200, -0.09, 0.05)
#H_hsxpfp_DATA_rand   = ROOT.TH1D("H_hsxpfp_DATA_rand","HMS xpfp", 200, -0.09, 0.05)
H_hsxpfp_DUMMY   = ROOT.TH1D("H_hsxpfp_DUMMY","HMS xpfp", 200, -0.09, 0.05)
H_hsxpfp_DUMMY_nocut   = ROOT.TH1D("H_hsxpfp_DUMMY_nocut","HMS xpfp", 200, -0.09, 0.05)
H_hsxpfp_DUMMY_nopid   = ROOT.TH1D("H_hsxpfp_DUMMY_nopid","HMS xpfp", 200, -0.09, 0.05)
#H_hsxpfp_DUMMY_rand   = ROOT.TH1D("H_hsxpfp_DUMMY_rand","HMS xpfp", 200, -0.09, 0.05)
H_hsxpfp_SIMC   = ROOT.TH1D("H_hsxpfp_SIMC","HMS xpfp", 200, -0.09, 0.05)

H_hsypfp_DATA   = ROOT.TH1D("H_hsypfp_DATA","HMS ypfp", 200, -0.05, 0.04)
H_hsypfp_DATA_nocut   = ROOT.TH1D("H_hsypfp_DATA_nocut","HMS ypfp", 200, -0.05, 0.04)
H_hsypfp_DATA_nopid   = ROOT.TH1D("H_hsypfp_DATA_nopid","HMS ypfp", 200, -0.05, 0.04)
#H_hsypfp_DATA_rand   = ROOT.TH1D("H_hsypfp_DATA_rand","HMS ypfp", 200, -0.05, 0.04)
H_hsypfp_DUMMY   = ROOT.TH1D("H_hsypfp_DUMMY","HMS ypfp", 200, -0.05, 0.04)
H_hsypfp_DUMMY_nocut   = ROOT.TH1D("H_hsypfp_DUMMY_nocut","HMS ypfp", 200, -0.05, 0.04)
H_hsypfp_DUMMY_nopid   = ROOT.TH1D("H_hsypfp_DUMMY_nopid","HMS ypfp", 200, -0.05, 0.04)
#H_hsypfp_DUMMY_rand   = ROOT.TH1D("H_hsypfp_DUMMY_rand","HMS ypfp", 200, -0.05, 0.04)
H_hsypfp_SIMC   = ROOT.TH1D("H_hsypfp_SIMC","HMS ypfp", 200, -0.05, 0.04)

H_ssdelta_DATA  = ROOT.TH1D("H_ssdelta_DATA","SHMS delta", 200, -20.0, 20.0)
H_ssdelta_DATA_nocut  = ROOT.TH1D("H_ssdelta_DATA_nocut","SHMS delta", 200, -20.0, 20.0)
H_ssdelta_DATA_nopid  = ROOT.TH1D("H_ssdelta_DATA_nopid","SHMS delta", 200, -20.0, 20.0)
#H_ssdelta_DATA_rand  = ROOT.TH1D("H_ssdelta_DATA_rand","SHMS delta", 200, -20.0, 20.0)
H_ssdelta_DUMMY  = ROOT.TH1D("H_ssdelta_DUMMY","SHMS delta", 200, -20.0, 20.0)
H_ssdelta_DUMMY_nocut  = ROOT.TH1D("H_ssdelta_DUMMY_nocut","SHMS delta", 200, -20.0, 20.0)
H_ssdelta_DUMMY_nopid  = ROOT.TH1D("H_ssdelta_DUMMY_nopid","SHMS delta", 200, -20.0, 20.0)
#H_ssdelta_DUMMY_rand  = ROOT.TH1D("H_ssdelta_DUMMY_rand","SHMS delta", 200, -20.0, 20.0)
H_ssdelta_SIMC  = ROOT.TH1D("H_ssdelta_SIMC","SHMS delta", 200, -20.0, 20.0)

H_ssxptar_DATA  = ROOT.TH1D("H_ssxptar_DATA","SHMS xptar", 200, -0.1, 0.1)
H_ssxptar_DATA_nocut  = ROOT.TH1D("H_ssxptar_DATA_nocut","SHMS xptar", 200, -0.1, 0.1)
H_ssxptar_DATA_nopid  = ROOT.TH1D("H_ssxptar_DATA_nopid","SHMS xptar", 200, -0.1, 0.1)
#H_ssxptar_DATA_rand  = ROOT.TH1D("H_ssxptar_DATA_rand","SHMS xptar", 200, -0.1, 0.1)
H_ssxptar_DUMMY  = ROOT.TH1D("H_ssxptar_DUMMY","SHMS xptar", 200, -0.1, 0.1)
H_ssxptar_DUMMY_nocut  = ROOT.TH1D("H_ssxptar_DUMMY_nocut","SHMS xptar", 200, -0.1, 0.1)
H_ssxptar_DUMMY_nopid  = ROOT.TH1D("H_ssxptar_DUMMY_nopid","SHMS xptar", 200, -0.1, 0.1)
#H_ssxptar_DUMMY_rand  = ROOT.TH1D("H_ssxptar_DUMMY_rand","SHMS xptar", 200, -0.1, 0.1)
H_ssxptar_SIMC  = ROOT.TH1D("H_ssxptar_SIMC","SHMS xptar", 200, -0.1, 0.1)

H_ssyptar_DATA  = ROOT.TH1D("H_ssyptar_DATA","SHMS yptar", 200, -0.04, 0.04)
H_ssyptar_DATA_nocut  = ROOT.TH1D("H_ssyptar_DATA_nocut","SHMS yptar", 200, -0.04, 0.04)
H_ssyptar_DATA_nopid  = ROOT.TH1D("H_ssyptar_DATA_nopid","SHMS yptar", 200, -0.04, 0.04)
#H_ssyptar_DATA_rand  = ROOT.TH1D("H_ssyptar_DATA_rand","SHMS yptar", 200, -0.04, 0.04)
H_ssyptar_DUMMY  = ROOT.TH1D("H_ssyptar_DUMMY","SHMS yptar", 200, -0.04, 0.04)
H_ssyptar_DUMMY_nocut  = ROOT.TH1D("H_ssyptar_DUMMY_nocut","SHMS yptar", 200, -0.04, 0.04)
H_ssyptar_DUMMY_nopid  = ROOT.TH1D("H_ssyptar_DUMMY_nopid","SHMS yptar", 200, -0.04, 0.04)
#H_ssyptar_DUMMY_rand  = ROOT.TH1D("H_ssyptar_DUMMY_rand","SHMS yptar", 200, -0.04, 0.04)
H_ssyptar_SIMC  = ROOT.TH1D("H_ssyptar_SIMC","SHMS yptar", 200, -0.04, 0.04)

H_q_DATA        = ROOT.TH1D("H_q_DATA","q", 200, 0.0, 10.0)
H_q_DATA_nocut        = ROOT.TH1D("H_q_DATA_nocut","q", 200, 0.0, 10.0)
H_q_DATA_nopid        = ROOT.TH1D("H_q_DATA_nopid","q", 200, 0.0, 10.0)
#H_q_DATA_rand        = ROOT.TH1D("H_q_DATA_rand","q", 200, 0.0, 10.0)
H_q_DUMMY        = ROOT.TH1D("H_q_DUMMY","q", 200, 0.0, 10.0)
H_q_DUMMY_nocut        = ROOT.TH1D("H_q_DUMMY_nocut","q", 200, 0.0, 10.0)
H_q_DUMMY_nopid        = ROOT.TH1D("H_q_DUMMY_nopid","q", 200, 0.0, 10.0)
#H_q_DUMMY_rand        = ROOT.TH1D("H_q_DUMMY_rand","q", 200, 0.0, 10.0)
H_q_SIMC        = ROOT.TH1D("H_q_SIMC","q", 200, 0.0, 10.0)

H_Q2_DATA       = ROOT.TH1D("H_Q2_DATA","Q2", 200, 0.0, 10.0)  
H_Q2_DATA_nocut       = ROOT.TH1D("H_Q2_DATA_nocut","Q2", 200, 0.0, 10.0)  
H_Q2_DATA_nopid       = ROOT.TH1D("H_Q2_DATA_nopid","Q2", 200, 0.0, 10.0)  
#H_Q2_DATA_rand       = ROOT.TH1D("H_Q2_DATA_rand","Q2", 200, 0.0, 10.0)  
H_Q2_DUMMY       = ROOT.TH1D("H_Q2_DUMMY","Q2", 200, 0.0, 10.0)  
H_Q2_DUMMY_nocut       = ROOT.TH1D("H_Q2_DUMMY_nocut","Q2", 200, 0.0, 10.0)  
H_Q2_DUMMY_nopid       = ROOT.TH1D("H_Q2_DUMMY_nopid","Q2", 200, 0.0, 10.0)  
#H_Q2_DUMMY_rand       = ROOT.TH1D("H_Q2_DUMMY_rand","Q2", 200, 0.0, 10.0)  
H_Q2_SIMC       = ROOT.TH1D("H_Q2_SIMC","Q2", 200, 0.0, 10.0)  

H_epsilon_DATA  = ROOT.TH1D("H_epsilon_DATA","epsilon", 200, 0.5, 1.0)
H_epsilon_DATA_nocut  = ROOT.TH1D("H_epsilon_DATA_nocut","epsilon", 200, 0.5, 1.0)
H_epsilon_DATA_nopid  = ROOT.TH1D("H_epsilon_DATA_nopid","epsilon", 200, 0.5, 1.0)
#H_epsilon_DATA_rand  = ROOT.TH1D("H_epsilon_DATA_rand","epsilon", 200, 0.5, 1.0)
H_epsilon_DUMMY  = ROOT.TH1D("H_epsilon_DUMMY","epsilon", 200, 0.5, 1.0)
H_epsilon_DUMMY_nocut  = ROOT.TH1D("H_epsilon_DUMMY_nocut","epsilon", 200, 0.5, 1.0)
H_epsilon_DUMMY_nopid  = ROOT.TH1D("H_epsilon_DUMMY_nopid","epsilon", 200, 0.5, 1.0)
#H_epsilon_DUMMY_rand  = ROOT.TH1D("H_epsilon_DUMMY_rand","epsilon", 200, 0.5, 1.0)
H_epsilon_SIMC  = ROOT.TH1D("H_epsilon_SIMC","epsilon", 200, 0.5, 1.0)

H_MMp2_DATA  = ROOT.TH1D("H_MMp2_DATA","(MM)^{2}_{p}", 200, -0.01, 0.01)
H_MMp2_DATA_nocut  = ROOT.TH1D("H_MMp2_DATA_nocut","(MM)^{2}_{p}", 200, -0.01, 0.01)
H_MMp2_DATA_nopid  = ROOT.TH1D("H_MMp2_DATA_nopid","(MM)^{2}_{p}", 200, -0.01, 0.01)
#H_MMp2_DATA_rand  = ROOT.TH1D("H_MMp2_DATA_rand","(MM)^{2}_{p}", 200, -0.01, 0.01)
H_MMp2_DUMMY  = ROOT.TH1D("H_MMp2_DUMMY","(MM)^{2}_{p}", 200, -0.01, 0.01)
H_MMp2_DUMMY_nocut  = ROOT.TH1D("H_MMp2_DUMMY_nocut","(MM)^{2}_{p}", 200, -0.01, 0.01)
H_MMp2_DUMMY_nopid  = ROOT.TH1D("H_MMp2_DUMMY_nopid","(MM)^{2}_{p}", 200, -0.01, 0.01)
#H_MMp2_DUMMY_rand  = ROOT.TH1D("H_MMp2_DUMMY_rand","(MM)^{2}_{p}", 200, -0.01, 0.01)
H_MMp2_SIMC  = ROOT.TH1D("H_MMp2_SIMC","(MM)^{2}_{p}", 200, -0.01, 0.01)

H_th_DATA  = ROOT.TH1D("H_th_DATA","X' tar", 200, -0.1, 0.1)
H_th_DATA_nocut  = ROOT.TH1D("H_th_DATA_nocut","X' tar", 200, -0.1, 0.1)
H_th_DATA_nopid  = ROOT.TH1D("H_th_DATA_nopid","X' tar", 200, -0.1, 0.1)
#H_th_DATA_rand  = ROOT.TH1D("H_th_DATA_rand","X' tar", 200, -0.1, 0.1)
H_th_DUMMY  = ROOT.TH1D("H_th_DUMMY","X' tar", 200, -0.1, 0.1)
H_th_DUMMY_nocut  = ROOT.TH1D("H_th_DUMMY_nocut","X' tar", 200, -0.1, 0.1)
H_th_DUMMY_nopid  = ROOT.TH1D("H_th_DUMMY_nopid","X' tar", 200, -0.1, 0.1)
#H_th_DUMMY_rand  = ROOT.TH1D("H_th_DUMMY_rand","X' tar", 200, -0.1, 0.1)
H_th_SIMC  = ROOT.TH1D("H_th_SIMC","X' tar", 200, -0.1, 0.1)

H_ph_DATA  = ROOT.TH1D("H_ph_DATA","Y' tar", 200, -0.1, 0.1)
H_ph_DATA_nocut  = ROOT.TH1D("H_ph_DATA_nocut","Y' tar", 200, -0.1, 0.1)
H_ph_DATA_nopid  = ROOT.TH1D("H_ph_DATA_nopid","Y' tar", 200, -0.1, 0.1)
#H_ph_DATA_rand  = ROOT.TH1D("H_ph_DATA_rand","Y' tar", 200, -0.1, 0.1)
H_ph_DUMMY  = ROOT.TH1D("H_ph_DUMMY","Y' tar", 200, -0.1, 0.1)
H_ph_DUMMY_nocut  = ROOT.TH1D("H_ph_DUMMY_nocut","Y' tar", 200, -0.1, 0.1)
H_ph_DUMMY_nopid  = ROOT.TH1D("H_ph_DUMMY_nopid","Y' tar", 200, -0.1, 0.1)
#H_ph_DUMMY_rand  = ROOT.TH1D("H_ph_DUMMY_rand","Y' tar", 200, -0.1, 0.1)
H_ph_SIMC  = ROOT.TH1D("H_ph_SIMC","Y' tar", 200, -0.1, 0.1)

H_ph_q_DATA  = ROOT.TH1D("H_ph_q_DATA","Phi Detected (ph_xq)", 200, -10.0, 10.0)
H_ph_q_DATA_nocut  = ROOT.TH1D("H_ph_q_DATA_nocut","Phi Detected (ph_xq)", 200, -10.0, 10.0)
H_ph_q_DATA_nopid  = ROOT.TH1D("H_ph_q_DATA_nopid","Phi Detected (ph_xq)", 200, -10.0, 10.0)
#H_ph_q_DATA_rand  = ROOT.TH1D("H_ph_q_DATA_rand","Phi Detected (ph_xq)", 200, -10.0, 10.0)
H_ph_q_DUMMY  = ROOT.TH1D("H_ph_q_DUMMY","Phi Detected (ph_xq)", 200, -10.0, 10.0)
H_ph_q_DUMMY_nocut  = ROOT.TH1D("H_ph_q_DUMMY_nocut","Phi Detected (ph_xq)", 200, -10.0, 10.0)
H_ph_q_DUMMY_nopid  = ROOT.TH1D("H_ph_q_DUMMY_nopid","Phi Detected (ph_xq)", 200, -10.0, 10.0)
#H_ph_q_DUMMY_rand  = ROOT.TH1D("H_ph_q_DUMMY_rand","Phi Detected (ph_xq)", 200, -10.0, 10.0)
H_ph_q_SIMC  = ROOT.TH1D("H_ph_q_SIMC","Phi Detected (ph_xq)", 200, -10.0, 10.0)

H_th_q_DATA  = ROOT.TH1D("H_th_q_DATA","Theta Detected (th_xq)", 200, -0.2, 0.2)
H_th_q_DATA_nocut  = ROOT.TH1D("H_th_q_DATA_nocut","Theta Detected (th_xq)", 200, -0.2, 0.2)
H_th_q_DATA_nopid  = ROOT.TH1D("H_th_q_DATA_nopid","Theta Detected (th_xq)", 200, -0.2, 0.2)
#H_th_q_DATA_rand  = ROOT.TH1D("H_th_q_DATA_rand","Theta Detected (th_xq)", 200, -0.2, 0.2)
H_th_q_DUMMY  = ROOT.TH1D("H_th_q_DUMMY","Theta Detected (th_xq)", 200, -0.2, 0.2)
H_th_q_DUMMY_nocut  = ROOT.TH1D("H_th_q_DUMMY_nocut","Theta Detected (th_xq)", 200, -0.2, 0.2)
H_th_q_DUMMY_nopid  = ROOT.TH1D("H_th_q_DUMMY_nopid","Theta Detected (th_xq)", 200, -0.2, 0.2)
#H_th_q_DUMMY_rand  = ROOT.TH1D("H_th_q_DUMMY_rand","Theta Detected (th_xq)", 200, -0.2, 0.2)
H_th_q_SIMC  = ROOT.TH1D("H_th_q_SIMC","Theta Detected (th_xq)", 200, -0.2, 0.2)

H_ph_recoil_DATA  = ROOT.TH1D("H_ph_recoil_DATA","Phi Recoil (ph_bq)", 200, -10.0, 10.0)
H_ph_recoil_DATA_nocut  = ROOT.TH1D("H_ph_recoil_DATA_nocut","Phi Recoil (ph_bq)", 200, -10.0, 10.0)
H_ph_recoil_DATA_nopid  = ROOT.TH1D("H_ph_recoil_DATA_nopid","Phi Recoil (ph_bq)", 200, -10.0, 10.0)
#H_ph_recoil_DATA_rand  = ROOT.TH1D("H_ph_recoil_DATA_rand","Phi Recoil (ph_bq)", 200, -10.0, 10.0)
H_ph_recoil_DUMMY  = ROOT.TH1D("H_ph_recoil_DUMMY","Phi Recoil (ph_bq)", 200, -10.0, 10.0)
H_ph_recoil_DUMMY_nocut  = ROOT.TH1D("H_ph_recoil_DUMMY_nocut","Phi Recoil (ph_bq)", 200, -10.0, 10.0)
H_ph_recoil_DUMMY_nopid  = ROOT.TH1D("H_ph_recoil_DUMMY_nopid","Phi Recoil (ph_bq)", 200, -10.0, 10.0)
#H_ph_recoil_DUMMY_rand  = ROOT.TH1D("H_ph_recoil_DUMMY_rand","Phi Recoil (ph_bq)", 200, -10.0, 10.0)
H_ph_recoil_SIMC  = ROOT.TH1D("H_ph_recoil_SIMC","Phi Recoil (ph_bq)", 200, -10.0, 10.0)

H_th_recoil_DATA  = ROOT.TH1D("H_th_recoil_DATA","Theta Recoil (th_bq)", 200, -10.0, 10.0)
H_th_recoil_DATA_nocut  = ROOT.TH1D("H_th_recoil_DATA_nocut","Theta Recoil (th_bq)", 200, -10.0, 10.0)
H_th_recoil_DATA_nopid  = ROOT.TH1D("H_th_recoil_DATA_nopid","Theta Recoil (th_bq)", 200, -10.0, 10.0)
#H_th_recoil_DATA_rand  = ROOT.TH1D("H_th_recoil_DATA_rand","Theta Recoil (th_bq)", 200, -10.0, 10.0)
H_th_recoil_DUMMY  = ROOT.TH1D("H_th_recoil_DUMMY","Theta Recoil (th_bq)", 200, -10.0, 10.0)
H_th_recoil_DUMMY_nocut  = ROOT.TH1D("H_th_recoil_DUMMY_nocut","Theta Recoil (th_bq)", 200, -10.0, 10.0)
H_th_recoil_DUMMY_nopid  = ROOT.TH1D("H_th_recoil_DUMMY_nopid","Theta Recoil (th_bq)", 200, -10.0, 10.0)
#H_th_recoil_DUMMY_rand  = ROOT.TH1D("H_th_recoil_DUMMY_rand","Theta Recoil (th_bq)", 200, -10.0, 10.0)
H_th_recoil_SIMC  = ROOT.TH1D("H_th_recoil_SIMC","Theta Recoil (th_bq)", 200, -10.0, 10.0)

H_pmiss_DATA  = ROOT.TH1D("H_pmiss_DATA","pmiss", 200, -1.0, 1.0)
H_pmiss_DATA_nocut  = ROOT.TH1D("H_pmiss_DATA_nocut","pmiss", 200, -1.0, 1.0)
H_pmiss_DATA_nopid  = ROOT.TH1D("H_pmiss_DATA_nopid","pmiss", 200, -1.0, 1.0)
#H_pmiss_DATA_rand  = ROOT.TH1D("H_pmiss_DATA_rand","pmiss", 200, -1.0, 1.0)
H_pmiss_DUMMY  = ROOT.TH1D("H_pmiss_DUMMY","pmiss", 200, -1.0, 1.0)
H_pmiss_DUMMY_nocut  = ROOT.TH1D("H_pmiss_DUMMY_nocut","pmiss", 200, -1.0, 1.0)
H_pmiss_DUMMY_nopid  = ROOT.TH1D("H_pmiss_DUMMY_nopid","pmiss", 200, -1.0, 1.0)
#H_pmiss_DUMMY_rand  = ROOT.TH1D("H_pmiss_DUMMY_rand","pmiss", 200, -1.0, 1.0)
H_pmiss_SIMC  = ROOT.TH1D("H_pmiss_SIMC","pmiss", 200, -1.0, 1.0)

H_emiss_DATA  = ROOT.TH1D("H_emiss_DATA","emiss", 200, -1.0, 1.0)
H_emiss_DATA_nocut  = ROOT.TH1D("H_emiss_DATA_nocut","emiss", 200, -1.0, 1.0)
H_emiss_DATA_nopid  = ROOT.TH1D("H_emiss_DATA_nopid","emiss", 200, -1.0, 1.0)
#H_emiss_DATA_rand  = ROOT.TH1D("H_emiss_DATA_rand","emiss", 200, -1.0, 1.0)
H_emiss_DUMMY  = ROOT.TH1D("H_emiss_DUMMY","emiss", 200, -1.0, 1.0)
H_emiss_DUMMY_nocut  = ROOT.TH1D("H_emiss_DUMMY_nocut","emiss", 200, -1.0, 1.0)
H_emiss_DUMMY_nopid  = ROOT.TH1D("H_emiss_DUMMY_nopid","emiss", 200, -1.0, 1.0)
#H_emiss_DUMMY_rand  = ROOT.TH1D("H_emiss_DUMMY_rand","emiss", 200, -1.0, 1.0)
H_emiss_SIMC  = ROOT.TH1D("H_emiss_SIMC","emiss", 200, -1.0, 1.0)

H_pmx_DATA  = ROOT.TH1D("H_pmx_DATA","pmx", 200, -1.0, 1.0)
H_pmx_DATA_nocut  = ROOT.TH1D("H_pmx_DATA_nocut","pmx", 200, -1.0, 1.0)
H_pmx_DATA_nopid  = ROOT.TH1D("H_pmx_DATA_nopid","pmx", 200, -1.0, 1.0)
#H_pmx_DATA_rand  = ROOT.TH1D("H_pmx_DATA_rand","pmx", 200, -1.0, 1.0)
H_pmx_DUMMY  = ROOT.TH1D("H_pmx_DUMMY","pmx", 200, -1.0, 1.0)
H_pmx_DUMMY_nocut  = ROOT.TH1D("H_pmx_DUMMY_nocut","pmx", 200, -1.0, 1.0)
H_pmx_DUMMY_nopid  = ROOT.TH1D("H_pmx_DUMMY_nopid","pmx", 200, -1.0, 1.0)
#H_pmx_DUMMY_rand  = ROOT.TH1D("H_pmx_DUMMY_rand","pmx", 200, -1.0, 1.0)
H_pmx_SIMC  = ROOT.TH1D("H_pmx_SIMC","pmx", 200, -1.0, 1.0)

H_pmy_DATA  = ROOT.TH1D("H_pmy_DATA","pmy ", 200, -1.0, 1.0)
H_pmy_DATA_nocut  = ROOT.TH1D("H_pmy_DATA_nocut","pmy ", 200, -1.0, 1.0)
H_pmy_DATA_nopid  = ROOT.TH1D("H_pmy_DATA_nopid","pmy ", 200, -1.0, 1.0)
#H_pmy_DATA_rand  = ROOT.TH1D("H_pmy_DATA_rand","pmy ", 200, -1.0, 1.0)
H_pmy_DUMMY  = ROOT.TH1D("H_pmy_DUMMY","pmy ", 200, -1.0, 1.0)
H_pmy_DUMMY_nocut  = ROOT.TH1D("H_pmy_DUMMY_nocut","pmy ", 200, -1.0, 1.0)
H_pmy_DUMMY_nopid  = ROOT.TH1D("H_pmy_DUMMY_nopid","pmy ", 200, -1.0, 1.0)
#H_pmy_DUMMY_rand  = ROOT.TH1D("H_pmy_DUMMY_rand","pmy ", 200, -1.0, 1.0)
H_pmy_SIMC  = ROOT.TH1D("H_pmy_SIMC","pmy", 200, -1.0, 1.0)

H_pmz_DATA  = ROOT.TH1D("H_pmz_DATA","pmz", 200, -1.0, 1.0)
H_pmz_DATA_nocut  = ROOT.TH1D("H_pmz_DATA_nocut","pmz", 200, -1.0, 1.0)
H_pmz_DATA_nopid  = ROOT.TH1D("H_pmz_DATA_nopid","pmz", 200, -1.0, 1.0)
#H_pmz_DATA_rand  = ROOT.TH1D("H_pmz_DATA_rand","pmz", 200, -1.0, 1.0)
H_pmz_DUMMY  = ROOT.TH1D("H_pmz_DUMMY","pmz", 200, -1.0, 1.0)
H_pmz_DUMMY_nocut  = ROOT.TH1D("H_pmz_DUMMY_nocut","pmz", 200, -1.0, 1.0)
H_pmz_DUMMY_nopid  = ROOT.TH1D("H_pmz_DUMMY_nopid","pmz", 200, -1.0, 1.0)
#H_pmz_DUMMY_rand  = ROOT.TH1D("H_pmz_DUMMY_rand","pmz", 200, -1.0, 1.0)
H_pmz_SIMC  = ROOT.TH1D("H_pmz_SIMC","pmz", 200, -1.0, 1.0)

H_W_DATA  = ROOT.TH1D("H_W_DATA","W ", 200, 0.5, 2.0)
H_W_DATA_nocut  = ROOT.TH1D("H_W_DATA_nocut","W ", 200, 0.5, 2.0)
H_W_DATA_nopid  = ROOT.TH1D("H_W_DATA_nopid","W ", 200, 0.5, 2.0)
#H_W_DATA_rand  = ROOT.TH1D("H_W_DATA_rand","W ", 200, 0.5, 2.0)
H_W_DUMMY  = ROOT.TH1D("H_W_DUMMY","W ", 200, 0.5, 2.0)
H_W_DUMMY_nocut  = ROOT.TH1D("H_W_DUMMY_nocut","W ", 200, 0.5, 2.0)
H_W_DUMMY_nopid  = ROOT.TH1D("H_W_DUMMY_nopid","W ", 200, 0.5, 2.0)
#H_W_DUMMY_rand  = ROOT.TH1D("H_W_DUMMY_rand","W ", 200, 0.5, 2.0)
H_W_SIMC  = ROOT.TH1D("H_W_SIMC","W", 200, 0.5, 2.0)

H_ct_ep_DATA = ROOT.TH1D("H_ct_ep_DATA", "Electron-Proton CTime", 200, -10, 10)
H_ct_ep_DATA_nocut = ROOT.TH1D("H_ct_ep_DATA_nocut", "Electron-Proton CTime", 200, -10, 10)
H_ct_ep_DATA_nopid = ROOT.TH1D("H_ct_ep_DATA_nopid", "Electron-Proton CTime", 200, -10, 10)
H_ct_ep_DUMMY = ROOT.TH1D("H_ct_ep_DUMMY", "Electron-Proton CTime", 200, -10, 10)
H_ct_ep_DUMMY_nocut = ROOT.TH1D("H_ct_ep_DUMMY_nocut", "Electron-Proton CTime", 200, -10, 10)
H_ct_ep_DUMMY_nopid = ROOT.TH1D("H_ct_ep_DUMMY_nopid", "Electron-Proton CTime", 200, -10, 10)

H_pbeta_DATA = ROOT.TH1D("H_pbeta_DATA", "SHMS_#beta", 200, 0, 2)
H_pbeta_DATA_nocut = ROOT.TH1D("H_pbeta_DATA_nocut", "SHMS_#beta no cut", 200, 0, 2)

H_hbeta_DATA = ROOT.TH1D("H_hbeta_DATA", "HMS_#beta", 200, 0, 2)
H_hbeta_DATA_nocut = ROOT.TH1D("H_hbeta_DATA_nocut", "HMS_#beta no cut", 200, 0, 2)

CoinTime_vs_pbeta_DATA = ROOT.TH2D("CoinTime_vs_pbeta_DATA", "CTime vs SHMS #beta; Coin_Time; SHMS_#beta", 500, -50, 50, 500, 0, 2)
CoinTime_vs_pbeta_DATA_nocut = ROOT.TH2D("CoinTime_vs_pbeta_DATA_nocut", "CTime vs SHMS #beta  no cut; Coin_Time; SHMS_#beta", 500, -50, 50, 500, 0, 2)

CoinTime_vs_hbeta_DATA = ROOT.TH2D("CoinTime_vs_hbeta_DATA", "CTime vs HMS #beta; Coin_Time; HMS_#beta", 500, -50, 50, 500, 0, 2)
CoinTime_vs_hbeta_DATA_nocut = ROOT.TH2D("CoinTime_vs_hbeta_DATA_nocut", "CTime vs HMS #beta  no cut; Coin_Time; HMS_#beta", 500, -50, 50, 500, 0, 2)

H_ct_ep_vs_H_MMp2_DATA = ROOT.TH2D("H_ct_ep_vs_H_MMp2_DATA","Electron-Proton CTime vs (MM)^{2}_{p}; e p Coin_Time; (MM)^{2}_{p}", 200, -10, 10, 200, -0.1, 0.1)
#H_ct_ep_vs_H_MMp2_DATA_rand = ROOT.TH2D("H_ct_ep_vs_H_MMp2_DATA_rand","Electron-Proton CTime vs (MM)^{2}_{p}; e p Coin_Time; (MM)^{2}_{p}", 200, -10, 10, 200, -0.1, 0.1)

H_emiss_vs_H_hsdelta_DATA = ROOT.TH2D("H_emiss_vs_H_hsdelta_DATA","Emiss vs HMS Delta;  Emiss; HMS Delta", 200, -0.1, 0.1, 200, -20.0, 20.0)
H_emiss_vs_H_ssdelta_DATA = ROOT.TH2D("H_emiss_vs_H_ssdelta_DATA","Emiss vs SHMS Delta;  Emiss; SHMS Delta", 200, -0.1, 0.1, 200, -20.0, 20.0)

H_pmiss_vs_H_hsdelta_DATA = ROOT.TH2D("H_pmiss_vs_H_hsdelta_DATA","Pmiss vs HMS Delta;  Pmiss; HMS Delta", 200, -0.1, 0.1, 200, -20.0, 20.0)
H_pmiss_vs_H_ssdelta_DATA = ROOT.TH2D("H_pmiss_vs_H_ssdelta_DATA","Pmiss vs SHMS Delta;  Pmiss; SHMS Delta", 200, -0.1, 0.1, 200, -20.0, 20.0)

H_hsdelta_vs_H_ssdelta_DATA = ROOT.TH2D("H_hsdelta_vs_H_ssdelta_DATA","HMS Delta vs SHMS Delta;  HMS Delta; SHMS Delta", 200, -20.0,20.0, 200, -20.0, 20.0)

H_raster_x_vs_H_pmiss_DATA = ROOT.TH2D("H_raster_x_vs_H_pmiss_DATA","Raster_X vs pmiss;  pmiss; Raster_X", 200, -0.1,0.1, 200, -0.25,0.25)
H_raster_x_vs_H_emiss_DATA = ROOT.TH2D("H_raster_x_vs_H_emiss_DATA","Raster_X vs emiss;  emiss; Raster_X", 200, -0.1,0.1, 200, -0.25,0.25)
H_raster_y_vs_H_pmiss_DATA = ROOT.TH2D("H_raster_y_vs_H_pmiss_DATA","Raster_Y vs pmiss;  pmiss; Raster_Y", 200, -0.1,0.1, 200, -0.05,0.25)
H_raster_y_vs_H_emiss_DATA = ROOT.TH2D("H_raster_y_vs_H_emiss_DATA","Raster_Y vs emiss;  emiss; Raster_Y", 200, -0.1,0.1, 200, -0.05,0.25)
H_raster_x_vs_H_raster_y_DATA = ROOT.TH2D("H_raster_x_vs_H_raster_y_DATA","Raster_X vs Raster_Y;  Raster_X; Raster_Y", 200, -0.25,0.25, 200, -0.05,0.25)

H_cal_etottracknorm_DATA = ROOT.TH1D("H_cal_etottracknorm_DATA", "HMS Cal etottracknorm", 200, 0.2, 1.8)
H_cer_npeSum_DATA = ROOT.TH1D("H_cer_npeSum_DATA", "HMS Cer Npe Sum", 200, 0, 30)

P_cal_etottracknorm_DATA = ROOT.TH1D("P_cal_etottracknorm_DATA", "SHMS Cal etottracknorm", 200, 0, 1)
P_hgcer_npeSum_DATA = ROOT.TH1D("P_hgcer_npeSum_DATA", "SHMS HGCer Npe Sum", 200, 0, 50)
P_aero_npeSum_DATA = ROOT.TH1D("P_aero_npeSum_DATA", "SHMS Aero Npe Sum", 200, 0, 50)

H_cal_etottracknorm_DATA_nocut = ROOT.TH1D("H_cal_etottracknorm_DATA_nocut", "HMS Cal etottracknorm", 200, 0.2, 1.8)
H_cal_etottracknorm_DATA_nopid = ROOT.TH1D("H_cal_etottracknorm_DATA_nopid", "HMS Cal etottracknorm", 200, 0.2, 1.8)
H_cer_npeSum_DATA_nocut = ROOT.TH1D("H_cer_npeSum_DATA_nocut", "HMS Cer Npe Sum", 200, 0, 30)
H_cer_npeSum_DATA_nopid = ROOT.TH1D("H_cer_npeSum_DATA_nopid", "HMS Cer Npe Sum", 200, 0, 30)

P_cal_etottracknorm_DATA_nocut = ROOT.TH1D("P_cal_etottracknorm_DATA_nocut", "SHMS Cal etottracknorm", 200, 0, 1)
P_cal_etottracknorm_DATA_nopid = ROOT.TH1D("P_cal_etottracknorm_DATA_nopid", "SHMS Cal etottracknorm", 200, 0, 1)
P_hgcer_npeSum_DATA_nocut = ROOT.TH1D("P_hgcer_npeSum_DATA_nocut", "SHMS HGCer Npe Sum", 200, 0, 50)
P_hgcer_npeSum_DATA_nopid = ROOT.TH1D("P_hgcer_npeSum_DATA_nopid", "SHMS HGCer Npe Sum", 200, 0, 50)
P_aero_npeSum_DATA_nocut = ROOT.TH1D("P_aero_npeSum_DATA_nocut", "SHMS Aero Npe Sum", 200, 0, 50)
P_aero_npeSum_DATA_nopid = ROOT.TH1D("P_aero_npeSum_DATA_nopid", "SHMS Aero Npe Sum", 200, 0, 50)

H_cal_etottracknorm_vs_H_cer_npeSum_DATA = ROOT.TH2D("H_cal_etottracknorm_vs_H_cer_npeSum_DATA","HMS Cal etottracknorm vs HMS Cer Npe Sum;  HMS Cal etottracknorm; HMS Cer Npe Sum", 200, 0.2, 1.8, 200, 0, 30)
P_cal_etottracknorm_vs_P_hgcer_npeSum_DATA = ROOT.TH2D("P_cal_etottracknorm_vs_P_hgcer_npeSum_DATA","SHMS Cal etottracknorm vs SHMS HGCer Npe Sum;  SHMS Cal etottracknorm; SHMS HGCer Npe Sum", 200, 0, 1, 200, 0, 50)
P_cal_etottracknorm_vs_P_aero_npeSum_DATA = ROOT.TH2D("P_cal_etottracknorm_vs_P_aero_npeSum_DATA","SHMS Cal etottracknorm vs SHMS Aero Npe Sum;  SHMS Cal etottracknorm; SHMS Aero Npe Sum", 200, 0, 1, 200, 0, 50)
P_hgcer_npeSum_vs_P_aero_npeSum_DATA = ROOT.TH2D("P_hgcer_npeSum_vs_P_aero_npeSum_DATA","SHMS HGCer Npe Sum vs SHMS Aero Npe Sum;  SHMS HGCer Npe Sum; SHMS Aero Npe Sum", 200, 0, 50, 200, 0, 50)

bpm_tar_x_DATA  = ROOT.TH1D("bpm_tar_x_DATA","BPM Target x", 200, -0.1, 0.1)
bpm_tar_x_DATA_nocut  = ROOT.TH1D("bpm_tar_x_DATA_nocut","BPM Target x", 200, -0.1, 0.1)
bpm_tar_x_DATA_nopid  = ROOT.TH1D("bpm_tar_x_DATA_nopid","BPM Target x", 200, -0.1, 0.1)

bpm_tar_y_DATA  = ROOT.TH1D("bpm_tar_y_DATA","BPM Target y", 200, 0.0, 0.2)
bpm_tar_y_DATA_nocut  = ROOT.TH1D("bpm_tar_y_DATA_nocut","BPM Target y", 200, 0.0, 0.2)
bpm_tar_y_DATA_nopid  = ROOT.TH1D("bpm_tar_y_DATA_nopid","BPM Target y", 200, 0.0, 0.2)

################################################################################################################################################
# Fill histograms for various trees called above

for evt in TBRANCH_SIMC:

  # Define the acceptance cuts  

  # Select the cuts
  SHMS_Acceptance = (evt.ssdelta>=-10.0) & (evt.ssdelta<=20.0) & (evt.ssxptar>=-0.06) & (evt.ssxptar<=0.06) & (evt.ssyptar>=-0.04) & (evt.ssyptar<=0.04)
  HMS_Acceptance = (evt.hsdelta>=-8.0) & (evt.hsdelta<=8.0) & (evt.hsxptar>=-0.08) & (evt.hsxptar<=0.08) & (evt.hsyptar>=-0.045) & (evt.hsyptar<=0.045)
  #........................................

  #Fill SIMC events
  if(HMS_Acceptance & SHMS_Acceptance):
    
      H_ssxfp_SIMC.Fill(evt.ssxfp, evt.Weight)
      H_ssyfp_SIMC.Fill(evt.ssyfp, evt.Weight)
      H_ssxpfp_SIMC.Fill(evt.ssxpfp, evt.Weight)
      H_ssypfp_SIMC.Fill(evt.ssypfp, evt.Weight)
      H_hsxfp_SIMC.Fill(evt.hsxfp, evt.Weight)
      H_hsyfp_SIMC.Fill(evt.hsyfp, evt.Weight)
      H_hsxpfp_SIMC.Fill(evt.hsxpfp, evt.Weight)
      H_hsypfp_SIMC.Fill(evt.hsypfp, evt.Weight)
      H_ssdelta_SIMC.Fill(evt.ssdelta, evt.Weight) 
      H_hsdelta_SIMC.Fill(evt.hsdelta, evt.Weight)
      H_ssxptar_SIMC.Fill(evt.ssxptar, evt.Weight)
      H_ssyptar_SIMC.Fill(evt.ssyptar, evt.Weight)
      H_hsxptar_SIMC.Fill(evt.hsxptar, evt.Weight)
      H_hsyptar_SIMC.Fill(evt.hsyptar, evt.Weight)

      H_ph_q_SIMC.Fill(evt.phipq, evt.Weight)
      H_th_q_SIMC.Fill(evt.thetapq, evt.Weight)

      H_pmiss_SIMC.Fill(evt.Pm, evt.Weight)
      H_emiss_SIMC.Fill(evt.Em, evt.Weight)
      H_pmx_SIMC.Fill(evt.Pmx, evt.Weight)
      H_pmy_SIMC.Fill(evt.Pmy, evt.Weight)
      H_pmz_SIMC.Fill(evt.Pmz, evt.Weight)
      H_Q2_SIMC.Fill(evt.Q2, evt.Weight)
      H_W_SIMC.Fill(evt.W, evt.Weight)
      H_epsilon_SIMC.Fill(evt.epsilon, evt.Weight)
      H_MMp2_SIMC.Fill(pow(evt.Em, 2) - pow(evt.Pm, 2), evt.Weight)
      
ibin = 1
for evt in TBRANCH_DATA:

  #CUTs Definations 
  SHMS_FixCut = (evt.P_hod_goodstarttime == 1) & (evt.P_dc_InsideDipoleExit == 1) 
  SHMS_Acceptance = (evt.ssdelta>=-10.0) & (evt.ssdelta<=20.0) & (evt.ssxptar>=-0.06) & (evt.ssxptar<=0.06) & (evt.ssyptar>=-0.04) & (evt.ssyptar<=0.04)

  HMS_FixCut = (evt.H_hod_goodstarttime == 1) & (evt.H_dc_InsideDipoleExit == 1)
  HMS_Acceptance = (evt.hsdelta>=-8.0) & (evt.hsdelta<=8.0) & (evt.hsxptar>=-0.08) & (evt.hsxptar<=0.08) & (evt.hsyptar>=-0.045) & (evt.hsyptar<=0.045)       

  #........................................
    
  if(HMS_FixCut & HMS_Acceptance & SHMS_FixCut & SHMS_Acceptance):

      H_ct_ep_vs_H_MMp2_DATA.Fill(evt.CTime_epCoinTime_ROC1, evt.MMp)
      H_ct_ep_DATA.Fill(evt.CTime_epCoinTime_ROC1)

      H_pbeta_DATA.Fill(evt.P_gtr_beta)
      H_hbeta_DATA.Fill(evt.H_gtr_beta)
      
      CoinTime_vs_pbeta_DATA.Fill(evt.CTime_epCoinTime_ROC1, evt.P_gtr_beta)
      CoinTime_vs_hbeta_DATA.Fill(evt.CTime_epCoinTime_ROC1, evt.H_gtr_beta)
      
      H_emiss_vs_H_hsdelta_DATA.Fill(evt.emiss, evt.hsdelta)
      H_emiss_vs_H_ssdelta_DATA.Fill(evt.emiss, evt.ssdelta)
      H_pmiss_vs_H_hsdelta_DATA.Fill(evt.pmiss, evt.hsdelta)
      H_pmiss_vs_H_ssdelta_DATA.Fill(evt.pmiss, evt.ssdelta)
      H_hsdelta_vs_H_ssdelta_DATA.Fill(evt.hsdelta, evt.ssdelta)

      H_raster_x_vs_H_pmiss_DATA.Fill(evt.pmiss, evt.raster_x)
      H_raster_x_vs_H_emiss_DATA.Fill(evt.emiss, evt.raster_x)
      H_raster_y_vs_H_pmiss_DATA.Fill(evt.pmiss, evt.raster_y)
      H_raster_y_vs_H_emiss_DATA.Fill(evt.emiss, evt.raster_y)
      H_raster_x_vs_H_raster_y_DATA.Fill(evt.raster_x, evt.raster_y)
      
      H_ssxfp_DATA.Fill(evt.ssxfp)
      H_ssyfp_DATA.Fill(evt.ssyfp)
      H_ssxpfp_DATA.Fill(evt.ssxpfp)
      H_ssypfp_DATA.Fill(evt.ssypfp)
      H_ssdelta_DATA.Fill(evt.ssdelta)
      H_ssxptar_DATA.Fill(evt.ssxptar)
      H_ssyptar_DATA.Fill(evt.ssyptar)
      
      H_hsxfp_DATA.Fill(evt.hsxfp)
      H_hsyfp_DATA.Fill(evt.hsyfp)
      H_hsxpfp_DATA.Fill(evt.hsxpfp)
      H_hsypfp_DATA.Fill(evt.hsypfp)
      H_hsdelta_DATA.Fill(evt.hsdelta)
      H_hsxptar_DATA.Fill(evt.hsxptar)
      H_hsyptar_DATA.Fill(evt.hsyptar)

      H_ph_q_DATA.Fill(evt.ph_q)
      H_th_q_DATA.Fill(evt.th_q)
      H_ph_recoil_DATA.Fill(evt.ph_recoil)
      H_th_recoil_DATA.Fill(evt.th_recoil)
      
      H_pmiss_DATA.Fill(evt.pmiss)
      H_emiss_DATA.Fill(evt.emiss)
      #H_emiss_DATA.Fill(evt.emiss_nuc)
      H_pmx_DATA.Fill(evt.pmx)
      H_pmy_DATA.Fill(evt.pmy)
      H_pmz_DATA.Fill(evt.pmz)
      H_Q2_DATA.Fill(evt.Q2)
      H_W_DATA.Fill(evt.W)
      H_epsilon_DATA.Fill(evt.epsilon)
      H_MMp2_DATA.Fill(pow(evt.emiss, 2) - pow(evt.pmiss, 2))  
      #H_MMp2_DATA.Fill(pow(evt.MMp, 2))  
      #H_MMp2_DATA.Fill(evt.Mrecoil)
      
      ###################################################################################################################################################

      bpm_tar_x_DATA.Fill(evt.bpm_tar_x)
      bpm_tar_y_DATA.Fill(evt.bpm_tar_y)      
      
      ###################################################################################################################################################
      
      '''
      # Random subtraction
      H_ct_ep_vs_H_MMp2_DATA_rand.Fill(evt.CTime_epCoinTime_ROC1, evt.MMp)
      
      H_ssxfp_DATA_rand.Fill(evt.ssxfp)
      H_ssyfp_DATA_rand.Fill(evt.ssyfp)
      H_ssxpfp_DATA_rand.Fill(evt.ssxpfp)
      H_ssypfp_DATA_rand.Fill(evt.ssypfp)
      H_ssdelta_DATA_rand.Fill(evt.ssdelta)
      H_ssxptar_DATA_rand.Fill(evt.ssxptar)
      H_ssyptar_DATA_rand.Fill(evt.ssyptar)
      
      H_hsxfp_DATA_rand.Fill(evt.hsxfp)
      H_hsyfp_DATA_rand.Fill(evt.hsyfp)
      H_hsxpfp_DATA_rand.Fill(evt.hsxpfp)
      H_hsypfp_DATA_rand.Fill(evt.hsypfp)
      H_hsdelta_DATA_rand.Fill(evt.hsdelta)
      H_hsxptar_DATA_rand.Fill(evt.hsxptar)
      H_hsyptar_DATA_rand.Fill(evt.hsyptar)
      
      H_pmiss_DATA_rand.Fill(evt.pmiss)
      H_emiss_DATA_rand.Fill(evt.emiss)
      #H_emiss_DATA_rand.Fill(evt.emiss_nuc)
      H_pmx_DATA_rand.Fill(evt.pmx)
      H_pmy_DATA_rand.Fill(evt.pmy)
      H_pmz_DATA_rand.Fill(evt.pmz)
      H_Q2_DATA_rand.Fill(evt.Q2)
      H_W_DATA_rand.Fill(evt.W)
      H_epsilon_DATA_rand.Fill(evt.epsilon)
      H_MMp2_DATA_rand.Fill(pow(evt.emiss, 2) - pow(evt.pmiss, 2))  
      #H_MMp2_DATA_rand.Fill(evt.MMp)  
      #H_MMp2_DATA_rand.Fill(evt.Mrecoil)
      '''

      H_cal_etottracknorm_DATA.Fill(evt.H_cal_etottracknorm)
      H_cer_npeSum_DATA.Fill(evt.H_cer_npeSum)

      P_cal_etottracknorm_DATA.Fill(evt.P_cal_etottracknorm)
      P_hgcer_npeSum_DATA.Fill(evt.P_hgcer_npeSum)
      P_aero_npeSum_DATA.Fill(evt.P_aero_npeSum)
      
      H_cal_etottracknorm_vs_H_cer_npeSum_DATA.Fill(evt.H_cal_etottracknorm,evt.H_cer_npeSum)
      P_cal_etottracknorm_vs_P_hgcer_npeSum_DATA.Fill(evt.P_cal_etottracknorm,evt.P_hgcer_npeSum)
      P_cal_etottracknorm_vs_P_aero_npeSum_DATA.Fill(evt.P_cal_etottracknorm,evt.P_aero_npeSum)
      P_hgcer_npeSum_vs_P_aero_npeSum_DATA.Fill(evt.P_hgcer_npeSum,evt.P_aero_npeSum)

      ibin+=1

ibin = 1      
for evt in TBRANCH_DATA_nocut:

  H_ct_ep_DATA_nocut.Fill(evt.CTime_epCoinTime_ROC1)

  H_pbeta_DATA_nocut.Fill(evt.P_gtr_beta)
  H_hbeta_DATA_nocut.Fill(evt.H_gtr_beta)
  
  CoinTime_vs_pbeta_DATA_nocut.Fill(evt.CTime_epCoinTime_ROC1, evt.P_gtr_beta)
  CoinTime_vs_hbeta_DATA_nocut.Fill(evt.CTime_epCoinTime_ROC1, evt.H_gtr_beta)
  
  H_ssxfp_DATA_nocut.Fill(evt.ssxfp)
  H_ssyfp_DATA_nocut.Fill(evt.ssyfp)
  H_ssxpfp_DATA_nocut.Fill(evt.ssxpfp)
  H_ssypfp_DATA_nocut.Fill(evt.ssypfp)
  H_ssdelta_DATA_nocut.Fill(evt.ssdelta)
  H_ssxptar_DATA_nocut.Fill(evt.ssxptar)
  H_ssyptar_DATA_nocut.Fill(evt.ssyptar)

  H_hsxfp_DATA_nocut.Fill(evt.hsxfp)
  H_hsyfp_DATA_nocut.Fill(evt.hsyfp)
  H_hsxpfp_DATA_nocut.Fill(evt.hsxpfp)
  H_hsypfp_DATA_nocut.Fill(evt.hsypfp)
  H_hsdelta_DATA_nocut.Fill(evt.hsdelta)
  H_hsxptar_DATA_nocut.Fill(evt.hsxptar)
  H_hsyptar_DATA_nocut.Fill(evt.hsyptar)

  H_ph_q_DATA_nocut.Fill(evt.ph_q)
  H_th_q_DATA_nocut.Fill(evt.th_q)
  H_ph_recoil_DATA_nocut.Fill(evt.ph_recoil)
  H_th_recoil_DATA_nocut.Fill(evt.th_recoil)

  H_pmiss_DATA_nocut.Fill(evt.pmiss)
  H_emiss_DATA_nocut.Fill(evt.emiss)
  #H_emiss_DATA_nocut.Fill(evt.emiss_nuc)
  H_pmx_DATA_nocut.Fill(evt.pmx)
  H_pmy_DATA_nocut.Fill(evt.pmy)
  H_pmz_DATA_nocut.Fill(evt.pmz)
  H_Q2_DATA_nocut.Fill(evt.Q2)
  H_W_DATA_nocut.Fill(evt.W)
  H_epsilon_DATA_nocut.Fill(evt.epsilon)
  H_MMp2_DATA_nocut.Fill(pow(evt.emiss, 2) - pow(evt.pmiss, 2))  
  #H_MMp2_DATA_nocut.Fill(pow(evt.MMp, 2))  
  #H_MMp2_DATA_nocut.Fill(evt.Mrecoil)

  H_cal_etottracknorm_DATA_nocut.Fill(evt.H_cal_etottracknorm)
  H_cer_npeSum_DATA_nocut.Fill(evt.H_cer_npeSum)

  P_cal_etottracknorm_DATA_nocut.Fill(evt.P_cal_etottracknorm)
  P_hgcer_npeSum_DATA_nocut.Fill(evt.P_hgcer_npeSum)
  P_aero_npeSum_DATA_nocut.Fill(evt.P_aero_npeSum)
  ###################################################################################################################################################

  bpm_tar_x_DATA_nocut.Fill(evt.bpm_tar_x)
  bpm_tar_y_DATA_nocut.Fill(evt.bpm_tar_y)      
  
  ###################################################################################################################################################
  ibin+= 1

ibin = 1  
for evt in TBRANCH_DATA_nopid:

  #CUTs Definations 
  SHMS_FixCut = (evt.P_hod_goodstarttime == 1) & (evt.P_dc_InsideDipoleExit == 1) 
  SHMS_Acceptance = (evt.ssdelta>=-10.0) & (evt.ssdelta<=20.0) & (evt.ssxptar>=-0.06) & (evt.ssxptar<=0.06) & (evt.ssyptar>=-0.04) & (evt.ssyptar<=0.04)

  HMS_FixCut = (evt.H_hod_goodstarttime == 1) & (evt.H_dc_InsideDipoleExit == 1)
  HMS_Acceptance = (evt.hsdelta>=-8.0) & (evt.hsdelta<=8.0) & (evt.hsxptar>=-0.08) & (evt.hsxptar<=0.08) & (evt.hsyptar>=-0.045) & (evt.hsyptar<=0.045)       

  #........................................  
  
  if(HMS_FixCut & HMS_Acceptance & SHMS_FixCut & SHMS_Acceptance):

      H_ct_ep_DATA_nopid.Fill(evt.CTime_epCoinTime_ROC1)

      H_ssxfp_DATA_nopid.Fill(evt.ssxfp)
      H_ssyfp_DATA_nopid.Fill(evt.ssyfp)
      H_ssxpfp_DATA_nopid.Fill(evt.ssxpfp)
      H_ssypfp_DATA_nopid.Fill(evt.ssypfp)
      H_ssdelta_DATA_nopid.Fill(evt.ssdelta)
      H_ssxptar_DATA_nopid.Fill(evt.ssxptar)
      H_ssyptar_DATA_nopid.Fill(evt.ssyptar)

      H_hsxfp_DATA_nopid.Fill(evt.hsxfp)
      H_hsyfp_DATA_nopid.Fill(evt.hsyfp)
      H_hsxpfp_DATA_nopid.Fill(evt.hsxpfp)
      H_hsypfp_DATA_nopid.Fill(evt.hsypfp)
      H_hsdelta_DATA_nopid.Fill(evt.hsdelta)
      H_hsxptar_DATA_nopid.Fill(evt.hsxptar)
      H_hsyptar_DATA_nopid.Fill(evt.hsyptar)

      H_ph_q_DATA_nopid.Fill(evt.ph_q)
      H_th_q_DATA_nopid.Fill(evt.th_q)
      H_ph_recoil_DATA_nopid.Fill(evt.ph_recoil)
      H_th_recoil_DATA_nopid.Fill(evt.th_recoil)

      H_pmiss_DATA_nopid.Fill(evt.pmiss)
      H_emiss_DATA_nopid.Fill(evt.emiss)
      #H_emiss_DATA_nopid.Fill(evt.emiss_nuc)
      H_pmx_DATA_nopid.Fill(evt.pmx)
      H_pmy_DATA_nopid.Fill(evt.pmy)
      H_pmz_DATA_nopid.Fill(evt.pmz)
      H_Q2_DATA_nopid.Fill(evt.Q2)
      H_W_DATA_nopid.Fill(evt.W)
      H_epsilon_DATA_nopid.Fill(evt.epsilon)
      H_MMp2_DATA_nopid.Fill(pow(evt.emiss, 2) - pow(evt.pmiss, 2))  
      #H_MMp2_DATA_nopid.Fill(pow(evt.MMp, 2))  
      #H_MMp2_DATA_nopid.Fill(evt.Mrecoil)

      H_cal_etottracknorm_DATA_nopid.Fill(evt.H_cal_etottracknorm)
      H_cer_npeSum_DATA_nopid.Fill(evt.H_cer_npeSum)

      P_cal_etottracknorm_DATA_nopid.Fill(evt.P_cal_etottracknorm)
      P_hgcer_npeSum_DATA_nopid.Fill(evt.P_hgcer_npeSum)
      P_aero_npeSum_DATA_nopid.Fill(evt.P_aero_npeSum)
      ###################################################################################################################################################

      bpm_tar_x_DATA_nopid.Fill(evt.bpm_tar_x)
      bpm_tar_y_DATA_nopid.Fill(evt.bpm_tar_y)      
      
      ###################################################################################################################################################
      ibin += 1

ibin = 1      
for evt in TBRANCH_DUMMY:

  #......... Define Cuts.................

  #CUTs Definations 
  SHMS_FixCut = (evt.P_hod_goodstarttime == 1) & (evt.P_dc_InsideDipoleExit == 1) 
  SHMS_Acceptance = (evt.ssdelta>=-10.0) & (evt.ssdelta<=20.0) & (evt.ssxptar>=-0.06) & (evt.ssxptar<=0.06) & (evt.ssyptar>=-0.04) & (evt.ssyptar<=0.04)

  HMS_FixCut = (evt.H_hod_goodstarttime == 1) & (evt.H_dc_InsideDipoleExit == 1)
  HMS_Acceptance = (evt.hsdelta>=-8.0) & (evt.hsdelta<=8.0) & (evt.hsxptar>=-0.08) & (evt.hsxptar<=0.08) & (evt.hsyptar>=-0.045) & (evt.hsyptar<=0.045)       
  
  #........................................
  
  if(HMS_FixCut & HMS_Acceptance & SHMS_FixCut & SHMS_Acceptance):

      H_ct_ep_DUMMY.Fill(evt.CTime_epCoinTime_ROC1)
      
      H_ssxfp_DUMMY.Fill(evt.ssxfp)
      H_ssyfp_DUMMY.Fill(evt.ssyfp)
      H_ssxpfp_DUMMY.Fill(evt.ssxpfp)
      H_ssypfp_DUMMY.Fill(evt.ssypfp)
      H_ssdelta_DUMMY.Fill(evt.ssdelta)
      H_ssxptar_DUMMY.Fill(evt.ssxptar)
      H_ssyptar_DUMMY.Fill(evt.ssyptar)
      
      H_hsxfp_DUMMY.Fill(evt.hsxfp)
      H_hsyfp_DUMMY.Fill(evt.hsyfp)
      H_hsxpfp_DUMMY.Fill(evt.hsxpfp)
      H_hsypfp_DUMMY.Fill(evt.hsypfp)
      H_hsdelta_DUMMY.Fill(evt.hsdelta)
      H_hsxptar_DUMMY.Fill(evt.hsxptar)
      H_hsyptar_DUMMY.Fill(evt.hsyptar)

      H_ph_q_DUMMY.Fill(evt.ph_q)
      H_th_q_DUMMY.Fill(evt.th_q)
      H_ph_recoil_DUMMY.Fill(evt.ph_recoil)
      H_th_recoil_DUMMY.Fill(evt.th_recoil)
            
      H_pmiss_DUMMY.Fill(evt.pmiss)
      H_emiss_DUMMY.Fill(evt.emiss)
      #H_emiss_DUMMY.Fill(evt.emiss_nuc)
      H_pmx_DUMMY.Fill(evt.pmx)
      H_pmy_DUMMY.Fill(evt.pmy)
      H_pmz_DUMMY.Fill(evt.pmz)
      H_Q2_DUMMY.Fill(evt.Q2)
      H_W_DUMMY.Fill(evt.W)
      H_epsilon_DUMMY.Fill(evt.epsilon)
      H_MMp2_DUMMY.Fill(pow(evt.emiss, 2) - pow(evt.pmiss, 2))  
      #H_MMp2_DUMMY.Fill(evt.MMp)  
      #H_MMp2_DUMMY.Fill(evt.Mrecoil)

      '''
      # Random subtraction
      
      H_ssxfp_DUMMY_rand.Fill(evt.ssxfp)
      H_ssyfp_DUMMY_rand.Fill(evt.ssyfp)
      H_ssxpfp_DUMMY_rand.Fill(evt.ssxpfp)
      H_ssypfp_DUMMY_rand.Fill(evt.ssypfp)
      H_ssdelta_DUMMY_rand.Fill(evt.ssdelta)
      H_ssxptar_DUMMY_rand.Fill(evt.ssxptar)
      H_ssyptar_DUMMY_rand.Fill(evt.ssyptar)
      
      H_hsxfp_DUMMY_rand.Fill(evt.hsxfp)
      H_hsyfp_DUMMY_rand.Fill(evt.hsyfp)
      H_hsxpfp_DUMMY_rand.Fill(evt.hsxpfp)
      H_hsypfp_DUMMY_rand.Fill(evt.hsypfp)
      H_hsdelta_DUMMY_rand.Fill(evt.hsdelta)
      H_hsxptar_DUMMY_rand.Fill(evt.hsxptar)
      H_hsyptar_DUMMY_rand.Fill(evt.hsyptar)
      
      H_pmiss_DUMMY_rand.Fill(evt.pmiss)
      H_emiss_DUMMY_rand.Fill(evt.emiss)
      #H_emiss_DUMMY_rand.Fill(evt.emiss_nuc)
      H_pmx_DUMMY_rand.Fill(evt.pmx)
      H_pmy_DUMMY_rand.Fill(evt.pmy)
      H_pmz_DUMMY_rand.Fill(evt.pmz)
      H_Q2_DUMMY_rand.Fill(evt.Q2)
      H_W_DUMMY_rand.Fill(evt.W)
      H_epsilon_DUMMY_rand.Fill(evt.epsilon)
      H_MMp2_DUMMY_rand.Fill(pow(evt.emiss, 2) - pow(evt.pmiss, 2))  
      #H_MMp2_DUMMY_rand.Fill(evt.MMp)  
      #H_MMp2_DUMMY_rand.Fill(evt.Mrecoil)
      '''
      
      ###################################################################################################################################################
      ibin += 1
      
ibin = 1
for evt in TBRANCH_DUMMY_nocut:

  H_ct_ep_DUMMY_nocut.Fill(evt.CTime_epCoinTime_ROC1)

  H_ssxfp_DUMMY_nocut.Fill(evt.ssxfp)
  H_ssyfp_DUMMY_nocut.Fill(evt.ssyfp)
  H_ssxpfp_DUMMY_nocut.Fill(evt.ssxpfp)
  H_ssypfp_DUMMY_nocut.Fill(evt.ssypfp)
  H_ssdelta_DUMMY_nocut.Fill(evt.ssdelta)
  H_ssxptar_DUMMY_nocut.Fill(evt.ssxptar)
  H_ssyptar_DUMMY_nocut.Fill(evt.ssyptar)

  H_hsxfp_DUMMY_nocut.Fill(evt.hsxfp)
  H_hsyfp_DUMMY_nocut.Fill(evt.hsyfp)
  H_hsxpfp_DUMMY_nocut.Fill(evt.hsxpfp)
  H_hsypfp_DUMMY_nocut.Fill(evt.hsypfp)
  H_hsdelta_DUMMY_nocut.Fill(evt.hsdelta)
  H_hsxptar_DUMMY_nocut.Fill(evt.hsxptar)
  H_hsyptar_DUMMY_nocut.Fill(evt.hsyptar)

  H_ph_q_DUMMY_nocut.Fill(evt.ph_q)
  H_th_q_DUMMY_nocut.Fill(evt.th_q)
  H_ph_recoil_DUMMY_nocut.Fill(evt.ph_recoil)
  H_th_recoil_DUMMY_nocut.Fill(evt.th_recoil)

  H_pmiss_DUMMY_nocut.Fill(evt.pmiss)
  H_emiss_DUMMY_nocut.Fill(evt.emiss)
  #H_emiss_DUMMY_nocut.Fill(evt.emiss_nuc)
  H_pmx_DUMMY_nocut.Fill(evt.pmx)
  H_pmy_DUMMY_nocut.Fill(evt.pmy)
  H_pmz_DUMMY_nocut.Fill(evt.pmz)
  H_Q2_DUMMY_nocut.Fill(evt.Q2)
  H_W_DUMMY_nocut.Fill(evt.W)
  H_epsilon_DUMMY_nocut.Fill(evt.epsilon)
  H_MMp2_DUMMY_nocut.Fill(pow(evt.emiss, 2) - pow(evt.pmiss, 2))  
  #H_MMp2_DUMMY_nocut.Fill(evt.MMp)  
  #H_MMp2_DUMMY_nocut.Fill(evt.Mrecoil)

  ###################################################################################################################################################
  ibin += 1

ibin = 1  
for evt in TBRANCH_DUMMY_nopid:

  #......... Define Cuts.................

  #CUTs Definations 
  SHMS_FixCut = (evt.P_hod_goodstarttime == 1) & (evt.P_dc_InsideDipoleExit == 1) 
  SHMS_Acceptance = (evt.ssdelta>=-10.0) & (evt.ssdelta<=20.0) & (evt.ssxptar>=-0.06) & (evt.ssxptar<=0.06) & (evt.ssyptar>=-0.04) & (evt.ssyptar<=0.04)

  HMS_FixCut = (evt.H_hod_goodstarttime == 1) & (evt.H_dc_InsideDipoleExit == 1)
  HMS_Acceptance = (evt.hsdelta>=-8.0) & (evt.hsdelta<=8.0) & (evt.hsxptar>=-0.08) & (evt.hsxptar<=0.08) & (evt.hsyptar>=-0.045) & (evt.hsyptar<=0.045)       
  
  #........................................
  
  if(HMS_FixCut & HMS_Acceptance & SHMS_FixCut & SHMS_Acceptance):

      H_ct_ep_DUMMY_nopid.Fill(evt.CTime_epCoinTime_ROC1)

      H_ssxfp_DUMMY_nopid.Fill(evt.ssxfp)
      H_ssyfp_DUMMY_nopid.Fill(evt.ssyfp)
      H_ssxpfp_DUMMY_nopid.Fill(evt.ssxpfp)
      H_ssypfp_DUMMY_nopid.Fill(evt.ssypfp)
      H_ssdelta_DUMMY_nopid.Fill(evt.ssdelta)
      H_ssxptar_DUMMY_nopid.Fill(evt.ssxptar)
      H_ssyptar_DUMMY_nopid.Fill(evt.ssyptar)

      H_hsxfp_DUMMY_nopid.Fill(evt.hsxfp)
      H_hsyfp_DUMMY_nopid.Fill(evt.hsyfp)
      H_hsxpfp_DUMMY_nopid.Fill(evt.hsxpfp)
      H_hsypfp_DUMMY_nopid.Fill(evt.hsypfp)
      H_hsdelta_DUMMY_nopid.Fill(evt.hsdelta)
      H_hsxptar_DUMMY_nopid.Fill(evt.hsxptar)
      H_hsyptar_DUMMY_nopid.Fill(evt.hsyptar)

      H_ph_q_DUMMY_nopid.Fill(evt.ph_q)
      H_th_q_DUMMY_nopid.Fill(evt.th_q)
      H_ph_recoil_DUMMY_nopid.Fill(evt.ph_recoil)
      H_th_recoil_DUMMY_nopid.Fill(evt.th_recoil)

      H_pmiss_DUMMY_nopid.Fill(evt.pmiss)
      H_emiss_DUMMY_nopid.Fill(evt.emiss)
      #H_emiss_DUMMY_nopid.Fill(evt.emiss_nuc)
      H_pmx_DUMMY_nopid.Fill(evt.pmx)
      H_pmy_DUMMY_nopid.Fill(evt.pmy)
      H_pmz_DUMMY_nopid.Fill(evt.pmz)
      H_Q2_DUMMY_nopid.Fill(evt.Q2)
      H_W_DUMMY_nopid.Fill(evt.W)
      H_epsilon_DUMMY_nopid.Fill(evt.epsilon)
      H_MMp2_DUMMY_nopid.Fill(pow(evt.emiss, 2) - pow(evt.pmiss, 2))  
      #H_MMp2_DUMMY_nopid.Fill(evt.MMp)  
      #H_MMp2_DUMMY_nopid.Fill(evt.Mrecoil)
      ###################################################################################################################################################
      ibin += 1

################################################################################################################################################
# Normalize simc by normfactor/nevents
# Normalize data by effective charge

normfac_data = 1/(data_charge)
dummy_target_corr = 4.8579
normfac_dummy = 1/(dummy_charge*dummy_target_corr)
normfac_simc = (simc_normfactor)/(simc_nevents)

num_evts_data = int(H_W_DATA.Integral()) - int(H_W_DUMMY.Integral())
yield_data = num_evts_data*normfac_data
num_evts_simc = int(H_W_SIMC.Integral())
yield_simc = num_evts_simc*normfac_simc
rel_yield = yield_data/yield_simc
      
################################################################################################################################################

H_ssxfp_SIMC.Scale(normfac_simc)
H_ssyfp_SIMC.Scale(normfac_simc)
H_ssxpfp_SIMC.Scale(normfac_simc)
H_ssypfp_SIMC.Scale(normfac_simc)
H_hsxfp_SIMC.Scale(normfac_simc)
H_hsyfp_SIMC.Scale(normfac_simc)
H_hsxpfp_SIMC.Scale(normfac_simc)
H_hsypfp_SIMC.Scale(normfac_simc)
H_ssdelta_SIMC.Scale(normfac_simc)
H_hsdelta_SIMC.Scale(normfac_simc)
H_ssxptar_SIMC.Scale(normfac_simc)
H_ssyptar_SIMC.Scale(normfac_simc)
H_hsxptar_SIMC.Scale(normfac_simc)
H_hsyptar_SIMC.Scale(normfac_simc)
H_ph_q_SIMC.Scale(normfac_simc)
H_th_q_SIMC.Scale(normfac_simc)
H_pmiss_SIMC.Scale(normfac_simc)
H_emiss_SIMC.Scale(normfac_simc)
H_pmx_SIMC.Scale(normfac_simc)
H_pmy_SIMC.Scale(normfac_simc)
H_pmz_SIMC.Scale(normfac_simc)
H_Q2_SIMC.Scale(normfac_simc)
H_W_SIMC.Scale(normfac_simc)
H_epsilon_SIMC.Scale(normfac_simc)
H_MMp2_SIMC.Scale(normfac_simc)

H_ssxfp_DUMMY.Scale(normfac_dummy)
H_ssyfp_DUMMY.Scale(normfac_dummy)
H_ssxpfp_DUMMY.Scale(normfac_dummy)
H_ssypfp_DUMMY.Scale(normfac_dummy)
H_hsxfp_DUMMY.Scale(normfac_dummy)
H_hsyfp_DUMMY.Scale(normfac_dummy)
H_hsxpfp_DUMMY.Scale(normfac_dummy)
H_hsypfp_DUMMY.Scale(normfac_dummy)
H_ssxptar_DUMMY.Scale(normfac_dummy)
H_ssyptar_DUMMY.Scale(normfac_dummy)
H_hsxptar_DUMMY.Scale(normfac_dummy)
H_hsyptar_DUMMY.Scale(normfac_dummy)
H_ssdelta_DUMMY.Scale(normfac_dummy)
H_hsdelta_DUMMY.Scale(normfac_dummy)
H_Q2_DUMMY.Scale(normfac_dummy)
H_epsilon_DUMMY.Scale(normfac_dummy)
H_MMp2_DUMMY.Scale(normfac_dummy)
H_ph_q_DUMMY.Scale(normfac_dummy)
H_th_q_DUMMY.Scale(normfac_dummy)
H_ph_recoil_DUMMY.Scale(normfac_dummy)
H_th_recoil_DUMMY.Scale(normfac_dummy)
H_pmiss_DUMMY.Scale(normfac_dummy)
H_emiss_DUMMY.Scale(normfac_dummy)
H_pmx_DUMMY.Scale(normfac_dummy)
H_pmy_DUMMY.Scale(normfac_dummy)
H_pmz_DUMMY.Scale(normfac_dummy)
H_W_DUMMY.Scale(normfac_dummy)
H_ct_ep_DUMMY.Scale(normfac_dummy)

H_ssxfp_DUMMY_nocut.Scale(normfac_dummy)
H_ssxfp_DUMMY_nopid.Scale(normfac_dummy)
H_ssyfp_DUMMY_nocut.Scale(normfac_dummy)
H_ssyfp_DUMMY_nopid.Scale(normfac_dummy)
H_ssxpfp_DUMMY_nocut.Scale(normfac_dummy)
H_ssxpfp_DUMMY_nopid.Scale(normfac_dummy)
H_ssypfp_DUMMY_nocut.Scale(normfac_dummy)
H_ssypfp_DUMMY_nopid.Scale(normfac_dummy)
H_hsxfp_DUMMY_nocut.Scale(normfac_dummy)
H_hsxfp_DUMMY_nopid.Scale(normfac_dummy)
H_hsyfp_DUMMY_nocut.Scale(normfac_dummy)
H_hsyfp_DUMMY_nopid.Scale(normfac_dummy)
H_hsxpfp_DUMMY_nocut.Scale(normfac_dummy)
H_hsxpfp_DUMMY_nopid.Scale(normfac_dummy)
H_hsypfp_DUMMY_nocut.Scale(normfac_dummy)
H_hsypfp_DUMMY_nopid.Scale(normfac_dummy)
H_ssxptar_DUMMY_nocut.Scale(normfac_dummy)
H_ssxptar_DUMMY_nopid.Scale(normfac_dummy)
H_ssyptar_DUMMY_nocut.Scale(normfac_dummy)
H_ssyptar_DUMMY_nopid.Scale(normfac_dummy)
H_hsxptar_DUMMY_nocut.Scale(normfac_dummy)
H_hsxptar_DUMMY_nopid.Scale(normfac_dummy)
H_hsyptar_DUMMY_nocut.Scale(normfac_dummy)
H_hsyptar_DUMMY_nopid.Scale(normfac_dummy)
H_ssdelta_DUMMY_nocut.Scale(normfac_dummy)
H_ssdelta_DUMMY_nopid.Scale(normfac_dummy)
H_hsdelta_DUMMY_nocut.Scale(normfac_dummy)
H_hsdelta_DUMMY_nopid.Scale(normfac_dummy)
H_Q2_DUMMY_nocut.Scale(normfac_dummy)
H_Q2_DUMMY_nopid.Scale(normfac_dummy)
H_epsilon_DUMMY_nocut.Scale(normfac_dummy)
H_epsilon_DUMMY_nopid.Scale(normfac_dummy)
H_MMp2_DUMMY_nocut.Scale(normfac_dummy)
H_MMp2_DUMMY_nopid.Scale(normfac_dummy)
H_ph_q_DUMMY_nocut.Scale(normfac_dummy)
H_ph_q_DUMMY_nopid.Scale(normfac_dummy)
H_th_q_DUMMY_nocut.Scale(normfac_dummy)
H_th_q_DUMMY_nopid.Scale(normfac_dummy)
H_ph_recoil_DUMMY_nocut.Scale(normfac_dummy)
H_ph_recoil_DUMMY_nopid.Scale(normfac_dummy)
H_th_recoil_DUMMY_nocut.Scale(normfac_dummy)
H_th_recoil_DUMMY_nopid.Scale(normfac_dummy)
H_pmiss_DUMMY_nocut.Scale(normfac_dummy)
H_pmiss_DUMMY_nopid.Scale(normfac_dummy)
H_emiss_DUMMY_nocut.Scale(normfac_dummy)
H_emiss_DUMMY_nopid.Scale(normfac_dummy)
H_pmx_DUMMY_nocut.Scale(normfac_dummy)
H_pmx_DUMMY_nopid.Scale(normfac_dummy)
H_pmy_DUMMY_nocut.Scale(normfac_dummy)
H_pmy_DUMMY_nopid.Scale(normfac_dummy)
H_pmz_DUMMY_nocut.Scale(normfac_dummy)
H_pmz_DUMMY_nopid.Scale(normfac_dummy)
H_W_DUMMY_nocut.Scale(normfac_dummy)
H_W_DUMMY_nopid.Scale(normfac_dummy)
H_ct_ep_DUMMY_nocut.Scale(normfac_dummy)
H_ct_ep_DUMMY_nopid.Scale(normfac_dummy)

H_ssxfp_DATA.Scale(normfac_data)
H_ssyfp_DATA.Scale(normfac_data)
H_ssxpfp_DATA.Scale(normfac_data)
H_ssypfp_DATA.Scale(normfac_data)
H_hsxfp_DATA.Scale(normfac_data)
H_hsyfp_DATA.Scale(normfac_data)
H_hsxpfp_DATA.Scale(normfac_data)
H_hsypfp_DATA.Scale(normfac_data)
H_ssxptar_DATA.Scale(normfac_data)
H_ssyptar_DATA.Scale(normfac_data)
H_hsxptar_DATA.Scale(normfac_data)
H_hsyptar_DATA.Scale(normfac_data)
H_ssdelta_DATA.Scale(normfac_data)
H_hsdelta_DATA.Scale(normfac_data)
H_Q2_DATA.Scale(normfac_data)
H_epsilon_DATA.Scale(normfac_data)
H_MMp2_DATA.Scale(normfac_data)
H_ph_q_DATA.Scale(normfac_data)
H_th_q_DATA.Scale(normfac_data)
H_ph_recoil_DATA.Scale(normfac_data)
H_th_recoil_DATA.Scale(normfac_data)
H_pmiss_DATA.Scale(normfac_data)
H_emiss_DATA.Scale(normfac_data)
H_pmx_DATA.Scale(normfac_data)
H_pmy_DATA.Scale(normfac_data)
H_pmz_DATA.Scale(normfac_data)
H_W_DATA.Scale(normfac_data)
H_ct_ep_DATA.Scale(normfac_data)
bpm_tar_x_DATA.Scale(normfac_data)
bpm_tar_y_DATA.Scale(normfac_data)


H_ssxfp_DATA_nocut.Scale(normfac_data)
H_ssxfp_DATA_nopid.Scale(normfac_data)
H_ssyfp_DATA_nocut.Scale(normfac_data)
H_ssyfp_DATA_nopid.Scale(normfac_data)
H_ssxpfp_DATA_nocut.Scale(normfac_data)
H_ssxpfp_DATA_nopid.Scale(normfac_data)
H_ssypfp_DATA_nocut.Scale(normfac_data)
H_ssypfp_DATA_nopid.Scale(normfac_data)
H_hsxfp_DATA_nocut.Scale(normfac_data)
H_hsxfp_DATA_nopid.Scale(normfac_data)
H_hsyfp_DATA_nocut.Scale(normfac_data)
H_hsyfp_DATA_nopid.Scale(normfac_data)
H_hsxpfp_DATA_nocut.Scale(normfac_data)
H_hsxpfp_DATA_nopid.Scale(normfac_data)
H_hsypfp_DATA_nocut.Scale(normfac_data)
H_hsypfp_DATA_nopid.Scale(normfac_data)
H_ssxptar_DATA_nocut.Scale(normfac_data)
H_ssxptar_DATA_nopid.Scale(normfac_data)
H_ssyptar_DATA_nocut.Scale(normfac_data)
H_ssyptar_DATA_nopid.Scale(normfac_data)
H_hsxptar_DATA_nocut.Scale(normfac_data)
H_hsxptar_DATA_nopid.Scale(normfac_data)
H_hsyptar_DATA_nocut.Scale(normfac_data)
H_hsyptar_DATA_nopid.Scale(normfac_data)
H_ssdelta_DATA_nocut.Scale(normfac_data)
H_ssdelta_DATA_nopid.Scale(normfac_data)
H_hsdelta_DATA_nocut.Scale(normfac_data)
H_hsdelta_DATA_nopid.Scale(normfac_data)
H_Q2_DATA_nocut.Scale(normfac_data)
H_Q2_DATA_nopid.Scale(normfac_data)
H_epsilon_DATA_nocut.Scale(normfac_data)
H_epsilon_DATA_nopid.Scale(normfac_data)
H_MMp2_DATA_nocut.Scale(normfac_data)
H_MMp2_DATA_nopid.Scale(normfac_data)
H_ph_q_DATA_nocut.Scale(normfac_data)
H_ph_q_DATA_nopid.Scale(normfac_data)
H_th_q_DATA_nocut.Scale(normfac_data)
H_th_q_DATA_nopid.Scale(normfac_data)
H_ph_recoil_DATA_nocut.Scale(normfac_data)
H_ph_recoil_DATA_nopid.Scale(normfac_data)
H_th_recoil_DATA_nocut.Scale(normfac_data)
H_th_recoil_DATA_nopid.Scale(normfac_data)
H_pmiss_DATA_nocut.Scale(normfac_data)
H_pmiss_DATA_nopid.Scale(normfac_data)
H_emiss_DATA_nocut.Scale(normfac_data)
H_emiss_DATA_nopid.Scale(normfac_data)
H_pmx_DATA_nocut.Scale(normfac_data)
H_pmx_DATA_nopid.Scale(normfac_data)
H_pmy_DATA_nocut.Scale(normfac_data)
H_pmy_DATA_nopid.Scale(normfac_data)
H_pmz_DATA_nocut.Scale(normfac_data)
H_pmz_DATA_nopid.Scale(normfac_data)
H_W_DATA_nocut.Scale(normfac_data)
H_W_DATA_nopid.Scale(normfac_data)
H_ct_ep_DATA_nocut.Scale(normfac_data)
H_ct_ep_DATA_nopid.Scale(normfac_data)
bpm_tar_x_DATA_nocut.Scale(normfac_data)
bpm_tar_y_DATA_nocut.Scale(normfac_data)
bpm_tar_x_DATA_nopid.Scale(normfac_data)
bpm_tar_y_DATA_nopid.Scale(normfac_data)

'''
# Data Random subtraction
H_ssxfp_DATA_rand.Scale(normfac_data/nWindows)
H_ssyfp_DATA_rand.Scale(normfac_data/nWindows)
H_ssxpfp_DATA_rand.Scale(normfac_data/nWindows)
H_ssypfp_DATA_rand.Scale(normfac_data/nWindows)
H_hsxfp_DATA_rand.Scale(normfac_data/nWindows)
H_hsyfp_DATA_rand.Scale(normfac_data/nWindows)
H_hsxpfp_DATA_rand.Scale(normfac_data/nWindows)
H_hsypfp_DATA_rand.Scale(normfac_data/nWindows)
H_ssxptar_DATA_rand.Scale(normfac_data/nWindows)
H_ssyptar_DATA_rand.Scale(normfac_data/nWindows)
H_hsxptar_DATA_rand.Scale(normfac_data/nWindows)
H_hsyptar_DATA_rand.Scale(normfac_data/nWindows)
H_ssdelta_DATA_rand.Scale(normfac_data/nWindows)
H_hsdelta_DATA_rand.Scale(normfac_data/nWindows)
H_Q2_DATA_rand.Scale(normfac_data/nWindows)
H_epsilon_DATA_rand.Scale(normfac_data/nWindows)
H_MMp2_DATA_rand.Scale(normfac_data/nWindows)
H_pmiss_DATA_rand.Scale(normfac_data/nWindows)
H_emiss_DATA_rand.Scale(normfac_data/nWindows)
H_pmx_DATA_rand.Scale(normfac_data/nWindows)
H_pmy_DATA_rand.Scale(normfac_data/nWindows)
H_pmz_DATA_rand.Scale(normfac_data/nWindows)
H_W_DATA_rand.Scale(normfac_data/nWindows)
#H_ct_ep_DATA_rand.Scale(normfac_data/nWindows)

# Dummy Random subtraction
H_ssxfp_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_ssyfp_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_ssxpfp_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_ssypfp_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_hsxfp_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_hsyfp_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_hsxpfp_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_hsypfp_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_ssxptar_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_ssyptar_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_hsxptar_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_hsyptar_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_ssdelta_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_hsdelta_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_Q2_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_epsilon_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_MMp2_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_pmiss_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_emiss_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_pmx_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_pmy_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_pmz_DUMMY_rand.Scale(normfac_dummy/nWindows)
H_W_DUMMY_rand.Scale(normfac_dummy/nWindows)
#H_ct_ep_DUMMY_rand.Scale(normfac_dummy/nWindows)

###

# Data Random subtraction
H_ssxfp_DATA.Add(H_ssxfp_DATA_rand,-1)
H_ssyfp_DATA.Add(H_ssyfp_DATA_rand,-1)
H_ssxpfp_DATA.Add(H_ssxpfp_DATA_rand,-1)
H_ssypfp_DATA.Add(H_ssypfp_DATA_rand,-1)
H_hsxfp_DATA.Add(H_hsxfp_DATA_rand,-1)
H_hsyfp_DATA.Add(H_hsyfp_DATA_rand,-1)
H_hsxpfp_DATA.Add(H_hsxpfp_DATA_rand,-1)
H_hsypfp_DATA.Add(H_hsypfp_DATA_rand,-1)
H_ssxptar_DATA.Add(H_ssxptar_DATA_rand,-1)
H_ssyptar_DATA.Add(H_ssyptar_DATA_rand,-1)
H_hsxptar_DATA.Add(H_hsxptar_DATA_rand,-1)
H_hsyptar_DATA.Add(H_hsyptar_DATA_rand,-1)
H_ssdelta_DATA.Add(H_ssdelta_DATA_rand,-1)
H_hsdelta_DATA.Add(H_hsdelta_DATA_rand,-1)
H_Q2_DATA.Add(H_Q2_DATA_rand,-1)
H_epsilon_DATA.Add(H_epsilon_DATA_rand,-1)
H_MMp2_DATA.Add(H_MMp2_DATA_rand,-1)
H_pmiss_DATA.Add(H_pmiss_DATA_rand,-1)
H_emiss_DATA.Add(H_emiss_DATA_rand,-1)
H_pmx_DATA.Add(H_pmx_DATA_rand,-1)
H_pmy_DATA.Add(H_pmy_DATA_rand,-1)
H_pmz_DATA.Add(H_pmz_DATA_rand,-1)
H_W_DATA.Add(H_W_DATA_rand,-1)
#H_ct_ep_DATA.Add(H_ct_ep_DATA_rand,-1)

# Dummy Random subtraction
H_ssxfp_DUMMY.Add(H_ssxfp_DUMMY_rand,-1)
H_ssyfp_DUMMY.Add(H_ssyfp_DUMMY_rand,-1)
H_ssxpfp_DUMMY.Add(H_ssxpfp_DUMMY_rand,-1)
H_ssypfp_DUMMY.Add(H_ssypfp_DUMMY_rand,-1)
H_hsxfp_DUMMY.Add(H_hsxfp_DUMMY_rand,-1)
H_hsyfp_DUMMY.Add(H_hsyfp_DUMMY_rand,-1)
H_hsxpfp_DUMMY.Add(H_hsxpfp_DUMMY_rand,-1)
H_hsypfp_DUMMY.Add(H_hsypfp_DUMMY_rand,-1)
H_ssxptar_DUMMY.Add(H_ssxptar_DUMMY_rand,-1)
H_ssyptar_DUMMY.Add(H_ssyptar_DUMMY_rand,-1)
H_hsxptar_DUMMY.Add(H_hsxptar_DUMMY_rand,-1)
H_hsyptar_DUMMY.Add(H_hsyptar_DUMMY_rand,-1)
H_ssdelta_DUMMY.Add(H_ssdelta_DUMMY_rand,-1)
H_hsdelta_DUMMY.Add(H_hsdelta_DUMMY_rand,-1)
H_Q2_DUMMY.Add(H_Q2_DUMMY_rand,-1)
H_epsilon_DUMMY.Add(H_epsilon_DUMMY_rand,-1)
H_MMp2_DUMMY.Add(H_MMp2_DUMMY_rand,-1)
H_pmiss_DUMMY.Add(H_pmiss_DUMMY_rand,-1)
H_emiss_DUMMY.Add(H_emiss_DUMMY_rand,-1)
H_pmx_DUMMY.Add(H_pmx_DUMMY_rand,-1)
H_pmy_DUMMY.Add(H_pmy_DUMMY_rand,-1)
H_pmz_DUMMY.Add(H_pmz_DUMMY_rand,-1)
H_W_DUMMY.Add(H_W_DUMMY_rand,-1)
#H_ct_ep_DUMMY.Add(H_ct_ep_DUMMY_rand,-1)
'''

################################################################################################################################################

# Dummy Subtraction
H_ssxfp_DATA.Add(H_ssxfp_DUMMY,-1)
H_ssyfp_DATA.Add(H_ssyfp_DUMMY,-1)
H_ssxpfp_DATA.Add(H_ssxpfp_DUMMY,-1)
H_ssypfp_DATA.Add(H_ssypfp_DUMMY,-1)
H_hsxfp_DATA.Add(H_hsxfp_DUMMY,-1)
H_hsyfp_DATA.Add(H_hsyfp_DUMMY,-1)
H_hsxpfp_DATA.Add(H_hsxpfp_DUMMY,-1)
H_hsypfp_DATA.Add(H_hsypfp_DUMMY,-1)
H_ssxptar_DATA.Add(H_ssxptar_DUMMY,-1)
H_ssyptar_DATA.Add(H_ssyptar_DUMMY,-1)
H_hsxptar_DATA.Add(H_hsxptar_DUMMY,-1)
H_hsyptar_DATA.Add(H_hsyptar_DUMMY,-1)
H_ssdelta_DATA.Add(H_ssdelta_DUMMY,-1)
H_hsdelta_DATA.Add(H_hsdelta_DUMMY,-1)
H_Q2_DATA.Add(H_Q2_DUMMY,-1)
H_epsilon_DATA.Add(H_epsilon_DUMMY,-1)
H_MMp2_DATA.Add(H_MMp2_DUMMY,-1)
H_ph_q_DATA.Add(H_ph_q_DUMMY,-1)
H_th_q_DATA.Add(H_th_q_DUMMY,-1)
H_ph_recoil_DATA.Add(H_ph_recoil_DUMMY,-1)
H_th_recoil_DATA.Add(H_th_recoil_DUMMY,-1)
H_pmiss_DATA.Add(H_pmiss_DUMMY,-1)
H_emiss_DATA.Add(H_emiss_DUMMY,-1)
H_pmx_DATA.Add(H_pmx_DUMMY,-1)
H_pmy_DATA.Add(H_pmy_DUMMY,-1)
H_pmz_DATA.Add(H_pmz_DUMMY,-1)
H_W_DATA.Add(H_W_DUMMY,-1)
H_ct_ep_DATA.Add(H_ct_ep_DUMMY,-1)

H_ssxfp_DATA_nocut.Add(H_ssxfp_DUMMY_nocut,-1)
H_ssxfp_DATA_nopid.Add(H_ssxfp_DUMMY_nopid,-1)
H_ssyfp_DATA_nocut.Add(H_ssyfp_DUMMY_nocut,-1)
H_ssyfp_DATA_nopid.Add(H_ssyfp_DUMMY_nopid,-1)
H_ssxpfp_DATA_nocut.Add(H_ssxpfp_DUMMY_nocut,-1)
H_ssxpfp_DATA_nopid.Add(H_ssxpfp_DUMMY_nopid,-1)
H_ssypfp_DATA_nocut.Add(H_ssypfp_DUMMY_nocut,-1)
H_ssypfp_DATA_nopid.Add(H_ssypfp_DUMMY_nopid,-1)
H_hsxfp_DATA_nocut.Add(H_hsxfp_DUMMY_nocut,-1)
H_hsxfp_DATA_nopid.Add(H_hsxfp_DUMMY_nopid,-1)
H_hsyfp_DATA_nocut.Add(H_hsyfp_DUMMY_nocut,-1)
H_hsyfp_DATA_nopid.Add(H_hsyfp_DUMMY_nopid,-1)
H_hsxpfp_DATA_nocut.Add(H_hsxpfp_DUMMY_nocut,-1)
H_hsxpfp_DATA_nopid.Add(H_hsxpfp_DUMMY_nopid,-1)
H_hsypfp_DATA_nocut.Add(H_hsypfp_DUMMY_nocut,-1)
H_hsypfp_DATA_nopid.Add(H_hsypfp_DUMMY_nopid,-1)
H_ssxptar_DATA_nocut.Add(H_ssxptar_DUMMY_nocut,-1)
H_ssxptar_DATA_nopid.Add(H_ssxptar_DUMMY_nopid,-1)
H_ssyptar_DATA_nocut.Add(H_ssyptar_DUMMY_nocut,-1)
H_ssyptar_DATA_nopid.Add(H_ssyptar_DUMMY_nopid,-1)
H_hsxptar_DATA_nocut.Add(H_hsxptar_DUMMY_nocut,-1)
H_hsxptar_DATA_nopid.Add(H_hsxptar_DUMMY_nopid,-1)
H_hsyptar_DATA_nocut.Add(H_hsyptar_DUMMY_nocut,-1)
H_hsyptar_DATA_nopid.Add(H_hsyptar_DUMMY_nopid,-1)
H_ssdelta_DATA_nocut.Add(H_ssdelta_DUMMY_nocut,-1)
H_ssdelta_DATA_nopid.Add(H_ssdelta_DUMMY_nopid,-1)
H_hsdelta_DATA_nocut.Add(H_hsdelta_DUMMY_nocut,-1)
H_hsdelta_DATA_nopid.Add(H_hsdelta_DUMMY_nopid,-1)
H_Q2_DATA_nocut.Add(H_Q2_DUMMY_nocut,-1)
H_Q2_DATA_nopid.Add(H_Q2_DUMMY_nopid,-1)
H_epsilon_DATA_nocut.Add(H_epsilon_DUMMY_nocut,-1)
H_epsilon_DATA_nopid.Add(H_epsilon_DUMMY_nopid,-1)
H_MMp2_DATA_nocut.Add(H_MMp2_DUMMY_nocut,-1)
H_MMp2_DATA_nopid.Add(H_MMp2_DUMMY_nopid,-1)
H_ph_q_DATA_nocut.Add(H_ph_q_DUMMY_nocut,-1)
H_ph_q_DATA_nopid.Add(H_ph_q_DUMMY_nopid,-1)
H_th_q_DATA_nocut.Add(H_th_q_DUMMY_nocut,-1)
H_th_q_DATA_nopid.Add(H_th_q_DUMMY_nopid,-1)
H_ph_recoil_DATA_nocut.Add(H_ph_recoil_DUMMY_nocut,-1)
H_ph_recoil_DATA_nopid.Add(H_ph_recoil_DUMMY_nopid,-1)
H_th_recoil_DATA_nocut.Add(H_th_recoil_DUMMY_nocut,-1)
H_th_recoil_DATA_nopid.Add(H_th_recoil_DUMMY_nopid,-1)
H_pmiss_DATA_nocut.Add(H_pmiss_DUMMY_nocut,-1)
H_pmiss_DATA_nopid.Add(H_pmiss_DUMMY_nopid,-1)
H_emiss_DATA_nocut.Add(H_emiss_DUMMY_nocut,-1)
H_emiss_DATA_nopid.Add(H_emiss_DUMMY_nopid,-1)
H_pmx_DATA_nocut.Add(H_pmx_DUMMY_nocut,-1)
H_pmx_DATA_nopid.Add(H_pmx_DUMMY_nopid,-1)
H_pmy_DATA_nocut.Add(H_pmy_DUMMY_nocut,-1)
H_pmy_DATA_nopid.Add(H_pmy_DUMMY_nopid,-1)
H_pmz_DATA_nocut.Add(H_pmz_DUMMY_nocut,-1)
H_pmz_DATA_nopid.Add(H_pmz_DUMMY_nopid,-1)
H_W_DATA_nocut.Add(H_W_DUMMY_nocut,-1)
H_W_DATA_nopid.Add(H_W_DUMMY_nopid,-1)
H_ct_ep_DATA_nocut.Add(H_ct_ep_DUMMY_nocut,-1)
H_ct_ep_DATA_nopid.Add(H_ct_ep_DUMMY_nopid,-1)

################################################################################################################################################

# Define a function for fitting a Gaussian with dynamically determined FWHM range
def fit_gaussian(hist, x_min, x_max, dtype):

    print(hist.GetName(),dtype,"-"*25)
    
    # Find the corresponding bin numbers
    bin_min = hist.GetXaxis().FindBin(x_min)
    bin_max = hist.GetXaxis().FindBin(x_max)
    
    # Find the maximum value within the specified range
    max_bin = bin_min
    max_value = hist.GetBinContent(max_bin)
    for i in range(bin_min, bin_max):
        if hist.GetBinContent(i) > max_value:
            max_bin = i
            max_value = hist.GetBinContent(i)

    # Print the results
    print("max_bin", max_bin)
    print("max_value", max_value)
    print("bin_center",hist.GetBinCenter(max_bin))
    
    half_max = max_value*0.75
    
    # Find left and right bins closest to half-max value
    left_bin = max_bin
    right_bin = max_bin
    while hist.GetBinContent(left_bin) > half_max and left_bin > 1:
        left_bin -= 1
    while hist.GetBinContent(right_bin) > half_max and right_bin < hist.GetNbinsX():
        right_bin += 1

    #min_range = hist.GetBinCenter(max_bin-100)
    #max_range = hist.GetBinCenter(max_bin+100)

    min_range = hist.GetBinCenter(left_bin)
    print("min_range",min_range)
    max_range = hist.GetBinCenter(right_bin)
    print("max_range",max_range)
    print("-"*25)

    hist.Fit("gaus", "Q", "", min_range, max_range)
    fit_func = hist.GetFunction('gaus')
    
    if dtype == "simc":
        fit_func.SetLineColor(kBlack)
    if dtype == "data":
        fit_func.SetLineColor(kRed)
    if dtype == "dummy":
        fit_func.SetLineColor(kGreen)    
    
    mean = fit_func.GetParameter(1)
    mean_err = fit_func.GetParError(1)
    
    return [mean, mean_err]

################################################################################################################################################
# Removes stat box
ROOT.gStyle.SetOptStat(0)
################################################################################################################################################
# Plot histograms

eff_plt = TCanvas()
G_eff_plt = ROOT.TMultiGraph()
l_eff_plt = ROOT.TLegend(0.115,0.55,0.33,0.9)

eff_plt.SetGrid()

G_data_eff.SetMarkerStyle(21)
G_dummy_eff.SetMarkerStyle(21)

G_data_eff.SetMarkerSize(1)
G_dummy_eff.SetMarkerSize(1)

G_dummy_eff.SetMarkerColor(kRed)

G_eff_plt.Add(G_data_eff)
G_eff_plt.Add(G_dummy_eff)

G_eff_plt.Draw("AP")

G_eff_plt.SetTitle(" ;Run Numbers; Total Efficiency")

i=0
while i <= G_eff_plt.GetXaxis().GetXmax():
    bin_ix = G_eff_plt.GetXaxis().FindBin(i)
    if i in data_runNums or i in dummy_runNums:
        G_eff_plt.GetXaxis().SetBinLabel(bin_ix,"%d" % i)
    i+=1

G_eff_plt.GetYaxis().SetTitleOffset(1.5)
G_eff_plt.GetXaxis().SetTitleOffset(1.5)
G_eff_plt.GetXaxis().SetLabelSize(0.04)

l_eff_plt.AddEntry(G_data_eff,"Data")
l_eff_plt.AddEntry(G_dummy_eff,"Dummy")

l_eff_plt.Draw()

eff_plt.Print(outputpdf + '(')

c_pbeta = TCanvas()

c_pbeta.Divide(2,1)

c_pbeta.cd(1)
H_pbeta_DATA_nocut.Draw("colz")

c_pbeta.cd(2)
H_pbeta_DATA.Draw("colz")

c_pbeta.Print(outputpdf)

c_hbeta = TCanvas()

c_hbeta.Divide(2,1)

c_hbeta.cd(1)
H_hbeta_DATA_nocut.Draw("colz")

c_hbeta.cd(2)
H_hbeta_DATA.Draw("colz")

c_hbeta.Print(outputpdf)

c_ctvpbeta = TCanvas()

c_ctvpbeta.Divide(2,1)

c_ctvpbeta.cd(1)
CoinTime_vs_pbeta_DATA_nocut.Draw("colz")

c_ctvpbeta.cd(2)
CoinTime_vs_pbeta_DATA.Draw("colz")

c_ctvpbeta.Print(outputpdf)

c_ctvhbeta = TCanvas()

c_ctvhbeta.Divide(2,1)

c_ctvhbeta.cd(1)
CoinTime_vs_pbeta_DATA_nocut.Draw("colz")

c_ctvhbeta.cd(2)
CoinTime_vs_pbeta_DATA.Draw("colz")

c_ctvhbeta.Print(outputpdf)

c_pid = TCanvas()
l_pid = ROOT.TLegend(0.115,0.55,0.33,0.9)

c_pid.Divide(2,3)

c_pid.cd(1)
gPad.SetLogy()
H_cal_etottracknorm_DATA_nocut.SetLineColor(kCyan)
H_cal_etottracknorm_DATA_nopid.SetLineColor(kMagenta)
H_cal_etottracknorm_DATA.Draw("E1")
H_cal_etottracknorm_DATA_nocut.Draw("same, E1")
H_cal_etottracknorm_DATA_nopid.Draw("same, E1")

c_pid.cd(2)
H_cer_npeSum_DATA_nocut.SetLineColor(kCyan)
H_cer_npeSum_DATA_nopid.SetLineColor(kMagenta)
gPad.SetLogy()
H_cer_npeSum_DATA.Draw("E1")
H_cer_npeSum_DATA_nocut.Draw("same, E1")
H_cer_npeSum_DATA_nopid.Draw("same, E1")

c_pid.cd(3)
P_cal_etottracknorm_DATA_nocut.SetLineColor(kCyan)
P_cal_etottracknorm_DATA_nopid.SetLineColor(kMagenta)
gPad.SetLogy()
P_cal_etottracknorm_DATA.Draw("E1")
P_cal_etottracknorm_DATA_nocut.Draw("same, E1")
P_cal_etottracknorm_DATA_nopid.Draw("same, E1")

c_pid.cd(4)
P_hgcer_npeSum_DATA_nocut.SetLineColor(kCyan)
P_hgcer_npeSum_DATA_nopid.SetLineColor(kMagenta)
gPad.SetLogy()
P_hgcer_npeSum_DATA.Draw("E1")
P_hgcer_npeSum_DATA_nocut.Draw("same, E1")
P_hgcer_npeSum_DATA_nopid.Draw("same, E1")

c_pid.cd(5)
P_aero_npeSum_DATA_nocut.SetLineColor(kCyan)
P_aero_npeSum_DATA_nopid.SetLineColor(kMagenta)
gPad.SetLogy()
P_aero_npeSum_DATA.Draw("E1")
P_aero_npeSum_DATA_nocut.Draw("same, E1")
P_aero_npeSum_DATA_nopid.Draw("same, E1")
'''
c_pid.cd(6)
l_pid.SetTextSize(0.05)
log_txt = ROOT.TPaveText(0.,0.3,1.0,0.5,"NDC");
log_entry = log_entry.replace("[","").replace("]","").replace("'","").replace("{","").replace("}","").split(",")
log_txt.SetTextSize(0.0335)
for cut in log_entry:
    log_txt.AddText(cut)
l_pid.AddEntry(H_cal_etottracknorm_DATA,"p cut")
l_pid.AddEntry(H_cal_etottracknorm_DATA_nocut,"No cut")
l_pid.AddEntry(H_cal_etottracknorm_DATA_nopid,"No PID cut")
log_txt.Draw("same, E1")
l_pid.Draw("same, E1")
c_pid.Draw()
'''
c_pid.Print(outputpdf)

c_pid_2d = TCanvas()

c_pid_2d.Divide(2,2)

c_pid_2d.cd(1)
H_cal_etottracknorm_vs_H_cer_npeSum_DATA.Draw("colz")

c_pid_2d.cd(2)
P_cal_etottracknorm_vs_P_hgcer_npeSum_DATA.Draw("colz")

c_pid_2d.cd(3)
P_cal_etottracknorm_vs_P_aero_npeSum_DATA.Draw("colz")

c_pid_2d.cd(4)
P_hgcer_npeSum_vs_P_aero_npeSum_DATA.Draw("colz")

c_pid_2d.Draw()

c_pid_2d.Print(outputpdf)

ct_ep = TCanvas()
l_ct_ep = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_ct_ep_DUMMY.SetLineColor(kGreen)
H_ct_ep_DATA.SetLineColor(kRed)
H_ct_ep_DATA_nocut.SetLineColor(kCyan)
H_ct_ep_DATA_nopid.SetLineColor(kMagenta)

H_ct_ep_DATA.Draw("E1")
H_ct_ep_DUMMY.Draw("same, E1")
H_ct_ep_DATA_nocut.Draw("same, E1")
H_ct_ep_DATA_nopid.Draw("same, E1")

l_ct_ep.AddEntry(H_ct_ep_DATA,"p cut")
l_ct_ep.AddEntry(H_ct_ep_DUMMY,"Dummy")
l_ct_ep.AddEntry(H_ct_ep_DATA_nocut,"No cut")
l_ct_ep.AddEntry(H_ct_ep_DATA_nopid,"No PID cut")

l_ct_ep.Draw()

ct_ep.Print(outputpdf)

ct_ep_mmp = TCanvas()

H_ct_ep_vs_H_MMp2_DATA.Draw("colz")

ct_ep_mmp.Print(outputpdf)

emiss_vs_delta = TCanvas()

emiss_vs_delta.Divide(1,2)

emiss_vs_delta.cd(1)
H_emiss_vs_H_hsdelta_DATA.Draw("colz")

emiss_vs_delta.cd(2)
H_emiss_vs_H_ssdelta_DATA.Draw("colz")

emiss_vs_delta.Print(outputpdf)

pmiss_vs_delta = TCanvas()

pmiss_vs_delta.Divide(1,2)

pmiss_vs_delta.cd(1)
H_pmiss_vs_H_hsdelta_DATA.Draw("colz")

pmiss_vs_delta.cd(2)
H_pmiss_vs_H_ssdelta_DATA.Draw("colz")

pmiss_vs_delta.Print(outputpdf)

hsdelta_vs_ssdelta = TCanvas()

H_hsdelta_vs_H_ssdelta_DATA.Draw("colz")

hsdelta_vs_ssdelta.Print(outputpdf)

raster_x_vs_miss = TCanvas()

raster_x_vs_miss.Divide(1,2)

raster_x_vs_miss.cd(1)
H_raster_x_vs_H_pmiss_DATA.Draw("colz")

raster_x_vs_miss.cd(2)
H_raster_x_vs_H_emiss_DATA.Draw("colz")

raster_x_vs_miss.Print(outputpdf)

raster_y_vs_miss = TCanvas()

raster_y_vs_miss.Divide(1,2)

raster_y_vs_miss.cd(1)
H_raster_y_vs_H_pmiss_DATA.Draw("colz")

raster_y_vs_miss.cd(2)
H_raster_y_vs_H_emiss_DATA.Draw("colz")

raster_y_vs_miss.Print(outputpdf)

raster_x_vs_raster_y = TCanvas()

H_raster_x_vs_H_raster_y_DATA.Draw("colz")

raster_x_vs_raster_y.Print(outputpdf)

bpm_tar_x = TCanvas()
l_bpm_tar_x = ROOT.TLegend(0.115,0.55,0.33,0.9)

bpm_tar_x_DATA.SetLineColor(kRed)
bpm_tar_x_DATA_nocut.SetLineColor(kCyan)
bpm_tar_x_DATA_nopid.SetLineColor(kMagenta)

tmp_b_mean_bpm_tar_x_data = fit_gaussian(bpm_tar_x_DATA, -0.1, 0.1, "data")
b_mean_bpm_tar_x_data = tmp_b_mean_bpm_tar_x_data[0]
b_mean_err_bpm_tar_x_data = tmp_b_mean_bpm_tar_x_data[1]

bpm_tar_x_DATA.Draw("E1")
if DEBUG:
    bpm_tar_x_DATA_nocut.Draw("same, E1")
    bpm_tar_x_DATA_nopid.Draw("same, E1")

l_bpm_tar_x.AddEntry(bpm_tar_x_DATA,"DATA, Mean = {:.4e}\pm{:.4e}".format( b_mean_bpm_tar_x_data, b_mean_err_bpm_tar_x_data))
    
b_stddev_bpm_tar_x_data = (bpm_tar_x_DATA.GetStdDev())
b_stddev_bpm_tar_x_data_nocut = (bpm_tar_x_DATA_nocut.GetStdDev())
b_stddev_bpm_tar_x_data_nopid = (bpm_tar_x_DATA_nopid.GetStdDev())

l_bpm_tar_x.AddEntry(bpm_tar_x_DATA,"DATA, Stddev = {:.4e}".format( b_stddev_bpm_tar_x_data))
if DEBUG:
    l_bpm_tar_x.AddEntry(bpm_tar_x_DATA_nocut,"DATA (no cut), Stddev = {:.4e}".format( b_stddev_bpm_tar_x_data_nocut))
    l_bpm_tar_x.AddEntry(bpm_tar_x_DATA_nopid,"DATA (no PID cut), Stddev = {:.4e}".format( b_stddev_bpm_tar_x_data_nopid))
    
l_bpm_tar_x.Draw()

bpm_tar_x.Print(outputpdf)

bpm_tar_y = TCanvas()
l_bpm_tar_y = ROOT.TLegend(0.115,0.55,0.33,0.9)

bpm_tar_y_DATA.SetLineColor(kRed)
bpm_tar_y_DATA_nocut.SetLineColor(kCyan)
bpm_tar_y_DATA_nopid.SetLineColor(kMagenta)

tmp_b_mean_bpm_tar_y_data = fit_gaussian(bpm_tar_y_DATA, 0.0, 0.2, "data")
b_mean_bpm_tar_y_data = tmp_b_mean_bpm_tar_y_data[0]
b_mean_err_bpm_tar_y_data = tmp_b_mean_bpm_tar_y_data[1]

bpm_tar_y_DATA.Draw("E1")
if DEBUG:
    bpm_tar_y_DATA_nocut.Draw("same, E1")
    bpm_tar_y_DATA_nopid.Draw("same, E1")

l_bpm_tar_y.AddEntry(bpm_tar_y_DATA,"DATA, Mean = {:.4e}\pm{:.4e}".format( b_mean_bpm_tar_y_data, b_mean_err_bpm_tar_y_data))
if DEBUG:
    l_bpm_tar_y.AddEntry(bpm_tar_y_DATA_nocut,"DATA (no cut), Mean = {:.4e}".format( b_mean_bpm_tar_y_data_nocut))
    l_bpm_tar_y.AddEntry(bpm_tar_y_DATA_nopid,"DATA (no PID cut), Mean = {:.4e}".format( b_mean_bpm_tar_y_data_nopid))
    
b_stddev_bpm_tar_y_data = (bpm_tar_y_DATA.GetStdDev())
b_stddev_bpm_tar_y_data_nocut = (bpm_tar_y_DATA_nocut.GetStdDev())
b_stddev_bpm_tar_y_data_nopid = (bpm_tar_y_DATA_nopid.GetStdDev())

l_bpm_tar_y.AddEntry(bpm_tar_y_DATA,"DATA, Stddev = {:.4e}".format( b_stddev_bpm_tar_y_data))
if DEBUG:
    l_bpm_tar_y.AddEntry(bpm_tar_y_DATA_nocut,"DATA (no cut), Stddev = {:.4e}".format( b_stddev_bpm_tar_y_data_nocut))
    l_bpm_tar_y.AddEntry(bpm_tar_y_DATA_nopid,"DATA (no PID cut), Stddev = {:.4e}".format( b_stddev_bpm_tar_y_data_nopid))
    
l_bpm_tar_y.Draw()

bpm_tar_y.Print(outputpdf)

xfp = TCanvas()
l_xfp = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_ssxfp_DATA.SetLineColor(kRed)
H_ssxfp_DATA_nocut.SetLineColor(kCyan)
H_ssxfp_DATA_nopid.SetLineColor(kMagenta)
H_ssxfp_DUMMY.SetLineColor(kGreen)

H_ssxfp_SIMC.Draw("E1")
H_ssxfp_DATA.Draw("same, E1")
H_ssxfp_DUMMY.Draw("same, E1")
if DEBUG:
    H_ssxfp_DATA_nocut.Draw("same, E1")
    H_ssxfp_DATA_nopid.Draw("same, E1")

b_int_xfp_simc = int(H_ssxfp_SIMC.Integral())
b_int_xfp_data = int(H_ssxfp_DATA.Integral())
b_int_xfp_dummy = int(H_ssxfp_DUMMY.Integral())
b_int_xfp_data_nocut = int(H_ssxfp_DATA_nocut.Integral())
b_int_xfp_data_nopid = int(H_ssxfp_DATA_nopid.Integral())

l_xfp.AddEntry(H_ssxfp_SIMC,"SIMC, INT = {:.0f}".format( b_int_xfp_simc))
l_xfp.AddEntry(H_ssxfp_DATA,"DATA, INT = {:.0f}".format( b_int_xfp_data))
l_xfp.AddEntry(H_ssxfp_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_xfp_dummy))
if DEBUG:
    l_xfp.AddEntry(H_ssxfp_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_xfp_data_nocut))
    l_xfp.AddEntry(H_ssxfp_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_xfp_data_nopid))

l_xfp.Draw()

xfp.Print(outputpdf)

yfp = TCanvas()
l_yfp = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_ssyfp_DATA.SetLineColor(kRed)
H_ssyfp_DATA_nocut.SetLineColor(kCyan)
H_ssyfp_DATA_nopid.SetLineColor(kMagenta)
H_ssyfp_DUMMY.SetLineColor(kGreen)

H_ssyfp_SIMC.Draw("E1")
H_ssyfp_DATA.Draw("same, E1")
H_ssyfp_DUMMY.Draw("same, E1")
if DEBUG:
    H_ssyfp_DATA_nocut.Draw("same, E1")
    H_ssyfp_DATA_nopid.Draw("same, E1")

b_int_yfp_simc = int(H_ssyfp_SIMC.Integral())
b_int_yfp_data = int(H_ssyfp_DATA.Integral())
b_int_yfp_dummy = int(H_ssyfp_DUMMY.Integral())
b_int_yfp_data_nocut = int(H_ssyfp_DATA_nocut.Integral())
b_int_yfp_data_nopid = int(H_ssyfp_DATA_nopid.Integral())

l_yfp.AddEntry(H_ssyfp_SIMC,"SIMC, INT = {:.0f}".format( b_int_yfp_simc))
l_yfp.AddEntry(H_ssyfp_DATA,"DATA, INT = {:.0f}".format( b_int_yfp_data))
l_yfp.AddEntry(H_ssyfp_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_yfp_dummy))
if DEBUG:
    l_yfp.AddEntry(H_ssyfp_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_yfp_data_nocut))
    l_yfp.AddEntry(H_ssyfp_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_yfp_data_nopid))

l_yfp.Draw()

yfp.Print(outputpdf)

xpfp = TCanvas()
l_xpfp = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_ssxpfp_DATA.SetLineColor(kRed)
H_ssxpfp_DATA_nocut.SetLineColor(kCyan)
H_ssxpfp_DATA_nopid.SetLineColor(kMagenta)
H_ssxpfp_DUMMY.SetLineColor(kGreen)

H_ssxpfp_SIMC.Draw("E1")
H_ssxpfp_DATA.Draw("same, E1")
if DEBUG:
    H_ssxpfp_DATA_nocut.Draw("same, E1")
    H_ssxpfp_DATA_nopid.Draw("same, E1")
H_ssxpfp_DUMMY.Draw("same, E1")

b_int_xpfp_simc = int(H_ssxpfp_SIMC.Integral())
b_int_xpfp_data = int(H_ssxpfp_DATA.Integral())
b_int_xpfp_data_nocut = int(H_ssxpfp_DATA_nocut.Integral())
b_int_xpfp_data_nopid = int(H_ssxpfp_DATA_nopid.Integral())
b_int_xpfp_dummy = int(H_ssxpfp_DUMMY.Integral())

l_xpfp.AddEntry(H_ssxpfp_SIMC,"SIMC, INT = {:.0f}".format( b_int_xpfp_simc))
l_xpfp.AddEntry(H_ssxpfp_DATA,"DATA, INT = {:.0f}".format( b_int_xpfp_data))
if DEBUG:
    l_xpfp.AddEntry(H_ssxpfp_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_xpfp_data_nocut))
    l_xpfp.AddEntry(H_ssxpfp_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_xpfp_data_nopid))
l_xpfp.AddEntry(H_ssxpfp_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_xpfp_dummy))

l_xpfp.Draw()

xpfp.Print(outputpdf)

ypfp = TCanvas()
l_ypfp = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_ssypfp_DATA.SetLineColor(kRed)
H_ssypfp_DATA_nocut.SetLineColor(kCyan)
H_ssypfp_DATA_nopid.SetLineColor(kMagenta)
H_ssypfp_DUMMY.SetLineColor(kGreen)

H_ssypfp_SIMC.Draw("E1")
H_ssypfp_DATA.Draw("same, E1")
if DEBUG:
    H_ssypfp_DATA_nocut.Draw("same, E1")
    H_ssypfp_DATA_nopid.Draw("same, E1")
H_ssypfp_DUMMY.Draw("same, E1")

b_int_ypfp_simc = int(H_ssypfp_SIMC.Integral())
b_int_ypfp_data = int(H_ssypfp_DATA.Integral())
b_int_ypfp_data_nocut = int(H_ssypfp_DATA_nocut.Integral())
b_int_ypfp_data_nopid = int(H_ssypfp_DATA_nopid.Integral())
b_int_ypfp_dummy = int(H_ssypfp_DUMMY.Integral())

l_ypfp.AddEntry(H_ssypfp_SIMC,"SIMC, INT = {:.0f}".format( b_int_ypfp_simc))
l_ypfp.AddEntry(H_ssypfp_DATA,"DATA, INT = {:.0f}".format( b_int_ypfp_data))
if DEBUG:
    l_ypfp.AddEntry(H_ssypfp_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_ypfp_data_nocut))
    l_ypfp.AddEntry(H_ssypfp_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_ypfp_data_nopid))
l_ypfp.AddEntry(H_ssypfp_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_ypfp_dummy))

l_ypfp.Draw()

ypfp.Print(outputpdf)

hxfp = TCanvas()
l_hxfp = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_hsxfp_DATA.SetLineColor(kRed)
H_hsxfp_DATA_nocut.SetLineColor(kCyan)
H_hsxfp_DATA_nopid.SetLineColor(kMagenta)
H_hsxfp_DUMMY.SetLineColor(kGreen)

H_hsxfp_SIMC.Draw("E1")
H_hsxfp_DATA.Draw("same, E1")
if DEBUG:
    H_hsxfp_DATA_nocut.Draw("same, E1")
    H_hsxfp_DATA_nopid.Draw("same, E1")
H_hsxfp_DUMMY.Draw("same, E1")

b_int_hxfp_simc = int(H_hsxfp_SIMC.Integral())
b_int_hxfp_data = int(H_hsxfp_DATA.Integral())
b_int_hxfp_data_nocut = int(H_hsxfp_DATA_nocut.Integral())
b_int_hxfp_data_nopid = int(H_hsxfp_DATA_nopid.Integral())
b_int_hxfp_dummy = int(H_hsxfp_DUMMY.Integral())

l_hxfp.AddEntry(H_hsxfp_SIMC,"SIMC, INT = {:.0f}".format( b_int_hxfp_simc))
l_hxfp.AddEntry(H_hsxfp_DATA,"DATA, INT = {:.0f}".format( b_int_hxfp_data))
if DEBUG:
    l_hxfp.AddEntry(H_hsxfp_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_hxfp_data_nocut))
    l_hxfp.AddEntry(H_hsxfp_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_hxfp_data_nopid))
l_hxfp.AddEntry(H_hsxfp_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_hxfp_dummy))

l_hxfp.Draw()

hxfp.Print(outputpdf)

hyfp = TCanvas()
l_hyfp = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_hsyfp_DATA.SetLineColor(kRed)
H_hsyfp_DATA_nocut.SetLineColor(kCyan)
H_hsyfp_DATA_nopid.SetLineColor(kMagenta)
H_hsyfp_DUMMY.SetLineColor(kGreen)

H_hsyfp_SIMC.Draw("E1")
H_hsyfp_DATA.Draw("same, E1")
if DEBUG:
    H_hsyfp_DATA_nocut.Draw("same, E1")
    H_hsyfp_DATA_nopid.Draw("same, E1")
H_hsyfp_DUMMY.Draw("same, E1")

b_int_hyfp_simc = int(H_hsyfp_SIMC.Integral())
b_int_hyfp_data = int(H_hsyfp_DATA.Integral())
b_int_hyfp_data_nocut = int(H_hsyfp_DATA_nocut.Integral())
b_int_hyfp_data_nopid = int(H_hsyfp_DATA_nopid.Integral())
b_int_hyfp_dummy = int(H_hsyfp_DUMMY.Integral())

l_hyfp.AddEntry(H_hsyfp_SIMC,"SIMC, INT = {:.0f}".format( b_int_hyfp_simc))
l_hyfp.AddEntry(H_hsyfp_DATA,"DATA, INT = {:.0f}".format( b_int_hyfp_data))
if DEBUG:
    l_hyfp.AddEntry(H_hsyfp_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_hyfp_data_nocut))
    l_hyfp.AddEntry(H_hsyfp_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_hyfp_data_nopid))
l_hyfp.AddEntry(H_hsyfp_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_hyfp_dummy))

l_hyfp.Draw()

hyfp.Print(outputpdf)

hxpfp = TCanvas()
l_hxpfp = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_hsxpfp_DATA.SetLineColor(kRed)
H_hsxpfp_DATA_nocut.SetLineColor(kCyan)
H_hsxpfp_DATA_nopid.SetLineColor(kMagenta)
H_hsxpfp_DUMMY.SetLineColor(kGreen)

H_hsxpfp_SIMC.Draw("E1")
H_hsxpfp_DATA.Draw("same, E1")
if DEBUG:
    H_hsxpfp_DATA_nocut.Draw("same, E1")
    H_hsxpfp_DATA_nopid.Draw("same, E1")
H_hsxpfp_DUMMY.Draw("same, E1")

b_int_hxpfp_simc = int(H_hsxpfp_SIMC.Integral())
b_int_hxpfp_data = int(H_hsxpfp_DATA.Integral())
b_int_hxpfp_data_nocut = int(H_hsxpfp_DATA_nocut.Integral())
b_int_hxpfp_data_nopid = int(H_hsxpfp_DATA_nopid.Integral())
b_int_hxpfp_dummy = int(H_hsxpfp_DUMMY.Integral())

l_hxpfp.AddEntry(H_hsxpfp_SIMC,"SIMC, INT = {:.0f}".format( b_int_hxpfp_simc))
l_hxpfp.AddEntry(H_hsxpfp_DATA,"DATA, INT = {:.0f}".format( b_int_hxpfp_data))
if DEBUG:
    l_hxpfp.AddEntry(H_hsxpfp_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_hxpfp_data_nocut))
    l_hxpfp.AddEntry(H_hsxpfp_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_hxpfp_data_nopid))
l_hxpfp.AddEntry(H_hsxpfp_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_hxpfp_dummy))

l_hxpfp.Draw()

hxpfp.Print(outputpdf)

hypfp = TCanvas()
l_hypfp = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_hsypfp_DATA.SetLineColor(kRed)
H_hsypfp_DATA_nocut.SetLineColor(kCyan)
H_hsypfp_DATA_nopid.SetLineColor(kMagenta)
H_hsypfp_DUMMY.SetLineColor(kGreen)

H_hsypfp_SIMC.Draw("E1")
H_hsypfp_DATA.Draw("same, E1")
if DEBUG:
    H_hsypfp_DATA_nocut.Draw("same, E1")
    H_hsypfp_DATA_nopid.Draw("same, E1")
H_hsypfp_DUMMY.Draw("same, E1")

b_int_hypfp_simc = int(H_hsypfp_SIMC.Integral())
b_int_hypfp_data = int(H_hsypfp_DATA.Integral())
b_int_hypfp_data_nocut = int(H_hsypfp_DATA_nocut.Integral())
b_int_hypfp_data_nopid = int(H_hsypfp_DATA_nopid.Integral())
b_int_hypfp_dummy = int(H_hsypfp_DUMMY.Integral())

l_hypfp.AddEntry(H_hsypfp_SIMC,"SIMC, INT = {:.0f}".format( b_int_hypfp_simc))
l_hypfp.AddEntry(H_hsypfp_DATA,"DATA, INT = {:.0f}".format( b_int_hypfp_data))
if DEBUG:
    l_hypfp.AddEntry(H_hsypfp_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_hypfp_data_nocut))
    l_hypfp.AddEntry(H_hsypfp_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_hypfp_data_nopid))
l_hypfp.AddEntry(H_hsypfp_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_hypfp_dummy))

l_hypfp.Draw()

hypfp.Print(outputpdf)

xptar = TCanvas()
l_xptar = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_ssxptar_DATA.SetLineColor(kRed)
H_ssxptar_DATA_nocut.SetLineColor(kCyan)
H_ssxptar_DATA_nopid.SetLineColor(kMagenta)
H_ssxptar_DUMMY.SetLineColor(kGreen)

H_ssxptar_SIMC.Draw("E1")
H_ssxptar_DATA.Draw("same, E1")
if DEBUG:
    H_ssxptar_DATA_nocut.Draw("same, E1")
    H_ssxptar_DATA_nopid.Draw("same, E1")
H_ssxptar_DUMMY.Draw("same, E1")

b_int_xptar_simc = int(H_ssxptar_SIMC.Integral())
b_int_xptar_data = int(H_ssxptar_DATA.Integral())
b_int_xptar_data_nocut = int(H_ssxptar_DATA_nocut.Integral())
b_int_xptar_data_nopid = int(H_ssxptar_DATA_nopid.Integral())
b_int_xptar_dummy = int(H_ssxptar_DUMMY.Integral())

l_xptar.AddEntry(H_ssxptar_SIMC,"SIMC, INT = {:.0f}".format( b_int_xptar_simc))
l_xptar.AddEntry(H_ssxptar_DATA,"DATA, INT = {:.0f}".format( b_int_xptar_data))
if DEBUG:
    l_xptar.AddEntry(H_ssxptar_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_xptar_data_nocut))
    l_xptar.AddEntry(H_ssxptar_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_xptar_data_nopid))
l_xptar.AddEntry(H_ssxptar_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_xptar_dummy))

l_xptar.Draw()

xptar.Print(outputpdf)

yptar = TCanvas()
l_yptar = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_ssyptar_DATA.SetLineColor(kRed)
H_ssyptar_DATA_nocut.SetLineColor(kCyan)
H_ssyptar_DATA_nopid.SetLineColor(kMagenta)
H_ssyptar_DUMMY.SetLineColor(kGreen)

H_ssyptar_SIMC.Draw("E1")
H_ssyptar_DATA.Draw("same, E1")
if DEBUG:
    H_ssyptar_DATA_nocut.Draw("same, E1")
    H_ssyptar_DATA_nopid.Draw("same, E1")
H_ssyptar_DUMMY.Draw("same, E1")

b_int_yptar_simc = int(H_ssyptar_SIMC.Integral())
b_int_yptar_data = int(H_ssyptar_DATA.Integral())
b_int_yptar_data_nocut = int(H_ssyptar_DATA_nocut.Integral())
b_int_yptar_data_nopid = int(H_ssyptar_DATA_nopid.Integral())
b_int_yptar_dummy = int(H_ssyptar_DUMMY.Integral())

l_yptar.AddEntry(H_ssyptar_SIMC,"SIMC, INT = {:.0f}".format( b_int_yptar_simc))
l_yptar.AddEntry(H_ssyptar_DATA,"DATA, INT = {:.0f}".format( b_int_yptar_data))
if DEBUG:
    l_yptar.AddEntry(H_ssyptar_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_yptar_data_nocut))
    l_yptar.AddEntry(H_ssyptar_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_yptar_data_nopid))
l_yptar.AddEntry(H_ssyptar_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_yptar_dummy))

l_yptar.Draw()

yptar.Print(outputpdf)

hxptar = TCanvas()
l_hxptar = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_hsxptar_DATA.SetLineColor(kRed)
H_hsxptar_DATA_nocut.SetLineColor(kCyan)
H_hsxptar_DATA_nopid.SetLineColor(kMagenta)
H_hsxptar_DUMMY.SetLineColor(kGreen)

H_hsxptar_SIMC.Draw("E1")
H_hsxptar_DATA.Draw("same, E1")
if DEBUG:
    H_hsxptar_DATA_nocut.Draw("same, E1")
    H_hsxptar_DATA_nopid.Draw("same, E1")
H_hsxptar_DUMMY.Draw("same, E1")

b_int_hxptar_simc = int(H_hsxptar_SIMC.Integral())
b_int_hxptar_data = int(H_hsxptar_DATA.Integral())
b_int_hxptar_data_nocut = int(H_hsxptar_DATA_nocut.Integral())
b_int_hxptar_data_nopid = int(H_hsxptar_DATA_nopid.Integral())
b_int_hxptar_dummy = int(H_hsxptar_DUMMY.Integral())

l_hxptar.AddEntry(H_hsxptar_SIMC,"SIMC, INT = {:.0f}".format( b_int_hxptar_simc))
l_hxptar.AddEntry(H_hsxptar_DATA,"DATA, INT = {:.0f}".format( b_int_hxptar_data))
if DEBUG:
    l_hxptar.AddEntry(H_hsxptar_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_hxptar_data_nocut))
    l_hxptar.AddEntry(H_hsxptar_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_hxptar_data_nopid))
l_hxptar.AddEntry(H_hsxptar_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_hxptar_dummy))

l_hxptar.Draw()

hxptar.Print(outputpdf)

hyptar = TCanvas()
l_hyptar = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_hsyptar_DATA.SetLineColor(kRed)
H_hsyptar_DATA_nocut.SetLineColor(kCyan)
H_hsyptar_DATA_nopid.SetLineColor(kMagenta)
H_hsyptar_DUMMY.SetLineColor(kGreen)

H_hsyptar_SIMC.Draw("E1")
H_hsyptar_DATA.Draw("same, E1")
if DEBUG:
    H_hsyptar_DATA_nocut.Draw("same, E1")
    H_hsyptar_DATA_nopid.Draw("same, E1")
H_hsyptar_DUMMY.Draw("same, E1")

b_int_hyptar_simc = int(H_hsyptar_SIMC.Integral())
b_int_hyptar_data = int(H_hsyptar_DATA.Integral())
b_int_hyptar_data_nocut = int(H_hsyptar_DATA_nocut.Integral())
b_int_hyptar_data_nopid = int(H_hsyptar_DATA_nopid.Integral())
b_int_hyptar_dummy = int(H_hsyptar_DUMMY.Integral())

l_hyptar.AddEntry(H_hsyptar_SIMC,"SIMC, INT = {:.0f}".format( b_int_hyptar_simc))
l_hyptar.AddEntry(H_hsyptar_DATA,"DATA, INT = {:.0f}".format( b_int_hyptar_data))
if DEBUG:
    l_hyptar.AddEntry(H_hsyptar_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_hyptar_data_nocut))
    l_hyptar.AddEntry(H_hsyptar_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_hyptar_data_nopid))
l_hyptar.AddEntry(H_hsyptar_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_hyptar_dummy))

l_hyptar.Draw()

hyptar.Print(outputpdf)

Delta = TCanvas()
l_Delta = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_ssdelta_DATA.SetLineColor(kRed)
H_ssdelta_DATA_nocut.SetLineColor(kCyan)
H_ssdelta_DATA_nopid.SetLineColor(kMagenta)
H_ssdelta_DUMMY.SetLineColor(kGreen)

H_ssdelta_SIMC.Draw("E1")
H_ssdelta_DATA.Draw("same, E1")
if DEBUG:
    H_ssdelta_DATA_nocut.Draw("same, E1")
    H_ssdelta_DATA_nopid.Draw("same, E1")
H_ssdelta_DUMMY.Draw("same, E1")

b_int_Delta_simc = int(H_ssdelta_SIMC.Integral())
b_int_Delta_data = int(H_ssdelta_DATA.Integral())
b_int_Delta_data_nocut = int(H_ssdelta_DATA_nocut.Integral())
b_int_Delta_data_nopid = int(H_ssdelta_DATA_nopid.Integral())
b_int_Delta_dummy = int(H_ssdelta_DUMMY.Integral())

l_Delta.AddEntry(H_ssdelta_SIMC,"SIMC, INT = {:.0f}".format( b_int_Delta_simc))
l_Delta.AddEntry(H_ssdelta_DATA,"DATA, INT = {:.0f}".format( b_int_Delta_data))
if DEBUG:
    l_Delta.AddEntry(H_ssdelta_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_Delta_data_nocut))
    l_Delta.AddEntry(H_ssdelta_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_Delta_data_nopid))
l_Delta.AddEntry(H_ssdelta_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_Delta_dummy))

l_Delta.Draw()

Delta.Print(outputpdf)

hDelta = TCanvas()
l_hDelta = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_hsdelta_DATA.SetLineColor(kRed)
H_hsdelta_DATA_nocut.SetLineColor(kCyan)
H_hsdelta_DATA_nopid.SetLineColor(kMagenta)
H_hsdelta_DUMMY.SetLineColor(kGreen)

H_hsdelta_SIMC.Draw("E1")
H_hsdelta_DATA.Draw("same, E1")
if DEBUG:
    H_hsdelta_DATA_nocut.Draw("same, E1")
    H_hsdelta_DATA_nopid.Draw("same, E1")
H_hsdelta_DUMMY.Draw("same, E1")

b_int_hDelta_simc = int(H_hsdelta_SIMC.Integral())
b_int_hDelta_data = int(H_hsdelta_DATA.Integral())
b_int_hDelta_data_nocut = int(H_hsdelta_DATA_nocut.Integral())
b_int_hDelta_data_nopid = int(H_hsdelta_DATA_nopid.Integral())
b_int_hDelta_dummy = int(H_hsdelta_DUMMY.Integral())

l_hDelta.AddEntry(H_hsdelta_SIMC,"SIMC, INT = {:.0f}".format( b_int_hDelta_simc))
l_hDelta.AddEntry(H_hsdelta_DATA,"DATA, INT = {:.0f}".format( b_int_hDelta_data))
if DEBUG:
    l_hDelta.AddEntry(H_hsdelta_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_hDelta_data_nocut))
    l_hDelta.AddEntry(H_hsdelta_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_hDelta_data_nopid))
l_hDelta.AddEntry(H_hsdelta_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_hDelta_dummy))

l_hDelta.Draw()

hDelta.Print(outputpdf)

CQ2 = TCanvas()
l_Q2 = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_Q2_DATA.SetLineColor(kRed)
H_Q2_DATA_nocut.SetLineColor(kCyan)
H_Q2_DATA_nopid.SetLineColor(kMagenta)
H_Q2_DUMMY.SetLineColor(kGreen)

H_Q2_SIMC.Draw("E1")
H_Q2_DATA.Draw("same, E1")
if DEBUG:
    H_Q2_DATA_nocut.Draw("same, E1")
    H_Q2_DATA_nopid.Draw("same, E1")
H_Q2_DUMMY.Draw("same, E1")

b_int_Q2_simc = int(H_Q2_SIMC.Integral())
b_int_Q2_data = int(H_Q2_DATA.Integral())
b_int_Q2_data_nocut = int(H_Q2_DATA_nocut.Integral())
b_int_Q2_data_nopid = int(H_Q2_DATA_nopid.Integral())
b_int_Q2_dummy = int(H_Q2_DUMMY.Integral())

l_Q2.AddEntry(H_Q2_SIMC,"SIMC, INT = {:.0f}".format( b_int_Q2_simc))
l_Q2.AddEntry(H_Q2_DATA,"DATA, INT = {:.0f}".format( b_int_Q2_data))
if DEBUG:
    l_Q2.AddEntry(H_Q2_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_Q2_data_nocut))
    l_Q2.AddEntry(H_Q2_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_Q2_data_nopid))
l_Q2.AddEntry(H_Q2_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_Q2_dummy))

l_Q2.Draw()

CQ2.Print(outputpdf)

Cepsilon = TCanvas()
l_epsilon = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_epsilon_DATA.SetLineColor(kRed)
H_epsilon_DATA_nocut.SetLineColor(kCyan)
H_epsilon_DATA_nopid.SetLineColor(kMagenta)
H_epsilon_DUMMY.SetLineColor(kGreen)

H_epsilon_SIMC.Draw("E1")
H_epsilon_DATA.Draw("same, E1")
if DEBUG:
    H_epsilon_DATA_nocut.Draw("same, E1")
    H_epsilon_DATA_nopid.Draw("same, E1")
H_epsilon_DUMMY.Draw("same, E1")

b_int_epsilon_simc = int(H_epsilon_SIMC.Integral())
b_int_epsilon_data = int(H_epsilon_DATA.Integral())
b_int_epsilon_data_nocut = int(H_epsilon_DATA_nocut.Integral())
b_int_epsilon_data_nopid = int(H_epsilon_DATA_nopid.Integral())
b_int_epsilon_dummy = int(H_epsilon_DUMMY.Integral())

l_epsilon.AddEntry(H_epsilon_SIMC,"SIMC, INT = {:.0f}".format( b_int_epsilon_simc))
l_epsilon.AddEntry(H_epsilon_DATA,"DATA, INT = {:.0f}".format( b_int_epsilon_data))
if DEBUG:
    l_epsilon.AddEntry(H_epsilon_DATA_nocut,"DATA (no cut), INT = {:.0f}".format( b_int_epsilon_data_nocut))
    l_epsilon.AddEntry(H_epsilon_DATA_nopid,"DATA (no PID cut), INT = {:.0f}".format( b_int_epsilon_data_nopid))
l_epsilon.AddEntry(H_epsilon_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_epsilon_dummy))

l_epsilon.Draw()

Cepsilon.Print(outputpdf)

CMMp2 = TCanvas()
l_MMp2 = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_MMp2_DATA.SetLineColor(kRed)
H_MMp2_DATA_nocut.SetLineColor(kCyan)
H_MMp2_DATA_nopid.SetLineColor(kMagenta)
H_MMp2_DUMMY.SetLineColor(kGreen)

H_MMp2_SIMC.Draw("E1")
H_MMp2_DATA.Draw("same, E1")
if DEBUG:
    H_MMp2_DATA_nocut.Draw("same, E1")
    H_MMp2_DATA_nopid.Draw("same, E1")
H_MMp2_DUMMY.Draw("same, E1")

b_int_MMp2_simc = int(H_MMp2_SIMC.Integral())
b_int_MMp2_data = int(H_MMp2_DATA.Integral())
b_int_MMp2_data_nocut = int(H_MMp2_DATA_nocut.Integral())
b_int_MMp2_data_nopid = int(H_MMp2_DATA_nopid.Integral())
b_int_MMp2_dummy = int(H_MMp2_DUMMY.Integral())

l_MMp2.Draw()

CMMp2.Print(outputpdf)

Cph_q = TCanvas()
l_ph_q = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_ph_q_DATA.SetLineColor(kRed)
H_ph_q_DATA_nocut.SetLineColor(kCyan)
H_ph_q_DATA_nopid.SetLineColor(kMagenta)
H_ph_q_DUMMY.SetLineColor(kGreen)

H_ph_q_SIMC.Draw("E1")
H_ph_q_DATA.Draw("same, E1")
if DEBUG:
    H_ph_q_DATA_nocut.Draw("same, E1")
    H_ph_q_DATA_nopid.Draw("same, E1")
H_ph_q_DUMMY.Draw("same, E1")

b_int_ph_q_simc = int(H_ph_q_SIMC.Integral())
b_int_ph_q_data = int(H_ph_q_DATA.Integral())
b_int_ph_q_data_nocut = int(H_ph_q_DATA_nocut.Integral())
b_int_ph_q_data_nopid = int(H_ph_q_DATA_nopid.Integral())
b_int_ph_q_dummy = int(H_ph_q_DUMMY.Integral())

l_ph_q.Draw()

Cph_q.Print(outputpdf)

Cth_q = TCanvas()
l_th_q = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_th_q_DATA.SetLineColor(kRed)
H_th_q_DATA_nocut.SetLineColor(kCyan)
H_th_q_DATA_nopid.SetLineColor(kMagenta)
H_th_q_DUMMY.SetLineColor(kGreen)

H_th_q_SIMC.Draw("E1")
H_th_q_DATA.Draw("same, E1")
if DEBUG:
    H_th_q_DATA_nocut.Draw("same, E1")
    H_th_q_DATA_nopid.Draw("same, E1")
H_th_q_DUMMY.Draw("same, E1")

b_int_th_q_simc = int(H_th_q_SIMC.Integral())
b_int_th_q_data = int(H_th_q_DATA.Integral())
b_int_th_q_data_nocut = int(H_th_q_DATA_nocut.Integral())
b_int_th_q_data_nopid = int(H_th_q_DATA_nopid.Integral())
b_int_th_q_dummy = int(H_th_q_DUMMY.Integral())

l_th_q.Draw()

Cth_q.Print(outputpdf)

Cpmiss = TCanvas()
l_pmiss = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_pmiss_DATA.SetLineColor(kRed)
H_pmiss_DATA_nocut.SetLineColor(kCyan)
H_pmiss_DATA_nopid.SetLineColor(kMagenta)
H_pmiss_DUMMY.SetLineColor(kGreen)

tmp_b_mean_pmiss_simc = fit_gaussian(H_pmiss_SIMC,-0.1, 0.1, "simc")
b_mean_pmiss_simc = tmp_b_mean_pmiss_simc[0]
b_mean_err_pmiss_simc = tmp_b_mean_pmiss_simc[1]
tmp_b_mean_pmiss_data = fit_gaussian(H_pmiss_DATA,-0.1, 0.1, "data")
b_mean_pmiss_data = tmp_b_mean_pmiss_data[0]
b_mean_err_pmiss_data = tmp_b_mean_pmiss_data[1]
tmp_b_mean_pmiss_dummy = fit_gaussian(H_pmiss_DUMMY,-0.1, 0.1, "dummy")
b_mean_pmiss_dummy = tmp_b_mean_pmiss_dummy[0]
b_mean_err_pmiss_dummy = tmp_b_mean_pmiss_dummy[1]

H_pmiss_SIMC.Draw("E1")
H_pmiss_DATA.Draw("same, E1")
if DEBUG:
    H_pmiss_DATA_nocut.Draw("same, E1")
    H_pmiss_DATA_nopid.Draw("same, E1")
H_pmiss_DUMMY.Draw("same, E1")

b_int_pmiss_simc = int(H_pmiss_SIMC.Integral())
b_int_pmiss_data = int(H_pmiss_DATA.Integral())
b_int_pmiss_data_nocut = int(H_pmiss_DATA_nocut.Integral())
b_int_pmiss_data_nopid = int(H_pmiss_DATA_nopid.Integral())
b_int_pmiss_dummy = int(H_pmiss_DUMMY.Integral())

l_pmiss.AddEntry(H_pmiss_SIMC,"SIMC, INT = {:.0f}".format( b_int_pmiss_simc))
l_pmiss.AddEntry(H_pmiss_DATA,"DATA, INT = {:.0f}".format( b_int_pmiss_data))
l_pmiss.AddEntry(H_pmiss_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_pmiss_dummy))
l_pmiss.AddEntry(H_pmiss_SIMC,"SIMC, MEAN = {:.4e}\pm{:.4e}".format(b_mean_pmiss_simc, b_mean_err_pmiss_simc))
l_pmiss.AddEntry(H_pmiss_DATA,"DATA, MEAN = {:.4e}\pm{:.4e}".format(b_mean_pmiss_data, b_mean_err_pmiss_data))
l_pmiss.AddEntry(H_pmiss_DUMMY,"DUMMY, MEAN = {:.4e}\pm{:.4e}".format(b_mean_pmiss_dummy, b_mean_err_pmiss_dummy))

l_pmiss.Draw()

Cpmiss.Print(outputpdf)

Cemiss = TCanvas()
l_emiss = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_emiss_DATA.SetLineColor(kRed)
H_emiss_DATA_nocut.SetLineColor(kCyan)
H_emiss_DATA_nopid.SetLineColor(kMagenta)
H_emiss_DUMMY.SetLineColor(kGreen)

tmp_b_mean_emiss_simc = fit_gaussian(H_emiss_SIMC,-0.1, 0.1, "simc")
b_mean_emiss_simc = tmp_b_mean_emiss_simc[0]
b_mean_err_emiss_simc = tmp_b_mean_emiss_simc[1]
tmp_b_mean_emiss_data = fit_gaussian(H_emiss_DATA,-0.1, 0.1, "data")
b_mean_emiss_data = tmp_b_mean_emiss_data[0]
b_mean_err_emiss_data = tmp_b_mean_emiss_data[1]
tmp_b_mean_emiss_dummy = fit_gaussian(H_emiss_DUMMY,-0.1, 0.1, "dummy")
b_mean_emiss_dummy = tmp_b_mean_emiss_dummy[0]
b_mean_err_emiss_dummy = tmp_b_mean_emiss_dummy[1]

H_emiss_SIMC.Draw("E1")
H_emiss_DATA.Draw("same, E1")
if DEBUG:
    H_emiss_DATA_nocut.Draw("same, E1")
    H_emiss_DATA_nopid.Draw("same, E1")
H_emiss_DUMMY.Draw("same, E1")

b_int_emiss_simc = int(H_emiss_SIMC.Integral())
b_int_emiss_data = int(H_emiss_DATA.Integral())
b_int_emiss_data_nocut = int(H_emiss_DATA_nocut.Integral())
b_int_emiss_data_nopid = int(H_emiss_DATA_nopid.Integral())
b_int_emiss_dummy = int(H_emiss_DUMMY.Integral())

l_emiss.AddEntry(H_emiss_SIMC,"SIMC, INT = {:.0f}".format( b_int_emiss_simc))
l_emiss.AddEntry(H_emiss_DATA,"DATA, INT = {:.0f}".format( b_int_emiss_data))
l_emiss.AddEntry(H_emiss_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_emiss_dummy))
l_emiss.AddEntry(H_emiss_SIMC,"SIMC, MEAN = {:.4e}\pm{:.4e}".format(b_mean_emiss_simc, b_mean_err_emiss_simc))
l_emiss.AddEntry(H_emiss_DATA,"DATA, MEAN = {:.4e}\pm{:.4e}".format(b_mean_emiss_data, b_mean_err_emiss_data))
l_emiss.AddEntry(H_emiss_DUMMY,"DUMMY, MEAN = {:.4e}\pm{:.4e}".format(b_mean_emiss_dummy, b_mean_err_emiss_dummy))

l_emiss.Draw()

Cemiss.Print(outputpdf)

Cpmiss_x = TCanvas()
l_pmx = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_pmx_DATA.SetLineColor(kRed)
H_pmx_DATA_nocut.SetLineColor(kCyan)
H_pmx_DATA_nopid.SetLineColor(kMagenta)
H_pmx_DUMMY.SetLineColor(kGreen)

tmp_b_mean_pmx_simc = fit_gaussian(H_pmx_SIMC,-0.1, 0.1, "simc")
b_mean_pmx_simc = tmp_b_mean_pmx_simc[0]
b_mean_err_pmx_simc = tmp_b_mean_pmx_simc[1]
tmp_b_mean_pmx_data = fit_gaussian(H_pmx_DATA,-0.1, 0.1, "data")
b_mean_pmx_data = tmp_b_mean_pmx_data[0]
b_mean_err_pmx_data = tmp_b_mean_pmx_data[1]
tmp_b_mean_pmx_dummy = fit_gaussian(H_pmx_DUMMY,-0.1, 0.1, "dummy")
b_mean_pmx_dummy = tmp_b_mean_pmx_dummy[0]
b_mean_err_pmx_dummy = tmp_b_mean_pmx_dummy[1]

H_pmx_SIMC.Draw("E1")
H_pmx_DATA.Draw("same, E1")
if DEBUG:
    H_pmx_DATA_nocut.Draw("same, E1")
    H_pmx_DATA_nopid.Draw("same, E1")
H_pmx_DUMMY.Draw("same, E1")

b_int_pmx_simc = int(H_pmx_SIMC.Integral())
b_int_pmx_data = int(H_pmx_DATA.Integral())
b_int_pmx_data_nocut = int(H_pmx_DATA_nocut.Integral())
b_int_pmx_data_nopid = int(H_pmx_DATA_nopid.Integral())
b_int_pmx_dummy = int(H_pmx_DUMMY.Integral())

l_pmx.AddEntry(H_pmx_SIMC,"SIMC, INT = {:.0f}".format( b_int_pmx_simc))
l_pmx.AddEntry(H_pmx_DATA,"DATA, INT = {:.0f}".format( b_int_pmx_data))
l_pmx.AddEntry(H_pmx_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_pmx_dummy))
l_pmx.AddEntry(H_pmx_SIMC,"SIMC, MEAN = {:.4e}\pm{:.4e}".format(b_mean_pmx_simc, b_mean_err_pmx_simc))
l_pmx.AddEntry(H_pmx_DATA,"DATA, MEAN = {:.4e}\pm{:.4e}".format(b_mean_pmx_data, b_mean_err_pmx_data))
l_pmx.AddEntry(H_pmx_DUMMY,"DUMMY, MEAN = {:.4e}\pm{:.4e}".format(b_mean_pmx_dummy, b_mean_err_pmx_dummy))

l_pmx.Draw()

Cpmiss_x.Print(outputpdf)

Cpmiss_y = TCanvas()
l_pmy = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_pmy_DATA.SetLineColor(kRed)
H_pmy_DATA_nocut.SetLineColor(kCyan)
H_pmy_DATA_nopid.SetLineColor(kMagenta)
H_pmy_DUMMY.SetLineColor(kGreen)

tmp_b_mean_pmy_simc = fit_gaussian(H_pmy_SIMC,-0.1, 0.1, "simc")
b_mean_pmy_simc = tmp_b_mean_pmy_simc[0]
b_mean_err_pmy_simc = tmp_b_mean_pmy_simc[1]
tmp_b_mean_pmy_data = fit_gaussian(H_pmy_DATA,-0.1, 0.1, "data")
b_mean_pmy_data = tmp_b_mean_pmy_data[0]
b_mean_err_pmy_data = tmp_b_mean_pmy_data[1]
tmp_b_mean_pmy_dummy = fit_gaussian(H_pmy_DUMMY,-0.1, 0.1, "dummy")
b_mean_pmy_dummy = tmp_b_mean_pmy_dummy[0]
b_mean_err_pmy_dummy = tmp_b_mean_pmy_dummy[1]

H_pmy_SIMC.Draw("E1")
H_pmy_DATA.Draw("same, E1")
if DEBUG:
    H_pmy_DATA_nocut.Draw("same, E1")
    H_pmy_DATA_nopid.Draw("same, E1")
H_pmy_DUMMY.Draw("same, E1")

b_int_pmy_simc = int(H_pmy_SIMC.Integral())
b_int_pmy_data = int(H_pmy_DATA.Integral())
b_int_pmy_data_nocut = int(H_pmy_DATA_nocut.Integral())
b_int_pmy_data_nopid = int(H_pmy_DATA_nopid.Integral())
b_int_pmy_dummy = int(H_pmy_DUMMY.Integral())

l_pmy.AddEntry(H_pmy_SIMC,"SIMC, INT = {:.0f}".format( b_int_pmy_simc))
l_pmy.AddEntry(H_pmy_DATA,"DATA, INT = {:.0f}".format( b_int_pmy_data))
l_pmy.AddEntry(H_pmy_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_pmy_dummy))
l_pmy.AddEntry(H_pmy_SIMC,"SIMC, MEAN = {:.4e}\pm{:.4e}".format(b_mean_pmy_simc, b_mean_err_pmy_simc))
l_pmy.AddEntry(H_pmy_DATA,"DATA, MEAN = {:.4e}\pm{:.4e}".format(b_mean_pmy_data, b_mean_err_pmy_data))
l_pmy.AddEntry(H_pmy_DUMMY,"DUMMY, MEAN = {:.4e}\pm{:.4e}".format(b_mean_pmy_dummy, b_mean_err_pmy_dummy))

l_pmy.Draw()

Cpmiss_y.Print(outputpdf)

Cpmiss_z = TCanvas()
l_pmz = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_pmz_DATA.SetLineColor(kRed)
H_pmz_DATA_nocut.SetLineColor(kCyan)
H_pmz_DATA_nopid.SetLineColor(kMagenta)
H_pmz_DUMMY.SetLineColor(kGreen)

tmp_b_mean_pmz_simc = fit_gaussian(H_pmz_SIMC,-0.1, 0.1, "simc")
b_mean_pmz_simc = tmp_b_mean_pmz_simc[0]
b_mean_err_pmz_simc = tmp_b_mean_pmz_simc[1]
tmp_b_mean_pmz_data = fit_gaussian(H_pmz_DATA,-0.1, 0.1, "data")
b_mean_pmz_data = tmp_b_mean_pmz_data[0]
b_mean_err_pmz_data = tmp_b_mean_pmz_data[1]
tmp_b_mean_pmz_dummy = fit_gaussian(H_pmz_DUMMY,-0.1, 0.1, "dummy")
b_mean_pmz_dummy = tmp_b_mean_pmz_dummy[0]
b_mean_err_pmz_dummy = tmp_b_mean_pmz_dummy[1]

H_pmz_SIMC.Draw("E1")
H_pmz_DATA.Draw("same, E1")
if DEBUG:
    H_pmz_DATA_nocut.Draw("same, E1")
    H_pmz_DATA_nopid.Draw("same, E1")
H_pmz_DUMMY.Draw("same, E1")

b_int_pmz_simc = int(H_pmz_SIMC.Integral())
b_int_pmz_data = int(H_pmz_DATA.Integral())
b_int_pmz_data_nocut = int(H_pmz_DATA_nocut.Integral())
b_int_pmz_data_nopid = int(H_pmz_DATA_nopid.Integral())
b_int_pmz_dummy = int(H_pmz_DUMMY.Integral())

l_pmz.AddEntry(H_pmz_SIMC,"SIMC, INT = {:.0f}".format( b_int_pmz_simc))
l_pmz.AddEntry(H_pmz_DATA,"DATA, INT = {:.0f}".format( b_int_pmz_data))
l_pmz.AddEntry(H_pmz_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_pmz_dummy))
l_pmz.AddEntry(H_pmz_SIMC,"SIMC, MEAN = {:.4e}\pm{:.4e}".format(b_mean_pmz_simc, b_mean_err_pmz_simc))
l_pmz.AddEntry(H_pmz_DATA,"DATA, MEAN = {:.4e}\pm{:.4e}".format(b_mean_pmz_data, b_mean_err_pmz_data))
l_pmz.AddEntry(H_pmz_DUMMY,"DUMMY, MEAN = {:.4e}\pm{:.4e}".format(b_mean_pmz_dummy, b_mean_err_pmz_dummy))

l_pmz.Draw()

Cpmiss_z.Print(outputpdf)

CW = TCanvas()
l_W = ROOT.TLegend(0.115,0.55,0.33,0.9)

H_W_DATA.SetLineColor(kRed)
H_W_DATA_nocut.SetLineColor(kCyan)
H_W_DATA_nopid.SetLineColor(kMagenta)
H_W_DUMMY.SetLineColor(kGreen)

tmp_b_mean_W_simc = fit_gaussian(H_W_SIMC,0.7, 1.1, "simc")
b_mean_W_simc = tmp_b_mean_W_simc[0]
b_mean_err_W_simc = tmp_b_mean_W_simc[1]
tmp_b_mean_W_data = fit_gaussian(H_W_DATA,0.7, 1.1, "data")
b_mean_W_data = tmp_b_mean_W_data[0]
b_mean_err_W_data = tmp_b_mean_W_data[1]
tmp_b_mean_W_dummy = fit_gaussian(H_W_DUMMY,0.7, 1.1, "dummy")
b_mean_W_dummy = tmp_b_mean_W_dummy[0]
b_mean_err_W_dummy = tmp_b_mean_W_dummy[1]

H_W_SIMC.Draw("E1")
H_W_DATA.Draw("same, E1")
if DEBUG:
    H_W_DATA_nocut.Draw("same, E1")
    H_W_DATA_nopid.Draw("same, E1")
H_W_DUMMY.Draw("same, E1")

b_int_W_simc = int(H_W_SIMC.Integral())
b_int_W_data = int(H_W_DATA.Integral())
b_int_W_data_nocut = int(H_W_DATA_nocut.Integral())
b_int_W_data_nopid = int(H_W_DATA_nopid.Integral())
b_int_W_dummy = int(H_W_DUMMY.Integral())

l_W.AddEntry(H_W_SIMC,"SIMC, INT = {:.0f}".format( b_int_W_simc))
l_W.AddEntry(H_W_DATA,"DATA, INT = {:.0f}".format( b_int_W_data))
l_W.AddEntry(H_W_DUMMY,"DUMMY, INT = {:.0f}".format( b_int_W_dummy))
l_W.AddEntry(H_W_SIMC,"SIMC, MEAN = {:.4e}\pm{:.4e}".format(b_mean_W_simc, b_mean_err_W_simc))
l_W.AddEntry(H_W_DATA,"DATA, MEAN = {:.4e}\pm{:.4e}".format(b_mean_W_data, b_mean_err_W_data))
l_W.AddEntry(H_W_DUMMY,"DUMMY, MEAN = {:.4e}\pm{:.4e}".format(b_mean_W_dummy, b_mean_err_W_dummy))

l_W.Draw()

CW.Print(outputpdf + ')')

print("W_simc err_W_simc W_data err_W_data pmz_simc err_pmz_simc pmz_data err_pmz_data pmy_simc err_pmy_simc pmy_data err_pmy_data pmx_simc err_pmx_simc pmx_data err_pmx_data emiss_simc err_emiss_simc emiss_data err_emiss_data")
print("{:.4e} {:.4e} {:.4e} {:.4e} {:.4e} {:.4e} {:.4e} {:.4e} {:.4e} {:.4e} {:.4e} {:.4e} {:.4e} {:.4e} {:.4e} {:.4e} {:.4e} {:.4e} {:.4e} {:.4e}".format(b_mean_W_simc,b_mean_err_W_simc,b_mean_W_data,b_mean_err_W_data,b_mean_pmz_simc,b_mean_err_pmz_simc,b_mean_pmz_data,b_mean_err_pmz_data,b_mean_pmy_simc,b_mean_err_pmy_simc,b_mean_pmy_data,b_mean_err_pmy_data,b_mean_pmx_simc,b_mean_err_pmx_simc,b_mean_pmx_data,b_mean_err_pmx_data,b_mean_emiss_simc,b_mean_err_emiss_simc,b_mean_emiss_data,b_mean_err_emiss_data))

print("\n\nY_data = {0:.2e}".format(yield_data))
print("Y_simc = {0:.2e}".format(yield_simc))
print("\nR = {0:.2e}".format(rel_yield))

#############################################################################################################################################
# Create new root file with trees representing cut simc and data used above. Good for those who see python as...problematic

outHistFile = ROOT.TFile.Open(foutname, "RECREATE")
d_Data = outHistFile.mkdir("Data")
d_Data_nocut = outHistFile.mkdir("Data (no cut)")
d_Data_nopid = outHistFile.mkdir("Data (no PID cut)")
d_Dummy = outHistFile.mkdir("Dummy")
d_Dummy_nocut = outHistFile.mkdir("Dummy (no cut)")
d_Dummy_nopid = outHistFile.mkdir("Dummy (no PID cut)")
d_Simc = outHistFile.mkdir("SIMC")

d_Data.cd()
H_hsdelta_DATA.Write()
H_hsxptar_DATA.Write()
H_hsyptar_DATA.Write()
H_ssxfp_DATA.Write()
H_ssyfp_DATA.Write()
H_ssxpfp_DATA.Write()
H_ssypfp_DATA.Write()
H_hsxfp_DATA.Write()
H_hsyfp_DATA.Write()
H_hsxpfp_DATA.Write()
H_hsypfp_DATA.Write()
H_ssdelta_DATA.Write()
H_ssxptar_DATA.Write()
H_ssyptar_DATA.Write()
H_q_DATA.Write()
H_Q2_DATA.Write()
H_epsilon_DATA.Write()
H_MMp2_DATA.Write()
H_th_DATA.Write()
H_ph_DATA.Write()
H_ph_q_DATA.Write()
H_th_q_DATA.Write()
H_ph_recoil_DATA.Write()
H_th_recoil_DATA.Write()
H_pmiss_DATA.Write()
H_emiss_DATA.Write()
H_pmx_DATA.Write()
H_pmy_DATA.Write()
H_pmz_DATA.Write()
H_W_DATA.Write()
H_ct_ep_DATA.Write()

d_Data_nocut.cd()
H_hsdelta_DATA_nocut.Write()
H_hsxptar_DATA_nocut.Write()
H_hsyptar_DATA_nocut.Write()
H_ssxfp_DATA_nocut.Write()
H_ssyfp_DATA_nocut.Write()
H_ssxpfp_DATA_nocut.Write()
H_ssypfp_DATA_nocut.Write()
H_hsxfp_DATA_nocut.Write()
H_hsyfp_DATA_nocut.Write()
H_hsxpfp_DATA_nocut.Write()
H_hsypfp_DATA_nocut.Write()
H_ssdelta_DATA_nocut.Write()
H_ssxptar_DATA_nocut.Write()
H_ssyptar_DATA_nocut.Write()
H_q_DATA_nocut.Write()
H_Q2_DATA_nocut.Write()
H_epsilon_DATA_nocut.Write()
H_MMp2_DATA_nocut.Write()
H_th_DATA_nocut.Write()
H_ph_DATA_nocut.Write()
H_ph_q_DATA_nocut.Write()
H_th_q_DATA_nocut.Write()
H_ph_recoil_DATA_nocut.Write()
H_th_recoil_DATA_nocut.Write()
H_pmiss_DATA_nocut.Write()
H_emiss_DATA_nocut.Write()
H_pmx_DATA_nocut.Write()
H_pmy_DATA_nocut.Write()
H_pmz_DATA_nocut.Write()
H_W_DATA_nocut.Write()
H_ct_ep_DATA_nocut.Write()

d_Data_nopid.cd()
H_hsdelta_DATA_nopid.Write()
H_hsxptar_DATA_nopid.Write()
H_hsyptar_DATA_nopid.Write()
H_ssxfp_DATA_nopid.Write()
H_ssyfp_DATA_nopid.Write()
H_ssxpfp_DATA_nopid.Write()
H_ssypfp_DATA_nopid.Write()
H_hsxfp_DATA_nopid.Write()
H_hsyfp_DATA_nopid.Write()
H_hsxpfp_DATA_nopid.Write()
H_hsypfp_DATA_nopid.Write()
H_ssdelta_DATA_nopid.Write()
H_ssxptar_DATA_nopid.Write()
H_ssyptar_DATA_nopid.Write()
H_q_DATA_nopid.Write()
H_Q2_DATA_nopid.Write()
H_epsilon_DATA_nopid.Write()
H_MMp2_DATA_nopid.Write()
H_th_DATA_nopid.Write()
H_ph_DATA_nopid.Write()
H_ph_q_DATA_nopid.Write()
H_th_q_DATA_nopid.Write()
H_ph_recoil_DATA_nopid.Write()
H_th_recoil_DATA_nopid.Write()
H_pmiss_DATA_nopid.Write()
H_emiss_DATA_nopid.Write()
H_pmx_DATA_nopid.Write()
H_pmy_DATA_nopid.Write()
H_pmz_DATA_nopid.Write()
H_W_DATA_nopid.Write()
H_ct_ep_DATA_nopid.Write()

d_Dummy.cd()
H_hsdelta_DUMMY.Write()
H_hsxptar_DUMMY.Write()
H_hsyptar_DUMMY.Write()
H_ssxfp_DUMMY.Write()
H_ssyfp_DUMMY.Write()
H_ssxpfp_DUMMY.Write()
H_ssypfp_DUMMY.Write()
H_hsxfp_DUMMY.Write()
H_hsyfp_DUMMY.Write()
H_hsxpfp_DUMMY.Write()
H_hsypfp_DUMMY.Write()
H_ssdelta_DUMMY.Write()
H_ssxptar_DUMMY.Write()
H_ssyptar_DUMMY.Write()
H_q_DUMMY.Write()
H_Q2_DUMMY.Write()
H_epsilon_DUMMY.Write()
H_MMp2_DUMMY.Write()
H_th_DUMMY.Write()
H_ph_DUMMY.Write()
H_ph_q_DUMMY.Write()
H_th_q_DUMMY.Write()
H_ph_recoil_DUMMY.Write()
H_th_recoil_DUMMY.Write()
H_pmiss_DUMMY.Write()
H_emiss_DUMMY.Write()
H_pmx_DUMMY.Write()
H_pmy_DUMMY.Write()
H_pmz_DUMMY.Write()
H_W_DUMMY.Write()
H_ct_ep_DUMMY.Write()

d_Dummy_nocut.cd()
H_hsdelta_DUMMY_nocut.Write()
H_hsxptar_DUMMY_nocut.Write()
H_hsyptar_DUMMY_nocut.Write()
H_ssxfp_DUMMY_nocut.Write()
H_ssyfp_DUMMY_nocut.Write()
H_ssxpfp_DUMMY_nocut.Write()
H_ssypfp_DUMMY_nocut.Write()
H_hsxfp_DUMMY_nocut.Write()
H_hsyfp_DUMMY_nocut.Write()
H_hsxpfp_DUMMY_nocut.Write()
H_hsypfp_DUMMY_nocut.Write()
H_ssdelta_DUMMY_nocut.Write()
H_ssxptar_DUMMY_nocut.Write()
H_ssyptar_DUMMY_nocut.Write()
H_q_DUMMY_nocut.Write()
H_Q2_DUMMY_nocut.Write()
H_epsilon_DUMMY_nocut.Write()
H_MMp2_DUMMY_nocut.Write()
H_th_DUMMY_nocut.Write()
H_ph_DUMMY_nocut.Write()
H_ph_q_DUMMY_nocut.Write()
H_th_q_DUMMY_nocut.Write()
H_ph_recoil_DUMMY_nocut.Write()
H_th_recoil_DUMMY_nocut.Write()
H_pmiss_DUMMY_nocut.Write()
H_emiss_DUMMY_nocut.Write()
H_pmx_DUMMY_nocut.Write()
H_pmy_DUMMY_nocut.Write()
H_pmz_DUMMY_nocut.Write()
H_W_DUMMY_nocut.Write()
H_ct_ep_DUMMY_nocut.Write()

d_Dummy_nopid.cd()
H_hsdelta_DUMMY_nopid.Write()
H_hsxptar_DUMMY_nopid.Write()
H_hsyptar_DUMMY_nopid.Write()
H_ssxfp_DUMMY_nopid.Write()
H_ssyfp_DUMMY_nopid.Write()
H_ssxpfp_DUMMY_nopid.Write()
H_ssypfp_DUMMY_nopid.Write()
H_hsxfp_DUMMY_nopid.Write()
H_hsyfp_DUMMY_nopid.Write()
H_hsxpfp_DUMMY_nopid.Write()
H_hsypfp_DUMMY_nopid.Write()
H_ssdelta_DUMMY_nopid.Write()
H_ssxptar_DUMMY_nopid.Write()
H_ssyptar_DUMMY_nopid.Write()
H_q_DUMMY_nopid.Write()
H_Q2_DUMMY_nopid.Write()
H_epsilon_DUMMY_nopid.Write()
H_MMp2_DUMMY_nopid.Write()
H_th_DUMMY_nopid.Write()
H_ph_DUMMY_nopid.Write()
H_ph_q_DUMMY_nopid.Write()
H_th_q_DUMMY_nopid.Write()
H_ph_recoil_DUMMY_nopid.Write()
H_th_recoil_DUMMY_nopid.Write()
H_pmiss_DUMMY_nopid.Write()
H_emiss_DUMMY_nopid.Write()
H_pmx_DUMMY_nopid.Write()
H_pmy_DUMMY_nopid.Write()
H_pmz_DUMMY_nopid.Write()
H_W_DUMMY_nopid.Write()
H_ct_ep_DUMMY_nopid.Write()

d_Simc.cd()
H_hsdelta_SIMC.Write()
H_hsxptar_SIMC.Write()
H_hsyptar_SIMC.Write()
H_ssxfp_SIMC.Write()
H_ssyfp_SIMC.Write()
H_ssxpfp_SIMC.Write()
H_ssypfp_SIMC.Write()
H_hsxfp_SIMC.Write()
H_hsyfp_SIMC.Write()
H_hsxpfp_SIMC.Write()
H_hsypfp_SIMC.Write()
H_ssdelta_SIMC.Write()
H_ssxptar_SIMC.Write()
H_ssyptar_SIMC.Write()
H_q_SIMC.Write()
H_Q2_SIMC.Write()
H_epsilon_SIMC.Write()
H_MMp2_SIMC.Write()
H_th_SIMC.Write()
H_ph_SIMC.Write()
H_pmiss_SIMC.Write()
H_emiss_SIMC.Write()
H_pmx_SIMC.Write()
H_pmy_SIMC.Write()
H_pmz_SIMC.Write()
H_W_SIMC.Write()

outHistFile.Close()
InFile_DATA.Close()
InFile_DUMMY.Close()
InFile_SIMC.Close()
print ("Processing Complete")
