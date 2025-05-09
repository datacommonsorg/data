import os
import requests
import logging
import configparser
from pathlib import Path
from retry import retry

#Configure Logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

#Read Config file

config = configparser.ConfigParser()
config.read("config.ini")
NCSES_Employed_URL = config["DEFAULT"]["NCSES_Employed_URL"]

#Ensure output directory exists

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_files")
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


#Retry function for handling request failures

@retry(tries=3, delay=5, backoff=2)
def retry_method(url, headers=None):
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response

#Function to download the NCSES data

def download_ncses_excel():
    logging.info("Starting NCSES Excel file Data download...")
    output_file = os.path.join(OUTPUT_DIR, "ncses_employed.xlsx")
    
    try:
        response = retry_method(NCSES_Employed_URL)
        with open(output_file, "wb") as f:
            f.write(response.content)
            
        logging.info(f"NCSES data file saved to {output_file}")
        return  output_file
    
    except requests.exceptions.RequestException as e:
        logging.fatal(f"Failed to download  NCSES data file: {e}")
        return None

#Main execution

def main():
    download_ncses_excel()

if __name__ == "__main__":
    main()
