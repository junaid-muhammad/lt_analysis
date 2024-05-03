#! /usr/bin/python

#
# Description:
# ================================================================
# Time-stamp: "2024-05-03 14:40:55 trottar"
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

lt=Root(os.path.realpath(__file__),"Plot_LTSep")

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

sys.path.append("utility")
from utility import flatten_hist

################################################################################################################################################

def find_bins(histlist, inpDict):

    ################################################################################################################################################
    
    ParticleType = inpDict["ParticleType"]

    tmin = inpDict["tmin"]
    tmax = inpDict["tmax"]
        
    ################################################################################################################################################
    # Define root file trees of interest

    # Initialize NumPy arrays
    H_t_Right = np.array([])
    H_t_Left = np.array([])
    H_t_Center = np.array([])

    H_phi_Right = np.array([])
    H_phi_Left = np.array([])
    H_phi_Center = np.array([])
    
    for i,hist in enumerate(histlist):
        
        t = flatten_hist(hist["H_t_DATA"])
        phi_deg = [(phi)*(180 / math.pi) for phi in flatten_hist(hist["H_ph_q_DATA"])]
        
        if hist["phi_setting"] == 'Right':
            H_t_Right = np.append(H_t_Right, t)
            H_phi_Right = np.append(H_phi_Right, phi_deg)

        elif hist["phi_setting"] == 'Left':
            H_t_Left = np.append(H_t_Left, t)
            H_phi_Left = np.append(H_phi_Left, phi_deg)

        elif hist["phi_setting"] == 'Center':
            H_t_Center = np.append(H_t_Center, t)
            H_phi_Center = np.append(H_phi_Center, phi_deg)

    ################################################################################################################################################

    # Concatenate the H_t arrays for Right, Left, and Center
    H_t_BinTest = np.concatenate((H_t_Right, H_t_Left, H_t_Center))

    # Apply proper boundaries for t
    H_t_BinTest = np.append(H_t_BinTest, tmin)
    H_t_BinTest = np.append(H_t_BinTest, tmax)

    # Concatenate the H_phi arrays for Right, Left, and Center
    H_phi_BinTest = np.concatenate((H_phi_Right, H_phi_Left, H_phi_Center))
    
    def find_phibins(H_phi_BinTest):

        print("\nFinding phi bins...")
        bin_edges = np.linspace(0.0, 360.0, inpDict["NumPhiBins"]+1)
        n, bins = np.histogram(H_phi_BinTest, bin_edges)

        for i,val in enumerate(n):
            print("Bin {} from {:.1f} to {:.1f} has {} events".format(i+1, bins[i], bins[i+1], n[i]))
        
        bin_centers = (bins[:-1] + bins[1:]) / 2

        print("phi_bins = ", bins)
        
        # Write phibin_interval for lt_analysis scripts
        lines = []
        with open("{}/src/{}/phi_bin_interval_Q{}W{}".format(LTANAPATH, ParticleType, inpDict["Q2"].replace("p",""), inpDict["W"].replace("p","")), "w") as file:
            file.write("{}\t{}\t{}\t{}\n".format(inpDict["Q2"].replace("p","."),inpDict["W"].replace("p","."),inpDict["NumtBins"],inpDict["NumPhiBins"]))            
            for i,phi in enumerate(bins):
                lines.append("\t{}".format(float(phi)))
            file.writelines(lines)

        return [n,bins]

    def find_tbins(H_t_BinTest):


        ################################################################################################################################################
 
        '''
        def histedges_equalN(x, nbin):
            npt = len(x) - 1  # npt-1 because starting at 0
            indices = np.linspace(0, npt, nbin+1).astype(int)
            sorted_x = np.sort(x)
            equalN_values = sorted_x[indices]
            return equalN_values
        '''
        
        def histedges_equalN(x, nbin, tolerance=1e-3, max_iterations=10):
            # Account for bin range
            nbin += 1
            npt = len(x)  # Total number of data points
            n_per_bin = npt // nbin  # Calculate the number of events per bin
            remainder = npt % nbin  # Calculate remainder for uneven division

            # Initialize bin edges with the minimum and maximum data points
            bin_edges = [np.min(x)]
            bin_edges.extend(np.linspace(np.min(x), np.max(x), num=nbin))

            # Perform iterations to adjust bin edges
            for _ in range(max_iterations):
                # Calculate the number of events in each bin
                counts, _ = np.histogram(x, bins=bin_edges)

                # Calculate the cumulative sum of counts
                cum_counts = np.cumsum(counts)

                # Calculate the difference between target and actual counts per bin
                diff_counts = n_per_bin - counts[:-1]

                # Find the bins where the difference exceeds the tolerance
                exceed_tolerance = np.abs(diff_counts) > tolerance

                # If all differences are within tolerance, break the loop
                if not np.any(exceed_tolerance):
                    break

                # Adjust bin edges based on the differences
                for i, exceed in enumerate(exceed_tolerance):
                    if exceed:
                        if diff_counts[i] > 0:
                            # Increase bin edge
                            bin_edges[i + 1] += tolerance / 2
                        else:
                            # Decrease bin edge
                            bin_edges[i + 1] -= tolerance / 2

            return np.array(bin_edges)

        print("\nFinding t bins...")
        # Histogram takes the array data set and the bins as input
        # The bins are determined by a linear interpolation (see function above)
        # This returns the binned data with equal number of events per bin
        print("H_t_BinTest: ", H_t_BinTest, type(H_t_BinTest))
        bin_edges = histedges_equalN(H_t_BinTest, inpDict["NumtBins"])
        n, bins = np.histogram(H_t_BinTest, bin_edges)

        ##############
        # HARD CODED #
        ##############
        # Set custom bins
        #custom_bins = [tmin, 0.2, 0.23, 0.26, 0.3, tmax]
        #n, bins = np.histogram(H_t_BinTest, np.array(custom_bins))
        ##############
        ##############
        ##############
        
        for i,val in enumerate(n):
            print("Bin {} from {:.3f} to {:.3f} has {} events".format(i+1, bins[i], bins[i+1], n[i]))

        # Stripping tmin and tmax
        #bin_centers = bins[1:-1]
        
        bin_centers = (bins[:-1] + bins[1:]) / 2
        
        print("t_bins = ", bins)
        
        # Write t_bin_interval for lt_analysis scripts
        lines = []
        with open("{}/src/{}/t_bin_interval_Q{}W{}".format(LTANAPATH, ParticleType, inpDict["Q2"].replace("p",""), inpDict["W"].replace("p","")), "w") as file:
            file.write("{}\t{}\t{}\t{}\n".format(inpDict["Q2"].replace("p","."),inpDict["W"].replace("p","."),inpDict["NumtBins"],inpDict["NumPhiBins"]))
            for i,t in enumerate(bins):
                lines.append("\t{:.2f}".format(float(t)))
            file.writelines(lines)

        return [n,bins]
    
    return [find_phibins(H_phi_BinTest), find_tbins(H_t_BinTest)]

