# Copyright 2026 Google LLC
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
"""Preprocesses raw OECD Regional Education SDMX CSV data before StatVar processing.

Steps performed:
1. Finds the latest raw SDMX CSV (e.g., `A.........`) in `gcs_output/source_files/`
   and retains the original file for provenance.
2. Filters out empty `OBS_VALUE` rows and standard error rows (`STATISTICAL_OPERATION == 'SE'`).
3. Resolves `REF_AREA` codes using `oecd_regional_education_places_resolved.csv`,
   projects the 7 required columns into `oecd_regional_education_data.csv`, and logs
   unmapped places to `counters/unresolved_places.csv`.

Features not directly supported by `stat_var_processor.py`:
- Dynamic filename discovery (`A.........`) while preserving the raw source file.
- Disambiguating duplicate `Education level` column headers in the raw SDMX
  `csvfilewithlabels` format.
- Logging unmapped place codes to a separate counter file without failing the job,
  plus a fail-fast check if 100% of rows are dropped.
"""
import csv
import os
import re

try:
    from absl import logging
    logging.set_verbosity(logging.INFO)
except ImportError:
    import logging as std_logging

    class _CompatLogger:
        def __init__(self):
            self._logger = std_logging.getLogger(__name__)
            self._logger.setLevel(std_logging.INFO)
            if not self._logger.handlers:
                handler = std_logging.StreamHandler()
                handler.setFormatter(
                    std_logging.Formatter('%(levelname)s:%(message)s'))
                self._logger.addHandler(handler)

        def set_verbosity(self, level):
            self._logger.setLevel(level)

        def info(self, msg, *args, **kwargs):
            self._logger.info(msg, *args, **kwargs)

        def warning(self, msg, *args, **kwargs):
            self._logger.warning(msg, *args, **kwargs)

        def error(self, msg, *args, **kwargs):
            self._logger.error(msg, *args, **kwargs)

    logging = _CompatLogger()
    logging.set_verbosity(std_logging.INFO)


def preprocess(base_path=None):
    if base_path is None:
        base_path = os.path.dirname(os.path.abspath(__file__))

