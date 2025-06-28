import os
import requests
import logging
from retry import retry
from bs4 import BeautifulSoup
import pandas as pd
import json

#Load Configuration
CONFIG_FILE = "config.json"
with open(CONFIG_FILE, "r") as file:
    config = json.load(file)
    
URL = config["url"]
OUTPUT_DIR = config["output_dir"]
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "poverty_data.csv")

#Ensure output directory exists

os.makedirs(OUTPUT_DIR, exist_ok=True)

#Configure Logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


#Retry function for handling request failures

@retry(tries=3, delay=5, backoff=2)
def fetch_page(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.fatal(f"Failed to fetch URL {url}: {e}")
        raise

#Fetch and parse data
def fetch_data():
    logging.info(f"Fetching data from {URL}")
    html_content = fetch_page(URL)
    
    if html_content is None:
        return None
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    #Extract all tables from the page
    tables = pd.read_html(str(soup))
    
    logging.info(f"Number of tables found: {len(tables)}")
    
    if not tables:
        logging.critical("No table found on the page.")
        return None
    
    #Select the correct table(modify index if needed)
    df = tables[0]
    
    #Save the Dataframe to CSV
    df.to_csv(OUTPUT_FILE, index=False)
    logging.info(f"Data saved to {OUTPUT_FILE}")
    
    return df
    
if __name__ == "__main__":
    fetch_data()