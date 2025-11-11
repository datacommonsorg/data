import os
import shutil
import sys
import logging
import re
from pathlib import Path
import tempfile

# --- Configuration ---
SCRIPT_DIRECTORY = Path(__file__).parent.resolve()
FILES_DIRECTORY = SCRIPT_DIRECTORY / "files"
UTIL_DIRECTORY = (SCRIPT_DIRECTORY / "../../util").resolve()

sys.path.insert(0, str(UTIL_DIRECTORY))

try:
    from download_util_script import download_file
except ImportError:
    print(f"Error: Could not import 'download_file' from '{UTIL_DIRECTORY}/download_util_script.py'.", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://civilrightsdata.ed.gov/assets/ocr/docs/"
DESTINATION_FOLDERS = ["credit"]
KEYWORD_TO_FOLDER_MAP = {
    "credit": "credit",
}

def generate_urls():
    """Generates the list of URLs to download."""
    urls = []
    for year in range(2012, 2025):
        year_str = f"{year}-{str(year + 1)[-2:]}"
        zip_file_name = f"{year_str}-crdc-data.zip"
        urls.append((f"{BASE_URL}{zip_file_name}", year_str))
    return urls

def organize_files(source_dir, year):
    """Moves relevant files to their destination folders."""
    print(f"\n--- Organizing files for year {year} ---")
    moved_count = 0
    for dirpath, _, filenames in os.walk(source_dir):
        for filename in filenames:
            for keyword, folder_name in KEYWORD_TO_FOLDER_MAP.items():
                if keyword.lower() in filename.lower():
                    source_path = Path(dirpath) / filename
                    destination_folder = FILES_DIRECTORY / folder_name
                    new_filename = f"{year}_{source_path.name}"
                    destination_path = destination_folder / new_filename
                    
                    try:
                        shutil.move(str(source_path), str(destination_path))
                        moved_count += 1
                        logging.info(f"Moved '{filename}' to '{destination_path}'")
                    except shutil.Error as e:
                        logging.error(f"Could not move file {source_path}: {e}")
                    break
    print(f"Successfully moved {moved_count} files for year {year}.")

def process_url(url, year):
    """Downloads, unzips, and organizes files from a single URL."""
    print(f"\n--- Processing: {url} ---")
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            download_success = download_file(
                url=url,
                output_folder=temp_dir,
                unzip=True,
                tries=3,
                delay=5,
                backoff=2
            )
            if not download_success:
                logging.warning(f"Failed to retrieve data from {url} after retries.")
            else:
                print(f"Successfully processed {os.path.basename(url)}")
                organize_files(temp_dir, year)
        except Exception as e:
            logging.error(f"An unexpected error occurred while processing {url}: {e}")

def create_destination_folders():
    """Creates the folders to organize the data into."""
    print("\n--- Creating destination folders ---")
    for folder_name in DESTINATION_FOLDERS:
        folder_path = FILES_DIRECTORY / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured folder exists: {folder_path}")

def clean_destination_folders():
    """Deletes the content of the destination folders."""
    print("\n--- Cleaning destination folders ---")
    for folder_name in DESTINATION_FOLDERS:
        folder_path = FILES_DIRECTORY / folder_name
        if folder_path.exists():
            for item in folder_path.iterdir():
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    logging.info(f"Deleted: {item}")
                except OSError as e:
                    logging.error(f"Error deleting {item}: {e}")
    print("Successfully cleaned destination folders.")

def main():
    """Main function to orchestrate the download and organization."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Starting CRDC data download and organization process...")
    
    FILES_DIRECTORY.mkdir(exist_ok=True)
    print(f"Ensured base directory exists: {FILES_DIRECTORY}")

    clean_destination_folders()
    create_destination_folders()
    urls_to_download = generate_urls()
    for url, year in urls_to_download:
        process_url(url, year)
    
    logging.info("Download and organization script finished.")

if __name__ == "__main__":
    os.chdir(SCRIPT_DIRECTORY)
    main()
