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
"""Converts Egypt Census SDMX XML files to Data Commons CSV format using sdmx1."""

import argparse
import contextlib
from decimal import Decimal
from decimal import InvalidOperation
import glob
import io
import logging
import os
import sys
import tempfile
import xml.etree.ElementTree as ET

import pandas as pd
import sdmx

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

EXPECTED_TABLES = (
    'actytif',
    'behvqtc',
    'bluhqme',
    'cjczlcd',
    'lxoyale',
    'mptocre',
    'pqpump',
    'szfufmb',
    'txbrrac',
    'ujtdaag',
    'ulouknf',
    'viytqvf',
    'wcssteb',
    'wtxyghf',
    'xovpotd',
    'zkjifzd',
    'zpdksog',
)


def _local_tag(tag: str) -> str:
    """Strips XML namespace URI from an element tag."""
    return tag.split('}')[-1]


def _strip_ns(attrib: dict[str, str]) -> dict[str, str]:
    """Strips XML namespace prefixes from attribute keys."""
    return {k.split('}')[-1]: v for k, v in attrib.items()}


def _format_obs_value(val: object) -> object:
    """Formats scientific-notation numeric values as plain decimal strings."""
    if pd.isna(val):
        return val
    s = str(val).strip()
    if 'e' not in s.lower():
        return val
    try:
        dec = Decimal(s)
        formatted = format(dec, 'f')
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        if formatted in ('', '-0', '+0'):
            return '0'
        return formatted
    except InvalidOperation:
        return val


