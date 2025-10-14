import os
import sys
import json
import logging
import shutil
import tempfile
import zipfile
from urllib.parse import urlparse, parse_qs
import pandas as pd

# --- Constants provided by the user's environment ---
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add the correct parent directory to the system path to find the utility script
# parent_dir = os.path.dirname(_MODULE_DIR)
# parent_of_parent_dir = os.path.dirname(parent_dir)
# sys.path.append(parent_of_parent_dir)
sys.path.insert(1, '../../../')

# Import download_file from the utility script
try:
    from util.download_util_script import download_file
except ImportError:
    logging.error("Could not import download_file. Make sure 'util/download_util_script.py' exists and is in the correct path.")
    sys.exit(1)

def setup_logging():
    """Sets up basic logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def clean_directory(directory_path):
    """Deletes all files and subdirectories within a given directory."""
    if not os.path.isdir(directory_path):
        logging.warning(f"Directory not found, skipping cleanup: {directory_path}")
        return
    
    logging.info(f"Cleaning directory: {directory_path}")
    for item_name in os.listdir(directory_path):
        item_path = os.path.join(directory_path, item_name)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
                logging.info(f"Deleted file: {item_path}")
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                logging.info(f"Deleted directory: {item_path}")
        except Exception as e:
            logging.error(f"Failed to delete {item_path}. Reason: {e}")

def create_directories(dirs):
    """Creates a list of directories if they don't exist."""
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        logging.info(f"Ensured directory exists: {directory}")

