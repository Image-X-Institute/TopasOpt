# Set threading self:
------------------------------------------------------------
i:Ts/NumberOfThreads = 0  # defaults to 1
i:Ts/ShowHistoryCountAtInterval = 1000000
b:Ts/ShowHistoryCountOnSingleLine = "True"

# Add World:
------------------------------------------------------------
s:Ge/World/Type = "TsBox"
s:Ge/World/Material = "Air"
d:Ge/World/HLX = 250 mm # Half Length
d:Ge/World/HLY = 250 mm
d:Ge/World/HLZ = 1200.0 mm
d:Ge/World/RotX = 0. deg
d:Ge/World/RotY = 0. deg
d:Ge/World/RotZ = 0. deg

d:Ge/SID = 1000 mm
d:Ge/SecondaryCollimatorOffset = 20 mm

# Ta scattering foil
------------------------------------------------------------
s:Ge/TaFoil/Type               = "TsCylinder"
s:Ge/TaFoil/Parent             = "World"
s:Ge/TaFoil/Material           = "G4_Ta"
d:Ge/TaFoil/TransX             = 0 cm
d:Ge/TaFoil/TransY             = 0 cm
d:Ge/TaFoil/TransZ             = Ge/SID mm
d:Ge/TaFoil/RotX               = 0 deg
#d:Ge/TaFoil/RotY               = 0 deg
d:Ge/TaFoil/RotZ               = 0 deg
d:Ge/TaFoil/RMax               = 10 mm
d:Ge/TaFoil/HL                 = 0.1 mm
s:Ge/TaFoil/Color              = "lightblue"

# Al scattering foil
------------------------------------------------------------
s:Ge/AlFoil/Type               = "TsCylinder"
s:Ge/AlFoil/Parent             = "World"
s:Ge/AlFoil/Material           = "G4_Al"
d:Ge/AlFoil/TransX             = 0 cm
d:Ge/AlFoil/TransY             = 0 cm
d:Ge/AlFoil/foil_offset        = 24.9 mm
d:Ge/AlFoil/TransZ             = Ge/TaFoil/TransZ - Ge/AlFoil/foil_offset mm
d:Ge/AlFoil/RotX               = 0 deg
d:Ge/AlFoil/RotY               = 0 deg
d:Ge/AlFoil/RotZ               = 0 deg
d:Ge/AlFoil/RMax               = 10 mm
d:Ge/AlFoil/HL                 = 1. mm
s:Ge/AlFoil/Color              = "red"

# Add phase space scorer below foils:
------------------------------------------------------------
#s:Ge/Magic/Type     = "TsBox"
#s:Ge/Magic/Parent   = "World"
#s:Ge/Magic/Material = "Vacuum"
#d:Ge/Magic/HLX      = 100 mm
#d:Ge/Magic/HLY      = 100 mm
#d:Ge/Magic/HLZ      = 1 mm
#d:Ge/Magic/TransX   = 0. cm
#d:Ge/Magic/TransY   = 0. cm
#d:Ge/Magic/TransZ   = Ge/AlFoil/TransZ - 3 mm
#d:Ge/Magic/RotX     = 0. deg
#d:Ge/Magic/RotY     = 0. deg
#d:Ge/Magic/RotZ     = 0. deg
#s:Ge/Magic/Color    = "skyblue"
#s:Ge/Magic/DrawingStyle = "wireframe"


# s:Sc/PhaseSpaceFromColl/Quantity                    = "PhaseSpace"
# b:Sc/PhaseSpaceFromColl/OutputToConsole             = "False"
# s:Sc/PhaseSpaceFromColl/Surface                     = "Magic/ZMinusSurface"
# s:Sc/PhaseSpaceFromColl/OutputType                  = "Binary" # ASCII, Binary, Limited or ROOT
# s:Sc/PhaseSpaceFromColl/OutputFile                  = "Results/scattered_phase_space"
# i:Sc/PhaseSpaceFromColl/OutputBufferSize            = 1000
# #s:Sc/PhaseSpaceFromColl/OnlyIncludeParticlesGoing  = "In"
# b:Sc/PhaseSpaceFromColl/IncludeTOPASTime            = "False"
# b:Sc/PhaseSpaceFromColl/IncludeTimeOfFlight         = "False"
# b:Sc/PhaseSpaceFromColl/IncludeRunID                = "False"
# b:Sc/PhaseSpaceFromColl/IncludeEventID              = "False"
# b:Sc/PhaseSpaceFromColl/IncludeTrackID              = "False"
# b:Sc/PhaseSpaceFromColl/IncludeParentID             = "False"
# b:Sc/PhaseSpaceFromColl/IncludeCreatorProcess       = "False"
# b:Sc/PhaseSpaceFromColl/IncludeVertexInfo           = "False"
# b:Sc/PhaseSpaceFromColl/IncludeSeed                 = "False"


# # Beam parameters (parameterised source):
------------------------------------------------------------
s:So/Beam/Type                     = "Beam"
sc:So/Beam/Component                = "ElectronSource"
sc:So/Beam/BeamParticle             = "e-"
dc:So/Beam/BeamEnergy               = 15.0 MeV
uc:So/Beam/BeamEnergySpread         = 10
sc:So/Beam/BeamPositionDistribution = "Gaussian" # None, Flat or Gaussian
sc:So/Beam/BeamAngularDistribution  = "Gaussian" # None, Flat or Gaussian
sc:So/Beam/BeamPositionCutoffShape = "Ellipse"
dc:So/Beam/BeamPositionCutoffX = 2 mm
dc:So/Beam/BeamPositionCutoffY = 1 mm
dc:So/Beam/BeamPositionSpreadX = 0.3 mm
dc:So/Beam/BeamPositionSpreadY = 0.6 mm
dc:So/Beam/BeamAngularCutoffX = 5 deg
dc:So/Beam/BeamAngularCutoffY = 2 deg
dc:So/Beam/BeamAngularSpreadX = 1 deg
dc:So/Beam/BeamAngularSpreadY = 0.07 deg
ic:So/Beam/NumberOfHistoriesInRun = 4000000
#ic:So/Beam/NumberOfHistoriesInRun = 5000000