def _normalize_obs_column(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes column names and expands scientific notation in OBS_VALUE."""
    df = df.copy()
    df.columns = [str(c).lstrip('@').strip().upper() for c in df.columns]
    if 'OBS_VALUE' not in df.columns:
        if 'VALUE' in df.columns:
            df = df.rename(columns={'VALUE': 'OBS_VALUE'})
        elif '0' in df.columns:
            df = df.rename(columns={'0': 'OBS_VALUE'})
    if 'OBS_VALUE' in df.columns:
        df['OBS_VALUE'] = df['OBS_VALUE'].map(_format_obs_value)
    return df


def _to_normalized_df(obj: object) -> pd.DataFrame | None:
    """Converts a parsed sdmx1 DataFrame or Series into a normalized DataFrame."""
    if isinstance(obj, pd.DataFrame):
        if isinstance(obj.index, pd.MultiIndex) or obj.index.name is not None:
            df = obj.reset_index()
        else:
            df = obj.copy()
    elif hasattr(obj, 'reset_index'):
        df = obj.reset_index()
    else:
        return None
    if df.empty:
        return None
    return _normalize_obs_column(df)


def convert_sdmx_xml_to_dataframe(xml_path: str) -> pd.DataFrame:
    """Reads SDMX XML using sdmx1 and converts to a pandas DataFrame."""
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f'XML file not found: {xml_path}')

    # 1. Read SDMX XML with sdmx1
    parsed = None
    try:
        with open(xml_path, 'rb') as f:
            xml_bytes = f.read()
        with contextlib.redirect_stdout(
                io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            msg = sdmx.read_sdmx(io.BytesIO(xml_bytes), format='XML')
            parsed = sdmx.to_pandas(msg)
    except Exception as e:
        logging.info('sdmx parser skipped for %s (%s); attempting fallback',
                     xml_path, e)

    if parsed is not None:
        if isinstance(parsed, dict):
            dfs = []
            for v in parsed.values():
                norm_v = _to_normalized_df(v)
                if norm_v is not None:
                    dfs.append(norm_v)
            if dfs:
                return pd.concat(dfs, ignore_index=True)
        else:
            norm_df = _to_normalized_df(parsed)
            if norm_df is not None:
                return norm_df

    # 2. Fallback path for headerless / structure-less XML files
    try:
        root = ET.parse(xml_path).getroot()
    except ET.ParseError as e:
        logging.error('Failed to parse XML file %s: %s', xml_path, e)
        raise ValueError(f'Failed to parse XML file {xml_path}: {e}') from e
    rows = []
    for elem in root.iter():
        tag = _local_tag(elem.tag)
        if tag == 'Series':
            series_attrib = _strip_ns(elem.attrib)
            for child in elem:
                if _local_tag(child.tag) == 'Obs':
                    obs_attrib = _strip_ns(child.attrib)
                    rows.append({**series_attrib, **obs_attrib})
        elif tag == 'DataSet':
            for child in elem:
                if _local_tag(child.tag) == 'Obs':
                    obs_attrib = _strip_ns(child.attrib)
                    rows.append(obs_attrib)

    if not rows:
        raise ValueError(f'No <Series> or <Obs> records found in {xml_path}')

    df = pd.DataFrame(rows)
    return _normalize_obs_column(df)


def convert_sdmx_xml_to_csv(xml_path: str, output_csv_path: str) -> None:
    """Converts an SDMX XML file to a CSV file atomically."""
    df = convert_sdmx_xml_to_dataframe(xml_path)
    out_dir = os.path.dirname(os.path.abspath(output_csv_path))
    os.makedirs(out_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=out_dir, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='') as f:
            df.to_csv(f, index=False)
        os.replace(tmp_path, output_csv_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise
    logging.info('Converted %s -> %s (%d rows)', xml_path, output_csv_path,
                 len(df))


def _verify_expected_csvs(output_dir: str) -> None:
    """Verifies that all 17 expected CSV tables exist and are non-empty."""
    for table_id in EXPECTED_TABLES:
        csv_file = os.path.join(output_dir, f'{table_id}.csv')
        if not os.path.isfile(csv_file) or os.path.getsize(csv_file) == 0:
            logging.error('Missing or empty CSV file: %s', csv_file)
            sys.exit(1)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
    )
    parser = argparse.ArgumentParser(
        description='Convert Egypt Census SDMX XML files to CSV format.')
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        '--input_file',
        default=None,
        help='Path to single SDMX XML file (e.g. xml/actytif.xml)',
    )
    source_group.add_argument(
        '--xml_dir',
        default=None,
        help='Path to directory containing SDMX XML files to convert',
    )
    parser.add_argument(
        '--output_dir',
        default=os.path.join(_MODULE_DIR, 'input_files'),
        help=
        'Directory where output CSVs should be written (default: input_files)',
    )
    parser.add_argument(
        '--allow_empty_xml_dir',
        action='store_true',
        help='Allow --xml_dir to have no .xml files when CSVs are pre-staged',
    )
    parser.add_argument(
        '--verify_expected_tables',
        action='store_true',
        help='Verify all 17 expected Egypt_Census CSV files exist in output_dir',
    )

    args = parser.parse_args()

    if args.input_file:
        resolved_input = os.path.abspath(args.input_file)
        if not os.path.isfile(resolved_input):
            logging.error('Input file not found: %s', resolved_input)
            sys.exit(1)
        base_name = os.path.splitext(os.path.basename(resolved_input))[0]
        out_csv = os.path.join(args.output_dir, f'{base_name}.csv')
        convert_sdmx_xml_to_csv(resolved_input, out_csv)
        if args.verify_expected_tables:
            _verify_expected_csvs(args.output_dir)
        return

    resolved_xml_dir = os.path.abspath(args.xml_dir)
    xml_files = glob.glob(os.path.join(resolved_xml_dir, '*.xml'))
    if not xml_files:
        if not args.allow_empty_xml_dir:
            logging.error('No XML files found in directory: %s',
                          resolved_xml_dir)
            sys.exit(1)
        logging.info(
            'No XML files found in %s; skipping XML conversion (--allow_empty_xml_dir)',
            resolved_xml_dir,
        )
    else:
        for xf in sorted(xml_files):
            base_name = os.path.splitext(os.path.basename(xf))[0]
            out_csv = os.path.join(args.output_dir, f'{base_name}.csv')
            convert_sdmx_xml_to_csv(xf, out_csv)

    if args.verify_expected_tables:
        _verify_expected_csvs(args.output_dir)


if __name__ == '__main__':
    main()
