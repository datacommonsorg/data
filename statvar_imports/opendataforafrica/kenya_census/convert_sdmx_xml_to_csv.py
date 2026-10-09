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
"""Converts Kenya Census SDMX XML files to Data Commons CSV format using sdmx1."""

import argparse
import contextlib
import glob
import io
import logging
import os
import sys
import xml.etree.ElementTree as ET
import pandas as pd
import sdmx

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)


def convert_sdmx_xml_to_dataframe(xml_path: str) -> pd.DataFrame:
    """Reads SDMX XML using sdmx1 and converts to a pandas DataFrame."""
    if not os.path.exists(xml_path):
        raise FileNotFoundError(f'XML file not found: {xml_path}')

    # 1. Read SDMX XML with sdmx1
    try:
        with open(xml_path, 'rb') as f:
            xml_bytes = f.read()
        with contextlib.redirect_stdout(
                io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            msg = sdmx.read_sdmx(io.BytesIO(xml_bytes), format='XML')
            parsed = sdmx.to_pandas(msg)

        if isinstance(parsed, dict):
            dfs = [
                v.reset_index() if hasattr(v, 'reset_index') else v
                for v in parsed.values()
            ]
            df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
        elif hasattr(parsed, 'reset_index'):
            df = parsed.reset_index()
        elif isinstance(parsed, pd.DataFrame):
            df = parsed
        else:
            df = None

        if df is not None and not df.empty:
            df.columns = [
                str(c).lstrip('@').strip().upper() for c in df.columns
            ]
            if 'OBS_VALUE' not in df.columns:
                if 'VALUE' in df.columns:
                    df.rename(columns={'VALUE': 'OBS_VALUE'}, inplace=True)
                elif 0 in df.columns or '0' in df.columns:
                    df.rename(columns={
                        0: 'OBS_VALUE',
                        '0': 'OBS_VALUE'
                    },
                              inplace=True)
            return df
    except Exception as e:
        logging.info('sdmx parser skipped for %s (%s); attempting fallback',
                     xml_path, e)

    # 2. Fallback path for headerless / structure-less XML files
    root = ET.parse(xml_path).getroot()
    rows = []
    for elem in root.iter():
        if elem.tag.endswith('Series'):
            series_attrib = {
                k.split('}')[-1]: v for k, v in elem.attrib.items()
            }
            for child in elem:
                if child.tag.endswith('Obs'):
                    obs_attrib = {
                        k.split('}')[-1]: v for k, v in child.attrib.items()
                    }
                    rows.append({**series_attrib, **obs_attrib})
        elif elem.tag.endswith('DataSet'):
            for child in elem:
                if child.tag.endswith('Obs'):
                    obs_attrib = {
                        k.split('}')[-1]: v for k, v in child.attrib.items()
                    }
                    rows.append(obs_attrib)

    if not rows:
        raise ValueError(f'No <Series> or <Obs> records found in {xml_path}')

    df = pd.DataFrame(rows)
    df.columns = [str(c).lstrip('@').strip().upper() for c in df.columns]
    if 'OBS_VALUE' not in df.columns:
        if 'VALUE' in df.columns:
            df.rename(columns={'VALUE': 'OBS_VALUE'}, inplace=True)
        elif 0 in df.columns or '0' in df.columns:
            df.rename(columns={0: 'OBS_VALUE', '0': 'OBS_VALUE'}, inplace=True)
    return df


def convert_sdmx_xml_to_csv(xml_path: str, output_csv_path: str) -> None:
    """Converts an SDMX XML file to a CSV file."""
    df = convert_sdmx_xml_to_dataframe(xml_path)
    out_dir = os.path.dirname(os.path.abspath(output_csv_path))
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(output_csv_path, index=False)
    logging.info('Converted %s -> %s (%d rows)', xml_path, output_csv_path,
                 len(df))


def main():
    parser = argparse.ArgumentParser(
        description='Convert Kenya Census SDMX XML files to CSV format.')
    parser.add_argument(
        '--input_file',
        default=None,
        help='Path to single SDMX XML file (e.g. xml/egdxgkd.xml)',
    )
    parser.add_argument(
        '--xml_dir',
        default=None,
        help='Path to directory containing SDMX XML files to convert',
    )
    parser.add_argument(
        '--output_dir',
        default='input_files',
        help=
        'Directory where output CSVs should be written (default: input_files)',
    )

    args = parser.parse_args()

    if not args.input_file and not args.xml_dir:
        parser.error('Must specify either --input_file or --xml_dir')

    if args.input_file:
        resolved_input = os.path.abspath(args.input_file)
        if not os.path.isfile(resolved_input):
            logging.error('Input file not found: %s', resolved_input)
            sys.exit(1)
        base_name = os.path.splitext(os.path.basename(resolved_input))[0]
        out_csv = os.path.join(args.output_dir, f'{base_name}.csv')
        convert_sdmx_xml_to_csv(resolved_input, out_csv)
        return

    if args.xml_dir:
        resolved_xml_dir = os.path.abspath(args.xml_dir)
        xml_files = glob.glob(os.path.join(resolved_xml_dir, '*.xml'))
        if not xml_files:
            logging.error('No XML files found in directory: %s',
                          resolved_xml_dir)
            sys.exit(1)
        for xf in sorted(xml_files):
            base_name = os.path.splitext(os.path.basename(xf))[0]
            out_csv = os.path.join(args.output_dir, f'{base_name}.csv')
            convert_sdmx_xml_to_csv(xf, out_csv)


if __name__ == '__main__':
    main()
