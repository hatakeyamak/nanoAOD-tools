## H --> aa --> 4b search with "boosted" decays to AK8 jets
## Find GEN-level Higgs and associated particles and decay products

from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
import ROOT
import os
import sys
import math
import random
ROOT.PyConfig.IgnoreCommandLineOptions = True

class Haa4bGenParticlesProducer(Module):
    def __init__(self):
        pass
    
    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree

        ## Branches for GEN-level particles, per event
        self.out.branch("GEN_H_idx",   "I")  ## Higgs
        self.out.branch("GEN_X1_idx",  "I")  ## 1st associated heavy particle
        self.out.branch("GEN_X2_idx",  "I")  ## 2nd associated heavy particle
        self.out.branch("GEN_a1_idx",  "I")  ## Higher-mass or higher-pT "a" from Higgs decay
        self.out.branch("GEN_a2_idx",  "I")  ## Lower-mass or lower-pT "a" from Higgs decay
        self.out.branch("GEN_b11_idx", "I")  ## Higher-pT b-quark from a1
        self.out.branch("GEN_b12_idx", "I")  ## Lower-pT b-quark from a1
        self.out.branch("GEN_b21_idx", "I")  ## Higher-pT b-quark from a2
        self.out.branch("GEN_b22_idx", "I")  ## Lower-pT b-quark from a2
        self.out.branch("GEN_d11_idx", "I")   ## Highest-pT particle from X1 decay (charged leptons have priority)
        self.out.branch("GEN_d12_idx", "I")   ## Lower-pT particle from X1 decay (neutrinio if it exists)
        self.out.branch("GEN_d13_idx", "I")   ## b-quark from X1 decay if X1 is a top quark
        self.out.branch("GEN_d21_idx", "I")   ## Highest-pT particle from X2 decay (charged leptons have priority)
        self.out.branch("GEN_d22_idx", "I")   ## Lower-pT particle from X2 decay (neutrinio if it exists)
        self.out.branch("GEN_d23_idx", "I")   ## b-quark from X2 decay if X2 is a top quark

        self.out.branch("GEN_X1_pdgId",  "I")
        self.out.branch("GEN_X2_pdgId",  "I")
        self.out.branch("GEN_d11_pdgId", "I")
        self.out.branch("GEN_d12_pdgId", "I")
        self.out.branch("GEN_d13_pdgId", "I")
        self.out.branch("GEN_d21_pdgId", "I")
        self.out.branch("GEN_d22_pdgId", "I")
        self.out.branch("GEN_d23_pdgId", "I")
        
        self.out.branch("GEN_H_pt",  "F")
        self.out.branch("GEN_X1_pt", "F")
        self.out.branch("GEN_X2_pt", "F")
        self.out.branch("GEN_H_dR3", "F")  ## 3rd-largest dR of decay products from parent
        self.out.branch("GEN_H_dR",  "F")  ## Largest dR of decay products from parent
        self.out.branch("GEN_X1_dR", "F")
        self.out.branch("GEN_X2_dR", "F")

        self.out.branch("GEN_fatH4b",  "b")
        self.out.branch("GEN_fatH3b",  "b")
        self.out.branch("GEN_trigLep", "b")
        self.out.branch("GEN_nLeps",   "I")
        self.out.branch("GEN_nBjets",  "I")
        self.out.branch("GEN_nFatX",   "I")
        
        ## Store process corresponding to different selection categories,
        ## and GEN-level category including pT/eta/dR cuts on GEN objects
        CATS = ['gg0l_VBFjj','Vjj','ttHad','Zvv','Zll','Wlv','ttlv','ttll']
        for cat in CATS:
            self.out.branch("GEN_proc_%s" % cat, "b")
            self.out.branch("GEN_cat_%s"  % cat, "b")
        self.out.branch("GEN_proc_idx", "I")
        self.out.branch("GEN_cat_idx",  "I")

        
    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        
        H_idx   = -99
        X1_idx  = -99
        X2_idx  = -99
        a1_idx  = -99
        a2_idx  = -99
        b11_idx = -99
        b12_idx = -99
        b21_idx = -99
        b22_idx = -99
        d11_idx = -99
        d12_idx = -99
        d13_idx = -99
        d21_idx = -99
        d22_idx = -99
        d23_idx = -99

        X1_pdgId  = -99
        X2_pdgId  = -99
        d11_pdgId = -99
        d12_pdgId = -99
        d13_pdgId = -99
        d21_pdgId = -99
        d22_pdgId = -99
        d23_pdgId = -99
        
        H_dR3 = -99.0
        H_dR  = -99.0
        X1_dR = -99.0
        X2_dR = -99.0

        H_vec   = ROOT.TLorentzVector()
        X1_vec  = ROOT.TLorentzVector()
        X2_vec  = ROOT.TLorentzVector()
        a1_vec  = ROOT.TLorentzVector()
        a2_vec  = ROOT.TLorentzVector()
        b11_vec = ROOT.TLorentzVector()
        b12_vec = ROOT.TLorentzVector()
        b21_vec = ROOT.TLorentzVector()
        b22_vec = ROOT.TLorentzVector()
        d11_vec = ROOT.TLorentzVector()
        d12_vec = ROOT.TLorentzVector()
        d13_vec = ROOT.TLorentzVector()
        d21_vec = ROOT.TLorentzVector()
        d22_vec = ROOT.TLorentzVector()
        d23_vec = ROOT.TLorentzVector()

        ###################
        ## Get GenPart info
        GPs = Collection(event, "GenPart")
        iGP = -1
        for gp in GPs:
            iGP += 1
            iMom = gp.genPartIdxMother
            iGrand = GPs[iMom].genPartIdxMother if iMom >= 0 else -99

            ## Higgs immediately before decay
            if gp.pdgId == 25 and gp.status == 62:
                H_idx = iGP
                H_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)

            ## W, Z, or top immediately before decay
            if abs(gp.pdgId) in [6,23,24] and gp.status == 62:
                if X1_idx < 0:
                    X1_idx = iGP
                    X1_pdgId = gp.pdgId
                    X1_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                elif X2_idx < 0:
                    if gp.pt < X1_vec.Pt() or abs(gp.pdgId) != abs(X1_pdgId):
                        X2_idx = iGP
                        X2_pdgId = gp.pdgId
                        X2_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                    else:
                        X2_idx = X1_idx
                        X2_pdgId = X1_pdgId
                        X2_vec = X1_vec
                        X1_idx = iGP
                        X1_pdgId = gp.pdgId
                        X1_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)

            ## "a" bosons directly from Higgs decay
            if gp.pdgId == 36 and iMom >= 0 and GPs[iMom].pdgId == 25:
                if a1_idx < 0:
                    a1_idx = iGP
                    a1_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                elif a2_idx < 0:
                    ## If > 5% mass difference, a1 = higher-mass "a"
                    ## If < 5% mass difference, a1 = higher-pT "a"
                    if ( (abs(gp.mass - a1_vec.M()) / (gp.mass + a1_vec.M()) > 0.1 and gp.mass < a1_vec.M()) or
                         (abs(gp.mass - a1_vec.M()) / (gp.mass + a1_vec.M()) <= 0.1 and gp.pt  < a1_vec.Pt()) ):
                        a2_idx = iGP
                        a2_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                    else:
                        a2_idx = a1_idx
                        a2_vec = a1_vec
                        a1_idx = iGP
                        a1_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)

            ## b quarks directly from "a" boson decay, or directly from Higgs decay
            if abs(gp.pdgId) == 5 and iMom >= 0 and GPs[iMom].pdgId in [25,36]:
                if iMom == a1_idx or GPs[iMom].pdgId == 25:
                    if b11_idx < 0:
                        b11_idx = iGP
                        b11_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                    elif b12_idx < 0:
                        if gp.pt < b11_vec.Pt():
                            b12_idx = iGP
                            b12_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                        else:
                            b12_idx = b11_idx
                            b12_vec = b11_vec
                            b11_idx = iGP
                            b11_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                elif iMom == a2_idx or (GPs[iMom].pdgId == 25 and b12_idx >= 0):
                    if b21_idx < 0:
                        b21_idx = iGP
                        b21_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                    elif b22_idx < 0:
                        if gp.pt < b21_vec.Pt():
                            b22_idx = iGP
                            b22_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                        else:
                            b22_idx = b21_idx
                            b22_vec = b21_vec
                            b21_idx = iGP
                            b21_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                            
            ## Partons from W, Z, or top decay
            if iMom >= 0 and abs(GPs[iMom].pdgId) in [5,6,23,24] and abs(gp.pdgId) in [1,2,3,4,5,11,12,13,14,15,16]:
                ## 1st decay product must come from W or Z (b from top reserved for 3rd decay product)
                if abs(GPs[iMom].pdgId) in [23,24] and d12_idx < 0 and \
                   (GPs[iMom].pdgId == X1_pdgId or (abs(X1_pdgId) == 6 and X1_pdgId*GPs[iMom].pdgId > 0)):
                    if d11_idx < 0:
                        d11_idx = iGP
                        d11_pdgId = gp.pdgId
                        d11_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                    elif d12_idx < 0:
                        if gp.pt < d11_vec.Pt() or (abs(gp.pdgId) in [12,14,16] and abs(d11_pdgId) in [11,13,15]):
                            d12_idx = iGP
                            d12_pdgId = gp.pdgId
                            d12_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                        else:
                            d12_idx = d11_idx
                            d12_pdgId = d11_pdgId
                            d12_vec = d11_vec
                            d11_idx = iGP
                            d11_pdgId = gp.pdgId
                            d11_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                elif abs(GPs[iMom].pdgId) in [23,24] and d22_idx < 0 and \
                     (GPs[iMom].pdgId == X2_pdgId or (abs(X2_pdgId) == 6 and X2_pdgId*GPs[iMom].pdgId > 0)):
                    if d21_idx < 0:
                        d21_idx = iGP
                        d21_pdgId = gp.pdgId
                        d21_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                    elif d22_idx < 0:
                        if gp.pt < d21_vec.Pt() or (abs(gp.pdgId) in [12,14,16] and abs(d21_pdgId) in [11,13,15]):
                            d22_idx = iGP
                            d22_pdgId = gp.pdgId
                            d22_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                        else:
                            d22_idx = d21_idx
                            d22_pdgId = d21_pdgId
                            d22_vec = d21_vec
                            d21_idx = iGP
                            d21_pdgId = gp.pdgId
                            d21_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                ## b quark from top decay always in 3rd decay product
                if ((iGrand >= 0 and abs(GPs[iMom].pdgId) == 5 and abs(GPs[iGrand].pdgId) == 6) or \
                    abs(GPs[iMom].pdgId) == 6) and abs(gp.pdgId) == 5:
                    if X1_pdgId in [GPs[iMom].pdgId, (GPs[iGrand].pdgId if iGrand >= 0 else -99)] and d13_idx < 0:
                        d13_idx = iGP
                        d13_pdgId = gp.pdgId
                        d13_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                    elif X2_pdgId in [GPs[iMom].pdgId, (GPs[iGrand].pdgId if iGrand >= 0 else -99)] and d23_idx < 0:
                        d23_idx = iGP
                        d23_pdgId = gp.pdgId
                        d23_vec.SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
            ## End conditional: if iMom >= 0 and abs(GPs[iMom].pdgId) in [6,23,24] and abs(gp.pdgId) in [1,2,3,4,5,11,12,13,14,15,16]
        ## End loop: for gp in GPs

        ## Compute maximum dR of decay products
        H_dRs = [H_vec.DeltaR(b11_vec) if b11_idx >= 0 else -99,
                 H_vec.DeltaR(b12_vec) if b12_idx >= 0 else -99,
                 H_vec.DeltaR(b21_vec) if b21_idx >= 0 else -99,
                 H_vec.DeltaR(b22_vec) if b22_idx >= 0 else -99]
        X1_dRs = [X1_vec.DeltaR(d11_vec) if d11_idx >= 0 else -99,
                  X1_vec.DeltaR(d12_vec) if d12_idx >= 0 else -99,
                  X1_vec.DeltaR(d13_vec) if d13_idx >= 0 else -99]
        X2_dRs = [X2_vec.DeltaR(d21_vec) if d21_idx >= 0 else -99,
                  X2_vec.DeltaR(d22_vec) if d22_idx >= 0 else -99,
                  X2_vec.DeltaR(d23_vec) if d23_idx >= 0 else -99]

        H_dRs.sort()
        H_dR3 = H_dRs[2]
        H_dR  = max(H_dRs)
        X1_dR = max(X1_dRs)
        X2_dR = max(X2_dRs)

        ## Categorize processes
        proc_gg0l_VBFjj = (X1_idx < 0 and X2_idx < 0)
        proc_Vjj   = (abs(X1_pdgId) in [23,24] and abs(d11_pdgId) <= 5 and not abs(d21_pdgId) in [11,12,13,14,15,16])
        proc_ttHad = (abs(X1_pdgId) == 6 and abs(X2_pdgId) == 6 and abs(d11_pdgId) <= 4 and abs(d21_pdgId) <= 4)
        proc_Zvv   = (X1_pdgId == 23 and abs(d11_pdgId) in [12,14,16] and abs(d12_pdgId) in [12,14,16])
        proc_Zll   = (X1_pdgId == 23 and abs(d11_pdgId) in [11,13,15] and abs(d12_pdgId) in [11,13,15])
        proc_Wlv   = (abs(X1_pdgId) == 24 and abs(d11_pdgId) in [11,13,15])
        proc_ttlv  = (abs(X1_pdgId) == 6 and abs(X2_pdgId) == 6 and \
                      (abs(d11_pdgId) in [11,13,15]) + (abs(d21_pdgId) in [11,13,15]) == 1)
        proc_ttll  = (abs(X1_pdgId) == 6 and abs(X2_pdgId) == 6 and \
                      (abs(d11_pdgId) in [11,13,15]) + (abs(d21_pdgId) in [11,13,15]) == 2)
        proc_idx = proc_gg0l_VBFjj + 3*proc_Vjj + 4*proc_ttHad + 5*proc_Zvv + 6*proc_Zll + 7*proc_Wlv + 8*proc_ttlv + 9*proc_ttll

        ## Fiducial quantites for particles to pass category selection cuts
        fatH = (H_idx >= 0 and H_vec.Pt() > 170 and (H_dR < 0.8 or (H_dR3 < 0.8 and H_dR < 1.4)))
        nBs  = ((d13_vec.Pt() > 30 and abs(d13_vec.Eta()) < 2.4) +
                (d23_vec.Pt() > 30 and abs(d23_vec.Eta()) < 2.4))
        nFJs = ((X1_vec.Pt() > 170 and X1_dR < 0.8 and abs(X1_vec.Eta()) < 2.4) +
                (X2_vec.Pt() > 170 and X2_dR < 0.8 and abs(X2_vec.Eta()) < 2.4))
        nLeps = ((abs(d11_pdgId) in [11,13] and d11_vec.Pt() > 10 and abs(d11_vec.Eta()) < 2.4) +
                 (abs(d12_pdgId) in [11,13] and d12_vec.Pt() > 10 and abs(d12_vec.Eta()) < 2.4) +
                 (abs(d21_pdgId) in [11,13] and d21_vec.Pt() > 10 and abs(d21_vec.Eta()) < 2.4)	+
                 (abs(d22_pdgId) in [11,13] and d22_vec.Pt() > 10 and abs(d22_vec.Eta()) < 2.4))
        
        trigLep = ((abs(d11_pdgId) == 13 and d11_vec.Pt() > 24 and abs(d11_vec.Eta()) < 2.4) or
                   (abs(d12_pdgId) == 13 and d12_vec.Pt() > 24 and abs(d12_vec.Eta()) < 2.4) or
                   (abs(d21_pdgId) == 13 and d21_vec.Pt() > 24 and abs(d21_vec.Eta()) < 2.4) or
                   (abs(d22_pdgId) == 13 and d22_vec.Pt() > 24 and abs(d22_vec.Eta()) < 2.4) or
                   (abs(d11_pdgId) == 11 and d11_vec.Pt() > 35 and abs(d11_vec.Eta()) < 2.5) or
                   (abs(d12_pdgId) == 11 and d12_vec.Pt() > 35 and abs(d12_vec.Eta()) < 2.5) or
                   (abs(d21_pdgId) == 11 and d21_vec.Pt() > 35 and abs(d21_vec.Eta()) < 2.5) or
                   (abs(d22_pdgId) == 11 and d22_vec.Pt() > 35 and abs(d22_vec.Eta()) < 2.5))

        cat_Vjj   = (fatH and proc_Vjj   and nFJs >= 1)
        cat_ttHad = (fatH and proc_ttHad and nBs >= 1 and nFJs >= 1)
        cat_Zvv   = (fatH and proc_Zvv   and X1_vec.Pt() > 200)
        cat_Zll   = (fatH and proc_Zll   and trigLep and abs(X1_vec.M() - 91) < 10.0 and d12_vec.Pt() > 10)
        cat_Wlv   = (fatH and (proc_Wlv or proc_ttlv) and trigLep and nBs == 0 and
                     abs((d11_vec+d12_vec).DeltaPhi(H_vec)) > 0.75*math.pi)
        cat_ttlv  = (fatH and (proc_ttlv or proc_ttll) and trigLep and nBs >= 1 and nLeps == 1)
        cat_ttll  = (fatH and proc_ttll  and trigLep and nBs >= 1 and nLeps == 2)
        cat_idx = 3*cat_Vjj + 4*cat_ttHad + 5*cat_Zvv + 6*cat_Zll + 7*cat_Wlv + 8*cat_ttlv + 9*cat_ttll
        cat_gg0l_VBFjj = (fatH and (cat_idx == 0) and (not trigLep))
        cat_idx += cat_gg0l_VBFjj
                

        ## Fill output branches
        self.out.fillBranch("GEN_H_idx",   H_idx)
        self.out.fillBranch("GEN_X1_idx",  X1_idx)
        self.out.fillBranch("GEN_X2_idx",  X2_idx)
        self.out.fillBranch("GEN_a1_idx",  a1_idx)
        self.out.fillBranch("GEN_a2_idx",  a2_idx)
        self.out.fillBranch("GEN_b11_idx", b11_idx)
        self.out.fillBranch("GEN_b12_idx", b12_idx)
        self.out.fillBranch("GEN_b21_idx", b21_idx)
        self.out.fillBranch("GEN_b22_idx", b22_idx)
        self.out.fillBranch("GEN_d11_idx", d11_idx)
        self.out.fillBranch("GEN_d12_idx", d12_idx)
        self.out.fillBranch("GEN_d13_idx", d13_idx)
        self.out.fillBranch("GEN_d21_idx", d21_idx)
        self.out.fillBranch("GEN_d22_idx", d22_idx)
        self.out.fillBranch("GEN_d23_idx", d23_idx)

        self.out.fillBranch("GEN_X1_pdgId",  X1_pdgId)
        self.out.fillBranch("GEN_X2_pdgId",  X2_pdgId)
        self.out.fillBranch("GEN_d11_pdgId", d11_pdgId)
        self.out.fillBranch("GEN_d12_pdgId", d12_pdgId)
        self.out.fillBranch("GEN_d13_pdgId", d13_pdgId)
        self.out.fillBranch("GEN_d21_pdgId", d21_pdgId)
        self.out.fillBranch("GEN_d22_pdgId", d22_pdgId)
        self.out.fillBranch("GEN_d23_pdgId", d23_pdgId)
        
        self.out.fillBranch("GEN_H_pt",  H_vec.Pt())
        self.out.fillBranch("GEN_X1_pt", X1_vec.Pt())
        self.out.fillBranch("GEN_X2_pt", X2_vec.Pt())
        self.out.fillBranch("GEN_H_dR3", H_dR3)
        self.out.fillBranch("GEN_H_dR",  H_dR)
        self.out.fillBranch("GEN_X1_dR", X1_dR)
        self.out.fillBranch("GEN_X2_dR", X2_dR)

        self.out.fillBranch("GEN_fatH4b",  (H_idx >= 0) and (H_vec.Pt() > 170) and (H_dR < 0.8))
        self.out.fillBranch("GEN_fatH3b",  (H_idx >= 0) and (H_vec.Pt() > 170) and (H_dR > 0.8) and (H_dR3 < 0.8) and (H_dR < 1.4))
        self.out.fillBranch("GEN_trigLep", trigLep)
        self.out.fillBranch("GEN_nLeps",   nLeps)
        self.out.fillBranch("GEN_nBjets",  nBs)
        self.out.fillBranch("GEN_nFatX",   nFJs)

        self.out.fillBranch("GEN_proc_gg0l_VBFjj", proc_gg0l_VBFjj)
        self.out.fillBranch("GEN_proc_Vjj",        proc_Vjj)
        self.out.fillBranch("GEN_proc_ttHad",      proc_ttHad)
        self.out.fillBranch("GEN_proc_Zvv",        proc_Zvv)
        self.out.fillBranch("GEN_proc_Zll",        proc_Zll)
        self.out.fillBranch("GEN_proc_Wlv",        proc_Wlv)
        self.out.fillBranch("GEN_proc_ttlv",       proc_ttlv)
        self.out.fillBranch("GEN_proc_ttll",       proc_ttll)

        self.out.fillBranch("GEN_cat_gg0l_VBFjj", cat_gg0l_VBFjj)
        self.out.fillBranch("GEN_cat_Vjj",        cat_Vjj)
        self.out.fillBranch("GEN_cat_ttHad",      cat_ttHad)
        self.out.fillBranch("GEN_cat_Zvv",        cat_Zvv)
        self.out.fillBranch("GEN_cat_Zll",        cat_Zll)
        self.out.fillBranch("GEN_cat_Wlv",        cat_Wlv)
        self.out.fillBranch("GEN_cat_ttlv",       cat_ttlv)
        self.out.fillBranch("GEN_cat_ttll",       cat_ttll)

        self.out.fillBranch("GEN_proc_idx", proc_idx)
        self.out.fillBranch("GEN_cat_idx",  cat_idx)
        
        ############
        ## All done!
        return True

Haa4bGenParticlesBranches = lambda: Haa4bGenParticlesProducer()
