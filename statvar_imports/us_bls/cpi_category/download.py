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

import requests
import os
import zipfile
import re
import shutil
from retry import retry
from absl import logging

logging.set_verbosity(logging.INFO)

def generate_cpi_urls(year: int, month: int) -> list[str]:
    """
    Generates a list of CPI (Consumer Price Index) URLs for individual Excel files
    from the BLS website's supplemental files section.

    Args:
        year (int): The year (e.g., 2025).
        month (int): The month (e.g., 4 for April).

    Returns:
        list[str]: A list of generated URLs for Excel files.
    """
    month_str = f"{month:02d}"

    base_urls = [
        "https://www.bls.gov/cpi/tables/supplemental-files/cpi-u-{year}{month_str}.xlsx",
        "https://www.bls.gov/cpi/tables/supplemental-files/cpi-w-{year}{month_str}.xlsx",
        "https://www.bls.gov/cpi/tables/supplemental-files/c-cpi-u-{year}{month_str}.xlsx"
    ]

    generated_urls = [
        url.format(year=year, month_str=month_str) for url in base_urls
    ]

    return generated_urls

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
def download_file(url: str, save_path: str):
    """
    Downloads a file from a given URL and saves it to a specified path.
    Includes common HTTP headers to mimic a web browser.
    Uses a retry decorator.

    Args:
        url (str): The URL of the file to download.
        save_path (str): The full path including filename where the file should be saved.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.bls.gov/cpi/',
        'DNT': '1'
    }

    try:
        logging.info(f"Attempting to download: {url}")
        response = requests.get(url, stream=True, headers=headers, timeout=10)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        # Ensure the directory for save_path exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        logging.info(f"Successfully downloaded: {os.path.basename(save_path)} to {os.path.dirname(save_path)}")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Error downloading {url}: {e}")
        if response is not None:
            logging.warning(f"  Status Code: {response.status_code}")
        # Crucial: Re-raise the exception so the @retry decorator can catch it and retry
        raise
    except IOError as e:
        logging.error(f"Error saving file {save_path}: {e}")
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

def unzip_and_filter_january_files(zip_file_path: str, temp_extract_base_path: str, final_destination_base_path: str):
    """
    Unzips a specified ZIP file to a temporary directory.
    It then moves ONLY the January CPI Excel files (cpi-u, cpi-w, c-cpi-u for January)
    from the unzipped contents into their respective category subfolders
    within 'final_destination_base_path', and deletes all other unzipped
    contents and the original ZIP file.

    This version is enhanced to find files regardless of whether they are directly
    in the unzipped root or nested within a single top-level folder.

    Args:
        zip_file_path (str): The full path to the ZIP file.
        temp_extract_base_path (str): The base directory for temporary extraction.
                                      A unique temporary folder will be created inside it.
        final_destination_base_path (str): The base folder where the category subfolders exist
                                           and files should be moved to.
    """
    if not os.path.exists(zip_file_path):
        logging.error(f"Error: ZIP file not found at {zip_file_path}")
        return

    temp_extract_dir = os.path.join(temp_extract_base_path, os.path.basename(zip_file_path).replace('.zip', '_unzipped_temp'))
    os.makedirs(temp_extract_dir, exist_ok=True)
    logging.info(f"Created temporary extraction directory: {temp_extract_dir}")

    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)
        logging.info(f"Successfully unzipped {os.path.basename(zip_file_path)} to {temp_extract_dir}")
        january_file_pattern = re.compile(
    r'(cpi-u|cpi-w|c-cpi-u)[-_]\d{4}01\.(?:xls|xlsx)$', re.IGNORECASE
)
        
        found_january_files = False

        for root, _, files in os.walk(temp_extract_dir):
            for file_name in files:
                # Use .search() here as the pattern is no longer anchored to the start
                if january_file_pattern.search(file_name):
                    category_folder_name = get_cpi_category_from_filename(file_name)
                    if category_folder_name != "other": # Ensure it's one of our target categories
                        source_path = os.path.join(root, file_name)
                        destination_category_path = os.path.join(final_destination_base_path, category_folder_name)
                        os.makedirs(destination_category_path, exist_ok=True) # Ensure category subfolder exists
                        destination_file_path = os.path.join(destination_category_path, file_name)
                        
                        try:
                            # Use shutil.move for robustness, handles cross-device moves better than os.rename
                            shutil.move(source_path, destination_file_path)
                            logging.info(f"Moved January file '{file_name}' to '{destination_category_path}'")
                            found_january_files = True
                        except OSError as e:
                            logging.error(f"Error moving file {file_name} from {source_path} to {destination_file_path}: {e}")
                
        if not found_january_files:
            logging.info(f"No January CPI Excel files (cpi-u, cpi-w, c-cpi-u, etc.) found in {os.path.basename(zip_file_path)}.")

    except zipfile.BadZipFile:
        logging.error(f"Error: {os.path.basename(zip_file_path)} is not a valid ZIP file.")
    except Exception as e:
        logging.error(f"An unexpected error occurred while unzipping/moving {os.path.basename(zip_file_path)}: {e}")
    finally:
        # Clean up temporary extraction directory
        if os.path.exists(temp_extract_dir):
            try:
                shutil.rmtree(temp_extract_dir)
                logging.info(f"Removed temporary extraction directory: {temp_extract_dir}")
            except Exception as e:
                logging.error(f"Error removing temporary directory {temp_extract_dir}: {e}")

        # Remove the original ZIP file
        if os.path.exists(zip_file_path):
            try:
                os.remove(zip_file_path)
                logging.info(f"Removed original ZIP file: {os.path.basename(zip_file_path)}")
            except Exception as e:
                logging.error(f"Error removing ZIP file {zip_file_path}: {e}")

# --- New Function to List Files Alphabetically ---
def list_and_log_files_alphabetically(folder_path: str):
    """
    Lists files in a given folder alphabetically and logs them.
    """
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        files_in_folder = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        files_in_folder.sort() # Sorts alphabetically by filename
        if files_in_folder:
            for f_name in files_in_folder:
                logging.info(f"  - {f_name}")
        else:
            logging.info(f"  (No files found in {os.path.basename(folder_path)})")
    else:
        logging.warning(f"Folder not found or not a directory: {folder_path}")

def main():
    """
    Main function to orchestrate downloading, unzipping, and cleaning up CPI data.
    """
    # Define the base target directory for all final data files
    output_base_folder = "input_data"

    # Define the category subfolders
    cpi_u_folder = os.path.join(output_base_folder, "cpi-u")
    cpi_w_folder = os.path.join(output_base_folder, "cpi-w")
    c_cpi_u_folder = os.path.join(output_base_folder, "c-cpi-u")

    # Create the base output directory and its category subfolders
    os.makedirs(cpi_u_folder, exist_ok=True)
    os.makedirs(cpi_w_folder, exist_ok=True)
    os.makedirs(c_cpi_u_folder, exist_ok=True)
    logging.info(f"Ensured main directory '{output_base_folder}' and subfolders exist.")

    logging.info("\n--- Starting download process for individual Excel files ---")

    periods_to_download_excel = [
        (2025, 1),
        (2025, 4),
        (2024, 1)
    ]

    for year, month in periods_to_download_excel:
        urls_for_period = generate_cpi_urls(year, month)

        logging.info(f"\nProcessing Excel URLs for {month:02d}/{year}:")
        for url in urls_for_period:
            filename = url.split('/')[-1]
            category = get_cpi_category_from_filename(filename)
            
            if category == "cpi-u":
                file_save_path = os.path.join(cpi_u_folder, filename)
            elif category == "cpi-w":
                file_save_path = os.path.join(cpi_w_folder, filename)
            elif category == "c-cpi-u":
                file_save_path = os.path.join(c_cpi_u_folder, filename)
            else:
                # Fallback if filename doesn't match expected categories (shouldn't happen with current URLs)
                file_save_path = os.path.join(output_base_folder, filename)
                logging.warning(f"Warning: Unexpected filename '{filename}', saving to base output folder.")

            try:
                # download_file now raises an exception on network errors to trigger @retry
                download_file(url, file_save_path)
            except Exception as e: # Catch any exception that might propagate from download_file after retries
                logging.error(f"Download of {url} failed after multiple retries: {e}")


    years_to_download_zip = [2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014, 2013, 2012]

    for year in years_to_download_zip:
        zip_url = generate_zip_url(year)

        logging.info(f"\nProcessing ZIP URL for Year {year}:")
        filename = zip_url.split('/')[-1]
        # Download ZIP to the base output folder initially
        zip_file_path = os.path.join(output_base_folder, filename)

        download_successful = False
        try:
            # download_file now raises an exception on network errors to trigger @retry
            download_successful = download_file(zip_url, zip_file_path)
        except Exception as e: # Catch any exception that might propagate from download_file after retries
            logging.error(f"Download of {zip_url} failed after multiple retries: {e}")

        # If download was successful, then unzip, filter, move, and remove
        if download_successful:
            unzip_and_filter_january_files(zip_file_path, output_base_folder, output_base_folder)
        
    list_and_log_files_alphabetically(cpi_u_folder)
    list_and_log_files_alphabetically(cpi_w_folder)
    list_and_log_files_alphabetically(c_cpi_u_folder)



if __name__ == "__main__":
    main()