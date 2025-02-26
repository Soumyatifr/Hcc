import FWCore.ParameterSet.Config as cms

from FWCore.ParameterSet.VarParsing import VarParsing

process = cms.Process("HccAnalysis")

process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 1000
#process.MessageLogger.categories.append('HccAna')

process.load("Configuration.StandardSequences.MagneticField_cff")
process.load("Configuration.Geometry.GeometryRecoDB_cff")
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
process.load('Configuration.StandardSequences.Services_cff')
process.GlobalTag.globaltag='130X_mcRun3_2022_realistic_postEE_v6' #MC2022v4

#from Configuration.AlCa.GlobalTag import GlobalTag
#process.GlobalTag = GlobalTag(process.GlobalTag, '130X_mcRun3_2022_realistic_v5','')

process.Timing = cms.Service("Timing",
                             summaryOnly = cms.untracked.bool(True)
                             )


process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(-1) )

process.options = cms.untracked.PSet(
        numberOfThreads = cms.untracked.uint32(1),
				#SkipEvent = cms.untracked.vstring('ProductNotFound')
)

process.options.numberOfConcurrentLuminosityBlocks = 1

myfilelist = cms.untracked.vstring(
'/store/mc/Run3Summer22EEMiniAODv4/Zto2Q-4Jets_HT-800_TuneCP5_13p6TeV_madgraphMLM-pythia8/MINIAODSIM/130X_mcRun3_2022_realistic_postEE_v6-v2/2520000/ffe3d2f1-36cd-4158-94bd-3440ba2e9739.root',
)

process.source = cms.Source("PoolSource",fileNames = myfilelist,
           #                 duplicateCheckMode = cms.untracked.string('noDuplicateCheck'),
           #eventsToProcess = cms.untracked.VEventRange('1:12:66017')
                            )

process.TFileService = cms.Service("TFileService",
                                   #fileName = cms.string("prova.root")
                                   fileName = cms.string("output.root")
)

# clean muons by segments 
process.boostedMuons = cms.EDProducer("PATMuonCleanerBySegments",
				     src = cms.InputTag("slimmedMuons"),
				     preselection = cms.string("track.isNonnull"),
				     passthrough = cms.string("isGlobalMuon && numberOfMatches >= 2"),
				     fractionOfSharedSegments = cms.double(0.499),
				     )


# Kalman Muon Calibrations
process.calibratedMuons = cms.EDProducer("KalmanMuonCalibrationsProducer",
                                         muonsCollection = cms.InputTag("boostedMuons"),
                                         isMC = cms.bool(True),
                                         isSync = cms.bool(True),
                                         useRochester = cms.untracked.bool(True),
                                         year = cms.untracked.int32(2018)
                                         )



process.selectedElectrons = cms.EDFilter("PATElectronSelector",
                                         src = cms.InputTag("slimmedElectrons"),
                                         #cut = cms.string("pt > 5 && abs(eta)<2.5 && abs(-log(tan(superClusterPosition.theta/2)))<2.5")
                                         cut = cms.string("pt > 5 && abs(eta)<2.5 ")
                                         )

process.RandomNumberGeneratorService = cms.Service("RandomNumberGeneratorService",
    calibratedPatElectrons = cms.PSet(
        #initialSeed = cms.untracked.uint32(SEED), # for HPC
        initialSeed = cms.untracked.uint32(123456), # for crab
        engineName = cms.untracked.string('TRandom3')
    )
)

# FSR Photons
process.load('Hcc.FSRPhotons.fsrPhotons_cff')

import os
# Jet Energy Corrections
#from CondCore.CondDB.CondDB_cfi  import *
from CondCore.DBCommon.CondDBSetup_cfi import *


# AK4 Puppi Jets JEC
process.jec_ak4 = cms.ESSource("PoolDBESSource",
                           CondDBSetup,
                           #for hpc
                           #connect = cms.string("sqlite_file:" +os.environ.get('CMSSW_BASE')+"/src/Hcc/HccAna/data/Summer22EE_22Sep2023_V2_MC.db"),
                           #for crab
                           connect = cms.string("sqlite_file:Summer22EE_22Sep2023_V2_MC.db"),
                           toGet =  cms.VPSet(
                              cms.PSet(
                                 record = cms.string("JetCorrectionsRecord"),
                                 tag = cms.string("JetCorrectorParametersCollection_Summer22EE_22Sep2023_V2_MC_AK4PFPuppi"),
                                 label= cms.untracked.string("AK4PFPuppi")
                              ),
              )
)

