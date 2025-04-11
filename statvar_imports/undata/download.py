import os
import requests
import zipfile
import logging
from pathlib import Path
from retry import retry
import configparser

#Configure Logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

#Read Config file

config = configparser.ConfigParser()
config.read("config.ini")
UN_ZIP_URL = config["DEFAULT"]["UN_ZIP_URL"]

#Ensure output directory exists

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_file")
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

#Retry function for handling request failures

@retry(tries=3, delay=5, backoff=2)
def retry_method(url, headers=None):
    response = requests.get(url, headers=headers, timeout=60)
    response.raise_for_status()
    return response

#Function to download and save the ZIP file
def download_file():
    logging.info("Starting download...")
    zip_path = os.path.join(OUTPUT_DIR, "UNdata_Export.zip")
    
    try:
        response = retry_method(UN_ZIP_URL)
        with open(zip_path, "wb") as f:
            f.write(response.content)
            
        logging.info(f"Downloaded file saved to {zip_path}")
        return  zip_path
    
    except requests.exceptions.RequestException as e:
        logging.fatal(f"Failed to download file: {e}")
        return None
    
#Function to extract and process the CSV file from ZIP

def extract_and_process(zip_path):
    logging.info("Extracting ZIP file...")
    
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(OUTPUT_DIR)
            csv_files = [f for f in zip_ref.namelist() if f.endswith(".csv")]
            
            if not csv_files:
                logging.fatal("No CSV files found in the ZIP archive!")
                return
            
            for csv_file in csv_files:
                logging.info(f"Processing extracted file: {csv_file}")
                csv_path = os.path.join(OUTPUT_DIR, csv_file)
                
                with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
                    logging.info(f"Read {len(lines)} lines from {csv_file}")
                    
    except zipfile.BadZipFile:
        logging.fatal("Invalid ZIP file format!")
        
#Main execution

def main():
    zip_path = download_file()
    if zip_path:
        extract_and_process(zip_path)


if __name__ == "__main__":
    main()