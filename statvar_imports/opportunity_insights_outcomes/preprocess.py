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
"""Resolves headers, formats geoIds, and shards Opportunity Insights CSVs for stat_var_processor.py."""

import collections
import concurrent.futures
import csv
import os
import re
import subprocess
import tempfile
from absl import app
from absl import flags
from absl import logging

FLAGS = flags.FLAGS

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

flags.DEFINE_string(
    'input_dir',
    os.path.join(_MODULE_DIR, 'raw_data'),
    'Directory containing downloaded raw Opportunity Insights CSV files.',
)
flags.DEFINE_string(
    'shard_dir',
    os.path.join(_MODULE_DIR, 'input_files'),
    'Directory where cleaned CSV inputs for stat_var_processor.py will be written.',
)
flags.DEFINE_string(
    'sv_output_prefix',
    os.path.join(_MODULE_DIR, 'output', 'output'),
    'Output prefix for parallel StatVarObservation CSV shards.',
)
flags.DEFINE_integer(
    'max_rows_per_shard',
    5_000,
    'Maximum rows per output CSV shard.',
)

DEFAULT_EXISTING_STATVAR_MCF = (
    'gs://unresolved_mcf/scripts/statvar/stat_vars.mcf'
)

DATASET_CONFIGS = [
    ('commuting_zone_outcomes.csv', 'commuting_zone', 'baseline_1978_1983'),
    ('county_outcomes.csv', 'county', 'baseline_1978_1983'),
    ('tract_outcomes.csv', 'tract', 'baseline_1978_1983'),
    ('tract_outcomes_late_simple.csv', 'tract', 'late_cohort_1984_1989'),
    ('county_by_cohort_outcomes.csv', 'county', 'annual_cohort_1978_1992'),
    ('cz_by_cohort_outcomes.csv', 'commuting_zone', 'annual_cohort_1978_1992'),
]

_NON_DATA_COLUMNS = frozenset({
    'state',
    'county',
    'tract',
    'cz',
    'czname',
    'cohort',
    'state_name',
    'county_name',
    'cz_name',
})

_MISSING_VALUE_PLACEHOLDERS = frozenset({'', 'NA', 'N/A', '.', 'NAN', 'NULL'})

_MULTI_WORD_TOKEN_REWRITES = (
    ('frac_below_median', 'fracbelowmedian'),
    ('frac_years_xw', 'fracyearsxw'),
    ('kid_blw_p50', 'kidblwp50'),
    ('kfr_native', 'kfrnative'),
    ('kir_native', 'kirnative'),
    ('kfr_stycz', 'kfrstycz'),
    ('kir_stycz', 'kirstycz'),
    ('kfr_top01', 'kfrtop01'),
    ('kir_top01', 'kirtop01'),
    ('kfr_top20', 'kfrtop20'),
    ('kir_top20', 'kirtop20'),
    ('pos_hours', 'poshours'),
    ('spouse_rk', 'spouserk'),
    ('hours_wk', 'hourswk'),
    ('lpov_nbh', 'lpovnbh'),
    ('wgflx_rk', 'wgflxrk'),
    ('par_rank', 'parrank'),
    ('has_dad', 'hasdad'),
    ('has_mom', 'hasmom'),
    ('kfr_imm', 'kfrimm'),
    ('kir_imm', 'kirimm'),
    ('marr_24', 'marr24'),
    ('marr_26', 'marr26'),
    ('marr_29', 'marr29'),
    ('marr_32', 'marr32'),
    ('work_24', 'work24'),
    ('work_26', 'work26'),
    ('work_29', 'work29'),
    ('work_32', 'work32'),
    ('two_par', 'twopar'),
    ('kfr_24', 'kfr24'),
    ('kfr_26', 'kfr26'),
    ('kfr_29', 'kfr29'),
    ('kir_24', 'kir24'),
    ('kir_26', 'kir26'),
    ('kir_29', 'kir29'),
    ('mean_se', 'meanse'),
    ('kid_n', 'kidn'),
)


