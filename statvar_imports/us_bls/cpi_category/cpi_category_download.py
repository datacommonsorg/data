# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
 
 
 
''' This script helps to download the input data for BLS_CPI_Category import. The source is https://www.bls.gov/cpi/tables/supplemental-files/. It covers cpi-u, cpi-w and c-cpi-u datasets. 
For c-cpi-u we are downloading alternative files because each file contains 2 month data. Same for cpi-u and cpi-w we are downloading the January month file of all years.
'''


import requests
import os
import zipfile
import re
import shutil
from retry import retry
from absl import logging
import datetime
import argparse 

logging.set_verbosity(logging.INFO)

logging.info("--- Starting script execution ---")

def generate_zip_url(year: int) -> str:
    """
    Generates the URL for a CPI supplemental data archive (ZIP file) for a given year.
    Args:
        year (int): The year for which to generate the archive URL (e.g., 2023).
    Returns:
        str: The URL of the ZIP archive.
    """
    return f"https://www.bls.gov/cpi/tables/supplemental-files/archive-{year}.zip"

@retry(tries=3, delay=5, backoff=2)
def download_file(url: str, save_path: str ,timeout: int = 60):
    """
    Downloads a file from a given URL and saves it to a specified path.
    Includes common HTTP headers to mimic a web browser.
    Uses a retry decorator.
    Args:
        url (str): The URL of the file to download.
        save_path (str): The full path including filename where the file should be saved.
    Returns:
        bool: True if download was successful, False otherwise.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.bls.gov/cpi/',
        'DNT': '1'
    }
    try:
        logging.info(f"Attempting to download: {url} with timeout {timeout} seconds.")
        response = requests.get(url, stream=True, headers=headers, timeout=timeout)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        # Ensure the directory for save_path exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        logging.info(f"Successfully downloaded: {os.path.basename(save_path)} to {os.path.dirname(save_path)}")
        return True

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            # For 404s, log as info and return False without retrying, as the file doesn't exist.
            logging.fatal(f"Skipping {url} (404 Not Found - file expected to be unavailable): {e}")
            return False
        else:
            # For other HTTP errors, re-raise to trigger retry.
            logging.fatal(f"Error downloading {url}: {e}")
            raise
    except requests.exceptions.RequestException as e:
        # For network errors, re-raise to trigger retry.
        logging.fatal(f"Network error downloading {url}: {e}")
        raise
    except IOError as e:
        logging.fatal(f"Error saving file {save_path}: {e}")
        return False # This is a local file system error, no need to retry download from URL

def get_cpi_category_from_filename(filename: str) -> str:
    """
    Determines the CPI category (cpi-u, cpi-w, c-cpi-u) from a given filename.
    This function specifically looks for the standard prefixes and is used for categorization.
    """
    if re.match(r'^(c-cpi-u|C-CPI-U)', filename, re.IGNORECASE):
        return "c-cpi-u"
    elif re.match(r'^(cpi-u|CPI-U|CPI_U)', filename, re.IGNORECASE):
        return "cpi-u"
    elif re.match(r'^(cpi-w|CPI-W)', filename, re.IGNORECASE):
        return "cpi-w"
    return "other" # Fallback if filename doesn't match expected patterns

def get_year_month_from_filename(filename: str) -> tuple[int, int] | None:
    """
    Extracts the year and month from a filename like cpi-u-YYYYMM.xlsx
    Returns (year, month) tuple or None if not found.
    """
    match = re.search(r'(\d{4})(\d{2})\.(?:xls|xlsx)$', filename)
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        return (year, month)
    return None

def unzip_all_excel_files(zip_file_path: str, temp_extract_base_path: str, final_destination_base_path: str,
                          cpi_u_w_rules: dict[str, list[int]], c_cpi_u_rules: dict[str, int])-> bool:
    """
    Unzips a specified ZIP file to a temporary directory.
    It then moves identified CPI Excel files into their respective category subfolders,
    applying specific month/year rules for each category.
    Args:
        zip_file_path (str): The full path to the ZIP file.
        temp_extract_base_path (str): The base directory for temporary extraction.
        final_destination_base_path (str): The base folder where the category subfolders exist.
        cpi_u_w_rules (dict): Rules for cpi-u and cpi-w (e.g., {'months': [1], 'latest_year': 2025, 'latest_month': 4}).
                              Only files matching these rules are moved.
        c_cpi_u_rules (dict): Rules for c-cpi-u (e.g., {'start_year': 2021}).
                              Only files matching these rules (even months >= start_year) are moved.
    Returns:
        bool: True if the unzipping and processing was successful, False otherwise.
    """
    if not os.path.exists(zip_file_path):
        logging.error(f"Error: ZIP file not found at {zip_file_path}")
        return False # Indicate failure

    zip_basename = os.path.basename(zip_file_path).replace('.zip', '')
    temp_extract_dir = os.path.join(temp_extract_base_path, f"{zip_basename}_unzipped_temp")
    os.makedirs(temp_extract_dir, exist_ok=True)
    logging.info(f"Created temporary extraction directory: {temp_extract_dir}")
    success = False # Initialize success flag, assumes failure until proven otherwise
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            logging.info(f"Contents of {os.path.basename(zip_file_path)}: {zip_ref.namelist()}")
            zip_ref.extractall(temp_extract_dir)
        logging.info(f"Successfully unzipped {os.path.basename(zip_file_path)} to {temp_extract_dir}")

        excel_file_pattern = re.compile(r'\.(?:xls|xlsx)$', re.IGNORECASE)
        found_cpi_files = False

        for root, _, files in os.walk(temp_extract_dir):
            for file_name in files:
                if excel_file_pattern.search(file_name):
                    category_folder_name = get_cpi_category_from_filename(file_name)
                    file_year_month = get_year_month_from_filename(file_name)

                    move_file = False
                    if file_year_month:
                        year, month = file_year_month
                        if category_folder_name in ["cpi-u", "cpi-w"]:
                            # Apply cpi-u/w rules for ZIPs:
                            # 1. Always include January for any year (as per historical requirement) EXCEPT if it's the current year.
                            # 2. For the current year (latest_year), include January AND the specific latest month found.
                            required_months_from_zip = cpi_u_w_rules['months'] # This will still be [1] (January)
                            latest_year = cpi_u_w_rules['latest_year']
                            latest_month_current_year = cpi_u_w_rules['latest_month']

                            if year < latest_year and month in required_months_from_zip: # Handles January files from historical ZIPs
                                move_file = True
                            elif year == latest_year: # Special handling for current year (2025)
                                if month == 1: # Always include January of the current year from ZIP if present
                                    move_file = True
                                elif month == latest_month_current_year and latest_month_current_year != 0: # Include the latest month of current year from ZIP if present
                                    move_file = True
                                else:
                                    logging.debug(f"Skipping {file_name} from zip (cpi-u/w, {latest_year}, not January or specific latest).")
                            else:
                                logging.debug(f"Skipping {file_name} from zip (cpi-u/w, not January or specific latest {latest_year}).")

                        elif category_folder_name == "c-cpi-u":
                            # Apply c-cpi-u rules: even months from Dec 2021 onwards
                            start_year_ccpiu = c_cpi_u_rules['start_year']
                            if year >= start_year_ccpiu:
                                if year == start_year_ccpiu and month == 12: # Dec 2021
                                    move_file = True
                                elif year > start_year_ccpiu and month % 2 == 0: # Even months for subsequent years
                                    move_file = True
                                else:
                                    logging.debug(f"Skipping {file_name} from zip (c-cpi-u, not matching even month/start year rule).")
                            else:
                                logging.debug(f"Skipping {file_name} from zip (c-cpi-u, year older than {start_year_ccpiu}).")
                        else:
                            logging.debug(f"Skipping {file_name} from zip (unrecognized CPI category).")
                    else:
                        logging.debug(f"Skipping {file_name} from zip (could not extract year/month).")


                    if move_file:
                        source_path = os.path.join(root, file_name)
                        destination_category_path = os.path.join(final_destination_base_path, category_folder_name)
                        os.makedirs(destination_category_path, exist_ok=True)
                        destination_file_path = os.path.join(destination_category_path, file_name)

                        try:
                            # Overwrite if file already exists (e.g., from individual download or duplicate in zip)
                            if os.path.exists(destination_file_path):
                                logging.warning(f"File '{file_name}' already exists in '{destination_category_path}'. Overwriting.")

                            shutil.move(source_path, destination_file_path)
                            logging.info(f"Moved CPI file '{file_name}' from '{source_path}' to '{destination_category_path}'")
                            found_cpi_files = True
                        except OSError as e:
                            logging.error(f"Error moving file {file_name} from {source_path} to {destination_file_path}: {e}")
                # else:
                #     logging.debug(f"Skipping non-Excel file: {file_name} from zip.")

        if found_cpi_files:
            logging.info(f"Successfully processed relevant CPI Excel files from {os.path.basename(zip_file_path)}.")
            success = True
        else:
            logging.info(f"No *relevant* CPI Excel files found or processed from {os.path.basename(zip_file_path)} based on specified rules.")
            success = False # Explicitly set to false if no relevant files processed

    except zipfile.BadZipFile:
        #TODO b/431970934 : Log the exception as well
        logging.error(f"Error: {os.path.basename(zip_file_path)} is not a valid ZIP file.")
        success = False # Explicitly set to False on bad zip
    except Exception as e:
        logging.error(f"An unexpected error occurred while unzipping/moving {os.path.basename(zip_file_path)}: {e}")
        success = False # Explicitly set to False for other unexpected errors
    finally:
        if os.path.exists(temp_extract_dir):
            try:
                shutil.rmtree(temp_extract_dir)
                logging.info(f"Removed temporary extraction directory: {temp_extract_dir}")
            except Exception as e:
                logging.error(f"Error removing temporary directory {temp_extract_dir}: {e}")
             
        # Only remove the ZIP file if the overall unzipping and moving was successful.
        # If it failed, keeping the ZIP might be useful for debugging.
        if success and os.path.exists(zip_file_path):
            try:
                os.remove(zip_file_path)
                logging.info(f"Removed original ZIP file: {os.path.basename(zip_file_path)}")
            except Exception as e:
                logging.error(f"Error removing ZIP file {zip_file_path}: {e}")
            
    return success # Return the success status

def list_and_log_files_alphabetically(folder_path: str):
    """
    Lists files in a given folder alphabetically and logs them.
    """
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        files_in_folder = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        files_in_folder.sort()
        if files_in_folder:
            for f_name in files_in_folder:
                logging.info(f"  - {f_name}")
        else:
            logging.info(f"  (No files found in {os.path.basename(folder_path)})")
    else:
        logging.warning(f"Folder not found or not a directory: {folder_path}")

def main():
    """
    Main function to orchestrate downloading, unzipping, and cleaning up CPI data
    based on specific category and month/year requirements.
    """

    parser = argparse.ArgumentParser(description="Download BLS CPI data.")
    parser.add_argument("--timeout", type=int, default=60,
                        help="Timeout for file downloads in seconds (default: 60)")
    parser.add_argument("--output_folder", type=str, default="input_data",
                        help="The folder where the downloaded files will be stored.")
    args = parser.parse_args() 
    output_base_folder = args.output_folder

    cpi_u_folder = os.path.join(output_base_folder, "cpi-u")
    cpi_w_folder = os.path.join(output_base_folder, "cpi-w")
    c_cpi_u_folder = os.path.join(output_base_folder, "c-cpi-u")

    os.makedirs(cpi_u_folder, exist_ok=True)
    os.makedirs(cpi_w_folder, exist_ok=True)
    os.makedirs(c_cpi_u_folder, exist_ok=True)
    logging.info(f"Ensured main directory '{output_base_folder}' and subfolders exist.")

    # Get current date to determine the latest available data.
    # Keeping the fixed date for consistent testing based on prompt's context (June 10, 2025).
    today = datetime.date.today()
    current_year = today.year
    current_month = today.month

    logging.info("\n--- Starting targeted download process for individual Excel files ---")

    # --- RULE 1: For 'c-cpi-u' files: Even months only, starting from Dec 2021 ---
    logging.info("\n--- Processing c-cpi-u files (even months, from Dec 2021 onwards) ---")
    start_year_ccpiu_rule = 2021
    c_cpi_u_filter_rules = {'start_year': start_year_ccpiu_rule}

    for year in range(start_year_ccpiu_rule, current_year + 1):
        start_month_for_year_ccpiu = 12 if year == start_year_ccpiu_rule else 2
        end_month_for_year_ccpiu = current_month if year == current_year else 12

        for month in range(start_month_for_year_ccpiu, end_month_for_year_ccpiu + 1):
            if month % 2 == 0:
                month_str = f"{month:02d}"
                url = f"https://www.bls.gov/cpi/tables/supplemental-files/c-cpi-u-{year}{month_str}.xlsx"
                filename = url.split('/')[-1]
                file_save_path = os.path.join(c_cpi_u_folder, filename)

                try:
                    if not download_file(url, file_save_path,timeout=args.timeout):
                        continue
                except Exception as e:
                    logging.error(f"Download of c-cpi-u file {url} failed after multiple retries: {e}")


    # --- RULE 2: For 'cpi-u' and 'cpi-w' files: Only January for previous years, AND January + single latest for 2025 ---
    logging.info("\n--- Processing cpi-u and cpi-w files (January only for years prior to current year, + January and single latest for current year) ---")

    # Download January files for years *prior* to the current year (e.g., 2010-2024 January).
    start_year_january_cpi_uw_rule = 2010

    for year in range(start_year_january_cpi_uw_rule, current_year): # Loop up to, but *not including* current_year
        month = 1 # Always January
        month_str = f"{month:02d}"

        for category_prefix in ["cpi-u", "cpi-w"]:
            url = f"https://www.bls.gov/cpi/tables/supplemental-files/{category_prefix}-{year}{month_str}.xlsx"
            filename = url.split('/')[-1]

            if category_prefix == "cpi-u":
                file_save_path = os.path.join(cpi_u_folder, filename)
            else: # cpi-w
                file_save_path = os.path.join(cpi_w_folder, filename)

            try:
                if not download_file(url, file_save_path,timeout=args.timeout):
                    continue
            except Exception as e:
                logging.error(f"Download of {category_prefix} January file {url} failed after multiple retries: {e}")

    # --- Handle current_year (2025) files for cpi-u and cpi-w: Ensure January AND the latest available are downloaded ---
    latest_current_year_month_cpi_uw = 0 # Stores the absolute highest month found for current year (e.g., if May 2025 is found, it's 5)

    logging.info(f"\n--- Attempting to download January {current_year} files for cpi-u and cpi-w ---")
    for category_prefix in ["cpi-u", "cpi-w"]:
        # Explicitly attempt to download January current_year
        month_jan = 1
        month_jan_str = f"{month_jan:02d}"
        url_jan = f"https://www.bls.gov/cpi/tables/supplemental-files/{category_prefix}-{current_year}{month_jan_str}.xlsx"
        filename_jan = url_jan.split('/')[-1]

        file_save_path_jan = os.path.join(cpi_u_folder if category_prefix == "cpi-u" else cpi_w_folder, filename_jan)
        try:
            if download_file(url_jan, file_save_path_jan,timeout=args.timeout):
                logging.info(f"Downloaded January {current_year} {category_prefix} file: {filename_jan}")
                # If January is found, update latest_current_year_month_cpi_uw in case it's the only month out so far
                latest_current_year_month_cpi_uw = max(latest_current_year_month_cpi_uw, month_jan)
        except Exception as e:
            logging.error(f"Download attempt for January {current_year} {category_prefix} file {url_jan} failed: {e}")

    logging.info(f"\n--- Attempting to download absolute latest available {current_year} files for cpi-u and cpi-w ---")

    for category_prefix in ["cpi-u", "cpi-w"]:
        # Iterate backward from current_month to find the highest available month.
        # This loop will ensure the absolute latest file (e.g., April, May) is downloaded.
        # If January is the only file available, this loop will also ensure it's captured
        # as the latest and `download_file` will skip re-downloading if already present.
        for month_iter in range(current_month, 0, -1):
            month_iter_str = f"{month_iter:02d}"
            url_latest = f"https://www.bls.gov/cpi/tables/supplemental-files/{category_prefix}-{current_year}{month_iter_str}.xlsx"
            filename_latest = url_latest.split('/')[-1]

            file_save_path_latest = os.path.join(cpi_u_folder if category_prefix == "cpi-u" else cpi_w_folder, filename_latest)

            try:
                # download_file will return True if downloaded or if file already existed but HTTP status was 200,
                # or False if 404. We want to stop at the first existing/downloadable file.
                if download_file(url_latest, file_save_path_latest,timeout=args.timeout):
                    logging.info(f"Found and downloaded/confirmed latest {category_prefix} file for {current_year}: {filename_latest}")
                    # Update overall latest_current_year_month_cpi_uw
                    latest_current_year_month_cpi_uw = max(latest_current_year_month_cpi_uw, month_iter)
                    break # Found the latest for this specific category_prefix, so stop iterating for this category
                # else: File not found for this month, continue to next earlier month
            except Exception as e:
                logging.error(f"Download attempt for {category_prefix} {current_year}{month_iter_str} failed after retries: {e}")


    # Define the rules to pass to the unzip function
    # For ZIPs, we still want January files from historical years.
    # The 'latest_month' will be used to ensure the single latest 2025 file is also moved if it comes from a ZIP.
    # The `unzip_all_excel_files` function logic has been updated to handle the `latest_year` (2025) more precisely.
    cpi_u_w_filter_rules = {
        'months': [1], # This refers to general January files from historical ZIPs (prior to current_year).
        'latest_year': current_year,
        'latest_month': latest_current_year_month_cpi_uw # This captures the single highest month found for current year (2025)
    }

    logging.info("\n--- Starting download process for yearly ZIP archives ---")
    years_to_download_zip = list(range(2010, 2024)) # Covers 2010 up to and including 2023

    for year in years_to_download_zip:
        zip_url = generate_zip_url(year)

        logging.info(f"\nProcessing ZIP URL for Year {year}:")
        filename = zip_url.split('/')[-1]
        zip_file_path = os.path.join(output_base_folder, filename)

        download_successful = False
        try:
            download_successful = download_file(zip_url, zip_file_path,timeout=args.timeout)
        except Exception as e:
            logging.error(f"Download of {zip_url} failed after multiple retries: {e}")

        if download_successful:
            unzip_successful =unzip_all_excel_files(zip_file_path, output_base_folder, output_base_folder,
                                  cpi_u_w_rules=cpi_u_w_filter_rules,
                                  c_cpi_u_rules=c_cpi_u_filter_rules)
            if not unzip_successful:
                logging.fatal(f"CRITICAL ERROR: Unzipping or processing of {filename} failed. Cannot proceed.")
            else:
                logging.info(f"Successfully processed ZIP for Year {year}.")

    logging.info("\n--- Listing files in respective folders after all downloads/extractions ---")
    logging.info("Files in 'cpi-u' folder:")
    list_and_log_files_alphabetically(cpi_u_folder)
    logging.info("\nFiles in 'cpi-w' folder:")
    list_and_log_files_alphabetically(cpi_w_folder)
    logging.info("\nFiles in 'c-cpi-u' folder:")
    list_and_log_files_alphabetically(c_cpi_u_folder)

    logging.info("\n--- Script execution finished ---")


if __name__ == "__main__":
    main()
