#!/usr/bin/env python
#from exampleModule import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetUncertainties import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.PrefireCorr import *
from PhysicsTools.NanoAODTools.postprocessing.modules.btv.btagSFProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.haa4b.objectSelection import Haa4bObjectSelectionProducer
from PhysicsTools.NanoAODTools.postprocessing.modules.haa4b.genParticles import Haa4bGenParticlesBranches
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from importlib import import_module
import os
import sys
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

IS_MC = True
YEAR  = '2018'

# this takes care of converting the input files from CRAB
#from PhysicsTools.NanoAODTools.postprocessing.framework.crabhelper import inputFiles, runsAndLumis

# soon to be deprecated
# new way of using jme uncertainty


# Function parameters
# (isMC=True, dataYear=2016, runPeriod="B", jesUncert="Total", redojec=False, jetType = "AK4PFchs", noGroom=False)
# All other parameters will be set in the helper module

#jmeCorrections = createJMECorrector(
#    True, "2016", "B", "Total", True, "AK4PFchs", False)
#jmeCorrections = createJMECorrector(
#    True, "2018", "D", "Total", True, "AK8PFchs", False)
#jmeCorrections = createJMECorrector(
#    True, "UL2018", "D", "Total", "AK8PFchs", False)
jmeCorrectionsAK8 = createJMECorrector(
    isMC          = True, 
    dataYear      = "UL"+YEAR,
    runPeriod     = "D", 
    jesUncert     = "Total", 
    jetType       = "AK8PFPuppi", # AK8PFPuppi, AK4PFchs
    noGroom       = False,
    applySmearing = True,
    isFastSim     = False,
    applyHEMfix   = False,
    splitJER      = False,
    saveMETUncs   = ['T1', 'T1Smear'])

jmeCorrectionsAK4 = createJMECorrector(
    isMC          = True, 
    dataYear      = "UL"+YEAR,
    runPeriod     = "D", 
    jesUncert     = "Total", 
    jetType       = "AK4PFchs", # AK8PFPuppi, AK4PFchs
    noGroom       = False,
    applySmearing = True,
    isFastSim     = False,
    applyHEMfix   = False,
    splitJER      = False,
    saveMETUncs   = ['T1', 'T1Smear'])

## PU weights
if YEAR == '2018':
    puWeights = puWeight_UL2018

## Prefiring corrections

'''
l1PrefirCorr2017 = lambda: PrefCorr(
    jetroot="L1prefiring_jetpt_2017BtoF.root",
    jetmapname="L1prefiring_jetpt_2017BtoF",
    photonroot="L1prefiring_photonpt_2017BtoF.root",
    photonmapname="L1prefiring_photonpt_2017BtoF",
    branchnames=[
        "PrefireWeight", "PrefireWeight_Up", "PrefireWeight_Down"
    ]
)
'''

# b-tag SF producer
btagSF = lambda: btagSFProducer(
    era = 'UL'+YEAR,
    algo='deepjet', 
    selectedWPs=['M', 'shape_corr'],
    sfFileName=None, 
    verbose=0, 
    jesSystsForShape=["jes"]
)

#fnames = ["/eos/cms/store/mc/RunIISummer16NanoAODv5/DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8/NANOAODSIM/PUMoriond17_Nano1June2019_102X_mcRun2_asymptotic_v7_ext2-v1/120000/FF69DF6E-2494-F543-95BF-F919B911CD23.root"]
#fnames = ["/afs/cern.ch/work/s/ssawant/private/htoaa/NanoAODProduction_wPNetHToAATo4B/CMSSW_10_6_30/src/test/PNet_v1.root"] 
#fnames = ["/eos/cms/store/user/ssawant/NanoPost/SUSY_GluGluH_01J_HToAATo4B_Pt150_M-20_TuneCP5_13TeV_madgraph_pythia8/NanoTestPost/240921_092131/0000/PNet_v1_1.root"] 
#fnames = ["/eos/cms/store/user/ssawant/NanoPost/SUSY_GluGluH_01J_HToAATo4B_Pt150_M-20_TuneCP5_13TeV_madgraph_pythia8/2017/2BFC55D0-269D-5045-8CF4-6174A5DEA5E7.root"] # 2017 sample
#fnames=["/afs/cern.ch/work/a/abrinke1/public/HiggsToAA/NanoAOD/crab/2018/CMSSW_10_6_30/src/PhysicsTools/NanoAOD/output/HtoAA_addHto4bPlus_HtoAA_MH-125_MA-50_Pt170_Eta2p4_Msoft10_Xbb0p6_skimFatCand_10k.root"]
fnames=["/afs/cern.ch/work/a/abrinke1/public/HiggsToAA/NanoAOD/crab/2018/CMSSW_10_6_30/src/PhysicsTools/NanoAOD/output/HtoAA_addHto4bPlus_ggH_HtoAA_MH-125_MA-32.5_Pt170_Eta2p4_Msoft10_Xbb0p6_skimFatCand_100k.root"]
#fnames=["/afs/cern.ch/work/a/abrinke1/public/HiggsToAA/NanoAOD/crab/2018/CMSSW_10_6_30/src/PhysicsTools/NanoAOD/output/HtoAA_addHto4bPlus_ggHToBB_Pt-200toInf_Pt170_Eta2p4_Msoft10_Xbb0p6_skimFatCand_20k.root"]
#fnames=["/afs/cern.ch/work/a/abrinke1/public/HiggsToAA/NanoAOD/crab/2018/CMSSW_10_6_30/src/PhysicsTools/NanoAOD/output/HtoAA_addHto4bPlus_JetHT_2018C_Pt170_Eta2p4_Msoft10_Xbb0p6_skimFatCand_100k.root"]

#fnames = ["PNet_v1.root"] 
##fnames = inputFiles()

# p=PostProcessor(".",fnames,"Jet_pt>150","",[jetmetUncertainties2016(),exampleModuleConstr()],provenance=True)
#p = PostProcessor(".", fnames, "Jet_pt>150", "", [
#                  jmeCorrections(), exampleModuleConstr()], provenance=True)
#p = PostProcessor(".", 
#                  fnames, "",  
#                  modules=[jmeCorrections()], 
#                  provenance=True,
#                  fwkJobReport=True,
#                  jsonInput=runsAndLumis())
p = PostProcessor(
    outputDir=".", 
    inputFiles=fnames, 
    #cut="",  
    modules=[
        jmeCorrectionsAK8(),
        #jmeCorrectionsAK4(),
        #puWeights(),
        #l1PrefirCorr2017(),
        #btagSF(),
        Haa4bGenParticlesBranches(),
        Haa4bObjectSelectionProducer(IS_MC, YEAR)
        ], 
    provenance=True,
    fwkJobReport=True,
    #jsonInput=runsAndLumis()
    )
p.run()

print("DONE example_postproc_1_AWB.py")
