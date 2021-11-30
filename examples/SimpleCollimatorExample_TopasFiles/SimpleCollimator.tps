# Set threading self:
------------------------------------------------------------
i:Ts/NumberOfThreads = 0  # defaults to 1
i:Ts/ShowHistoryCountAtInterval = 1000000
b:Ts/ShowHistoryCountOnSingleLine = "True"

# Add World:
------------------------------------------------------------
s:Ge/World/Type = "TsBox"
s:Ge/World/Material = "Vacuum"
d:Ge/World/HLX = 250 mm # Half Length
d:Ge/World/HLY = 250 mm
d:Ge/World/HLZ = 1200.0 mm
d:Ge/World/RotX = 0. deg
d:Ge/World/RotY = 0. deg
d:Ge/World/RotZ = 0. deg

d:Ge/SID = 1000 mm
d:Ge/SecondaryCollimatorOffset = 20 mm

Target
------------------------------------------------------------
s:Ge/Target/Type 			= "TsCylinder"
s:Ge/Target/Parent 			= "World"
s:Ge/Target/Material 			= "G4_W"
d:Ge/Target/RMax   			= 50 mm
d:Ge/Target/HL  			= 2 mm
d:Ge/Target/TransZ 			= Ge/SID + Ge/Target/HL mm
sc:Ge/Target/DrawingStyle 		= "Solid"
sc:Ge/Target/Color 			= "magenta"

# primary collimator (abuts target)
------------------------------------------------------------
s:Ge/PrimaryCollimator/Parent     = "World" #IEC gantry coordinate
s:Ge/PrimaryCollimator/Material   = "G4_W"
s:Ge/PrimaryCollimator/Type       = "G4Cons"
d:Ge/PrimaryCollimator/RMin1      = 5 mm
d:Ge/PrimaryCollimator/RMax1      = 50 mm #Portions of collimator axis within 4 cm of air
d:Ge/PrimaryCollimator/RMin2      = 3 mm
d:Ge/PrimaryCollimator/RMax2      = 50 mm
d:Ge/PrimaryCollimator/HL         = 48 mm
d:Ge/PrimaryCollimator/Pos        = 1.7 cm
d:Ge/PrimaryCollimator/TransZ     = Ge/SID - Ge/PrimaryCollimator/HL  mm
sc:Ge/PrimaryCollimator/DrawingStyle 		= "Solid"
s:Ge/PrimaryCollimator/Color      = "Blue"


# Secondary collimator
------------------------------------------------------------
s:Ge/SecondaryCollimator/Parent     = "World" #IEC gantry coordinate
s:Ge/SecondaryCollimator/Material   = "G4_Pb"
s:Ge/SecondaryCollimator/Type       = "G4Cons"
d:Ge/SecondaryCollimator/RMin1      = 3 mm
d:Ge/SecondaryCollimator/RMax1      = 50 mm #Portions of collimator axis within 4 cm of air
d:Ge/SecondaryCollimator/RMin2      = 1.82 mm
d:Ge/SecondaryCollimator/RMax2      = 50 mm
d:Ge/SecondaryCollimator/HL         = 27 mm
d:Ge/SecondaryCollimator/Pos        = 1.7 cm
d:Ge/SecondaryCollimator/temp_TransZ1 = Ge/PrimaryCollimator/TransZ - Ge/PrimaryCollimator/HL  mm
d:Ge/SecondaryCollimator/temp_TransZ2 = Ge/SecondaryCollimator/temp_TransZ1 - Ge/SecondaryCollimator/HL mm
d:Ge/SecondaryCollimator/TransZ     = Ge/SecondaryCollimator/temp_TransZ2 - Ge/SecondaryCollimatorOffset mm
sc:Ge/SecondaryCollimator/DrawingStyle 		= "Solid"
s:Ge/SecondaryCollimator/Color      = "green"



