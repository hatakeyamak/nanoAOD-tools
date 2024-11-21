#!/usr/bin/env python
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetUncertainties import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.PrefireCorr import *
from PhysicsTools.NanoAODTools.postprocessing.modules.btv.btagSFProducerUL import *
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
runLocally = True

if not runLocally:
    ## This takes care of converting the input files from CRAB
    from PhysicsTools.NanoAODTools.postprocessing.framework.crabhelper import inputFiles, runsAndLumis

jmeCorrectionsAK8 = createJMECorrector(
    isMC          = IS_MC,
    dataYear      = "UL"+YEAR,
    runPeriod     = "D", 
    jesUncert     = "Total",      # Options: Total, All
    jetType       = "AK8PFPuppi", # Options: AK8PFPuppi, AK4PFchs
    noGroom       = False,
    applyWJMS     = False, 
    applyMsdJMS   = False,
    applyMsdJMR   = False,
    applySmearing = True,
    isFastSim     = False,
    applyHEMfix   = (YEAR == '2018'),
    splitJER      = False,
    saveMETUncs   = ['T1', 'T1Smear'])

jmeCorrectionsAK4 = createJMECorrector(
    isMC          = IS_MC,
    dataYear      = "UL2018", 
    runPeriod     = "D", 
    jesUncert     = "Total", 
    jetType       = "AK4PFchs", # Options: AK8PFPuppi, AK4PFchs
    noGroom       = False,
    applySmearing = True,
    isFastSim     = False,
    applyHEMfix   = (YEAR == '2018'),
    splitJER      = False,
    saveMETUncs   = ['T1', 'T1Smear'])

## PU weights
if YEAR == '2018':
    puWeights = puWeight_UL2018
elif YEAR == '2017':
    puWeights = puWeight_UL2017
elif YEAR == '2016':
    puWeights = puWeight_UL2016

## Prefiring corrections
l1PrefirCorr2017 = lambda: PrefCorr(
    jetroot="L1prefiring_jetpt_2017BtoF.root",
    jetmapname="L1prefiring_jetpt_2017BtoF",
    photonroot="L1prefiring_photonpt_2017BtoF.root",
    photonmapname="L1prefiring_photonpt_2017BtoF",
    branchnames=["PrefireWeight%s" % suff  for suff in ["","_Up","_Down"]],
)

# b-tag SF producer
btagSF = lambda: btagSFProducer(
    era = 'UL'+YEAR,
    algo='deepjet', 
    selectedWPs=['M'], # To include shapes: ['M', 'shape_corr']
    sfFileName=None, 
    verbose=0, 
    jesSystsForShape=["jes"]
)

#fnames = ["/eos/cms/store/user/ssawant/NanoPost/SUSY_GluGluH_01J_HToAATo4B_Pt150_M-20_TuneCP5_13TeV_madgraph_pythia8/NanoTestPost/240921_092131/0000/PNet_v1_1.root"] 
#fnames = ["/eos/cms/store/user/ssawant/NanoPost/SUSY_GluGluH_01J_HToAATo4B_Pt150_M-20_TuneCP5_13TeV_madgraph_pythia8/2017/2BFC55D0-269D-5045-8CF4-6174A5DEA5E7.root"] # 2017 sample
fnames=["/afs/cern.ch/work/a/abrinke1/public/HiggsToAA/NanoAOD/crab/2018/CMSSW_10_6_30/src/PhysicsTools/NanoAOD/output/HtoAA_addHto4bPlus_ggH_HtoAA_MH-125_MA-32.5_Pt170_Eta2p4_Msoft10_Xbb0p6_skimFatCand_100k.root"]
#fnames=["/afs/cern.ch/work/a/abrinke1/public/HiggsToAA/NanoAOD/crab/2018/CMSSW_10_6_30/src/PhysicsTools/NanoAOD/output/HtoAA_addHto4bPlus_ggHToBB_Pt-200toInf_Pt170_Eta2p4_Msoft10_Xbb0p6_skimFatCand_20k.root"]

if not runLocally:
    print("Hto4b_postproc_MC.py:: inputFiles() ", type(inputFiles()), ' : ',  inputFiles())
    print("Hto4b_postproc_MC.py:: runsAndLumis ", type(runsAndLumis()), ' : ', runsAndLumis())

p = PostProcessor(
    outputDir=".", 
    inputFiles=fnames, 
    modules=[
        jmeCorrectionsAK8(),
        jmeCorrectionsAK4(),
        puWeights(),
        btagSF(),
        Haa4bGenParticlesBranches(),
        Haa4bObjectSelectionProducer(IS_MC, YEAR)
        ] + ([l1PrefirCorr2017()] if YEAR == '2017' else []), 
    )
p.run()

print("DONE Hto4b_postproc_MC.py")
