"""Base data loader for ACS subject tables"""

import os
import csv
import json
import pandas as pd

from io import BytesIO
from requests import get
from zipfile import ZipFile

from  generate_col_map import generate


_TEMPLATE_TMCF = """Node: E:SubjectTable->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: C:SubjectTable->dcs:{statVar}
measurementMethod: dcs:CensusACS{estimatePeriod}yrSurvey
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
  def __init__(self, has_percentages=True, config_json_path=None, output_path=None):
    ## inputs specified by the user
    tableID = 'S2702'
    self.estimatePeriod = 5
    ## read JSON spec
    f = open(config_json_path, 'r')
    self.features = json.load(f)
    f.close()

    self.hasPercentages = has_percentages
    ## default outputPaths
    self.csv_out_path = f'{output_path}/{tableID}.csv'
    self.tmcf_out_path = f'{output_path}/{tableID}.tmcf'
    #self.mcf_out_path = f'{output_path}/{tableID}.mcf'

    ## default initializations
    self.base_url = 'https://data.census.gov/api/access/table/download'
    self.column_map = None
    self.clean_csv =  pd.DataFrame(columns=['observationDate', 'observationAbout', 'statVar', 'unit', 'scalingFactor'])

  def _convert_percentages_to_count(self, df):
    """utility the converts the percentage values in a column to absolute
    counts using the 'denominators' key in the configJSON.
    """
    if 'denominators' in self.features.keys():
     for countCol, percentColList in self.features['denominators'].items():
       count = 0
       for col in df.columns.tolist():
         if countCol in col:
           count = df[col]
         for percentCol in percentColList:
           if percentCol in col:
             df[col] = df[col] * count
    return df

  def _convert_to_geoId(self, row):
    """extracts geoId from the Geographic ID column in the dataset.
    Rows which contain stats for the entire country (US), will have the return
    as an empty string (''), which needs to be removed in further processing.
    """
    #TODO: Test if the code expands for all Census supported place types
    return 'dcs:geoId/' + row.split('US')[1]

  def _set_column_map(self, colList):
    """method that updates column_map for the table if it is None, else returns True"""
    if self.column_map == None:
      self.column_map = generate(specDict=self.features, columnList=colList)
      return True
    else:
      return True 

  def _get_column_map(self):
    """get method to fetch the column_map for unit test"""
    return self.column_map

  def _process_csv(self, filename):
    """barebones function with common methods for csv processing"""
    df = pd.read_csv(filename, header=1)
    df = df.dropna() #drop null values
    df['observationAbout'] = df['id'].apply(self._convert_to_geoId)
    df['observationPeriod'] = filename.split('ACSST5Y')[1][:4]
    if self.hasPercentages:
      df = self._convert_percentages_to_count(df)
   # #TODO:associate columns to statVars
   # #TODO:append selected columns to the cleanCSV

  def _process_zip_file(self, zip_file_path):
    """for the moment generates column map alone for the dataset"""
    #TODO: link to the _process_csv()
    with ZipFile(zip_file_path) as zf:
      for filename in zf.namelist():
        if 'data_with_overlays' in filename:
            df = pd.read_csv(zf.open(filename, 'r'), header=1)
            if self._set_column_map(df.columns.tolist()):
              continue
            zf.close()
            #NOTE: The scope of this script is currently to validate column map generation from file
            break

