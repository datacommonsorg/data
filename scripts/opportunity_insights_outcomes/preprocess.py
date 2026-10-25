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
"""Resolves headers, formats geoIds, and generates Opportunity Insights cleaned CSV shards and TMCF."""

import concurrent.futures
import csv
import math
import os
import re
import shutil
import subprocess
import sys
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
    'sv_output_prefix',
    os.path.join(_MODULE_DIR, 'output', 'output'),
    'Output prefix for generated TMCF, MCF, and StatVarObservation CSV shards.',
)
flags.DEFINE_string(
    'counters_file',
    os.path.join(_MODULE_DIR, 'counters', 'output_counters.csv'),
    'Output path for stat_var_processor.py resolution counters.',
)
flags.DEFINE_integer(
    'max_rows_per_shard',
    5_000,
    'Maximum rows per output CSV shard.',
)

DEFAULT_EXISTING_STATVAR_MCF = (
    'gs://unresolved_mcf/scripts/statvar/stat_vars.mcf'
)

flags.DEFINE_string(
    'existing_statvar_mcf',
    DEFAULT_EXISTING_STATVAR_MCF,
    'Existing StatVar MCF path passed to stat_var_processor.py during header resolution.',
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


def _is_valid_number(val: str) -> bool:
    """Returns True if val is a non-placeholder finite numeric string."""
    if not val or val.upper() in _MISSING_VALUE_PLACEHOLDERS:
        return False
    try:
        return math.isfinite(float(val))
    except ValueError:
        return False


def str_from_number(
    number: int | float | str, precision_digits: int | None = 5
) -> str:
    """Converts a number or numeric string to its formatted string representation matching stat_var_processor.py."""
    num = float(number) if isinstance(number, str) else number
    if int(num) == num:
        return f'{int(num)}'
    if precision_digits is not None:
        num = round(num, precision_digits)
    return f'{num}'


def _to_positive_int_str(val, width: int = 0) -> str:
    """Returns a zero-padded positive integer string if val is a valid positive integer, else ''."""
    if val is None:
        return ''
    text = str(val).strip()
    if not text or text.upper() in _MISSING_VALUE_PLACEHOLDERS:
        return ''
    try:
        num = float(text)
        if math.isfinite(num) and num > 0 and num.is_integer():
            return f'{int(num):0{width}d}' if width > 0 else str(int(num))
    except (ValueError, TypeError, OverflowError):
        pass
    return ''


def format_geo_id(row: dict, geo_level: str) -> str:
    """Returns the Data Commons geoId dcid for a CSV row."""
    if geo_level == 'county':
        s = _to_positive_int_str(row.get('state'), 2)
        c = _to_positive_int_str(row.get('county'), 3)
        return f'geoId/{s}{c}' if s and c else ''
    if geo_level == 'tract':
        s = _to_positive_int_str(row.get('state'), 2)
        c = _to_positive_int_str(row.get('county'), 3)
        t = _to_positive_int_str(row.get('tract'), 6)
        return f'geoId/{s}{c}{t}' if s and c and t else ''
    if geo_level == 'commuting_zone':
        cz = _to_positive_int_str(row.get('cz'), 5)
        return f'geoId/cz{cz}' if cz else ''
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


_DEFAULT_COHORT_YEARS = tuple(str(y) for y in range(1978, 1993))
_COHORT_TOKEN_RE = re.compile(r'(?:^|_)c(\d+)$')


def _mapped_cohort_years(
    header_to_sv: dict[str, tuple[str, str, str, str]],
) -> list[str]:
    """Returns sorted birth cohort year strings present in resolved header_to_sv keys."""
    years = set()
    for h in header_to_sv:
        m = _COHORT_TOKEN_RE.search(h)
        if m:
            years.add(m.group(1))
    return sorted(years, key=int) if years else list(_DEFAULT_COHORT_YEARS)


def _write_tmcf(sv_output_prefix: str) -> str:
    """Writes the StatVarObservation TMCF file for sv_output_prefix."""
    table_name = os.path.basename(sv_output_prefix) or 'output'
    tmcf_path = f'{sv_output_prefix}.tmcf'
    os.makedirs(os.path.dirname(os.path.abspath(tmcf_path)), exist_ok=True)
    with open(tmcf_path, mode='w', encoding='utf-8', newline='\n') as tmcf_file:
        tmcf_file.write(
            f'Node: E:{table_name}->E0\n'
            f'observationAbout: C:{table_name}->observationAbout\n'
            f'observationDate: C:{table_name}->observationDate\n'
            f'observationPeriod: C:{table_name}->observationPeriod\n'
            f'variableMeasured: C:{table_name}->variableMeasured\n'
            f'value: C:{table_name}->value\n'
            f'unit: C:{table_name}->unit\n'
            'typeOf: dcs:StatVarObservation\n'
        )
    return tmcf_path


def _resolve_headers_via_svp(
    raw_dir: str,
    max_cols_per_seed: int = 4_000,
    existing_statvar_mcf: str = DEFAULT_EXISTING_STATVAR_MCF,
    sv_output_prefix: str = '',
    counters_path: str = '',
) -> dict[str, tuple[str, str, str, str]]:
    """Resolves all unique column headers via stat_var_processor.py in a temp directory."""
    repo_root = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..'))
    svp_script = os.path.join(
        repo_root, 'tools/statvar_importer/stat_var_processor.py'
    )
    pvmap_path = os.path.join(_MODULE_DIR, 'pvmap.csv')
    config_path = os.path.join(_MODULE_DIR, 'metadata.csv')

    pvmap_keys = set()
    if os.path.exists(pvmap_path):
        with open(pvmap_path, mode='r', encoding='utf-8') as f:
            for row in csv.reader(f):
                if row and row[0].strip():
                    pvmap_keys.add(row[0].strip())

    unique_headers = []
    seen = set()
    discovered_cohort_tokens = set()
    for filename, _, dataset_mode in DATASET_CONFIGS:
        input_path = os.path.join(raw_dir, filename)
        if not os.path.exists(input_path):
            raise FileNotFoundError(
                f'Required input file not found for {filename}: {input_path}'
            )
        with open(input_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            raw_headers = next(reader)
            col_indices = {h: i for i, h in enumerate(raw_headers)}
            data_cols = [c for c in raw_headers if c not in _NON_DATA_COLUMNS]
            if dataset_mode == 'annual_cohort_1978_1992':
                cohort_years = set(_DEFAULT_COHORT_YEARS)
                for row in reader:
                    c_str = _parse_cohort(row, col_indices)
                    if c_str:
                        cohort_years.add(c_str)
                cohorts = [f'c{y}' for y in sorted(cohort_years, key=int)]
                discovered_cohort_tokens.update(cohorts)
            else:
                cohorts = ['']
        for cohort_tok in cohorts:
            for c in data_cols:
                norm_h = normalize_column_header(c, dataset_mode, cohort_tok)
                if norm_h not in seen:
                    seen.add(norm_h)
                    unique_headers.append(norm_h)

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
        counters_seed = os.path.join(tmpdir, 'counters_seed.csv')
        cmd = [
            sys.executable,
            svp_script,
            f'--input_data={",".join(seed_files)}',
            f'--pv_map={pvmap_path}',
            f'--config_file={config_path}',
            f'--output_path={out_prefix}',
            f'--output_counters={counters_seed}',
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

        bad_counters = {}
        if os.path.exists(counters_seed):
            with open(counters_seed, mode='r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    k = row.get('key', '')
                    v = (row.get('value') or '').strip()
                    if v in ('', '0', '0.0'):
                        continue
                    if k.startswith((
                        '1:process_input_error-',
                        '1:process_input_dropped-',
                        'dropped_',
                        'error_',
                        'unmapped_',
                    )) or 'unmapped' in k:
                        bad_counters[k] = v

        # Seed header resolution relies on unscaled 1..N observation values
        # (no MultiplyFactor/scalingFactor in pvmap.csv) to recover col_id.
        header_to_sv = {}
        with open(f'{out_prefix}.csv', mode='r', encoding='utf-8') as f:
            for row in csv.DictReader(f):
                seed_place = row['observationAbout'].split('geoId/seed')[-1]
                chunk_idx = int(seed_place)
                col_id = chunk_idx * max_cols_per_seed + int(
                    round(float(row['value']))
                )
                if not (1 <= col_id <= len(unique_headers)):
                    raise RuntimeError(
                        f'Out-of-bounds col_id {col_id} (expected 1..{len(unique_headers)}) from seed row: {row}'
                    )
                norm_h = unique_headers[col_id - 1]
                if norm_h in header_to_sv:
                    raise RuntimeError(
                        f'Duplicate seed resolution for col_id {col_id} ({norm_h}): {row}'
                    )
                header_to_sv[norm_h] = (
                    row['observationDate'],
                    row['observationPeriod'],
                    row['variableMeasured'],
                    row.get('unit', ''),
                )

        unmapped_cohorts = (
            sorted(discovered_cohort_tokens - pvmap_keys)
            if pvmap_keys
            else []
        )
        if unmapped_cohorts:
            bad_counters['unmapped_cohort_tokens'] = ','.join(unmapped_cohorts)
            unmapped_suffixes = tuple(f'_{c}' for c in unmapped_cohorts)
            for h in list(header_to_sv):
                if h.endswith(unmapped_suffixes):
                    del header_to_sv[h]

        missing = sorted(set(unique_headers) - set(header_to_sv))
        if missing or bad_counters:
            logging.error(
                'Unmapped column headers: %s; seed error counters: %s',
                missing,
                bad_counters,
            )
            raise RuntimeError(
                f'Unmapped column headers ({len(missing)}): {missing}; counters: {bad_counters}'
            )

        if sv_output_prefix:
            os.makedirs(
                os.path.dirname(os.path.abspath(sv_output_prefix)),
                exist_ok=True,
            )
            for suffix in ('_stat_vars.mcf', '_stat_vars_schema.mcf'):
                src_mcf = f'{out_prefix}{suffix}'
                if os.path.exists(src_mcf):
                    shutil.copyfile(src_mcf, f'{sv_output_prefix}{suffix}')
        if counters_path and os.path.exists(counters_seed):
            os.makedirs(
                os.path.dirname(os.path.abspath(counters_path)), exist_ok=True
            )
            shutil.copyfile(counters_seed, counters_path)

    logging.info(
        'Resolved %d unique column headers via stat_var_processor.py',
        len(header_to_sv),
    )
    return header_to_sv


_REQUIRED_GEO_COLS = {
    'county': ('state', 'county'),
    'tract': ('state', 'county', 'tract'),
    'commuting_zone': ('cz',),
}


def _extract_row_cell(row: list[str], pos: int | None) -> str:
    """Safely returns stripped cell value at pos if within row bounds, else ''."""
    if pos is None or pos < 0 or pos >= len(row):
        return ''
    return row[pos].strip()


def _parse_cohort(row: list[str], col_indices: dict[str, int]) -> str:
    """Safely extracts and validates the annual cohort year string from a CSV row."""
    return _to_positive_int_str(_extract_row_cell(row, col_indices.get('cohort')))


def _validate_required_columns(
    col_indices: dict[str, int],
    geo_level: str,
    dataset_mode: str,
    input_path: str,
) -> None:
    """Validates that required geographic and cohort columns exist in the CSV header."""
    required = list(_REQUIRED_GEO_COLS.get(geo_level, ()))
    if dataset_mode == 'annual_cohort_1978_1992':
        required.append('cohort')
    missing = [c for c in required if c not in col_indices]
    if missing:
        raise ValueError(f'Missing required columns {missing} in {input_path}')


def _format_geo_from_row_list(
    row: list[str], col_indices: dict[str, int], geo_level: str
) -> str:
    """Formats geoId/<FIPS> or geoId/cz<ID> directly from a csv.reader row list."""
    if geo_level == 'county':
        return format_geo_id(
            {
                'state': _extract_row_cell(row, col_indices.get('state')),
                'county': _extract_row_cell(row, col_indices.get('county')),
            },
            'county',
        )
    if geo_level == 'tract':
        return format_geo_id(
            {
                'state': _extract_row_cell(row, col_indices.get('state')),
                'county': _extract_row_cell(row, col_indices.get('county')),
                'tract': _extract_row_cell(row, col_indices.get('tract')),
            },
            'tract',
        )
    return format_geo_id(
        {'cz': _extract_row_cell(row, col_indices.get('cz'))},
        'commuting_zone',
    )


def _expand_chunk_worker(args: tuple) -> int:
    """Worker function to expand a slice of wide CSV rows into StatVarObservations."""
    (
        input_path,
        geo_level,
        dataset_mode,
        start_row,
        end_row,
        out_csv_path,
        header_to_sv,
        start_offset,
    ) = args

    obs_written = 0
    with open(input_path, mode='r', encoding='utf-8') as infile, open(
        out_csv_path, mode='w', encoding='utf-8', newline=''
    ) as outfile:
        raw_headers = next(csv.reader([infile.readline()]), [])
        col_indices = {h: i for i, h in enumerate(raw_headers)}
        _validate_required_columns(col_indices, geo_level, dataset_mode, input_path)
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
            for y in _mapped_cohort_years(header_to_sv):
                ctok = f'c{y}'
                specs = []
                for pos, h in data_col_positions:
                    norm_h = normalize_column_header(h, dataset_mode, ctok)
                    sv_meta = header_to_sv.get(norm_h)
                    if sv_meta:
                        specs.append(
                            (pos, sv_meta[0], sv_meta[1], sv_meta[2], sv_meta[3])
                        )
                cohort_col_specs[y] = specs

        if start_offset > 0:
            infile.seek(start_offset)
            base_row_idx = start_row
        else:
            base_row_idx = 0

        reader = csv.reader(infile)
        for offset_idx, row in enumerate(reader):
            row_idx = base_row_idx + offset_idx
            if row_idx < start_row:
                continue
            if end_row > 0 and row_idx >= end_row:
                break
            if not row:
                continue

            if dataset_mode == 'annual_cohort_1978_1992':
                cohort_str = _parse_cohort(row, col_indices)
                if not cohort_str:
                    continue
                if cohort_str not in cohort_col_specs:
                    raise ValueError(
                        f'Unmapped birth cohort {cohort_str} in {input_path}'
                    )
                active_specs = cohort_col_specs[cohort_str]
            else:
                active_specs = col_specs

            geo_id = _format_geo_from_row_list(row, col_indices, geo_level)
            if not geo_id:
                continue

            out_batch = []
            for pos, obs_date, obs_period, var_measured, unit in active_specs:
                val = _extract_row_cell(row, pos)
                if not _is_valid_number(val):
                    continue
                out_batch.append((
                    geo_id,
                    obs_date,
                    obs_period,
                    var_measured,
                    str_from_number(val, precision_digits=5),
                    unit,
                ))
            if out_batch:
                writer.writerows(out_batch)
                obs_written += len(out_batch)

    if obs_written == 0 and os.path.exists(out_csv_path):
        os.remove(out_csv_path)
    return obs_written


def prepare_parallel_shards_and_svp_inputs(
    raw_dir: str,
    sv_output_prefix: str,
    rows_per_chunk: int = 5_000,
    workers: int = 0,
    existing_statvar_mcf: str = DEFAULT_EXISTING_STATVAR_MCF,
    counters_path: str = '',
) -> int:
    """Resolves headers via stat_var_processor.py, writes TMCF/MCF, and expands all cells across parallel workers into output/output_part_*.csv."""
    out_dir = os.path.dirname(sv_output_prefix) or '.'
    os.makedirs(out_dir, exist_ok=True)
    base_prefix = os.path.basename(sv_output_prefix)
    for fname in os.listdir(out_dir):
        if fname.startswith(base_prefix) and fname.endswith('.csv'):
            os.remove(os.path.join(out_dir, fname))

    header_to_sv = _resolve_headers_via_svp(
        raw_dir,
        existing_statvar_mcf=existing_statvar_mcf,
        sv_output_prefix=sv_output_prefix,
        counters_path=counters_path,
    )
    _write_tmcf(sv_output_prefix)

    chunk_size = max(1, rows_per_chunk)
    tasks = []
    part_idx = 1
    for filename, geo_level, dataset_mode in DATASET_CONFIGS:
        input_path = os.path.join(raw_dir, filename)
        chunk_offsets: dict[int, int] = {}
        total_rows = 0

        with open(input_path, mode='r', encoding='utf-8') as infile:
            raw_headers = next(csv.reader([infile.readline()]), [])
            col_indices = {h: i for i, h in enumerate(raw_headers)}
            _validate_required_columns(
                col_indices, geo_level, dataset_mode, input_path
            )
            row_idx = 0
            while True:
                if row_idx % chunk_size == 0:
                    chunk_offsets[row_idx] = infile.tell()
                raw_line = infile.readline()
                if not raw_line:
                    break
                row_idx += 1
                total_rows = row_idx

        if total_rows > 0:
            for start_row in range(0, total_rows, chunk_size):
                end_row = start_row + chunk_size
                part_path = f'{sv_output_prefix}_part_{part_idx:04d}.csv'
                tasks.append((
                    input_path,
                    geo_level,
                    dataset_mode,
                    start_row,
                    end_row,
                    part_path,
                    header_to_sv,
                    chunk_offsets.get(start_row, 0),
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
        'Parallel shard preparation complete: wrote %d StatVarObservations to %s_part_*.csv and %s.tmcf.',
        total_obs,
        sv_output_prefix,
        sv_output_prefix,
    )
    return total_obs


def main(_):
    os.makedirs(os.path.dirname(FLAGS.sv_output_prefix), exist_ok=True)
    if FLAGS.counters_file:
        os.makedirs(
            os.path.dirname(os.path.abspath(FLAGS.counters_file)), exist_ok=True
        )
    try:
        prepare_parallel_shards_and_svp_inputs(
            FLAGS.input_dir,
            FLAGS.sv_output_prefix,
            rows_per_chunk=FLAGS.max_rows_per_shard,
            existing_statvar_mcf=FLAGS.existing_statvar_mcf,
            counters_path=FLAGS.counters_file,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        logging.fatal('Preprocessing failed: %s', e)


if __name__ == '__main__':
    app.run(main)