# # Beam parameters (paramterised source):
------------------------------------------------------------
s:So/Beam/Type                     = "Beam"
sc:So/Beam/Component                = "ElectronSource"
sc:So/Beam/BeamParticle             = "e-"
dc:So/Beam/BeamEnergy               = 10.0 MeV
uc:So/Beam/BeamEnergySpread         = 0
sc:So/Beam/BeamPositionDistribution = "Gaussian" # None, Flat or Gaussian
sc:So/Beam/BeamAngularDistribution  = "Gaussian" # None, Flat or Gaussian
sc:So/Beam/BeamPositionCutoffShape = "Ellipse"
dc:So/Beam/BeamPositionCutoffX = 2 mm
dc:So/Beam/BeamPositionCutoffY = 2 mm
dc:So/Beam/BeamPositionSpreadX = 0.3 mm
dc:So/Beam/BeamPositionSpreadY = 0.3 mm
dc:So/Beam/BeamAngularCutoffX = 5 deg
dc:So/Beam/BeamAngularCutoffY = 5 deg
dc:So/Beam/BeamAngularSpreadX = 0.07 deg
dc:So/Beam/BeamAngularSpreadY = 0.07 deg
ic:So/Beam/NumberOfHistoriesInRun = 1

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

# Variance reduction in target
# ------------------------------------------------------------
b:Vr/UseVarianceReduction = "False"
s:Ge/Target/AssignToRegionNamed = "VarianceReduction"
s:Vr/ParticleSplit/Type = "SecondaryBiasing"
sv:Vr/ParticleSplit/ForRegion/VarianceReduction/ProcessesNamed = 1 "eBrem"
uv:Vr/ParticleSplit/ForRegion/VarianceReduction/SplitNumber = 1 1000 
dv:Vr/ParticleSplit/ForRegion/VarianceReduction/MaximumEnergies = 1 10.0 MeV
s:Vr/ParticleSplit/ReferenceComponent = "Target"
dv:Vr/ParticleSplit/ForRegion/VarianceReduction/DirectionalSplitLimits = 1 -1 * Ge/Target/TransZ mm
dv:Vr/ParticleSplit/ForRegion/VarianceReduction/DirectionalSplitRadius = 1 100 mm

# # Add phase space scorer below collimator:
# ------------------------------------------------------------
s:Ge/PhaseSpaceScorer/Type     = "TsBox"
s:Ge/PhaseSpaceScorer/Parent   = "World"
s:Ge/PhaseSpaceScorer/Material = "Vacuum"
d:Ge/PhaseSpaceScorer/HLX      = Ge/SecondaryCollimator/RMax2 mm
d:Ge/PhaseSpaceScorer/HLY      = Ge/SecondaryCollimator/RMax2 mm
d:Ge/PhaseSpaceScorer/HLZ      = 1 mm
d:Ge/PhaseSpaceScorer/TransX   = 0. cm
d:Ge/PhaseSpaceScorer/TransY   = 0. cm
d:Ge/PhaseSpaceScorer/temp_TranZ1   = Ge/SecondaryCollimator/TransZ mm
d:Ge/PhaseSpaceScorer/temp_TranZ2   = Ge/PhaseSpaceScorer/temp_TranZ1 - Ge/SecondaryCollimator/HL   mm
d:Ge/PhaseSpaceScorer/TransZ   = Ge/PhaseSpaceScorer/temp_TranZ2 - 10  mm
d:Ge/PhaseSpaceScorer/RotX     = 0. deg
d:Ge/PhaseSpaceScorer/RotY     = 0. deg
d:Ge/PhaseSpaceScorer/RotZ     = 0. deg
s:Ge/PhaseSpaceScorer/Color    = "skyblue"
s:Ge/PhaseSpaceScorer/DrawingStyle = "wireframe"


s:Sc/PhaseSpaceFromColl/Quantity                    = "PhaseSpace"
b:Sc/PhaseSpaceFromColl/OutputToConsole             = "False"
s:Sc/PhaseSpaceFromColl/Surface                     = "PhaseSpaceScorer/ZMinusSurface"
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
b:Gr/Enable = "True"  # Enable/Disable graphics
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
b:Ph/ListProcesses = "False"

------------------------------------------------------------
# QT
# --
Ts/UseQt = Gr/Enable
Ts/PauseBeforeQuit = Gr/Enable
Ts/IncludeDefaultGeant4QtWidgets = "F"
