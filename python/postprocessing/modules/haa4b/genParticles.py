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

        GPks = ['H','X1','X2','a1','a2','b11','b12','b21','b22','d11','d12','d13','d21','d22','d23']
        for gpk in GPks:
            self.out.branch("GEN_%s_pdgId" % gpk, "I")

        self.out.branch("GEN_H_pt",    "F")
        self.out.branch("GEN_X1_pt",   "F")
        self.out.branch("GEN_X2_pt",   "F")
        self.out.branch("GEN_H_mass",  "F")
        self.out.branch("GEN_a1_mass", "F")
        self.out.branch("GEN_a2_mass", "F")

        self.out.branch("GEN_H_nB_AK8",  "I")  ## Number of b quarks from Higgs with dR < 0.8
        self.out.branch("GEN_H_nB_AK14", "I")  ## Number of b quarks from Higgs with dR < 1.4
        self.out.branch("GEN_H_dR_max2", "F")  ## 2nd-largest dR of decay products from parent
        self.out.branch("GEN_H_dR_max",  "F")  ## Largest dR of decay products from parent
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

        GPks = ['H','X1','X2','a1','a2','b11','b12','b21','b22','d11','d12','d13','d21','d22','d23']
        idx = {}
        pid = {}
        vec = {}
        for gpk in GPks:
            idx[gpk] = -99
            pid[gpk] = -99
            vec[gpk] = ROOT.TLorentzVector()

        H_nB_AK8  = 0
        H_nB_AK14 = 0
        H_dR_max2 = -99.0
        H_dR_max  = -99.0
        X1_dR = -99.0
        X2_dR = -99.0

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
                idx['H'] = iGP
                pid['H'] = gp.pdgId
                vec['H'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)

            ## W, Z, or top immediately before decay
            if abs(gp.pdgId) in [6,23,24] and gp.status == 62:
                if idx['X1'] < 0:
                    idx['X1'] = iGP
                    pid['X1'] = gp.pdgId
                    vec['X1'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                elif idx['X2'] < 0:
                    if gp.pt < vec['X1'].Pt() or abs(gp.pdgId) != abs(pid['X1']):
                        idx['X2'] = iGP
                        pid['X2'] = gp.pdgId
                        vec['X2'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                    else:
                        idx['X2'] = idx['X1']
                        pid['X2'] = pid['X1']
                        vec['X2'] = vec['X1']
                        idx['X1'] = iGP
                        pid['X1'] = gp.pdgId
                        vec['X1'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)

            ## "a" bosons directly from Higgs decay (also allow photons and Z bosons)
            if abs(gp.pdgId) in [22,23,36] and iMom >= 0 and GPs[iMom].pdgId == 25:
                if idx['a1'] < 0:
                    idx['a1'] = iGP
                    pid['a1'] = gp.pdgId
                    vec['a1'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                elif idx['a2'] < 0:
                    ## If > 5% mass difference, a1 = higher-mass "a"
                    ## If < 5% mass difference, a1 = higher-pT "a"
                    if ( (abs(gp.mass - vec['a1'].M()) / (gp.mass + vec['a1'].M()) > 0.1 and gp.mass < vec['a1'].M()) or
                         (abs(gp.mass - vec['a1'].M()) / (gp.mass + vec['a1'].M()) <= 0.1 and gp.pt  < vec['a1'].Pt()) ):
                        idx['a2'] = iGP
                        pid['a2'] = gp.pdgId
                        vec['a2'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                    else:
                        idx['a2'] = idx['a1']
                        pid['a2'] = pid['a1']
                        vec['a2'] = vec['a1']
                        idx['a1'] = iGP
                        pid['a1'] = gp.pdgId
                        vec['a1'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)

            ## b quarks from "a"/Z/gamma boson decay, or directly from Higgs decay
            if abs(gp.pdgId) == 5 and iMom >= 0 and GPs[iMom].pdgId in [-25/gp.pdgId,22,23,25,36]:
                ## Include b quarks radiated from oppositely-charged b quarks, if parent comes from "a"/H/Z/gamma 
                if abs(GPs[iMom].pdgId) == 5 and (iGrand < 0 or not GPs[iGrand].pdgId in [22,23,25,26]):
                    continue
                if iMom == idx['a1'] or (idx['b12'] < 0 and iMom != idx['a2']):
                    if idx['b11'] < 0:
                        idx['b11'] = iGP
                        pid['b11'] = gp.pdgId
                        vec['b11'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                    elif idx['b12'] < 0:
                        if gp.pt < vec['b11'].Pt():
                            idx['b12'] = iGP
                            pid['b12'] = gp.pdgId
                            vec['b12'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                        else:
                            idx['b12'] = idx['b11']
                            pid['b12'] = pid['b11']
                            vec['b12'] = vec['b11']
                            idx['b11'] = iGP
                            pid['b11'] = gp.pdgId
                            vec['b11'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                elif iMom == idx['a2'] or idx['b22'] < 0:
                    if idx['b21'] < 0:
                        idx['b21'] = iGP
                        pid['b21'] = gp.pdgId
                        vec['b21'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                    elif idx['b22'] < 0:
                        if gp.pt < vec['b21'].Pt():
                            idx['b22'] = iGP
                            pid['b22'] = gp.pdgId
                            vec['b22'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                        else:
                            idx['b22'] = idx['b21']
                            pid['b22'] = pid['b21']
                            vec['b22'] = vec['b21']
                            idx['b21'] = iGP
                            pid['b21'] = gp.pdgId
                            vec['b21'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                            
            ## Partons from W, Z, or top decay
            if iMom >= 0 and abs(GPs[iMom].pdgId) in [5,6,23,24] and abs(gp.pdgId) in [1,2,3,4,5,11,12,13,14,15,16]:
                ## 1st decay product must come from W or Z (b from top reserved for 3rd decay product)
                if abs(GPs[iMom].pdgId) in [23,24] and idx['d12'] < 0 and \
                   (GPs[iMom].pdgId == pid['X1'] or (abs(pid['X1']) == 6 and pid['X1']*GPs[iMom].pdgId > 0)):
                    if idx['d11'] < 0:
                        idx['d11'] = iGP
                        pid['d11'] = gp.pdgId
                        vec['d11'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                    elif idx['d12'] < 0:
                        if gp.pt < vec['d11'].Pt() or (abs(gp.pdgId) in [12,14,16] and abs(pid['d11']) in [11,13,15]):
                            idx['d12'] = iGP
                            pid['d12'] = gp.pdgId
                            vec['d12'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                        else:
                            idx['d12'] = idx['d11']
                            pid['d12'] = pid['d11']
                            vec['d12'] = vec['d11']
                            idx['d11'] = iGP
                            pid['d11'] = gp.pdgId
                            vec['d11'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                elif abs(GPs[iMom].pdgId) in [23,24] and idx['d22'] < 0 and \
                     (GPs[iMom].pdgId == pid['X2'] or (abs(pid['X2']) == 6 and pid['X2']*GPs[iMom].pdgId > 0)):
                    if idx['d21'] < 0:
                        idx['d21'] = iGP
                        pid['d21'] = gp.pdgId
                        vec['d21'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                    elif idx['d22'] < 0:
                        if gp.pt < vec['d21'].Pt() or (abs(gp.pdgId) in [12,14,16] and abs(pid['d21']) in [11,13,15]):
                            idx['d22'] = iGP
                            pid['d22'] = gp.pdgId
                            vec['d22'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                        else:
                            idx['d22'] = idx['d21']
                            pid['d22'] = pid['d21']
                            vec['d22'] = vec['d21']
                            idx['d21'] = iGP
                            pid['d21'] = gp.pdgId
                            vec['d21'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                ## b quark from top decay always in 3rd decay product
                if ((iGrand >= 0 and abs(GPs[iMom].pdgId) == 5 and abs(GPs[iGrand].pdgId) == 6) or \
                    abs(GPs[iMom].pdgId) == 6) and abs(gp.pdgId) == 5:
                    if pid['X1'] in [GPs[iMom].pdgId, (GPs[iGrand].pdgId if iGrand >= 0 else -99)] and idx['d13'] < 0:
                        idx['d13'] = iGP
                        pid['d13'] = gp.pdgId
                        vec['d13'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
                    elif pid['X2'] in [GPs[iMom].pdgId, (GPs[iGrand].pdgId if iGrand >= 0 else -99)] and idx['d23'] < 0:
                        idx['d23'] = iGP
                        pid['d23'] = gp.pdgId
                        vec['d23'].SetPtEtaPhiM(gp.pt, gp.eta, gp.phi, gp.mass)
            ## End conditional: if iMom >= 0 and abs(GPs[iMom].pdgId) in [6,23,24] and abs(gp.pdgId) in [1,2,3,4,5,11,12,13,14,15,16]
        ## End loop: for gp in GPs

        ## Compute maximum dR of decay products
        H_dRs = [vec['H'].DeltaR(vec['b11']) if idx['b11'] >= 0 else -99,
                 vec['H'].DeltaR(vec['b12']) if idx['b12'] >= 0 else -99,
                 vec['H'].DeltaR(vec['b21']) if idx['b21'] >= 0 else -99,
                 vec['H'].DeltaR(vec['b22']) if idx['b22'] >= 0 else -99]
        X1_dRs = [vec['X1'].DeltaR(vec['d11']) if idx['d11'] >= 0 else -99,
                  vec['X1'].DeltaR(vec['d12']) if idx['d12'] >= 0 else -99,
                  vec['X1'].DeltaR(vec['d13']) if idx['d13'] >= 0 else -99]
        X2_dRs = [vec['X2'].DeltaR(vec['d21']) if idx['d21'] >= 0 else -99,
                  vec['X2'].DeltaR(vec['d22']) if idx['d22'] >= 0 else -99,
                  vec['X2'].DeltaR(vec['d23']) if idx['d23'] >= 0 else -99]

        H_dRs.sort()
        H_nB_AK8  = sum([(dr >= 0 and dr < 0.8) for dr in H_dRs])
        H_nB_AK14 = sum([(dr >= 0 and dr < 1.4) for dr in H_dRs])
        H_dR_max2 = H_dRs[2]
        H_dR_max  = max(H_dRs)
        X1_dR = max(X1_dRs)
        X2_dR = max(X2_dRs)

        ## Categorize processes
        proc_gg0l_VBFjj = (idx['X1'] < 0 and idx['X2'] < 0)
        proc_Vjj   = (abs(pid['X1']) in [23,24] and abs(pid['d11']) <= 5 and not abs(pid['d21']) in [11,12,13,14,15,16])
        proc_ttHad = (abs(pid['X1']) == 6 and abs(pid['X2']) == 6 and abs(pid['d11']) <= 4 and abs(pid['d21']) <= 4)
        proc_Zvv   = (pid['X1'] == 23 and abs(pid['d11']) in [12,14,16] and abs(pid['d12']) in [12,14,16])
        proc_Zll   = (pid['X1'] == 23 and abs(pid['d11']) in [11,13,15] and abs(pid['d12']) in [11,13,15])
        proc_Wlv   = (abs(pid['X1']) == 24 and abs(pid['d11']) in [11,13,15])
        proc_ttlv  = (abs(pid['X1']) == 6 and abs(pid['X2']) == 6 and \
                      (abs(pid['d11']) in [11,13,15]) + (abs(pid['d21']) in [11,13,15]) == 1)
        proc_ttll  = (abs(pid['X1']) == 6 and abs(pid['X2']) == 6 and \
                      (abs(pid['d11']) in [11,13,15]) + (abs(pid['d21']) in [11,13,15]) == 2)
        proc_idx = proc_gg0l_VBFjj + 3*proc_Vjj + 4*proc_ttHad + 5*proc_Zvv + 6*proc_Zll + 7*proc_Wlv + 8*proc_ttlv + 9*proc_ttll

        ## Fiducial quantites for particles to pass category selection cuts
        fatH = (idx['H'] >= 0 and vec['H'].Pt() > 170 and H_nB_AK8 >= 3 and H_nB_AK14 >= 4)
        nBs  = ((vec['d13'].Pt() > 30 and abs(vec['d13'].Eta()) < 2.4) +
                (vec['d23'].Pt() > 30 and abs(vec['d23'].Eta()) < 2.4))
        nFJs = ((vec['X1'].Pt() > 170 and X1_dR < 0.8 and abs(vec['X1'].Eta()) < 2.4) +
                (vec['X2'].Pt() > 170 and X2_dR < 0.8 and abs(vec['X2'].Eta()) < 2.4))
        nLeps = ((abs(pid['d11']) in [11,13] and vec['d11'].Pt() > 10 and abs(vec['d11'].Eta()) < 2.4) +
                 (abs(pid['d12']) in [11,13] and vec['d12'].Pt() > 10 and abs(vec['d12'].Eta()) < 2.4) +
                 (abs(pid['d21']) in [11,13] and vec['d21'].Pt() > 10 and abs(vec['d21'].Eta()) < 2.4)	+
                 (abs(pid['d22']) in [11,13] and vec['d22'].Pt() > 10 and abs(vec['d22'].Eta()) < 2.4))
        
        trigLep = ((abs(pid['d11']) == 13 and vec['d11'].Pt() > 24 and abs(vec['d11'].Eta()) < 2.4) or
                   (abs(pid['d12']) == 13 and vec['d12'].Pt() > 24 and abs(vec['d12'].Eta()) < 2.4) or
                   (abs(pid['d21']) == 13 and vec['d21'].Pt() > 24 and abs(vec['d21'].Eta()) < 2.4) or
                   (abs(pid['d22']) == 13 and vec['d22'].Pt() > 24 and abs(vec['d22'].Eta()) < 2.4) or
                   (abs(pid['d11']) == 11 and vec['d11'].Pt() > 35 and abs(vec['d11'].Eta()) < 2.5) or
                   (abs(pid['d12']) == 11 and vec['d12'].Pt() > 35 and abs(vec['d12'].Eta()) < 2.5) or
                   (abs(pid['d21']) == 11 and vec['d21'].Pt() > 35 and abs(vec['d21'].Eta()) < 2.5) or
                   (abs(pid['d22']) == 11 and vec['d22'].Pt() > 35 and abs(vec['d22'].Eta()) < 2.5))

        cat_Vjj   = (fatH and proc_Vjj   and nFJs >= 1)
        cat_ttHad = (fatH and proc_ttHad and nBs >= 1 and nFJs >= 1)
        cat_Zvv   = (fatH and proc_Zvv   and vec['X1'].Pt() > 200)
        cat_Zll   = (fatH and proc_Zll   and trigLep and abs(vec['X1'].M() - 91) < 10.0 and vec['d12'].Pt() > 10)
        cat_Wlv   = (fatH and (proc_Wlv or proc_ttlv) and trigLep and nBs == 0 and
                     abs((vec['d11']+vec['d12']).DeltaPhi(vec['H'])) > 0.75*math.pi)
        cat_ttlv  = (fatH and (proc_ttlv or proc_ttll) and trigLep and nBs >= 1 and nLeps == 1)
        cat_ttll  = (fatH and proc_ttll  and trigLep and nBs >= 1 and nLeps == 2)
        cat_idx = 3*cat_Vjj + 4*cat_ttHad + 5*cat_Zvv + 6*cat_Zll + 7*cat_Wlv + 8*cat_ttlv + 9*cat_ttll
        cat_gg0l_VBFjj = (fatH and (cat_idx == 0) and (not trigLep))
        cat_idx += cat_gg0l_VBFjj

        ## Fill output branches
        for gpk in GPks:
            self.out.fillBranch("GEN_%s_idx"   % gpk, idx[gpk])
            self.out.fillBranch("GEN_%s_pdgId" % gpk, pid[gpk])
            if idx[gpk] >= 0 and event.GenPart_pdgId[idx[gpk]] != pid[gpk]:
                print('\nWeird error!!! idx[%s] = %d, pid[%s] = %d, pdgId = %d' % (gpk, idx[gpk], gpk, pid[gpk],
                                                                                   event.GenPart_pdgId[idx[gpk]]))
                print('(run == %d && luminosityBlock == %d && event == %d)' % (event.run, event.luminosityBlock, event.event))

        self.out.fillBranch("GEN_H_pt",    vec['H'].Pt())
        self.out.fillBranch("GEN_X1_pt",   vec['X1'].Pt())
        self.out.fillBranch("GEN_X2_pt",   vec['X2'].Pt())
        self.out.fillBranch("GEN_H_mass",  vec['H'].M())
        self.out.fillBranch("GEN_a1_mass", vec['a1'].M())
        self.out.fillBranch("GEN_a2_mass", vec['a2'].M())

        self.out.fillBranch("GEN_H_nB_AK8",  H_nB_AK8)
        self.out.fillBranch("GEN_H_nB_AK14", H_nB_AK14)
        self.out.fillBranch("GEN_H_dR_max",  H_dR_max)
        self.out.fillBranch("GEN_H_dR_max2", H_dR_max2)
        self.out.fillBranch("GEN_H_dR_max",  H_dR_max)
        self.out.fillBranch("GEN_X1_dR", X1_dR)
        self.out.fillBranch("GEN_X2_dR", X2_dR)

        self.out.fillBranch("GEN_fatH4b",  idx['H'] >= 0 and vec['H'].Pt() > 170 and H_nB_AK8 >= 4)
        self.out.fillBranch("GEN_fatH3b",  idx['H'] >= 0 and vec['H'].Pt() > 170 and H_nB_AK8 == 3 and H_nB_AK14 >= 4)
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
