"""Base data loader for ACS subject tables"""

import os
import csv
import json
import pandas as pd
from io import BytesIO
from requests import get
from zipfile import ZipFile

_TEMPLATE_STAT_VAR = """Node: dcid:{name}
typeOf: dcs:StatisticalVariable
populationType: dcs:{populationType}
statType: dcs:{statType}
measuredProperty: dcs:{measuredProperty}
{constraints}
"""

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

## A dictionary that maps the desired prefix for statVar based on statType
_PREFIX_LOOKUP = {
  'measuredValue': 'Count',
  'medianValue': 'Median'
}

_UNIT_TEMPLATE = """unit: dcs{unit}"""

_IGNORED_VALUES = set(['-', '*', '***', '*****', 'N', '(X)', 'null'])

class SubjectTableDataLoaderBase:
  ##TODO: Move utilty methods to a separate module
  """Base dataloader specification for processing subjectTables"""
  def __init__(self, tableID='S2702', acsEstimatePeriod='5',
               config_json_path=None, outputPath=None, statVarListPath=None):
    ## inputs specified by the user
    self.tableID = tableID
    self.estimatePeriod = acsEstimatePeriod
    self.features = json.load(open(config_json_path, 'r'))
    self.statVarList = open(statVarListPath, 'r').read().splitlines()

    ## default outputPaths
    self.csvOutPath = f'{outputPath}/{tableID}_cleaned.csv'
    self.tmcfOutPath = f'{outputPath}/{tableID}.tmcf'
    self.mcfOutPath = f'{outputPath}/{tableID}.mcf'

    ## default initializations
    self.baseURL = 'https://data.census.gov/api/access/table/download'
    self.statVars = None
    self.colMap = None
    self.rawData = None
    self.cleanCSV = pd.DataFrame(columns=['observationAbout',\
                                           'observationAbout', 'statVar',\
                                           'unit', 'scalingFactor'])

  def _download(self, download_id):
    """given an baseURL and download_id for the session, the data download is
    done through a get request."""
    response = get(f'{self.baseURL}?download_id={download_id}')
    if response.status_code != 200:
      print(f'Error while downloading from {self.baseURL}?download_id={download_id} with code {respsonse.status_code}')
      print('Exiting.....')
      exit()
    return BytesIO(response.content)

  def _process(self, zipFile):
    #TODO[sharadshriram]: extend this to work with directories too.
    """processes a zip file with all the data files that was downloaded."""
    with ZipFile(zipFile) as zf:
      for filename in zf.namelist():
        if 'data_with_overlays' in filename:
            columnMap = self._clean_csv(filename)
  
  def _convert_percentages_to_count(self, df, features=self.features):
    """utility the converts the percentage values in a column to absolute
    counts using the 'denominators' key in the configJSON.
    """
    for countCol, percentColList in features['denominators'].items():
      const = 0
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
    return 'dcs:geoId/' + row.split('US')[1]

  def _get_populationType(self, part, features=self.features):
    """
    """
    for c in features['populationType'].keys():
      if c in part:
        print(c)
        return features['populationType'][c]
      else:
        return features['populationType']['_DEFAULT']

  def _convert_to_lowerCamelCase(self, string):
    """utility that converts string to camelCase,
       used for mapping columsn to keys in features['pvs']"""
    string = string.title()
    string = string.replace(' ', '')
    return string[0].lower() + string[1:]


  def _column_to_statVar(self, column, features=self.features):
    #TODO[sharadshriram]: Handle dcs prefixes in each statVar node
    """generates a dictionary statistical variable with all properties specified in the JSON spec 
        for a single column"""
    base = False
    pvFlag = False
    statVar = {}
    partList = column.split('!!')

    for idx, part in enumerate(partList):

      #set the base for special cases like median, etc.
      if not base and 'measurement' in features:
        if part in features['measurement']:
          statVar.update(features['measurement'][part])
          base = True
      #set the default statVar definition
      if not base and 'measurement' in features and '_DEFAULT' in features['measurement']:
        statVar.update(features['measurement']['_DEFAULT'])
    
      #TODO[sharadshriram]: resolve the toggle for non-default populationTypes
      statVar['populationType'] = _get_populationType(column)

      # associate pvs to statVar
      if partList[-1] not in features['measurement']:
        ## find the whole words
        if not pvFlag and 'pvs' in features and _convert_to_lowerCamelCase(partList[idx]) in features['pvs']:
          for p in partList[(idx+1):]:
            try:
              statVar[_convert_to_lowerCamelCase(partList[idx])] = features['pvs'][_convert_to_lowerCamelCase(partList[idx])][p]
              if 'inferredSpec' in features and _convert_to_lowerCamelCase(partList[idx]) in features['inferredSpec']:
                statVar.update(features['inferredSpec'][_convert_to_lowerCamelCase(partList[idx])])
              pvFlag = True
            except KeyError:
              continue #handles the count
        ## handle the case to map race and citizenship which occur as substrings
        for p in [*map(_convert_to_lowerCamelCase, part.split())]:
          if not pvFlag and 'pvs' in features and p in features['pvs']:
            try:
              statVar[p] = features['pvs'][p][partList[-1]]
            except KeyError:
              continue #handles the count

        ## handle special cases: gender/ residence status / worker class
        if not pvFlag and 'SEX' in partList:
          statVar['gender'] = features['pvs']['gender'][partList[-1]]
        if not pvFlag and 'RESIDENCE 1 YEAR AGO' in partList:
          try:
            statVar['residentStatus'] = features['pvs']['residentStatus'][partList[-1]]
          except KeyError:
            continue # Handles the count

        if not pvFlag and 'CLASS OF WORKER' in partList:
          statVar['establishmentOwnership'] = features['pvs']['establishmentOwnership'][partList[-1]]
          statVar['workerClassification'] = features['pvs']['workerClassification'][partList[-1]]       

        # handle the case to attribute employment property based on status
        if 'EMPLOYMENT STATUS' in partList:
          try:
            statVar['employment'] = features['pvs']['employment'][partList[-1]]
          except KeyError:
            continue # Handles the count
        
      #if the column is Margin of Error, update statType key
      if 'Margin Of Error' in column:
        statVar.update({
            'statType':'marginOfError',
            })

    ## if statVar column in enumSpecializations' value's value then remove
    ##Add the defaultPV
    if 'defaultPVs' in features and features['defaultPVs'].keys():
      for k, v in features['defaultPVs'].items():
        statVar[k] = v
        statVar['constraintProperties'] = k

    ## TODO[sharadshriram]: Make the statVar and call Anush's function
    # statVar['dcid'] = get_stat_var_name(stat_var_dict, ignore_props=None)
    
    ##Add Universe PVs based on the populationType of StatVar
    if 'universePVs' in features:
      for elem in features['universePVs']:
        if statVar['populationType'] == elem['populationType'] and statVar['constraintProperties'] in elem['constraintProperties']:
          for k, v in elem['dependentPVs'].items():
            statVar[k] = v
    return statVar

  def validate_columnMap(self, columnMap):
    ##TODO: needs to be improved with better rules
    """utility function which validates mapping of csv columns and statistcal variables on set of rules"""
    #clean up the colMap
    for key in columnMap.keys():
      ## 1. remove keys that are defined as keys in denominators
      if key in self.features['denominators']:
        del columnMap[key]
      ## 2. remove keys that are defined are values in enumSpecializations
      for k in self.features['enumSpecializations'].keys():
        if self.features['enumSpecializations'][k] == key:
          del columnMap[key]

    ## columnMap checks
    if self.columnMap is None:
      self.columnMap = columnMap
    if self.columnMap != columnMap:
      print("WARNING! The statVar nodes seems to differ")
    return columnMap



  def _generate_columnMap(self, columnList):
    """generates definitions fo statistical variables based on the columns of the raw data"""
    if self.columnMap is not None and 'ignoreColumns' in self.features and len(columnList) > 0:
      columnMap = {}
      for column in columnList:
        if col not in self.features['ignoreColumns']:
            columnMap[col] = self._column_to_statVar(col)
      self.columnMap = validate_columnMap(columnMap)
      return True
    else:
      return True


  def _clean_csv(self, filename):
    """reads a data csv file into self.raw_data class for each data file,
    processes the file by converting percentage columns to counts"""
    df = pd.read_csv(filename, header=1)
    ## generate or update columnMap is not defined or modified
    if self.columnMap is None:
      self._generate_columnMap(df.columns.tolist())
    ## Process CSV
    df['id'] = df['id'].apply(lambda row: _convert_to_geoId(row))
    df = _convert_percentages_to_count(df)

  

