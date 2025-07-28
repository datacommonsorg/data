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
"""
This script downloads data files as specified in a JSON configuration file.

It is designed to be a robust and production-ready tool for data ingestion
pipelines. It supports downloading CSV and ZIP files, handling file renames,
and provides clear logging for all its actions.

Key Features:
- Reads download configurations from a JSON file.
- Accepts command-line arguments for specifying the import name, config file
  path, and a dry-run mode.
- Uses a utility script (`download_util_script.py`) for the actual download
  process.
- Logs all major actions, including download start, success, failure, and
  file renaming.
- Exits with a non-zero status code on error to signal failure in automated
  workflows.
- Supports a dry-run mode to preview actions without downloading files.

Example Usage:
  python3 download_script.py --import_name=CDC_StandardizedPrecipitationIndex \
    --config_file=import_configs.json

  python3 download_script.py --import_name=CDC_StandardizedPrecipitationEvapotranspirationIndex \
    --config_file=import_configs.json
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from absl import app, flags, logging

# Add the project root to the Python path for robust module imports
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(script_dir, '..', '..', '..'))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from util import download_util_script as download_util

FLAGS = flags.FLAGS

flags.DEFINE_string("import_name", None,
                    "The name of the import configuration to process.")
flags.DEFINE_string("config_file", "import_configs.json",
                    "Path to the JSON configuration file.")
flags.DEFINE_boolean(
    "dry_run", False,
    "If true, prints the actions that would be taken without downloading files."
)
flags.mark_flag_as_required("import_name")


def _get_inferred_filename(url: str, is_zip: bool) -> str:
    """
    Infers the filename from a URL, mimicking the logic in download_util_script.

    Args:
        url: The URL to infer the filename from.
        is_zip: A boolean indicating if the file is expected to be a zip archive.

    Returns:
        The inferred filename.
    """
    parsed_url = urllib.parse.urlparse(url)
    inferred_filename = os.path.basename(parsed_url.path)

    if not inferred_filename:
        return "downloaded_file"

    # The utility script appends '.xlsx' if there's no extension and it's not a zip.
    if "." not in inferred_filename and not is_zip:
        inferred_filename += ".xlsx"

    return inferred_filename


def process_downloads(import_name: str, config_file: str,
                      dry_run: bool) -> bool:
    """
    Processes the download for a given import name based on the config file.

    Args:
        import_name: The name of the import configuration to process.
        config_file: The path to the JSON configuration file.
        dry_run: If True, prints actions without downloading files.

    Returns:
        True if all downloads and operations succeed, False otherwise.
    """
    # Socrata query to get the total row count.
    record_count_query = "?$query=select%20count(*)%20as%20count"
    logging.info(f"Starting download process for import: '{import_name}'")

    try:
        with open(config_file, "r") as f:
            configs = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        logging.fatal(
            f"Failed to read or parse config file '{config_file}': {e}")
        return False

    import_config = next(
        (c for c in configs if c.get("import_name") == import_name), None)

    if not import_config:
        logging.fatal(
            f"Import name '{import_name}' not found in config file '{config_file}'."
        )
        return False

    for file_info in import_config.get("files", []):
        url = file_info.get("url")
        target_filename = file_info.get("input_file_name")

        if not url or not target_filename:
            logging.fatal(
                f"Skipping file config due to missing 'url' or 'input_file_name': {file_info}"
            )
            return False

        target_dir = os.path.dirname(target_filename) or "."
        is_zip = url.lower().endswith(".zip")
        full_url = url

        # For CSV files from data.cdc.gov, attempt to get the full dataset
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.path.endswith(
                ".csv") and parsed_url.hostname == "data.cdc.gov":
            count_url = url.replace(".csv", record_count_query)
            try:
                logging.info(
                    f"Attempting to get record count from: {count_url}")
                with urllib.request.urlopen(count_url, timeout=30) as response:
                    if response.status == 200:
                        count_data = json.loads(response.read().decode("utf-8"))
                        record_count = int(count_data[0]["count"])
                        full_url = f"{url}?$limit={record_count}&$offset=0"
                        logging.info(
                            f"Successfully retrieved record count: {record_count}. Full URL: {full_url}"
                        )
                    else:
                        logging.fatal(
                            f"Failed to get record count (HTTP {response.status}). Proceeding with base URL."
                        )
            except Exception as e:
                logging.fatal(
                    f"Could not get record count. Proceeding with base URL. Error: {e}"
                )

        logging.info(f"Processing file from URL: {full_url}")
        logging.info(f"Target local file: {target_filename}")

        if dry_run:
            logging.info(
                f"[DRY RUN] Would download from '{full_url}' to '{target_filename}'"
            )
            inferred_filename = _get_inferred_filename(url, is_zip)
            if inferred_filename != os.path.basename(target_filename):
                logging.info(
                    f"[DRY RUN] Would rename '{inferred_filename}' to '{os.path.basename(target_filename)}'"
                )
            continue

        os.makedirs(target_dir, exist_ok=True)

        success = download_util.download_file(url=full_url,
                                              output_folder=target_dir,
                                              unzip=is_zip)

        if not success:
            logging.fatal(f"Download failed for URL: {full_url}")
            return False

        logging.info(f"Successfully downloaded content from: {full_url}")

        # Use the original base URL to infer the filename, as the full URL has query params
        inferred_filename = _get_inferred_filename(url, is_zip)
        downloaded_path = os.path.join(target_dir, inferred_filename)
        target_path = os.path.join(target_dir,
                                   os.path.basename(target_filename))

        if downloaded_path != target_path:
            logging.info(
                f"Renaming downloaded file from '{inferred_filename}' to '{os.path.basename(target_filename)}'"
            )
            try:
                os.rename(downloaded_path, target_path)
                logging.info(f"Successfully renamed file to: {target_path}")
            except OSError as e:
                logging.fatal(
                    f"Failed to rename '{downloaded_path}' to '{target_path}': {e}"
                )
                return False

    return True


def main(argv):
    """
    Main function to parse arguments and initiate the download process.
    """
    if len(argv) > 1:
        raise app.UsageError("Too many command-line arguments.")

    if FLAGS.dry_run:
        logging.info("--- Starting DRY RUN mode ---")

    if not process_downloads(FLAGS.import_name, FLAGS.config_file,
                             FLAGS.dry_run):
        logging.fatal("The download process encountered errors.")
    else:
        logging.info("Download process completed successfully.")


if __name__ == "__main__":
    app.run(main)
