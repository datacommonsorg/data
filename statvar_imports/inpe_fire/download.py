import os
import time
import sys
import csv
import shutil
from pathlib import Path
import re 
from absl import logging


# Get the directory of the current script (download.py)
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define output directories
# Files will be downloaded into this base GCS output directory
_GCS_OUTPUT_BASE_DIR = os.path.join(_MODULE_DIR, 'gcs_output')

# Destination folder for the 27 downloaded files after merge (outside gcs_output)
_ARCHIVE_DOWNLOADED_FILES_DIR = os.path.join(_MODULE_DIR, 'downloaded_source_files_archive') 

# Base URL for the CSV files
BASE_URL = "https://terrabrasilis.dpi.inpe.br/queimadas/situacao-atual/media/estado/csv_estatisticas/historico_estado_"

# List of state names (used for generating URLs and validating completeness)
STATE_NAMES = [
    'acre', 'alagoas', 'amapa', 'amazonas', 'bahia', 'ceara', 'distrito_federal',
    'espirito_santo', 'goias', 'maranhao', 'mato_grosso', 'mato_grosso_do_sul',
    'minas_gerais', 'para', 'paraiba', 'parana', 'pernambuco', 'piaui',
    'rio_de_janeiro', 'rio_grande_do_norte', 'rio_grande_do_sul', 'rondonia',
    'roraima', 'santa_catarina', 'sao_paulo', 'sergipe', 'tocantins'
]

# Name for the merged output CSV file (stays in the script's root directory)
MERGED_CSV_FILE_NAME = os.path.join(_MODULE_DIR, "input.csv")

# Ensure util.download_util_script is accessible
parent_of_parent_dir = os.path.join(_MODULE_DIR, '..', '..')
sys.path.append(parent_of_parent_dir)

# Import download_file from the utility script
try:
    from util.download_util_script import download_file
except ImportError:
    logging.error("Could not import download_file. Make sure 'util/download_util_script.py' exists and is in the correct path.")
    sys.exit(1)


