import os
import sys
from absl import app, logging
import datetime
import glob
import shutil
import pandas as pd 
import re
# NOTE: To handle .xlsx files, the 'openpyxl' library is required (pip install openpyxl).

# --- Configuration Constants ---
_SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
# Ensure the utility script is available
sys.path.append(os.path.join(_SCRIPT_PATH, '../../../util/'))
from download_util_script import download_file

logging.set_verbosity(logging.INFO)

_BASE_URL = "https://civilrightsdata.ed.gov/assets/ocr/docs/{year_range}-crdc-data.zip"
# Base directory where all year-wise data is downloaded
_BASE_DOWNLOAD_DIRECTORY = "source_files" 
# Final destination for the collected files
_SOURCE_FILES_DIRECTORY = "input_files" 
_START_YEAR = 2011
_CURRENT_YEAR = datetime.datetime.now().year

# --- File Collection and Renaming Logic (Updated) ---

def _find_and_collect_files(year_range: str):
    """
    Locates files, reads them with pandas (handling CSV/XLSX), 
    renames them using the SECOND year of the range, and saves them 
    exclusively as CSV files in the source_files directory.
    """
    logging.info(f"Starting file collection and CSV conversion for {year_range}...")
    
    # Directory where the data for this year was downloaded/unzipped
    year_download_dir = os.path.join(_BASE_DOWNLOAD_DIRECTORY, f"crdc_data_{year_range}")
    
    target_dir = None
    file_paths = []

    # 1. Targeted Folder Search for 2009-10 and 2011-12
    if year_range in ["2009-10", "2011-12"]:
        harassment_dir_pattern = os.path.join(year_download_dir, '**', '*[Hh]arassment*')
        
        potential_dirs = [d for d in glob.glob(harassment_dir_pattern, recursive=True) if os.path.isdir(d)]
        
        if potential_dirs:
            target_dir = potential_dirs[0]
            logging.info(f"Found Harassment folder for {year_range}: {target_dir}")
            
            # Now, collect ALL files (csv/xlsx) inside this specific folder
            file_paths.extend(glob.glob(os.path.join(target_dir, '*.csv')))
            file_paths.extend(glob.glob(os.path.join(target_dir, '*.xlsx')))
        
    # 2. Recursive Filename Search for all other years
    else:
        search_terms = ['*[Hh]arassment*.csv', '*[Hh]arassment*.xlsx']
        
        for term in search_terms:
            search_pattern = os.path.join(year_download_dir, '**', term)
            file_paths.extend(glob.glob(search_pattern, recursive=True))
            
        # Remove duplicates
        file_paths = list(set(file_paths))


    # 3. Process, Convert, and Rename the collected files
    
    if not file_paths:
        logging.warning(f"No Harassment data files found for {year_range}.")
        return

    # Prepare for renaming
    try:
        # Extract the first year (e.g., 2009 from 2009-10) and convert to int
        first_year = int(year_range.split('-')[0])
        # Calculate the target year (second year of the range, e.g., 2010)
        target_year = first_year + 1
        target_year_str = str(target_year)
    except ValueError:
        logging.error(f"Could not parse year from range: {year_range}. Using default prefix.")
        target_year_str = year_range.replace('-', '_') # Fallback
        
    base_name = f"crdc_harassment_or_bullying_{target_year_str}"
    
    # Sort files to ensure consistent 'part' numbering 
    file_paths.sort() 
    
    for i, old_filepath in enumerate(file_paths):
        # --- NEW CONVERSION LOGIC ---
        
        # Output extension is always CSV
        extension = ".csv"
        
        # Determine the new filename based on the number of files
        if len(file_paths) == 1:
            new_filename = f"{base_name}{extension}"
        else:
            # Use 2 digits for part number (e.g., _part_01)
            new_filename = f"{base_name}_part_{i+1:02d}{extension}" 
        
        new_filepath = os.path.join(_SOURCE_FILES_DIRECTORY, new_filename)
        original_extension = os.path.splitext(old_filepath)[1].lower()
        
        logging.info(f"Converting '{os.path.basename(old_filepath)}' ({original_extension}) to CSV at '{new_filepath}'")
        
        try:
            # Step 1: Read the file based on its original extension
            if original_extension == '.csv':
                df = pd.read_csv(old_filepath)
            elif original_extension in ['.xlsx', '.xls']:
                # Read the first sheet of the Excel file
                df = pd.read_excel(old_filepath, sheet_name=0)
            else:
                logging.warning(f"Skipping {old_filepath}: Unsupported original format {original_extension}.")
                continue

            # Step 2: Save the DataFrame as a CSV file
            # index=False prevents pandas from writing its row index as an extra column
            df.to_csv(new_filepath, index=False)
            
        except ImportError:
             logging.error(f"Failed to read Excel file {old_filepath}. Please ensure 'openpyxl' is installed (pip install openpyxl).")
             continue
        except Exception as e:
            logging.error(f"Failed to process and save file {old_filepath} as CSV: {e}")
            continue

    logging.info(f"Collection and conversion complete for {year_range}. Collected **{len(file_paths)}** file(s) and saved them as CSV.")

# --- Main Logic (Unchanged) ---

def main(_):
    # Ensure all directories exist
    os.makedirs(_BASE_DOWNLOAD_DIRECTORY, exist_ok=True)
    os.makedirs(_SOURCE_FILES_DIRECTORY, exist_ok=True)
    logging.info(f"Base output directories ensured to exist.")

    # Define all years to process
    # MODIFIED: Generate starting years from _START_YEAR (2009) 
    # up to (but not including) _CURRENT_YEAR (2025), with a step of 1.
    # This creates ranges like 2009-10, 2010-11, ..., 2024-25.
    years_to_try = list(range(_START_YEAR, _CURRENT_YEAR, 1))
    
    # 1. Download Stage
    downloaded_year_ranges = []
    for year in years_to_try:
        # Format the year range: 2009 -> 2009-10
        year_range = f"{year}-{str(year+1)[-2:]}"
        url = _BASE_URL.format(year_range=year_range)
        output_dir_for_year = os.path.join(_BASE_DOWNLOAD_DIRECTORY, f"crdc_data_{year_range}")
        os.makedirs(output_dir_for_year, exist_ok=True)

        logging.info(f"Attempting to download data for year range: **{year_range}**")
        
        # NOTE: download_file is imported from download_util_script
        success = download_file(url=url,
                                output_folder=output_dir_for_year,
                                unzip=True)

        if not success:
            logging.warning(
                f"Failed to download data for year {year_range}. It might not be available yet or the URL is incorrect."
            )
            # Clean up empty directory if download failed
            if not os.listdir(output_dir_for_year):
                shutil.rmtree(output_dir_for_year)
            continue # Skip to the next year
        
        logging.info(
            f"Successfully downloaded and extracted ALL data for **{year_range}**."
        )
        downloaded_year_ranges.append(year_range)    

    logging.info("--- Download Stage Complete ---")

    # 2. Collection Stage
    for year_range in downloaded_year_ranges:
        _find_and_collect_files(year_range)

    logging.info("--- Collection Stage Complete ---")
    logging.info(f"Script finished. Collected files are in the '{_SOURCE_FILES_DIRECTORY}' folder.")


if __name__ == '__main__':
    app.run(main)