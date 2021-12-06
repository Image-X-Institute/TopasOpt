## Editing GenerateTopasScript.py

In order to reduce the total number of parameters we need to tune, we are going to make the assumption that our source is symetric.

```python
# change
SimpleCollimator.append('dc:So/Beam/BeamEnergy               = 10.0 MeV')
# to 
SimpleCollimator.append('dc:So/Beam/BeamEnergy               = ' + str(variable_dict['BeamEnergy']) + ' MeV')

# and change
SimpleCollimator.append('dc:So/Beam/BeamPositionCutoffX = 2 mm')
SimpleCollimator.append('dc:So/Beam/BeamPositionCutoffY = 2 mm')
SimpleCollimator.append('dc:So/Beam/BeamPositionSpreadX = 0.3 mm')
SimpleCollimator.append('dc:So/Beam/BeamPositionSpreadY = 0.3 mm')
SimpleCollimator.append('dc:So/Beam/BeamAngularCutoffX = 5 deg')
SimpleCollimator.append('dc:So/Beam/BeamAngularCutoffY = 5 deg')
SimpleCollimator.append('dc:So/Beam/BeamAngularSpreadX = 0.07 deg')
SimpleCollimator.append('dc:So/Beam/BeamAngularSpreadY = 0.07 deg')
SimpleCollimator.append('ic:So/Beam/NumberOfHistoriesInRun = 500000 ')
# to
SimpleCollimator.append('dc:So/Beam/BeamPositionCutoffX = ' + str(variable_dict['BeamPositionCutoff']) + ' mm')
SimpleCollimator.append('dc:So/Beam/BeamPositionCutoffY = ' + str(variable_dict['BeamPositionCutoff']) + ' mm')
SimpleCollimator.append('dc:So/Beam/BeamPositionSpreadX = ' + str(variable_dict['BeamPositionSpread']) + ' mm')
SimpleCollimator.append('dc:So/Beam/BeamPositionSpreadY = ' + str(variable_dict['BeamPositionSpread']) + ' mm')
SimpleCollimator.append('dc:So/Beam/BeamAngularCutoffX = ' + str(variable_dict['BeamPositionCutoff']) + ' deg')
SimpleCollimator.append('dc:So/Beam/BeamAngularCutoffY = ' + str(variable_dict['BeamPositionCutoff']) + ' deg')
SimpleCollimator.append('dc:So/Beam/BeamAngularSpreadX = ' + str(variable_dict['BeamAngularSpread']) + ' deg')
SimpleCollimator.append('dc:So/Beam/BeamAngularSpreadY = ' + str(variable_dict['BeamAngularSpread']) + ' deg')
SimpleCollimator.append('ic:So/Beam/NumberOfHistoriesInRun = 50000')
```

Note that there are many other beam parameters we could choose to include. 
We are going to keep this relaitvely simple by just having four optimisation parameters
