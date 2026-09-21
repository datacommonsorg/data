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
"""Unpivots and shards wide Opportunity Insights CSVs into raw token columns for stat_var_processor.py.

All Data Commons StatisticalVariable and StatVarObservation schema mappings
(populationType, measuredProperty, statType, race, gender, parentIncome,
observationDate, and observationPeriod) live declaratively in
opportunity_insights_outcomes_pvmap.csv.
"""

import csv
import os
import re
from absl import app
from absl import flags
from absl import logging

try:
    from statvar_imports.opportunity_insights_outcomes import download as download_script
except ImportError:
    import download as download_script

FLAGS = flags.FLAGS

flags.DEFINE_string(
    'input_dir',
    'raw_data',
    'Directory containing raw Opportunity Atlas CSV files downloaded from source.',
)
flags.DEFINE_string(
    'output_dir',
    'input_files',
    'Directory where sharded CSV files for stat_var_processor.py will be written.',
)
flags.DEFINE_bool(
    'download',
    True,
    'Whether to download/refresh the raw CSV files from opportunityinsights.org/data/ before processing.',
)
flags.DEFINE_integer(
    'max_rows_per_shard',
    5_000_000,
    'Maximum observation rows per output CSV shard before rotating to a new shard file.',
)

DATASET_CONFIGS = [
    ('commuting_zone_outcomes.csv', 'commuting_zone', 'baseline_1978_1983'),
    ('county_outcomes.csv', 'county', 'baseline_1978_1983'),
    ('tract_outcomes.csv', 'tract', 'baseline_1978_1983'),
    ('tract_outcomes_late_simple.csv', 'tract', 'late_cohort_1984_1989'),
    ('county_by_cohort_outcomes.csv', 'county', 'annual_cohort_1978_1992'),
    ('cz_by_cohort_outcomes.csv', 'commuting_zone', 'annual_cohort_1978_1992'),
]

# Raw source tokens present in Opportunity Insights CSV column headers
RAW_OUTCOME_CODES = (
    'coll',
    'comcoll',
    'emp',
    'fpw',
    'grad',
    'has_dad',
    'has_mom',
    'hours_wk',
    'hs',
    'jail',
    'kfi',
    'kfr_imm',
    'kfr_native',
    'kfr_stycz',
    'kfr_top01',
    'kfr_top20',
    'kfr_24',
    'kfr_26',
    'kfr_29',
    'kfr',
    'kii',
    'kir_imm',
    'kir_native',
    'kir_stycz',
    'kir_top01',
    'kir_top20',
    'kir_24',
    'kir_26',
    'kir_29',
    'kir',
    'lpov_nbh',
    'married',
    'marr_24',
    'marr_26',
    'marr_29',
    'marr_32',
    'pos_hours',
    'proginc',
    'somecoll',
    'spouse_rk',
    'staycz',
    'stayhome',
    'staytract',
    'teenbrth',
    'two_par',
    'wgflx_rk',
    'working',
    'work_24',
    'work_26',
    'work_29',
    'work_32',
)

RAW_RACE_CODES = ('pooled', 'aian', 'asian', 'black', 'hisp', 'natam', 'white', 'other')
RAW_GENDER_CODES = ('pooled', 'male', 'female')
RAW_PERCENTILE_CODES = ('p100', 'p10', 'p1', 'p25', 'p50', 'p75')

OUTPUT_FIELDNAMES = [
    'geo_id',
    'metric',
    'stat_type',
    'race',
    'gender',
    'parent_income',
    'cohort',
    'value',
]

_MISSING_VALUE_PLACEHOLDERS = frozenset({'', 'NA', 'N/A', '.', 'NAN', 'NULL'})


