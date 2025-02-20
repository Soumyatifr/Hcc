import FWCore.ParameterSet.Config as cms

from FWCore.ParameterSet.VarParsing import VarParsing

process = cms.Process("HccAnalysis")

process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.threshold = 'DEBUG'
process.MessageLogger.cerr.FwkReport.reportEvery = 1000
#process.MessageLogger.categories.append('HccAna')

process.load("Configuration.StandardSequences.MagneticField_cff")
process.load("Configuration.Geometry.GeometryRecoDB_cff")
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
process.load('Configuration.StandardSequences.Services_cff')
process.GlobalTag.globaltag='130X_dataRun3_PromptAnalysis_v1'
#process.GlobalTag.globaltag='124X_dataRun3_v11'
#process.GlobalTag.globaltag='124X_dataRun3_Prompt_v10'

process.Timing = cms.Service("Timing",
                             summaryOnly = cms.untracked.bool(True)
                             )


process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(-1) )

process.options = cms.untracked.PSet(
        numberOfThreads = cms.untracked.uint32(2),
                #SkipEvent = cms.untracked.vstring('ProductNotFound')
)

process.options.numberOfConcurrentLuminosityBlocks = 1

myfilelist = cms.untracked.vstring(
    '/store/data/Run2022F/JetMET/MINIAOD/19Dec2023-v2/50000/e07ccccd-dec6-4d25-9b84-2561d5e6d0a0.root'
)

process.source = cms.Source("PoolSource",fileNames = myfilelist,
                            duplicateCheckMode = cms.untracked.string('noDuplicateCheck'),
                            )

process.TFileService = cms.Service("TFileService",
                                   fileName = cms.string("Data2022_corrected.root")
)

process.RandomNumberGeneratorService = cms.Service("RandomNumberGeneratorService",
    calibratedPatElectrons = cms.PSet(
        #initialSeed = cms.untracked.uint32(SEED), # for HPC
        initialSeed = cms.untracked.uint32(123456), # for crab
        engineName = cms.untracked.string('TRandom3')
    )
)


from PhysicsTools.SelectorUtils.tools.vid_id_tools import *
dataFormat = DataFormat.MiniAOD
switchOnVIDElectronIdProducer(process, dataFormat)
# define which IDs we want to produce
my_id_modules = [ 'RecoEgamma.ElectronIdentification.Identification.mvaElectronID_Fall17_iso_V2_cff' ]
# add them to the VID producer
for idmod in my_id_modules:
    setupAllVIDIdsInModule(process,idmod,setupVIDElectronSelection)


import os
# Jet Energy Corrections
from CondCore.DBCommon.CondDBSetup_cfi import *

# AK4 Puppi Jets JEC
process.jec_ak4 = cms.ESSource("PoolDBESSource",
                           CondDBSetup,
                           # for HPC
                           connect = cms.string("sqlite_file:Summer22EE_22Sep2023_RunF_V2_DATA.db"),
                           toGet =  cms.VPSet(
                              cms.PSet(
                                 record = cms.string("JetCorrectionsRecord"),
                                 tag = cms.string("JetCorrectorParametersCollection_Summer22EE_22Sep2023_RunF_V2_DATA_AK4PFPuppi"),
                                 label= cms.untracked.string("AK4PFPuppi")
                              ),
              )
)

# AK8 Puppi Jets JEC
process.jec_ak8 = cms.ESSource("PoolDBESSource",
                               CondDBSetup,
                               # for HPC
                               connect = cms.string("sqlite_file:Summer22EE_22Sep2023_RunF_V2_DATA.db"),
                               toGet =  cms.VPSet(
                                  cms.PSet(
                                     record = cms.string("JetCorrectionsRecord"),
                                     tag = cms.string("JetCorrectorParametersCollection_Summer22EE_22Sep2023_RunF_V2_DATA_AK8PFPuppi"),
                                     label= cms.untracked.string("AK8PFPuppi")
                                  ),
                  )
)

process.es_prefer_jec_ak4 = cms.ESPrefer('PoolDBESSource', 'jec_ak4')
process.es_prefer_jec_ak8 = cms.ESPrefer('PoolDBESSource', 'jec_ak8')

from PhysicsTools.PatAlgos.tools.jetTools import updateJetCollection

