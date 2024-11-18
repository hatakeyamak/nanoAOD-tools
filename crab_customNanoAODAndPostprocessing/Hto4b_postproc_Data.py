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

IS_MC = False
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

fnames=["/afs/cern.ch/work/a/abrinke1/public/HiggsToAA/NanoAOD/crab/2018/CMSSW_10_6_30/src/PhysicsTools/NanoAOD/output/HtoAA_addHto4bPlus_JetHT_2018C_Pt170_Eta2p4_Msoft10_Xbb0p6_skimFatCand_56k.root"]

if not runLocally:
    print("Hto4b_postproc_Data.py:: inputFiles() ", type(inputFiles()), ' : ',  inputFiles())
    print("Hto4b_postproc_Data.py:: runsAndLumis ", type(runsAndLumis()), ' : ', runsAndLumis())

p = PostProcessor(
    outputDir=".", 
    inputFiles=fnames, 
    modules=[
        jmeCorrectionsAK8(),
        jmeCorrectionsAK4(),
        Haa4bObjectSelectionProducer(IS_MC, YEAR)
        ]
    )
p.run()

print("DONE Hto4b_postproc_Data.py")
