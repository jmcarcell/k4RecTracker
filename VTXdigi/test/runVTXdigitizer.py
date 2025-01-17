import os, math

from Gaudi.Configuration import *

from Configurables import FCCDataSvc
podioevent  = FCCDataSvc("EventDataSvc")

from GaudiKernel.SystemOfUnits import MeV, GeV, tesla
################## Particle gun setup
momentum = 5 # in GeV
thetaMin = 0
thetaMax = 180
pdgCode = 13 # 11 electron, 13 muon, 22 photon, 111 pi0, 211 pi+
magneticField = True
_pi = 3.14159

################## Vertex sensor resolutions
# IDEA
innerVertexResolution_x = 0.003 # [mm], assume 5 µm resolution for ARCADIA sensor
innerVertexResolution_y = 0.003 # [mm], assume 5 µm resolution for ARCADIA sensor
innerVertexResolution_t = 1000 # [ns]
outerVertexResolution_x = 0.050/math.sqrt(12) # [mm], assume ATLASPix3 sensor with 50 µm pitch
outerVertexResolution_y = 0.150/math.sqrt(12) # [mm], assume ATLASPix3 sensor with 150 µm pitch
outerVertexResolution_t = 1000 # [ns]

# CLD
vertexBarrelResolution_x = 0.003 # [mm], assume 5 µm resolution
vertexBarrelResolution_y = 0.003 # [mm], assume 5 µm resolution
vertexBarrelResolution_t = 1000 # [ns]
vertexEndcapResolution_x = 0.003 # [mm], assume 5 µm resolution
vertexEndcapResolution_y = 0.003 # [mm], assume 5 µm resolution
vertexEndcapResolution_t = 1000 # [ns]


siWrapperResolution_x = 0.050/math.sqrt(12) # [mm]
siWrapperResolution_y = 1.0/math.sqrt(12) # [mm]
siWrapperResolution_t = 0.040 # [ns], assume 40 ps timing resolution for a single layer -> Should lead to <30 ps resolution when >1 hit

from Configurables import GenAlg
genAlg = GenAlg()
from Configurables import  MomentumRangeParticleGun
pgun = MomentumRangeParticleGun("ParticleGun_Electron")
pgun.PdgCodes = [pdgCode]
pgun.MomentumMin = momentum * GeV
pgun.MomentumMax = momentum * GeV
pgun.PhiMin = 0
pgun.PhiMax = 2 * _pi
pgun.ThetaMin = thetaMin * _pi / 180.
pgun.ThetaMax = thetaMax * _pi / 180.
genAlg.SignalProvider = pgun

genAlg.hepmc.Path = "hepmc"

from Configurables import HepMCToEDMConverter
hepmc_converter = HepMCToEDMConverter()
hepmc_converter.hepmc.Path="hepmc"
genParticlesOutputName = "genParticles"
hepmc_converter.GenParticles.Path = genParticlesOutputName
hepmc_converter.hepmcStatusList = []

################## Simulation setup
# Detector geometry
from Configurables import GeoSvc
geoservice = GeoSvc("GeoSvc")
# if FCC_DETECTORS is empty, this should use relative path to working directory
path_to_detector = os.environ.get("K4GEO", "") # Previously used "FCCDETECTORS"
print(path_to_detector)
detectors_to_use=[
                   'FCCee/IDEA/compact/IDEA_o1_v02/IDEA_o1_v02.xml',
                    # 'FCCee/CLD/compact/CLD_o2_v05/CLD_o2_v05.xml',
                  ]
# prefix all xmls with path_to_detector
geoservice.detectors = [os.path.join(path_to_detector, _det) for _det in detectors_to_use]
geoservice.OutputLevel = INFO

# geoservice.detectors = ["../lcgeo/FCCee/IDEA/compact/IDEA_o1_v02/IDEA_o1_v02.xml"] # Force to use my local version

# Geant4 service
# Configures the Geant simulation: geometry, physics list and user actions

from Configurables import SimG4FullSimActions, SimG4Alg, SimG4PrimariesFromEdmTool, SimG4SaveParticleHistory
actions = SimG4FullSimActions()
# Uncomment if history from Geant4 decays is needed (e.g. to get the photons from pi0) and set actions=actions in SimG4Svc + uncomment saveHistTool in SimG4Alg
#actions.enableHistory=True
#actions.energyCut = 0.2 * GeV
#saveHistTool = SimG4SaveParticleHistory("saveHistory")


# Magnetic field
from Configurables import SimG4ConstantMagneticFieldTool
field = SimG4ConstantMagneticFieldTool("SimG4ConstantMagneticFieldTool", FieldComponentZ = -2 * tesla, FieldOn = magneticField, IntegratorStepper = "ClassicalRK4")

from Configurables import SimG4Svc
geantservice = SimG4Svc("SimG4Svc", detector = 'SimG4DD4hepDetector', physicslist = "SimG4FtfpBert", magneticField = field) # , actions = actions)