updateJetCollection(
   process,
   jetSource = cms.InputTag('slimmedJetsAK8'),
   labelName = 'UpdatedJECak8',
   jetCorrections = ('AK8PFPuppi', cms.vstring(['L1FastJet', 'L2Relative', 'L3Absolute', 'L2L3Residual']), 'None')  # Update: Safe to always add 'L2L3Residual' as MC contains dummy L2L3Residual corrections (always set to 1)
)

process.jecSequence_ak8 = cms.Sequence(process.patJetCorrFactorsUpdatedJECak8 * process.updatedPatJetsUpdatedJECak8)

updateJetCollection(
   process,
   jetSource = cms.InputTag('slimmedJetsPuppi'),
   labelName = 'UpdatedJECak4',
   jetCorrections = ('AK4PFPuppi', cms.vstring(['L1FastJet', 'L2Relative', 'L3Absolute', 'L2L3Residual']), 'None')  # Update: Safe to always add 'L2L3Residual' as MC contains dummy L2L3Residual corrections (always set to 1)
)

process.jecSequence_ak4 = cms.Sequence(process.patJetCorrFactorsUpdatedJECak4 * process.updatedPatJetsUpdatedJECak4)

updateJetCollection(
   process,
   jetSource = cms.InputTag('slimmedJetsAK8PFPuppiSoftDropPacked:SubJets'),
   labelName = 'UpdatedJECsubak4',
   jetCorrections = ('AK4PFPuppi', cms.vstring(['L1FastJet', 'L2Relative', 'L3Absolute', 'L2L3Residual']), 'None'),  # Update: Safe to always add 'L2L3Residual' as MC contains dummy L2L3Residual corrections (always set to 1)
   explicitJTA = False,          # needed for subjet b tagging
   svClustering = False,        # needed for subjet b tagging (IMPORTANT: Needs to be set to False to disable ghost-association which does not work with slimmed jets)
   fatJets = cms.InputTag('slimmedJetsAK8'), # needed for subjet b tagging
   rParam = 0.8,                # needed for subjet b tagging
   algo = 'ak'                  # has to be defined but is not used with svClustering=False
)
# la collezione di jet con le correzioni applicate si chiama "updatedPatJetsUpdatedJEC"

#process.jecSequence = cms.Sequence(process.patJetCorrFactorsUpdatedJEC * process.updatedPatJetsUpdatedJEC)
process.jecSequence_subak4 = cms.Sequence(process.patJetCorrFactorsUpdatedJECsubak4 * process.updatedPatJetsUpdatedJECsubak4)

#from CondCore.CondDB.CondDB_cfi import *
era = "Fall17_17Nov2017BCDEF_V6_DATA"

process.load("PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff")

#QGTag
process.load("CondCore.CondDB.CondDB_cfi")
process.QGPoolDBESSource = cms.ESSource("PoolDBESSource",
      DBParameters = cms.PSet(messageLevel = cms.untracked.int32(1)),
      timetype = cms.string('runnumber'),
      toGet = cms.VPSet(
        cms.PSet(
            record = cms.string('QGLikelihoodRcd'),
            tag    = cms.string('QGLikelihoodObject_cmssw8020_v2_AK4PFchs'),
            label  = cms.untracked.string('QGL_AK4PFchs')
        ),
      ),
      connect = cms.string('sqlite_file:QGL_cmssw8020_v2.db')
)
process.es_prefer_qg = cms.ESPrefer('PoolDBESSource','QGPoolDBESSource')
process.load('RecoJets.JetProducers.QGTagger_cfi')
process.QGTagger.srcJets = cms.InputTag( 'slimmedJets' )
process.QGTagger.jetsLabel = cms.string('QGL_AK4PFchs')
process.QGTagger.srcVertexCollection=cms.InputTag("offlinePrimaryVertices")

# compute corrected pruned jet mass
process.corrJets = cms.EDProducer ( "CorrJetsProducer",
                                    jets    = cms.InputTag( "slimmedJetsAK8JEC" ),
                                    vertex  = cms.InputTag( "offlineSlimmedPrimaryVertices" ), 
                                    rho     = cms.InputTag( "fixedGridRhoFastjetAll"   ),
                                    payload = cms.string  ( "AK8PFchs" ),
                                    isData  = cms.bool    (  True ))


# Recompute MET
from PhysicsTools.PatUtils.tools.runMETCorrectionsAndUncertainties import runMetCorAndUncFromMiniAOD

runMetCorAndUncFromMiniAOD(process,
            isData=True,
            )