def format_geo_id(row: dict, geo_level: str) -> str:
    """Returns the Data Commons geoId dcid for a CSV row."""

    def to_int_str(val, width: int) -> str:
        try:
            return f'{int(float(str(val).strip())):0{width}d}'
        except (ValueError, TypeError):
            return str(val).strip().zfill(width)

    if geo_level == 'county':
        return f'geoId/{to_int_str(row["state"], 2)}{to_int_str(row["county"], 3)}'
    if geo_level == 'tract':
        return (
            f'geoId/{to_int_str(row["state"], 2)}'
            f'{to_int_str(row["county"], 3)}'
            f'{to_int_str(row["tract"], 6)}'
        )
    if geo_level == 'commuting_zone':
        return f'geoId/cz{to_int_str(row["cz"], 5)}'
    raise ValueError(f'Unsupported geo_level: {geo_level}')


def normalize_column_header(
    col: str, dataset_mode: str = 'baseline_1978_1983', cohort_token: str = ''
) -> str:
    """Normalizes column tokens into single-word PVMAP tokens, strips 'pooled', and appends cohort token."""
    race_pat = 'pooled|aian|asian|black|hisp|natam|white|other'
    gender_pat = 'pooled|male|female'

    kid_n_match = re.fullmatch(
        f'(?:kid_)?(({race_pat})_({gender_pat}))_(?:n|count)', col
    )
    if kid_n_match:
        base_col = f'kidn_{kid_n_match.group(1)}'
        if dataset_mode == 'late_cohort_1984_1989':
            normalized = f'{base_col}_latekidn'
        else:
            normalized = f'{base_col}_{cohort_token}' if cohort_token else base_col
        return '_'.join(t for t in normalized.split('_') if t != 'pooled')

    blw_p50_match = re.fullmatch(
        f'(?:kid_)?(({race_pat})_({gender_pat}))_blw_p50_(?:n|count)', col
    )
    if blw_p50_match:
        base_col = f'kidblwp50_{blw_p50_match.group(1)}'
        normalized = f'{base_col}_{cohort_token}' if cohort_token else base_col
        return '_'.join(t for t in normalized.split('_') if t != 'pooled')

    if dataset_mode == 'late_cohort_1984_1989':
        if col.startswith('jail_'):
            normalized = f'{col}_latejail'
        else:
            normalized = f'{col}_late'
    elif cohort_token:
        normalized = f'{col}_{cohort_token}'
    else:
        normalized = col

    for old_tok, new_tok in _MULTI_WORD_TOKEN_REWRITES:
        normalized = re.sub(
            r'(^|_)' + old_tok + r'(?=_|$)', r'\1' + new_tok, normalized
        )
    return '_'.join(t for t in normalized.split('_') if t != 'pooled')


def _get_shard_path(output_csv: str, shard_idx: int, suffix_tag: str = '') -> str:
    """Returns the output path for a given 0-based shard index."""
    if output_csv.endswith('_cleaned.csv'):
        base = output_csv[: -len('_cleaned.csv')]
        tag = f'_{suffix_tag}' if suffix_tag else ''
        if shard_idx == 0 and not tag:
            return output_csv
        return f'{base}{tag}_part_{shard_idx:03d}_cleaned.csv'
    stem, ext = os.path.splitext(output_csv)
    if shard_idx == 0 and not suffix_tag:
        return output_csv
    return f'{stem}_{suffix_tag}_part_{shard_idx:03d}{ext}'


def _clean_existing_shards(output_csv: str) -> None:
    """Removes any pre-existing shard files for the given output_csv stem."""
    out_dir = os.path.dirname(output_csv)
    if not out_dir or not os.path.exists(out_dir):
        return
    base_name = os.path.basename(output_csv)
    stem = (
        base_name[: -len('_cleaned.csv')]
        if base_name.endswith('_cleaned.csv')
        else os.path.splitext(base_name)[0]
    )
    for fname in os.listdir(out_dir):
        if fname == base_name or (
            fname.startswith(f'{stem}_') and fname.endswith('_cleaned.csv')
        ):
            os.remove(os.path.join(out_dir, fname))


