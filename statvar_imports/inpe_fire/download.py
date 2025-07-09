import requests
import os
import time
import logging
import csv 

# Configure logging for better output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

# Directory to save the downloaded CSV files
SCRIPT_DIR = os.path.dirname(__file__)
DOWNLOAD_DIR = os.path.join(SCRIPT_DIR, "inpe_data")

# Name for the merged output CSV file
MERGED_CSV_FILE_NAME = os.path.join(SCRIPT_DIR, "input.csv")

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

    # Create download directory if it doesn't exist
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)
        logging.info(f"Created download directory: {DOWNLOAD_DIR}")
    else:
        logging.info(f"Download directory already exists: {DOWNLOAD_DIR}")

    successful_downloads = []
    failed_downloads = []

    for state_in_list in STATE_NAMES:
        full_url = f"{BASE_URL}{state_in_list}.csv"
        file_name_local = f"{state_in_list}.csv"
        file_path = os.path.join(DOWNLOAD_DIR, file_name_local)

        logging.info(f"Attempting to download: {file_name_local} from {full_url}")

        try:
            with requests.get(full_url, stream=True) as response:
                response.raise_for_status()

                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            logging.info(f"Successfully downloaded: {file_name_local}")
            successful_downloads.append(state_in_list) # Add to successful list

        except requests.exceptions.HTTPError as errh:
            logging.error(f"HTTP Error for {file_name_local}: {errh} (URL: {full_url})")
            failed_downloads.append(f"{state_in_list} (HTTP Error: {errh})")
        except requests.exceptions.ConnectionError as errc:
            logging.error(f"Error Connecting for {file_name_local}: {errc}")
            failed_downloads.append(f"{state_in_list} (Connection Error: {errc})")
        except requests.exceptions.Timeout as errt:
            logging.error(f"Timeout Error for {file_name_local}: {errt}")
            failed_downloads.append(f"{state_in_list} (Timeout Error: {errt})")
        except requests.exceptions.RequestException as err:
            logging.error(f"An unexpected error occurred for {file_name_local}: {err}")
            failed_downloads.append(f"{state_in_list} (General Error: {err})")

        time.sleep(0.1)

    logging.info("\n--- Download Summary ---")
    if successful_downloads:
        logging.info(f"Successfully downloaded {len(successful_downloads)} files:")
        for s in successful_downloads:
            logging.info(f"- {s}")
    else:
        logging.info("No files were successfully downloaded.")

    if failed_downloads:
        logging.warning(f"Failed to download {len(failed_downloads)} files:")
        for f in failed_downloads:
            logging.warning(f"- {f}")
    else:
        logging.info("No files failed to download.")

    # --- Call the merge function after downloads are complete ---
    if successful_downloads:
        merge_csv_files(DOWNLOAD_DIR, MERGED_CSV_FILE_NAME, successful_downloads)
    else:
        logging.info("No files were downloaded, so skipping the merge operation.")

    logging.info("Script finished.")
