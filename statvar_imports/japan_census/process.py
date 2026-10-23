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
"""Parallel wrapper for running stat_var_processor.py across multiple input CSVs.

Spawns concurrent worker processes (one per input CSV file), merges all output
CSVs, MCFs, and counters into the unified output_path, and preserves full
stat_var_processor CLI flag compatibility.
"""

from collections import defaultdict
import concurrent.futures
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
flags.DEFINE_integer(
    'parallelism',
    2,
    'Maximum number of concurrent stat_var_processor worker processes.',
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
    # Sort largest files first so long-running shards start immediately.
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
    """Merges shard CSV files atomically into final_csv_path, keeping a single header."""
    total_rows = 0
    wrote_header = False
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
                        out_f.write(line)
                        total_rows += 1
        os.replace(tmp_path, final_csv_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    return total_rows


def _counter_aggregation_mode(key: str) -> str:
    """Returns how a stat_var_processor counter key should be aggregated across shards."""
    lower = key.lower()
    if lower == 'existing-statvars-from-mcf' or lower.startswith('existing-'):
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
    input_files = _expand_input_files(_FLAGS.input_data)
    if not input_files:
        raise RuntimeError(f'No input files matched: {_FLAGS.input_data}')

    output_path = os.path.abspath(_FLAGS.output_path)
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    shards_tmp_dir = tempfile.mkdtemp(prefix='.shards_', dir=output_dir)
    max_workers = max(
        1, min(_FLAGS.parallelism, len(input_files),
               os.cpu_count() or 1))
    logging.info(
        'Processing %d input files across %d parallel workers...',
        len(input_files),
        max_workers,
    )

    try:
        local_statvar_mcf = _prepare_local_statvar_mcf(
            _FLAGS.existing_statvar_mcf, shards_tmp_dir)
        shard_prefixes: list[str] = []
        shard_counters: list[str] = []
        futures = []

        with concurrent.futures.ThreadPoolExecutor(
                max_workers=max_workers) as executor:
            for idx, input_file in enumerate(input_files):
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
                    tmcf_text = f.read().replace(shard_table, table_name)
                _atomic_write_text(final_tmcf, tmcf_text)
                break

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
