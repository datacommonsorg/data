#!/usr/bin/env python3
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
"""Parallel processor for Japan Census datasets.

Preprocesses raw input CSV files (computes exact broad age-group sums for Census
datasets, merges historical records from GCS CSV, and splits municipality census
shards by year), runs stat_var_processor.py concurrently across shards, and merges
output CSV, TMCF, MCFs, and counters into unified output files.
"""

from collections import defaultdict
import concurrent.futures
import csv
import glob
import os
import shutil
import subprocess
import sys
import tempfile

from absl import app
from absl import flags
from absl import logging

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.join(_MODULE_DIR, '../../util/'))
import file_util

_PROCESSOR_SCRIPT = os.path.abspath(
    os.path.join(_MODULE_DIR,
                 '../../tools/statvar_importer/stat_var_processor.py'))

_FLAGS = flags.FLAGS
flags.DEFINE_string(
    'input_data',
    os.path.join(_MODULE_DIR, 'input_files/*.csv'),
    'Comma-separated list or glob pattern of input CSV files.',
)
flags.DEFINE_string(
    'pv_map',
    os.path.join(_MODULE_DIR, 'japan_census_pv_map.csv'),
    'Path to the PV map CSV file.',
)
flags.DEFINE_string(
    'config_file',
    os.path.join(_MODULE_DIR, 'japan_census_metadata.csv'),
    'Path to the metadata config CSV file.',
)
flags.DEFINE_string(
    'output_path',
    os.path.join(_MODULE_DIR, 'output_files/japan_census_output'),
    'Output prefix path for merged CSV, TMCF, and MCF files.',
)
flags.DEFINE_string(
    'output_counters',
    os.path.join(_MODULE_DIR, 'counters/japan_census_counters.csv'),
    'Output path for merged counters CSV file.',
)
flags.DEFINE_string(
    'existing_statvar_mcf',
    'gs://unresolved_mcf/scripts/statvar/stat_vars.mcf',
    'Path to existing StatVar MCF file.',
)
flags.DEFINE_string(
    'historical_gcs_path',
    'gs://unresolved_mcf/country/japan/deleted_historical_data.csv',
    'GCS path to the deleted historical data CSV file.',
)
flags.DEFINE_integer(
    'parallelism',
    2,
    'Maximum number of concurrent stat_var_processor worker processes.',
)

CSV_HEADER = [
    'year',
    'indicatorCd',
    'regionCd',
    'value',
    'indicatorName',
    'unitCd',
    'unitName',
    'statCd',
    'regionName',
    'timeCd',
    'cycle',
    'regionRank',
    'isSeasonal',
    'isProvisional',
]


