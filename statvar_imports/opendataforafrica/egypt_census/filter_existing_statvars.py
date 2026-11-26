# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Filters generated *_stat_vars.mcf files against a local existing_statvar_mcf."""

import argparse
import glob
import logging
import os
import re
import tempfile

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_SINGLE_VALUED_SV_PROPS = frozenset(
    ('name', 'alternateName', 'measurementDenominator', 'description'))
_MULTI_QUOTED_RE = re.compile(r'"\s*,\s*"')
_UNEXPANDED_REF_RE = re.compile(r'\{@?[A-Za-z0-9_]+\}')


def _strip_inline_comment(val: str) -> str:
    """Strips trailing unquoted '#' comments from an MCF value."""
    in_quotes = False
    for idx, ch in enumerate(val):
        if ch == '"':
            in_quotes = not in_quotes
        elif ch == '#' and not in_quotes:
            return val[:idx]
    return val


def _strip_ns(val: str) -> str:
    val = _strip_inline_comment(val).strip().strip('"').strip()
    for prefix in ('dcid:', 'dcs:', 'schema:'):
        if val.startswith(prefix):
            return val[len(prefix):].strip()
    return val


def _resolve_canonical_dcid(cur_node: str | None,
                            cur_dcid: str | None) -> str | None:
    """Resolves a block's canonical DCID, letting dcid: override local Node:."""
    if cur_dcid:
        return cur_dcid
    if cur_node and not cur_node.startswith(
        ('l:', 'E:')) and '->' not in cur_node:
        return cur_node
    return None


def load_existing_dcids(mcf_path: str) -> set[str]:
    """Extracts all defined node DCIDs from an MCF file."""
    if not os.path.isfile(mcf_path):
        raise FileNotFoundError(f'Existing StatVar MCF not found: {mcf_path}')
    dcids: set[str] = set()
    cur_node: str | None = None
    cur_dcid: str | None = None
    with open(mcf_path, encoding='utf-8') as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line or line.startswith('#'):
                continue
            if line.startswith('Node:'):
                canonical_dcid = _resolve_canonical_dcid(cur_node, cur_dcid)
                if canonical_dcid:
                    dcids.add(canonical_dcid)
                cur_node = _strip_ns(line.split(':', 1)[1])
                cur_dcid = None
            elif line.startswith('dcid:'):
                cur_dcid = _strip_ns(line.split(':', 1)[1])
        canonical_dcid = _resolve_canonical_dcid(cur_node, cur_dcid)
        if canonical_dcid:
            dcids.add(canonical_dcid)
    dcids.discard('')
    return dcids


def _validate_statvar_block(canonical_dcid: str | None, lines: list[str],
                            mcf_path: str) -> None:
    """Rejects duplicated or unexpanded metadata in a kept StatVar block."""
    seen_props: set[str] = set()
    node_label = canonical_dcid or '<unknown>'
    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped or stripped.startswith('#') or ':' not in stripped:
            continue
        prop, raw_val = stripped.split(':', 1)
        prop = prop.strip()
        if prop not in _SINGLE_VALUED_SV_PROPS:
            continue
        val = _strip_inline_comment(raw_val).strip()
        if prop in seen_props:
            raise ValueError(
                f'{mcf_path}: StatVar {node_label} has repeated {prop}: property'
            )
        seen_props.add(prop)
        if _MULTI_QUOTED_RE.search(val):
            raise ValueError(
                f'{mcf_path}: StatVar {node_label} has multi-valued {prop}: {val}'
            )
        if prop == 'measurementDenominator' and ',' in val:
            raise ValueError(
                f'{mcf_path}: StatVar {node_label} has multi-valued '
                f'measurementDenominator: {val}')
        if _UNEXPANDED_REF_RE.search(val):
            raise ValueError(
                f'{mcf_path}: StatVar {node_label} has unexpanded placeholder '
                f'in {prop}: {val}')