def load_config(config_path):
    """Loads a JSON configuration file."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Config file not found: {config_path}")
        return None
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from file: {config_path}")
        return None

def download_and_organize_zip_files(urls, output_folder):
    """
    Downloads zip files, unzips them, and moves only files containing specific keywords
    from the unzipped folder to the target output folder.
    """
    if not urls:
        logging.warning("No ZIP URLs provided in the configuration. Skipping download.")
        return

    keywords = ["boro", "borough", "school"]
    logging.info(f"Filtering for files containing: {keywords}")

    for url in urls:
        logging.info(f"Starting download and processing for: {url}")
        
        # Create a temporary directory for unzipping
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Download the file, but do not ask the utility to unzip it.
                download_success = download_file(
                    url=url,
                    output_folder=temp_dir,
                    unzip=False,  # We will handle unzipping manually
                    headers=None,
                    tries=3,
                    delay=5,
                    backoff=2
                )
            
                if download_success:
                    logging.info("Download successful. Now unzipping...")
                    
                    # Find the downloaded file in the temp directory.
                    downloaded_files = os.listdir(temp_dir)
                    if not downloaded_files:
                        logging.error(f"Download reported success, but no file found in temp directory for {url}.")
                        continue

                    downloaded_file_name = downloaded_files[0]
                    downloaded_file_path = os.path.join(temp_dir, downloaded_file_name)

                    # Attempt to unzip the file. If it fails, assume it's a single file.
                    try:
                        with zipfile.ZipFile(downloaded_file_path, 'r') as zip_ref:
                            files_in_zip = zip_ref.namelist()
                            if not files_in_zip:
                                logging.warning(f"Zip file from {url} is empty. Skipping.")
                                continue
                            
                            logging.info(f"Files found in '{downloaded_file_name}': {files_in_zip}")
                            zip_ref.extractall(temp_dir)
                        
                        os.remove(downloaded_file_path) # Remove the original zip after extraction
                        logging.info(f"Successfully unzipped and removed '{downloaded_file_name}'.")

                        # Filter and move the extracted files
                        logging.info("Filtering and moving extracted files...")
                        for root, _, files in os.walk(temp_dir):
                            for filename in files:
                                source_path = os.path.join(root, filename)
                                if any(keyword in filename.lower() for keyword in keywords):
                                    dest_path = os.path.join(output_folder, filename)
                                    logging.info(f"Moving file '{filename}' to {output_folder}...")
                                    shutil.move(source_path, dest_path)
                                else:
                                    logging.info(f"Skipping file (does not match keywords): '{filename}'")

                    except zipfile.BadZipFile:
                        logging.warning(f"'{downloaded_file_name}' is not a valid zip file. Treating as a single file.")
                        # The file is not a zip, so move it directly if it matches keywords
                        if any(keyword in downloaded_file_name.lower() for keyword in keywords):
                            dest_path = os.path.join(output_folder, downloaded_file_name)
                            logging.info(f"Moving file '{downloaded_file_name}' to {output_folder}...")
                            shutil.move(downloaded_file_path, dest_path)
                        else:
                             logging.info(f"Skipping file (does not match keywords): '{downloaded_file_name}'")
                   
                    except Exception as e:
                        logging.error(f"An error occurred during processing for {url}: {e}")
                        continue
                    
                    logging.info(f"Finished processing files for {url}.")
                else:
                    logging.error(f"Failed to download file from {url}.")
            except Exception as e:
                logging.error(f"An error occurred while processing {url}: {e}")

def download_files(urls, output_folder):
    """Downloads files and saves them to a target folder with correct filenames."""
    if not urls:
        logging.warning("No URLs provided in the configuration. Skipping download.")
        return

    for url in urls:
        logging.info(f"Starting download for: {url}")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Download the file to a temporary directory
                download_success = download_file(
                    url=url,
                    output_folder=temp_dir,
                    unzip=False,  # These are not zip files
                    headers=None,
                    tries=3,
                    delay=5,
                    backoff=2
                )
                
                if download_success:
                    # Find the downloaded file (will have a UUID-like name)
                    downloaded_files = os.listdir(temp_dir)
                    if not downloaded_files:
                        logging.error(f"Download reported success, but no file found in temp directory for {url}.")
                        continue
                    
                    temp_file_name = downloaded_files[0]
                    source_path = os.path.join(temp_dir, temp_file_name)

                    # Extract the correct filename from the URL query parameter
                    parsed_url = urlparse(url)
                    query_params = parse_qs(parsed_url.query)
                    correct_filename = query_params.get('filename', [None])[0]

                    if not correct_filename:
                        logging.warning(f"Could not determine correct filename for {url}. Using default.")
                        correct_filename = temp_file_name # Fallback to the downloaded name

                    dest_path = os.path.join(output_folder, correct_filename)
                    
                    logging.info(f"Moving file '{temp_file_name}' to '{dest_path}'...")
                    shutil.move(source_path, dest_path)

                else:
                    logging.error(f"Failed to download file from {url}.")
            except Exception as e:
                logging.error(f"An error occurred while downloading {url}: {e}")

def extract_sheets_from_xlsx(directory_path):
    """
    Finds all .xlsx files in a directory, extracts each sheet to a separate CSV file.
    It deletes the original .xlsx file UNLESS it contains a sheet that would result 
    in a file named 'notes.csv'. Finally, it removes any generated CSV files 
    that contain 'notes.csv' in their name.
    """
    xlsx_files = [f for f in os.listdir(directory_path) if f.endswith('.xlsx')]
    
    for xlsx_file in xlsx_files:
        file_path = os.path.join(directory_path, xlsx_file)
        # Flag to preserve the original .xlsx file
        preserve_file = False
        
        try:
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names
            
            if not sheet_names:
                logging.warning(f"No sheets found in {xlsx_file}. Skipping.")
                continue

            logging.info(f"Extracting sheets from {xlsx_file}: {sheet_names}")
            
            base_name = os.path.splitext(xlsx_file)[0]

            for sheet_name in sheet_names:
                # Create a clean name for the CSV file
                clean_sheet_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '_')).rstrip()
                output_csv_name = f"{base_name}_{clean_sheet_name}.csv"
                output_csv_path = os.path.join(directory_path, output_csv_name)
                
                # Check for the preservation rule (from your previous request)
                if output_csv_name.lower() == "notes.csv":
                    preserve_file = True
                    logging.info(f"Original XLSX file {xlsx_file} will be PRESERVED.")
                
                # Save the sheet
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                df.to_csv(output_csv_path, index=False)
                logging.info(f"Saved sheet '{sheet_name}' to '{output_csv_path}'")

        except Exception as e:
            logging.error(f"Failed to process {xlsx_file}: {e}")
            preserve_file = True # Preserve original file on error
            
        
        # Deletion logic for the original XLSX file
        if not preserve_file:
            try:
                os.remove(file_path)
                logging.info(f"Removed original file: {file_path}")
            except Exception as e:
                logging.error(f"Failed to remove original file {xlsx_file}: {e}")
        else:
            logging.warning(f"Original file {xlsx_file} was preserved.")


    # --- NEW CLEANUP STEP ADDED HERE ---
    logging.info("Starting CSV cleanup: removing files containing 'notes.csv'.")
    
    # Iterate through all files in the directory after extraction
    for filename in os.listdir(directory_path):
        # Check if the file is a CSV and contains "notes.csv" (case-insensitive)
        if filename.lower().endswith('.csv') and any(s in filename.lower() for s in ["notes.csv", "all_students.csv","all.csv","lookup.csv","profile.csv","02_","econ status.csv","(public)_ell.csv","Regents.csv"]):
            file_path_to_remove = os.path.join(directory_path, filename)
        try:
            os.remove(file_path_to_remove)
            logging.warning(f"Cleanup: Successfully REMOVED generated file: {filename}")
        except Exception as e:
            logging.error(f"Cleanup: Failed to remove file {filename}: {e}")
        logging.info("Extraction and cleanup process complete.")

# --- New Function to Process and Save Data ---
def process_and_save_data(file_paths):
    """
    Processes files by removing duplicates based on the first four columns,
    keeping the last entry, and replacing 's' values.
    Saves the output as a new CSV file, preserving all original columns.
    """
    for file_path in file_paths:
        try:
            # Read file based on its extension
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                logging.warning(f"Skipping unsupported file type: {file_path}")
                continue
            
            logging.info(f"Processing file: {file_path}")

            # Replace cells with exact value 's' with ''
            df.replace('s', '', inplace=True)

            # Ensure the DataFrame has at least 4 columns
            if df.shape[1] < 4:
                logging.warning(f"File has less than 4 columns and will not be deduplicated: {file_path}")
            else:
                # Get the names of the first four columns for deduplication
                subset_cols = df.columns[:4].tolist()
                df.drop_duplicates(subset=subset_cols, keep='first', inplace=True)

            # Overwrite the original file with the processed data
            df.to_csv(file_path, index=False)
            logging.info(f"Successfully processed and saved (overwritten): {file_path}")

        except Exception as e:
            logging.error(f"Failed to process file {file_path}: {e}")

def organize_files(download_dir, math_dir, english_dir, source_dir, math_files, english_files):
    """
    Organizes downloaded files into math and english directories,
    and copies original files to a source directory.
    """
    all_downloaded_files = os.listdir(download_dir)

    for filename in all_downloaded_files:
        source_path = os.path.join(download_dir, filename)
        matched = False

        # Check against math files list
        for math_file_pattern in math_files:
            if math_file_pattern.replace('.xlsx', '') in filename:
                # Copy file to math folder
                shutil.copy(source_path, os.path.join(math_dir, filename))
                logging.info(f"Organized math file: {filename}")
                matched = True
                break
        
        if matched:
            continue

        # Check against english files list
        for english_file_pattern in english_files:
            if english_file_pattern.replace('.xlsx', '') in filename:
                # Copy file to english folder
                shutil.copy(source_path, os.path.join(english_dir, filename))
                logging.info(f"Organized english file: {filename}")
                matched = True
                break

        # If not matched, delete the file
        if not matched:
            try:
                os.remove(source_path)
                logging.info(f"Deleted unmatched file: {source_path}")
            except Exception as e:
                logging.error(f"Failed to delete unmatched file {source_path}: {e}")

if __name__ == "__main__":
    setup_logging()

    config_file_path = os.path.join(_MODULE_DIR, 'config.json')
    config = load_config(config_file_path)

    if config is None:
        sys.exit(1)

    # --- Define Directory Structure ---
    source_files_path = os.path.join(_MODULE_DIR, 'source_folder')
    math_files_path = os.path.join(_MODULE_DIR, 'input_files/maths')
    english_files_path = os.path.join(_MODULE_DIR, 'input_files/english')
    metadata_path = os.path.join(_MODULE_DIR, 'metadata')

    # --- Create and Clean Directories ---
    create_directories([source_files_path, math_files_path, english_files_path, metadata_path])
    clean_directory(source_files_path)
    clean_directory(math_files_path)
    clean_directory(english_files_path)
    clean_directory(metadata_path)

    # --- Download and Extract All Files ---
    zip_urls = config.get('zip_urls', [])
    xlsx_urls = config.get('xlsx_urls', [])
    download_and_organize_zip_files(zip_urls, source_files_path)
    download_files(xlsx_urls, metadata_path)
    extract_sheets_from_xlsx(source_files_path)

    # --- Define File Lists ---
    math_files_to_keep = [
        "Math_Test_Results_2006-2012_-_Borough_-_Ethnicity.csv",
        "02_borough-math-results-2013-2023-(public).xlsx",
        "04_school-math-results-2013-2023-(public).xlsx",
        "2006_-_2012_Math_Test_Results_-_Borough_-_ELL.csv",
        "2006_-_2012_Math_Test_Results_-_Borough_-_Gender.csv",
        "2006_-_2012_Math_Test_Results_-_Borough_-_SWD.csv",
        "2006_-_2012_Math_Test_Results_-_Charter_Schools.csv",
        "2006_-_2012_Math_Test_Results_-_School_-_ELL.csv",
        "2006_-_2012_Math_Test_Results_-_School_-_Gender.csv",
        "2006_-_2012_Math_Test_Results_-_School_-_SWD.csv",
        "2006-2012_Math_Test_Results_-_School_-_Ethnicity.csv"
    ]
    english_files_to_keep = [
        "2006-2012_English_Language_Arts__ELA__Test_Results_-_Borough_-_All_Students.csv",
        "2006-2012_English_Language_Arts__ELA__Test_Results_-_Borough_-_ELL.csv",
        "2006-2012_English_Language_Arts__ELA__Test_Results_-_Borough_-_Ethnicity.csv",
        "2006-2012_English_Language_Arts__ELA__Test_Results_-_Borough_-_Gender.csv",
        "2006-2012_English_Language_Arts__ELA__Test_Results_-_Borough_-_SWD.csv",
        "2006-2012_English_Language_Arts__ELA__Test_Results_-_Charter_Schools.csv",
        "2006-2012_English_Language_Arts__ELA__Test_Results_-_School_-_ELL.csv",
        "2006-2012_English_Language_Arts__ELA__Test_Results_-_School_-_Ethnicity.csv",
        "2006-2012_English_Language_Arts__ELA__Test_Results_-_School_-_Gender.csv",
        "2006-2012_English_Language_Arts__ELA__Test_Results_-_School_-_SWD.csv",
        "2006-2012_English_Language_Arts__ELA__Test_Results-_School_-_All_Students.csv",
        "school-ela-results-2013-2023-(public).xlsx"
    ]

    # --- Organize and Process Files ---
    organize_files(source_files_path, math_files_path, english_files_path, source_files_path, math_files_to_keep, english_files_to_keep)

    # Process the organized files
    math_files_to_process = [os.path.join(math_files_path, f) for f in os.listdir(math_files_path)]
    english_files_to_process = [os.path.join(english_files_path, f) for f in os.listdir(english_files_path)]
    
    process_and_save_data(math_files_to_process)
    process_and_save_data(english_files_to_process)

    logging.info("Script finished.")
