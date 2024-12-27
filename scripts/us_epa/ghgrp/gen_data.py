from gas import *
from process import *
from sources import *
from download import *

import os
import sys
import unittest
import csv

_FACILITY_ID = 'Facility Id'
_DCID = 'dcid'
_SV = 'sv'
_YEAR = 'year'
_VALUE = 'value'
_OUT_FIELDNAMES = [_DCID, _SV, _YEAR, _VALUE]
_SAVE_PATH = 'tmp_data'
_OUT_PATH = 'import_data'

if __name__ == '__main__':
    with open(os.path.join('import_data', 'gas_node.mcf'), 'w') as fp:
        append_gas_mcf(fp)
    with open(os.path.join('import_data', 'gas_sv.mcf'), 'w') as fp:
        append_sv_mcf(fp)

    with open(os.path.join('import_data', 'sources_node.mcf'), 'w') as fp:
        append_source_mcf(fp)
    with open(os.path.join('import_data', 'sources_sv.mcf'), 'w') as fp:
        append_sv_mcf(fp)

    downloader = Downloader('tmp_data')
    downloader = download.Downloader(_SAVE_PATH)
    url_year = datetime.now().year
    if url_year < 2030:
        downloader.download_data(url_year, url_year - 1)
    files = downloader.extract_all_years()
    crosswalk_file = os.path.join(_SAVE_PATH, 'crosswalks.csv')
    downloader.save_all_crosswalks(crosswalk_file)
    crosswalk = cw.Crosswalk(crosswalk_file)
    process_data(files, crosswalk, os.path.join(_OUT_PATH, 'all_data.csv'))
