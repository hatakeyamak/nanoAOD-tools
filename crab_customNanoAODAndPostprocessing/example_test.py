#!/usr/bin/env python
#from exampleModule import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetHelperRun2 import *
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetmetUncertainties import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.puWeightProducer import *
from PhysicsTools.NanoAODTools.postprocessing.modules.common.PrefireCorr import *
from PhysicsTools.NanoAODTools.postprocessing.modules.btv.btagSFProducer import *
from PhysicsTools.NanoAODTools.postprocessing.framework.postprocessor import PostProcessor
from importlib import import_module
import os
import sys
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True 
import correctionlib
import correctionlib._core as correctionlibcore
import numpy as np

print('correctionlibcore:',correctionlibcore)
print('correctionlibcore.CorrectionSet:',correctionlibcore.CorrectionSet)
print('correctionlibcore.CorrectionSet.from_file:',correctionlibcore.CorrectionSet.from_file('../data/jme/Substructure_jmssf_UL_PhysicsResultsDP23044.json'))

print('os.environ[\'CMSSW_BASE\']',os.environ['CMSSW_BASE'])

print('correctionlibcore.CorrectionSet.from_file:',correctionlibcore.CorrectionSet.from_file(os.environ['CMSSW_BASE']+'/src/PhysicsTools/NanoAODTools/data/jme/Substructure_jmssf_UL_PhysicsResultsDP23044.json'))

sFJMSSF = os.environ['CMSSW_BASE']+'/src/PhysicsTools/NanoAODTools/data/jme/Substructure_jmssf_UL_PhysicsResultsDP23044.json'
print('sFJMSSF: ',sFJMSSF)
corr_FatJetSubstrc = correctionlibcore.CorrectionSet.from_file(sFJMSSF)


print('corr_FatJetSubstrc[\'jmssf_UL18\'].evaluate(250.0, \'\')', corr_FatJetSubstrc['jmssf_UL18'].evaluate(250.0, ''))

sBTVSF = '/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/BTV/2018_UL/btagging.json.gz'
print('sBTVSF: ',sBTVSF)
corr_JetBTagSF = correctionlibcore.CorrectionSet.from_file(sBTVSF)

print('SF: ', corr_JetBTagSF["deepJet_comb"].evaluate("central", "M", 5, 1.3, 130.0))
print('SF: ', corr_JetBTagSF["deepJet_incl"].evaluate("central", "L", 0, 1.3, 130.0))
print('corr_JetBTagSF: ', type(corr_JetBTagSF), ' ', corr_JetBTagSF, ', ', dir(corr_JetBTagSF))
print('corr_JetBTagSF.describe()', corr_JetBTagSF.description)

#print('corr_JetBTagSF.itput ', corr_JetBTagSF.keys())

print('corr_JetBTagSF["deepJet_comb"]: ', type(corr_JetBTagSF["deepJet_comb"]), ' ', corr_JetBTagSF["deepJet_comb"], ', ', dir(corr_JetBTagSF["deepJet_comb"]), " \n")
#print('', corr_JetBTagSF.)

for corr in corr_JetBTagSF:
    #print('corr: ', type(corr), ' ', corr, ', ', dir(corr), ', ',corr_JetBTagSF[corr])
    #print('corr_JetBTagSF[corr]: ', type(corr_JetBTagSF[corr]), ' ', corr_JetBTagSF[corr], ', ', dir(corr_JetBTagSF[corr]))
    
    print(corr, ', ', corr_JetBTagSF[corr].name, ', ', corr_JetBTagSF[corr].description, ', ', corr_JetBTagSF[corr].inputs, ', ', corr_JetBTagSF[corr].output, ', ')