import os, config
import requests, io
from absl import logging
from pathlib import Path
from retry import retry
import pandas as pd

#Read urls from Config file

Mexico_Census_URL = config.Mexico_Census_URL

#Ensure output directory exists

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input_files")
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

#Retry function for handling request failures

@retry(tries=3, delay=5, backoff=2)
def retry_method(url, headers=None):
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response

#Function to download the Mexico_Census_AA2 Data

def download_and_convert_excel_to_csv():
    logging.info("Starting download and conversion of Excel files...")
    KEYWORDS = ["adm1", "adm2"]
    try:
        for url in Mexico_Census_URL:
            response = retry_method(url)
            excel_file = pd.ExcelFile(io.BytesIO(response.content))
            for sheet_name in excel_file.sheet_names:
                try:
                    if any(keyword in sheet_name.lower() for keyword in KEYWORDS):
                        df = excel_file.parse(sheet_name)
                        if "ISO3" in df.columns:
                            df = df.drop(columns=["ISO3"])
                        csv_filename = os.path.join(OUTPUT_DIR, f"{sheet_name}.csv")
                        df.to_csv(csv_filename, index=False, encoding='utf-8')
                        logging.info(f"Sheet '{sheet_name}' converted to: {csv_filename}")
                except Exception as e:
                    logging.error(f"Error processing sheet '{sheet_name}' : {e}")

    except requests.exceptions.RequestException as e:
        logging.fatal(f"Failed to download Mexico Census data file: {e}")
        return None

if __name__ == "__main__":
    download_and_convert_excel_to_csv()