# # Electron source position
# ------------------------------------------------------------
s:Ge/ElectronSource/Parent = "World"
s:Ge/ElectronSource/Type="TsSPhere"
d:Ge/ElectronSource/Rmax = 5 mm
d:Ge/ElectronSource/TransZ = 1100 mm
d:Ge/ElectronSource/RotX = 180. deg
s:Ge/ElectronSource/Material = Ge/World/Material
s:Ge/ElectronSource/Color = "yellow"
sc:Ge/ElectronSource/DrawingStyle = "Solid"



# Add the phantom
------------------------------------------------------------
# Phantom
s:Ge/Phantom/Type = "TsBox"
s:Ge/Phantom/Parent = "World"
sc:Ge/Phantom/Material = "G4_WATER"
# We draw the phantom to be field size plus one beamlet
dc:Ge/Phantom/HLX = 75 mm
dc:Ge/Phantom/HLY = 75 mm
dc:Ge/Phantom/HLZ =  75 mm
dc:Ge/Phantom/TransX = 0. cm
dc:Ge/Phantom/TransY = 0. cm
dc:Ge/Phantom/TransZ = 70. cm
dc:Ge/Phantom/RotX = 0. deg
dc:Ge/Phantom/RotY = 0. deg
dc:Ge/Phantom/RotZ = 0. deg
ic:Ge/Phantom/XBins = 30
ic:Ge/Phantom/YBins = 30
ic:Ge/Phantom/ZBins = 30
sc:Ge/Phantom/Color    = "green"
sc:Ge/Phantom/DrawingStyle = "Solid"

# Add Volume scorer to phantom:
------------------------------------------------------------
s:Sc/PhantomScorer/Component = "Phantom"
s:Sc/PhantomScorer/Material = "Water"
s:Sc/PhantomScorer/Quantity                  = "DoseToMedium"
b:Sc/PhantomScorer/OutputToConsole           = "FALSE"
s:Sc/PhantomScorer/IfOutputFileAlreadyExists = "Overwrite"
s:Sc/PhantomScorer/OutputType = "Binary" # "csv", "binary", "Root", "Xml" or "DICOM"
s:Sc/PhantomScorer/OutputFile                  = "WaterTank_fixed_VRT_range_cut"


# Graphics View and trajectory filters:
------------------------------------------------------------
b:Gr/Enable = "False"  # Enable/Disable graphics
s:Gr/ViewA/Type              = "OpenGL"
d:Gr/ViewA/Theta            = 90 deg
d:Gr/ViewA/Phi              = 0 deg
u:Gr/ViewA/TransX           = 0
u:Gr/ViewA/TransY           = 0.
s:Gr/ViewA/Projection       = "Orthogonal"
d:Gr/ViewA/PerspectiveAngle = 60 deg
u:Gr/ViewA/Zoom             = 1
b:Gr/ViewA/IncludeStepPoints = "False"
b:Gr/ViewA/HiddenLineRemovalForTrajectories = "True"

# Physics
------------------------------------------------------------
sv:Ph/Default/Modules = 1 "g4em-standard_opt0"
#d:Ph/Default/EMRangeMin = 10000. eV # minimum for EM tables
#d:Ph/Default/CutForElectron = 10 mm # overrides CutForAllParticles for Electron
b:Ph/ListProcesses = "False"
s:Ge/Phantom/AssignToRegionNamed = "Phantom"
d:Ph/Default/ForRegion/Phantom/CutForElectron = 2.5 mm

# Variance reduction
------------------------------------------------------------
s:Ge/VrtParallelWorld/Parent = "World"
s:Ge/VrtParallelWorld/Type = "TsBox"
b:Ge/VrtParallelWorld/IsParallel = "True"
d:Ge/VrtParallelWorld/HLX = Ge/World/HLX cm
d:Ge/VrtParallelWorld/HLY = Ge/World/HLY cm
d:Ge/VrtParallelWorld/HLZ = Ge/World/HLZ cm

b:Vr/UseVarianceReduction = "True"

s:Ge/impCell1/Parent = "VrtParallelWorld"
s:Ge/impCell1/Type = "TsBox"
b:Ge/impCell1/IsParallel = "True"
d:Ge/impCell1/HLX = Ge/Phantom/HLX cm
d:Ge/impCell1/HLY = Ge/Phantom/HLY cm
d:Ge/impCell1/HLZ = Ge/Phantom/HLZ cm
d:Ge/impCell1/TransZ = Ge/Phantom/TransZ cm

# Importance sampling
b:Vr/ImportanceSampling/Active         = "true"
sv:Vr/ImportanceSampling/ParticleName  = 2 "gamma" "e-"
s:Vr/ImportanceSampling/Component      = "VrtParallelWorld"
sv:Vr/ImportanceSampling/SubComponents = 1 "impCell1"
s:Vr/ImportanceSampling/Type = "ImportanceSampling"
uvc:Vr/ImportanceSampling/ImportanceValues = 1 10

------------------------------------------------------------
# QT
# --
Ts/UseQt = Gr/Enable
Ts/PauseBeforeQuit = Gr/Enable
Ts/IncludeDefaultGeant4QtWidgets = "F"
