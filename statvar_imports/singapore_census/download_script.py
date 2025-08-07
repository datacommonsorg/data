# # Copyright 2025 Google LLC
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #      http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.

import json
import pandas as pd
from urllib.request import Request, urlopen
import os
from absl import app
from absl import logging

logging.set_verbosity(logging.INFO)

def process_singstat_json_to_wide_csv(json_data_str, output_filename):
    """
    Parses a JSON string from the SingStat API, creates a wide-format DataFrame,
    and saves it to a CSV file, handling various data formats.

    Args:
        json_data_str (str): The raw JSON string from the SingStat API.
        output_filename (str): The path to the CSV file for saving the data.
    """
    try:
        data = json.loads(json_data_str)
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON: {e}")
        return

    records = []
    if "Data" not in data or "row" not in data["Data"]:
        logging.info("JSON structure not as expected: Missing 'Data' or 'row' key.")
        return

    for row_item in data["Data"]["row"]:
        row_text = row_item.get("rowText")
        uom = row_item.get("uoM")
        series_no = row_item.get("seriesNo")
        columns_data = row_item.get("columns", [])

        for col_item in columns_data:
            year = col_item.get("key")
            value = col_item.get("value")
            records.append({
                "Row Text": row_text,
                "Unit of Measure": uom,
                "Year": year,
                "Value": value,
                "Series No": series_no
            })

    if records:
        df_long = pd.DataFrame(records)
        df_long['Data Series'] = df_long['Row Text'] + ' (' + df_long['Unit of Measure'] + ')'

        # Robust sorting logic for 'Series No' to handle both integers and hierarchical strings (e.g., '1.1.1').
        try:
            df_long['sort_key'] = df_long['Series No'].str.split('.').apply(lambda x: [int(i) for i in x])
            df_long.sort_values(by='sort_key', inplace=True)
        except (AttributeError, ValueError):
            # Fallback to a simple numeric sort if the 'Series No' format is not hierarchical.
            df_long['Series No'] = pd.to_numeric(df_long['Series No'], errors='coerce')
            df_long.sort_values(by='Series No', inplace=True)

        desired_order = df_long['Data Series'].unique()

        # Use pivot_table to handle duplicate entries by taking the first value.
        df_wide = pd.pivot_table(df_long,
                                 index='Data Series',
                                 columns='Year',
                                 values='Value',
                                 aggfunc='first')

        df_wide = df_wide.reindex(desired_order)
        df_wide.reset_index(inplace=True)
        df_wide.columns.name = None

        #  column sorting to handle both yearly and monthly data keys.
        all_columns = df_wide.columns.tolist()
        data_series_column = all_columns[0]
        year_columns = [col for col in all_columns[1:] if str(col).isdigit()]
        monthly_columns = [col for col in all_columns[1:] if not str(col).isdigit()]
        
        year_columns.sort(key=int, reverse=True)
        
        final_columns = [data_series_column] + year_columns + monthly_columns
        df_wide = df_wide[final_columns]
        
        df_wide.to_csv(output_filename, index=False)
        logging.info(f"Successfully converted data to '{output_filename}' in wide format.")
    else:
        logging.warning("No records found to convert.")

def main(_):
    """Main function to fetch data for multiple tables and process them."""
    hdr = {'User-Agent': 'Mozilla/5.0', "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,/;q=0.8"}
    output_folder = "input_files"
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        logging.info(f"Created output folder: {output_folder}")
    
    table_id_configs = {
        "M810001": "Population_Indicator.csv",
        "M810011": "Pop_Resident.csv",
        "M810671": "Pop_Citizens.csv",
        "M810121": "Mortality.csv",
        "M810481": "Death_DeathRate.csv",
        "M810501": "Life_Expectancy.csv",
        "M810131": "DeathByCause.csv"
    }
    
    for table_id, filename in table_id_configs.items():
        url = f"https://tablebuilder.singstat.gov.sg/api/table/tabledata/{table_id}"
        output_filename = os.path.join(output_folder, filename)
        
        logging.info(f"Fetching data for table ID: {table_id} -> Saving to '{output_filename}'")
        try:
            request = Request(url, headers=hdr)
            with urlopen(request) as response:
                data_bytes = response.read()
                json_data_string = data_bytes.decode('utf-8')
            
            process_singstat_json_to_wide_csv(json_data_string, output_filename)
        except Exception as e:
            logging.fatal(f"An error occurred during data fetching or processing for table {table_id}: {e}")
        logging.info("-" * 50)

if __name__ == "__main__":
    app.run(main)