"""Base data loader for ACS subject tables"""

import os
import csv
import json
import pandas as pd

from io import BytesIO
from requests import get
from zipfile import ZipFile

import generateColMap


_TEMPLATE_TMCF = """Node: E:SubjectTable->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: C:SubjectTable->dcs:{statVar}
measurementMethod: dcs:CesnsusACS{estimatePeriod}yrSurvey
observationDate: C:SubjectTable->ObservationDate
observationAbout: C:SubjectTable->ObservationAbout
value: C:SubjectTable->{statVar}
scalingFactor: C:SubjectTable->{scalingFactor}
unit: C:SubjectTable->{unit}
"""

_UNIT_TEMPLATE = """unit: dcs{unit}"""

_IGNORED_VALUES = set(['-', '*', '***', '*****', 'N', '(X)', 'null'])

class SubjectTableDataLoaderBase:
  """Base dataloader specification for processing subjectTables"""
  def __init__(self, tableID='S2702', acsEstimatePeriod='5', hasPercentages=True, config_json_path=None, outputPath=None):
    ## inputs specified by the user
    self.tableID = tableID
    self.estimatePeriod = acsEstimatePeriod
    self.features = json.load(open(config_json_path, 'r'))
    self.hasPercentages = hasPecentages
    ## default outputPaths
    self.csvOutPath = f'{outputPath}/{tableID}.csv'
    self.tmcfOutPath = f'{outputPath}/{tableID}.tmcf'
    #self.mcfOutPath = f'{outputPath}/{tableID}.mcf'

    ## default initializations
    self.baseURL = 'https://data.census.gov/api/access/table/download'
    self.colMap = None
    self.cleanCSV = pd.DataFrame(columns=['observationDate', 'observationAbout', 'statVar', 'unit', 'scalingFactor'])

  def convert_percentages_to_count(self, df):
    """utility the converts the percentage values in a column to absolute
    counts using the 'denominators' key in the configJSON.
    """
    for countCol, percentColList in self.features['denominators'].items():
      count = 0
      for col in df.columns.tolist():
        if countCol in col:
          count = df[col]
        for percentCol in percentColList:
          if percentCol in col:
            df[col] = df[col] * count
    return df

  def convert_to_geoId(self, row):
    """extracts geoId from the Geographic ID column in the dataset.
    Rows which contain stats for the entire country (US), will have the return
    as an empty string (''), which needs to be removed in further processing.
    """
    return 'dcs:geoId/' + row.split('US')[1]
  
  def create_tmcf():
    with open(path, 'w') as f:
      f.write(_TMCF_TEMPLATE) #since the csv will be having a new row for each stat Var's observation

  def process_csv(self, filename):
    df = pd.read_csv(filename, header=1)
    df['observationAbout'] = df['id'].apply(self.convert_to_geoId)
    df['observationPeriod'] = filename.split('ACSST5Y')[1][:4]
    if self.hasPercentages:
      df = self.convert_percentages_to_count(df)
    #TODO:associate columns to statVars
    #TODO:append selected columns to the cleanCSV
    pass
  
  def getColMap(self, colList):
    if self.colMap == None:
      self.colMap = generateColMap.generateColMap(specDict=self.features, columnList=colList)

    
