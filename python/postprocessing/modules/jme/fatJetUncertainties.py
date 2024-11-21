from PhysicsTools.NanoAODTools.postprocessing.modules.jme.JetReCalibrator import JetReCalibrator
from PhysicsTools.NanoAODTools.postprocessing.modules.jme.jetSmearer import jetSmearer
from PhysicsTools.NanoAODTools.postprocessing.tools import matchObjectCollection, matchObjectCollectionMultiple
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection, Object
import ROOT
import math
import os
import re
import tarfile
import tempfile
import shutil
import numpy as np
ROOT.PyConfig.IgnoreCommandLineOptions = True
import correctionlib._core as correctionlibcore

## Round pt and mass to 1 decimal place
def rnd(inList):
    return [round(val,1) for val in inList]

class fatJetUncertaintiesProducer(Module):
    def __init__(
            self,
            era,
            globalTag,
            jesUncertainties=["Total"],
            archive=None,
            jetType="AK8PFPuppi",
            noGroom=False,
            jerTag="",
            jmrVals=[],
            jmsVals=[],
            jmsMsdVals=[],
            applyWJMS=True, # apply W-JetMassScale, formally known as puppi correction https://twiki.cern.ch/twiki/bin/view/CMS/JetWtagging#W_Jet_Mass_Scale_W_JMS_correctio 
            applyMsdJMS=True,
            applyMsdJMR=True,
            isData=False,
            applySmearing=True,
            applyHEMfix=False,
            splitJER=False
    ):
        self.era = era
        self.noGroom = noGroom
        self.isData = isData
        self.applySmearing = applySmearing if not isData else False  # don't smear for data
        self.applyWJMS   = applyWJMS
        self.applyMsdJMS = applyMsdJMS
        self.applyMsdJMR = applyMsdJMR
        self.storeMassJMS = self.storeMassJMR = False 
        # No need to store JMS, JMR related branches if JMS, JMR are equal to 1
        for j_ in jmsVals:
            if abs(j_ - 1.0) > 1e-10: 
                self.storeMassJMS = True
                break
        for j_ in jmrVals:
            if abs(j_ - 1.0) > 1e-10: 
                self.storeMassJMR = True
                break            
        print('self.storeMassJMS ',self.storeMassJMS)
        print('self.storeMassJMR ',self.storeMassJMR)        
        # ---------------------------------------------------------------------
        # CV: globalTag and jetType not yet used in the jet smearer, as there
        # is no consistent set of txt files for JES uncertainties and JER scale
        # factors and uncertainties yet
        # ---------------------------------------------------------------------
        self.splitJER = splitJER
        if self.splitJER:
            self.splitJERIDs = list(range(6))
        else:
            self.splitJERIDs = [""]  # "empty" ID for the overall JER

        self.jesUncertainties = jesUncertainties
        # smear jet pT to account for measured difference in JER between data
        # and simulation.
        if jerTag != "":
            self.jerInputFileName = jerTag + "_PtResolution_" + jetType + ".txt"
            self.jerUncertaintyInputFileName = jerTag + "_SF_" + jetType + ".txt"
        else:
            print(
                "WARNING: jerTag is empty!!! This module will soon be "
                "deprecated! Please use jetmetHelperRun2 in the future."
            )
            if era == "2016":
                self.jerInputFileName = ''.join([
                    "Summer16_25nsV1_MC_PtResolution_", jetType, ".txt"])
                self.jerUncertaintyInputFileName = ''.join([
                    "Summer16_25nsV1_MC_SF_", jetType, ".txt"])
            elif era == "2017" or era == "2018":
            # use Fall17 as temporary placeholder until
            # post-Moriond 2019 JERs are out
                self.jerInputFileName = ''.join([
                    "Fall17_V3_MC_PtResolution_", jetType, ".txt"])
                self.jerUncertaintyInputFileName = ''.join([
                    "Fall17_V3_MC_SF_", jetType, ".txt"])

        # jet mass resolution: https://twiki.cern.ch/twiki/bin/view/CMS/JetWtagging
        self.jmrVals = jmrVals
        if not self.jmrVals:
            print(
                "WARNING: jmrVals is empty!!! Using default values. This "
                "module will soon be deprecated! Please use "
                "jetmetHelperRun2 in the future."
            )
            self.jmrVals = [1.0, 1.2, 0.8]  # nominal, up, down
            # Use 2017 values for 2018 until 2018 are released
            if self.era in ["2017", "2018"]:
                self.jmrVals = [1.09, 1.14, 1.04]

        self.jetSmearer = jetSmearer(globalTag, jetType, self.jerInputFileName,
                                     self.jerUncertaintyInputFileName,
                                     self.jmrVals)

        if "AK4" in jetType:
            self.jetBranchName = "Jet"
            self.genJetBranchName = "GenJet"
            self.genSubJetBranchName = None
            self.doGroomed = False
        elif "AK8" in jetType:
            self.jetBranchName = "FatJet"
            self.subJetBranchName = "SubJet"
            self.genJetBranchName = "GenJetAK8"
            self.genSubJetBranchName = "SubGenJetAK8"
            if not self.noGroom:
                self.doGroomed = True
                self.puppiCorrFile = ROOT.TFile.Open(
                    os.environ['CMSSW_BASE'] +
                    "/src/PhysicsTools/NanoAODTools/data/jme/puppiCorr.root")
                self.puppisd_corrGEN = self.puppiCorrFile.Get(
                    "puppiJECcorr_gen")
                self.puppisd_corrRECO_cen = self.puppiCorrFile.Get(
                    "puppiJECcorr_reco_0eta1v3")
                self.puppisd_corrRECO_for = self.puppiCorrFile.Get(
                    "puppiJECcorr_reco_1v3eta2v5")
            else:
                self.doGroomed = False
        else:
            raise ValueError("ERROR: Invalid jet type = '%s'!" % jetType)
        self.rhoBranchName = "fixedGridRhoFastjetAll"
        self.lenVar = "n" + self.jetBranchName

        # jet mass scale
        print('jmsVals: ',jmsVals)
        self.jmsVals = jmsVals
        if not self.jmsVals:
            print(
                "WARNING: jmsVals is empty!!! Using default values! This "
                + "module will soon be deprecated! Please use "
                + "jetmetHelperRun2 in the future."
            )
            # 2016 values
            self.jmsVals = [1.00, 0.9906, 1.0094]  # nominal, down, up
            # Use 2017 values for 2018 until 2018 are released
            if self.era in ["2017", "2018"]:
                self.jmsVals = [0.982, 0.978, 0.986]
        print('jmsMsdVals: ',jmsMsdVals)
        self.jmsMsdVals = jmsMsdVals                
        # load (pT, eta) dependent JMS for Ultra-legacy Run2 data: https://twiki.cern.ch/twiki/bin/view/CMSPublic/PhysicsResultsDP23044
        self.jmsMsdVals_funcOfPtEta = None
        if 'UL' in self.era and self.jmsMsdVals and isinstance(self.jmsMsdVals[0], str): 
            if '16_preVFP' in self.era:
                corrEraName = 'UL16preVFP'
            elif '16' in self.era:
                corrEraName = 'UL16postVFP'
            elif '17' in self.era:
                corrEraName = 'UL17'
            elif '18' in self.era:
                corrEraName = 'UL18'
            self.jmsMsdVals_funcOfPtEta_file = os.environ['CMSSW_BASE']+'/src/'+self.jmsMsdVals[0]
            correction_dict = correctionlibcore.CorrectionSet.from_file(self.jmsMsdVals_funcOfPtEta_file)
            self.jmsMsdVals_funcOfPtEta = correction_dict['jmssf_%s' % corrEraName]
            self.jmsMsdVals = [1.000, 1.000, 1.000]  # dummy
            #print('self.jmsMsdVals_funcOfPtEta: ', self.jmsMsdVals_funcOfPtEta)
            #print('self.jmsVals: ', self.jmsVals)
            
            
            

        # read jet energy scale (JES) uncertainties
        # (downloaded from https://twiki.cern.ch/twiki/bin/view/CMS/JECDataMC )
        self.jesInputArchivePath = os.environ['CMSSW_BASE'] + \
            "/src/PhysicsTools/NanoAODTools/data/jme/"
        # Text files are now tarred so must extract first into temporary
        # directory (gets deleted during python memory management at script exit)
        jesInputFileName = self.jesInputArchivePath + globalTag + ".tgz" if not archive else self.jesInputArchivePath + archive + ".tgz"
        print('fatjetUncertainties.py:: jesInputFileName: ',jesInputFileName)
        self.jesArchive = tarfile.open(
            self.jesInputArchivePath + globalTag +
            ".tgz", "r:gz") if not archive else tarfile.open(
                self.jesInputArchivePath + archive + ".tgz", "r:gz")
        self.jesInputFilePath = tempfile.mkdtemp()
        self.jesArchive.extractall(self.jesInputFilePath)

        if len(jesUncertainties) == 1 and jesUncertainties[0] == "Total":
            self.jesUncertaintyInputFileName = globalTag + "_Uncertainty_" + jetType + ".txt"
        elif jesUncertainties[0] == "Merged" and not self.isData:
            self.jesUncertaintyInputFileName = "Regrouped_" + \
                globalTag + "_UncertaintySources_" + jetType + ".txt"
        else:
            self.jesUncertaintyInputFileName = globalTag + \
                "_UncertaintySources_" + jetType + ".txt"

        # read all uncertainty source names from the loaded file
        if jesUncertainties[0] in ["All", "Merged"]:
            with open(self.jesInputFilePath + '/' +
                      self.jesUncertaintyInputFileName) as f:
                lines = f.read().split("\n")
                sources = [
                    x for x in lines if x.startswith("[") and x.endswith("]")
                ]
                sources = [x[1:-1] for x in sources]
                self.jesUncertainties = sources
        if applyHEMfix:
            self.jesUncertainties.append("HEMIssue")
        print('self.jesUncertainties: ',self.jesUncertainties)

        self.jetReCalibrator = JetReCalibrator(
            globalTag,
            jetType,
            True,
            self.jesInputFilePath,
            calculateSeparateCorrections=False,
            calculateType1METCorrection=False)

        # load libraries for accessing JES scale factors and uncertainties
        # from txt files
        for library in [
                "libCondFormatsJetMETObjects", "libPhysicsToolsNanoAODTools"
        ]:
            if library not in ROOT.gSystem.GetLibraries():
                print("Load Library '%s'" % library.replace("lib", ""))
                ROOT.gSystem.Load(library)

    def getJERsplitID(self, pt, eta):
        if not self.splitJER:
            return ""
        if abs(eta) < 1.93:
            return 0
        elif abs(eta) < 2.5:
            return 1
        elif abs(eta) < 3:
            if pt < 50:
                return 2
            else:
                return 3
        else:
            if pt < 50:
                return 4
            else:
                return 5

    def beginJob(self):

        print("Loading jet energy scale (JES) uncertainties from file '%s'" %
              os.path.join(self.jesInputFilePath,
                           self.jesUncertaintyInputFileName))
        # self.jesUncertainty = ROOT.JetCorrectionUncertainty(os.path.join(self.jesInputFilePath, self.jesUncertaintyInputFileName))

        self.jesUncertainty = {}
        # implementation didn't seem to work for factorized JEC,try again
        # another way
        for jesUncertainty in self.jesUncertainties:
            jesUncertainty_label = jesUncertainty
            if jesUncertainty == 'Total' \
                and (len(self.jesUncertainties) == 1
                     or len(self.jesUncertainties) == 2 and 'HEMIssue'
                     in self.jesUncertainties):
                jesUncertainty_label = ''
            #print('jesUncertainty: ', jesUncertainty,', jesUncertainty_label: ',jesUncertainty_label)
            if jesUncertainty != "HEMIssue":
                pars = ROOT.JetCorrectorParameters(
                    os.path.join(self.jesInputFilePath,
                                 self.jesUncertaintyInputFileName),
                    jesUncertainty_label)
                #print('pars: ', pars)
                self.jesUncertainty[
                    jesUncertainty] = ROOT.JetCorrectionUncertainty(pars)
                #print('self.jesUncertainty[',jesUncertainty,']: ', self.jesUncertainty[jesUncertainty])

        if not self.isData:
            self.jetSmearer.beginJob()

    def endJob(self):
        if not self.isData:
            self.jetSmearer.endJob()
        shutil.rmtree(self.jesInputFilePath)

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch("%s_pt_raw" % self.jetBranchName,
                        "F",
                        lenVar=self.lenVar)
        self.out.branch("%s_pt_nom" % self.jetBranchName,
                        "F",
                        lenVar=self.lenVar)
        self.out.branch("%s_mass_raw" % self.jetBranchName,
                        "F",
                        lenVar=self.lenVar)
        self.out.branch("%s_mass_nom" % self.jetBranchName,
                        "F",
                        lenVar=self.lenVar)
        self.out.branch("%s_corr_JEC" % self.jetBranchName,
                        "F",
                        lenVar=self.lenVar)
        self.out.branch("%s_corr_JER" % self.jetBranchName,
                        "F",
                        lenVar=self.lenVar)
        if self.storeMassJMS:
            self.out.branch("%s_corr_JMS" % self.jetBranchName,
                            "F",
                            lenVar=self.lenVar)
        if self.storeMassJMR:
            self.out.branch("%s_corr_JMR" % self.jetBranchName,
                            "F",
                            lenVar=self.lenVar)

        if self.doGroomed:
            self.out.branch("%s_msoftdrop_raw" % self.jetBranchName,
                            "F",
                            lenVar=self.lenVar)
            self.out.branch("%s_msoftdrop_nom" % self.jetBranchName,
                            "F",
                            lenVar=self.lenVar)
            if self.applyMsdJMR:
                self.out.branch("%s_msoftdrop_corr_JMR" % self.jetBranchName,
                                "F",
                                lenVar=self.lenVar)
            #if self.applyMsdJMS:
            self.out.branch("%s_msoftdrop_corr_JMS" % self.jetBranchName,
                            "F",
                            lenVar=self.lenVar)
            self.out.branch("%s_msoftdrop_corr_JMSUp" % self.jetBranchName,
                            "F",
                            lenVar=self.lenVar)
            self.out.branch("%s_msoftdrop_corr_JMSDown" % self.jetBranchName,
                            "F",
                            lenVar=self.lenVar)
            self.out.branch("%s_msoftdrop_corr_PUPPI" % self.jetBranchName,
                            "F",
                            lenVar=self.lenVar)

        if not self.isData:
            if self.applyWJMS:
                self.out.branch("%s_msoftdrop_tau21DDT_nom" % self.jetBranchName,
                                "F",
                                lenVar=self.lenVar)
            for shift in ["Up", "Down"]:
                for jerID in self.splitJERIDs:
                    self.out.branch("%s_pt_jer%s%s" %
                                    (self.jetBranchName, jerID, shift),
                                    "F",
                                    lenVar=self.lenVar)
                    self.out.branch("%s_mass_jer%s%s" %
                                    (self.jetBranchName, jerID, shift),
                                    "F",
                                    lenVar=self.lenVar)
                if self.storeMassJMR:
                    self.out.branch("%s_mass_jmr%s" % (self.jetBranchName, shift),
                                    "F",
                                    lenVar=self.lenVar)
                if self.storeMassJMS:
                    self.out.branch("%s_mass_jms%s" % (self.jetBranchName, shift),
                                    "F",
                                    lenVar=self.lenVar)

                if self.doGroomed:
                    for jerID in self.splitJERIDs:
                        self.out.branch("%s_msoftdrop_jer%s%s" %
                                        (self.jetBranchName, jerID, shift),
                                        "F",
                                        lenVar=self.lenVar)
                        if self.applyWJMS:
                            self.out.branch("%s_msoftdrop_tau21DDT_jer%s%s" %
                                            (self.jetBranchName, jerID, shift),
                                            "F",
                                            lenVar=self.lenVar)
                    if self.applyMsdJMR:
                        self.out.branch("%s_msoftdrop_jmr%s" %
                                        (self.jetBranchName, shift),
                                        "F",
                                        lenVar=self.lenVar)
                    if self.applyMsdJMS:
                        self.out.branch("%s_msoftdrop_jms%s" %
                                        (self.jetBranchName, shift),
                                        "F",
                                        lenVar=self.lenVar)
                    if self.applyWJMS:
                        self.out.branch("%s_msoftdrop_tau21DDT_jmr%s" %
                                        (self.jetBranchName, shift),
                                        "F",
                                        lenVar=self.lenVar)
                        self.out.branch("%s_msoftdrop_tau21DDT_jms%s" %
                                        (self.jetBranchName, shift),
                                        "F",
                                        lenVar=self.lenVar)

                for jesUncertainty in self.jesUncertainties:
                    self.out.branch(
                        "%s_pt_jes%s%s" %
                        (self.jetBranchName, jesUncertainty, shift),
                        "F",
                        lenVar=self.lenVar)
                    self.out.branch(
                        "%s_mass_jes%s%s" %
                        (self.jetBranchName, jesUncertainty, shift),
                        "F",
                        lenVar=self.lenVar)
                    if self.doGroomed:
                        self.out.branch(
                            "%s_msoftdrop_jes%s%s" %
                            (self.jetBranchName, jesUncertainty, shift),
                            "F",
                            lenVar=self.lenVar)

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        jets = Collection(event, self.jetBranchName)
        if not self.isData:
            genJets = Collection(event, self.genJetBranchName)

        if self.doGroomed:
            subJets = Collection(event, self.subJetBranchName)
            if not self.isData:
                genSubJets = Collection(event, self.genSubJetBranchName)
                genSubJetMatcher = matchObjectCollectionMultiple(genJets,
                                                                 genSubJets,
                                                                 dRmax=0.8)

        if not self.isData:
            self.jetSmearer.setSeed(event)

        jets_pt_raw = []
        jets_pt_nom = []
        jets_mass_raw = []
        jets_mass_nom = []

        jets_corr_JEC = []
        jets_corr_JER = []
        jets_corr_JMS = []
        jets_corr_JMR = []

        jets_pt_jerUp = {}
        jets_pt_jerDown = {}
        jets_pt_jesUp = {}
        jets_pt_jesDown = {}

        jets_mass_jerUp = {}
        jets_mass_jerDown = {}
        jets_mass_jmrUp = []
        jets_mass_jmrDown = []
        jets_mass_jesUp = {}
        jets_mass_jesDown = {}
        jets_mass_jmsUp = []
        jets_mass_jmsDown = []

        for jerID in self.splitJERIDs:
            jets_pt_jerUp[jerID] = []
            jets_pt_jerDown[jerID] = []
            jets_mass_jerUp[jerID] = []
            jets_mass_jerDown[jerID] = []

        for jesUncertainty in self.jesUncertainties:
            jets_pt_jesUp[jesUncertainty] = []
            jets_pt_jesDown[jesUncertainty] = []
            jets_mass_jesUp[jesUncertainty] = []
            jets_mass_jesDown[jesUncertainty] = []

        if self.doGroomed:
            jets_msdcorr_raw = []
            jets_msdcorr_nom = []
            jets_msdcorr_corr_JMR = []
            jets_msdcorr_corr_JMS = []
            jets_msdcorr_corr_JMSUp = []
            jets_msdcorr_corr_JMSDown = []
            jets_msdcorr_corr_PUPPI = []
            jets_msdcorr_jerUp = {}
            jets_msdcorr_jerDown = {}
            jets_msdcorr_jmrUp = []
            jets_msdcorr_jmrDown = []
            jets_msdcorr_jesUp = {}
            jets_msdcorr_jesDown = {}
            jets_msdcorr_jmsUp = []
            jets_msdcorr_jmsDown = []
            jets_msdcorr_tau21DDT_nom = []
            jets_msdcorr_tau21DDT_jerUp = {}
            jets_msdcorr_tau21DDT_jerDown = {}
            jets_msdcorr_tau21DDT_jmrUp = []
            jets_msdcorr_tau21DDT_jmrDown = []
            jets_msdcorr_tau21DDT_jmsUp = []
            jets_msdcorr_tau21DDT_jmsDown = []
            for jerID in self.splitJERIDs:
                jets_msdcorr_jerUp[jerID] = []
                jets_msdcorr_jerDown[jerID] = []
                jets_msdcorr_tau21DDT_jerUp[jerID] = []
                jets_msdcorr_tau21DDT_jerDown[jerID] = []
            for jesUncertainty in self.jesUncertainties:
                jets_msdcorr_jesUp[jesUncertainty] = []
                jets_msdcorr_jesDown[jesUncertainty] = []

        rho = getattr(event, self.rhoBranchName)

        # match reconstructed jets to generator level ones
        # (needed to evaluate JER scale factors and uncertainties)
        if not self.isData:
            pairs = matchObjectCollection(jets, genJets)

        for jet in jets:
            # jet pt and mass corrections
            jet_pt = jet.pt
            jet_mass = jet.mass

            if hasattr(jet, "rawFactor"):
                jet_rawpt = jet_pt * (1 - jet.rawFactor)
                jet_rawmass = jet_mass * (1 - jet.rawFactor)
            else:
                jet_rawpt = -1.0 * jet_pt  # If factor not present factor will be saved as -1
                jet_rawmass = -1.0 * jet_mass  # If factor not present factor will be saved as -1

            (jet_pt, jet_mass) = self.jetReCalibrator.correct(jet, rho)
            jet.pt = jet_pt
            jet.mass = jet_mass
            jets_pt_raw.append(jet_rawpt)
            jets_mass_raw.append(jet_rawmass)
            jets_corr_JEC.append(jet_pt / jet_rawpt)

            if not self.isData:
                genJet = pairs[jet]

            # evaluate JER scale factors and uncertainties
            # (cf. https://twiki.cern.ch/twiki/bin/view/CMS/JetResolution and https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookJetEnergyResolution )
            if not self.isData:
                (jet_pt_jerNomVal, jet_pt_jerUpVal,
                 jet_pt_jerDownVal) = self.jetSmearer.getSmearValsPt(
                     jet, genJet, rho)
            else:
                # set values to 1 for data so that jet_pt_nom is not smeared
                (jet_pt_jerNomVal, jet_pt_jerUpVal, jet_pt_jerDownVal) = (1, 1,
                                                                          1)
            jets_corr_JER.append(jet_pt_jerNomVal)

            jet_pt_nom = jet_pt_jerNomVal * jet_pt if self.applySmearing else jet_pt
            if jet_pt_nom < 0.0:
                jet_pt_nom *= -1.0
            jets_pt_nom.append(jet_pt_nom)

            # Evaluate JMS and JMR scale factors and uncertainties
            jmsNomVal, jmsDownVal, jmsUpVal = self.jmsVals if not self.isData else (1, 1, 1)              
            if not self.isData:
                (jet_mass_jmrNomVal, jet_mass_jmrUpVal,
                 jet_mass_jmrDownVal) = self.jetSmearer.getSmearValsM(
                     jet, genJet)
            else:
                # set values to 1 for data so that jet_mass_nom is not smeared
                (jet_mass_jmrNomVal, jet_mass_jmrUpVal,
                 jet_mass_jmrDownVal) = (1, 1, 1)
            jets_corr_JMS.append(jmsNomVal)
            jets_corr_JMR.append(jet_mass_jmrNomVal)

            jet_mass_nom = jet_pt_jerNomVal * jet_mass_jmrNomVal * \
                jmsNomVal * jet_mass if self.applySmearing else jet_mass
            if jet_mass_nom < 0.0:
                jet_mass_nom *= -1.0
            jets_mass_nom.append(jet_mass_nom)

            
            if not self.isData:
                jet_pt_jerUp = {
                    jerID: jet_pt_nom
                    for jerID in self.splitJERIDs
                }
                jet_pt_jerDown = {
                    jerID: jet_pt_nom
                    for jerID in self.splitJERIDs
                }
                jet_mass_jerUp = {
                    jerID: jet_mass_nom
                    for jerID in self.splitJERIDs
                }
                jet_mass_jerDown = {
                    jerID: jet_mass_nom
                    for jerID in self.splitJERIDs
                }
                thisJERID = self.getJERsplitID(jet_pt_nom, jet.eta)
                jet_pt_jerUp[thisJERID] = jet_pt_jerUpVal * jet_pt
                jet_pt_jerDown[thisJERID] = jet_pt_jerDownVal * jet_pt
                jet_mass_jerUp[thisJERID] = jet_pt_jerUpVal * \
                    jet_mass_jmrNomVal * jmsNomVal * jet_mass
                jet_mass_jerDown[thisJERID] = jet_pt_jerDownVal * \
                    jet_mass_jmrNomVal * jmsNomVal * jet_mass

                for jerID in self.splitJERIDs:
                    jets_pt_jerUp[jerID].append(jet_pt_jerUp[jerID])
                    jets_pt_jerDown[jerID].append(jet_pt_jerDown[jerID])
                    jets_mass_jerUp[jerID].append(jet_mass_jerUp[jerID])
                    jets_mass_jerDown[jerID].append(jet_mass_jerDown[jerID])

                jets_mass_jmrUp.append(jet_pt_jerNomVal * jet_mass_jmrUpVal *
                                       jmsNomVal * jet_mass)
                jets_mass_jmrDown.append(jet_pt_jerNomVal *
                                         jet_mass_jmrDownVal * jmsNomVal *
                                         jet_mass)
                jets_mass_jmsUp.append(jet_pt_jerNomVal * jet_mass_jmrNomVal *
                                       jmsUpVal * jet_mass)
                jets_mass_jmsDown.append(jet_pt_jerNomVal *
                                         jet_mass_jmrNomVal * jmsDownVal *
                                         jet_mass)


            if self.doGroomed:
                if not self.isData:
                    genGroomedSubJets = genSubJetMatcher[
                        genJet] if genJet is not None else None
                    genGroomedJet = genGroomedSubJets[0].p4(
                    ) + genGroomedSubJets[1].p4(
                    ) if genGroomedSubJets is not None and len(
                        genGroomedSubJets) >= 2 else None
                else:
                    genGroomedSubJets = None
                    genGroomedJet = None
                groomedP4 = groomedRawP4 = None
                if jet.subJetIdx1 >= 0 and jet.subJetIdx2 >= 0:
                    ## Take JEC corrected subjets
                    #groomedP4 = subJets[jet.subJetIdx1].p4() + subJets[
                    #    jet.subJetIdx2].p4()  # check subjet jecs

                    ## Redo subjet JEC with AK8 jet JES
                    subjets_raw_LV = []
                    subjets_LV     = []
                    for subjet_ in [subJets[jet.subJetIdx1], subJets[jet.subJetIdx2]]:
                        subjet_rawpt   = subjet_.pt   * (1 - subjet_.rawFactor)
                        subjet_rawmass = subjet_.mass * (1 - subjet_.rawFactor)
                        subjet_pt      = subjet_rawpt   * jets_corr_JEC[-1]
                        subjet_mass    = subjet_rawmass * jets_corr_JEC[-1]

                        subjet_raw_LV  = ROOT.TLorentzVector()
                        subjet_LV      = ROOT.TLorentzVector()
                        subjet_raw_LV.SetPtEtaPhiM(subjet_rawpt, subjet_.eta, subjet_.phi, subjet_rawmass)
                        subjet_LV    .SetPtEtaPhiM(subjet_pt,    subjet_.eta, subjet_.phi, subjet_mass   )
                        subjets_raw_LV.append(subjet_raw_LV)
                        subjets_LV    .append(subjet_LV    ) 
                        
                    groomedRawP4 = subjets_raw_LV[0] + subjets_raw_LV[1]
                    groomedP4    = subjets_LV[0] + subjets_LV[1]
                else:
                    groomedP4 = None

                jet_msdcorr_raw = groomedRawP4.M() if groomedRawP4 is not None else 0.0
                if jet_msdcorr_raw < 0.0:
                    jet_msdcorr_raw *= -1.0
                
                # raw value always stored withoud mass correction
                jets_msdcorr_raw.append(jet_msdcorr_raw)
                # LC: Apply PUPPI SD mass correction https://github.com/cms-jet/PuppiSoftdropMassCorr/
                puppisd_genCorr = self.puppisd_corrGEN.Eval(jet.pt)
                if abs(jet.eta) <= 1.3:
                    puppisd_recoCorr = self.puppisd_corrRECO_cen.Eval(jet.pt)
                else:
                    puppisd_recoCorr = self.puppisd_corrRECO_for.Eval(jet.pt)

                puppisd_total = puppisd_genCorr * puppisd_recoCorr
                jets_msdcorr_corr_PUPPI.append(puppisd_total)
                puppisd_total_toUse = puppisd_total if self.applyWJMS else 1.0
                if groomedP4 is not None:
                    groomedP4.SetPtEtaPhiM(groomedP4.Perp(), groomedP4.Eta(),
                                           groomedP4.Phi(),
                                           groomedP4.M() * puppisd_total_toUse)

                # now apply the mass correction to the raw or jec-corrected value
                jet_msdcorr_jec = groomedP4.M() if groomedP4 is not None else 0.0
                if jet_msdcorr_jec < 0.0:
                    jet_msdcorr_jec *= -1.0

                # Evaluate JMS and JMR scale factors and uncertainties
                jmsMsdNomVal, jmsMsdDownVal, jmsMsdUpVal = self.jmsMsdVals if not self.isData else (1, 1, 1)
                if not self.isData and self.jmsMsdVals_funcOfPtEta: 
                    # load (pT, eta) dependent JMS for Ultra-legacy Run2 data: https://twiki.cern.ch/twiki/bin/view/CMSPublic/PhysicsResultsDP23044
                    jmsMsdNomVal  = self.jmsMsdVals_funcOfPtEta.evaluate(jet.pt, ''    ) # use jet_pt_nom or jet_pt?
                    jmsMsdDownVal = self.jmsMsdVals_funcOfPtEta.evaluate(jet.pt, 'down') 
                    jmsMsdUpVal   = self.jmsMsdVals_funcOfPtEta.evaluate(jet.pt, 'up'  ) 
                    #print("jet_pt: %f %f, jet_pt_nom: %f, jmsMsdNomVal: %f, jmsMsdDownVal: %f, jmsMsdUpVal: %f," % 
                    #      (jet_pt, jet.pt, jet_pt_nom, jmsMsdNomVal, jmsMsdDownVal, jmsMsdUpVal))

                if not self.isData:
                    (jet_msdcorr_jmrNomVal, jet_msdcorr_jmrUpVal,
                     jet_msdcorr_jmrDownVal) = \
                        (self.jetSmearer.getSmearValsM(groomedP4,
                         genGroomedJet) if groomedP4 is not None
                         and genGroomedJet is not None else (0., 0., 0.)) # else (0., 0., 0.)) or (1, 1, 1) ??
                else:
                    (jet_msdcorr_jmrNomVal, jet_msdcorr_jmrUpVal,
                     jet_msdcorr_jmrDownVal) = (1, 1, 1)

                jets_msdcorr_corr_JMS.append(jmsMsdNomVal)
                jets_msdcorr_corr_JMSUp.append(jmsMsdUpVal)
                jets_msdcorr_corr_JMSDown.append(jmsMsdDownVal)
                jets_msdcorr_corr_JMR.append(jet_msdcorr_jmrNomVal)

                if not self.isData: 
                    # skip msd JMS, JMR if you don't want to apply
                    if not self.applyMsdJMS:
                        (jmsMsdNomVal, jmsMsdDownVal, jmsMsdUpVal) = (1, 1, 1)
                    if not self.applyMsdJMR:
                        (jet_msdcorr_jmrNomVal, jet_msdcorr_jmrUpVal,
                        jet_msdcorr_jmrDownVal) = (1, 1, 1)

                jet_msdcorr_nom = jet_msdcorr_jec * jet_pt_jerNomVal * \
                    jmsMsdNomVal * jet_msdcorr_jmrNomVal 
                # store the nominal mass value
                jets_msdcorr_nom.append(jet_msdcorr_nom)                

                if not self.isData:
                    jet_msdcorr_jerUp = {
                        jerID: jet_msdcorr_nom
                        for jerID in self.splitJERIDs
                    }
                    jet_msdcorr_jerDown = {
                        jerID: jet_msdcorr_nom
                        for jerID in self.splitJERIDs
                    }
                    thisJERID = self.getJERsplitID(jet_pt_nom, jet.eta)
                    jet_msdcorr_jerUp[thisJERID] = jet_pt_jerUpVal * \
                        jet_msdcorr_jmrNomVal * jmsMsdNomVal * jet_msdcorr_jec
                    jet_msdcorr_jerDown[thisJERID] = jet_pt_jerDownVal * \
                        jet_msdcorr_jmrNomVal * jmsMsdNomVal * jet_msdcorr_jec
                    for jerID in self.splitJERIDs:
                        jets_msdcorr_jerUp[jerID].append(
                            jet_msdcorr_jerUp[jerID])
                        jets_msdcorr_jerDown[jerID].append(
                            jet_msdcorr_jerDown[jerID])

                    jets_msdcorr_jmrUp.append(
                        jet_pt_jerNomVal * jet_msdcorr_jmrUpVal * jmsMsdNomVal *
                        jet_msdcorr_jec)
                    jets_msdcorr_jmrDown.append(
                        jet_pt_jerNomVal * jet_msdcorr_jmrDownVal * jmsMsdNomVal *
                        jet_msdcorr_jec)
                    jets_msdcorr_jmsUp.append(
                        jet_pt_jerNomVal * jet_msdcorr_jmrNomVal * jmsMsdUpVal *
                        jet_msdcorr_jec)
                    jets_msdcorr_jmsDown.append(
                        jet_pt_jerNomVal * jet_msdcorr_jmrNomVal * jmsMsdDownVal *
                        jet_msdcorr_jec)

                    if self.applyWJMS:
                        # Also evaluated JMS&JMR SD corr in tau21DDT region: https://twiki.cern.ch/twiki/bin/viewauth/CMS/JetWtagging#tau21DDT_0_43
                        # UL recommendations not yet available, use same factors in both cases
                        if self.era in ["2016"]:
                            jmstau21DDTNomVal = 1.014
                            jmstau21DDTDownVal = 1.007
                            jmstau21DDTUpVal = 1.021
                            self.jetSmearer.jmr_vals = [1.086, 1.176, 0.996]
                        elif self.era in ["2017"]:
                            jmstau21DDTNomVal = 0.983
                            jmstau21DDTDownVal = 0.976
                            jmstau21DDTUpVal = 0.99
                            self.jetSmearer.jmr_vals = [1.080, 1.161, 0.999]
                        elif self.era in ["2018"]:
                            jmstau21DDTNomVal = 1.000  # tau21DDT < 0.43 WP
                            jmstau21DDTDownVal = 0.990
                            jmstau21DDTUpVal = 1.010
                            self.jetSmearer.jmr_vals = [1.124, 1.208, 1.040]
                        elif self.era in ["UL2016", "UL2016_preVFP"]:
                            jmstau21DDTNomVal = 1.014
                            jmstau21DDTDownVal = 1.007
                            jmstau21DDTUpVal = 1.021
                            self.jetSmearer.jmr_vals = [1.086, 1.176, 0.996]
                        elif self.era in ["UL2017"]:
                            jmstau21DDTNomVal = 0.983
                            jmstau21DDTDownVal = 0.976
                            jmstau21DDTUpVal = 0.99
                            self.jetSmearer.jmr_vals = [1.080, 1.161, 0.999]
                        elif self.era in ["UL2018"]:
                            jmstau21DDTNomVal = 1.000  # tau21DDT < 0.43 WP
                            jmstau21DDTDownVal = 0.990
                            jmstau21DDTUpVal = 1.010
                            self.jetSmearer.jmr_vals = [1.124, 1.208, 1.040]

                        (jet_msdcorr_tau21DDT_jmrNomVal,
                        jet_msdcorr_tau21DDT_jmrUpVal,
                        jet_msdcorr_tau21DDT_jmrDownVal
                        ) = self.jetSmearer.getSmearValsM(
                            groomedP4, genGroomedJet
                        ) if groomedP4 is not None and genGroomedJet is not None else (0., 0., 0.)

                        jet_msdcorr_tau21DDT_nom = jet_pt_jerNomVal * \
                            jet_msdcorr_tau21DDT_jmrNomVal * jmstau21DDTNomVal * jet_msdcorr_jec
                        jets_msdcorr_tau21DDT_nom.append(jet_msdcorr_tau21DDT_nom)

                        jet_msdcorr_tau21DDT_jerUp = {
                            jerID: jet_msdcorr_tau21DDT_nom
                            for jerID in self.splitJERIDs
                        }
                        jet_msdcorr_tau21DDT_jerDown = {
                            jerID: jet_msdcorr_tau21DDT_nom
                            for jerID in self.splitJERIDs
                        }
                        jet_msdcorr_tau21DDT_jerUp[thisJERID] = jet_pt_jerUpVal * \
                            jet_msdcorr_tau21DDT_jmrNomVal * jmstau21DDTNomVal * jet_msdcorr_jec
                        jet_msdcorr_tau21DDT_jerDown[thisJERID] = jet_pt_jerDownVal * \
                            jet_msdcorr_tau21DDT_jmrNomVal * jmstau21DDTNomVal * jet_msdcorr_jec
                        for jerID in self.splitJERIDs:
                            jets_msdcorr_tau21DDT_jerUp[jerID].append(
                                jet_msdcorr_tau21DDT_jerUp[jerID])
                            jets_msdcorr_tau21DDT_jerDown[jerID].append(
                                jet_msdcorr_tau21DDT_jerDown[jerID])

                        jets_msdcorr_tau21DDT_jmrUp.append(
                            jet_pt_jerNomVal * jet_msdcorr_tau21DDT_jmrUpVal *
                            jmstau21DDTNomVal * jet_msdcorr_jec)
                        jets_msdcorr_tau21DDT_jmrDown.append(
                            jet_pt_jerNomVal * jet_msdcorr_tau21DDT_jmrDownVal *
                            jmstau21DDTNomVal * jet_msdcorr_jec)
                        jets_msdcorr_tau21DDT_jmsUp.append(
                            jet_pt_jerNomVal * jet_msdcorr_tau21DDT_jmrNomVal *
                            jmstau21DDTUpVal * jet_msdcorr_jec)
                        jets_msdcorr_tau21DDT_jmsDown.append(
                            jet_pt_jerNomVal * jet_msdcorr_tau21DDT_jmrNomVal *
                            jmstau21DDTDownVal * jet_msdcorr_jec)

                        # Restore original jmr_vals in jetSmearer
                        self.jetSmearer.jmr_vals = self.jmrVals

            if not self.isData:
                # evaluate JES uncertainties
                jet_pt_jesUp = {}
                jet_pt_jesDown = {}
                jet_mass_jesUp = {}
                jet_mass_jesDown = {}
                jet_msdcorr_jesUp = {}
                jet_msdcorr_jesDown = {}

                for jesUncertainty in self.jesUncertainties:
                    # (cf. https://twiki.cern.ch/twiki/bin/view/CMSPublic/WorkBookJetEnergyCorrections#JetCorUncertainties)
                    # cf. https://hypernews.cern.ch/HyperNews/CMS/get/JetMET/2000.html
                    if jesUncertainty == "HEMIssue":
                        delta = 1.
                        if jet_pt_nom > 15 and jet.jetId & 2 and jet.phi > -1.57 and jet.phi < -0.87:
                            if jet.eta > -2.5 and jet.eta < -1.3:
                                delta = 0.8
                            elif jet.eta <= -2.5 and jet.eta > -3:
                                delta = 0.65
                        jet_pt_jesUp[jesUncertainty] = jet_pt_nom
                        jet_pt_jesDown[jesUncertainty] = delta * jet_pt_nom
                        jet_mass_jesUp[jesUncertainty] = jet_mass_nom
                        jet_mass_jesDown[jesUncertainty] = delta * jet_mass_nom
                        if self.doGroomed:
                            jet_msdcorr_jesUp[jesUncertainty] = jet_msdcorr_nom
                            jet_msdcorr_jesDown[jesUncertainty] = delta * \
                                jet_msdcorr_nom
                    else:
                        self.jesUncertainty[jesUncertainty].setJetPt(
                            jet_pt_nom)
                        self.jesUncertainty[jesUncertainty].setJetEta(jet.eta)
                        delta = self.jesUncertainty[
                            jesUncertainty].getUncertainty(True)
                        jet_pt_jesUp[jesUncertainty] = jet_pt_nom * \
                            (1. + delta)
                        jet_pt_jesDown[jesUncertainty] = jet_pt_nom * \
                            (1. - delta)
                        jet_mass_jesUp[jesUncertainty] = jet_mass_nom * \
                            (1. + delta)
                        jet_mass_jesDown[jesUncertainty] = jet_mass_nom * \
                            (1. - delta)
                        if self.doGroomed:
                            jet_msdcorr_jesUp[jesUncertainty] = jet_msdcorr_nom * \
                                (1. + delta)
                            jet_msdcorr_jesDown[
                                jesUncertainty] = jet_msdcorr_nom * (1. - delta)

                    jets_pt_jesUp[jesUncertainty].append(
                        jet_pt_jesUp[jesUncertainty])
                    jets_pt_jesDown[jesUncertainty].append(
                        jet_pt_jesDown[jesUncertainty])
                    jets_mass_jesUp[jesUncertainty].append(
                        jet_mass_jesUp[jesUncertainty])
                    jets_mass_jesDown[jesUncertainty].append(
                        jet_mass_jesDown[jesUncertainty])
                    if self.doGroomed:
                        jets_msdcorr_jesUp[jesUncertainty].append(
                            jet_msdcorr_jesUp[jesUncertainty])
                        jets_msdcorr_jesDown[jesUncertainty].append(
                            jet_msdcorr_jesDown[jesUncertainty])

        self.out.fillBranch("%s_pt_raw" % self.jetBranchName, rnd(jets_pt_raw))
        self.out.fillBranch("%s_pt_nom" % self.jetBranchName, rnd(jets_pt_nom))
        self.out.fillBranch("%s_corr_JEC" % self.jetBranchName, jets_corr_JEC)
        self.out.fillBranch("%s_mass_raw" % self.jetBranchName, rnd(jets_mass_raw))
        self.out.fillBranch("%s_mass_nom" % self.jetBranchName, rnd(jets_mass_nom))

        if not self.isData:
            self.out.fillBranch("%s_corr_JER" % self.jetBranchName,
                                jets_corr_JER)
            if self.storeMassJMS:
                self.out.fillBranch("%s_corr_JMS" % self.jetBranchName,
                                    jets_corr_JMS)
            if self.storeMassJMR:
                self.out.fillBranch("%s_corr_JMR" % self.jetBranchName,
                                    jets_corr_JMR)
            for jerID in self.splitJERIDs:
                self.out.fillBranch(
                    "%s_pt_jer%sUp" % (self.jetBranchName, jerID),
                    rnd(jets_pt_jerUp[jerID]))
                self.out.fillBranch(
                    "%s_pt_jer%sDown" % (self.jetBranchName, jerID),
                    rnd(jets_pt_jerDown[jerID]))
                self.out.fillBranch(
                    "%s_mass_jer%sUp" % (self.jetBranchName, jerID),
                    rnd(jets_mass_jerUp[jerID]))
                self.out.fillBranch(
                    "%s_mass_jer%sDown" % (self.jetBranchName, jerID),
                    rnd(jets_mass_jerDown[jerID]))
            if self.storeMassJMR:
                self.out.fillBranch("%s_mass_jmrUp" % self.jetBranchName,
                                    rnd(jets_mass_jmrUp))
                self.out.fillBranch("%s_mass_jmrDown" % self.jetBranchName,
                                    rnd(jets_mass_jmrDown))
            if self.storeMassJMS:
                self.out.fillBranch("%s_mass_jmsUp" % self.jetBranchName,
                                    rnd(jets_mass_jmsUp))
                self.out.fillBranch("%s_mass_jmsDown" % self.jetBranchName,
                                    rnd(jets_mass_jmsDown))

        if self.doGroomed:
            self.out.fillBranch("%s_msoftdrop_raw" % self.jetBranchName,
                                rnd(jets_msdcorr_raw))
            self.out.fillBranch("%s_msoftdrop_nom" % self.jetBranchName,
                                rnd(jets_msdcorr_nom))
            #if self.applyMsdJMS:
            self.out.fillBranch("%s_msoftdrop_corr_JMS" % self.jetBranchName,
                                rnd(jets_msdcorr_corr_JMS))
            self.out.fillBranch("%s_msoftdrop_corr_JMSUp" % self.jetBranchName,
                                rnd(jets_msdcorr_corr_JMSUp))
            self.out.fillBranch("%s_msoftdrop_corr_JMSDown" % self.jetBranchName,
                                rnd(jets_msdcorr_corr_JMSDown))
            if self.applyMsdJMR:
                self.out.fillBranch("%s_msoftdrop_corr_JMR" % self.jetBranchName,
                                    rnd(jets_msdcorr_corr_JMR))
            self.out.fillBranch("%s_msoftdrop_corr_PUPPI" % self.jetBranchName,
                                rnd(jets_msdcorr_corr_PUPPI))
            if not self.isData:
                if self.applyWJMS:
                    self.out.fillBranch(
                        "%s_msoftdrop_tau21DDT_nom" % self.jetBranchName,
                        rnd(jets_msdcorr_tau21DDT_nom))
                for jerID in self.splitJERIDs:
                    self.out.fillBranch(
                        "%s_msoftdrop_jer%sUp" % (self.jetBranchName, jerID),
                        rnd(jets_msdcorr_jerUp[jerID]))
                    self.out.fillBranch(
                        "%s_msoftdrop_jer%sDown" % (self.jetBranchName, jerID),
                        rnd(jets_msdcorr_jerDown[jerID]))
                    if self.applyWJMS:
                        self.out.fillBranch(
                            "%s_msoftdrop_tau21DDT_jer%sUp" %
                            (self.jetBranchName, jerID),
                            rnd(jets_msdcorr_tau21DDT_jerUp[jerID]))
                        self.out.fillBranch(
                            "%s_msoftdrop_tau21DDT_jer%sDown" %
                            (self.jetBranchName, jerID),
                            rnd(jets_msdcorr_tau21DDT_jerDown[jerID]))
                if self.applyMsdJMR:
                    self.out.fillBranch("%s_msoftdrop_jmrUp" % self.jetBranchName,
                                        rnd(jets_msdcorr_jmrUp))
                    self.out.fillBranch(
                        "%s_msoftdrop_jmrDown" % self.jetBranchName,
                        rnd(jets_msdcorr_jmrDown))
                if self.applyMsdJMS:
                    self.out.fillBranch("%s_msoftdrop_jmsUp" % self.jetBranchName,
                                        rnd(jets_msdcorr_jmsUp))
                    self.out.fillBranch(
                        "%s_msoftdrop_jmsDown" % self.jetBranchName,
                        rnd(jets_msdcorr_jmsDown))
                if self.applyWJMS:
                    self.out.fillBranch(
                        "%s_msoftdrop_tau21DDT_jmrUp" % self.jetBranchName,
                        rnd(jets_msdcorr_tau21DDT_jmrUp))
                    self.out.fillBranch(
                        "%s_msoftdrop_tau21DDT_jmrDown" % self.jetBranchName,
                        rnd(jets_msdcorr_tau21DDT_jmrDown))
                    self.out.fillBranch(
                        "%s_msoftdrop_tau21DDT_jmsUp" % self.jetBranchName,
                        rnd(jets_msdcorr_tau21DDT_jmsUp))
                    self.out.fillBranch(
                        "%s_msoftdrop_tau21DDT_jmsDown" % self.jetBranchName,
                        rnd(jets_msdcorr_tau21DDT_jmsDown))

        if not self.isData:
            for jesUncertainty in self.jesUncertainties:
                self.out.fillBranch(
                    "%s_pt_jes%sUp" % (self.jetBranchName, jesUncertainty),
                    rnd(jets_pt_jesUp[jesUncertainty]))
                self.out.fillBranch(
                    "%s_pt_jes%sDown" % (self.jetBranchName, jesUncertainty),
                    rnd(jets_pt_jesDown[jesUncertainty]))
                self.out.fillBranch(
                    "%s_mass_jes%sUp" % (self.jetBranchName, jesUncertainty),
                    rnd(jets_mass_jesUp[jesUncertainty]))
                self.out.fillBranch(
                    "%s_mass_jes%sDown" % (self.jetBranchName, jesUncertainty),
                    rnd(jets_mass_jesDown[jesUncertainty]))

                if self.doGroomed:
                    self.out.fillBranch(
                        "%s_msoftdrop_jes%sUp" %
                        (self.jetBranchName, jesUncertainty),
                        rnd(jets_msdcorr_jesUp[jesUncertainty]))
                    self.out.fillBranch(
                        "%s_msoftdrop_jes%sDown" %
                        (self.jetBranchName, jesUncertainty),
                        rnd(jets_msdcorr_jesDown[jesUncertainty]))

        return True


# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed
fatJetUncertainties2016 = lambda: fatJetUncertaintiesProducer(
    "2016", "Summer16_07Aug2017_V11_MC", ["Total"])
fatJetUncertainties2016All = lambda: fatJetUncertaintiesProducer(
    "2016", "Summer16_07Aug2017_V11_MC", ["All"])

fatJetUncertainties2017 = lambda: fatJetUncertaintiesProducer(
    "2017", "Fall17_17Nov2017_V32_MC", ["Total"])
fatJetUncertainties2017All = lambda: fatJetUncertaintiesProducer(
    "2017", "Fall17_17Nov2017_V32_MC", ["All"])

fatJetUncertainties2018 = lambda: fatJetUncertaintiesProducer(
    "2018", "Autumn18_V8_MC", ["Total"])
fatJetUncertainties2018All = lambda: fatJetUncertaintiesProducer(
    "2018", "Autumn18_V8_MC", ["All"])

fatJetUncertainties2016AK4Puppi = lambda: fatJetUncertaintiesProducer(
    "2016", "Summer16_07Aug2017_V11_MC", ["Total"], jetType="AK4PFPuppi")
fatJetUncertainties2016AK4PuppiAll = lambda: fatJetUncertaintiesProducer(
    "2016", "Summer16_07Aug2017_V11_MC", ["All"], jetType="AK4PFPuppi")

