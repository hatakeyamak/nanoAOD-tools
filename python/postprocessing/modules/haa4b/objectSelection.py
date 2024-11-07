## H --> aa --> 4b search with "boosted" decays to AK8 jets
## Select object candidates and "clean" between types of objects

from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
import ROOT
import os
import random
ROOT.PyConfig.IgnoreCommandLineOptions = True

class Haa4bObjectSelectionProducer(Module):
    def __init__(self):
        ## Latest object selection information:
        ## https://indico.cern.ch/event/1430644/#2-update-on-higgs-aa-4b-booste
        ## https://indico.cern.ch/event/1450818/#17-andrew-brinkerhoff
        self.Fat_sel_ID = 6
        self.Fat_sel_pt = 170.0
        self.Fat_sel_eta = 2.4
        self.Fat_sel_msoft = 20.0
        self.Fat_candH_Xbb = 0.75
        self.Fat_candX_msoft = 50.0

        self.Mu_sel_pt = 10.0
        self.Mu_sel_eta = 2.4
        self.Mu_sel_iso = 0.10
        self.Mu_sel_dxy = 0.02
        self.Mu_sel_dz = 0.10
        #self.Mu_sel_ID = (mediumPromptId or (pt > 53 and highPtId))
        self.Mu_trig_pt = 26.0

        self.Ele_sel_pt = 10.0
        self.Ele_sel_eta = 2.5
        self.Ele_sel_crack = [1.44, 1.57]
        #self.Ele_sel_ID = (mvaFall17V2Iso_WPL and (mvaFall17V2Iso_WP90 or (pt > 35 and cutBased_HEEP)
        self.Ele_trig_pt = 35.0
        self.Ele_trig_dxy = 0.02
        self.Ele_trig_dz = 0.10
        #self.Ele_trig_ID = (mvaFall17V2Iso_WP90 and (mvaFall17V2Iso_WP80 or cutBased_HEEP))

        self.Jet_presel_pt = 15.0
        self.Jet_presel_ID = 6
        #self.Jet_presel_puId = (pt > 50 or puId >= 4)
        self.Jet_sel_pt = 30.0
        self.bJet_sel_eta = 2.4
        self.bJet_sel_flavB = 0.2783
        self.bJet_candH_dR = 1.4


    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        ## Branches for object selection, per object
        ## Include separate flags for JES/JMS shifts? - AWB 2024.10.15
        self.out.branch("FatJet_Haa4b_sel",       "b", lenVar="nFatJet")
        self.out.branch("FatJet_Haa4b_candH",     "b", lenVar="nFatJet")
        self.out.branch("FatJet_Haa4b_candX",     "b", lenVar="nFatJet")
        self.out.branch("FatJet_Haa4b_ovlp_iMu",  "I", lenVar="nFatJet")
        self.out.branch("FatJet_Haa4b_ovlp_iEle", "I", lenVar="nFatJet")
        self.out.branch("Muon_Haa4b_sel",       "b", lenVar="nMuon")
        self.out.branch("Muon_Haa4b_trig",      "b", lenVar="nMuon")
        self.out.branch("Muon_Haa4b_ovlp_iFat", "I", lenVar="nMuon")
        self.out.branch("Electron_Haa4b_sel",       "b", lenVar="nElectron")
        self.out.branch("Electron_Haa4b_trig",      "b", lenVar="nElectron")
        self.out.branch("Electron_Haa4b_ovlp_iFat", "I", lenVar="nElectron")
        self.out.branch("Jet_Haa4b_presel",    "b", lenVar="nJet")
        self.out.branch("Jet_Haa4b_sel",       "b", lenVar="nJet")
        self.out.branch("Jet_Haa4b_btag",      "b", lenVar="nJet")
        self.out.branch("Jet_Haa4b_candH",     "b", lenVar="nJet")
        self.out.branch("Jet_Haa4b_ovlp_iFat", "I", lenVar="nJet")
        self.out.branch("Jet_Haa4b_ovlp_iMu",  "I", lenVar="nJet")
        self.out.branch("Jet_Haa4b_ovlp_iEle", "I", lenVar="nJet")

        ## Branches for counting selected objects, per event
        self.out.branch("Haa4b_nFatSel",  "I")
        self.out.branch("Haa4b_nFatH",    "I")
        self.out.branch("Haa4b_nFatH3b",  "I")
        self.out.branch("Haa4b_nFatX",    "I")
        self.out.branch("Haa4b_nMuSel",   "I")
        self.out.branch("Haa4b_nMuTrig",  "I")
        self.out.branch("Haa4b_nEleSel",  "I")
        self.out.branch("Haa4b_nEleTrig", "I")
        self.out.branch("Haa4b_nJetSel",  "I")
        self.out.branch("Haa4b_nJetBtag", "I")

        ## Branches for preliminary category designations
        CATS = ['gg0l','VBFjj','Vjj','ttHad','Zvv','Zll','Wlv','ttlv','ttll','3l','other']
        for cat in CATS:
            self.out.branch("Haa4b_cat_%s" % cat, "b")
        
        ## Branches with special or multi-object quantities
        self.out.branch("Haa4b_iFatH",        "I")
        self.out.branch("Haa4b_FatH",         "F")
        self.out.branch("Haa4b_FatX_tagWZ",   "F")  ## Exclude lep-overlap
        self.out.branch("Haa4b_FatX_tagTop",  "F")  ## Exclude lep-overlap
        self.out.branch("Haa4b_dijet_mass",   "F")
        self.out.branch("Haa4b_dijet_pt",     "F")
        self.out.branch("Haa4b_dijet_dEta",   "F")
        self.out.branch("Haa4b_dijet_dPhi",   "F")
        self.out.branch("Haa4b_dilep_mass",   "F")
        self.out.branch("Haa4b_dilep_pt",     "F")
        self.out.branch("Haa4b_dilep_dR",     "F")
        self.out.branch("Haa4b_dilep_dPhi",   "F")
        self.out.branch("Haa4b_dilep_charge", "I")
        self.out.branch("Haa4b_dilep_SFOS",   "b")

        ## Branches for categorization and triggers, per event
        self.out.branch("Haa4b_isHad",      "b")
        self.out.branch("Haa4b_isLep",      "b")
        self.out.branch("Haa4b_isMu",       "b")
        self.out.branch("Haa4b_isEle",      "b")
        self.out.branch("Haa4b_trigFat",    "b")
        self.out.branch("Haa4b_trigBtag",   "b")
        self.out.branch("Haa4b_trigVBF",    "b")
        self.out.branch("Haa4b_trigMET",    "b")
        self.out.branch("Haa4b_trigMu",     "b")
        self.out.branch("Haa4b_trigEle",    "b")
        self.out.branch("Haa4b_passFilters","b")
        

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):

        #######################
        ## Set bits for FatJets
        FatJets = Collection(event, "FatJet")
        Fat_sel_bits    = list(0 for fj in FatJets)
        Fat_candH_bits  = list(0 for fj in FatJets)
        Fat_candX_bits  = list(0 for fj in FatJets)
        Fat_ovlp_iMu  = list(-99 for fj in FatJets)
        Fat_ovlp_iEle = list(-99 for fj in FatJets)

        max_Haa_score = -99.0
        iCandH = -99
        vCandH = ROOT.TLorentzVector()
        iCandsX = []
        vCandsX = []
        iFat = -1
        for fj in FatJets:
            iFat += 1
            ## Common FatJet selection
            if fj.jetId     < self.Fat_sel_ID:    continue
            if fj.pt        < self.Fat_sel_pt:    continue
            if abs(fj.eta)  > self.Fat_sel_eta:   continue
            if fj.msoftdrop < self.Fat_sel_msoft: continue
            Fat_sel_bits[iFat] = 1
            ## Higher soft-drop mass cut for W/Z/top candidates
            if fj.msoftdrop >= self.Fat_candX_msoft:
                Fat_candX_bits[iFat] = 1
                iCandsX.append(iFat)
                vCandX = ROOT.TLorentzVector()
                vCandX.SetPtEtaPhiMass(fj.pt, fj.eta, fj.phi, fj.mass)
                vCandsX.append(vCandX)
            ## Xbb selection for Haa4b candidates
            if fj.particleNetMD_Xbb_vs_QCD < self.Fat_candH_Xbb: continue
            Haa_score = fj.PNet_X4b_v2a_Haa34b_score + fj.PNet_X4b_v2b_Haa34b_score
            if Haa_score > max_Haa_score:
                max_Haa_score = Haa_score
                iCandH = iFat
                vCandH.SetPtEtaPhiMass(fj.pt, fj.eta, fj.phi, fj.mass)
        ## End loop: for fj in FatJets

        ## Set the single Higgs candidate, exclude from W/Z/top candidates ("X")
        if iCandH >= 0:
            Fat_candH_bits[iCandH] = 1
            Fat_candX_bits[iCandH] = 0
            for iX in range(len(iCandsX)):
                if iCandsX[iX] == iCandH:
                    del iCandsX[iX]
                    del vCandsX[iX]

        self.out.fillBranch("FatJet_Haa4b_sel",   Fat_sel_bits)
        self.out.fillBranch("FatJet_Haa4b_candH", Fat_candH_bits)
        self.out.fillBranch("FatJet_Haa4b_candX", Fat_candX_bits)
        self.out.fillBranch("Haa4b_nFatSel", sum(Fat_sel_bits))
        self.out.fillBranch("Haa4b_nFatH",   sum(Fat_candH_bits))
        self.out.fillBranch("Haa4b_nFatX",   sum(Fat_candX_bits))


        #####################
        ## Set bits for Muons
        Muons = Collection(event, "Muon")
        Mu_sel_bits  = list(0 for mu in Muons)
        Mu_trig_bits = list(0 for mu in Muons)
        Mu_ovlp_iFat = list(-99 for mu in Muons)

        iSelMus = []
        vSelMus = []
        iTrigMus = []
        vTrigMus = []
        iMu = -1
        for mu in Muons:
            iMu += 1
            ## Check for overlap with candidate FatJets
            vMu = ROOT.TLorentzVector()
            vMu.SetPtEtaPhiMass(mu.pt, mu.eta, mu.phi, 0.10566)
            if iCandH >= 0 and vMu.DeltaR(vCandH) < 0.8:
                Mu_ovlp_iFat[iMu] = iCandH
                if Fat_ovlp_iMu[iCandH] < 0:
                    Fat_ovlp_iMu[iCandH] = iMu
            for iX in range(len(iCandsX)):
                if vMu.DeltaR(vCandsX[iX]) < 0.8:
                    if Mu_ovlp_iFat[iMu] < 0:
                        Mu_ovlp_iFat[iMu] = iCandsX[iX]
                    if Fat_ovlp_iMu[iCandsX[iX]] < 0:
                        Fat_ovlp_iMu[iCandsX[iX]] = iMu
            ## Common muon selection
            if mu.pt               < self.Mu_sel_pt:  continue
            if abs(mu.eta)         > self.Mu_sel_eta: continue
            if mu.miniPFRelIso_all > self.Mu_sel_iso: continue
            if abs(mu.dxy)         > self.Mu_sel_dxy: continue
            if abs(mu.dz)          > self.Mu_sel_dz:  continue
            if not ( mu.mediumPromptId >= 1 or
                     (mu.pt >= 53 and mu.highPtId >= 1) ): continue
            Mu_sel_bits[iMu] = 1
            iSelMus.append(iMu)
            vSelMus.append(vMu)
            ## Triggerable muon selection
            if mu.pt < self.Mu_trig_pt: continue
            Mu_trig_bits[iMu] = 1
            iTrigMus.append(iMu)
            vTrigMus.append(vMu)
        ## End loop: for mu in Muons

        self.out.fillBranch("Muon_Haa4b_sel",  Mu_sel_bits)
        self.out.fillBranch("Muon_Haa4b_trig", Mu_trig_bits)
        self.out.fillBranch("Muon_Haa4b_ovlp_iFat", Mu_ovlp_iFat)
        self.out.fillBranch("FatJet_Haa4b_ovlp_iMu", Fat_ovlp_iMu)
        self.out.fillBranch("Haa4b_nMuSel",  sum(Mu_sel_bits))
        self.out.fillBranch("Haa4b_nMuTrig", sum(Mu_trig_bits))


        #########################
        ## Set bits for Electrons
        Electrons = Collection(event, "Electron")
        Ele_sel_bits  = list(0 for ele in Electrons)
        Ele_trig_bits = list(0 for ele in Electrons)
        Ele_ovlp_iFat = list(-99 for ele in Electrons)

        iSelEles = []
        vSelEles = []
        iTrigEles = []
        vTrigEles = []
        iEle = -1
        for ele in Electrons:
            iEle += 1
            ## Check for overlap with candidate FatJets
            vEle = ROOT.TLorentzVector()
            vEle.SetPtEtaPhiMass(ele.pt, ele.eta, ele.phi, 0.000511)
            if iCandH >= 0 and vEle.DeltaR(vCandH) < 0.8:
                Ele_ovlp_iFat[iEle] = iCandH
                if Fat_ovlp_iEle[iCandH] < 0:
                    Fat_ovlp_iEle[iCandH] = iEle
            for iX in range(len(iCandsX)):
                if vEle.DeltaR(vCandsX[iX]) < 0.8:
                    if Ele_ovlp_iFat[iEle] < 0:
                        Ele_ovlp_iFat[iEle] = iCandsX[iX]
                    if Fat_ovlp_iEle[iCandsX[iX]] < 0:
                        Fat_ovlp_iEle[iCandsX[iX]] = iEle
            ## Common electron selection
            if ele.pt                 < self.Ele_sel_pt:  continue
            if abs(ele.eta)           > self.Ele_sel_eta: continue
            if (abs(ele.eta)    > self.Ele_sel_crack[0] and
                abs(ele.eta)    < self.Ele_sel_crack[1]): continue
            if ele.mvaFall17V2Iso_WPL < 1:                continue
            if not ( ele.mvaFall17V2Iso_WP90 >= 1 or
                     (ele.pt >= 35 and ele.cutBased_HEEP >= 1) ): continue
            Ele_sel_bits[iEle] = 1
            iSelEles.append(iEle)
            vSelEles.append(vEle)
            ## Triggerable electron selection
            if ele.pt       < self.Ele_trig_pt:  continue
            if abs(ele.dxy) > self.Ele_trig_dxy: continue
            if abs(ele.dz)  > self.Ele_trig_dz:  continue
            if ele.mvaFall17V2Iso_WP90 < 1:      continue
            if not ( ele.mvaFall17V2Iso_WP80 >= 1 or
                     ele.cutBased_HEEP >= 1):    continue
            Ele_trig_bits[iEle] = 1
            iTrigEles.append(iEle)
            vTrigEles.append(vEle)
        ## End loop: for ele in Electrons

        self.out.fillBranch("Electron_Haa4b_sel",  Ele_sel_bits)
        self.out.fillBranch("Electron_Haa4b_trig", Ele_trig_bits)
        self.out.fillBranch("Electron_Haa4b_ovlp_iFat", Ele_ovlp_iFat)
        self.out.fillBranch("FatJet_Haa4b_ovlp_iEle", Fat_ovlp_iEle)
        self.out.fillBranch("Haa4b_nEleSel",  sum(Ele_sel_bits))
        self.out.fillBranch("Haa4b_nEleTrig", sum(Ele_trig_bits))

        ## Events with at least one triggerable lepton belong to lepton categories
        nTrigLeps = len(iTrigMus) + len(iTrigEles)
        nSelLeps  = len(iSelMus)  + len(iSelEles)
        ## Find how many trigger and selected leptons overlap AK8 Higgs candidate
        nTrigLepsOvlpH = 0
        idSelLepsNonOvlpH = []
        vSelLepsNonOvlpH  = []
        for iMu in range(len(Mu_ovlp_iFat)):
            if iCandH >= 0 and Mu_ovlp_iFat[iMu] == iCandH:
                nTrigLepsOvlpH += Mu_trig_bits[iMu]
                if Mu_sel_bits[iMu] == 1:
                    idSelLepsNonOvlpH.append(-13*Muons[iMu].charge)
                    vSelLepsNonOvlpH.append(vSelMus[iSelMus.index(iMu)])
        for iEle in range(len(Ele_ovlp_iFat)):
            if iCandH >= 0 and Ele_ovlp_iFat[iEle] == iCandH:
                nTrigLepsOvlpH += Ele_trig_bits[iEle]
                if Ele_sel_bits[iEle] == 1:
                    idSelLepsNonOvlpH.append(-11*Electrons[iEle].charge)
                    vSelLepsNonOvlpH.append(vSelEles[iSelEles.index(iEle)])
        nSelLepsNonOvlpH = len(vSelLepsNonOvlpH)


        #####################
        ## Set bits for Jets
        Jets = Collection(event, "Jet")
        Jet_presel_bits = list(0 for jet in Jets)
        Jet_sel_bits    = list(0 for jet in Jets)
        Jet_btag_bits   = list(0 for jet in Jets)
        Jet_candH_bits  = list(0 for jet in Jets)
        Jet_ovlp_iFat = list(-99 for jet in Jets)
        Jet_ovlp_iMu  = list(-99 for jet in Jets)
        Jet_ovlp_iEle = list(-99 for jet in Jets)

        vSelJets  = []
        iJetCandH = -99
        vJetCandH = ROOT.TLorentzVector()
        iJet = -1
        for jet in Jets:
            iJet += 1
            ## Check for overlap with candidate FatJets and selected leptons
            vJet = ROOT.TLorentzVector()
            vJet.SetPtEtaPhiMass(jet.pt, jet.eta, jet.phi, jet.mass)
            if iCandH >= 0 and vJet.DeltaR(vCandH) < 0.8:
                Jet_ovlp_iFat[iJet] = iCandH
            else:
                for iX in range(len(iCandsX)):
                    if vJet.DeltaR(vCandsX[iX]) < 0.8:
                        Jet_ovlp_iFat[iJet] = iCandsX[iX]
                        break
            for iMu in range(len(iSelMus)):
                if vJet.DeltaR(vSelMus[iMu]) < 0.4:
                    Jet_ovlp_iMu[iJet] = iSelMus[iX]
                    break
            for iEle in range(len(iSelEles)):
                if vJet.DeltaR(vSelEles[iEle]) < 0.4:
                    Jet_ovlp_iEle[iJet] = iSelEles[iX]
                    break
            ## Common jet pre-selection
            if jet.pt    < self.Jet_presel_pt: continue
            if jet.jetId < self.Jet_presel_ID: continue
            if (jet.pt < 50 and jet.puId < 4): continue
            Jet_presel_bits[iJet] = 1
            ## Reject all AK4 jets overlapping Higgs candidate AK8 jet
            if iCandH >= 0 and Jet_ovlp_iFat[iJet] == iCandH: continue
            ## If at least one triggerable lepton, reject jets overlapping selected leptons
            if nTrigLeps > 0 and (Jet_ovlp_iMu[iJet] >= 0 or Jet_ovlp_iEle[iJet] >= 0): continue
            ## "Regular" jet selection (i.e. not part of Haa4b candidate)
            if jet.pt >= self.Jet_sel_pt:
                Jet_sel_bits[iJet] = 1
                vSelJets.append(vJet)
            ## b-tagged jet selection
            if abs(jet.eta)      > self.bJet_sel_eta: continue
            if jet.btagDeepFlavB < self.bJet_sel_flavB: continue
            if jet.pt >= self.Jet_sel_pt:
                Jet_btag_bits[iJet] = 1
            ## b-tagged jet closest to Higgs candidate AK8 jet
            if iCandH >= 0 and vJet.DeltaR(vCandH) <= self.bJet_candH_dR:
                if iJetCandH >= 0 and vJetCandH.DeltaR(vCandH) <= vJet.DeltaR(vCandH): continue
                Jet_candH_bits.fill(0)
                Jet_candH_bits[iJet] = 1
                iJetCandH = iJet
                vJetCandH = vJet
        ## End loop: for jet in Jets

        self.out.fillBranch("Jet_Haa4b_presel",    Jet_presel_bits)
        self.out.fillBranch("Jet_Haa4b_sel",       Jet_sel_bits)
        self.out.fillBranch("Jet_Haa4b_btag",      Jet_btag_bits)
        self.out.fillBranch("Jet_Haa4b_candH",     Jet_candH_bits)
        self.out.fillBranch("Jet_Haa4b_ovlp_iFat", Jet_ovlp_iFat)
        self.out.fillBranch("Jet_Haa4b_ovlp_iMu",  Jet_ovlp_iMu)
        self.out.fillBranch("Jet_Haa4b_ovlp_iEle", Jet_ovlp_iEle)
        self.out.fillBranch("Haa4b_nJetSel",   sum(Jet_sel_bits))
        self.out.fillBranch("Haa4b_nJetBtag",  sum(Jet_btag_bits))
        self.out.fillBranch("Haa4b_nFatH3b",   sum(Jet_candH_bits))


        ############################
        ## Compute useful quantities
        MET = Collection(event, "MET")
        vMET = ROOT.TLorentzVector()
        vMET.SetPtEtaPhiM(MET.pt, 0, MET.phi, 0)

        ## Pick 2 highest-pT jets for di-jet pair
        is2j = (len(vSelJets) >= 2)
        dijet_mass = ((vSelJets[0]+vSelJets[1]).M()          if is2j else -99)
        dijet_pt   = ((vSelJets[0]+vSelJets[1]).Pt()         if is2j else -99)
        dijet_dEta = (abs(vSelJets[0].DeltaEta(vSelJets[1])) if is2j else -99)
        dijet_dPhi = (abs(vSelJets[0].DeltaPhi(vSelJets[1])) if is2j else -99)
        ## Pick highest-pT muons then highest-pT electrons for di-lepton pair
        is2L = (nSelLepsNonOvlpH >= 2)
        if is2L:
            vLep1 = vSelLepsNonOvlpH[0]
            vLep2 = vSelLepsNonOvlpH[1]
            idLep1 = idSelLepsNonOvlpH[0]
            idLep2 = idSelLepsNonOvlpH[1]
        dilep_mass   = ((vLep1+vLep2).M()           if is2L else -99)
        dilep_pt     = ((vLep1+vLep2).Pt()          if is2L else -99)
        dilep_dR     = (vLep1.DeltaR(vLep2)         if is2L else -99)
        dilep_dPhi   = (abs(vLep1.DeltaPhi(vLep2))  if is2L else -99)
        dilep_charge = (2*(1-(idLep1>0)-(idLep2>0)) if is2L else -99)
        dilep_SFOS   = ((idLep1 + idLep2 == 0)      if is2L else -99)

        self.out.fillBranch("Haa4b_iFatH",        iCandH)
        self.out.fillBranch("Haa4b_FatH",         AWBdecidewhattoaddhere:tag,masses,etc)
        self.out.fillBranch("Haa4b_FatX_tagWZ",   "F")  ## Exclude lep-overlap
        self.out.fillBranch("Haa4b_FatX_tagTop",  "F")  ## Exclude lep-overlap
        self.out.fillBranch("Haa4b_dijet_mass",   dijet_mass)
        self.out.fillBranch("Haa4b_dijet_pt",     dijet_pt)
        self.out.fillBranch("Haa4b_dijet_dEta",   dijet_dEta)
        self.out.fillBranch("Haa4b_dijet_dPhi",   dijet_dPhi)
        self.out.fillBranch("Haa4b_dilep_mass",   dilep_mass)
        self.out.fillBranch("Haa4b_dilep_pt",     dilep_pt)
        self.out.fillBranch("Haa4b_dilep_dR",     dilep_dR)
        self.out.fillBranch("Haa4b_dilep_dPhi",   dilep_dPhi)
        self.out.fillBranch("Haa4b_dilep_charge", dilep_charge)
        self.out.fillBranch("Haa4b_dilep_SFOS",   dilep_SFOS)


        ####################
        ## Define categories
        cat_bit = {}
        for cat in CATS:
            cat_bit[cat] = 0
        ## 0-lepton categories: gg0l, VBFjj, Vjj, ttHad, Zvv
        if iCandH >= 0 and nTrigLeps == 0:
            ## For now, only make "exclusive" categories for >=1b, 0b+MET, 0b+dijet, and 0b
            if sum(Jet_btag_bits) > 0:
                cat_bit['ttHad'] = 1
            elif MET.pt > 200:
                if abs(vMET.DeltaPhi(vCandH)) > 0.5*math.pi and (nSelLeps - nSelLepsOvlpH) == 0:
                    cat_bit['Zvv'] = 1
            elif dijet_mass > 450 and dijet_dEta > 2.2:
                ## https://indico.cern.ch/event/1450818/#34-mohamed-darwish
                cat_bit['VBFjj'] = 1
            else:
                cat_bit['gg0l'] = 1
            ## Hadronic categories based on 2nd AK8 jet are provisional, non-exclusive
            if len(iCandsX) > 0:
                cat_bit['Vjj']   = 1
                cat_bit['ttHad'] = 1
        ## >=1-lepton categories: Zll, Wlv, ttlv, ttll, 3l
        if iCandH >= 0 and nTrigLeps >= 1 and nTrigLepsOvlpH == 0:
            if nSelLepsNonOvlpH >= 3:
                cat_bit['3l'] = 1
            elif nSelLepsNonOvlpH == 2:
                if dilep_charge == 0:
                    if sum(Jet_btag_bits) > 0:
                        cat_bit['ttll'] = 1
                    elif dilep_SFOS == 1 and abs(dilep_mass - 90.0) < 10.0:
                        cat_bit['Zll'] = 1
            elif nSelLepsNonOvlpH == 1:
                if sum(Jet_btag_bits) > 0:
                    cat_bit['ttlv'] = 1
                elif abs((vLep+vMET).DeltaPhi(vCandH)) > 0.75*math.pi:
                    cat_bit['Wlv'] = 1
        ## Figure how many good Higgs candidate events we're losing "through the cracks"
        nCats = sum([cat_bit[cat] for cat in CATS])
        cat_bit['other'] = iCandH >= 1 and nCats == 0
        ## Fill category bits
        for iCat in range(len(CATS)):
            self.out.fillBranch("Haa4b_cat_%s" % CATS[iCat], cat_bits[iCat])

        self.out.fillBranch("Haa4b_isHad", (iCandH >= 0 and nTrigLeps == 0))
        self.out.fillBranch("Haa4b_isLep", (iCandH >= 0 and nTrigLeps >= 1 and nTrigLepsOvlpH == 0))
        self.out.fillBranch("Haa4b_isMu",  (iCandH >= 0 and len(iTrigMus) >= 1 and nTrigLepsOvlpH == 0))
        self.out.fillBranch("Haa4b_isEle", (iCandH >= 0 and len(iTrigEles) >= 1 and len(iTrigMus) == 0 and nTrigLepsOvlpH == 0))

        HLT  = Collection(event, "HLT")
        L1   = Collection(event, "L1")
        Flag = Collection(event, "Flag")
        self.out.fillBranch("Haa4b_trigFat",  ( ((HLT.PFJet500 or HLT.AK8PFJet500 or HLT.AK8PFJet400_TrimMass30 or
                                                  HLT.AK8PFJet330_TrimMass30_PFAK8BoostedDoubleB_np4) and (L1.SingleJet180)) or
                                                ((HLT.AK8PFHT800_TrimMass50 or HLT.PFHT1050) and (L1.SingleJet180 or L1.HTT360er)) ) )
        self.out.fillBranch("Haa4b_trigBtag", ( (HLT.DoublePFJets116MaxDeta1p6_DoubleCaloBTagDeepCSV_p71 and
                                                 (L1.DoubleJet112er2p3_dEta_Max1p6 or L1.DoubleJet150er2p5)) or
                                                (HLT.PFHT330PT30_QuadPFJet_75_60_45_40_TriplePFBTagDeepCSV_4p5 and
                                                 (L1.HTT320er or L1.HTT360er or L1.HTT400er or L1.ETT2000 or
                                                  L1.HTT320er_QuadJet_70_55_40_40_er2p4 or
                                                  L1.HTT320er_QuadJet_80_60_er2p1_45_40_er2p3)) ) )
        self.out.fillBranch("Haa4b_trigVBF", ( (HLT.QuadPFJet103_88_75_15_PFBTagDeepCSV_1p3_VBF2 or
                                                HLT.QuadPFJet103_88_75_15_DoublePFBTagDeepCSV_1p3_7p7_VBF1) and
                                               (L1.TripleJet_95_75_65_DoubleJet_75_65_er2p5 or
                                                L1.HTT320er or L1.SingleJet180) ) )
        self.out.fillBranch("Haa4b_trigMET", ( ((HLT.PFMET120_PFMHT120_IDTight_PFHT60 or HLT.PFMETNoMu120_PFMHTNoMu120_IDTight_PFHT60) and
                                                (L1.ETMHF90_HTT60er or L1.ETMHF100_HTT60er or L1.ETMHF110_HTT60er)) or
                                               ((HLT.PFMET110_PFMHT110_IDTight_CaloBTagDeepCSV_3p1 or
                                                 HLT.PFMETTypeOne200_HBHE_BeamHaloCleaned or HLT.PFMETTypeOne140_PFMHT140_IDTight) and
                                                (L1.ETMHF100 or L1.ETMHF110 or L1.ETMHF120 or L1.ETMHF130)) ) )
        self.out.fillBranch("Haa4b_trigMu",  ( (HLT.IsoMu24 or HLT.IsoMu50) and (L1.SingleMu22 or L1.SingleMu25) ) )
        self.out.fillBranch("Haa4b_trigEle", ( (HLT.Ele32_WPTight_Gsf or HLT.Ele50_CaloIdVT_GsfTrkIdT_PFJet165 or
                                                HLT.Ele115_CaloIdVT_GsfTrkIdT or HLT.Ele35_WPTight_Gsf_L1EGMT) ) )
        self.out.fillBranch("Haa4b_passFilters", (Flag.goodVertices and Flag.globalSuperTightHalo2016Filter and Flag.HBHENoiseFilter and
                                                  Flag.HBHENoiseIsoFilter and Flag.eeBadScFilter and Flag.BadPFMuonFilter and
                                                  Flag.BadPFMuonDzFilter and Flag.ecalBadCalibFilter and Flag.EcalDeadCellTriggerPrimitiveFilter) )


        ############
        ## All done!
        return True

Haa4bObjectSelectionBranches = lambda: Haa4bObjectSelectionProducer()
