import os
import requests
import logging
import configparser
from pathlib import Path
from retry import retry

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

# Read Config file
logging.info("Reading configuration from config.ini...")
config = configparser.ConfigParser()
config.read("config.ini")

try:
    NCES_EXCEL_URL = config["DEFAULT"]["NCES_EXCEL_URL"]
    logging.info("NCES_EXCEL_URL retrieved successfully.")
except KeyError as e:
    logging.fatal(f"Missing configuration key: {e}")
    raise

# Ensure source_files directory exists
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_files")
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
logging.info(f"Output directory ensured at: {OUTPUT_DIR}")

# Retry function for handling request failures
@retry(tries=3, delay=5, backoff=2)
def retry_method(url, headers=None):
    logging.info(f"Attempting to fetch data from URL: {url}")
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    logging.info("Data fetched successfully.")
    return response

# Function to download the NCES data
def download_nces_excel():
    logging.info("Starting NCES Excel file data download...")
    output_file = os.path.join(OUTPUT_DIR, "nces_table_318_45.xlsx")
    
    try:
        response = retry_method(NCES_EXCEL_URL)
        with open(output_file, "wb") as f:
            f.write(response.content)
        logging.info(f"NCES data file saved to {output_file}")
        return output_file
    
    except requests.exceptions.RequestException as e:
        logging.fatal(f"Failed to download NCES data file: {e}")
        return None

# Main execution
def main():
    logging.info("Download script initiated.")
    result = download_nces_excel()
    if result:
        logging.info("Download completed successfully.")
    else:
        logging.error("Download failed.")

if __name__ == "__main__":
    main()