# AK8 Puppi Jets JEC
process.jec_ak8 = cms.ESSource("PoolDBESSource",
                               CondDBSetup,
                               #for hpc
                               #connect = cms.string("sqlite_file:" +os.environ.get('CMSSW_BASE')+"/src/Hcc/HccAna/data/Summer22EE_22Sep2023_V2_MC.db"),
                               #for crab
                               connect = cms.string("sqlite_file:Summer22EE_22Sep2023_V2_MC.db"),
                               toGet =  cms.VPSet(
                                  cms.PSet(
                                     record = cms.string("JetCorrectionsRecord"),
                                     tag = cms.string("JetCorrectorParametersCollection_Summer22EE_22Sep2023_V2_MC_AK8PFPuppi"),
                                     label= cms.untracked.string("AK8PFPuppi")
                                  ),
                  )
)

process.es_prefer_jec_ak4 = cms.ESPrefer('PoolDBESSource', 'jec_ak4')
process.es_prefer_jec_ak8 = cms.ESPrefer('PoolDBESSource', 'jec_ak8')

from PhysicsTools.PatAlgos.tools.jetTools import updateJetCollection

deep_discriminators = [
        "pfParticleNetMassRegressionJetTags:mass"
]
from RecoBTag.ONNXRuntime.pfParticleNet_cff import _pfParticleNetJetTagsAll as pfParticleNetJetTagsAll
from RecoBTag.ONNXRuntime.pfParticleNet_cff import _pfParticleNetMassRegressionOutputs as pfParticleNetMassRegressionOutputs 
deep_discriminators += pfParticleNetMassRegressionOutputs

