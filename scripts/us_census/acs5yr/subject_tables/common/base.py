"""Base data loader for ACS subject tables"""

import os
import csv
import json
import pandas as pd
from io import BytesIO
from requests import get
from zipfile import ZipFile

_TEMPLATE_STAT_VAR = """Node: dcid:{name}
description: "{description}"
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

_UNIT_TEMPLATE = """unit: dcs{unit}"""

_IGNORED_VALUES = set(['-', '*', '***', '*****', 'N', '(X)', 'null'])

class SubjectTableDataLoaderBase:
  def __init__(self, tableID='S2702', acsEstimatePeriod='5', config_json_path=None, outputPath=None, statVarListPath=None):
    self.estimatePeriod = acsEstimatePeriod
    self.config_json = json.load(open(config_json_path, 'r'))
    self.statVarList = open(statVarListPath, 'r').read().splitlines()
    self.csv_outPath = f'{outputPath}/{tableID}_cleaned.csv'
    self.tmcf_outPath = f'{outputPath}/{tableID}.tmcf'
    self.mcf_outPath = f'{outputPath}/{tableID}.mcf'

    self.raw_data = None
    self.clean_csv = pd.DataFrame(columns=['observationAbout', 'observationAbout', 'statVar', 'unit'])

  def _download(self, download_id):
    response = get(f'https://data.census.gov/api/access/table/download?download_id={download_id}')
    return BytesIO(response.content)

  def _process(self, zipFile):
    with ZipFile(zipFile) as zf:
      for filename in zf.namelist():
        if 'data_with_overlays' in filename:
            self._clean_csv(filename)

  def _clean_csv(self, filename):
    pass

  def _create_mcf(self):
    pass

  def _create_tmcf(self):
    pass

  def _convert_percentages_to_count(self, row):
    pass

  def _convert_to_geoId(self, row):
    pass

  def _get_constraints(self, row):
    pass


  def download_and_process(self, download_id=None):
    zf = _download(download_id)
    _process(zf)
    _create_mcf()
    _create_tmcf()

  def process_zip(self, zipFile=None):
    _process(zipFile)
    _create_mcf()
    _create_tmcf()