# Fixed seed to have reproducible results, change it for each job if you split one production into several jobs
# Mind that if you leave Gaudi handle random seed and some job start within the same second (very likely) you will have duplicates
geantservice.randomNumbersFromGaudi = False
geantservice.seedValue = 4242

# Range cut
geantservice.g4PreInitCommands += ["/run/setCut 0.1 mm"]

# Geant4 algorithm
# Translates EDM to G4Event, passes the event to G4, writes out outputs via tools
# and a tool that saves the calorimeter hits

# next, create the G4 algorithm, giving the list of names of tools ("XX/YY")
from Configurables import SimG4PrimariesFromEdmTool
particle_converter = SimG4PrimariesFromEdmTool("EdmConverter")
particle_converter.GenParticles.Path = genParticlesOutputName

from Configurables import SimG4SaveTrackerHits

### CLD
SimG4SaveTrackerHitsB = SimG4SaveTrackerHits("SimG4SaveTrackerHitsB", readoutName="VertexBarrelCollection")
SimG4SaveTrackerHitsB.SimTrackHits.Path = "VTXB_simTrackerHits"

SimG4SaveTrackerHitsE = SimG4SaveTrackerHits("SimG4SaveTrackerHitsE", readoutName="VertexEndcapCollection")
SimG4SaveTrackerHitsE.SimTrackHits.Path = "VTXE_simTrackerHits"


### IDEA
SimG4SaveTrackerHitsIB = SimG4SaveTrackerHits("SimG4SaveTrackerHitsIB", readoutName="VTXIBCollection")
SimG4SaveTrackerHitsIB.SimTrackHits.Path = "VTXIB_simTrackerHits"

SimG4SaveTrackerHitsOB = SimG4SaveTrackerHits("SimG4SaveTrackerHitsOB", readoutName="VTXOBCollection")
SimG4SaveTrackerHitsOB.SimTrackHits.Path = "VTXOB_simTrackerHits"

SimG4SaveTrackerHitsD = SimG4SaveTrackerHits("SimG4SaveTrackerHitsD", readoutName="VTXDCollection")
SimG4SaveTrackerHitsD.SimTrackHits.Path = "VTXD_simTrackerHits"

SimG4SaveTrackerHitsSiWrB = SimG4SaveTrackerHits("SimG4SaveTrackerHitsSiWrB", readoutName="SiWrBCollection")
SimG4SaveTrackerHitsSiWrB.SimTrackHits.Path = "SiWrB_simTrackerHits"

SimG4SaveTrackerHitsSiWrD = SimG4SaveTrackerHits("SimG4SaveTrackerHitsSiWrD", readoutName="SiWrDCollection")
SimG4SaveTrackerHitsSiWrD.SimTrackHits.Path = "SiWrD_simTrackerHits"

from Configurables import SimG4Alg

# CLD
# geantsim = SimG4Alg("SimG4Alg",
#                        outputs= [SimG4SaveTrackerHitsB, SimG4SaveTrackerHitsE,
#                                  #saveHistTool
#                        ],
#                        eventProvider=particle_converter,
#                        OutputLevel=INFO)

# IDEA
geantsim = SimG4Alg("SimG4Alg",
                       outputs= [SimG4SaveTrackerHitsIB, SimG4SaveTrackerHitsOB, SimG4SaveTrackerHitsD,
                                 SimG4SaveTrackerHitsSiWrB, SimG4SaveTrackerHitsSiWrD,
                                 #saveHistTool
                       ],
                       eventProvider=particle_converter,
                       OutputLevel=INFO)

# Digitize tracker hits
from Configurables import VTXdigitizer

### For CLD. Not working yet, SimG4 doesn't produce hits in CLD vertex yet
vtxb_digitizer = VTXdigitizer("VTXBdigitizer",
    inputSimHits = SimG4SaveTrackerHitsB.SimTrackHits.Path,
    outputDigiHits = SimG4SaveTrackerHitsB.SimTrackHits.Path.replace("sim", "digi"),
    detectorName = "Vertex",
    readoutName = "VertexBarrelCollection",
    xResolution = vertexBarrelResolution_x, 
    yResolution = vertexBarrelResolution_y,
    tResolution = vertexBarrelResolution_t,
    forceHitsOntoSurface = False,
    OutputLevel = INFO
)

vtxe_digitizer = VTXdigitizer("VTXEdigitizer",
    inputSimHits = SimG4SaveTrackerHitsE.SimTrackHits.Path,
    outputDigiHits = SimG4SaveTrackerHitsE.SimTrackHits.Path.replace("sim", "digi"),
    detectorName = "Vertex",
    readoutName = "VertexEndcapCollection",
    xResolution = vertexEndcapResolution_x,
    yResolution = vertexEndcapResolution_y,
    tResolution = vertexEndcapResolution_t,
    forceHitsOntoSurface = False,
    OutputLevel = INFO
)


