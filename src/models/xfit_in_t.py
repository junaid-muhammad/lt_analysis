#! /usr/bin/python

#
# Description:
# ================================================================
# Time-stamp: "2024-06-04 11:05:29 trottar"
# ================================================================
#
# Author:  Richard L. Trotta III <trotta@cua.edu>
#
# Copyright (c) trottar
#
import ROOT
from ROOT import TFile, TNtuple, TText
from ROOT import TGraph, TGraphErrors, TCanvas
from ROOT import TF1, TFitResultPtr
import math
import os, sys

################################################################################################################################################
'''
ltsep package import and pathing definitions
'''

# Import package for cuts
from ltsep import Root
# Import package for progress bar
from ltsep import Misc

lt=Root(os.path.realpath(__file__),"Plot_LTSep")

# Add this to all files for more dynamic pathing
USER=lt.USER # Grab user info for file finding
HOST=lt.HOST
REPLAYPATH=lt.REPLAYPATH
UTILPATH=lt.UTILPATH
LTANAPATH=lt.LTANAPATH
ANATYPE=lt.ANATYPE
OUTPATH=lt.OUTPATH
CACHEPATH=lt.CACHEPATH

################################################################################################################################################
# Suppressing the terminal splash of Print()
ROOT.gROOT.ProcessLine("gErrorIgnoreLevel = kError;")
ROOT.gROOT.SetBatch(ROOT.kTRUE) # Set ROOT to batch mode explicitly, does not splash anything to screen
###############################################################################################################################################

# Define constants
PI = math.pi
m_p = 0.93827231
m_n = 0.93956541
mkpl = 0.493677

DEBUG=False
#DEBUG=True

###############################################################################################################################################
# Import separated xsects models

from xfit_active import fun_Sig_L, fun_Sig_T, fun_Sig_LT, fun_Sig_TT, set_val

###############################################################################################################################################

def x_fit_in_t(ParticleType, pol_str, closest_date, Q2, W, inpDict):

    tmin_range = inpDict["tmin"]
    tmax_range = inpDict["tmax"]
    Q2min_range = inpDict["Q2min"]
    Q2max_range = inpDict["Q2max"]

    iter_num = inpDict["iter_num"]
    
    ##############
    # HARD CODED #
    ##############
    # Limit for finding new parameters (units of percent)
    if iter_num == 2:
        par_lim = 100.00 # +/-10000%
    else:
        #par_lim = 0.001 # +/-.1%
        #par_lim = 0.01 # +/-1%
        #par_lim = 0.05 # +/-5%
        par_lim = 0.2 # +/-20%
        #par_lim = 0.75 # +/-75%
        #par_lim = 10.00 # +/-1000%        
    ##############
    ##############
    ##############
    
    single_setting(ParticleType, pol_str, closest_date, Q2, W, tmin_range, tmax_range, Q2min_range, Q2max_range, par_lim)
    
