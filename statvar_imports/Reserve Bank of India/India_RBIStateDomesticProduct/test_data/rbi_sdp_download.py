import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import logging
import json
import time
import re

#Configure Logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

#Retry method
def retry_request(url, retries=3, delay=5):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logging.warning(f"Attempt {attempt + 1}/{retries} failed: {str(e)}")
            time.sleep(delay)
    logging.fatal(f"Failed to fetch URL after {retries} attempts: {url}")
    return None

def extract_table_number(table_name):
    #Extract numeric table number from table name string
    match = re.search(r'Table\s+(\d+)', table_name)
    return int(match.group(1)) if match else None

def download_state_tables():
    try:
        with open("config.json") as f:
            config = json.load(f)
    
        base_url = config["base_url"]
        download_dir = config["download_dir"]
        
        #Create Download Directory
        os.makedirs(download_dir, exist_ok=True)
        
        #Fetch webpage
        response = retry_request(base_url)
        if not response:
            logging.fatal("Main page request failed")
            return
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        #Locate STATE DOMESTIC PRODUCT section
        section_header = soup.find('td', class_='tableheader', string=lambda t: t and 'STATE DOMESTIC PRODUCT' in t.upper())
        
        if not section_header:
            logging.fatal("STATE DOMESTIC PRODUCT section not found")
            return
        
        logging.info("Successfully located STATE DOMESTIC PRODUCT section")
        
        #Find parent container table
        main_table = section_header.find_parent('table')
        if not main_table:
            logging.fatal("Main data container table not found")
            return
        
        #Process all table rows
        downloaded_files = 0
        for row in main_table.find_all('tr'):
            #Extract table name and download link
            title_link = row.find('a', class_='link2')
            #Get actual XLS/XLSX link
            xls_link = row.find('a', href=lambda href: href and any(ext in href.upper() for ext in ['.XLS', '.XLSX']))
            
            if not title_link or not xls_link:
                continue
            
            #Extract and validate table number
            table_name = title_link.text.strip()
            table_number = extract_table_number(table_name)
            
            if not table_number:
                logging.warning(f"Skipping unparseable table: {table_name}")
                continue
            
            if not (26 <= table_number <= 57):
                logging.debug(f"Skipping table {table_number} (out of range)")
                continue
            
            #Build download parameters
            file_url = urljoin(base_url, xls_link['href'])
            clean_name = re.sub(r'[\\/*?:"<>|]', "", table_name) #Remove invalid filename chars
            
            filename = f"{clean_name}.xlsx"
            filepath = os.path.join(download_dir, filename)
            
            #Skip existing files
            if os.path.exists(filepath):
                logging.info(f"Skipping existing file: {filename}")
                continue
            
            #Download file
            file_response = retry_request(file_url)
            if file_response:
                with open(filepath, 'wb') as f:
                    f.write(file_response.content)
                downloaded_files += 1
                logging.info(f"Downloaded Table {table_number}: {filename}")
            
        logging.info(f"Total files downloaded: {downloaded_files}")
        
    except Exception as e:
        logging.fatal(f"Critical error: {str(e)}")
        raise
    
if __name__ == "__main__":
    download_state_tables()
    logging.info("Process Completed successfully")
    