updateJetCollection(
   process,
   jetSource = cms.InputTag('slimmedJetsAK8'),
   labelName = 'UpdatedJECak8',
   btagDiscriminators = deep_discriminators,
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

# the corrected jet collection is "updatedPatJetsUpdatedJECsubak4"
process.jecSequence_subak4 = cms.Sequence(process.patJetCorrFactorsUpdatedJECsubak4 * process.updatedPatJetsUpdatedJECsubak4)

process.load("PhysicsTools.PatAlgos.producersLayer1.jetUpdater_cff")
### add pileup id and discriminant to patJetsReapplyJEC
from RecoJets.JetProducers.PileupJetID_cfi import _chsalgos_106X_UL18
process.load("RecoJets.JetProducers.PileupJetID_cfi")
process.pileupJetIdUpdated = process.pileupJetId.clone(
    jets=cms.InputTag("slimmedJets"),
    inputIsCorrected=False,
    applyJec=True,
    vertexes=cms.InputTag("offlineSlimmedPrimaryVertices"),
    algos=cms.VPSet(_chsalgos_106X_UL18),

)

#QGTag
process.load("CondCore.CondDB.CondDB_cfi")
process.QGPoolDBESSource = cms.ESSource("PoolDBESSource",
      DBParameters = cms.PSet(messageLevel = cms.untracked.int32(1)),
      timetype = cms.string('runnumber'),
      toGet = cms.VPSet(
        cms.PSet(
            record = cms.string('QGLikelihoodRcd'),
            tag    = cms.string('QGLikelihoodObject_cmssw8020_v2_AK4PFchs'),
            label  = cms.untracked.string('QGL_AK4PFPuppi')
        ),
      ),
      connect = cms.string('sqlite_file:QGL_cmssw8020_v2.db')
)

process.es_prefer_qg = cms.ESPrefer('PoolDBESSource','QGPoolDBESSource')
process.load('RecoJets.JetProducers.QGTagger_cfi')
#process.QGTagger.srcJets = cms.InputTag( 'slimmedJetsJEC' )
process.QGTagger.srcJets = cms.InputTag( 'slimmedJets' )
process.QGTagger.jetsLabel = cms.string('QGL_AK4PFPuppi')
process.QGTagger.srcVertexCollection=cms.InputTag("offlinePrimaryVertices")

# Recompute MET
from PhysicsTools.PatUtils.tools.runMETCorrectionsAndUncertainties import runMetCorAndUncFromMiniAOD

runMetCorAndUncFromMiniAOD(process,
            isData=False,
            )

# STXS
process.load("SimGeneral.HepPDTESSource.pythiapdt_cfi")
process.mergedGenParticles = cms.EDProducer("MergedGenParticleProducer",
    inputPruned = cms.InputTag("prunedGenParticles"),
    inputPacked = cms.InputTag("packedGenParticles"),
)
process.myGenerator = cms.EDProducer("GenParticles2HepMCConverter",
    genParticles = cms.InputTag("mergedGenParticles"),
    genEventInfo = cms.InputTag("generator"),
    signalParticlePdgIds = cms.vint32(25)
)
process.rivetProducerHTXS = cms.EDProducer('HTXSRivetProducer',
  HepMCCollection = cms.InputTag('myGenerator','unsmeared'),
  LHERunInfo = cms.InputTag('externalLHEProducer'),
  ProductionMode = cms.string('AUTO'),
)
# HZZ Fiducial from RIVET
process.rivetProducerHZZFid = cms.EDProducer('HZZRivetProducer',
  HepMCCollection = cms.InputTag('myGenerator','unsmeared'),
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

# Analyzer
process.Ana = cms.EDAnalyzer('HccAna',
                              photonSrc    = cms.untracked.InputTag("slimmedPhotons"),
                              electronSrc  = cms.untracked.InputTag("slimmedElectrons"),
                              electronUnSSrc  = cms.untracked.InputTag("selectedElectrons"),
                              muonSrc      = cms.untracked.InputTag("slimmedMuons"),
                              tauSrc      = cms.untracked.InputTag("slimmedTaus"),
                              jetSrc       = cms.untracked.InputTag("slimmedJets"),
                              AK4PuppiJetSrc       = cms.InputTag("updatedPatJetsUpdatedJECak4"),
                              AK8PuppiJetSrc       = cms.untracked.InputTag("slimmedJetsAK8WithGloParT"),
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
                              isMC         = cms.untracked.bool(True),
                              isHcc         = cms.untracked.bool(False),
                              isZqq         = cms.untracked.bool(True),
                              ispreEE         = cms.untracked.bool(False),
                              isBCDE         = cms.untracked.bool(False),
                              isZcc         = cms.untracked.bool(False),
                              isZbb         = cms.untracked.bool(False),
                              isSignal     = cms.untracked.bool(True),
                              mH           = cms.untracked.double(125.0),
                              CrossSection = cms.untracked.double(1),#DUMMYCROSSSECTION),
                              FilterEff    = cms.untracked.double(1),
                              weightEvents = cms.untracked.bool(True),
                              elRhoSrc     = cms.untracked.InputTag("fixedGridRhoFastjetAll"),
                              muRhoSrc     = cms.untracked.InputTag("fixedGridRhoFastjetAll"),
                              rhoSrcSUS    = cms.untracked.InputTag("fixedGridRhoFastjetCentralNeutral"),
                              pileupSrc     = cms.untracked.InputTag("slimmedAddPileupInfo"),
                              pfCandsSrc   = cms.untracked.InputTag("packedPFCandidates"),
                              fsrPhotonsSrc = cms.untracked.InputTag("boostedFsrPhotons"),
                              prunedgenParticlesSrc = cms.untracked.InputTag("prunedGenParticles"),
                              packedgenParticlesSrc = cms.untracked.InputTag("packedGenParticles"),
                              genJetsSrc = cms.untracked.InputTag("slimmedGenJets"),
                              generatorSrc = cms.untracked.InputTag("generator"),
                              lheInfoSrc = cms.untracked.InputTag("externalLHEProducer"),
                              reweightForPU = cms.untracked.bool(True),
                              triggerSrc = cms.InputTag("TriggerResults","","HLT"),
                              triggerObjects = cms.InputTag("selectedPatTrigger"),
                              doJER = cms.untracked.bool(True),
                              doJEC = cms.untracked.bool(True),
                              algInputTag = cms.InputTag("gtStage2Digis"),
                              doTriggerMatching = cms.untracked.bool(False),
                              triggerList = cms.untracked.vstring(
				                #VBFHToCC
				                'HLT_QuadPFJet70_50_45_35_PFBTagParticleNet_2BTagSum0p65_v',
				                'HLT_PFJet500_v',
                              ),
                              verbose = cms.untracked.bool(False),              
                              skimLooseLeptons = cms.untracked.int32(0),              
                              skimTightLeptons = cms.untracked.int32(0),              
                              #bestCandMela = cms.untracked.bool(False),
                              year = cms.untracked.int32(2018),####for year put 2016,2017, or 2018 to select correct setting
                              isCode4l = cms.untracked.bool(True),
                              payload = cms.string("AK4PFPuppi"),
                              #for hpc
                              #uncertainty_source_path_src = cms.untracked.string(os.environ.get('CMSSW_BASE')+"/src/Hcc/HccAna/data/Summer22EE_22Sep2023_V2_MC_UncertaintySources_AK4PFPuppi.txt"),
                              #for crab
                              uncertainty_source_path_src = cms.untracked.string("Summer22EE_22Sep2023_V2_MC_UncertaintySources_AK4PFPuppi.txt"),
                             )


process.p = cms.Path(process.jecSequence_subak4*
                     process.jecSequence_ak4*
                     process.jecSequence_ak8*
                     process.pfGlobalParticleTransformerAK8TagInfos*
                     process.pfGlobalParticleTransformerAK8JetTags*
                     process.slimmedJetsAK8WithGloParT*
                     process.pileupJetIdUpdated*
                     process.QGTagger*
                     process.mergedGenParticles*process.myGenerator*process.rivetProducerHTXS*#process.rivetProducerHZZFid*
                     process.Ana
                     )

