# Copyright 2025 Google LLC

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#      https://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from absl import logging, app
import pandas as pd
import requests
from io import BytesIO
import re
import os

# Constants
URL = "https://ncses.nsf.gov/pubs/nsf19304/assets/data/tables/wmpd19-sr-tab09-026.xlsx"
OUTPUT_FOLDER = "source_files"
OUTPUT_CSV = os.path.join(OUTPUT_FOLDER, "wmpd19-sr-tab09-026.csv")

def download_excel(url):
    """Downloads an Excel file from a given URL into a BytesIO object.

    Args:
        url: The URL of the Excel file to download.

    Returns:
        A BytesIO object containing the content of the downloaded Excel file.
    """
    logging.info(f"Downloading file from {url}")
    response = requests.get(url)
    response.raise_for_status()
    logging.info("Download successful")
    return BytesIO(response.content)

def extract_year(file_stream):
    """Extracts a four-digit year from the metadata in the Excel file stream.

    Args:
        file_stream: An in-memory file stream (BytesIO) of the Excel data.

    Returns:
        The four-digit year as an integer.
    
    Raises:
        ValueError: If no year could be extracted from the file metadata.
    """
    df_top = pd.read_excel(file_stream, engine='openpyxl', nrows=3, header=None)
    year_line = df_top.iloc[1, 0]
    match = re.search(r"\b(20\d{2})\b", str(year_line))
    if match:
        year = int(match.group(1))
        logging.info(f"Extracted year: {year}")
        return year
    else:
        raise ValueError("Could not extract year from metadata row.")

def process_excel(file_stream, year):
    """Processes the Excel data, cleans it, and adds a 'Year' column.

    This function reads the Excel data, assigns correct column names, and fixes a
    specific data entry issue in the source file.

    Args:
        file_stream: An in-memory file stream (BytesIO) of the Excel data.
        year: The year to be added to the new 'Year' column.

    Returns:
        A pandas DataFrame with the processed and cleaned data.
    """
    df = pd.read_excel(file_stream, engine='openpyxl', skiprows=4)
    expected_cols = [
        "Occupation, sex, race, and ethnicity",
        "Total",
        "Tenured",
        "On tenure track",
        "Not on tenure track",
        "Tenure not applicable"
    ]
    df.columns = expected_cols[:len(df.columns)]
    df.insert(1, "Year", year)
    logging.info(f"Final columns: {df.columns.tolist()}")

    for idx, row in df.iterrows():
        for col in df.columns:
            if str(row[col]).strip() == "Tenure not applicable":
                if idx + 1 < len(df):
                    df.at[idx, col] = None
                    df.at[idx + 1, col] = "Tenure not applicable"
                    logging.info(f"Moved 'Tenure not applicable' from row {idx} to {idx + 1}")
                break

    return df

def save_to_csv(df, filename):
    """Saves a pandas DataFrame to a CSV file.

    This function creates the necessary directory structure if it doesn't
    already exist before writing the file.

    Args:
        df: The pandas DataFrame to save.
        filename: The full path to the output CSV file.
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    df.to_csv(filename, index=False)
    logging.info(f"Saved cleaned data to {filename}")

def main(argv):
    """Main function to run the data processing pipeline.

    Downloads an Excel file, extracts the year, processes the data, and saves
    the result to a CSV file. Includes error handling for the entire process.

    Args:
        argv: Command line arguments.
    """
    try:
        file_stream = download_excel(URL)
        year = extract_year(file_stream)
        file_stream.seek(0)
        df = process_excel(file_stream, year)
        save_to_csv(df, OUTPUT_CSV)
    except Exception as e:
        logging.fatal(f"A error occurred: {e}", exc_info=True)
        raise RuntimeError(f"Script execution failed due to a error: {e}")

if __name__ == "__main__":
    app.run(main)
