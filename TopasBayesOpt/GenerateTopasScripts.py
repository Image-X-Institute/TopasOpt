from pathlib import Path

def GenerateTopasScripts(BaseDirectory, iteration, **vars):
    """
    This file simply returns a list object, where each list entry corresponds to
    a line in the topas script.
    When it is called from an Optimiser object,it will receive a dictionary that contains the current values of 
    the variables you set up in optimisation_params when you initialised the optimiser.
    """
    
    FlatteningFilter = []
    FlatteningFilter.append('')
    FlatteningFilter.append('')
    FlatteningFilter.append('')
    FlatteningFilter.append('')
    FlatteningFilter.append('')
    FlatteningFilter.append('b:Ge/World/Invisible = "True"')
    FlatteningFilter.append('')
    FlatteningFilter.append('s:Gr/MyViewA/Type = "OpenGL"')
    FlatteningFilter.append('d:Gr/MyViewA/Phi = 45. deg')
    FlatteningFilter.append('d:Gr/MyViewA/Theta = 45. deg')
    FlatteningFilter.append('')
    FlatteningFilter.append('b:Ts/PauseBeforeQuit = "True"')
    FlatteningFilter.append('')
    FlatteningFilter.append('s:Ge/FlatteningFilter/Type = "Group"')
    FlatteningFilter.append('s:Ge/FlatteningFilter/Parent = "World"')
    FlatteningFilter.append('')
    FlatteningFilter.append('')
    FlatteningFilter.append('')
    FlatteningFilter.append('s:Ge/InnerCone/Type              = "G4SPolycone"')
    FlatteningFilter.append('s:Ge/InnerCone/Parent            = "FlatteningFilter"')
    FlatteningFilter.append('s:Ge/InnerCone/Material          = "G4_Ti"')
    FlatteningFilter.append('s:Ge/InnerCone/Color             = "grey"')
    FlatteningFilter.append('s:Ge/InnerCone/DrawingStyle      = "Solid"')
    FlatteningFilter.append('dv:Ge/InnerCone/R                = 7 0 9 9 6 5 2  0 mm')
    FlatteningFilter.append('dv:Ge/InnerCone/Z                = 7 0 0 1 2 6 8 10 mm')
    FlatteningFilter.append('')
    FlatteningFilter.append('')
    FlatteningFilter.append('s:Ge/OuterCone/Type              = "G4HPolycone"')
    FlatteningFilter.append('s:Ge/OuterCone/Parent            = "FlatteningFilter"')
    FlatteningFilter.append('s:Ge/OuterCone/Material          = "G4_Ti"')
    FlatteningFilter.append('s:Ge/OuterCone/Color             = "brown"')
    FlatteningFilter.append('s:Ge/OuterCone/DrawingStyle      = "Solid"')
    FlatteningFilter.append('dv:Ge/OuterCone/ROuter           = 4 15 15 15 15 mm')
    FlatteningFilter.append('dv:Ge/OuterCone/RInner           = 4  9  9 10 13 mm')
    FlatteningFilter.append('dv:Ge/OuterCone/Z                = 4  0  1  2  3 mm')

    return [FlatteningFilter]