def check_bins(histlist, inpDict):

    ################################################################################################################################################
    
    ParticleType = inpDict["ParticleType"]

    tmin = inpDict["tmin"]
    tmax = inpDict["tmax"]

    t_bins = histlist[0]["t_bins"]
    phi_bins = histlist[0]["phi_bins"]

    ################################################################################################################################################
    # Define root file trees of interest

    # Initialize NumPy arrays
    H_t_Right = np.array([])
    H_t_Left = np.array([])
    H_t_Center = np.array([])

    H_phi_Right = np.array([])
    H_phi_Left = np.array([])
    H_phi_Center = np.array([])
    
    for i,hist in enumerate(histlist):
        
        t = flatten_hist(hist["H_t_DATA"])
        phi_deg = [(phi)*(180 / math.pi) for phi in flatten_hist(hist["H_ph_q_DATA"])]
        
        if hist["phi_setting"] == 'Right':
            H_t_Right = np.append(H_t_Right, t)
            H_phi_Right = np.append(H_phi_Right, phi_deg)

        elif hist["phi_setting"] == 'Left':
            H_t_Left = np.append(H_t_Left, t)
            H_phi_Left = np.append(H_phi_Left, phi_deg)

        elif hist["phi_setting"] == 'Center':
            H_t_Center = np.append(H_t_Center, t)
            H_phi_Center = np.append(H_phi_Center, phi_deg)

    ################################################################################################################################################

    # Concatenate the H_t arrays for Right, Left, and Center
    H_t_BinTest = np.concatenate((H_t_Right, H_t_Left, H_t_Center))

    # Apply proper boundaries for t
    H_t_BinTest = np.append(H_t_BinTest, tmin)
    H_t_BinTest = np.append(H_t_BinTest, tmax)

    # Concatenate the H_phi arrays for Right, Left, and Center
    H_phi_BinTest = np.concatenate((H_phi_Right, H_phi_Left, H_phi_Center))
    
    def find_phibins(H_phi_BinTest):

        print("\nFinding phi bins...")
        n, bins = np.histogram(H_phi_BinTest, phi_bins)

        for i,val in enumerate(n):
            print("Bin {} from {:.1f} to {:.1f} has {} events".format(i+1, bins[i], bins[i+1], n[i]))
        
        print("phi_bins = ", bins)
        
    def find_tbins(H_t_BinTest):
        
        print("\nFinding t bins...")
        n, bins = np.histogram(H_t_BinTest, t_bins)
        
        for i,val in enumerate(n):
            print("Bin {} from {:.3f} to {:.3f} has {} events".format(i+1, bins[i], bins[i+1], n[i]))
        
        print("t_bins = ", bins)
    

    find_phibins(H_phi_BinTest)
    find_tbins(H_t_BinTest)
        
