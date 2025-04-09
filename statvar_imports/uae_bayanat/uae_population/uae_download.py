import os
import requests
from absl import logging
import configparser
from pathlib import Path
from retry import retry

##Configure Logging


#Read Config file

config = configparser.ConfigParser()
config.read("config.ini")
UAE_Population_URL = config["DEFAULT"]["UAE_Population_URL"]

#Ensure output directory exists

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input")
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


#Retry function for handling request failures

@retry(tries=3, delay=5, backoff=2)
def retry_method(url, headers=None):
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response

#Function to download the UAE_Population file

def download_UAE_Population():
    logging.info("Starting UAE_Population file download...")
    output_file = os.path.join(OUTPUT_DIR, "uae_populationbyemiratesnationalityandgender.xlsx")
    
    try:
        response = retry_method(UAE_Population_URL)
        with open(output_file, "wb") as f:
            f.write(response.content)
            
        logging.info(f"UAE_Population file saved to {output_file}")
        return  output_file
    
    except requests.exceptions.RequestException as e:
        logging.fatal(f"Failed to download UAE_Population file: {e}")
        return None

#Main execution

def main():
    download_UAE_Population()

if __name__ == "__main__":
    main()
