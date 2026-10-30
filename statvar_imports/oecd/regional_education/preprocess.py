# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Preprocesses raw OECD Regional Education data before stat_var_processor execution.

1. Locates the downloaded raw source data file in gcs_output/source_files/
   and writes the cleaned output to oecd_regional_education_data.csv while
   retaining the original raw downloaded file for GCS archiving.
2. Filters out rows whose REF_AREA is not present in
   oecd_regional_education_places_resolved.csv to prevent unresolved place
   counters and warnings during StatVar processing.
3. Strips unused columns so only required columns are passed downstream,
   avoiding noisy unmapped column value counters.
"""

import csv
import os
import re
from absl import logging

logging.set_verbosity(logging.INFO)


def preprocess(base_path: str = None):
    """Preprocesses raw OECD Regional Education data before stat_var_processor execution.

    1. Locates the downloaded raw source data file in gcs_output/source_files/
       and writes the cleaned output to oecd_regional_education_data.csv while
       retaining the original raw downloaded file for GCS archiving.
    2. Filters out rows whose REF_AREA is not present in
       oecd_regional_education_places_resolved.csv to prevent unresolved place
       counters and warnings during StatVar processing.
    3. Strips unused columns so only required columns are passed downstream,
       avoiding noisy unmapped column value counters.

    Args:
        base_path: Optional base directory path. Defaults to the directory
            containing this script.

    Raises:
        FileNotFoundError: If required input directories, places_resolved file,
            or candidate raw data files are missing.
        PermissionError: If file system permissions prevent reading or writing.
        ValueError: If places_resolved or filtered output is empty, or required
            columns are missing.
    """
    if base_path is None:
        base_path = os.path.dirname(os.path.abspath(__file__))

    target_folder = os.path.join(base_path, 'gcs_output', 'source_files')
    places_resolved_file = os.path.join(
        base_path, 'oecd_regional_education_places_resolved.csv')
    target_csv = os.path.join(target_folder, 'oecd_regional_education_data.csv')
    unmapped_log_path = os.path.join(base_path, 'counters',
                                     'unresolved_places.csv')

    if not os.path.exists(target_folder):
        logging.error(f"Target folder not found: {target_folder}")
        raise FileNotFoundError(f"Target folder not found: {target_folder}")

    if not os.path.isdir(target_folder):
        logging.error(
            f"Target path exists, but is not a directory: {target_folder}")
        raise NotADirectoryError(
            f"Target path exists, but is not a directory: {target_folder}")

    if not os.path.isfile(places_resolved_file):
        logging.error(f"Places resolved file not found: {places_resolved_file}")
        raise FileNotFoundError(
            f"Places resolved file not found: {places_resolved_file}")

    valid_places = {}
    with open(places_resolved_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            place_name = row.get('place_name', '').strip()
            dcid = row.get('dcid', '').strip()
            if place_name and dcid:
                if not dcid.startswith('dcid:'):
                    dcid = f"dcid:{dcid}"
                valid_places[place_name] = dcid

    if not valid_places:
        raise ValueError(f"No valid places loaded from {places_resolved_file}. "
                         "Aborting preprocessing to prevent silent data drop.")

    logging.info(
        f"Loaded {len(valid_places)} valid places from {places_resolved_file}")

    src_path = None
    # Match OECD SDMX downloaded file names (e.g. 'A.........', 'OECD.CFE.EDS...',
    # or files containing 'REG_EDU') while excluding already processed/temp files.
    pattern = re.compile(r'^(?:A.*|OECD.*|.*REG_EDU.*)$', re.IGNORECASE)
    candidate_files = [
        f for f in os.listdir(target_folder)
        if os.path.isfile(os.path.join(target_folder, f)) and not f.startswith(
            '.') and f not in ('oecd_regional_education_data.csv',
                               'filtered_tmp.csv') and pattern.match(f)
    ]
    if candidate_files:
        candidate_files.sort(
            key=lambda f: os.path.getmtime(os.path.join(target_folder, f)),
            reverse=True)
        chosen_file = candidate_files[0]
        src_path = os.path.join(target_folder, chosen_file)
        logging.info(f"Found raw data file '{chosen_file}' to process.")

    if src_path and valid_places:
        tmp_path = os.path.join(target_folder, 'filtered_tmp.csv')
        _filter_csv(src_path,
                    tmp_path,
                    valid_places,
                    unmapped_log_path=unmapped_log_path)
        os.replace(tmp_path, target_csv)
        logging.info(f"Retained raw downloaded source file at '{src_path}'.")
        logging.info("Preprocessing and filtering completed successfully.")
    elif os.path.isfile(target_csv) and valid_places:
        tmp_path = os.path.join(target_folder, 'filtered_tmp.csv')
        logging.info(f"Checking and filtering existing '{target_csv}'...")
        _filter_csv(target_csv,
                    tmp_path,
                    valid_places,
                    unmapped_log_path=unmapped_log_path)
        os.replace(tmp_path, target_csv)
        logging.info("Filtering completed successfully.")
    else:
        logging.error("No matching source data file found to process.")
        raise FileNotFoundError(
            f"No candidate raw data file found to process in '{target_folder}'."
        )


def _filter_csv(src_path: str,
                dst_path: str,
                valid_places: dict,
                unmapped_log_path: str = None):
    required_columns = [
        'REF_AREA',
        'TIME_PERIOD',
        'UNIT_MULT',
        'SEX',
        'Education level',
        'AGE',
        'OBS_VALUE',
    ]
    with open(src_path, 'r', encoding='utf-8', errors='replace') as fin, \
         open(dst_path, 'w', encoding='utf-8', newline='') as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout)

        header = next(reader, None)
        if not header:
            raise ValueError(f"Source file '{src_path}' is empty.")

        missing_columns = [c for c in required_columns if c not in header]
        if missing_columns:
            raise ValueError(
                f"Source file '{src_path}' is missing required columns: "
                f"{missing_columns}. Available columns: {header}")

        col_indices = [header.index(c) for c in required_columns]
        ref_area_idx = header.index('REF_AREA')
        out_ref_area_idx = required_columns.index('REF_AREA')
        obs_val_idx = header.index('OBS_VALUE')
        stat_op_idx = (header.index('STATISTICAL_OPERATION')
                       if 'STATISTICAL_OPERATION' in header else None)

        writer.writerow(required_columns)

        kept = 0
        dropped = 0
        unmapped_places = set()
        for row in reader:
            if len(row) > ref_area_idx:
                # Skip rows with empty OBS_VALUE or ignored STATISTICAL_OPERATION (SE)
                if len(row) > obs_val_idx:
                    if not row[obs_val_idx].strip():
                        dropped += 1
                        continue
                if stat_op_idx is not None and len(row) > stat_op_idx:
                    if row[stat_op_idx].strip() == 'SE':
                        dropped += 1
                        continue

                ref_area = row[ref_area_idx].strip()
                # Handle both raw ref_area codes and already-prefixed dcid values
                clean_ref = ref_area
                resolved_dcid = valid_places.get(clean_ref)
                if not resolved_dcid and clean_ref.startswith('dcid:'):
                    # Check reverse lookup if already dcid-prefixed
                    resolved_dcid = clean_ref

                if resolved_dcid:
                    out_row = [
                        row[idx] if len(row) > idx else ''
                        for idx in col_indices
                    ]
                    out_row[out_ref_area_idx] = resolved_dcid
                    writer.writerow(out_row)
                    kept += 1
                else:
                    dropped += 1
                    unmapped_places.add(ref_area)
            else:
                dropped += 1

        if kept == 0:
            raise ValueError(
                f"Critical: All {dropped} rows in '{src_path}' were filtered out! "
                "Output CSV would be completely empty. "
                "Aborting preprocessing to prevent silent data drop.")

        logging.info(
            f"Filtered source data: {kept} rows kept, {dropped} rows dropped.")
        if unmapped_places:
            logging.warning(
                f"Encountered {len(unmapped_places)} unmapped REF_AREA codes. "
                f"Sample unmapped places: {sorted(list(unmapped_places))[:25]}")
            if unmapped_log_path:
                try:
                    os.makedirs(os.path.dirname(unmapped_log_path),
                                exist_ok=True)
                    with open(unmapped_log_path,
                              'w',
                              encoding='utf-8',
                              newline='') as uf:
                        u_writer = csv.writer(uf)
                        u_writer.writerow(['unmapped_ref_area'])
                        for p in sorted(unmapped_places):
                            u_writer.writerow([p])
                    logging.info(
                        f"Wrote {len(unmapped_places)} unmapped places to {unmapped_log_path}"
                    )
                except Exception as e:
                    logging.warning(f"Failed to write unmapped places log: {e}")


if __name__ == '__main__':
    preprocess()