def shard_wide_csv(
    input_csv: str,
    output_csv: str,
    geo_level: str,
    dataset_mode: str = 'baseline_1978_1983',
    max_rows_per_shard: int = 5_000,
) -> int:
    """Prepends geo_id, strips missing placeholders, and shards a wide CSV for stat_var_processor.py."""
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    _clean_existing_shards(output_csv)
    with open(input_csv, mode='r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)
        data_cols = [
            c for c in (reader.fieldnames or []) if c not in _NON_DATA_COLUMNS
        ]

        if dataset_mode == 'annual_cohort_1978_1992':
            cohort_rows = collections.defaultdict(list)
            for row in reader:
                raw_cohort = (row.get('cohort') or '').strip()
                if not raw_cohort:
                    continue
                cohort_str = str(int(float(raw_cohort)))
                cohort_rows[cohort_str].append(row)

            total_rows = 0
            for cohort_str, rows in sorted(cohort_rows.items()):
                cohort_token = f'c{cohort_str}'
                header = ['geo_id'] + [
                    normalize_column_header(c, dataset_mode, cohort_token)
                    for c in data_cols
                ]
                for shard_idx in range(
                    0, max(1, len(rows)), max(1, max_rows_per_shard)
                ):
                    chunk = rows[shard_idx : shard_idx + max_rows_per_shard]
                    shard_path = _get_shard_path(
                        output_csv,
                        shard_idx // max(1, max_rows_per_shard),
                        cohort_token,
                    )
                    with open(
                        shard_path, mode='w', encoding='utf-8', newline=''
                    ) as out:
                        writer = csv.writer(out)
                        writer.writerow(header)
                        for row in chunk:
                            cleaned_vals = [
                                ''
                                if (row.get(c) or '').strip().upper()
                                in _MISSING_VALUE_PLACEHOLDERS
                                else (row.get(c) or '').strip()
                                for c in data_cols
                            ]
                            if any(cleaned_vals):
                                writer.writerow(
                                    [format_geo_id(row, geo_level)] + cleaned_vals
                                )
                                total_rows += 1
            return total_rows

        header = ['geo_id'] + [
            normalize_column_header(c, dataset_mode) for c in data_cols
        ]
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
            writer = csv.writer(outfile)
            writer.writerow(header)
            for row in reader:
                cleaned_vals = [
                    ''
                    if (row.get(c) or '').strip().upper()
                    in _MISSING_VALUE_PLACEHOLDERS
                    else (row.get(c) or '').strip()
                    for c in data_cols
                ]
                if not any(cleaned_vals):
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
                    writer = csv.writer(outfile)
                    writer.writerow(header)
                writer.writerow([format_geo_id(row, geo_level)] + cleaned_vals)
                rows_written += 1
                shard_rows += 1
        finally:
            outfile.close()
        return rows_written


def _resolve_headers_via_svp(
    raw_dir: str,
    max_cols_per_seed: int = 4_000,
    existing_statvar_mcf: str = DEFAULT_EXISTING_STATVAR_MCF,
) -> dict[str, tuple[str, str, str, str]]:
    """Resolves all unique column headers via stat_var_processor.py in a temp directory."""
    unique_headers = []
    seen = set()
    for filename, _, dataset_mode in DATASET_CONFIGS:
        input_path = os.path.join(raw_dir, filename)
        if not os.path.exists(input_path):
            raise FileNotFoundError(
                f'Required input file not found for {filename}: {input_path}'
            )
        with open(input_path, mode='r', encoding='utf-8') as f:
            raw_headers = next(csv.reader(f))
        data_cols = [c for c in raw_headers if c not in _NON_DATA_COLUMNS]
        cohorts = (
            [f'c{y}' for y in range(1978, 1993)]
            if dataset_mode == 'annual_cohort_1978_1992'
            else ['']
        )
        for cohort_tok in cohorts:
            for c in data_cols:
                norm_h = normalize_column_header(c, dataset_mode, cohort_tok)
                if norm_h not in seen:
                    seen.add(norm_h)
                    unique_headers.append(norm_h)

    repo_root = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..'))
    svp_script = os.path.join(
        repo_root, 'tools/statvar_importer/stat_var_processor.py'
    )
    pvmap_path = os.path.join(_MODULE_DIR, 'pvmap.csv')
    config_path = os.path.join(_MODULE_DIR, 'metadata.csv')

    with tempfile.TemporaryDirectory() as tmpdir:
        seed_files = []
        for chunk_idx, start in enumerate(
            range(0, len(unique_headers), max_cols_per_seed)
        ):
            chunk_headers = unique_headers[start : start + max_cols_per_seed]
            seed_path = os.path.join(
                tmpdir, f'schema_seed_part_{chunk_idx:03d}_cleaned.csv'
            )
            with open(
                seed_path, mode='w', encoding='utf-8', newline=''
            ) as s_file:
                w = csv.writer(s_file)
                w.writerow(['geo_id'] + chunk_headers)
                w.writerow(
                    [f'geoId/seed{chunk_idx:03d}']
                    + [str(i + 1) for i in range(len(chunk_headers))]
                )
            seed_files.append(seed_path)

        out_prefix = os.path.join(tmpdir, 'sv_seed')
        cmd = [
            'python3',
            svp_script,
            f'--input_data={",".join(seed_files)}',
            f'--pv_map={pvmap_path}',
            f'--config_file={config_path}',
            f'--output_path={out_prefix}',
        ]
        if existing_statvar_mcf:
            cmd.append(f'--existing_statvar_mcf={existing_statvar_mcf}')
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode != 0:
            raise RuntimeError(
                f'Header resolution via stat_var_processor.py failed: {res.stderr}'
            )

        header_to_sv = {}
        with open(f'{out_prefix}.csv', mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                seed_place = row['observationAbout'].split('geoId/seed')[-1]
                chunk_idx = int(seed_place)
                col_id = chunk_idx * max_cols_per_seed + int(
                    round(float(row['value']))
                )
                if 1 <= col_id <= len(unique_headers):
                    norm_h = unique_headers[col_id - 1]
                    header_to_sv[norm_h] = (
                        row['observationDate'],
                        row['observationPeriod'],
                        row['variableMeasured'],
                        row.get('unit', ''),
                    )

    logging.info(
        'Resolved %d unique column headers via stat_var_processor.py',
        len(header_to_sv),
    )
    return header_to_sv


def _format_geo_from_row_list(
    row: list[str], col_indices: dict[str, int], geo_level: str
) -> str:
    """Formats geoId/<FIPS> or geoId/cz<ID> directly from a csv.reader row list."""
    if geo_level == 'county':
        return format_geo_id(
            {'state': row[col_indices['state']], 'county': row[col_indices['county']]},
            'county',
        )
    if geo_level == 'tract':
        return format_geo_id(
            {
                'state': row[col_indices['state']],
                'county': row[col_indices['county']],
                'tract': row[col_indices['tract']],
            },
            'tract',
        )
    return format_geo_id({'cz': row[col_indices['cz']]}, 'commuting_zone')


def _expand_chunk_worker(args: tuple) -> int:
    """Worker function to expand a slice of wide CSV rows into StatVarObservations, skipping cells already routed to input_files/*_cleaned.csv."""
    (
        input_path,
        geo_level,
        dataset_mode,
        start_row,
        end_row,
        out_csv_path,
        header_to_sv,
        emitted_by_row,
    ) = args
    obs_written = 0
    with open(input_path, mode='r', encoding='utf-8') as infile, open(
        out_csv_path, mode='w', encoding='utf-8', newline=''
    ) as outfile:
        reader = csv.reader(infile)
        raw_headers = next(reader)
        col_indices = {h: i for i, h in enumerate(raw_headers)}
        data_col_positions = [
            (i, h)
            for i, h in enumerate(raw_headers)
            if h not in _NON_DATA_COLUMNS
        ]

        writer = csv.writer(outfile)
        writer.writerow([
            'observationAbout',
            'observationDate',
            'observationPeriod',
            'variableMeasured',
            'value',
            'unit',
        ])

        if dataset_mode != 'annual_cohort_1978_1992':
            col_specs = []
            for pos, h in data_col_positions:
                norm_h = normalize_column_header(h, dataset_mode)
                sv_meta = header_to_sv.get(norm_h)
                if sv_meta:
                    col_specs.append(
                        (pos, sv_meta[0], sv_meta[1], sv_meta[2], sv_meta[3])
                    )
        else:
            cohort_col_specs = {}
            for y in range(1978, 1993):
                ctok = f'c{y}'
                specs = []
                for pos, h in data_col_positions:
                    norm_h = normalize_column_header(h, dataset_mode, ctok)
                    sv_meta = header_to_sv.get(norm_h)
                    if sv_meta:
                        specs.append(
                            (pos, sv_meta[0], sv_meta[1], sv_meta[2], sv_meta[3])
                        )
                cohort_col_specs[str(y)] = specs

        for row_idx, row in enumerate(reader):
            if row_idx < start_row:
                continue
            if end_row > 0 and row_idx >= end_row:
                break
            if not row:
                continue

            if dataset_mode == 'annual_cohort_1978_1992':
                raw_cohort = row[col_indices['cohort']].strip()
                if not raw_cohort:
                    continue
                cohort_str = str(int(float(raw_cohort)))
                active_specs = cohort_col_specs.get(cohort_str, ())
            else:
                active_specs = col_specs

            skip_positions = emitted_by_row.get(row_idx)
            geo_id = _format_geo_from_row_list(row, col_indices, geo_level)

            out_batch = []
            for pos, obs_date, obs_period, var_measured, unit in active_specs:
                if skip_positions and pos in skip_positions:
                    continue
                val = row[pos].strip()
                if not val or val.upper() in _MISSING_VALUE_PLACEHOLDERS:
                    continue
                out_batch.append(
                    (geo_id, obs_date, obs_period, var_measured, val, unit)
                )
            if out_batch:
                writer.writerows(out_batch)
                obs_written += len(out_batch)

    if obs_written == 0 and os.path.exists(out_csv_path):
        os.remove(out_csv_path)
    return obs_written


def prepare_parallel_shards_and_svp_inputs(
    raw_dir: str,
    shard_dir: str,
    sv_output_prefix: str,
    rows_per_chunk: int = 5_000,
    workers: int = 0,
    existing_statvar_mcf: str = DEFAULT_EXISTING_STATVAR_MCF,
) -> int:
    """Routes the first non-empty observation of each column into shard_dir/*_cleaned.csv for stat_var_processor.py, and expands all remaining cells across parallel workers into output/output_part_*.csv."""
    os.makedirs(shard_dir, exist_ok=True)
    for fname in os.listdir(shard_dir):
        if fname.endswith('_cleaned.csv'):
            os.remove(os.path.join(shard_dir, fname))

    out_dir = os.path.dirname(sv_output_prefix) or '.'
    os.makedirs(out_dir, exist_ok=True)
    base_prefix = os.path.basename(sv_output_prefix)
    for fname in os.listdir(out_dir):
        if fname.startswith(base_prefix) and fname.endswith('.csv'):
            os.remove(os.path.join(out_dir, fname))

    header_to_sv = _resolve_headers_via_svp(
        raw_dir, existing_statvar_mcf=existing_statvar_mcf
    )

    tasks = []
    part_idx = 1
    for filename, geo_level, dataset_mode in DATASET_CONFIGS:
        input_path = os.path.join(raw_dir, filename)
        stem = os.path.splitext(filename)[0]
        emitted_by_row: dict[int, set[int]] = {}
        total_rows = 0

        with open(input_path, mode='r', encoding='utf-8') as infile:
            reader = csv.reader(infile)
            raw_headers = next(reader)
            col_indices = {h: i for i, h in enumerate(raw_headers)}
            data_col_positions = [
                (i, h)
                for i, h in enumerate(raw_headers)
                if h not in _NON_DATA_COLUMNS
            ]
            num_data_cols = len(data_col_positions)

            if dataset_mode == 'annual_cohort_1978_1992':
                unseen_by_cohort = {
                    str(y): set(range(num_data_cols)) for y in range(1978, 1993)
                }
                svp_rows_by_cohort: dict[str, list[list[str]]] = {
                    str(y): [] for y in range(1978, 1993)
                }
                for row_idx, row in enumerate(reader):
                    total_rows = row_idx + 1
                    if not row:
                        continue
                    raw_cohort = row[col_indices['cohort']].strip()
                    if not raw_cohort:
                        continue
                    cohort_str = str(int(float(raw_cohort)))
                    unseen = unseen_by_cohort.get(cohort_str)
                    if not unseen:
                        continue
                    matched_d_indices = []
                    for d_idx in unseen:
                        pos = data_col_positions[d_idx][0]
                        val = row[pos].strip()
                        if val and val.upper() not in _MISSING_VALUE_PLACEHOLDERS:
                            matched_d_indices.append(d_idx)
                    if matched_d_indices:
                        geo_id = _format_geo_from_row_list(
                            row, col_indices, geo_level
                        )
                        cleaned_vals = [''] * num_data_cols
                        row_emitted = emitted_by_row.setdefault(row_idx, set())
                        for d_idx in matched_d_indices:
                            pos = data_col_positions[d_idx][0]
                            cleaned_vals[d_idx] = row[pos].strip()
                            unseen.remove(d_idx)
                            row_emitted.add(pos)
                        svp_rows_by_cohort[cohort_str].append(
                            [geo_id] + cleaned_vals
                        )

                for cohort_str, svp_rows in svp_rows_by_cohort.items():
                    if not svp_rows:
                        continue
                    cohort_token = f'c{cohort_str}'
                    header = ['geo_id'] + [
                        normalize_column_header(c, dataset_mode, cohort_token)
                        for _, c in data_col_positions
                    ]
                    shard_path = os.path.join(
                        shard_dir, f'{stem}_{cohort_token}_part_000_cleaned.csv'
                    )
                    with open(
                        shard_path, mode='w', encoding='utf-8', newline=''
                    ) as out:
                        w = csv.writer(out)
                        w.writerow(header)
                        w.writerows(svp_rows)
            else:
                unseen = set(range(num_data_cols))
                svp_rows = []
                for row_idx, row in enumerate(reader):
                    total_rows = row_idx + 1
                    if not row or not unseen:
                        continue
                    matched_d_indices = []
                    for d_idx in unseen:
                        pos = data_col_positions[d_idx][0]
                        val = row[pos].strip()
                        if val and val.upper() not in _MISSING_VALUE_PLACEHOLDERS:
                            matched_d_indices.append(d_idx)
                    if matched_d_indices:
                        geo_id = _format_geo_from_row_list(
                            row, col_indices, geo_level
                        )
                        cleaned_vals = [''] * num_data_cols
                        row_emitted = emitted_by_row.setdefault(row_idx, set())
                        for d_idx in matched_d_indices:
                            pos = data_col_positions[d_idx][0]
                            cleaned_vals[d_idx] = row[pos].strip()
                            unseen.remove(d_idx)
                            row_emitted.add(pos)
                        svp_rows.append([geo_id] + cleaned_vals)

                if svp_rows:
                    header = ['geo_id'] + [
                        normalize_column_header(c, dataset_mode)
                        for _, c in data_col_positions
                    ]
                    shard_path = os.path.join(shard_dir, f'{stem}_cleaned.csv')
                    with open(
                        shard_path, mode='w', encoding='utf-8', newline=''
                    ) as out:
                        w = csv.writer(out)
                        w.writerow(header)
                        w.writerows(svp_rows)

        if total_rows > 0:
            for start_row in range(0, total_rows, max(1, rows_per_chunk)):
                end_row = start_row + rows_per_chunk
                chunk_emitted = {
                    r: positions
                    for r, positions in emitted_by_row.items()
                    if start_row <= r < end_row
                }
                part_path = f'{sv_output_prefix}_part_{part_idx:04d}.csv'
                tasks.append((
                    input_path,
                    geo_level,
                    dataset_mode,
                    start_row,
                    end_row,
                    part_path,
                    header_to_sv,
                    chunk_emitted,
                ))
                part_idx += 1

    total_obs = 0
    if tasks:
        num_workers = workers if workers > 0 else (os.cpu_count() or 4)
        logging.info(
            'Expanding %d dataset chunks across %d parallel worker processes...',
            len(tasks),
            num_workers,
        )
        with concurrent.futures.ProcessPoolExecutor(max_workers=num_workers) as ex:
            for count in ex.map(_expand_chunk_worker, tasks):
                total_obs += count

    logging.info(
        'Parallel shard preparation complete: wrote %d StatVarObservations to %s_part_*.csv and first-seen column seed CSVs to %s for final stat_var_processor.py execution.',
        total_obs,
        sv_output_prefix,
        shard_dir,
    )
    return total_obs


def main(_):
    os.makedirs(FLAGS.shard_dir, exist_ok=True)
    os.makedirs(os.path.dirname(FLAGS.sv_output_prefix), exist_ok=True)
    os.makedirs(os.path.join(_MODULE_DIR, 'counters'), exist_ok=True)
    prepare_parallel_shards_and_svp_inputs(
        FLAGS.input_dir,
        FLAGS.shard_dir,
        FLAGS.sv_output_prefix,
        rows_per_chunk=FLAGS.max_rows_per_shard,
    )


if __name__ == '__main__':
    app.run(main)
