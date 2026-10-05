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
"""Converts and manages Kenya Census SDMX/XML data from Open Data for Africa.

Datasets:
  dlrrjxg, egdxgkd, emxkej, fwjfdnc, gxbucsd, ixdvqrf,
  rsfzlbg, srricmg, tdxdksf, vdbvyfd, welrttb, xszlbb

Usage:
    # 1. Convert a single XML file to input_files/<dataset_id>.csv:
    python3 download.py --input_file xml/egdxgkd.xml

    # 2. Batch convert all XML files in a folder:
    python3 download.py --xml_dir xml/

    # 3. Pull latest files from GCS:
    python3 download.py --from_gcs
"""

import argparse
import glob
import logging
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
)

ALL_DATASETS = [
    'dlrrjxg',
    'egdxgkd',
    'emxkej',
    'fwjfdnc',
    'gxbucsd',
    'ixdvqrf',
    'rsfzlbg',
    'srricmg',
    'tdxdksf',
    'vdbvyfd',
    'welrttb',
    'xszlbb',
]

GCS_BUCKET_DIR = "gs://unresolved_mcf/opendataforafrica/kenya_census/input_files"


def convert_sdmx_xml_to_dataframe(xml_path: str) -> pd.DataFrame:
    """Parses OpenDataForAfrica StructureSpecificData SDMX XML into a DataFrame."""
    try:
        root = ET.parse(xml_path).getroot()
    except Exception as e:
        logging.error("Failed to parse XML file %s: %s", xml_path, e)
        raise ValueError(f"Failed to parse XML file {xml_path}: {e}") from e

    rows = []
    for elem in root.iter():
        if elem.tag.endswith('Series'):
            # Extract attributes of Series (e.g. SEX, GRADE, etc.), stripping namespace
            series_attrib = {k.split('}')[-1]: v for k, v in elem.attrib.items()}
            for child in elem:
                if child.tag.endswith('Obs'):
                    obs_attrib = {k.split('}')[-1]: v for k, v in child.attrib.items()}
                    row = {**series_attrib, **obs_attrib}
                    rows.append(row)

    if not rows:
        logging.error("No <Series> or <Obs> records found in %s", xml_path)
        raise ValueError(f"No <Series> or <Obs> records found in {xml_path}")

    df = pd.DataFrame(rows)

    # Standardize column names (strip '@' if present, uppercase)
    cleaned_cols = [c.lstrip('@').strip().upper() for c in df.columns]
    df.columns = cleaned_cols

    return df


def process_xml_file(xml_path: str, output_csv_path: str) -> pd.DataFrame:
    """Converts an SDMX XML file to a CSV matching the StatVar importer schema atomically."""
    logging.info("Processing: %s", xml_path)
    df = convert_sdmx_xml_to_dataframe(xml_path)

    out_dir = os.path.dirname(os.path.abspath(output_csv_path))
    os.makedirs(out_dir, exist_ok=True)

    with tempfile.NamedTemporaryFile('w', dir=out_dir, delete=False, suffix='.tmp') as tmp_file:
        tmp_path = tmp_file.name

    try:
        df.to_csv(tmp_path, index=False)
        if os.path.getsize(tmp_path) == 0:
            raise IOError(f"Output temporary file {tmp_path} is empty after writing.")
        os.replace(tmp_path, output_csv_path)
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        logging.error("Failed writing output CSV %s: %s", output_csv_path, e)
        raise e

    logging.info("  -> Generated: %s (%d rows, columns: %s)",
                 output_csv_path, len(df), list(df.columns))
    return df


def pull_from_gcs(output_dir: str):
    """Copies raw census input files from GCS to local input_files/ directory."""
    os.makedirs(output_dir, exist_ok=True)
    cmd = ["gcloud", "storage", "cp", "--recursive", f"{GCS_BUCKET_DIR}/*", output_dir]
    logging.info("Running: %s", " ".join(cmd))
    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        logging.error("Failed to pull files from GCS: %s", e)
        raise e
    logging.info("Successfully pulled files from GCS to %s", output_dir)


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser(
        description=(
            "Convert OpenDataForAfrica Kenya Census SDMX XML files to Data Commons CSV format."
        )
    )
    parser.add_argument(
        '--input_file',
        default=None,
        help="Path to an individual XML file (e.g. xml/egdxgkd.xml)",
    )
    parser.add_argument(
        '--xml_dir',
        default=None,
        help="Path to directory containing XML files to batch convert (e.g. xml/)",
    )
    parser.add_argument(
        '--output_dir',
        default=os.path.join(script_dir, 'input_files'),
        help="Directory where output CSVs should be written (default: input_files/)",
    )
    parser.add_argument(
        '--from_gcs',
        action='store_true',
        help="Download latest input files from GCS bucket",
    )

    args = parser.parse_args()

    if args.from_gcs:
        pull_from_gcs(args.output_dir)
        return

    if args.input_file:
        resolved_input = os.path.abspath(args.input_file)
        base_name = os.path.splitext(os.path.basename(resolved_input))[0]
        out_csv = os.path.join(args.output_dir, f"{base_name}.csv")
        process_xml_file(resolved_input, out_csv)
        return

    if args.xml_dir:
        resolved_xml_dir = os.path.abspath(args.xml_dir)
        xml_files = glob.glob(os.path.join(resolved_xml_dir, "*.xml"))
        if not xml_files:
            logging.error("No XML files found in directory: %s", resolved_xml_dir)
            sys.exit(1)

        logging.info("Found %d XML file(s) in %s", len(xml_files), resolved_xml_dir)
        for xf in sorted(xml_files):
            base_name = os.path.splitext(os.path.basename(xf))[0]
            out_csv = os.path.join(args.output_dir, f"{base_name}.csv")
            process_xml_file(xf, out_csv)
        return

    parser.print_help()


if __name__ == '__main__':
    main()