def filter_statvar_mcf_file(mcf_path: str,
                            existing_dcids: set[str]) -> tuple[int, int]:
    """Retains only MCF node blocks not present in existing_dcids; removes empty MCFs."""
    header_lines: list[str] = []
    blocks: list[tuple[str | None, list[str]]] = []
    cur_lines: list[str] = []
    cur_node: str | None = None
    cur_dcid: str | None = None

    with open(mcf_path, encoding='utf-8') as f:
        for raw_line in f:
            stripped = raw_line.strip()
            if stripped.startswith('Node:'):
                if cur_lines:
                    blocks.append(
                        (_resolve_canonical_dcid(cur_node,
                                                 cur_dcid), cur_lines))
                cur_lines = [raw_line]
                cur_node = _strip_ns(stripped.split(':', 1)[1])
                cur_dcid = None
            elif cur_node is None:
                if stripped.startswith('#'):
                    header_lines.append(raw_line)
            else:
                if stripped.startswith('dcid:'):
                    cur_dcid = _strip_ns(stripped.split(':', 1)[1])
                cur_lines.append(raw_line)
        if cur_lines:
            blocks.append((_resolve_canonical_dcid(cur_node,
                                                   cur_dcid), cur_lines))

    kept_blocks: list[list[str]] = []
    for canonical_dcid, lines in blocks:
        if canonical_dcid and canonical_dcid in existing_dcids:
            continue
        _validate_statvar_block(canonical_dcid, lines, mcf_path)
        kept_blocks.append(lines)
    dropped = len(blocks) - len(kept_blocks)
    if not kept_blocks:
        os.remove(mcf_path)
        return (0, dropped)

    out_dir = os.path.dirname(os.path.abspath(mcf_path))
    fd, tmp_path = tempfile.mkstemp(dir=out_dir, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as out_f:
            for hl in header_lines:
                out_f.write(hl)
            if header_lines:
                out_f.write('\n')
            for blk in kept_blocks:
                text = ''.join(blk).rstrip('\n') + '\n\n'
                out_f.write(text)
        os.replace(tmp_path, mcf_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    return (len(kept_blocks), dropped)


def filter_statvar_mcf_dir(statvar_mcf_dir: str,
                           existing_statvar_mcf: str) -> None:
    """Filters all *_stat_vars.mcf files in statvar_mcf_dir against existing_statvar_mcf."""
    if not os.path.isdir(statvar_mcf_dir):
        raise FileNotFoundError(
            f'StatVar MCF directory not found: {statvar_mcf_dir}')
    existing_dcids = load_existing_dcids(existing_statvar_mcf)
    pattern = os.path.join(statvar_mcf_dir, '*_stat_vars.mcf')
    mcf_files = sorted(glob.glob(pattern))
    total_kept = 0
    total_dropped = 0
    for mcf_file in mcf_files:
        kept, dropped = filter_statvar_mcf_file(mcf_file, existing_dcids)
        total_kept += kept
        total_dropped += dropped
        logging.info('Filtered %s: kept=%d new StatVars, dropped=%d existing',
                     mcf_file, kept, dropped)
    logging.info(
        'Completed filtering %d files against %d existing StatVars (kept=%d, dropped=%d)',
        len(mcf_files), len(existing_dcids), total_kept, total_dropped)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
    )
    parser = argparse.ArgumentParser(
        description=
        'Filter generated *_stat_vars.mcf files against existing_statvar_mcf.')
    parser.add_argument(
        '--statvar_mcf_dir',
        default=os.path.join(_MODULE_DIR, 'output'),
        help='Directory containing *_stat_vars.mcf files (default: output)',
    )
    parser.add_argument(
        '--existing_statvar_mcf',
        required=True,
        help='Path to local existing_statvar_mcf file',
    )
    args = parser.parse_args()
    filter_statvar_mcf_dir(args.statvar_mcf_dir, args.existing_statvar_mcf)


if __name__ == '__main__':
    main()
