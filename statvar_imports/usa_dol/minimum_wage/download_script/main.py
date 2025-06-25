import os
import csv
import requests
import pandas as pd
from absl import logging
from bs4 import BeautifulSoup
from retry import retry

url = "https://www.dol.gov/agencies/whd/state/minimum-wage/history"
source_folder = "source_files"
input_folder = "input_files"
os.makedirs(source_folder, exist_ok=True)
os.makedirs(input_folder, exist_ok=True)
file_path = os.path.join(source_folder, "raw_data.html")
file_path2 = os.path.join(source_folder, "raw_data.csv")

@retry(tries=5,delay=3,backoff=5)
def download_with_retry(url):
    logging.info(f"Trying to access url : {url}")
    return requests.get(url) 

def extract_all_table_data(url):
    try:
        response = download_with_retry(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        with open(file_path, 'w') as file:
            file.write(str(soup))

        all_tables = soup.find_all('table')

        if all_tables:
            table_data = []
            for index, table in enumerate(all_tables):
                rows = table.find_all('tr')
                table_rows = []
                for row in rows:
                    cols = row.find_all(['td', 'th'])
                    row_data = [col.text.strip() for col in cols]
                    table_rows.append(row_data)
                table_data.append(table_rows)

            with open(file_path2, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for index, table in enumerate(table_data):
                    writer.writerows(table)
                    writer.writerow([])
            logging.info("Downloaded files")
            return table_data
        else:
            print(f"No tables found on the page {url}")
            return None
    except requests.exceptions.RequestException as e:
        logging.fatal(f"Error fetching URL: {e}")

def main():
    logging.info("Process starts")
    all_tables_data = extract_all_table_data(url)

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
    logging.set_verbosity(1)
    main()