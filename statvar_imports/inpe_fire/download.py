import requests
import os
import time
from absl import logging 
import csv 
import shutil


# Base URL for the CSV files
BASE_URL = "https://terrabrasilis.dpi.inpe.br/queimadas/situacao-atual/media/estado/csv_estatisticas/historico_estado_"

# List of state names 
STATE_NAMES = [
    'acre', 'alagoas', 'amapa', 'amazonas', 'bahia', 'ceara', 'distrito_federal',
    'espirito_santo', 'goias', 'maranhao', 'mato_grosso', 'mato_grosso_do_sul',
    'minas_gerais', 'para', 'paraiba', 'parana', 'pernambuco', 'piaui',
    'rio_de_janeiro', 'rio_grande_do_norte', 'rio_grande_do_sul', 'rondonia',
    'roraima', 'santa_catarina', 'sao_paulo', 'sergipe', 'tocantins'
]

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

# Local directory acting as your "GCS output persistent path"
_GCS_OUTPUT_PERSISTENT_PATH = os.path.join(
    _MODULE_DIR, 'gcs_output', 'inpe_source_files') # Using 'gcs_output/inpe_source_files'
_GCS_BASE_DIR = os.path.join(_MODULE_DIR, 'gcs_output') # Base directory for GCS-like structure

# Directory to save temporary downloaded CSV files before "uploading" to _GCS_OUTPUT_PERSISTENT_PATH
# This acts as a staging area.
TEMP_DOWNLOAD_DIR = os.path.join(_MODULE_DIR, "temp_downloads")

# Name for the merged output CSV file
MERGED_CSV_FILE_NAME = os.path.join(_MODULE_DIR, "input.csv")

# --- Function: Merge CSV Files ---
def merge_csv_files(input_directory, output_filepath, downloaded_states_list):
   
    #Reads all CSV files from a given directory and merges them into a single CSV file.
    '''Args:
        input_directory (str): The path to the directory containing the CSV files.
        output_filepath (str): The full path and filename for the merged CSV output.
        downloaded_states_list (list): A list of state names that were successfully
                                       downloaded, used to determine the order of merging.'''
   
    logging.info(f"Starting CSV merge process. Output file: {output_filepath}")

    all_rows_to_write = []
    header_found = False

    for state_name_for_url in downloaded_states_list:
        file_name_local = f"{state_name_for_url}.csv" 
        file_path = os.path.join(input_directory, file_name_local)

        if not os.path.exists(file_path):
            logging.warning(f"Skipping merge for '{state_name_for_url}': File not found at {file_path}. Was it downloaded?")
            continue

        try:
            with open(file_path, mode='r', newline='', encoding='utf-8') as infile:
                reader = csv.reader(infile)

                # Attempt to read the first row (which should be the header)
                try:
                    current_file_header = next(reader)
                except StopIteration:
                    logging.warning(f"File '{file_name_local}' is empty, skipping.")
                    continue

                if not header_found:
                    # This is the very first file with data, so we modify its header
                    # A1 = 'year'
                    if len(current_file_header) > 0:
                        current_file_header[0] = 'year'
                    
                    # B1 = 'place' - insert it as the second column header (index 1)
                    # Ensure the list is long enough for an insert at index 1
                    if len(current_file_header) < 1: 
                        current_file_header.append('place')
                    else:
                        current_file_header.insert(1, 'place')
                    
                    all_rows_to_write.append(current_file_header)
                    header_found = True
                    logging.info(f"Using and modifying header from {file_name_local}")
                else:
                    # For subsequent files, we explicitly skip their headers
                    logging.debug(f"Skipping header from {file_name_local}")

                # Prepare the display-friendly state name to insert into each row
                display_state_name = state_name_for_url.replace('_', ' ').title()

                # Append all remaining rows (the actual data) from this file
                # and insert the 'place' (state name) into each row at column B (index 1)
                for row in reader: # 'reader' continues from the row *after* the header
                    # Ensure the row has at least one element before inserting at index 1
                    if len(row) < 1:
                        row.append(display_state_name) # If row is empty, just append
                    else:
                        row.insert(1, display_state_name) # Insert at index 1 (column B)
                    all_rows_to_write.append(row)

            logging.info(f"Successfully processed data from {file_name_local} for merging.")

        except UnicodeDecodeError:
            logging.error(f"Encoding error reading {file_name_local}. Please check file encoding. Skipping this file.")
        except csv.Error as e:
            logging.error(f"CSV parsing error in {file_name_local}: {e}. Skipping this file.")
        except Exception as e:
            logging.error(f"An unexpected error occurred while reading {file_name_local}: {e}. Skipping this file.")

    if not all_rows_to_write:
        logging.warning("No data found to merge after processing all files. No output CSV created.")
        return

    try:
        with open(output_filepath, mode='w', newline='', encoding='utf-8') as outfile:
            writer = csv.writer(outfile)
            writer.writerows(all_rows_to_write)
        logging.info(f"CSV merge complete. All data saved to {output_filepath}")
    except Exception as e:
        logging.error(f"Error writing merged CSV to {output_filepath}: {e}")


