"""A simple script to download a full table in CSV form from https://data.epa.gov/efservice"""

import os
import pathlib
import ssl
import sys

import pandas as pd

from absl import app
from absl import flags

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_SCRIPT_PATH, '../..'))
from us_epa.util import facilities_helper as fh

FLAGS = flags.FLAGS

flags.DEFINE_string('epa_table_name', 'PUB_DIM_FACILITY',
                    'Name of table to download')
flags.DEFINE_string('epa_output_path', 'input_files', 'Output directory')

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


def _load_oris_crosswalk():
    for url in (_ORIS_CROSSWALK_URL, _ORIS_CROSSWALK_FALLBACK_URL):
        try:
            df = pd.read_excel(url,
                               'ORIS Crosswalk',
                               header=0,
                               dtype=str,
                               usecols=_CROSSWALK_COLS,
                               storage_options=_STORAGE_OPTIONS,
                               engine='openpyxl')
            print(f'Downloaded ORIS crosswalk ({len(df)} rows) from {url}')
            return df.rename(columns={'GHGRP Facility ID': 'Facility Id'})
        except Exception as e:
            print(f'Warning: failed to download ORIS crosswalk from {url}: {e}')
    return pd.DataFrame(columns=[
        'Facility Id', 'ORIS CODE', 'ORIS CODE 2', 'ORIS CODE 3', 'ORIS CODE 4',
        'ORIS CODE 5'
    ])


def _generate_crosswalk(table_csv_path, crosswalk_csv_path):
    ssl._create_default_https_context = ssl._create_unverified_context
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
    merged.to_csv(crosswalk_csv_path, index=False)
    print(f'Generated {crosswalk_csv_path} ({len(merged)} rows)')


def main(_):
    assert FLAGS.epa_output_path
    assert FLAGS.epa_table_name
    pathlib.Path(FLAGS.epa_output_path).mkdir(parents=True, exist_ok=True)
    fh.download(_API_ROOT, FLAGS.epa_table_name, _MAX_ROWS,
                FLAGS.epa_output_path)
    table_csv_path = os.path.join(FLAGS.epa_output_path,
                                  FLAGS.epa_table_name + '.csv')
    crosswalk_path = os.path.join(FLAGS.epa_output_path, 'crosswalks.csv')
    if not os.path.exists(crosswalk_path):
        _generate_crosswalk(table_csv_path, crosswalk_path)


if __name__ == '__main__':
    app.run(main)