from Hcc.HccAna.pfGlobalParticleTransformerAK8TagInfos_cfi import pfGlobalParticleTransformerAK8TagInfos
process.pfGlobalParticleTransformerAK8TagInfos = pfGlobalParticleTransformerAK8TagInfos.clone(
    min_jet_pt = 180.0,
    jet_radius = 0.8,
    max_jet_eta = 2.5,
    vertices = 'offlineSlimmedPrimaryVertices',
    secondary_vertices = 'slimmedSecondaryVertices',
    pf_candidates = 'packedPFCandidates',
    jets = 'updatedPatJetsUpdatedJECak8',
    lost_tracks = 'lostTracks',
    use_puppiP4 = False,
)

from RecoBTag.ONNXRuntime.boostedJetONNXJetTagsProducer_cfi import boostedJetONNXJetTagsProducer
process.pfGlobalParticleTransformerAK8JetTags = boostedJetONNXJetTagsProducer.clone(
    src = 'pfGlobalParticleTransformerAK8TagInfos',
    preprocess_json = 'Hcc/HccAna/data/GloParTV3/preprocess.json',
    model_path = 'Hcc/HccAna/data/GloParTV3/model.onnx',
    flav_names = [
        'probXbb', 'probXcc', 'probXcs', 'probXqq', 'probXtauhtaue', 'probXtauhtaum', 'probXtauhtauh', 'probXWW4q', 'probXWW3q', 'probXWWqqev', 'probXWWqqmv', 'probTopbWqq', 'probTopbWq', 'probTopbWev', 'probTopbWmv', 'probTopbWtauhv', 'probQCD', 'massCorrX2p', 'massCorrGeneric', 'probWithMassTopvsQCD', 'probWithMassWvsQCD', 'probWithMassZvsQCD'
    ] + ['hidNeuron' + str(i).zfill(3) for i in range(256)],
    debugMode = False,
)
pfGlobalParticleTransformerAK8JetTagsProbs = ['pfGlobalParticleTransformerAK8JetTags:' + flav_name for flav_name in process.pfGlobalParticleTransformerAK8JetTags.flav_names]

from PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cfi import updatedPatJets
process.slimmedJetsAK8WithGloParT = updatedPatJets.clone(
    jetSource = "updatedPatJetsUpdatedJECak8",
    addJetCorrFactors = False
)
process.slimmedJetsAK8WithGloParT.discriminatorSources += pfGlobalParticleTransformerAK8JetTagsProbs