fatJetUncertainties2017AK4Puppi = lambda: fatJetUncertaintiesProducer(
    "2017", "Fall17_17Nov2017_V32_MC", ["Total"], jetType="AK4PFPuppi")
fatJetUncertainties2017AK4PuppiAll = lambda: fatJetUncertaintiesProducer(
    "2017", "Fall17_17Nov2017_V32_MC", ["All"], jetType="AK4PFPuppi")

fatJetUncertainties2018AK4Puppi = lambda: fatJetUncertaintiesProducer(
    "2018", "Autumn18_V8_MC", ["Total"], jetType="AK4PFPuppi")
fatJetUncertainties2018AK4PuppiAll = lambda: fatJetUncertaintiesProducer(
    "2018", "Autumn18_V8_MC", ["All"], jetType="AK4PFPuppi")

fatJetUncertainties2016AK8Puppi = lambda: fatJetUncertaintiesProducer(
    "2016", "Summer16_07Aug2017_V11_MC", ["Total"], jetType="AK8PFPuppi")
fatJetUncertainties2016AK8PuppiAll = lambda: fatJetUncertaintiesProducer(
    "2016", "Summer16_07Aug2017_V11_MC", ["All"], jetType="AK8PFPuppi")
fatJetUncertainties2016AK8PuppiNoGroom = lambda: fatJetUncertaintiesProducer(
    "2016",
    "Summer16_07Aug2017_V11_MC", ["Total"],
    jetType="AK8PFPuppi",
    noGroom=True)
fatJetUncertainties2016AK8PuppiAllNoGroom = lambda: fatJetUncertaintiesProducer(
    "2016",
    "Summer16_07Aug2017_V11_MC", ["All"],
    jetType="AK8PFPuppi",
    noGroom=True)

fatJetUncertainties2017AK8Puppi = lambda: fatJetUncertaintiesProducer(
    "2017", "Fall17_17Nov2017_V32_MC", ["Total"], jetType="AK8PFPuppi")
fatJetUncertainties2017AK8PuppiAll = lambda: fatJetUncertaintiesProducer(
    "2017", "Fall17_17Nov2017_V32_MC", ["All"], jetType="AK8PFPuppi")

fatJetUncertainties2018AK8Puppi = lambda: fatJetUncertaintiesProducer(
    "2018", "Autumn18_V8_MC", ["Total"], jetType="AK8PFPuppi")
fatJetUncertainties2018AK8PuppiAll = lambda: fatJetUncertaintiesProducer(
    "2018", "Autumn18_V8_MC", ["All"], jetType="AK8PFPuppi")