def format_geo_id(row: dict, geo_level: str) -> str:
    """Returns the Data Commons geoId dcid for a CSV row."""
    if geo_level == 'county':
        state = str(int(float(str(row['state']).strip()))).zfill(2)
        county = str(int(float(str(row['county']).strip()))).zfill(3)
        return f'geoId/{state}{county}'
    if geo_level == 'tract':
        state = str(int(float(str(row['state']).strip()))).zfill(2)
        county = str(int(float(str(row['county']).strip()))).zfill(3)
        tract = str(int(float(str(row['tract']).strip()))).zfill(6)
        return f'geoId/{state}{county}{tract}'
    if geo_level == 'commuting_zone':
        cz = str(int(float(str(row['cz']).strip()))).zfill(5)
        return f'geoId/cz{cz}'
    raise ValueError(f'Unsupported geo_level: {geo_level}')


def parse_population_slices(formatted_col: str) -> tuple[str, str, str]:
    """Splits a raw column slice into raw source tokens (race, gender, parent_income)."""
    race_pattern = '|'.join(RAW_RACE_CODES)
    gender_pattern = '|'.join(RAW_GENDER_CODES)
    percentile_pattern = '|'.join(RAW_PERCENTILE_CODES)

    rgp_match = re.fullmatch(
        f'({race_pattern})_({gender_pattern})_({percentile_pattern})',
        formatted_col,
    )
    if rgp_match:
        return rgp_match.group(1), rgp_match.group(2), rgp_match.group(3)

    rg_match = re.fullmatch(f'({race_pattern})_({gender_pattern})', formatted_col)
    if rg_match:
        return rg_match.group(1), rg_match.group(2), ''

    raise ValueError(f'Unable to parse population slice: {formatted_col}')


def classify_column(col: str) -> tuple[str, str, str, str, str] | None:
    """Splits a wide CSV header into raw source tokens (metric, stat_type, race, gender, parent_income)."""
    outcome_pattern = '|'.join(RAW_OUTCOME_CODES)
    outcome_match = re.fullmatch(f'({outcome_pattern})_(\\w+)', col)
    if outcome_match:
        outcome = outcome_match.group(1)
        rest = outcome_match.group(2)
        meta_match = re.fullmatch(r'(\w+?)_(mean_se|mean|se|n)', rest)
        if meta_match:
            formatted_name = meta_match.group(1)
            stat_token = meta_match.group(2)
        else:
            formatted_name = rest
            stat_token = 'measured'

        try:
            race, gender, parent_income = parse_population_slices(formatted_name)
        except ValueError:
            return None

        return outcome, stat_token, race, gender, parent_income

    race_pattern = '|'.join(RAW_RACE_CODES)
    gender_pattern = '|'.join(RAW_GENDER_CODES)
    par_rank_match = re.fullmatch(
        f'par_rank_(({race_pattern})_({gender_pattern}))_(mean_se|mean)', col
    )
    if par_rank_match:
        race, gender, parent_income = parse_population_slices(par_rank_match.group(1))
        return 'par_rank', par_rank_match.group(4), race, gender, parent_income

    non_outcome_patterns = [
        ('kid_n', f'kid_(({race_pattern})_({gender_pattern}))_n'),
        ('kid_n', f'(({race_pattern})_({gender_pattern}))_count'),
        ('frac_below_median', f'frac_below_median_(({race_pattern})_({gender_pattern}))'),
        ('kid_blw_p50', f'kid_(({race_pattern})_({gender_pattern}))_blw_p50_n'),
        ('kid_blw_p50', f'(({race_pattern})_({gender_pattern}))_blw_p50_count'),
        ('frac_years_xw', f'frac_years_xw_(({race_pattern})_({gender_pattern}))'),
    ]
    for code, pat in non_outcome_patterns:
        m = re.fullmatch(pat, col)
        if m:
            race, gender, parent_income = parse_population_slices(m.group(1))
            return code, 'measured', race, gender, parent_income

    return None


def resolve_cohort_key(row: dict, dataset_mode: str, metric_code: str) -> str:
    """Returns the raw cohort token for PVMAP date lookup (or empty string for baseline)."""
    if dataset_mode == 'baseline_1978_1983':
        return ''
    if dataset_mode == 'late_cohort_1984_1989':
        if metric_code == 'jail':
            return 'late_jail'
        if metric_code == 'kid_n':
            return 'late_kid_n'
        return 'late'
    if dataset_mode == 'annual_cohort_1978_1992':
        row_cohort = (row.get('cohort') or '').strip()
        if row_cohort:
            try:
                return str(int(float(row_cohort)))
            except ValueError:
                pass
    return ''