process.Ana = cms.EDAnalyzer('HccAna',
                              photonSrc    = cms.untracked.InputTag("slimmedPhotons"),
                              electronSrc  = cms.untracked.InputTag("slimmedElectrons"),
                              #electronUnSSrc  = cms.untracked.InputTag("selectedElectrons"),
                              muonSrc      = cms.untracked.InputTag("slimmedMuons"),
                              #muonSrc      = cms.untracked.InputTag("boostedMuons"),
                              tauSrc      = cms.untracked.InputTag("slimmedTaus"),
                              jetSrc       = cms.untracked.InputTag("slimmedJets"),
                              #AK4PuppiJetSrc       = cms.InputTag("slimmedJetsPuppi"),
                              AK4PuppiJetSrc       = cms.InputTag("updatedPatJetsUpdatedJECak4"),
                              #AK8PuppiJetSrc       = cms.untracked.InputTag("slimmedJetsAK8"),
                              AK8PuppiJetSrc       = cms.untracked.InputTag("slimmedJetsAK8WithGloParT"),
                              #AK8PFPuppiSoftDropPackedSrc = cms.untracked.InputTag("slimmedJetsAK8PFPuppiSoftDropPacked:SubJets"),
                              AK8PFPuppiSoftDropPackedSrc       = cms.untracked.InputTag("updatedPatJetsUpdatedJECsubak4"),
                              hltAK4PFJetsCorrectedSrc  = cms.InputTag("hltAK4PFJetsCorrected", "", "HLT"),
                              bxvCaloJetSrc =  cms.InputTag("caloStage2Digis","Jet"),
                              bxvCaloMuonSrc =  cms.InputTag("gmtStage2Digis","Muon"),
                              bxvCaloHTSrc =  cms.InputTag("caloStage2Digis","EtSum"),
                              mergedjetSrc = cms.untracked.InputTag("slimmedJets"),
                              metSrc       = cms.untracked.InputTag("slimmedMETs","","HccAnalysis"),
                              vertexSrc    = cms.untracked.InputTag("offlineSlimmedPrimaryVertices"),
                              beamSpotSrc  = cms.untracked.InputTag("offlineBeamSpot"),
                              conversionSrc  = cms.untracked.InputTag("reducedEgamma","reducedConversions"),
                              isMC         = cms.untracked.bool(False),
                              isHcc         = cms.untracked.bool(False),
                              isZcc         = cms.untracked.bool(False),
                              isZbb         = cms.untracked.bool(False),
                              isZqq         = cms.untracked.bool(False),
                              ispreEE         = cms.untracked.bool(False),
                              isBCDE         = cms.untracked.bool(False),
                              isSignal     = cms.untracked.bool(False),
                              mH           = cms.untracked.double(125.0),
                              CrossSection = cms.untracked.double(1.0),
                              FilterEff    = cms.untracked.double(1),
                              weightEvents = cms.untracked.bool(False),
                              elRhoSrc     = cms.untracked.InputTag("fixedGridRhoFastjetAll"),
                              muRhoSrc     = cms.untracked.InputTag("fixedGridRhoFastjetAll"),
                              rhoSrcSUS    = cms.untracked.InputTag("fixedGridRhoFastjetCentralNeutral"),
                              pileupSrc     = cms.untracked.InputTag("slimmedAddPileupInfo"),
                              pfCandsSrc   = cms.untracked.InputTag("packedPFCandidates"),
                              #fsrPhotonsSrc = cms.untracked.InputTag("boostedFsrPhotons"),
                              prunedgenParticlesSrc = cms.untracked.InputTag("prunedGenParticles"),
                              packedgenParticlesSrc = cms.untracked.InputTag("packedGenParticles"),
                              genJetsSrc = cms.untracked.InputTag("slimmedGenJets"),
                              generatorSrc = cms.untracked.InputTag("generator"),
                              lheInfoSrc = cms.untracked.InputTag("externalLHEProducer"),
                              reweightForPU = cms.untracked.bool(False),
                              triggerSrc = cms.InputTag("TriggerResults","","HLT"),
                              triggerObjects = cms.InputTag("slimmedPatTrigger"),
                              doJER = cms.untracked.bool(True),
                              doJEC = cms.untracked.bool(True),
                              algInputTag = cms.InputTag("gtStage2Digis"),
                              doTriggerMatching = cms.untracked.bool(True),
                              triggerList = cms.untracked.vstring(
                                  # Control path VBFHToBB 
                                  'HLT_QuadPFJet103_88_75_15_v',
                                  'HLT_QuadPFJet105_88_76_15_v',
                                  'HLT_QuadPFJet111_90_80_15_v',
                                  'HLT PFJet80_v',
                                  # Single Jet VBFHToBB path:
                                  'HLT_QuadPFJet103_88_75_15_PFBTagDeepJet_1p3_VBF2_v',
                                  'HLT_QuadPFJet105_88_76_15_PFBTagDeepJet_1p3_VBF2_v',
                                  'HLT_QuadPFJet111_90_80_15_PFBTagDeepJet_1p3_VBF2_v',
                                  # DoubleJet VBFHToBB path
                                  'HLT_QuadPFJet103_88_75_15_DoublePFBTagDeepJet_1p3_7p7_VBF1_v',
                                  'HLT_QuadPFJet105_88_76_15_DoublePFBTagDeepJet_1p3_7p7_VBF1_v',
                                  'HLT_QuadPFJet111_90_80_15_DoublePFBTagDeepJet_1p3_7p7_VBF1_v',
                                  #AK8 for Zqq
                                  'PFHT1050_v',
                                  'PFJet500_v',
                                  'AK8PFJet500_v',
                                  'AK8PFJet400_TrimMass30_v',
                                  'AK8PFJet420_TrimMass30_v',
                                  'AK8PFHT800_TrimMass50_v',
                              ),
                              skimLooseLeptons = cms.untracked.int32(4),              
                              skimTightLeptons = cms.untracked.int32(4),              
                              doMela = cms.untracked.bool(False),
                              payload = cms.string("AK4PFPuppi"),
                              #verbose = cms.untracked.bool(True)              
                             )

process.p = cms.Path(process.egmGsfElectronIDSequence*
                     process.jecSequence_subak4*
                     process.jecSequence_ak4*
                     process.jecSequence_ak8*
                     process.pfGlobalParticleTransformerAK8TagInfos*
                     process.pfGlobalParticleTransformerAK8JetTags*
                     process.slimmedJetsAK8WithGloParT*
                     process.QGTagger*
                     process.Ana
                     )