def _derive_census_population_rows(records: list[dict[str, str]],
                                   mode: str) -> list[dict[str, str]]:
    """Filters to 5-year census years and computes exact unrounded broad age sums.

    At National (RegionalRank=2) and Prefecture (RegionalRank=3) levels, direct
    broad-age indicators (0201010*100000100*) report rounded annual Population
    Estimates (in thousands), whereas summing the 5-year Census age brackets
    (0201010*20000010* + 0201010*30000011000) yields the exact unrounded Population
    Census counts for <15, 15-64, 65+, and 85+.
    """
    census_records = [
        r for r in records if r['year'].isdigit() and int(r['year']) % 5 == 0
    ]

    by_reg_yr_ind: dict[tuple[str, str, str], dict[str, str]] = {}
    reg_meta: dict[tuple[str, str], dict[str, str]] = {}
    for r in census_records:
        key = (r['regionCd'], r['year'], r['indicatorCd'])
        by_reg_yr_ind[key] = r
        reg_meta[(r['regionCd'], r['year'])] = r

    output_rows: list[dict[str, str]] = []
    # Keep total population (Both sexes, Male, Female) and 5-year brackets:
    # National keeps 010..230 (0-4 through 110+); Prefecture keeps 010..170 (0-4 through 80-84);
    # Municipality keeps only the 3 totals + 9 broad age sums (<15, 15-64, 65+ for Both/Male/Female = 12 StatVars).
    if mode == 'municipality':
        allowed_5yr: set[str] = set()
    else:
        max_5yr_suffix = 230 if mode == 'national' else 170
        allowed_5yr = {
            f'0201010{g}20000010{i:03d}' for g in ('0', '1', '2')
            for i in range(10, max_5yr_suffix + 10, 10)
        }
    allowed_totals = {
        '0201010000000010000',
        '0201010100000010000',
        '0201010200000010000',
    }

    for r in census_records:
        ind = r['indicatorCd']
        if ind in allowed_totals or ind in allowed_5yr:
            output_rows.append(r)

    # Derive exact Census counts for <15, 15-64, 65+, and (for National/Prefecture) 85+ from 5-year brackets.
    broad_specs = [
        ('10000010010', 'Population (under 15)',
         [f'{i:03d}' for i in (10, 20, 30)], False),
        ('10000010020', 'Population (15-64)',
         [f'{i:03d}' for i in range(40, 140, 10)], False),
        ('10000010030', 'Population (65 and over)',
         [f'{i:03d}' for i in range(140, 210, 10)], True),
    ]
    if mode != 'municipality':
        broad_specs.append(('40000010070', 'Population (85 and over)',
                            [f'{i:03d}' for i in (180, 190, 200)], True))

    for reg_cd, yr in sorted(reg_meta.keys()):
        base = reg_meta[(reg_cd, yr)]
        for g in ('0', '1', '2'):
            for target_tail, desc, suffixes, include_100plus in broad_specs:
                part_codes = [f'0201010{g}20000010{s}' for s in suffixes]
                if include_100plus:
                    part_codes.append(f'0201010{g}30000011000')
                vals: list[int] = []
                valid = True
                for c in part_codes:
                    rec = by_reg_yr_ind.get((reg_cd, yr, c))
                    if not rec or not rec['value'].lstrip('-').isdigit():
                        valid = False
                        break
                    vals.append(int(rec['value']))
                if valid:
                    new_row = dict(base)
                    new_row['indicatorCd'] = f'0201010{g}{target_tail}'
                    new_row['indicatorName'] = desc
                    new_row['value'] = str(sum(vals))
                    output_rows.append(new_row)

    return output_rows


_HISTORICAL_CACHE: dict[str, list[dict[str, str]]] = {}


