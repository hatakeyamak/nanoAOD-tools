#!/usr/bin/env python
#from exampleModule import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetUncertainties import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.PrefireCorr import *
#from PhysicsTools.NanoAODTools.postprocessing.modules.btv.btagSFProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.btv.btagSFProducerUL import *
from PhysicsTools.NanoAODTools.postprocessing.modules.haa4b.objectSelection import Haa4bObjectSelectionProducer
from PhysicsTools.NanoAODTools.postprocessing.modules.haa4b.genParticles import Haa4bGenParticlesBranches
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from importlib import import_module
import os
import sys
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True 
import re


runLocally = False

  
RunEraForMC = { #
    'UL2016_preVFP': 'E',
    'UL2016': 'G',
    'UL2017': 'F',
    'UL2018': 'D',      
}

isMC = True
DataYear  = 'UL2018'
RunPeriod = 'D'

if not runLocally:
    # this takes care of converting the input files from CRAB
    from PhysicsTools.NanoAODTools.postprocessing.framework.crabhelper import inputFiles, runsAndLumis

    crabFiles = inputFiles()
    for iFile in range(0, len(crabFiles)):
        #print("\n\nexample_postproc_1.py:: crabFiles[iFile] (", type(crabFiles[iFile]), ') : ', crabFiles[iFile])
        # file name:
        # /store/data/Run2018A/JetHT/MINIAOD/UL2018_MiniAODv2_GT36-v1/2820000/06B31097-D7BB-A54A-80EE-C2823A835177.root
        # /store/mc/RunIISummer20UL18MiniAODv2/SUSY_ZH_ZToAll_HToAATo4B_Pt150_M-20_TuneCP5_13TeV_madgraph_pythia8/MINIAODSIM/106X_upgrade2018_realistic_v16_L1v1-v1/2520000/0EA35ABE-277F-6543-8296-CE3476695505.root

        dataType = re.search('/store/(?P<DataType>\w+)/', crabFiles[iFile]).group('DataType') # '/store/mc/'
        isMC = True if dataType.lower() == 'mc' else False

        if not isMC:
            r_ = re.search('Run(?P<DataYear>\d{4})(?P<RunPeriod>[a-zA-Z])', crabFiles[iFile]) # '/store/data/Run2018A/'
            DataYear  = r_.group('DataYear')
            RunPeriod = r_.group('RunPeriod')
        else:
            r_ = re.search('RunIISummer20UL(?P<DataYear>\d{2})MiniAOD', crabFiles[iFile]) # '/store/mc/RunIISummer20UL18MiniAODv2/'
            DataYear  = '20%s' % (r_.group('DataYear'))
            if 'APV' in crabFiles[iFile]:
                DataYear += '_preVFP'

        if 'UL' in crabFiles[iFile]:
            DataYear = 'UL%s' % (DataYear)

        if isMC:
            RunPeriod = RunEraForMC[DataYear]

        print('example_postproc_1.py:: ', crabFiles[iFile], DataYear, RunPeriod)
        break

    print('example_postproc_1.py:: DataYear: ', DataYear, ', RunPeriod: ', RunPeriod)




jmeCorrectionsAK8 = createJMECorrector(
    isMC          = isMC, 
    dataYear      = DataYear, 
    runPeriod     = RunPeriod, 
    jesUncert     = "Total", # Options: "Total", "All"
    jetType       = "AK8PFPuppi", # AK8PFPuppi, AK4PFchs
    noGroom       = False,
    applyWJMS     = False, 
    applyMsdJMS   = False,
    applyMsdJMR   = False,
    applySmearing = True,
    isFastSim     = False,
    applyHEMfix   = True, # <<<< True for 2018: additional "HEMIssue" uncertainty 
    splitJER      = False,
    saveMETUncs   = ['T1', 'T1Smear'])

jmeCorrectionsAK4 = createJMECorrector(
    isMC          = isMC, 
    dataYear      = DataYear, 
    runPeriod     = RunPeriod, 
    jesUncert     = "Total", 
    jetType       = "AK4PFchs", # AK8PFPuppi, AK4PFchs
    noGroom       = False,
    applySmearing = True,
    isFastSim     = False,
    applyHEMfix   = True, # <<<< True for 2018: additional "HEMIssue" uncertainty
    splitJER      = False,
    saveMETUncs   = ['T1', 'T1Smear'])


modulesToRun = [
    jmeCorrectionsAK8(),
    jmeCorrectionsAK4()
]

if isMC:
    ## PU weights
    puWeights = None
    if   '16' in DataYear:
        puWeights = puWeight_UL2016
    elif '17' in DataYear:
        puWeights = puWeight_UL2017
    elif '18' in DataYear:
        puWeights = puWeight_UL2018
    else:
        print('example_postproc_1.py:: puWeights DataYear ', DataYear, ' not compatible *** ERROR ***')
        exit(0)
        

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
        era = DataYear, 
        algo='deepjet', 
        selectedWPs=['M'], #['M', 'shape_corr'],
        sfFileName=None, 
        verbose=0, 
        jesSystsForShape=["jes"]
    )

    modulesToRun.extend([
        puWeights(),
        btagSF(),
        Haa4bGenParticlesBranches(),
    ])

modulesToRun.extend([
    Haa4bObjectSelectionProducer(isMC, DataYear.replace('UL', ''))
])

fnames = ["PNet_v1.root"] 
if runLocally:
    fnames = ["/afs/cern.ch/work/s/ssawant/private/htoaa/NanoAODProduction_wPNetHToAATo4B/CMSSW_10_6_30/src/PhysicsTools/NanoAOD/output/HtoAA_addHto4bPlus_ggH_HtoAA_MH-125_MA-32.5_Pt170_Eta2p4_Msoft10_Xbb0p6_skimFatCand_1k.root"]



p = PostProcessor(
    outputDir=".", 
    inputFiles=fnames, 
    #cut="",  
    modules=modulesToRun, 
    #provenance=True,
    #fwkJobReport=True,
    #jsonInput=runsAndLumis()
    )
p.run()

print("DONE example_postproc_1.py")