def _get_shard_path(output_csv: str, shard_idx: int) -> str:
    """Returns the output path for a given 0-based shard index."""
    if shard_idx == 0:
        return output_csv
    if output_csv.endswith('_cleaned.csv'):
        base = output_csv[: -len('_cleaned.csv')]
        return f'{base}_part_{shard_idx:03d}_cleaned.csv'
    stem, ext = os.path.splitext(output_csv)
    return f'{stem}_part_{shard_idx:03d}{ext}'


def process_csv_file(
    input_csv: str,
    output_csv: str,
    geo_level: str,
    dataset_mode: str = 'baseline_1978_1983',
    max_rows_per_shard: int = 5_000_000,
) -> int:
    """Unpivots a wide Opportunity Atlas CSV into sharded CSV(s) for stat_var_processor.py."""
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    rows_written = 0
    shard_idx = 0
    shard_rows = 0

    outfile = open(
        _get_shard_path(output_csv, shard_idx),
        mode='w',
        encoding='utf-8',
        newline='',
    )
    try:
        writer = csv.DictWriter(outfile, fieldnames=OUTPUT_FIELDNAMES)
        writer.writeheader()

        with open(input_csv, mode='r', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            col_specs = {}
            for col in reader.fieldnames or []:
                spec = classify_column(col)
                if spec:
                    col_specs[col] = spec

            for row in reader:
                geo_id = format_geo_id(row, geo_level)

                for col, (
                    metric_code,
                    stat_token,
                    race,
                    gender,
                    parent_income,
                ) in col_specs.items():
                    raw_val = (row.get(col) or '').strip()
                    if raw_val.upper() in _MISSING_VALUE_PLACEHOLDERS:
                        continue
                    if max_rows_per_shard > 0 and shard_rows >= max_rows_per_shard:
                        outfile.close()
                        shard_idx += 1
                        shard_rows = 0
                        outfile = open(
                            _get_shard_path(output_csv, shard_idx),
                            mode='w',
                            encoding='utf-8',
                            newline='',
                        )
                        writer = csv.DictWriter(
                            outfile, fieldnames=OUTPUT_FIELDNAMES
                        )
                        writer.writeheader()

                    writer.writerow({
                        'geo_id': geo_id,
                        'metric': metric_code,
                        'stat_type': stat_token,
                        'race': race,
                        'gender': gender,
                        'parent_income': parent_income,
                        'cohort': resolve_cohort_key(
                            row, dataset_mode, metric_code
                        ),
                        'value': raw_val,
                    })
                    rows_written += 1
                    shard_rows += 1
    finally:
        outfile.close()

    logging.info(
        'Wrote %d normalized observation rows across %d shard(s) for %s',
        rows_written,
        shard_idx + 1,
        output_csv,
    )
    return rows_written


def main(_):
    os.makedirs(FLAGS.input_dir, exist_ok=True)
    os.makedirs(FLAGS.output_dir, exist_ok=True)

    if FLAGS.download:
        download_script.download_all_sources(FLAGS.input_dir)

    for filename, geo_level, dataset_mode in DATASET_CONFIGS:
        input_path = os.path.join(FLAGS.input_dir, filename)
        if not os.path.exists(input_path):
            raise FileNotFoundError(
                f'Required input file not found for {filename}: {input_path}'
            )
        stem = os.path.splitext(filename)[0]
        output_path = os.path.join(FLAGS.output_dir, f'{stem}_cleaned.csv')
        process_csv_file(
            input_path,
            output_path,
            geo_level,
            dataset_mode,
            max_rows_per_shard=FLAGS.max_rows_per_shard,
        )


if __name__ == '__main__':
    app.run(main)