### For IDEA
vtxib_digitizer = VTXdigitizer("VTXIBdigitizer",
    inputSimHits = SimG4SaveTrackerHitsIB.SimTrackHits.Path,
    outputDigiHits = SimG4SaveTrackerHitsIB.SimTrackHits.Path.replace("sim", "digi"),
    detectorName = "Vertex",
    readoutName = "VTXIBCollection",
    xResolution = innerVertexResolution_x, # mm, r-phi direction
    yResolution = innerVertexResolution_y, # mm, z direction
    tResolution = innerVertexResolution_t,
    forceHitsOntoSurface = False,
    OutputLevel = INFO
)

vtxob_digitizer = VTXdigitizer("VTXOBdigitizer",
    inputSimHits = SimG4SaveTrackerHitsOB.SimTrackHits.Path,
    outputDigiHits = SimG4SaveTrackerHitsOB.SimTrackHits.Path.replace("sim", "digi"),
    detectorName = "Vertex",
    readoutName = "VTXOBCollection",
    xResolution = outerVertexResolution_x, # mm, r-phi direction
    yResolution = outerVertexResolution_y, # mm, z direction
    tResolution = outerVertexResolution_t, # ns
    forceHitsOntoSurface = False,
    OutputLevel = INFO
)

vtxd_digitizer  = VTXdigitizer("VTXDdigitizer",
    inputSimHits = SimG4SaveTrackerHitsD.SimTrackHits.Path,
    outputDigiHits = SimG4SaveTrackerHitsD.SimTrackHits.Path.replace("sim", "digi"),
    detectorName = "Vertex",
    readoutName = "VTXDCollection",
    xResolution = outerVertexResolution_x, # mm, r direction
    yResolution = outerVertexResolution_y, # mm, phi direction
    tResolution = outerVertexResolution_t, # ns
    forceHitsOntoSurface = False,
    OutputLevel = INFO
)

siwrb_digitizer = VTXdigitizer("SiWrBdigitizer",
    inputSimHits = SimG4SaveTrackerHitsSiWrB.SimTrackHits.Path,
    outputDigiHits = SimG4SaveTrackerHitsSiWrB.SimTrackHits.Path.replace("sim", "digi"),
    detectorName = "SiliconWrapper",
    readoutName = "SiWrBCollection",
    xResolution = siWrapperResolution_x, # mm, r direction
    yResolution = siWrapperResolution_y, # mm, phi direction
    tResolution = siWrapperResolution_t, # ns
    forceHitsOntoSurface = False,
    OutputLevel = INFO
)

siwrd_digitizer = VTXdigitizer("SiWrDdigitizer",
    inputSimHits = SimG4SaveTrackerHitsSiWrD.SimTrackHits.Path,
    outputDigiHits = SimG4SaveTrackerHitsSiWrD.SimTrackHits.Path.replace("sim", "digi"),
    detectorName = "SiliconWrapper",
    readoutName = "SiWrDCollection",
    xResolution = siWrapperResolution_x, # mm, r direction
    yResolution = siWrapperResolution_y, # mm, phi direction
    tResolution = siWrapperResolution_t, # ns
    forceHitsOntoSurface = False,
    OutputLevel = INFO
)

# run the genfit tracking 
# from Configurables import GenFitter
# genfitter = GenFitter("GenFitter", inputHits = savetrackertool.SimTrackHits.Path.replace("sim", "digi"), outputTracks = "genfit_tracks") 

################ Output
from Configurables import PodioOutput
out = PodioOutput("out",
                  OutputLevel=INFO)
out.outputCommands = ["keep *"]

import uuid
out.filename = "output_vertex_"+str(magneticField)+"_pMin_"+str(momentum*1000)+"_MeV"+"_ThetaMinMax_"+str(thetaMin)+"_"+str(thetaMax)+"_pdgId_"+str(pdgCode)+".root"

#CPU information
from Configurables import AuditorSvc, ChronoAuditor
chra = ChronoAuditor()
audsvc = AuditorSvc()
audsvc.Auditors = [chra]
genAlg.AuditExecute = True
hepmc_converter.AuditExecute = True
geantsim.AuditExecute = True
out.AuditExecute = True

from Configurables import EventCounter
event_counter = EventCounter('event_counter')
event_counter.Frequency = 1

from Configurables import ApplicationMgr

# # CLD
# ApplicationMgr(
#     TopAlg = [
#               event_counter,
#               genAlg,
#               hepmc_converter,
#               geantsim,
#               vtxb_digitizer,vtxe_digitizer,
#               out
#               ],
#     EvtSel = 'NONE',
#     EvtMax   = 1000,
#     ExtSvc = [geoservice, podioevent, geantservice, audsvc],
#     StopOnSignal = True
#  )

# IDEA
ApplicationMgr(
    TopAlg = [
              event_counter,
              genAlg,
              hepmc_converter,
              geantsim,
              vtxib_digitizer, vtxob_digitizer, vtxd_digitizer,
              siwrb_digitizer, siwrd_digitizer,
              out
              ],
    EvtSel = 'NONE',
    EvtMax   = 100000,
    ExtSvc = [geoservice, podioevent, geantservice, audsvc],
    StopOnSignal = True
 )
