"""A simple script to download a full table in CSV form from https://data.epa.gov/efservice"""

import io
import os
import pathlib
import sys
import time

from absl import app
from absl import flags
from absl import logging
import pandas as pd
import requests

# Allows the following module imports to work when running as a script
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from scripts.us_epa.util import facilities_helper as fh

FLAGS = flags.FLAGS


def _define_flags() -> None:
    """Defines command-line flags for this script."""
    flags.DEFINE_string('epa_table_name', 'PUB_DIM_FACILITY',
                        'Name of table to download')
    flags.DEFINE_string('epa_output_path',
                        os.path.join(_SCRIPT_PATH, 'input_files'),
                        'Output directory',
                        allow_override=True)


_API_ROOT = 'https://data.epa.gov/efservice/'
_MAX_ROWS = 10000
# EPA publishes a static crosswalk mapping GHGRP Facility IDs to EIA ORIS
# Power Plant codes (up to 5 ORIS codes per facility). We use this mapping to
# link EpaReportingFacility entities to existing EIA power plant nodes
# (dcid:eia/pp/<ORIS_CODE>) in Data Commons via the `partOf` property.
# A Wayback Machine mirror is configured as a fallback in case the primary
# epa.gov URL is temporarily unavailable.
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
                         request_timeout=60,
                         raw_xlsx_output_dir=None):
    """Downloads the EPA GHGRP-to-ORIS power plant crosswalk Excel sheet.

    Tries the primary EPA URL first and falls back to the Internet Archive
    mirror with exponential backoff. Renames 'GHGRP Facility ID' to
    'Facility Id' so it can be joined with the facility table.
    """
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
                if raw_xlsx_output_dir:
                    xlsx_path = os.path.join(
                        raw_xlsx_output_dir,
                        'ghgrp_oris_power_plant_crosswalk_12_13_21.xlsx')
                    tmp_xlsx = xlsx_path + '.tmp'
                    with open(tmp_xlsx, 'wb') as fp:
                        fp.write(resp.content)
                    os.replace(tmp_xlsx, xlsx_path)
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
    """Builds crosswalks.csv mapping each GHGRP Facility Id to its FRS Id and EIA ORIS codes.

     Output schema of `crosswalks.csv`:
        Facility Id, FRS Id, ORIS CODE, ORIS CODE 2, ORIS CODE 3, ORIS CODE 4, ORIS CODE 5

    How the crosswalk is constructed:
      1. Extracts (Facility Id, FRS Id, year) from the downloaded facility table
         (e.g., PUB_DIM_FACILITY.csv, which contains one row per facility per
         reporting year).
      2. Because a facility's FRS_ID may be missing in some reporting years,
         sorts rows per facility chronologically by reporting year and
         forward-fills (`ffill`) non-empty FRS IDs so the latest known FRS ID
         is retained when deduplicating to one row per Facility Id.
      3. Left-joins the deduplicated (Facility Id, FRS Id) pairs with the
         EPA GHGRP-to-ORIS power plant crosswalk (`oris_df`) on `Facility Id`
         to attach up to 5 EIA ORIS plant codes per facility.
      4. Writes the resulting table atomically via a `.tmp` file to
         `crosswalks.csv` for consumption by `process_facility.py`.
    """
    oris_df = _load_oris_crosswalk(
        raw_xlsx_output_dir=os.path.dirname(crosswalk_csv_path) or None)
    df = pd.read_csv(table_csv_path, dtype=str)
    # Support both lowercase (PUB_DIM_FACILITY) and uppercase (legacy views) column names.
    fac_col = 'facility_id' if 'facility_id' in df.columns else 'FACILITY_ID'
    frs_col = 'frs_id' if 'frs_id' in df.columns else 'FRS_ID'
    year_col = ('year' if 'year' in df.columns else
                ('YEAR' if 'YEAR' in df.columns else None))
    if fac_col in df.columns:
        fac_df = pd.DataFrame({
            'Facility Id':
                df[fac_col],
            'FRS Id': (df[frs_col].fillna('').str.strip()
                       if frs_col in df.columns else ''),
            '_year': (pd.to_numeric(df[year_col], errors='coerce').fillna(0)
                      if year_col else 0),
        })
        fac_df['Facility Id'] = fac_df['Facility Id'].fillna('').str.strip()
        fac_df = fac_df[fac_df['Facility Id'] != '']
        # Preserve original facility appearance order while sorting each
        # facility's multi-year rows chronologically by `_year`.
        fac_df['_fac_order'] = fac_df.groupby('Facility Id',
                                              sort=False).ngroup()
        fac_df = fac_df.sort_values(by=['_fac_order', '_year'],
                                    ascending=[True, True],
                                    kind='mergesort')
        # Forward-fill missing FRS IDs across years within the same facility,
        # then keep the most recent year's record (`keep='last'`).
        fac_df['FRS Id'] = fac_df['FRS Id'].replace('', pd.NA)
        fac_df['FRS Id'] = fac_df.groupby('Facility Id')['FRS Id'].ffill()
        fac_df['FRS Id'] = fac_df['FRS Id'].fillna('')
        fac_df = fac_df[['Facility Id',
                         'FRS Id']].drop_duplicates(subset=['Facility Id'],
                                                    keep='last')
        # Attach EIA ORIS power plant codes (ORIS CODE .. ORIS CODE 5) to each facility.
        merged = fac_df.merge(oris_df, how='left',
                              on='Facility Id').drop_duplicates(
                                  subset=['Facility Id'], keep='first')
    else:
        # Fallback if the input table lacks a facility_id column: emit ORIS
        # crosswalk rows directly with empty FRS Ids.
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
    # Generate crosswalks.csv (GHGRP Facility Id -> FRS Id + EIA ORIS codes)
    # alongside the downloaded facility table in input_files/.
    crosswalk_path = os.path.join(FLAGS.epa_output_path, 'crosswalks.csv')
    _generate_crosswalk(table_csv_path, crosswalk_path)


if __name__ == '__main__':
    _define_flags()
    app.run(main)