def _load_historical_rows(historical_gcs_path: str) -> list[dict[str, str]]:
    """Loads and caches historical rows from GCS or local CSV."""
    if not historical_gcs_path:
        return []
    if historical_gcs_path in _HISTORICAL_CACHE:
        return _HISTORICAL_CACHE[historical_gcs_path]
    logging.info('Reading historical deleted data: %s', historical_gcs_path)
    with file_util.FileIO(historical_gcs_path, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise RuntimeError(
            f'Historical supplement file is empty: {historical_gcs_path}')
    _HISTORICAL_CACHE[historical_gcs_path] = rows
    return rows


_HISTORICAL_SUPPLEMENT_DATASETS = frozenset({
    'jpn_gender_age_total_population.csv',
    'jpn_aa1_gender_age_total_population.csv',
    'jpn_aa1_aa2_age_gender.csv',
    'jpn_employment.csv',
    'jpn_employement.csv',
    'jpn_unemploymentrate.csv',
    'jpn_student.csv',
    'jpn_aa1_teacher.csv',
    'jpn_aa1_death.csv',
    'jpn_aa1_health.csv',
})


def _apply_historical_supplement(
    dataset_filename: str,
    records: list[dict[str, str]],
    historical_gcs_path: str = '',
) -> list[dict[str, str]]:
    """Merges pre-1975 historical Census and exact archival rows from GCS CSV."""
    if not historical_gcs_path:
        return records
    is_aa2_shard = (dataset_filename.startswith('jpn_aa1_aa2_age_gender_') and
                    dataset_filename.endswith('.csv'))
    if (dataset_filename not in _HISTORICAL_SUPPLEMENT_DATASETS and
            not is_aa2_shard):
        return records
    hist_rows = _load_historical_rows(historical_gcs_path)
    if not hist_rows:
        return records

    by_key: dict[tuple[str, str, str], dict[str, str]] = {}
    for r in records:
        by_key[(r['regionCd'], r['year'], r['indicatorCd'])] = r

    norm_target = dataset_filename.replace('jpn_employement.csv',
                                           'jpn_employment.csv')
    added = 0
    for s in hist_rows:
        norm_src = s['dataset'].replace('jpn_employement.csv',
                                        'jpn_employment.csv')
        if norm_src != norm_target:
            continue
        key = (s['regionCd'], s['year'], s['indicatorCd'])
        if key in by_key:
            continue
        by_key[key] = {
            'year': s['year'],
            'indicatorCd': s['indicatorCd'],
            'regionCd': s['regionCd'],
            'value': s['value'],
            'indicatorName': '',
            'unitCd': '',
            'unitName': '',
            'statCd': '',
            'regionName': '',
            'timeCd': f"{s['year']}CY00",
            'cycle': '3',
            'regionRank': '2' if s['regionCd'] == '00000' else '3',
            'isSeasonal': '1',
            'isProvisional': '0',
        }
        added += 1

    if added:
        logging.info(
            'Applied %d historical supplement rows to %s',
            added,
            dataset_filename,
        )
    return list(by_key.values())


def _write_staged_csv(
    filepath: str,
    rows: list[dict[str, str]],
    fieldnames: list[str],
) -> None:
    """Writes preprocessed rows to a staged CSV file."""
    if not rows:
        return
    all_keys = list(fieldnames)
    for r in rows:
        for k in r.keys():
            if k not in all_keys:
                all_keys.append(k)
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def _prepare_shard_inputs(
    input_files: list[str],
    staging_dir: str,
    historical_gcs_path: str = '',
) -> list[str]:
    """Preprocesses raw input files into staged shard CSV files.

    Applies Census broad age derivations, historical data supplement merging,
    and municipality year-splitting in the temporary staging directory.
    """
    for filepath in input_files:
        if not os.path.exists(filepath):
            continue
        filename = os.path.basename(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            fieldnames = list(reader.fieldnames or CSV_HEADER)

        if not rows:
            continue

        if filename == 'jpn_gender_age_total_population.csv':
            rows = _derive_census_population_rows(rows, mode='national')
            rows = _apply_historical_supplement(filename, rows,
                                                historical_gcs_path)
            out_file = os.path.join(staging_dir, filename)
            _write_staged_csv(out_file, rows, fieldnames)
        elif filename == 'jpn_aa1_gender_age_total_population.csv':
            rows = _derive_census_population_rows(rows, mode='prefecture')
            rows = _apply_historical_supplement(filename, rows,
                                                historical_gcs_path)
            out_file = os.path.join(staging_dir, filename)
            _write_staged_csv(out_file, rows, fieldnames)
        elif filename == 'jpn_aa1_aa2_age_gender.csv':
            rows = _derive_census_population_rows(rows, mode='municipality')
            rows = _apply_historical_supplement(filename, rows,
                                                historical_gcs_path)
            by_year: dict[str, list[dict[str, str]]] = {}
            for r in rows:
                by_year.setdefault(r['year'], []).append(r)
            for yr, yr_rows in sorted(by_year.items()):
                yr_file = os.path.join(staging_dir,
                                       f'jpn_aa1_aa2_age_gender_{yr}.csv')
                _write_staged_csv(yr_file, yr_rows, fieldnames)
        elif (filename.startswith('jpn_aa1_aa2_age_gender_') and
              filename.endswith('.csv')):
            has_5yr = any('20000010' in r.get('indicatorCd', '') for r in rows)
            if has_5yr:
                rows = _derive_census_population_rows(rows, mode='municipality')
            rows = _apply_historical_supplement(filename, rows,
                                                historical_gcs_path)
            out_file = os.path.join(staging_dir, filename)
            _write_staged_csv(out_file, rows, fieldnames)
        else:
            rows = _apply_historical_supplement(filename, rows,
                                                historical_gcs_path)
            out_file = os.path.join(staging_dir, filename)
            _write_staged_csv(out_file, rows, fieldnames)

    return sorted(
        glob.glob(os.path.join(staging_dir, '*.csv')),
        key=lambda p: -os.path.getsize(p),
    )


def _expand_input_files(input_data: str) -> list[str]:
    """Expands comma-separated paths or glob patterns into sorted file paths."""
    files: list[str] = []
    for pattern in input_data.split(','):
        pattern = pattern.strip()
        if not pattern:
            continue
        dir_path = os.path.dirname(pattern)
        if dir_path and os.path.exists(dir_path) and not os.listdir(dir_path):
            raise FileNotFoundError(f'Input directory is empty: {dir_path}')
        matched = sorted(glob.glob(pattern))
        if matched:
            files.extend(matched)
        elif os.path.exists(pattern):
            files.append(pattern)
    return sorted(set(files), key=lambda p: -os.path.getsize(p))


def _run_shard(
    shard_idx: int,
    input_file: str,
    shard_output_prefix: str,
    shard_counters_path: str,
    pv_map: str,
    config_file: str,
    existing_statvar_mcf: str,
) -> tuple[int, str, str, str]:
    """Runs stat_var_processor.py on a single input file in a subprocess."""
    cmd = [
        sys.executable,
        _PROCESSOR_SCRIPT,
        f'--input_data={input_file}',
        f'--pv_map={pv_map}',
        f'--config_file={config_file}',
        f'--output_path={shard_output_prefix}',
        f'--output_counters={shard_counters_path}',
        f'--existing_statvar_mcf={existing_statvar_mcf}',
    ]
    logging.info('[Shard %02d] Starting %s', shard_idx,
                 os.path.basename(input_file))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f'Shard {shard_idx} ({input_file}) failed with exit code {proc.returncode}:\n'
            f'{proc.stderr[-2000:]}')
    logging.info('[Shard %02d] Finished %s', shard_idx,
                 os.path.basename(input_file))
    return shard_idx, input_file, shard_output_prefix, shard_counters_path


def _atomic_write_text(target_path: str, content: str) -> None:
    """Writes text content atomically to target_path via a temp file + os.replace."""
    target_dir = os.path.dirname(os.path.abspath(target_path))
    os.makedirs(target_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix='.tmp_proc_', dir=target_dir)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as out_f:
            out_f.write(content)
        os.replace(tmp_path, target_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _merge_csv_files(shard_prefixes: list[str], final_csv_path: str) -> int:
    """Merges shard CSV files atomically into final_csv_path, deduplicating rows across shards."""
    total_rows = 0
    wrote_header = False
    seen_lines: set[str] = set()
    target_dir = os.path.dirname(os.path.abspath(final_csv_path))
    os.makedirs(target_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix='.tmp_merge_',
                                    suffix='.csv',
                                    dir=target_dir)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as out_f:
            for prefix in shard_prefixes:
                shard_csv = f'{prefix}.csv'
                if not os.path.exists(shard_csv):
                    continue
                with open(shard_csv, 'r', encoding='utf-8') as in_f:
                    header = in_f.readline()
                    if not header:
                        continue
                    if not wrote_header:
                        out_f.write(header)
                        wrote_header = True
                    for line in in_f:
                        if line in seen_lines:
                            continue
                        seen_lines.add(line)
                        out_f.write(line)
                        total_rows += 1
        os.replace(tmp_path, final_csv_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    return total_rows


def _counter_aggregation_mode(key: str) -> str:
    """Returns how a stat_var_processor counter key should be aggregated across shards.

    Note: Per-shard '*-unique-*' cardinality counters (except output-svobs-unique-typeOf,
    which is always 1 across shards) are summed across shards because exact set union
    cardinality cannot be reconstructed from per-shard integer counts alone.
    """
    lower = key.lower()
    if (lower == 'existing-statvars-from-mcf' or
            lower.startswith('existing-') or
            lower.endswith('output-svobs-unique-typeof')):
        return 'max'
    if 'start_time' in lower:
        return 'min'
    if 'end_time' in lower or 'mem' in lower:
        return 'max'
    if lower.endswith('_rate') or '_rate_' in lower:
        return 'avg'
    return 'sum'


def _merge_counters(shard_counter_files: list[str],
                    final_counters_path: str) -> None:
    """Aggregates numeric counters across all shards into final_counters_path."""
    if not final_counters_path:
        return
    values_by_key: dict[str, list[float]] = defaultdict(list)
    is_int_map: dict[str, bool] = defaultdict(lambda: True)

    for cf in shard_counter_files:
        if not os.path.exists(cf):
            continue
        with open(cf, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('key,'):
                    continue
                parts = line.rsplit(',', 1)
                if len(parts) != 2:
                    continue
                k, v_str = parts[0].strip('"'), parts[1].strip()
                try:
                    if '.' in v_str:
                        values_by_key[k].append(float(v_str))
                        is_int_map[k] = False
                    else:
                        values_by_key[k].append(float(int(v_str)))
                except ValueError:
                    continue

    lines = ['key,value\n']
    for k in sorted(values_by_key.keys()):
        vals = values_by_key[k]
        mode = _counter_aggregation_mode(k)
        if mode == 'max':
            val = max(vals)
        elif mode == 'min':
            val = min(vals)
        elif mode == 'avg':
            val = sum(vals) / len(vals)
            is_int_map[k] = False
        else:
            val = sum(vals)

        if is_int_map[k]:
            lines.append(f'{k},{int(val)}\n')
        else:
            lines.append(f'{k},{val:.2f}\n')

    _atomic_write_text(final_counters_path, ''.join(lines))


def _merge_mcf_files(shard_prefixes: list[str], suffix: str,
                     final_mcf_path: str) -> None:
    """Deduplicates MCF nodes by Node line across shards and writes final_mcf_path."""
    seen_nodes: dict[str, str] = {}
    for prefix in shard_prefixes:
        shard_mcf = f'{prefix}{suffix}'
        if not os.path.exists(shard_mcf):
            continue
        with open(shard_mcf, 'r', encoding='utf-8') as f:
            content = f.read()
        for block in content.split('\n\n'):
            block = block.strip()
            if not block:
                continue
            lines = [
                l for l in block.splitlines() if not l.strip().startswith('#')
            ]
            if not lines:
                continue
            node_line = next((l for l in lines if l.startswith('Node:')),
                             lines[0])
            if node_line not in seen_nodes:
                seen_nodes[node_line] = '\n'.join(lines)

    if os.path.exists(final_mcf_path):
        os.remove(final_mcf_path)

    if not seen_nodes:
        return

    body = ''.join(
        seen_nodes[node_key] + '\n\n' for node_key in sorted(seen_nodes.keys()))
    _atomic_write_text(final_mcf_path, body)


def _prepare_local_statvar_mcf(existing_statvar_mcf: str, tmp_dir: str) -> str:
    """Copies a gs:// existing_statvar_mcf file once to tmp_dir for all shards."""
    if not existing_statvar_mcf or not existing_statvar_mcf.startswith('gs://'):
        return existing_statvar_mcf
    local_mcf = os.path.join(
        tmp_dir,
        os.path.basename(existing_statvar_mcf) or 'stat_vars.mcf')
    logging.info(
        'Caching %s once to %s for all shard workers...',
        existing_statvar_mcf,
        local_mcf,
    )
    file_util.file_copy(existing_statvar_mcf, local_mcf)
    if not os.path.exists(local_mcf) or os.path.getsize(local_mcf) == 0:
        raise RuntimeError(
            f'Failed to copy existing_statvar_mcf from {existing_statvar_mcf}')
    return local_mcf


def _run_pipeline() -> None:
    """Executes the parallel sharded stat_var_processor pipeline and merges outputs."""
    raw_input_files = _expand_input_files(_FLAGS.input_data)
    if not raw_input_files:
        raise RuntimeError(f'No input files matched: {_FLAGS.input_data}')

    output_path = os.path.abspath(_FLAGS.output_path)
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    shards_tmp_dir = tempfile.mkdtemp(prefix='.shards_', dir=output_dir)

    try:
        staging_dir = os.path.join(shards_tmp_dir, 'staged_inputs')
        os.makedirs(staging_dir, exist_ok=True)
        shard_input_files = _prepare_shard_inputs(
            raw_input_files,
            staging_dir=staging_dir,
            historical_gcs_path=_FLAGS.historical_gcs_path,
        )
        if not shard_input_files:
            raise RuntimeError(
                f'No staged input files generated from: {raw_input_files}')

        max_workers = max(
            1,
            min(_FLAGS.parallelism, len(shard_input_files),
                os.cpu_count() or 1))
        logging.info(
            'Processing %d staged input files across %d parallel workers...',
            len(shard_input_files),
            max_workers,
        )

        local_statvar_mcf = _prepare_local_statvar_mcf(
            _FLAGS.existing_statvar_mcf, shards_tmp_dir)
        shard_prefixes: list[str] = []
        shard_counters: list[str] = []
        futures = []

        with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers) as executor:
            for idx, input_file in enumerate(shard_input_files):
                base = os.path.splitext(os.path.basename(input_file))[0]
                s_prefix = os.path.join(shards_tmp_dir,
                                        f'shard_{idx:02d}_{base}')
                s_counters = os.path.join(shards_tmp_dir,
                                          f'counters_{idx:02d}_{base}.csv')
                shard_prefixes.append(s_prefix)
                shard_counters.append(s_counters)
                futures.append(
                    executor.submit(
                        _run_shard,
                        idx,
                        os.path.abspath(input_file),
                        s_prefix,
                        s_counters,
                        os.path.abspath(_FLAGS.pv_map),
                        os.path.abspath(_FLAGS.config_file),
                        local_statvar_mcf,
                    ))

            for fut in concurrent.futures.as_completed(futures):
                fut.result()

        # 1. Merge CSV outputs
        final_csv = f'{output_path}.csv'
        total_rows = _merge_csv_files(shard_prefixes, final_csv)
        if total_rows == 0:
            raise RuntimeError(f'Merged output CSV has 0 rows: {final_csv}')
        logging.info('Merged %d SVObs rows into %s', total_rows, final_csv)

        # 2. Generate unified TMCF (normalizing table reference to japan_census_output)
        final_tmcf = f'{output_path}.tmcf'
        table_name = os.path.basename(output_path)
        for prefix in shard_prefixes:
            shard_tmcf = f'{prefix}.tmcf'
            if os.path.exists(shard_tmcf):
                shard_table = os.path.basename(prefix)
                with open(shard_tmcf, 'r', encoding='utf-8') as f:
                    tmcf_text = (f.read().replace(f'E:{shard_table}->',
                                                  f'E:{table_name}->').replace(
                                                      f'C:{shard_table}->',
                                                      f'C:{table_name}->'))
                _atomic_write_text(final_tmcf, tmcf_text)
                break
        if not os.path.exists(final_tmcf):
            raise RuntimeError(
                f'Failed to generate unified TMCF file: {final_tmcf}')

        # 3. Merge StatVar MCF and Schema MCF files
        _merge_mcf_files(shard_prefixes, '_stat_vars.mcf',
                         f'{output_path}_stat_vars.mcf')
        _merge_mcf_files(
            shard_prefixes,
            '_stat_vars_schema.mcf',
            f'{output_path}_stat_vars_schema.mcf',
        )

        # 4. Merge Counters
        if _FLAGS.output_counters:
            _merge_counters(shard_counters,
                            os.path.abspath(_FLAGS.output_counters))
            logging.info('Merged counters into %s', _FLAGS.output_counters)

    finally:
        if os.path.exists(shards_tmp_dir):
            shutil.rmtree(shards_tmp_dir)


def main(_) -> None:
    try:
        _run_pipeline()
    except Exception as e:
        logging.fatal('%s', e, exc_info=True)


if __name__ == '__main__':
    app.run(main)
