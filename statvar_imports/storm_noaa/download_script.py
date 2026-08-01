
import os
import shutil
import sys
import gzip
import re
from ftplib import FTP, error_perm
from absl import logging
import time

# Add the project root directory to the Python path.
_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPTS_DIR, '..', '..'))
sys.path.append(_PROJECT_ROOT)
sys.path.append(os.path.join(_PROJECT_ROOT, 'util'))
from util import file_util

DATA_DIR = "noaa_storm_data"
FTP_HOST = "ftp.ncdc.noaa.gov"
FTP_PATH = "/pub/data/swdi/stormevents/csvfiles/"
DOWNLOAD_RETRIES = 10
INITIAL_RETRY_DELAY_SECONDS = 5


def get_existing_files(data_dir):
    """
    Returns a set of existing CSV filenames in the data directory.
    """
    existing_files = set()
    for filename in os.listdir(data_dir):
        if filename.endswith('.csv'):
            existing_files.add(filename)
    return existing_files


def download_and_unzip_data(data_dir, existing_files):
    """
    Downloads and unzips the NOAA storm data using ftplib, with retries for individual file downloads.
    """
    logging.info(f"Connecting to FTP server: {FTP_HOST}...")
    try:
        with FTP(FTP_HOST, timeout=120) as ftp:
            ftp.login()
            ftp.cwd(FTP_PATH)
            filenames = [f for f in ftp.nlst() if f.endswith('.csv.gz')]
            logging.info(f"Found {len(filenames)} files in {FTP_PATH}.")
            downloaded_count = 0
            failed_downloads = []

            for filename in filenames:
                local_gz_path = os.path.join(data_dir, filename)
                local_csv_path = local_gz_path[:-3]  # Remove .gz extension

                if local_csv_path in existing_files:
                    logging.info(f"Skipping {filename} as it already exists.")
                    downloaded_count += 1
                    continue

                delay = INITIAL_RETRY_DELAY_SECONDS
                for attempt in range(DOWNLOAD_RETRIES):
                    try:
                        logging.info(f"Downloading {filename} (attempt {attempt + 1}/{DOWNLOAD_RETRIES})...")
                        with file_util.FileIO(local_gz_path, 'wb') as f:
                            ftp.retrbinary(f"RETR {filename}", f.write)

                        logging.info(f"Unzipping {filename}...")
                        with gzip.open(local_gz_path, 'rb') as f_in:
                            with file_util.FileIO(local_csv_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        os.remove(local_gz_path) # Clean up the gzipped file
                        downloaded_count += 1
                        break  # Success, break the retry loop
                    except (TimeoutError, error_perm) as e:
                        logging.warning(f"Attempt {attempt + 1} failed for {filename}: {e}")
                        if attempt < DOWNLOAD_RETRIES - 1:
                            logging.info(f"Retrying in {delay} seconds...")
                            time.sleep(delay)
                            delay *= 2 # Exponentially increase the delay
                        else:
                            logging.error(f"Failed to download {filename} after {DOWNLOAD_RETRIES} attempts.")
                            failed_downloads.append(filename)
                            if os.path.exists(local_gz_path):
                                os.remove(local_gz_path)
            
            if downloaded_count != len(filenames):
                logging.error(f"Download incomplete. Expected {len(filenames)} files, but only downloaded {downloaded_count}.")
                if failed_downloads:
                    logging.error(f"The following files failed to download: {', '.join(failed_downloads)}")
                    raise RuntimeError(
                        "Failed to download files after multiple retries.")
            else:
                logging.info("Download and extraction completed successfully.")

    except error_perm as e:
        logging.error(f"FTP permission error: {e}")
        logging.error("Please check your FTP credentials and permissions.")
    except TimeoutError:
        logging.error(f"Connection to {FTP_HOST} timed out.")
        logging.error("This could be due to a network issue, a firewall blocking the connection, or the server being temporarily unavailable.")
        logging.error("You can try running the script again later or manually downloading the data from:")
        logging.error(f"ftp://{FTP_HOST}{FTP_PATH}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during the FTP process: {e}")


def create_missing_location_files(data_dir):
    """
    Creates empty location files for years that have details files but no
    location files.
    """
    logging.info("Checking for and creating missing location files...")
    header = "YEARMONTH,EPISODE_ID,EVENT_ID,LOCATION_INDEX,RANGE,AZIMUTH,LOCATION,LATITUDE,LONGITUDE,LAT2,LON2"

    details_files = file_util.file_get_matching(
        os.path.join(data_dir, "StormEvents_details*_d*.csv"))
    locations_files = file_util.file_get_matching(
        os.path.join(data_dir, "StormEvents_locations*_d*.csv"))

    def extract_year(filename):
        match = re.search(r"_d(\d{4})_", filename)
        return match.group(1) if match else None

    detail_years = {extract_year(f) for f in details_files if extract_year(f)}
    location_years = {extract_year(f) for f in locations_files if extract_year(f)}

    missing_years = detail_years - location_years

    for year in sorted(list(missing_years)):
        location_filename = os.path.join(
            data_dir, f"StormEvents_locations_d{year}_generated.csv")
        with file_util.FileIO(location_filename, "w") as f:
            f.write(header + "\n")
        logging.info(f"Created missing locations file: {location_filename}")

    logging.info("Missing location file check complete.")


if __name__ == "__main__":
    logging.set_verbosity(logging.INFO)
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    existing_files = get_existing_files(DATA_DIR)
    download_and_unzip_data(DATA_DIR, existing_files)
    create_missing_location_files(DATA_DIR)