def single_setting(ParticleType, pol_str, dir_iter, q2_set, w_set, tmin_range, tmax_range, Q2min_range, Q2max_range, par_lim):

    # Set pol_str, q2_set for xfit_active script
    set_val(pol_str, q2_set)
    
    outputpdf  = "{}/{}_xfit_in_t_Q{}W{}.pdf".format(OUTPATH, ParticleType, q2_set, w_set)
    
    prv_par_vec = []
    g_vec = []
    w_vec = []
    q2_vec = []
    th_vec = []
    par_vec = []
    par_err_vec = []
    par_chi2_vec = []

    l0, l1, l2, l3 = 0, 0, 0, 0
    t0, t1, t2, t3 = 0, 0, 0, 0
    lt0, lt1, lt2, lt3 = 0, 0, 0, 0
    tt0, tt1, tt2, tt3 = 0, 0, 0, 0

    fn_sep = "{}/src/{}/xsects/x_sep.{}_Q{}W{}.dat".format(LTANAPATH, ParticleType, pol_str, q2_set.replace("p",""), w_set.replace("p",""))
    nsep = TNtuple("nsep", "nsep", "sigl:sigl_e:sigt:sigt_e:siglt:siglt_e:sigtt:sigtt_e:chi:t:w:q2:thetacm")
    nsep.ReadFile(fn_sep)

    '''
    print("Reading {}...".format(fn_sep))
    for entry in nsep:
        print("sigl: {}, sigl_e: {}, sigt: {}, sigt_e: {}, siglt: {}, siglt_e: {}, sigtt: {}, sigtt_e: {}, chi: {}, t: {}, w: {}, q2: {}, thetacm: {}".format(
            entry.sigl, entry.sigl_e, entry.sigt, entry.sigt_e, entry.siglt, entry.siglt_e, entry.sigtt, entry.sigtt_e, entry.chi, entry.t, entry.w, entry.q2, entry.thetacm
        ))
    '''

    prv_par_vec = []
    para_file_in =  "{}/{}/{}/Q{}W{}/{}/parameters/par.{}_Q{}W{}.dat".format(CACHEPATH, USER, ParticleType, q2_set, w_set, dir_iter, \
                                                                             pol_str, q2_set.replace("p",""), w_set.replace("p",""))
    print("Reading {}...".format(para_file_in))
    try:
        with open(para_file_in, 'r') as f:
            for line in f:
                data = line.split()
                par, par_err, indx, chi2 = map(float, data)
                print("  {} {} {} {}".format(par, par_err, indx, chi2))
                prv_par_vec.append(par)
    except FileNotFoundError:
        print("File {} not found.".format(para_file_in))
        
    l0, l1, l2, l3, t0, t1, t2, t3, lt0, lt1, lt2, lt3, tt0, tt1, tt2, tt3 = prv_par_vec[:16]
    
    ave_file_in = "{}/src/{}/averages/avek.Q{}W{}.dat".format(LTANAPATH, ParticleType, q2_set.replace("p",""), w_set.replace("p",""))
    with open(ave_file_in, 'r') as f:
        for line in f:
            w, w_e, q2, q2_e, tt, tt_e, thetacm, it = map(float, line.strip().split())

            if pol_str == "pl":
                g = (1 / ((w**2) - (m_p**2))**2)
            else:
                g = (1 / ((w**2) - (m_n**2))**2)
            g_vec.append(g)
            w_vec.append(w)
            q2_vec.append(q2)
            th_vec.append(thetacm)

    g_sigl_prv = TGraph()            
    g_sigt_prv = TGraph()
    g_siglt_prv = TGraph()
    g_sigtt_prv = TGraph()

    g_sigl_fit = TGraphErrors()
    g_sigt_fit = TGraphErrors()
    g_siglt_fit = TGraphErrors()
    g_sigtt_fit = TGraphErrors()

    g_sigl_fit_tot = TGraph()    
    g_sigt_fit_tot = TGraph()
    g_siglt_fit_tot = TGraph()
    g_sigtt_fit_tot = TGraph()

    c1 = TCanvas("c1", "c1", 800, 800)
    c1.Divide(2, 2)

    c2 = TCanvas("c2", "c2", 800, 800)
    c2.Divide(2, 2)

    ########
    # SigL #
    ########
    
    print("/*--------------------------------------------------*/")
    print("Fit for Sig L")

    c1.cd(1).SetLeftMargin(0.12)
    nsep.Draw("sigl:t:sigl_e", "", "goff")
    
    ##############
    # HARD CODED #
    ##############
    f_sigL_pre = TF1("sig_L", fun_Sig_L, tmin_range, tmax_range, 3)
    f_sigL_pre.SetParNames("p1","p2","p3")
    #f_sigL_pre.SetParameters(l0, l1, l2)
    # Fixed unused parameters
    #f_sigL_pre.FixParameter(0, 0)
    #f_sigL_pre.FixParameter(1, 0)
    #f_sigL_pre.FixParameter(2, 0)
    # Set range limit of used parameters
    if l0 != 0.0:
        f_sigL_pre.SetParLimits(0, l0-abs(l0*par_lim), l0+abs(l0*par_lim))
    else:
        f_sigL_pre.SetParLimits(0, -par_lim, par_lim)        
    if l1 != 0.0:
        f_sigL_pre.SetParLimits(1, l1-abs(l1*par_lim), l1+abs(l1*par_lim))
    else: 
        f_sigL_pre.SetParLimits(1, -par_lim, par_lim)       
    if l2 != 0.0:
        f_sigL_pre.SetParLimits(2, l2-abs(l2*par_lim), l2+abs(l2*par_lim))
    else: 
        f_sigL_pre.SetParLimits(2, -par_lim, par_lim)
    # Fixing sigL terms for testing
    #f_sigL_pre.FixParameter(0, l0)
    #f_sigL_pre.FixParameter(1, l1)
    #f_sigL_pre.FixParameter(2, l2)
    # Fixing sigL terms to zero
    #f_sigL_pre.FixParameter(0, 0.0)
    #f_sigL_pre.FixParameter(1, 0.0)
    #f_sigL_pre.FixParameter(2, 0.0)
    if DEBUG:
        f_sigL_pre.FixParameter(0, l0)
        f_sigL_pre.FixParameter(1, l1)
        f_sigL_pre.FixParameter(2, l2)
    ##############
    ##############
    ##############
    
    #g_sigl = TGraphErrors(nsep.GetSelectedRows(), nsep.GetV2(), nsep.GetV1(), 0, nsep.GetV3())
    g_sigl = TGraphErrors()
    for i in range(nsep.GetSelectedRows()):
        g_sigl.SetPoint(i, nsep.GetV2()[i], nsep.GetV1()[i])
        g_sigl.SetPointError(i, 0, nsep.GetV3()[i])

    for i in range(len(w_vec)):
        
        sigl_X_pre = (f_sigL_pre.Eval(g_sigl.GetX()[i])) * (g_vec[i])
        g_sigl_prv.SetPoint(i, g_sigl.GetX()[i], sigl_X_pre)

        sigl_X_fit = g_sigl.GetY()[i]
        sigl_X_fit_err = g_sigl.GetEY()[i]

        g_sigl_fit.SetPoint(i, g_sigl.GetX()[i], sigl_X_fit)
        g_sigl_fit.SetPointError(i, 0, sigl_X_fit_err)
        
    g_sigl.SetTitle("Sig L")

    g_sigl.SetMarkerStyle(5)
    g_sigl.Draw("AP")

    g_sigl.GetXaxis().SetTitle("#it{-t} [GeV^{2}]")
    g_sigl.GetXaxis().CenterTitle()
    g_sigl.GetYaxis().SetTitle("#left(#frac{#it{d#sigma}}{#it{dt}}#right)_{L} [nb/GeV^{2}]")
    g_sigl.GetYaxis().SetTitleOffset(1.5)
    g_sigl.GetYaxis().SetTitleSize(0.035)
    g_sigl.GetYaxis().CenterTitle()

    g_sigl_prv.SetMarkerColor(4)
    g_sigl_prv.SetMarkerStyle(25)
    g_sigl_prv.Draw("P")

    c2.cd(1).SetLeftMargin(0.12)
    g_sigl_fit.SetTitle("Sigma L Model Fit")
    g_sigl_fit.Draw("A*")

    g_sigl_fit.GetXaxis().SetTitle("#it{-t} [GeV^{2}]")
    g_sigl_fit.GetXaxis().CenterTitle()
    g_sigl_fit.GetYaxis().SetTitle("#left(#frac{#it{d#sigma}}{#it{dt}}#right)_{L} [nb/GeV^{2}]")
    g_sigl_fit.GetYaxis().SetTitleOffset(1.5)
    g_sigl_fit.GetYaxis().SetTitleSize(0.035)
    g_sigl_fit.GetYaxis().CenterTitle()
    
    ##############
    # HARD CODED #
    ##############
    # Fixed unused parameters
    f_sigL = TF1("sig_L", fun_Sig_L, tmin_range, tmax_range, 3)
    f_sigL.SetParNames("p1","p2","p3")
    #f_sigL.SetParameters(l0, l1, l2)        
    #f_sigL.FixParameter(0, 0)
    #f_sigL.FixParameter(1, 0)
    #f_sigL.FixParameter(2, 0)
    # Set range limit of used parameters
    if l0 != 0.0:
        f_sigL.SetParLimits(0, l0-abs(l0*par_lim), l0+abs(l0*par_lim))
    else: 
        f_sigL.SetParLimits(0, -par_lim, par_lim)       
    if l1 != 0.0:
        f_sigL.SetParLimits(1, l1-abs(l1*par_lim), l1+abs(l1*par_lim))
    else: 
        f_sigL.SetParLimits(1, -par_lim, par_lim)       
    if l2 != 0.0:
        f_sigL.SetParLimits(2, l2-abs(l2*par_lim), l2+abs(l2*par_lim))
    else: 
        f_sigL.SetParLimits(2, -par_lim, par_lim)
    # Fixing sigL terms for testing
    #f_sigL.FixParameter(0, l0)
    #f_sigL.FixParameter(1, l1)
    #f_sigL.FixParameter(2, l2)
    # Fixing sigL terms to zero
    #f_sigL.FixParameter(0, 0.0)
    #f_sigL.FixParameter(1, 0.0)
    #f_sigL.FixParameter(2, 0.0)
    if DEBUG:
        f_sigL.FixParameter(0, l0)
        f_sigL.FixParameter(1, l1)
        f_sigL.FixParameter(2, l2)
    ##############
    ##############
    ##############    
    
    g_q2_sigl_fit = TGraphErrors()
    for i in range(len(w_vec)):
        g_q2_sigl_fit.SetPoint(i, g_sigl.GetX()[i], sigl_X_fit)
        g_q2_sigl_fit.SetPointError(i, 0.0, sigl_X_fit_err)
        sigl_X = (f_sigL.Eval(g_sigl.GetX()[i])) * (g_vec[i])
        g_sigl_fit_tot.SetPoint(i, g_sigl.GetX()[i], sigl_X)
    # Options: S-> Simultaneous fit, M-> Improve fit info splash, R-> Use range specified, Q-> Quiet splash
    g_sigl_fit.Fit(f_sigL, "SM")

    f_sigL.Draw("same")
    
    # Check the fit status for 'f_sigL'
    f_sigL_status = f_sigL.GetNDF()  # GetNDF() returns the number of degrees of freedom
    f_sigL_status_message = "Not Fitted" if f_sigL_status == 0 else "Fit Successful"

    fit_status = TText()
    fit_status.SetTextSize(0.04)
    fit_status.DrawTextNDC(0.35, 0.85, " Fit Status: {}".format(f_sigL_status_message))
        
    c1.cd(1)

    g_sigl_fit_tot.SetMarkerStyle(26)
    g_sigl_fit_tot.SetMarkerColor(2)
    g_sigl_fit_tot.SetLineColor(2)
    g_sigl_fit_tot.Draw("LP")

    par_vec.append(f_sigL.GetParameter(0))
    par_vec.append(f_sigL.GetParameter(1))
    par_vec.append(f_sigL.GetParameter(2))
    par_vec.append(f_sigL.GetParameter(3))

    par_err_vec.append(f_sigL.GetParError(0))
    par_err_vec.append(f_sigL.GetParError(1))
    par_err_vec.append(f_sigL.GetParError(2))
    par_err_vec.append(f_sigL.GetParError(3))

    par_chi2_vec.append(f_sigL.GetChisquare())
    par_chi2_vec.append(f_sigL.GetChisquare())
    par_chi2_vec.append(f_sigL.GetChisquare())
    par_chi2_vec.append(f_sigL.GetChisquare())

    ########
    # SigT #
    ########

    print("/*--------------------------------------------------*/")
    print("Fit for Sig T")
    
    c1.cd(2).SetLeftMargin(0.12)
    nsep.Draw("sigt:t:sigt_e", "", "goff")

    ##############
    # HARD CODED #
    ##############
    f_sigT_pre = TF1("sig_T", fun_Sig_T, tmin_range, tmax_range, 3)
    f_sigT_pre.SetParNames("p5","p6","p7")
    #f_sigT_pre.SetParameters(t0, t1)        
    # Fixed unused parameters
    #f_sigT_pre.FixParameter(0, 0)
    #f_sigT_pre.FixParameter(1, 0)
    ##f_sigT_pre.FixParameter(2, 0)
    # Set range limit of used parameters
    if t0 != 0.0:
        f_sigT_pre.SetParLimits(0, t0-abs(t0*par_lim), t0+abs(t0*par_lim))
    else: 
        f_sigT_pre.SetParLimits(0, -par_lim, par_lim)       
    if t1 != 0.0:
        f_sigT_pre.SetParLimits(1, t1-abs(t1*par_lim), t1+abs(t1*par_lim))
    else: 
        f_sigT_pre.SetParLimits(1, -par_lim, par_lim)
    if t2 != 0.0:
        f_sigT_pre.SetParLimits(2, t2-abs(t2*par_lim), t2+abs(t2*par_lim))
    else: 
        f_sigT_pre.SetParLimits(2, -par_lim, par_lim)
    # Fixing sigT terms for testing
    #f_sigT_pre.FixParameter(0, t0)
    #f_sigT_pre.FixParameter(1, t1)
    #f_sigT_pre.FixParameter(2, t2)
    # Fixing sigT terms to zero
    #f_sigT_pre.FixParameter(0, 0.0)
    #f_sigT_pre.FixParameter(1, 0.0)
    if DEBUG:
        f_sigT_pre.FixParameter(0, t0)
        f_sigT_pre.FixParameter(1, t1)
        f_sigT_pre.FixParameter(2, t2)
    ##############
    ##############
    ##############    
    
    #g_sigt = TGraphErrors(nsep.GetSelectedRows(), nsep.GetV2(), nsep.GetV1(), [0] * nsep.GetSelectedRows(), nsep.GetV3())
    g_sigt = TGraphErrors()
    for i in range(nsep.GetSelectedRows()):
        g_sigt.SetPoint(i, nsep.GetV2()[i], nsep.GetV1()[i])
        g_sigt.SetPointError(i, 0, nsep.GetV3()[i])

    for i in range(len(w_vec)):

        sigt_X_pre = (f_sigT_pre.Eval(g_sigt.GetX()[i])) * (g_vec[i])
        g_sigt_prv.SetPoint(i, g_sigt.GetX()[i], sigt_X_pre)

        sigt_X_fit = (g_sigt.GetY()[i])
        sigt_X_fit_err = g_sigt.GetEY()[i]

        g_sigt_fit.SetPoint(i, g_sigt.GetX()[i], sigt_X_fit)
        g_sigt_fit.SetPointError(i, 0, sigt_X_fit_err)
        
    g_sigt.SetTitle("Sig T")

    g_sigt.SetMarkerStyle(5)
    g_sigt.Draw("AP")
    
    g_sigt.GetXaxis().SetTitle("#it{-t} [GeV^{2}]")
    g_sigt.GetXaxis().CenterTitle()
    g_sigt.GetYaxis().SetTitle("#left(#frac{#it{d#sigma}}{#it{dt}}#right)_{T} [nb/GeV^{2}]")
    g_sigt.GetYaxis().SetTitleOffset(1.5)
    g_sigt.GetYaxis().SetTitleSize(0.035)
    g_sigt.GetYaxis().CenterTitle()

    g_sigt_prv.SetMarkerColor(4)
    g_sigt_prv.SetMarkerStyle(25)
    g_sigt_prv.Draw("P")
        
    c2.cd(2).SetLeftMargin(0.12)
    g_sigt_fit.SetTitle("Sigma T Model Fit")
    g_sigt_fit.Draw("A*")

    g_sigt_fit.GetXaxis().SetTitle("#it{-t} [GeV^{2}]")
    g_sigt_fit.GetXaxis().CenterTitle()
    g_sigt_fit.GetYaxis().SetTitle("#left(#frac{#it{d#sigma}}{#it{dt}}#right)_{LT} [nb/GeV^{2}]")
    g_sigt_fit.GetYaxis().SetTitleOffset(1.5)
    g_sigt_fit.GetYaxis().SetTitleSize(0.035)
    g_sigt_fit.GetYaxis().CenterTitle()
    

    ##############
    # HARD CODED #
    ##############
    f_sigT = TF1("sig_T", fun_Sig_T, tmin_range, tmax_range, 3)
    f_sigT.SetParNames("p5","p6","p7")
    #f_sigT.SetParameters(t0, t1)    
    # Fixed unused parameters
    #f_sigT.FixParameter(0, 0)
    #f_sigT.FixParameter(1, 0)
    ##f_sigT.FixParameter(2, 0)
    # Set range limit of used parameters
    if t0 != 0.0:
        f_sigT.SetParLimits(0, t0-abs(t0*par_lim), t0+abs(t0*par_lim))
    else: 
        f_sigT.SetParLimits(0, -par_lim, par_lim)       
    if t1 != 0.0:
        f_sigT.SetParLimits(1, t1-abs(t1*par_lim), t1+abs(t1*par_lim))
    else: 
        f_sigT.SetParLimits(1, -par_lim, par_lim)
    if t2 != 0.0:
        f_sigT_pre.SetParLimits(2, t2-abs(t2*par_lim), t2+abs(t2*par_lim))
    else: 
        f_sigT_pre.SetParLimits(2, -par_lim, par_lim)
    # Fixing sigT terms for testing
    #f_sigT.FixParameter(0, t0)
    #f_sigT.FixParameter(1, t1)
    #f_sigT.FixParameter(2, t2)
    # Fixing sigT terms to zero
    #f_sigT.FixParameter(0, 0.0)
    #f_sigT.FixParameter(1, 0.0)
    if DEBUG:
        f_sigT.FixParameter(0, t0)
        f_sigT.FixParameter(1, t1)
        f_sigT.FixParameter(2, t2)
    ##############
    ##############
    ##############    
    
    g_q2_sigt_fit = TGraphErrors()
    for i in range(len(w_vec)):
        g_q2_sigt_fit.SetPoint(i, g_sigt.GetX()[i], sigt_X_fit)
        g_q2_sigt_fit.SetPointError(i, 0.0, sigt_X_fit_err)
        sigt_X = (f_sigT.Eval(g_sigt.GetX()[i])) * (g_vec[i])
        g_sigt_fit_tot.SetPoint(i, g_sigt.GetX()[i], sigt_X)
    # Options: S-> Simultaneous fit, M-> Improve fit info splash, R-> Use range specified, Q-> Quiet splash
    g_sigt_fit.Fit(f_sigT, "SM")
    
    # Check the fit status for 'f_sigT'
    f_sigT_status = f_sigT.GetNDF()  # GetNDF() returns the number of degrees of freedom
    f_sigT_status_message = "Not Fitted" if f_sigT_status == 0 else "Fit Successful"

    f_sigT.Draw("same")
    
    fit_status = TText()
    fit_status.SetTextSize(0.04)
    fit_status.DrawTextNDC(0.35, 0.85, " Fit Status: {}".format(f_sigT_status_message))
        
    c1.cd(2)

    g_sigt_fit_tot.SetMarkerStyle(26)
    g_sigt_fit_tot.SetMarkerColor(2)
    g_sigt_fit_tot.SetLineColor(2)
    g_sigt_fit_tot.Draw("LP")
    
    par_vec.append(f_sigT.GetParameter(0))
    par_vec.append(f_sigT.GetParameter(1))
    par_vec.append(f_sigT.GetParameter(2))
    par_vec.append(f_sigT.GetParameter(3))

    par_err_vec.append(f_sigT.GetParError(0))
    par_err_vec.append(f_sigT.GetParError(1))
    par_err_vec.append(f_sigT.GetParError(2))
    par_err_vec.append(f_sigT.GetParError(3))

    par_chi2_vec.append(f_sigT.GetChisquare())
    par_chi2_vec.append(f_sigT.GetChisquare())
    par_chi2_vec.append(f_sigT.GetChisquare())
    par_chi2_vec.append(f_sigT.GetChisquare())
    
    #########
    # SigLT #
    #########

    print("/*--------------------------------------------------*/")
    print("Fit for Sig LT")

    c1.cd(3).SetLeftMargin(0.12)
    nsep.Draw("siglt:t:siglt_e", "", "goff")

    ##############
    # HARD CODED #
    ##############
    f_sigLT_pre = TF1("sig_LT", fun_Sig_LT, tmin_range, tmax_range, 3)
    f_sigLT_pre.SetParNames("p9","p10","p11")
    #lt0, lt1, lt2 = 0.0, 0.0, 0.0
    #f_sigLT_pre.SetParameters(lt0, lt1, lt2)        
    # Fixed unused parameters
    #f_sigLT_pre.FixParameter(0, 0)
    #f_sigLT_pre.FixParameter(1, 0)
    #f_sigLT_pre.FixParameter(2, 0)
    ##f_sigLT_pre.FixParameter(3, 0)
    # Set range limit of used parameters
    if lt0 != 0.0:
        f_sigLT_pre.SetParLimits(0, lt0-abs(lt0*par_lim), lt0+abs(lt0*par_lim))
    else: 
        f_sigLT_pre.SetParLimits(0, -par_lim, par_lim)       
    if lt1 != 0.0:
        f_sigLT_pre.SetParLimits(1, lt1-abs(lt1*par_lim), lt1+abs(lt1*par_lim))
    else: 
        f_sigLT_pre.SetParLimits(1, -par_lim, par_lim)       
    if lt2 != 0.0:
        f_sigLT_pre.SetParLimits(2, lt2-abs(lt2*par_lim), lt2+abs(lt2*par_lim))
    else: 
        f_sigLT_pre.SetParLimits(2, -par_lim, par_lim)    
    #f_sigLT_pre.SetParLimits(3, lt3-abs(lt3*par_lim_LTTT), lt3+abs(lt3*par_lim_LTTT))        
    # Fixing sigLT terms for testing
    #f_sigLT_pre.FixParameter(0, lt0)
    #f_sigLT_pre.FixParameter(1, lt1)
    #f_sigLT_pre.FixParameter(2, lt2)
    # Fixing sigLT terms to zero
    #f_sigLT_pre.FixParameter(0, 0.0)
    #f_sigLT_pre.FixParameter(1, 0.0)
    #f_sigLT_pre.FixParameter(2, 0.0)
    if DEBUG:
        f_sigLT_pre.FixParameter(0, lt0)
        f_sigLT_pre.FixParameter(1, lt1)
        f_sigLT_pre.FixParameter(2, lt2)
    ##############
    ##############
    ##############    
    
    #g_siglt = TGraphErrors(nsep.GetSelectedRows(), nsep.GetV2(), nsep.GetV1(), ROOT.nullptr, nsep.GetV3())
    g_siglt = TGraphErrors()
    for i in range(nsep.GetSelectedRows()):
        g_siglt.SetPoint(i, nsep.GetV2()[i], nsep.GetV1()[i])
        g_siglt.SetPointError(i, 0, nsep.GetV3()[i])

    for i in range(len(w_vec)):
        
        siglt_X_pre = (f_sigLT_pre.Eval(g_siglt.GetX()[i]) * math.sin(th_vec[i] * PI / 180)) * (g_vec[i])
        g_siglt_prv.SetPoint(i, g_sigl.GetX()[i], siglt_X_pre)

        siglt_X_fit = g_siglt.GetY()[i] #/ (math.sin(th_vec[i] * PI / 180))
        siglt_X_fit_err = g_siglt.GetEY()[i] #/ (math.sin(th_vec[i] * PI / 180))

        g_siglt_fit.SetPoint(i, g_siglt.GetX()[i], siglt_X_fit)
        g_siglt_fit.SetPointError(i, 0, siglt_X_fit_err)
        
    g_siglt.SetTitle("Sig LT")

    g_siglt.SetMarkerStyle(5)
    g_siglt.Draw("AP")

    g_siglt.GetXaxis().SetTitle("#it{-t} [GeV^{2}]")
    g_siglt.GetXaxis().CenterTitle()
    g_siglt.GetYaxis().SetTitle("#left(#frac{#it{d#sigma}}{#it{dt}}#right)_{LT} [nb/GeV^{2}]")
    g_siglt.GetYaxis().SetTitleOffset(1.5)
    g_siglt.GetYaxis().SetTitleSize(0.035)
    g_siglt.GetYaxis().CenterTitle()
    
    g_siglt_prv.SetMarkerColor(4)
    g_siglt_prv.SetMarkerStyle(25)
    g_siglt_prv.Draw("P")

    c2.cd(3).SetLeftMargin(0.12)
    g_siglt_fit.SetTitle("Sigma LT Model Fit")
    g_siglt_fit.Draw("A*")

    g_siglt_fit.GetXaxis().SetTitle("#it{-t} [GeV^{2}]")
    g_siglt_fit.GetXaxis().CenterTitle()
    g_siglt_fit.GetYaxis().SetTitle("#left(#frac{#it{d#sigma}}{#it{dt}}#right)_{LT} [nb/GeV^{2}]")
    g_siglt_fit.GetYaxis().SetTitleOffset(1.5)
    g_siglt_fit.GetYaxis().SetTitleSize(0.035)
    g_siglt_fit.GetYaxis().CenterTitle()
    
    ##############
    # HARD CODED #
    ##############
    f_sigLT = TF1("sig_LT", fun_Sig_LT, tmin_range, tmax_range, 3)
    f_sigLT.SetParNames("p9","p10","p11")
    #lt0, lt1, lt2 = 0.0, 0.0, 0.0
    #f_sigLT.SetParameters(lt0, lt1, lt2)    
    # Fixed unused parameters
    #f_sigLT.FixParameter(0, 0)
    #f_sigLT.FixParameter(1, 0)
    #f_sigLT.FixParameter(2, 0)
    ##f_sigLT.FixParameter(3, 0)
    # Set range limit of used parameters
    if lt0 != 0.0:
        f_sigLT.SetParLimits(0, lt0-abs(lt0*par_lim), lt0+abs(lt0*par_lim))
    else: 
        f_sigLT.SetParLimits(0, -par_lim, par_lim)       
    if lt1 != 0.0:
        f_sigLT.SetParLimits(1, lt1-abs(lt1*par_lim), lt1+abs(lt1*par_lim))
    else: 
        f_sigLT.SetParLimits(1, -par_lim, par_lim)       
    if lt2 != 0.0:
        f_sigLT.SetParLimits(2, lt2-abs(lt2*par_lim), lt2+abs(lt2*par_lim))
    else: 
        f_sigLT.SetParLimits(2, -par_lim, par_lim)
    #f_sigLT.SetParLimits(3, lt3-abs(lt3*par_lim_LTTT), lt3+abs(lt3*par_lim_LTTT))
    # Fixing sigLT terms for testing
    #f_sigLT.FixParameter(0, lt0)
    #f_sigLT.FixParameter(1, lt1)
    #f_sigLT.FixParameter(2, lt2)
    # Fixing sigLT terms to zero
    #f_sigLT.FixParameter(0, 0.0)
    #f_sigLT.FixParameter(1, 0.0)
    #f_sigLT.FixParameter(2, 0.0)
    if DEBUG:
        f_sigLT.FixParameter(0, lt0)
        f_sigLT.FixParameter(1, lt1)
        f_sigLT.FixParameter(2, lt2)
    ##############
    ##############
    ##############    
    
    g_q2_siglt_fit = TGraphErrors()
    for i in range(len(w_vec)):
        g_q2_siglt_fit.SetPoint(i, g_siglt.GetX()[i], siglt_X_fit)
        g_q2_siglt_fit.SetPointError(i, 0.0, siglt_X_fit_err)
        siglt_X = (f_sigLT.Eval(g_siglt.GetX()[i]) * math.sin(th_vec[i] * PI / 180)) * (g_vec[i])
        g_siglt_fit_tot.SetPoint(i, g_siglt.GetX()[i], siglt_X)
    # Options: S-> Simultaneous fit, M-> Improve fit info splash, R-> Use range specified, Q-> Quiet splash
    g_siglt_fit.Fit(f_sigLT, "SM")
    
    # Check the fit status for 'f_sigLT'
    f_sigLT_status = f_sigLT.GetNDF()  # GetNDF() returns the number of degrees of freedom
    f_sigLT_status_message = "Not Fitted" if f_sigLT_status == 0 else "Fit Successful"

    f_sigLT.Draw("same")
    
    fit_status = TText()
    fit_status.SetTextSize(0.04)
    fit_status.DrawTextNDC(0.35, 0.85, " Fit Status: {}".format(f_sigLT_status_message))
        
    c1.cd(3)

    g_siglt_fit_tot.SetMarkerStyle(26)
    g_siglt_fit_tot.SetMarkerColor(2)
    g_siglt_fit_tot.SetLineColor(2)
    g_siglt_fit_tot.Draw("LP")
        
    par_vec.append(f_sigLT.GetParameter(0))
    par_vec.append(f_sigLT.GetParameter(1))
    par_vec.append(f_sigLT.GetParameter(2))
    par_vec.append(f_sigLT.GetParameter(3))

    par_err_vec.append(f_sigLT.GetParError(0))
    par_err_vec.append(f_sigLT.GetParError(1))
    par_err_vec.append(f_sigLT.GetParError(2))
    par_err_vec.append(f_sigLT.GetParError(3))

    par_chi2_vec.append(f_sigLT.GetChisquare())
    par_chi2_vec.append(f_sigLT.GetChisquare())
    par_chi2_vec.append(f_sigLT.GetChisquare())
    par_chi2_vec.append(f_sigLT.GetChisquare())

    #########
    # SigTT #
    #########

    print("/*--------------------------------------------------*/")
    print("Fit for Sig TT")

    c1.cd(4).SetLeftMargin(0.12)
    nsep.Draw("sigtt:t:sigtt_e", "", "goff")

    ##############
    # HARD CODED #
    ##############
    f_sigTT_pre = TF1("sig_TT", fun_Sig_TT, tmin_range, tmax_range, 1)
    f_sigTT_pre.SetParNames("p13")
    #tt0 = 0.0
    #f_sigTT_pre.SetParameters(tt0, 0.0)
    # Fixed unused parameters
    #f_sigTT_pre.FixParameter(0, 0)
    ##f_sigTT_pre.FixParameter(1, 0)
    ##f_sigTT_pre.FixParameter(2, 0)
    ##f_sigTT_pre.FixParameter(3, 0)
    # Set range limit of used parameters
    if tt0 != 0.0:
        f_sigTT_pre.SetParLimits(0, tt0-abs(tt0*par_lim), tt0+abs(tt0*par_lim))
    else: 
        f_sigTT_pre.SetParLimits(0, -par_lim, par_lim)
    # Fixing sigTT terms for testing
    #f_sigTT_pre.FixParameter(0, tt0)
    # Fixing sigTT terms to zero
    #f_sigTT_pre.FixParameter(0, 0.0)
    if DEBUG:
        f_sigTT_pre.FixParameter(0, tt0)
    ##############
    ##############
    ##############    
    
    #g_sigtt = TGraphErrors(nsep.GetSelectedRows(), nsep.GetV2(), nsep.GetV1(), [0]*nsep.GetSelectedRows(), nsep.GetV3())
    g_sigtt = TGraphErrors()
    for i in range(nsep.GetSelectedRows()):
        g_sigtt.SetPoint(i, nsep.GetV2()[i], nsep.GetV1()[i])
        g_sigtt.SetPointError(i, 0, nsep.GetV3()[i])

    for i in range(len(w_vec)):
        
        sigtt_X_pre = (f_sigTT_pre.Eval(g_sigtt.GetX()[i]) * math.sin(th_vec[i] * PI / 180)**2) * (g_vec[i])

        g_sigtt_prv.SetPoint(i, nsep.GetV2()[i], sigtt_X_pre)

        sigtt_X_fit = g_sigtt.GetY()[i] #/ (math.sin(th_vec[i] * PI / 180)**2)
        sigtt_X_fit_err = g_sigtt.GetEY()[i] #/ (math.sin(th_vec[i] * PI / 180)**2)

        g_sigtt_fit.SetPoint(i, g_sigtt.GetX()[i], sigtt_X_fit)
        g_sigtt_fit.SetPointError(i, 0, sigtt_X_fit_err)
        
    g_sigtt.SetTitle("Sig TT")

    g_sigtt.SetMarkerStyle(5)
    g_sigtt.Draw("AP")

    g_sigtt.GetXaxis().SetTitle("#it{-t} [GeV^{2}]")
    g_sigtt.GetXaxis().CenterTitle()
    g_sigtt.GetYaxis().SetTitle("#left(#frac{#it{d#sigma}}{#it{dt}}#right)_{TT} [nb/GeV^{2}]")
    g_sigtt.GetYaxis().SetTitleOffset(1.5)
    g_sigtt.GetYaxis().SetTitleSize(0.035)
    g_sigtt.GetYaxis().CenterTitle()
    
    g_sigtt_prv.SetMarkerColor(4)
    g_sigtt_prv.SetMarkerStyle(25)
    g_sigtt_prv.Draw("P")

    c2.cd(4).SetLeftMargin(0.12)
    g_sigtt_fit.SetTitle("Sigma TT Model Fit")
    g_sigtt_fit.Draw("A*")

    g_sigtt_fit.GetXaxis().SetTitle("#it{-t} [GeV^{2}]")
    g_sigtt_fit.GetXaxis().CenterTitle()
    g_sigtt_fit.GetYaxis().SetTitle("#left(#frac{#it{d#sigma}}{#it{dt}}#right)_{TT} [nb/GeV^{2}]")
    g_sigtt_fit.GetYaxis().SetTitleOffset(1.5)
    g_sigtt_fit.GetYaxis().SetTitleSize(0.035)
    g_sigtt_fit.GetYaxis().CenterTitle()
    
    ##############
    # HARD CODED #
    ##############
    f_sigTT = TF1("sig_TT", fun_Sig_TT, tmin_range, tmax_range, 1)
    f_sigTT.SetParNames("p13")
    #tt0 = 0.0
    #f_sigTT.SetParameters(tt0, 0.0)
    # Fixed unused parameters
    #f_sigTT.FixParameter(0, 0)
    ##f_sigTT.FixParameter(1, 0)
    ##f_sigTT.FixParameter(2, 0)
    ##f_sigTT.FixParameter(3, 0)
    # Set range limit of used parameters
    if tt0 != 0.0:
        f_sigTT.SetParLimits(0, tt0-abs(tt0*par_lim), tt0+abs(tt0*par_lim))
    else: 
        f_sigTT.SetParLimits(0, -par_lim, par_lim)
    # Fixing sigTT terms for testing
    #f_sigTT.FixParameter(0, tt0)
    # Fixing sigTT terms to zero
    #f_sigTT.FixParameter(0, 0.0)
    if DEBUG:
        f_sigTT.FixParameter(0, tt0)    
    ##############
    ##############
    ##############
    
    g_q2_sigtt_fit = TGraphErrors()
    for i in range(len(w_vec)):
        g_q2_sigtt_fit.SetPoint(i, g_sigtt.GetX()[i], sigtt_X_fit)
        g_q2_sigtt_fit.SetPointError(i, 0.0, sigtt_X_fit_err)
        sigtt_X = (f_sigTT.Eval(g_sigtt.GetX()[i]) * math.sin(th_vec[i] * PI / 180)**2) * (g_vec[i])
        g_sigtt_fit_tot.SetPoint(i, g_sigtt.GetX()[i], sigtt_X)
    # Options: S-> Simultaneous fit, M-> Improve fit info splash, R-> Use range specified, Q-> Quiet splash
    g_sigtt_fit.Fit(f_sigTT, "SM")

    # Check the fit status for 'f_sigTT'
    f_sigTT_status = f_sigTT.GetNDF()  # GetNDF() returns the number of degrees of freedom
    f_sigTT_status_message = "Not Fitted" if f_sigTT_status == 0 else "Fit Successful"

    f_sigTT.Draw("same")
    
    fit_status = TText()
    fit_status.SetTextSize(0.04)
    fit_status.DrawTextNDC(0.35, 0.85, " Fit Status: {}".format(f_sigTT_status_message))
        
    c1.cd(4)

    g_sigtt_fit_tot.SetMarkerStyle(26)
    g_sigtt_fit_tot.SetMarkerColor(2)
    g_sigtt_fit_tot.SetLineColor(2)
    g_sigtt_fit_tot.Draw("LP")
    
    par_vec.append(f_sigTT.GetParameter(0))
    par_vec.append(f_sigTT.GetParameter(1))
    par_vec.append(f_sigTT.GetParameter(2))
    par_vec.append(f_sigTT.GetParameter(3))

    par_err_vec.append(f_sigTT.GetParError(0))
    par_err_vec.append(f_sigTT.GetParError(1))
    par_err_vec.append(f_sigTT.GetParError(2))
    par_err_vec.append(f_sigTT.GetParError(3))

    par_chi2_vec.append(f_sigTT.GetChisquare())
    par_chi2_vec.append(f_sigTT.GetChisquare())
    par_chi2_vec.append(f_sigTT.GetChisquare())
    par_chi2_vec.append(f_sigTT.GetChisquare())
    
    c1.Print(outputpdf+'(')
    c2.Print(outputpdf+')')
    
    for i, (old, new) in enumerate(zip(prv_par_vec, par_vec)):
        if old != new:
            print("par{} changed from {:.3f} to {:.3f}".format(i+1, old, new))
            
    # Don't write to new parameter file if debugging
    if not DEBUG:
        para_file_out = "{}/src/{}/parameters/par.{}_Q{}W{}.dat".format(LTANAPATH, ParticleType, pol_str, q2_set.replace("p",""), w_set.replace("p",""))
        print("\nWriting {}...".format(para_file_out))
        with open(para_file_out, 'w') as f:
            for i in range(len(par_vec)):
                f.write("{:13.5e} {:13.5e} {:3d} {:12.1f}\n".format(par_vec[i], par_err_vec[i], i+1, par_chi2_vec[i]))
                print("  {:.3f} {:.3f} {:.1f} {:.1f}".format(par_vec[i], par_err_vec[i], i+1, par_chi2_vec[i]))
    else:
        print("\n\nDEBUG ENABLED: No changes to previous iteration...")
        for i,par in enumerate(prv_par_vec):
            print("par{} = {:.3f}".format(i+1, par))
