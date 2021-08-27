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

_TEMPLATE_TMCF = """Node: E:Subject_Table->E{index}
typeOf: dcs:StatVarObservation
variableMeasured: C:Subject_Table->dcs:{statVar}
measurementMethod: dcs:CesnsusACS{estimatePeriod}yrSurvey
observationDate: C:Subject_Table->ObservationDate
observationAbout: C:Subject_Table->ObservationAbout
value: C:Subject_Table->{statVar}{unit}
"""

## A dictionary that maps the desired prefix for statVar based on statType
_PREFIX_LOOKUP = {
  'measuredValue': 'Count',
  'medianValue': 'Median'
}

_UNIT_TEMPLATE = """unit: dcs{unit}"""

_IGNORED_VALUES = set(['-', '*', '***', '*****', 'N', '(X)', 'null'])

class SubjectTableDataLoaderBase:
  """Base dataloader specification for processing subjectTables"""
  def __init__(self, tableID='S2702', acsEstimatePeriod='5',
               config_json_path=None, outputPath=None, statVarListPath=None):
    ## inputs specified by the user
    self.tableID = tableID
    self.estimatePeriod = acsEstimatePeriod
    self.configJSON = json.load(open(config_json_path, 'r'))
    self.statVarList = open(statVarListPath, 'r').read().splitlines()
    self.csvOutPath = f'{outputPath}/{tableID}_cleaned.csv'
    self.tmcfOutPath = f'{outputPath}/{tableID}.tmcf'
    self.mcfOutPath = f'{outputPath}/{tableID}.mcf'

    ## default initializations
    self.baseURL = 'https://data.census.gov/api/access/table/download'
    self.columnMap = {}
    self.statVars = []
    self.rawData = None
    self.cleanCSV = pd.DataFrame(columns=['observationAbout',\
                                           'observationAbout', 'statVar',\
                                           'unit'])

  def _download(self, download_id):
    """given an baseURL and download_id for the session, the data download is
    done through a get request."""
    response = get(f'{self.baseURL}?download_id={download_id}')
    return BytesIO(response.content)

  def _process(self, zipFile):
    #TODO[sharadshriram]: extend this to work with directories too.
    """processes a zip file with all the data files that was downloaded."""
    with ZipFile(zipFile) as zf:
      for filename in zf.namelist():
        if 'data_with_overlays' in filename:
            self._clean_csv(filename)

  def _clean_csv(self, filename):
    """reads a data csv file into self.raw_data class for each data file,
    processes the file by converting percentage columns to counts"""
    self.rawData = pd.read_csv(filename, header=1)
    self.rawData['id'] = self.rawData['id'].apply(lambda row:
                                                  self._convert_to_geoId(row))
    #TODO[sharadshriram]: Convert percent columns to count based on a flag
    self._convert_percentages_to_count()

    #for each column in the dataset, make statVars, from the third column
    #columns 1 and 2 contains the geographic code and name respectively.
    for column in self.rawData[2:]:
      self._convert_column_to_statVar(column)
    return True

  def _convert_percentages_to_count(self):
    """
    """
    for countCol, percentColList in self.configJSON['denominator'].items():
      self.raw_data[percentColList] = self.raw_data[percentColList].multiply(
                                      self.raw[countCol], axis="index")
      return True

  def _convert_to_geoId(self, row):
    """extracts geoId from the Geographic ID column in the dataset.
    Rows which contain stats for the entire country (US), will have the return
    as an empty string (''), which needs to be removed in further processing.
    """
    return 'dcs:geoId/' + row.split('US')[1]



  def download_and_process(self, download_id=None):
    zf = _download(download_id)
    _process(zf)
    _create_mcf()
    _create_tmcf()

  def process_zip(self, zipFile=None):
    _process(zipFile)
    _create_mcf()
    _create_tmcf()
