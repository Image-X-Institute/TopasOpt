# Set threading self:
------------------------------------------------------------
i:Ts/NumberOfThreads = 0  # defaults to 1
i:Ts/ShowHistoryCountAtInterval = 10000000


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

# Add phase space scorer below collimator:
------------------------------------------------------------
s:Ge/Magic/Type     = "TsBox"
s:Ge/Magic/Parent   = "World"
s:Ge/Magic/Material = "Vacuum"
d:Ge/Magic/HLX      = 50 mm
d:Ge/Magic/HLY      = 50 mm
d:Ge/Magic/HLZ      = 1 mm
d:Ge/Magic/TransX   = 0. cm
d:Ge/Magic/TransY   = 0. cm
d:Ge/Magic/TransZ   = 580 mm
d:Ge/Magic/RotX     = 0. deg
d:Ge/Magic/RotY     = 0. deg
d:Ge/Magic/RotZ     = 0. deg
s:Ge/Magic/Color    = "skyblue"
s:Ge/Magic/DrawingStyle = "wireframe"

# Phase Space source:
------------------------------------------------------------
s:So/Example/Type                            = "PhaseSpace"
s:So/Example/PhaseSpaceFileName              = "Results/coll_PhaseSpace"
s:So/Example/Component                       = "World"
i:So/Example/PhaseSpaceMultipleUse          = 300
b:So/Example/PhaseSpaceIncludeEmptyHistories = "False"
# i:So/Example/NumberOfHistoriesInRun = 10 # set PhaseSpaceMultipleUse to 0 to enable this option

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
dc:Ge/Phantom/TransZ = 0. cm
dc:Ge/Phantom/RotX = 0. deg
dc:Ge/Phantom/RotY = 0. deg
dc:Ge/Phantom/RotZ = 0. deg
ic:Ge/Phantom/XBins = 30
ic:Ge/Phantom/YBins = 30
ic:Ge/Phantom/ZBins = 60
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
s:Sc/PhantomScorer/OutputFile                  = "Results/WaterTank"


# Graphics View and trajectory filters:
------------------------------------------------------------
b:Gr/Enable = "False"  # Enable/Disable graphics
s:Gr/ViewA/Type              = "OpenGL"
dc:Gr/ViewA/Theta            = 90 deg
dc:Gr/ViewA/Phi              = 0 deg
uc:Gr/ViewA/TransX           = -0.5
uc:Gr/ViewA/TransY           = 0.
sc:Gr/ViewA/Projection       = "Orthogonal"
dc:Gr/ViewA/PerspectiveAngle = 30 deg
uc:Gr/ViewA/Zoom             = 10
bc:Gr/ViewA/IncludeStepPoints = "False"
bc:Gr/ViewA/HiddenLineRemovalForTrajectories = "True"
# sv:Gr/OnlyIncludeParticlesFromVolume = 1 "ElectronSource" # one or more volume
# sv:Gr/OnlyIncludeParticlesFromComponentOrSubComponentsOf = 1 "ElectronSource"
# sv:Gr/OnlyIncludeParticlesFromComponent = 2 "Target" "Sphinx"  # one or more component
# sv:Gr/OnlyIncludeParticlesFromVolume = 1 "Film1/Film1_Z_Division"
# sv:Gr/OnlyIncludeParticlesFromComponent = 1 "Film2"
sv:Gr/OnlyIncludeParticlesFromProcess = 1 "primary"


# Physics
------------------------------------------------------------
sv:Ph/Default/Modules = 1 "g4em-standard_opt0"
b:Ph/ListProcesses = "True"


------------------------------------------------------------
# QT
# --
Ts/UseQt = Gr/Enable
Ts/PauseBeforeQuit = Gr/Enable
Ts/IncludeDefaultGeant4QtWidgets = "T"
