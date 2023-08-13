#! /usr/bin/python

#
# Description:
# ================================================================
# Time-stamp: "2023-08-13 16:09:34 trottar"
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
import csv
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

def calculate_aver_data(kin_type, hist_data, hist_dummy, phi_data, phi_bins, t_bins, eff_charge, EPSSET, Q2, W, ParticleType):
    
    # Initialize lists for binned_phi_data, binned_hist_data, and binned_hist_dummy
    binned_phi_data = []
    binned_hist_data = []
    binned_hist_dummy = []
    
    phi_bins = np.append(phi_bins, 0.0) # Needed to fully finish loop over bins
    # Loop through bins in phi_data and identify events in specified bins
    for j in range(len(phi_bins)-1):
        tmp_phi_data = [[],[]]
        tmp_hist_data = [[],[]]
        tmp_hist_dummy = [[],[]]
        for bin_index in range(1, phi_data.GetNbinsX() + 1):
            bin_center = (phi_data.GetBinCenter(bin_index)+math.pi)*(180 / math.pi)
            if phi_bins[j] <= bin_center <= phi_bins[j+1]:
                if hist_data.GetBinContent(bin_index) > 0:
                    #print("Checking if {} <= {} <= {}".format(phi_bins[j], bin_center, phi_bins[j+1]))
                    #print("Bin {}, Hist bin {} Passed with content {}".format(j, hist_data.GetBinCenter(bin_index), hist_data.GetBinContent(bin_index)))
                    tmp_phi_data[0].append(phi_data.GetBinCenter(bin_index))
                    tmp_phi_data[1].append(phi_data.GetBinContent(bin_index))
                    tmp_hist_data[0].append(hist_data.GetBinCenter(bin_index))
                    tmp_hist_data[1].append(hist_data.GetBinContent(bin_index))
                    tmp_hist_dummy[0].append(hist_dummy.GetBinCenter(bin_index))
                    tmp_hist_dummy[1].append(hist_dummy.GetBinContent(bin_index))
        binned_phi_data.append(tmp_phi_data)
        binned_hist_data.append(tmp_hist_data)
        binned_hist_dummy.append(tmp_hist_dummy)
    phi_bins = phi_bins[:-1] # Pop last element used for loop

    aver_hist = []
    yield_hist = []
    binned_sub_data = [[], []]
    i = 0  # iter
    print("-" * 25)
    print("\n\nFinding average {} per phi-bin...".format(kin_type))
    print("-" * 25)

    # Create lists to store values for CSV export
    data_for_csv = []

    # Subtract binned_hist_dummy from binned_hist_data element-wise
    for data, dummy in zip(binned_hist_data, binned_hist_dummy):
        bin_val_data, hist_val_data = data
        bin_val_dummy, hist_val_dummy = dummy
        sub_val = np.subtract(hist_val_data, hist_val_dummy)
        if sub_val.size != 0:
            # Calculate the weighted sum of frequencies and divide by the total count
            weighted_sum = np.sum(sub_val * bin_val_data)
            total_count = np.sum(sub_val)
            average = weighted_sum / total_count
            yield_val = total_count / eff_charge
            aver_hist.append(average)
            yield_hist.append(yield_val)

            # Append values to CSV list
            data_for_csv.append([phi_bins[i], total_count, yield_val, EPSSET])  # Replace 'EPSSET' with the actual value

            print("Weighted Sum:", weighted_sum)
            print("Total Count:", total_count)
            print("Average for phi-bin {}:".format(i), average)
            print("Yield for phi-bin {}:".format(i), yield_val)
            binned_sub_data[0].append(bin_val_data)
            binned_sub_data[1].append(sub_val)
        else:
            aver_hist.append(0)
            total_count = 0
            yield_val = 0
            aver_hist.append(0)
            yield_hist.append(0)

            # Append values to CSV list
            data_for_csv.append([phi_bins[i], total_count, yield_val, EPSSET])  # Replace 'EPSSET' with the actual value
            
            print("Weighted Sum: N/A")
            print("Total Count: N/A")
            print("Average for phi-bin {}: 0.0".format(i))
            print("Yield for phi-bin {}: 0.0".format(i))
            binned_sub_data[0].append(bin_val_data)
            binned_sub_data[1].append([0] * len(bin_val_data))
        i += 1
        print("-" * 25)

    # Write values to a single CSV file with columns
    csv_filename = '{}_Q{}W{}.csv'.format(ParticleType, Q2, W)
    file_exists = os.path.exists(csv_filename)

    existing_lines = set()
    if file_exists:
        with open(csv_filename, 'r') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header
            existing_lines = set(row[0] for row in reader)

    with open(csv_filename, 'a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['total_count', 'yield_val', 'EPSSET'])
        for row in data_for_csv:
            if row[0] not in existing_lines:
                writer.writerow(row)
                existing_lines.add(row[0])
    print("Data saved to {}".format(csv_filename))

    # Print statements to check sizes
    print("\nSize of binned_phi_data:", len(binned_phi_data))
    print("Size of binned_hist_data:", len(binned_hist_data))
    print("Size of binned_hist_dummy:", len(binned_hist_dummy))
    print("Size of binned_sub_data:", len(binned_sub_data[1]))
    print("Size of aver_hist:", len(aver_hist))
    print("Size of phi_bins:", len(phi_bins))

    dict_lst = []
    for j in range(len(phi_bins) - 1):
        phibin_index = j
        for k in range(len(t_bins) - 1):
            tbin_index = k
            hist_val = [binned_sub_data[0][j], binned_sub_data[1][j]]
            aver_val = aver_hist[j]
            print("----------------------",(phibin_index, tbin_index, len(hist_val), aver_val))
            dict_lst.append((phibin_index, tbin_index, hist_val, aver_val))

    # Group the tuples by the first two elements using defaultdict
    groups = defaultdict(list)
    for tup in dict_lst:
        key = (tup[0], tup[1])
        groups[key] = {
            "{}_arr".format(kin_type) : tup[2],
            "{}_aver".format(kin_type) : tup[3],
        }            
        
    
    return groups

def calculate_aver_simc(kin_type, hist_data, phi_data, phi_bins, t_bins):
    
    # Initialize lists for binned_phi_data, and binned_hist_data
    binned_phi_data = []
    binned_hist_data = []
    
    phi_bins = np.append(phi_bins, 0.0) # Needed to fully finish loop over bins
    # Loop through bins in phi_data and identify events in specified bins
    for j in range(len(phi_bins)-1):
        tmp_phi_data = [[],[]]
        tmp_hist_data = [[],[]]
        for bin_index in range(1, phi_data.GetNbinsX() + 1):
            bin_center = phi_data.GetBinCenter(bin_index)
            if phi_bins[j] <= bin_center <= phi_bins[j+1]:
                if hist_data.GetBinContent(bin_index) > 0:
                    #print("Checking if {} <= {} <= {}".format(phi_bins[j], bin_center, phi_bins[j+1]))
                    #print("Bin {}, Hist bin {} Passed with content {}".format(j, hist_data.GetBinCenter(bin_index), hist_data.GetBinContent(bin_index)))
                    tmp_phi_data[0].append(phi_data.GetBinCenter(bin_index))
                    tmp_phi_data[1].append(phi_data.GetBinContent(bin_index))
                    tmp_hist_data[0].append(hist_data.GetBinCenter(bin_index))
                    tmp_hist_data[1].append(hist_data.GetBinContent(bin_index))
        binned_phi_data.append(tmp_phi_data)
        binned_hist_data.append(tmp_hist_data)
    phi_bins = phi_bins[:-1] # Pop last element used for loop

    aver_hist = []
    yield_hist = []
    binned_sub_data = [[], []]
    i = 0  # iter
    print("-" * 25)
    print("\n\nFinding average {} per phi-bin...".format(kin_type))
    print("-" * 25)

    # Create lists to store values for CSV export
    total_count_list = []
    yield_val_list = []
    epset_list = []

    # Subtract binned_hist_dummy from binned_hist_data element-wise
    for data, dummy in zip(binned_hist_data, binned_hist_dummy):
        bin_val_data, hist_val_data = data
        bin_val_dummy, hist_val_dummy = dummy
        sub_val = np.subtract(hist_val_data, hist_val_dummy)
        if sub_val.size != 0:
            # Calculate the weighted sum of frequencies and divide by the total count
            weighted_sum = np.sum(sub_val * bin_val_data)
            total_count = np.sum(sub_val)
            average = weighted_sum / total_count
            yield_val = total_count / eff_charge
            aver_hist.append(average)
            yield_hist.append(yield_val)

            # Append values to CSV lists
            total_count_list.append(total_count)
            yield_val_list.append(yield_val)
            epset_list.append(EPSSET)  # Replace 'EPSSET' with the actual value

            print("Weighted Sum:", weighted_sum)
            print("Total Count:", total_count)
            print("Average for phi-bin {}:".format(i), average)
            print("Yield for phi-bin {}:".format(i), yield_val)
            binned_sub_data[0].append(bin_val_data)
            binned_sub_data[1].append(sub_val)
        else:
            aver_hist.append(0)
            total_count = 0
            yield_val = 0
            aver_hist.append(0)
            yield_hist.append(0)
            print("Weighted Sum: N/A")
            print("Total Count: N/A")
            print("Average for phi-bin {}: 0.0".format(i))
            print("Yield for phi-bin {}: 0.0".format(i))
            binned_sub_data[0].append(bin_val_data)
            binned_sub_data[1].append([0] * len(bin_val_data))
        i += 1
        print("-" * 25)

    if kin_type == "MM":
        # Write values to CSV files
        with open('total_count.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(total_count_list)

        with open('yield_val.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(yield_val_list)

        with open('epset.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(epset_list)

    
    # Print statements to check sizes
    print("\nSize of binned_phi_data:", len(binned_phi_data))
    print("Size of binned_hist_data:", len(binned_hist_data))
    print("Size of binned_sub_data:", len(binned_sub_data[1]))
    print("Size of aver_hist:", len(aver_hist))
    print("Size of phi_bins:", len(phi_bins))

    dict_lst = []
    for j in range(len(phi_bins) - 1):
        phibin_index = j
        for k in range(len(t_bins) - 1):
            tbin_index = k
            hist_val = [binned_sub_data[0][j], binned_sub_data[1][j]]
            aver_val = aver_hist[j]
            dict_lst.append((phibin_index, tbin_index, hist_val, aver_val))

    # Group the tuples by the first two elements using defaultdict
    groups = defaultdict(list)
    for tup in dict_lst:
        key = (tup[0], tup[1])
        groups[key] = {
            "{}_arr".format(kin_type) : tup[2],
            "{}_aver".format(kin_type) : tup[3],
        }                    
    
    return groups

##################################################################################################################################################

def aver_per_bin_data(histlist, inpDict):

    for hist in histlist:
        eff_charge = hist["normfac_data"]
        phi_bins = hist["phi_bins"]
        t_bins = hist["t_bins"]

        # Assign histograms for Q2
        if hist["phi_setting"] == "Center":
            Q2_Center_DATA = hist["H_Q2_DATA"]
        if hist["phi_setting"] == "Left":
            Q2_Left_DATA = hist["H_Q2_DATA"]
        if hist["phi_setting"] == "Right":
            Q2_Right_DATA = hist["H_Q2_DATA"]

        # Assign histograms for W
        if hist["phi_setting"] == "Center":
            W_Center_DATA = hist["H_W_DATA"]
        if hist["phi_setting"] == "Left":
            W_Left_DATA = hist["H_W_DATA"]
        if hist["phi_setting"] == "Right":
            W_Right_DATA = hist["H_W_DATA"]

        # Assign histograms for t
        if hist["phi_setting"] == "Center":
            phi_Center_DATA = hist["H_phi_DATA"]
        if hist["phi_setting"] == "Left":
            phi_Left_DATA = hist["H_phi_DATA"]
        if hist["phi_setting"] == "Right":
            phi_Right_DATA = hist["H_phi_DATA"]

        # Assign histograms for MM
        if hist["phi_setting"] == "Center":
            MM_Center_DATA = hist["H_MM_DATA"]
        if hist["phi_setting"] == "Left":
            MM_Left_DATA = hist["H_MM_DATA"]
        if hist["phi_setting"] == "Right":
            MM_Right_DATA = hist["H_MM_DATA"]
            
        # Assign histograms for Q2
        if hist["phi_setting"] == "Center":
            Q2_Center_DUMMY = hist["H_Q2_DUMMY"]
        if hist["phi_setting"] == "Left":
            Q2_Left_DUMMY = hist["H_Q2_DUMMY"]
        if hist["phi_setting"] == "Right":
            Q2_Right_DUMMY = hist["H_Q2_DUMMY"]

        # Assign histograms for W
        if hist["phi_setting"] == "Center":
            W_Center_DUMMY = hist["H_W_DUMMY"]
        if hist["phi_setting"] == "Left":
            W_Left_DUMMY = hist["H_W_DUMMY"]
        if hist["phi_setting"] == "Right":
            W_Right_DUMMY = hist["H_W_DUMMY"]

        # Assign histograms for t
        if hist["phi_setting"] == "Center":
            phi_Center_DUMMY = hist["H_phi_DUMMY"]
        if hist["phi_setting"] == "Left":
            phi_Left_DUMMY = hist["H_phi_DUMMY"]
        if hist["phi_setting"] == "Right":
            phi_Right_DUMMY = hist["H_phi_DUMMY"]

        # Assign histograms for MM
        if hist["phi_setting"] == "Center":
            MM_Center_DUMMY = hist["H_MM_DUMMY"]
        if hist["phi_setting"] == "Left":
            MM_Left_DUMMY = hist["H_MM_DUMMY"]
        if hist["phi_setting"] == "Right":
            MM_Right_DUMMY = hist["H_MM_DUMMY"]
            
            
    # Combine histograms for Q2_data
    Q2_data = ROOT.TH1F("Q2_data", "Combined Q2_data Histogram", Q2_Center_DATA.GetNbinsX(), Q2_Center_DATA.GetXaxis().GetXmin(), Q2_Center_DATA.GetXaxis().GetXmax())
    for bin in range(1, Q2_Center_DATA.GetNbinsX() + 1):
        try:
            combined_content = Q2_Center_DATA.GetBinContent(bin) + Q2_Left_DATA.GetBinContent(bin) + Q2_Right_DATA.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = Q2_Center_DATA.GetBinContent(bin) + Q2_Left_DATA.GetBinContent(bin)
        Q2_data.SetBinContent(bin, combined_content)

    # Combine histograms for W_data
    W_data = ROOT.TH1F("W_data", "Combined W_data Histogram", W_Center_DATA.GetNbinsX(), W_Center_DATA.GetXaxis().GetXmin(), W_Center_DATA.GetXaxis().GetXmax())
    for bin in range(1, W_Center_DATA.GetNbinsX() + 1):
        try:
            combined_content = W_Center_DATA.GetBinContent(bin) + W_Left_DATA.GetBinContent(bin) + W_Right_DATA.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = W_Center_DATA.GetBinContent(bin) + W_Left_DATA.GetBinContent(bin)
        W_data.SetBinContent(bin, combined_content)

    # Combine histograms for phi_data
    phi_data = ROOT.TH1F("phi_data", "Combined phi_data Histogram", phi_Center_DATA.GetNbinsX(), phi_Center_DATA.GetXaxis().GetXmin(), phi_Center_DATA.GetXaxis().GetXmax())
    for bin in range(1, phi_Center_DATA.GetNbinsX() + 1):
        try:
            combined_content = phi_Center_DATA.GetBinContent(bin) + phi_Left_DATA.GetBinContent(bin) + phi_Right_DATA.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = phi_Center_DATA.GetBinContent(bin) + phi_Left_DATA.GetBinContent(bin)
        phi_data.SetBinContent(bin, combined_content)

    # Combine histograms for MM_data
    MM_data = ROOT.TH1F("MM_data", "Combined MM_data Histogram", MM_Center_DATA.GetNbinsX(), MM_Center_DATA.GetXaxis().GetXmin(), MM_Center_DATA.GetXaxis().GetXmax())
    for bin in range(1, MM_Center_DATA.GetNbinsX() + 1):
        try:
            combined_content = MM_Center_DATA.GetBinContent(bin) + MM_Left_DATA.GetBinContent(bin) + MM_Right_DATA.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = MM_Center_DATA.GetBinContent(bin) + MM_Left_DATA.GetBinContent(bin)
        MM_data.SetBinContent(bin, combined_content)
        
    # Combine histograms for Q2_dummy
    Q2_dummy = ROOT.TH1F("Q2_dummy", "Combined Q2_dummy Histogram", Q2_Center_DUMMY.GetNbinsX(), Q2_Center_DUMMY.GetXaxis().GetXmin(), Q2_Center_DUMMY.GetXaxis().GetXmax())
    for bin in range(1, Q2_Center_DUMMY.GetNbinsX() + 1):
        try:
            combined_content = Q2_Center_DUMMY.GetBinContent(bin) + Q2_Left_DUMMY.GetBinContent(bin) + Q2_Right_DUMMY.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = Q2_Center_DUMMY.GetBinContent(bin) + Q2_Left_DUMMY.GetBinContent(bin)
        Q2_dummy.SetBinContent(bin, combined_content)

    # Combine histograms for W_dummy
    W_dummy = ROOT.TH1F("W_dummy", "Combined W_dummy Histogram", W_Center_DUMMY.GetNbinsX(), W_Center_DUMMY.GetXaxis().GetXmin(), W_Center_DUMMY.GetXaxis().GetXmax())
    for bin in range(1, W_Center_DUMMY.GetNbinsX() + 1):
        try:
            combined_content = W_Center_DUMMY.GetBinContent(bin) + W_Left_DUMMY.GetBinContent(bin) + W_Right_DUMMY.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = W_Center_DUMMY.GetBinContent(bin) + W_Left_DUMMY.GetBinContent(bin)
        W_dummy.SetBinContent(bin, combined_content)

    # Combine histograms for phi_dummy
    phi_dummy = ROOT.TH1F("phi_dummy", "Combined phi_dummy Histogram", phi_Center_DUMMY.GetNbinsX(), phi_Center_DUMMY.GetXaxis().GetXmin(), phi_Center_DUMMY.GetXaxis().GetXmax())
    for bin in range(1, phi_Center_DUMMY.GetNbinsX() + 1):
        try:
            combined_content = phi_Center_DUMMY.GetBinContent(bin) + phi_Left_DUMMY.GetBinContent(bin) + phi_Right_DUMMY.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = phi_Center_DUMMY.GetBinContent(bin) + phi_Left_DUMMY.GetBinContent(bin)
        phi_dummy.SetBinContent(bin, combined_content)

    # Combine histograms for MM_dummy
    MM_dummy = ROOT.TH1F("MM_dummy", "Combined MM_dummy Histogram", MM_Center_DUMMY.GetNbinsX(), MM_Center_DUMMY.GetXaxis().GetXmin(), MM_Center_DUMMY.GetXaxis().GetXmax())
    for bin in range(1, MM_Center_DUMMY.GetNbinsX() + 1):
        try:
            combined_content = MM_Center_DUMMY.GetBinContent(bin) + MM_Left_DUMMY.GetBinContent(bin) + MM_Right_DUMMY.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = MM_Center_DUMMY.GetBinContent(bin) + MM_Left_DUMMY.GetBinContent(bin)
        MM_dummy.SetBinContent(bin, combined_content)
        
    averDict = {
        "phi_bins" : phi_bins,
        "t_bins" : t_bins
    }
    averDict.update(calculate_aver_data("Q2", Q2_data, Q2_dummy, phi_data, phi_bins, t_bins, eff_charge, hist["EPSSET"], hist["Q2"], hist["W"], hist["ParticleType"]))
    averDict.update(calculate_aver_data("W", W_data, W_dummy, phi_data, phi_bins, t_bins, eff_charge, hist["EPSSET"], hist["Q2"], hist["W"], hist["ParticleType"]))
    averDict.update(calculate_aver_data("phi", phi_data, phi_dummy, phi_data, phi_bins, t_bins, eff_charge, hist["EPSSET"], hist["Q2"], hist["W"], hist["ParticleType"]))
    averDict.update(calculate_aver_data("MM", MM_data, MM_dummy, phi_data, phi_bins, t_bins, eff_charge, hist["EPSSET"], hist["MM"], hist["W"], hist["ParticleType"]))
    
    return {"binned_DATA" : averDict}

def aver_per_bin_simc(histlist, inpDict):

    for hist in histlist:
        phi_bins = hist["phi_bins"]
        t_bins = hist["t_bins"]

        # Assign histograms for Q2
        if hist["phi_setting"] == "Center":
            Q2_Center_SIMC = hist["H_Q2_SIMC"]
        if hist["phi_setting"] == "Left":
            Q2_Left_SIMC = hist["H_Q2_SIMC"]
        if hist["phi_setting"] == "Right":
            Q2_Right_SIMC = hist["H_Q2_SIMC"]

        # Assign histograms for W
        if hist["phi_setting"] == "Center":
            W_Center_SIMC = hist["H_W_SIMC"]
        if hist["phi_setting"] == "Left":
            W_Left_SIMC = hist["H_W_SIMC"]
        if hist["phi_setting"] == "Right":
            W_Right_SIMC = hist["H_W_SIMC"]

        # Assign histograms for t
        if hist["phi_setting"] == "Center":
            phi_Center_SIMC = hist["H_phi_SIMC"]
        if hist["phi_setting"] == "Left":
            phi_Left_SIMC = hist["H_phi_SIMC"]
        if hist["phi_setting"] == "Right":
            phi_Right_SIMC = hist["H_phi_SIMC"]        
    
    # Combine histograms for Q2_simc
    Q2_simc = ROOT.TH1F("Q2_simc", "Combined Q2_simc Histogram", Q2_Center_SIMC.GetNbinsX(), Q2_Center_SIMC.GetXaxis().GetXmin(), Q2_Center_SIMC.GetXaxis().GetXmax())
    for bin in range(1, Q2_Center_SIMC.GetNbinsX() + 1):
        try:
            combined_content = Q2_Center_SIMC.GetBinContent(bin) + Q2_Left_SIMC.GetBinContent(bin) + Q2_Right_SIMC.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = Q2_Center_SIMC.GetBinContent(bin) + Q2_Left_SIMC.GetBinContent(bin)
        Q2_simc.SetBinContent(bin, combined_content)

    # Combine histograms for W_simc
    W_simc = ROOT.TH1F("W_simc", "Combined W_simc Histogram", W_Center_SIMC.GetNbinsX(), W_Center_SIMC.GetXaxis().GetXmin(), W_Center_SIMC.GetXaxis().GetXmax())
    for bin in range(1, W_Center_SIMC.GetNbinsX() + 1):
        try:
            combined_content = W_Center_SIMC.GetBinContent(bin) + W_Left_SIMC.GetBinContent(bin) + W_Right_SIMC.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = W_Center_SIMC.GetBinContent(bin) + W_Left_SIMC.GetBinContent(bin)
        W_simc.SetBinContent(bin, combined_content)

    # Combine histograms for phi_simc
    phi_simc = ROOT.TH1F("phi_simc", "Combined phi_simc Histogram", phi_Center_SIMC.GetNbinsX(), phi_Center_SIMC.GetXaxis().GetXmin(), phi_Center_SIMC.GetXaxis().GetXmax())
    for bin in range(1, phi_Center_SIMC.GetNbinsX() + 1):
        try:
            combined_content = phi_Center_SIMC.GetBinContent(bin) + phi_Left_SIMC.GetBinContent(bin) + phi_Right_SIMC.GetBinContent(bin)
        except UnboundLocalError:
            combined_content = phi_Center_SIMC.GetBinContent(bin) + phi_Left_SIMC.GetBinContent(bin)
        phi_simc.SetBinContent(bin, combined_content)

    averDict = {}        
    averDict.update(calculate_aver_simc("Q2", Q2_simc, phi_simc, phi_bins, t_bins))
    averDict.update(calculate_aver_simc("W", W_simc, phi_simc, phi_bins, t_bins))
    averDict.update(calculate_aver_simc("phi", phi_simc, phi_simc, phi_bins, t_bins))

    return {"binned_SIMC" : averDict}
