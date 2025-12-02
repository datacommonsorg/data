import os
import shutil
import sys
from absl import app, flags, logging
import re
from pathlib import Path
import tempfile
import datetime

# --- Configuration ---
SCRIPT_DIRECTORY = Path(__file__).parent.resolve()
SOURCE_DIRECTORY = SCRIPT_DIRECTORY / "source"
UTIL_DIRECTORY = (SCRIPT_DIRECTORY / "../../util").resolve()

sys.path.insert(0, str(UTIL_DIRECTORY))

try:
    from download_util_script import download_file
except ImportError:
    logging.error("Could not import 'download_file' from '%s/download_util_script.py'.", UTIL_DIRECTORY)
    raise RuntimeError(f"Could not import 'download_file' from '{UTIL_DIRECTORY}/download_util_script.py'.")

BASE_URL = "https://civilrightsdata.ed.gov/assets/ocr/docs/"
KEYWORD = "dual enrollment"

def generate_urls():
    """
    Generates the list of URLs to download.
    The end year is dynamic, based on the current year, and includes one future year
    to proactively check for new data.
    """
    urls = []
    # The end year is set to the next calendar year to ensure we check for data
    # from the most recently completed school year.
    end_year = datetime.date.today().year + 1
    for year in range(2012, end_year):
        year_str = f"{year}-{str(year + 1)[-2:]}"
        zip_file_name = f"{year_str}-crdc-data.zip"
        urls.append((f"{BASE_URL}{zip_file_name}", year_str))
    return urls

def organize_files(source_dir, year):
    """Moves relevant files to the source folder."""
    logging.info("\n--- Organizing files for year %s ---", year)
    moved_count = 0
    for dirpath, _, filenames in os.walk(source_dir):
        for filename in filenames:
            if KEYWORD.lower() in filename.lower():
                source_path = Path(dirpath) / filename
                destination_folder = SOURCE_DIRECTORY
                new_filename = f"{year}_{source_path.name}"
                destination_path = destination_folder / new_filename
                
                try:
                    shutil.move(str(source_path), str(destination_path))
                    moved_count += 1
                    logging.info("Moved '%s' to '%s'", filename, destination_path)
                except shutil.Error as e:
                    logging.error("Could not move file %s: %s", source_path, e)
                    raise RuntimeError(f"Could not move file {source_path}: {e}")
    logging.info("Successfully moved %d files for year %s.", moved_count, year)

def process_url(url, year):
    """Downloads, unzips, and organizes files from a single URL."""
    logging.info("\n--- Processing: %s ---", url)
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
                logging.warning("Failed to retrieve data from %s after retries.", url)
            else:
                logging.info("Successfully processed %s", os.path.basename(url))
                organize_files(temp_dir, year)
        except Exception as e:
            logging.error("An unexpected error occurred while processing %s: %s", url, e)
            raise RuntimeError(f"An unexpected error occurred while processing {url}: {e}")

def create_source_folder():
    """Creates the folder to organize the data into."""
    logging.info("\n--- Creating source folder ---")
    SOURCE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    logging.info("Ensured folder exists: %s", SOURCE_DIRECTORY)

def clean_source_folder():
    """Deletes the content of the source folder."""
    logging.info("\n--- Cleaning source folder ---")
    if SOURCE_DIRECTORY.exists():
        for item in SOURCE_DIRECTORY.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
                logging.info("Deleted: %s", item)
            except OSError as e:
                logging.error("Error deleting %s: %s", item, e)
                raise RuntimeError(f"Error deleting {item}: {e}")
    logging.info("Successfully cleaned source folder.")

def main(argv):
    """Main function to orchestrate the download and organization."""
    del argv  # Unused.
    logging.info("Starting CRDC data download and organization process...")
    
    clean_source_folder()
    create_source_folder()
    urls_to_download = generate_urls()
    for url, year in urls_to_download:
        process_url(url, year)
    
    logging.info("Download and organization script finished.")

if __name__ == "__main__":
    os.chdir(SCRIPT_DIRECTORY)
    app.run(main)