# --- Main Download Logic ---
if __name__ == "__main__":
    logging.info("Starting CSV download script.")

    # --- Setup _GCS_OUTPUT_PERSISTENT_PATH and TEMP_DOWNLOAD_DIR ---
    # Ensure _GCS_BASE_DIR exists
    if not os.path.exists(_GCS_BASE_DIR):
        os.makedirs(_GCS_BASE_DIR)
        logging.info(f"Created base GCS-like directory: {_GCS_BASE_DIR}")


    # Create _GCS_OUTPUT_PERSISTENT_PATH if it doesn't exist.
    if not os.path.exists(_GCS_OUTPUT_PERSISTENT_PATH):
        os.makedirs(_GCS_OUTPUT_PERSISTENT_PATH)
        logging.info(f"Created GCS-like output directory for persistent files: {_GCS_OUTPUT_PERSISTENT_PATH}")
    else:
        logging.info(f"GCS-like output directory already exists: {_GCS_OUTPUT_PERSISTENT_PATH}")

    # Create temporary download directory
    if not os.path.exists(TEMP_DOWNLOAD_DIR):
        os.makedirs(TEMP_DOWNLOAD_DIR)
        logging.info(f"Created temporary download directory: {TEMP_DOWNLOAD_DIR}")
    else:
        logging.info(f"Temporary download directory already exists: {TEMP_DOWNLOAD_DIR}")

    # Get already downloaded files from the "persistent storage"
    downloaded_files_in_persistent_storage = set(os.listdir(_GCS_OUTPUT_PERSISTENT_PATH))
    logging.info(f"Files already in persistent storage: {downloaded_files_in_persistent_storage}")

    successful_downloads = []
    failed_downloads = []

    for state_in_list in STATE_NAMES:
        full_url = f"{BASE_URL}{state_in_list}.csv"
        file_name_to_save = f"{state_in_list}.csv"
        temp_file_path = os.path.join(TEMP_DOWNLOAD_DIR, file_name_to_save)
        persistent_file_path = os.path.join(_GCS_OUTPUT_PERSISTENT_PATH, file_name_to_save)

        logging.info(f"Attempting to download: {file_name_to_save} from {full_url}")

        # Check if file already exists in persistent storage
        if file_name_to_save in downloaded_files_in_persistent_storage:
            logging.info(f"File {file_name_to_save} already exists in persistent storage. Skipping download.")
            successful_downloads.append(state_in_list)
            continue # Skip to next state

        # --- Resumable download logic (local temporary file) ---
        headers = {}
        current_size = 0

        if os.path.exists(temp_file_path):
            current_size = os.path.getsize(temp_file_path)
            if current_size > 0:
                headers['Range'] = f'bytes={current_size}-'
                logging.info(f"Resuming download of {file_name_to_save} from byte {current_size} to temp location.")
            else:
                logging.info(f"Existing empty temp file {file_name_to_save}, restarting download.")
                # If file exists but is empty, don't use Range header, effectively restart
                # Optionally delete it first: os.remove(temp_file_path)
        else:
            logging.info(f"Starting new download for {file_name_to_save} to temp location.")


        try:
            with requests.get(full_url, headers=headers, stream=True, timeout=30) as response:
                response.raise_for_status()

                # Handle cases where server doesn't support Range requests (status 200 without Range header)
                if response.status_code == 200 and 'Range' not in headers and current_size > 0:
                    logging.warning(f"Server did not honor Range request for {file_name_to_save}, re-downloading full file.")
                    current_size = 0 # Reset current size to overwrite existing partial file

                mode = 'wb' if current_size == 0 else 'ab'
                with open(temp_file_path, mode) as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            # After successful download to temp, "upload" to _GCS_OUTPUT_PERSISTENT_PATH
            shutil.copy(temp_file_path, persistent_file_path)
            logging.info(f"Successfully downloaded {file_name_to_save} to temporary location and moved to persistent storage.")
            successful_downloads.append(state_in_list)

            # Clean up the temporary file after successful "upload"
            os.remove(temp_file_path)
            logging.debug(f"Removed temporary file: {temp_file_path}")

        except requests.exceptions.HTTPError as errh:
            logging.error(f"HTTP Error for {file_name_to_save}: {errh} (URL: {full_url})")
            failed_downloads.append(f"{state_in_list} (HTTP Error: {errh})")
        except requests.exceptions.ConnectionError as errc:
            logging.error(f"Error Connecting for {file_name_to_save}: {errc}")
            failed_downloads.append(f"{state_in_list} (Connection Error: {errc})")
        except requests.exceptions.Timeout as errt:
            logging.error(f"Timeout Error for {file_name_to_save}: {errt}")
            failed_downloads.append(f"{state_in_list} (Timeout Error: {errt})")
        except requests.exceptions.RequestException as err:
            logging.error(f"An unexpected error occurred for {file_name_to_save}: {err}")
            failed_downloads.append(f"{state_in_list} (General Error: {err})")
        except Exception as e:
            logging.error(f"An error occurred during file copy for {file_name_to_save}: {e}")
            failed_downloads.append(f"{state_in_list} (File Copy Error: {e})")

        time.sleep(0.1)

    logging.info("\n--- Download and Persistence Summary ---")
    if successful_downloads:
        logging.info(f"Successfully processed {len(successful_downloads)} files (downloaded or already present):")
        for s in successful_downloads:
            logging.info(f"- {s}")
    else:
        logging.info("No files were successfully downloaded or processed.")

    if failed_downloads:
        logging.warning(f"Failed to download/persist {len(failed_downloads)} files:")
        for f in failed_downloads:
            logging.warning(f"- {f}")
    else:
        logging.info("No files failed to download or persist.")

    # Clean up the temporary download directory at the end
    if os.path.exists(TEMP_DOWNLOAD_DIR):
        try:
            shutil.rmtree(TEMP_DOWNLOAD_DIR)
            logging.info(f"Cleaned up temporary download directory: {TEMP_DOWNLOAD_DIR}")
        except Exception as e:
            logging.error(f"Error cleaning up temporary directory {TEMP_DOWNLOAD_DIR}: {e}")

    # --- Call the merge function using the persistent storage directory ---
    if successful_downloads:
        # We merge from the _GCS_OUTPUT_PERSISTENT_PATH
        merge_csv_files(_GCS_OUTPUT_PERSISTENT_PATH, MERGED_CSV_FILE_NAME, successful_downloads)
    else:
        logging.info("No files were successfully processed for persistence, so skipping the merge operation.")

    logging.info("Script finished.")