def rename_target_file(base_path='.'):
    folder_name = 'gcs_output/source_files'
    target_folder = os.path.join(base_path, folder_name)
    counters_folder = os.path.join(base_path, 'counters')
    os.makedirs(counters_folder, exist_ok=True)
    output_folder = os.path.join(base_path, 'output')
    os.makedirs(output_folder, exist_ok=True)

    places_resolved_file = os.path.join(
        base_path, 'oecd_regional_education_places_resolved.csv')
    valid_places = {}
    if not os.path.isfile(places_resolved_file):
        raise FileNotFoundError(
            f"Places resolved file not found: {places_resolved_file}. "
            "Aborting preprocessing to prevent silent data drop.")

    with open(places_resolved_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dcid = row.get('dcid', '').strip()
            place_name = row.get('place_name', '').strip()
            if dcid and place_name:
                if not dcid.startswith('dcid:'):
                    dcid = f'dcid:{dcid}'
                valid_places[place_name] = dcid

    if not valid_places:
        raise ValueError(
            f"No valid places loaded from {places_resolved_file}. "
            "Aborting preprocessing to prevent silent data drop.")

    logging.info(f"Loaded {len(valid_places)} valid places from {places_resolved_file}")

    if not os.path.isdir(target_folder):
        logging.error(f"Folder '{folder_name}' not found in '{base_path}'")
        raise FileNotFoundError(f"Folder '{folder_name}' not found in '{base_path}'")
    try:
        # Check if the folder exists
        if not os.path.isdir(target_folder):
            logging.fatal(f"Folder '{folder_name}' not found in '{base_path}'"
                         )  # Changed to error for non-fatal issues
            return  # Exit function if folder not found

    pattern = re.compile(r'^(?:A.*|OECD.*|.*REG_EDU.*)$', re.IGNORECASE)
    candidate_files = [
        f for f in os.listdir(target_folder)
        if os.path.isfile(os.path.join(target_folder, f))
        and not f.startswith('.')
        and f not in ('oecd_regional_education_data.csv', 'filtered_tmp.csv')
        and pattern.match(f)
    ]
    if candidate_files:
        candidate_files.sort(
            key=lambda f: os.path.getmtime(os.path.join(target_folder, f)),
            reverse=True
        )
        raw_file = candidate_files[0]
        if len(candidate_files) > 1:
            logging.info(
                f"Found multiple candidate source files: {candidate_files}. "
                f"Selecting newest file '{raw_file}'.")
    else:
        raw_file = None

    target_csv = os.path.join(target_folder, 'oecd_regional_education_data.csv')
    unmapped_log_path = os.path.join(counters_folder, 'unresolved_places.csv')
        # Search through files in the folder
        for filename in os.listdir(target_folder):
            logging.info(f"Checking file: {filename}")
            if pattern.match(filename):
                old_path = os.path.join(target_folder, filename)
                new_path = os.path.join(target_folder,
                                        'oecd_regional_education_data.csv')

    if raw_file:
        src_path = os.path.join(target_folder, raw_file)
        tmp_path = os.path.join(target_folder, 'filtered_tmp.csv')
        logging.info(f"Filtering '{raw_file}' into 'oecd_regional_education_data.csv'...")
        _filter_csv(src_path, tmp_path, valid_places, unmapped_log_path=unmapped_log_path)
        os.replace(tmp_path, target_csv)
        # Preserve original downloaded raw file in GCS source_files per Data Commons guidelines
        logging.info(f"Retained raw downloaded source file at '{src_path}'.")
        logging.info("Preprocessing and filtering completed successfully.")
    elif os.path.isfile(target_csv) and valid_places:
        tmp_path = os.path.join(target_folder, 'filtered_tmp.csv')
        logging.info(f"Checking and filtering existing '{target_csv}'...")
        _filter_csv(target_csv, tmp_path, valid_places, unmapped_log_path=unmapped_log_path)
        os.replace(tmp_path, target_csv)
        logging.info("Filtering completed successfully.")
    else:
        logging.error("No matching source data file found to process.")
        raise FileNotFoundError(
            f"No candidate raw data file found to process in '{target_folder}'.")


def _filter_csv(src_path: str, dst_path: str, valid_places: dict, unmapped_log_path: str = None):
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
                    out_row = [row[idx] if len(row) > idx else '' for idx in col_indices]
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

        logging.info(f"Filtered source data: {kept} rows kept, {dropped} rows dropped.")
        if unmapped_places:
            logging.warning(
                f"Encountered {len(unmapped_places)} unmapped REF_AREA codes. "
                f"Sample unmapped places: {sorted(list(unmapped_places))[:25]}")
            if unmapped_log_path:
                try:
                    os.makedirs(os.path.dirname(unmapped_log_path), exist_ok=True)
                    with open(unmapped_log_path, 'w', encoding='utf-8', newline='') as uf:
                        u_writer = csv.writer(uf)
                        u_writer.writerow(['unmapped_ref_area'])
                        for p in sorted(unmapped_places):
                            u_writer.writerow([p])
                    logging.info(
                        f"Wrote {len(unmapped_places)} unmapped places to {unmapped_log_path}")
                except Exception as e:
                    logging.warning(f"Failed to write unmapped places log: {e}")


if __name__ == '__main__':
    preprocess()
                    os.rename(old_path, new_path)
                    logging.info(
                        f"Renamed '{filename}' to 'oecd_regional_education_data.csv'"
                    )
                    renamed = True
                except PermissionError:
                    logging.warning(
                        f"Permission denied while renaming '{filename}'."
                    )  # Changed to warning
                except OSError as e:
                    logging.fatal(f"OS error while renaming '{filename}': {e}"
                                 )  # Changed to error
                break  # Rename only the first match

        if not renamed:
            logging.info("No matching file starting with 'A' found to rename.")

    except FileNotFoundError as e:
        # This block might not be hit if caught earlier, but good for other FileNotFoundError
        logging.fatal(f"File system error: {e}")
    except PermissionError as e:
        # This block might not be hit if caught earlier, but good for other PermissionError
        logging.fatal(f"Global permission error: {e}")
    except Exception as e:
        logging.fatal(f"An unexpected critical error occurred: {e}"
                     )  # Changed to critical for unexpected errors


# Run it
rename_target_file()
