# cmsDriver.py --python_filename HIG-RunIISummer20UL18NanoAODv9-02146_1_cfg.py --eventcontent NANOAODSIM --datatier NANOAODSIM --fileout file:HIG-RunIISummer20UL18NanoAODv9-02146.root --conditions 106X_upgrade2018_realistic_v16_L1v1 --step NANO --era Run2_2018,run2_nanoAOD_106Xv2 --no_exec --mc -n 100

import FWCore.ParameterSet.Config as cms

from Configuration.Eras.Era_Run2_2018_cff import Run2_2018
from Configuration.Eras.Modifier_run2_nanoAOD_106Xv2_cff import run2_nanoAOD_106Xv2

process = cms.Process('NANO',Run2_2018,run2_nanoAOD_106Xv2)


# import of standard configurations
process.load('Configuration.StandardSequences.Services_cff')
process.load('SimGeneral.HepPDTESSource.pythiapdt_cfi')
process.load('FWCore.MessageService.MessageLogger_cfi')
process.load('Configuration.EventContent.EventContent_cff')
process.load('SimGeneral.MixingModule.mixNoPU_cfi')
process.load('Configuration.StandardSequences.GeometryRecoDB_cff')
process.load('Configuration.StandardSequences.MagneticField_cff')
#process.load('PhysicsTools.NanoAOD.nano_cff')
process.load('PhysicsTools.NanoAOD.nano_addHto4bPlus_cff')
process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')

process.maxEvents = cms.untracked.PSet(                                                                                                                                                                                                                      
    input = cms.untracked.int32(100) 
    #input = cms.untracked.int32(-1)                                                                                                                                                                                                                     
)

# Input source
process.source = cms.Source("PoolSource",
    #fileNames = cms.untracked.vstring('DUMMY'),
    #fileNames = cms.untracked.vstring('file:/eos/cms/store/group/phys_susy/HToaaTo4b/MiniAOD/2018/MC/SUSY_GluGluH_01J_HToAATo4B_Pt150_M-20_TuneCP5_13TeV_madgraph_pythia8/RunIISummer20UL18/003A1234-0E1D-154A-9704-9406B61CB642.root'),
    fileNames = cms.untracked.vstring('file:/eos/cms/store/group/phys_susy/HToaaTo4b/MiniAOD/2018/MC/SUSY_GluGluH_01J_HToAATo4B_Pt150_M-20_TuneCP5_13TeV_madgraph_pythia8/RunIISummer20UL18/0B5221FE-B9CF-A449-A523-33FFCAF65CD2.root'),
    secondaryFileNames = cms.untracked.vstring()
)
process.options = cms.untracked.PSet(
)

# Production Info
process.configurationMetadata = cms.untracked.PSet(
    annotation = cms.untracked.string('--python_filename nevts:100'),
    name = cms.untracked.string('Applications'),
    version = cms.untracked.string('$Revision: 1.19 $')
)

# Output definition
process.NANOAODSIMoutput = cms.OutputModule("NanoAODOutputModule",
    #skimFatJet = cms.untracked.bool(True),
    compressionAlgorithm = cms.untracked.string('LZMA'),
    compressionLevel = cms.untracked.int32(9),
    dataset = cms.untracked.PSet(
        dataTier = cms.untracked.string('NANOAODSIM'),
        filterName = cms.untracked.string('')
    ),
    fileName = cms.untracked.string('PNet_v1.root'),
    outputCommands = process.NANOAODSIMEventContent.outputCommands
)
# Additional output definition

# Other statements
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2018_realistic_v16_L1v1', '')

# Path and EndPath definitions
process.nanoAOD_step = cms.Path(process.nanoSequenceMC)
process.endjob_step = cms.EndPath(process.endOfProcess)
process.NANOAODSIMoutput_step = cms.EndPath(process.NANOAODSIMoutput)

# Schedule definition
process.schedule = cms.Schedule(process.nanoAOD_step,process.endjob_step,process.NANOAODSIMoutput_step)
from PhysicsTools.PatAlgos.tools.helpers import associatePatAlgosToolsTask
associatePatAlgosToolsTask(process)

# customisation of the process.
# Automatic addition of the customisation function from PhysicsTools.NanoAOD.nano_addHto4bPlus_cff
from PhysicsTools.NanoAOD.nano_addHto4bPlus_cff import nanoAOD_customizeMC 
#call to customisation function nanoAOD_customizeMC imported from PhysicsTools.NanoAOD.nano_addHto4bPlus_cff
process = nanoAOD_customizeMC(process, True)
#process = nanoAOD_customizeMC(process, False)


# Automatic addition of the customisation function from PhysicsTools.NanoAOD.nano_cff
#from PhysicsTools.NanoAOD.nano_cff import nanoAOD_customizeMC 
#call to customisation function nanoAOD_customizeMC imported from PhysicsTools.NanoAOD.nano_cff
#process = nanoAOD_customizeMC(process)

# add PF branches
#from PhysicsTools.PFNano.pfnano_cff import PFnano_customizeMC
#process = PFnano_customizeMC(process)
# End of customisation functions

# Customisation from command line

# Add early deletion of temporary data products to reduce peak memory need
from Configuration.StandardSequences.earlyDeleteSettings_cff import customiseEarlyDelete
process = customiseEarlyDelete(process)
# End adding early deletion
