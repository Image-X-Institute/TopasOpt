# Set threading self:
------------------------------------------------------------
i:Ts/NumberOfThreads = 0  # defaults to 1
i:Ts/ShowHistoryCountAtInterval = 10000000
b:Ts/ShowHistoryCountOnSingleLine = "True"

# Define collimator
------------------------------------------------------------
s:Ge/Collimator/Type                = "TsCylinder"
s:Ge/Collimator/Parent              = "World"
s:Ge/Collimator/Material            = "G4_W"
d:Ge/Collimator/TransX              = 0 cm
d:Ge/Collimator/TransY              = 0 cm
d:Ge/Collimator/TransZ              = 650 mm
d:Ge/Collimator/RMin                = 5 mm
d:Ge/Collimator/RMax                = 50 mm
d:Ge/Collimator/HL                  = 50 mm
s:Ge/Collimator/DrawingStyle        = "solid"

# Add World:
------------------------------------------------------------
s:Ge/World/Type = "TsBox"
s:Ge/World/Material = "Vacuum"
d:Ge/World/HLX = 250 mm # Half Length
d:Ge/World/HLY = 250 mm
d:Ge/World/HLZ = 1000.0 mm
d:Ge/World/RotX = 0. deg
d:Ge/World/RotY = 0. deg
d:Ge/World/RotZ = 0. deg

# Beam parameters (paramterised source):
------------------------------------------------------------
s:So/Beam/Type                     = "Beam"
sc:So/Beam/Component                = "ElectronSource"
sc:So/Beam/BeamParticle             = "e-"
dc:So/Beam/BeamEnergy               = 10.0 MeV
uc:So/Beam/BeamEnergySpread         = 0
sc:So/Beam/BeamPositionDistribution = "Gaussian" # None, Flat or Gaussian
sc:So/Beam/BeamAngularDistribution  = "Gaussian" # None, Flat or Gaussian
sc:So/Beam/BeamPositionCutoffShape = "Ellipse"
dc:So/Beam/BeamPositionCutoffX = 1 mm
dc:So/Beam/BeamPositionCutoffY = 1 mm
dc:So/Beam/BeamPositionSpreadX = 0.3 mm
dc:So/Beam/BeamPositionSpreadY = 0.3 mm
dc:So/Beam/BeamAngularCutoffX = 5 deg
dc:So/Beam/BeamAngularCutoffY = 5 deg
dc:So/Beam/BeamAngularSpreadX = 0.07 deg
dc:So/Beam/BeamAngularSpreadY = 0.07 deg
ic:So/Beam/NumberOfHistoriesInRun = 1000


# Electron source position
------------------------------------------------------------
s:Ge/ElectronSource/Parent = "World"
s:Ge/ElectronSource/Type="Group"
d:Ge/ElectronSource/TransZ = 800 mm
d:Ge/ElectronSource/RotX = 180. deg
s:Ge/ElectronSource/Material = Ge/World/Material
s:Ge/ElectronSource/Color = "yellow"
sc:Ge/ElectronSource/DrawingStyle = "Solid"

Target
------------------------------------------------------------
# Target is implemented as a separate component from the TsApertureArray
# so that one can independently score on it
# But all of its parameters are derived from Sphinx parameters above
s:Ge/Target/Type 			= "TsCylinder"
s:Ge/Target/Parent 			= "World"
s:Ge/Target/Material 			= "G4_W"
d:Ge/Target/RMax   			= 50 mm
d:Ge/Target/HL  			= 2 mm
d:Ge/Target/TransZ 			= 703 mm
sc:Ge/Target/DrawingStyle 		= "Solid"
sc:Ge/Target/Color 			= "magenta"

Variance reduction in target
------------------------------------------------------------
b:Vr/UseVarianceReduction = "true"
s:Ge/Target/AssignToRegionNamed = "VarianceReduction"
s:Vr/ParticleSplit/Type = "SecondaryBiasing"
sv:Vr/ParticleSplit/ForRegion/VarianceReduction/ProcessesNamed = 1 "eBrem"
uv:Vr/ParticleSplit/ForRegion/VarianceReduction/SplitNumber = 1 1000
# why would I not want to split all particles?
dv:Vr/ParticleSplit/ForRegion/VarianceReduction/MaximumEnergies = 1 10.0 MeV
s:Vr/ParticleSplit/ReferenceComponent = "Target"
dv:Vr/ParticleSplit/ForRegion/VarianceReduction/DirectionalSplitLimits = 1 -1 * Ge/Target/TransZ mm
dv:Vr/ParticleSplit/ForRegion/VarianceReduction/DirectionalSplitRadius = 1 100 mm


# Add phase space scorer below collimator:
------------------------------------------------------------
s:Ge/Magic/Type     = "TsBox"
s:Ge/Magic/Parent   = "World"
s:Ge/Magic/Material = "Vacuum"
d:Ge/Magic/HLX      = Ge/Collimator/RMax mm
d:Ge/Magic/HLY      = Ge/Collimator/RMax mm
d:Ge/Magic/HLZ      = 1 mm
d:Ge/Magic/TransX   = 0. cm
d:Ge/Magic/TransY   = 0. cm
d:Ge/Magic/TransZ   = 580 mm
d:Ge/Magic/RotX     = 0. deg
d:Ge/Magic/RotY     = 0. deg
d:Ge/Magic/RotZ     = 0. deg
s:Ge/Magic/Color    = "skyblue"
s:Ge/Magic/DrawingStyle = "wireframe"


s:Sc/PhaseSpaceFromColl/Quantity                    = "PhaseSpace"
b:Sc/PhaseSpaceFromColl/OutputToConsole             = "False"
s:Sc/PhaseSpaceFromColl/Surface                     = "Magic/ZMinusSurface"
s:Sc/PhaseSpaceFromColl/OutputType                  = "Binary" # ASCII, Binary, Limited or ROOT
s:Sc/PhaseSpaceFromColl/OutputFile                  = "Results/coll_PhaseSpace"
i:Sc/PhaseSpaceFromColl/OutputBufferSize            = 1000
#s:Sc/PhaseSpaceFromColl/OnlyIncludeParticlesGoing  = "In"
b:Sc/PhaseSpaceFromColl/IncludeTOPASTime            = "False"
b:Sc/PhaseSpaceFromColl/IncludeTimeOfFlight         = "False"
b:Sc/PhaseSpaceFromColl/IncludeRunID                = "False"
b:Sc/PhaseSpaceFromColl/IncludeEventID              = "False"
b:Sc/PhaseSpaceFromColl/IncludeTrackID              = "False"
b:Sc/PhaseSpaceFromColl/IncludeParentID             = "False"
b:Sc/PhaseSpaceFromColl/IncludeCreatorProcess       = "False"
b:Sc/PhaseSpaceFromColl/IncludeVertexInfo           = "False"
b:Sc/PhaseSpaceFromColl/IncludeSeed                 = "False"
s:Sc/PhaseSpaceFromColl/IfOutputFileAlreadyExists   = "Overwrite"


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
sv:Gr/OnlyIncludeParticlesNamed = 1 "gamma"

# Physics
------------------------------------------------------------
sv:Ph/Default/Modules = 1 "g4em-standard_opt0"
b:Ph/ListProcesses = "False"

------------------------------------------------------------
# QT
# --
Ts/UseQt = Gr/Enable
Ts/PauseBeforeQuit = Gr/Enable
Ts/IncludeDefaultGeant4QtWidgets = "F"
