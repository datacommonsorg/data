"""Module to generate a column map to their corresponding statistical variable defintions"""

import os
import json
import pandas as pd

#TODO:Remove this import and make it from ~/data/utils/ directory when it is available
os.system('curl https://raw.githubusercontent.com/Abilityguy/data/dcid_gen/util/statvar_dcid_generator.py -LO statvar_dcid_generator.py')
import statvar_dcid_generator

dcid_gen = statvar_dcid_generator.StatVarDcidGenerator()

class generateColMap:
  """module to generate a column map given a list of columns of the dataset and a JSON Spec"""
  def __init__(self, specDict=None, columnList=None):
    """module init """
    features = specDict
    columnMap = {}
    #for each column generate the definition of their respective statistical variable node
    for col in columnList:
      if 'ignoreColumns' in features and col not in self.features['ignoreColumns']:
          columnMap[col] = self.column_to_statVar(col)
    #validate the generate columnMap
    if self.valid_colMap():
      return columnMap
    else:
      return {'Error': 'Encountered an error while generating column map'}

  def column_to_statVar(self, column):
    """generates a dictionary statistical variable with all properties specified in the JSON spec for a single column"""
    base = False
    statVar = {}
    partList = column.split('!!')

    for part in partList:
      #set the base for special cases like median, etc.
      if not base and 'measurement' in self.self.features:
        if part in self.features['measurement']:
          statVar.update(self.features['measurement'][part])
          base = True

    #set the default statVar definition
    if not base and 'measurement' in self.features and '_DEFAULT' in self.features['measurement']:
      statVar.update(self.features['measurement']['_DEFAULT'])

    #set the populationType attribute
    statVar['populationType'] = self.get_populationType(partList)

    # associate pvs to statVar
    if partList[-1] not in self.features['measurement']:
      if 'pvs' in self.features:
        #p = property, k = dictionary of partList[-1] to propertyValue
        for p, k in self.features['pvs'].items():
          for c, v in k.items():
            if c == partList[-1]: #last token of column name matches in property
              statVar[p] = v
              if 'inferredSpec' in self.features and p in self.features['inferredSpec']:
                statVar.update(self.features['inferredSpec'][p])
            ##if the property is somewhere in the column name
            for part in partList:
              if c in part:
                statVar[p] = v

    #TODO: Add units and scalingFactor

    #if the column is Margin of Error, update statType key
    if 'Margin of Error' in partList:
      statVar['statType'] = 'marginOfError'

    #generating dcid using the utils/statvar_dcid_generator.py
    statVar['dcid'] = dcid_gen.get_stat_var_name(statVar, ignore_props=None)

    ##Add Universe PVs based on the populationType of StatVar
    if 'universePVs' in self.features:
      for elem in self.features['universePVs']:
        if statVar['populationType'] == elem['populationType']:
          for k, v in elem['dependentPVs'].items():
            statVar[k] = v
    return statVar
  
  def get_populationType(self, partList):
    """From tokenized column name, find the most relevant populationType from the JSON Spec """
    if 'populationType' in self.features:
      for part in partList:
        for k, v in self.features['populationType'].items():
          if k in part:
            return self.features['populationType'][k]
      return self.features['populationType']['_DEFAULT']

  def valid_colMap(self):
    """Collection of rules to validate and clean-up the column map"""
    
