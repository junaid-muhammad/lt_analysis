#! /usr/bin/python

#
# Description:
# ================================================================
# Time-stamp: "2023-08-04 12:55:18 trottar"
# ================================================================
#
# Author:  Richard L. Trotta III <trotta@cua.edu>
#
# Copyright (c) trottar
#

##################################################################################################################################################

# Import relevant packages
import uproot as up
import numpy as np
import root_numpy as rnp
import ROOT
import scipy
import scipy.integrate as integrate
from scipy.integrate import quad
import matplotlib.pyplot as plt
from collections import defaultdict
import sys, math, os, subprocess
from array import array
from ROOT import TCanvas, TColor, TGaxis, TH1F, TH2F, TPad, TStyle, gStyle, gPad, TGaxis, TLine, TMath, TPaveText, TArc, TGraphPolar, TLatex, TH2Poly
from ROOT import kBlack, kCyan, kRed, kGreen, kMagenta
from functools import reduce

################################################################################################################################################
'''
ltsep package import and pathing definitions
'''

# Import package for cuts
from ltsep import Root

lt=Root(os.path.realpath(__file__),"Plot_Prod")

# Add this to all files for more dynamic pathing
USER=lt.USER # Grab user info for file finding
HOST=lt.HOST
REPLAYPATH=lt.REPLAYPATH
UTILPATH=lt.UTILPATH
LTANAPATH=lt.LTANAPATH
ANATYPE=lt.ANATYPE
OUTPATH=lt.OUTPATH

##################################################################################################################################################
# Importing utility functions

from utility import weight_bins

##################################################################################################################################################

def calculate_yield(histlist, inpDict, DataType):
        
    # Initialize NumPy arrays before the loop
    t = np.array([])
    phi_deg = np.array([])
    Q2 = np.array([])
    W = np.array([])
    MM = np.array([])

    for hist in histlist:

        # Convert to NumPy arrays
        t = np.append(t, weight_bins(hist["H_t_{}".format(DataType)]))
        phi_deg = np.append(phi_deg, [(phi + math.pi)*(180 / math.pi) for phi in weight_bins(hist["H_ph_q_{}".format(DataType)])])
        Q2 = np.append(Q2, weight_bins(hist["H_Q2_{}".format(DataType)]))
        W = np.append(W, weight_bins(hist["H_W_{}".format(DataType)]))
        MM = np.append(MM, weight_bins(hist["H_MM_{}".format(DataType)]))

    for hist in histlist:
        t_bins = hist["t_bins"]
        phi_bins = hist["phi_bins"]

    aver_lst = []
    for j in range(len(t_bins) - 1):
        tbin_indices = np.where((float(t_bins[j]) <= t) & (t < float(t_bins[j + 1])))[0]
        if len(tbin_indices) > 0:
            tbin_index = j
            Q2_val = Q2[tbin_indices]
            W_val = W[tbin_indices]
            t_val = t[tbin_indices]
            # Append tbin_index, Q2, W, and t to aver_lst
            for k in range(len(phi_bins) - 1):
                phibin_indices = np.where((float(phi_bins[k]) <= phi_deg) & (phi_deg < float(phi_bins[k + 1])))[0]
                if len(phibin_indices) > 0:
                    phibin_index = k
                    # t binning
                    #MM_val = MM[tbin_indices]
                    # t+phi binning
                    # Combine tbin_indices and phibin_indices using logical AND
                    combined_indices = np.intersect1d(tbin_indices, phibin_indices)
                    MM_val = MM[combined_indices]
                    print("________________",tbin_index, phibin_index, len(MM), len(Q2), len(W), len(t),"________________")
                    print("----------------",tbin_index, phibin_index, len(MM_val), len(Q2_val), len(W_val), len(t_val),"----------------")
                    aver_lst.append((tbin_index, phibin_index, Q2_val, W_val, t_val, MM_val))
                    print("________________",aver_lst,"________________\n")

    # Group the tuples by the first two elements using defaultdict
    groups = defaultdict(list)
    for tup in aver_lst:
        key = (tup[0], tup[1])
        # Calculate averages for each Q2, W, t value per t-bin
        Q2_aver = [np.average(tup[2])]
        W_aver = [np.average(tup[3])]
        t_aver = [np.average(tup[4])]
        # Find the number of events per t/phi bin
        try:
            nevents = abs(integrate.simps(tup[5]))
        except IndexError:
            nevents = 0
        groups[key] = {"Q2_aver" : Q2_aver, "W_aver" : W_aver, "t_aver" : t_aver, "nevents" : nevents}

    print(groups)

    return {"binned_{}".format(DataType) : groups}
