# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Consolidates the 162 legacy CDCDiabetes CSVs (2004-2021) into 1 baseline CSV."""

import csv
import glob
import math
import os
import re
import shutil
import subprocess
import tempfile

from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'cns_dir',
    '/cns/jv-d/home/datcom/v3_mcf/cdc/diabetes/20240112',
    'Legacy CNS directory (or gs:// prefix) containing the 162 2004-2021 CSVs.',
    allow_override=True,
)
flags.DEFINE_string(
    'output_dir',
    'historical',
    'Output directory for the consolidated historical baseline CSV and TMCF.',
    allow_override=True,
)

OUTPUT_COLUMNS = [
    'observationAbout',
    'observationDate',
    'variableMeasured',
    'value',
    'measurementMethod',
    'observationPeriod',
]

DEFAULT_MEASUREMENT_METHOD = 'dcid:AgeAdjustedPrevalence'
DEFAULT_OBSERVATION_PERIOD = 'P1Y'

DIABETES_FILE_RE = re.compile(r'^DiabetesAtlasCountyData_.*\.csv$')

SUPPRESSED_TOKENS = frozenset({
    '',
    'no data',
    'suppressed',
    'data suppressed',
    'na',
    'n/a',
    'null',
    'none',
    '.',
    '-',
})


def list_source_csvs(source_dir: str) -> list[str]:
    """Lists all DiabetesAtlasCountyData_*.csv files in CNS, GCS, or local."""
    source_dir = source_dir.rstrip('/')
    if source_dir.startswith('gs://'):
        cmd = ['gsutil', 'ls', f'{source_dir}/DiabetesAtlasCountyData_*.csv']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        files = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.endswith('.csv') and DIABETES_FILE_RE.match(
                    os.path.basename(line)):
                files.append(line)
        return sorted(files)
    if source_dir.startswith('/cns/'):
        cmd = ['fileutil', 'ls', f'{source_dir}/DiabetesAtlasCountyData_*.csv']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        files = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.endswith('.csv') and DIABETES_FILE_RE.match(
                    os.path.basename(line)):
                files.append(line)
        return sorted(files)
    pattern = os.path.join(source_dir, 'DiabetesAtlasCountyData_*.csv')
    return sorted(glob.glob(pattern))


def normalize_dcid(val: str) -> str:
    """Normalizes observationAbout/variableMeasured/measurementMethod strings."""
    val = val.strip()
    val = val.removeprefix('dcid:')
    val = val.removeprefix('dcs:')
    if val.endswith(')'):
        val = val.rstrip(')')
    return val


def is_valid_numeric_value(val_str: str) -> bool:
    """Returns True if val_str is a finite numeric value and not suppressed."""
    text = val_str.strip()
    if text.lower() in SUPPRESSED_TOKENS:
        return False
    try:
        parsed = float(text)
    except ValueError:
        return False
    return math.isfinite(parsed)


def consolidate_files(
    source_files: list[str],
    output_csv_path: str,
    local_staging_dir: str,
) -> None:
    """Copies CNS/GCS CSVs locally, merges, deduplicates, and writes output."""
    if not source_files:
        logging.warning('No matching files found for %s', output_csv_path)
        return

    logging.info(
        'Copying %d source files to local staging for %s...',
        len(source_files),
        output_csv_path,
    )
    if source_files[0].startswith('gs://'):
        subprocess.run(
            ['gsutil', '-m', 'cp'] + source_files + [f'{local_staging_dir}/'],
            check=True,
        )
    elif source_files[0].startswith('/cns/'):
        subprocess.run(
            ['fileutil', 'cp', '-f'] + source_files + [f'{local_staging_dir}/'],
            check=True,
        )
    else:
        for src_file in source_files:
            dst_file = os.path.join(local_staging_dir,
                                    os.path.basename(src_file))
            if os.path.abspath(src_file) != os.path.abspath(dst_file):
                shutil.copy2(src_file, dst_file)

    deduped_rows: dict[tuple[str, str, str], dict[str, str]] = {}
    total_rows_read = 0

    for src_path in sorted(source_files):
        fname = os.path.basename(src_path)
        local_path = os.path.join(local_staging_dir, fname)
        with open(local_path, mode='r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                reader.fieldnames = [
                    fn.strip() if fn else '' for fn in reader.fieldnames
                ]
            for row in reader:
                total_rows_read += 1
                obs_about = normalize_dcid(
                    str(
                        row.get('observationAbout') or row.get('location') or
                        ''))
                obs_date = str(
                    row.get('observationDate') or row.get('year') or
                    '').strip()
                var_measured = normalize_dcid(
                    str(row.get('variableMeasured') or ''))
                val = str(row.get('value') or '').strip()
                method = normalize_dcid(str(row.get('measurementMethod') or ''))
                period = str(row.get('observationPeriod') or '').strip()

                if (not obs_about or not obs_date or not var_measured or
                        not is_valid_numeric_value(val)):
                    continue

                obs_about_dcid = f'dcid:{obs_about}'
                var_measured_dcid = f'dcid:{var_measured}'
                method_dcid = (f'dcid:{method}'
                               if method else DEFAULT_MEASUREMENT_METHOD)
                period_val = period if period else DEFAULT_OBSERVATION_PERIOD

                key = (obs_about_dcid, obs_date, var_measured_dcid)
                deduped_rows[key] = {
                    'observationAbout': obs_about_dcid,
                    'observationDate': obs_date,
                    'variableMeasured': var_measured_dcid,
                    'value': val,
                    'measurementMethod': method_dcid,
                    'observationPeriod': period_val,
                }

    os.makedirs(os.path.dirname(output_csv_path) or '.', exist_ok=True)
    with open(output_csv_path, mode='w', encoding='utf-8', newline='') as out_f:
        writer = csv.DictWriter(out_f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for key in sorted(deduped_rows.keys()):
            writer.writerow(deduped_rows[key])

    table_name = os.path.splitext(os.path.basename(output_csv_path))[0]
    tmcf_path = os.path.splitext(output_csv_path)[0] + '.tmcf'
    with open(tmcf_path, mode='w', encoding='utf-8') as tmcf_f:
        tmcf_f.write(f'Node: E:{table_name}->E0\n'
                     'typeOf: dcs:StatVarObservation\n'
                     f'observationAbout: C:{table_name}->observationAbout\n'
                     f'observationDate: C:{table_name}->observationDate\n'
                     f'variableMeasured: C:{table_name}->variableMeasured\n'
                     f'value: C:{table_name}->value\n'
                     f'measurementMethod: C:{table_name}->measurementMethod\n'
                     f'observationPeriod: C:{table_name}->observationPeriod\n')

    logging.info(
        'Wrote %s: %d unique observations (from %d raw rows across %d files).',
        output_csv_path,
        len(deduped_rows),
        total_rows_read,
        len(source_files),
    )


def main(_):
    source_csvs = list_source_csvs(FLAGS.cns_dir)
    logging.info('Found %d CDCDiabetes historical CSVs.', len(source_csvs))

    os.makedirs(FLAGS.output_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp_dir:
        consolidate_files(
            source_csvs,
            os.path.join(FLAGS.output_dir,
                         'cdc_diabetes_historical_2004_2021.csv'),
            tmp_dir,
        )


if __name__ == '__main__':
    app.run(main)
