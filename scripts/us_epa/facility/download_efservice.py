"""A simple script to download a full table in CSV form from https://data.epa.gov/efservice"""

import io
import os
import pathlib
import sys
import time

import pandas as pd
import requests

from absl import app
from absl import flags
from absl import logging

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../..'))
from us_epa.util import facilities_helper as fh

FLAGS = flags.FLAGS

flags.DEFINE_string('epa_table_name', 'PUB_DIM_FACILITY',
                    'Name of table to download')
flags.DEFINE_string('epa_output_path',
                    'input_files',
                    'Output directory',
                    allow_override=True)

_API_ROOT = 'https://data.epa.gov/efservice/'
_MAX_ROWS = 10000
_ORIS_CROSSWALK_URL = ('https://www.epa.gov/system/files/documents/2022-04/'
                       'ghgrp_oris_power_plant_crosswalk_12_13_21.xlsx')
_ORIS_CROSSWALK_FALLBACK_URL = (
    'https://web.archive.org/web/2024id_/'
    'https://www.epa.gov/system/files/documents/2022-04/'
    'ghgrp_oris_power_plant_crosswalk_12_13_21.xlsx')
_CROSSWALK_COLS = [
    'GHGRP Facility ID',
    'ORIS CODE',
    'ORIS CODE 2',
    'ORIS CODE 3',
    'ORIS CODE 4',
    'ORIS CODE 5',
]
_STORAGE_OPTIONS = {
    'User-Agent': 'Mozilla/5.0',
    'Accept-Encoding': 'gzip, deflate',
}


def _load_oris_crosswalk(max_retries=3,
                         retry_backoff_sec=2.0,
                         request_timeout=60):
    last_err = None
    for url in (_ORIS_CROSSWALK_URL, _ORIS_CROSSWALK_FALLBACK_URL):
        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(url,
                                    headers=_STORAGE_OPTIONS,
                                    timeout=request_timeout)
                resp.raise_for_status()
                df = pd.read_excel(io.BytesIO(resp.content),
                                   'ORIS Crosswalk',
                                   header=0,
                                   dtype=str,
                                   usecols=_CROSSWALK_COLS,
                                   engine='openpyxl')
                print(f'Downloaded ORIS crosswalk ({len(df)} rows) from {url}')
                return df.rename(columns={'GHGRP Facility ID': 'Facility Id'})
            except Exception as e:
                last_err = e
                logging.warning(
                    'Attempt %d/%d failed to download ORIS crosswalk from %s: %s',
                    attempt, max_retries, url, e)
                if attempt < max_retries:
                    time.sleep(retry_backoff_sec * (2**(attempt - 1)))
    raise RuntimeError(
        'Failed to download ORIS crosswalk from both primary and fallback URLs: '
        f'{last_err}') from last_err


def _generate_crosswalk(table_csv_path, crosswalk_csv_path):
    oris_df = _load_oris_crosswalk()
    df = pd.read_csv(table_csv_path, dtype=str)
    fac_col = 'facility_id' if 'facility_id' in df.columns else 'FACILITY_ID'
    frs_col = 'frs_id' if 'frs_id' in df.columns else 'FRS_ID'
    if fac_col in df.columns:
        fac_df = pd.DataFrame({
            'Facility Id': df[fac_col],
            'FRS Id': df[frs_col] if frs_col in df.columns else '',
        }).dropna(subset=['Facility Id']).drop_duplicates(
            subset=['Facility Id'], keep='last')
        merged = fac_df.merge(oris_df, how='left',
                              on='Facility Id').drop_duplicates(
                                  subset=['Facility Id'], keep='first')
    else:
        merged = oris_df.assign(**{'FRS Id': ''})[[
            'Facility Id', 'FRS Id', 'ORIS CODE', 'ORIS CODE 2', 'ORIS CODE 3',
            'ORIS CODE 4', 'ORIS CODE 5'
        ]].drop_duplicates(subset=['Facility Id'], keep='first')
    tmp_path = crosswalk_csv_path + '.tmp'
    merged.to_csv(tmp_path, index=False)
    os.replace(tmp_path, crosswalk_csv_path)
    print(f'Generated {crosswalk_csv_path} ({len(merged)} rows)')


def main(_):
    if not FLAGS.epa_output_path:
        raise ValueError('epa_output_path must be provided.')
    if not FLAGS.epa_table_name:
        raise ValueError('epa_table_name must be provided.')
    pathlib.Path(FLAGS.epa_output_path).mkdir(parents=True, exist_ok=True)
    fh.download(_API_ROOT, FLAGS.epa_table_name, _MAX_ROWS,
                FLAGS.epa_output_path)
    table_csv_path = os.path.join(FLAGS.epa_output_path,
                                  FLAGS.epa_table_name + '.csv')
    crosswalk_path = os.path.join(FLAGS.epa_output_path, 'crosswalks.csv')
    _generate_crosswalk(table_csv_path, crosswalk_path)


if __name__ == '__main__':
    app.run(main)
