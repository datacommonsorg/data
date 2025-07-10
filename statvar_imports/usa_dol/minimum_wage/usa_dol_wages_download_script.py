# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

'''
This script downloads historical minimum wage data from the U.S. Department of Labor website.
'''
# Import necessary libraries
import os
import csv
import requests
import pandas as pd
from absl import logging
from bs4 import BeautifulSoup
from retry import retry

# URL of the data source
url = "https://www.dol.gov/agencies/whd/state/minimum-wage/history"
source_folder = "source_files" # For raw downloaded files.
input_folder = "input_files"   # For processed, final output files.
os.makedirs(source_folder, exist_ok=True)
os.makedirs(input_folder, exist_ok=True)
file_path = os.path.join(source_folder, "raw_data.html")
file_path2 = os.path.join(source_folder, "raw_data.csv")

@retry(tries=5,delay=3,backoff=5)
def download_with_retry(url):
    """
    Downloads content from a given URL with a retry mechanism.

    This function attempts to make an HTTP GET request to the specified URL. If the
    request fails with a status code indicating an error (e.g., 404, 500),
    it will retry the request up to 5 times with an increasing delay.

    Args:
        url (str): The URL to download content from.

    Returns:
        requests.Response: The response object from the successful HTTP request.
    
    Raises:
        requests.exceptions.RequestException: If the request fails after all retry attempts.
    """
    # Log the attempt to access the URL
    logging.info(f"Trying to access url : {url}")
    response=requests.get(url)
    response.raise_for_status()
    return response 

def extract_all_table_data(url):
    """
    Extracts all tables from a given URL, saves the raw HTML and CSV, and returns the data.

    Args:
        url (str): The URL of the web page to scrape.

    Returns:
        list: A list of tables. Each table is represented as a list of rows,
              and each row is a list of cell strings. Returns None if no tables are found.
    """
    try:
        # Download the page content with retries
        response = download_with_retry(url)
        # Raise an exception for bad status codes
        response.raise_for_status()
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        with open(file_path, 'w') as file:
            file.write(str(soup))

        # Find all table elements in the parsed HTML
        all_tables = soup.find_all('table')
        # Check if any tables were found
        if all_tables:
            # Initialize a list to hold all table data
            table_data = []
            # Iterate over each found table
            for index, table in enumerate(all_tables):
                rows = table.find_all('tr')
                table_rows = []
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    row_data = [col.text.strip() for col in cols]
                    table_rows.append(row_data)
                table_data.append(table_rows)

            # Write the extracted table data to a CSV file
            with open(file_path2, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for index, table in enumerate(table_data):
                    writer.writerows(table)
                    writer.writerow([])
            logging.info("Downloaded files")
            return table_data
        else:
            logging.info(f"No tables found on the page {url}")
            return None
    except requests.exceptions.RequestException as e:
        logging.fatal(f"Error fetching URL: {e}")

def main():
    """
    Main function for data extraction, processing, and saving.
    """
    # Log the start of the process
    logging.info("Process starts")
    # Extract all tables from the specified URL
    all_tables_data = extract_all_table_data(url)

    # Check if table data was successfully extracted
    if all_tables_data:
        all_dfs = []
        for index, table in enumerate(all_tables_data):
            if index == 0:
                df = pd.DataFrame(table[1:], columns=table[0])
            else:
                dfm = pd.DataFrame(table[1:], columns=table[0])
                df = pd.merge(df, dfm, on=['State or otherjurisdiction'])

        transposed_df = df.transpose()
        transposed_df.to_csv('input_files/final_data.csv', header=False)
if __name__ == "__main__" : 
    # Set the logging verbosity to display info-level messages
    logging.set_verbosity(1)
    main()