# --- Function: Merge CSV Files ---
def merge_csv_files(input_directory, output_filepath, expected_state_names):
    """
    Reads all CSV files from a given directory (assuming 'historico_estado_*.csv' format)
    and merges them into a single CSV file.

    Args:
        input_directory (str): The path to the directory containing the downloaded CSV files.
        output_filepath (str): The full path and filename for the merged CSV output.
        expected_state_names (list): A list of state names that are expected to be present
                                     (used for validation and consistent ordering).
    """
    logging.info(f"Starting CSV merge process. Output file: {output_filepath}")

    all_rows_to_write = []
    header_found = False

    # Create a mapping of found state files for ordered processing
    found_state_files = {}
    for filename in os.listdir(input_directory):
        match = re.match(r'historico_estado_(\w+)\.csv', filename)
        if match:
            state_name = match.group(1)
            found_state_files[state_name] = os.path.join(input_directory, filename)

    # Process files in the expected order of STATE_NAMES
    # This loop assumes all files are present due to the pre-merge check
    for state_name_key in expected_state_names:
        file_path = found_state_files.get(state_name_key)
        try:
            with open(file_path, mode='r', newline='', encoding='utf-8') as infile:
                reader = csv.reader(infile)

                try:
                    current_file_header = next(reader)
                except StopIteration:
                    logging.warning(f"File '{os.path.basename(file_path)}' is empty, skipping.")
                    continue

                if not header_found:
                    # Modify header for the first file
                    if len(current_file_header) > 0:
                        current_file_header[0] = 'year'
                    if len(current_file_header) < 1:
                        current_file_header.append('place')
                    else:
                        current_file_header.insert(1, 'place')

                    all_rows_to_write.append(current_file_header)
                    header_found = True
                    logging.info(f"Using and modifying header from {os.path.basename(file_path)}")
                else:
                    logging.debug(f"Skipping header from {os.path.basename(file_path)}")

                display_state_name = state_name_key.replace('_', ' ').title()

                for row in reader:
                    if len(row) < 1:
                        row.append(display_state_name)
                    else:
                        row.insert(1, display_state_name)
                    all_rows_to_write.append(row)

            logging.info(f"Successfully processed data from {os.path.basename(file_path)} for merging.")

        except UnicodeDecodeError:
            logging.error(f"Encoding error reading {os.path.basename(file_path)}. Please check file encoding. Skipping this file.")
        except csv.Error as e:
            logging.error(f"CSV parsing error in {os.path.basename(file_path)}: {e}. Skipping this file.")
        except Exception as e:
            logging.error(f"An unexpected error occurred while reading {os.path.basename(file_path)}: {e}. Skipping this file.")

    if not all_rows_to_write:
        logging.warning("No data found to merge after processing all files. No output CSV created.")
        return False
    
    Path(os.path.dirname(output_filepath)).mkdir(parents=True, exist_ok=True)

    try:
        with open(output_filepath, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerows(all_rows_to_write)
        logging.info(f"CSV merge complete. All data saved to {output_filepath}")
        return True
    except Exception as e:
        logging.error(f"Error writing merged CSV to {output_filepath}: {e}")
        return False


# --- Main Download Logic ---
if __name__ == "__main__":
    logging.info("Starting CSV download script.")

    # --- Setup Directories ---
    # Create the base GCS-like output directory where files will be directly downloaded
    Path(_GCS_OUTPUT_BASE_DIR).mkdir(parents=True, exist_ok=True)
    logging.info(f"Ensured base GCS-like directory exists: {_GCS_OUTPUT_BASE_DIR}")

    # Create the archive directory for downloaded files outside gcs_output
    Path(_ARCHIVE_DOWNLOADED_FILES_DIR).mkdir(parents=True, exist_ok=True)
    logging.info(f"Ensured archive directory for downloaded files exists: {_ARCHIVE_DOWNLOADED_FILES_DIR}")

    # Set to keep track of successfully downloaded/present states for validation
    downloaded_states_set = set() # This is only for tracking, the main validation is the file count

    for state_in_list in STATE_NAMES:
        full_url = f"{BASE_URL}{state_in_list}.csv"
        # The filename as it will be downloaded from the URL
        downloaded_filename_from_url = os.path.basename(full_url)
        # The full path where the file is expected to be in _GCS_OUTPUT_BASE_DIR
        download_target_path = os.path.join(_GCS_OUTPUT_BASE_DIR, downloaded_filename_from_url)

        logging.info(f"\nAttempting to download: {full_url}")

        # Check if file already exists in the _GCS_OUTPUT_BASE_DIR
        if os.path.exists(download_target_path):
            logging.info(f"File {downloaded_filename_from_url} already exists in {_GCS_OUTPUT_BASE_DIR}. Skipping download.")
            downloaded_states_set.add(state_in_list) 
            continue # Skip to next state

        try:
            download_success = download_file(
                url=full_url,
                output_folder=_GCS_OUTPUT_BASE_DIR, 
                unzip=False,
                headers=None,
                tries=3,
                delay=5,
                backoff=2
            )

            if download_success and os.path.exists(download_target_path):
                logging.info(f"Successfully downloaded {downloaded_filename_from_url} directly to {_GCS_OUTPUT_BASE_DIR}.")
                downloaded_states_set.add(state_in_list) # Mark as successfully handled
            else:
                logging.fatal(f" Critical Error: Failed to download {full_url}. Terminating script.")

        except Exception as e:
            logging.fatal(f" Critical Error: An unexpected error occurred during download or file operation for {full_url}: {e}. Terminating script.")

        time.sleep(0.1)

    # --- Pre-Merge Validation: Ensure all expected files are present ---
    logging.info("\n--- Performing pre-merge validation ---")
    
    # Get all CSV files actually present in the download directory
    actual_downloaded_csv_files = [f for f in os.listdir(_GCS_OUTPUT_BASE_DIR) if f.endswith('.csv') and f.startswith('historico_estado_')]
    actual_downloaded_count = len(actual_downloaded_csv_files)
    
    expected_count = len(STATE_NAMES)

    if actual_downloaded_count != expected_count:
        missing_states = []
        for state_name in STATE_NAMES:
            expected_filename = f"historico_estado_{state_name}.csv"
            if not os.path.exists(os.path.join(_GCS_OUTPUT_BASE_DIR, expected_filename)):
                missing_states.append(state_name)

        logging.fatal(
            f" Critical Error: Pre-merge validation failed! "
            f"Expected {expected_count} CSV files, but found {actual_downloaded_count} in '{_GCS_OUTPUT_BASE_DIR}'. "
            f"Missing states: {', '.join(missing_states)}. Terminating script."
        )
        sys.exit(1)
    else:
        logging.info(f"Pre-merge validation successful: Found {actual_downloaded_count} out of {expected_count} expected CSV files.")


    logging.info("\n--- All Downloads Confirmed Successful ---")
    logging.info(f"All {len(STATE_NAMES)} expected files are present in {_GCS_OUTPUT_BASE_DIR}.")

    # --- Call the merge function using the GCS_OUTPUT_BASE_DIR ---
    logging.info("\n--- Starting Merge Operation ---")
    merge_success = merge_csv_files(_GCS_OUTPUT_BASE_DIR, MERGED_CSV_FILE_NAME, STATE_NAMES)

    if merge_success:
        logging.info(f"Successfully merged data into: {MERGED_CSV_FILE_NAME}")
        
        # --- Move downloaded source files from gcs_output to _ARCHIVE_DOWNLOADED_FILES_DIR ---
        try:
            logging.info(f"Moving downloaded source files from '{_GCS_OUTPUT_BASE_DIR}' to '{_ARCHIVE_DOWNLOADED_FILES_DIR}'...")
            
            # Ensure the archive folder is clean before moving
            for item in os.listdir(_ARCHIVE_DOWNLOADED_FILES_DIR):
                item_path = os.path.join(_ARCHIVE_DOWNLOADED_FILES_DIR, item)
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            logging.info(f"Cleaned up existing contents in archive directory: {_ARCHIVE_DOWNLOADED_FILES_DIR}")

            # Move each individual downloaded file (historico_estado_*.csv)
            for state_name in STATE_NAMES:
                original_downloaded_filename = f"historico_estado_{state_name}.csv"
                source_file_path_in_gcs_output = os.path.join(_GCS_OUTPUT_BASE_DIR, original_downloaded_filename)
                destination_file_path_in_archive = os.path.join(_ARCHIVE_DOWNLOADED_FILES_DIR, original_downloaded_filename)
                
                # Check if the file exists before moving it
                if os.path.exists(source_file_path_in_gcs_output):
                    shutil.move(source_file_path_in_gcs_output, destination_file_path_in_archive)
                    logging.info(f"Moved '{original_downloaded_filename}' to archive.")
                # Removed the else block here as requested.

            # The _GCS_OUTPUT_BASE_DIR (gcs_output) will now be empty but not deleted.
            if os.path.exists(_GCS_OUTPUT_BASE_DIR) and not os.listdir(_GCS_OUTPUT_BASE_DIR):
                 logging.info(f"GCS output directory '{_GCS_OUTPUT_BASE_DIR}' is now empty as requested.")
            else:
                 logging.warning(f"GCS output directory '{_GCS_OUTPUT_BASE_DIR}' is not empty after cleanup. Check for unexpected files.")

            logging.info("Script finished successfully! ")
        except Exception as e:
            logging.fatal(f"Error during file archiving and cleanup: {e} ")
    else:
        logging.fatal("Merge operation failed. Please review logs. ")
