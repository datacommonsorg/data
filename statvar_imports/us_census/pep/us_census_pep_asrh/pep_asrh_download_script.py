from absl import logging
from absl import flags
from retry import retry
from google.cloud import storage  # GCS Client
import os
import shutil
import pandas as pd
import numpy as np
from absl import app, flags
import requests
import json


input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  "input_files")
_URLS_TO_SCAN = {
        "national" : "https://www2.census.gov/programs-surveys/popest/datasets/2020-{YEAR}/national/asrh/nc-est{YEAR}-alldata-r-file{i}.csv",
        "county" : "https://www2.census.gov/programs-surveys/popest/datasets/2020-{YEAR}/counties/asrh/cc-est{YEAR}-alldata.csv",
        "state" : "https://www2.census.gov/programs-surveys/popest/datasets/2020-{YEAR}/state/asrh/sc-est{YEAR}-alldata6.csv"
    }
_FILES_TO_DOWNLOAD= None

@retry(tries=3,
       delay=2,
       backoff=2,
       exceptions=(requests.RequestException, Exception))


def add_future_urls():
    global _FILES_TO_DOWNLOAD
    # Initialize the list to store files to download
    _FILES_TO_DOWNLOAD = {}
    for key,value in _URLS_TO_SCAN.items():
        _FILES_TO_DOWNLOAD[key] = []        
        for future_year in range(2030, 2022, -1):  # From 2030 to 2023
            YEAR = future_year            
            if "{i}" in value:  # This URL contains the {i} variable, so we loop through i from 01 to 10
                
                for i in range(1, 11):
                    formatted_i = f"{i:02}"  # Ensure i is always 2 digits (01, 02, ..., 10)
                    url_to_check = value.format(YEAR=YEAR, i=formatted_i)
                    try:
                        
                        check_url = requests.head(url_to_check,
                                                    allow_redirects=True)
                        if check_url.status_code == 200:
                            _FILES_TO_DOWNLOAD[key].append(url_to_check)
                    except requests.exceptions.RequestException as e:
                        logging.fatal(
                            f"URL is not accessible {value} due to {e}")
            else:
                url_to_check = value.format(YEAR=YEAR)
                logging.info(f"checking url: {url_to_check}")
                try:
                    url_to_check = value.format(YEAR=YEAR)
                    check_url = requests.head(url_to_check,
                                                allow_redirects=True)
                    if check_url.status_code == 200:
                        _FILES_TO_DOWNLOAD[key].append(url_to_check)
                        print(_FILES_TO_DOWNLOAD)
                except requests.exceptions.RequestException as e:
                    logging.error(
                        f"URL is not accessible {value} due to {e}")
    print("files to download",_FILES_TO_DOWNLOAD)

            
def download_files():
    global _FILES_TO_DOWNLOAD, input_path
    for key,value in  _FILES_TO_DOWNLOAD.items():
            # Local path to save the downloaded file
        for url in value:
            output_file_name = url.split('/')[-1]
            download_folder = os.path.join(input_path, key)
            output_file_path = f"input_files/{key}/"+output_file_name

            # Send GET request
            response = requests.get(url)
            if not (os.path.exists(download_folder)):
                os.mkdir(download_folder)

            
            
            # Save the file content
            with open(output_file_path, 'wb') as f:
                f.write(response.content)

            logging.info(f"File downloaded successfully and saved as {output_file_path}")

def main(_):
    """
    Main function that produces the output files and place them in the output folder
    It also includes the modes to run the scripts.
    Arg : None
    Return : None

    """
    
    #Clearing the download folder is it already exists
    try:
        if os.path.exists(input_path):
            if os.listdir(input_path):
                for filename in os.listdir(input_path):
                    file_path = os.path.join(input_path, filename)
                    try:
                        if os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                        else:
                            os.remove(file_path)
                    except Exception as e:
                        logging.error(f"Error while clearing {file_path}: {e}")
    except Exception as e:
        logging.error(f"Error in clear_folder: {e}")


    # add_future_urls(_URLS_TO_SCAN.("state"))
    add_future_urls()
    # add_future_urls(_URLS_TO_SCAN.get("state"))
    
    download_files()
    
if __name__ == "__main__":
    app.run(main)