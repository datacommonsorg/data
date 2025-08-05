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
    logging.info(f"Downloading file from {url}")
    response = requests.get(url)
    response.raise_for_status()
    logging.info("Download successful")
    return BytesIO(response.content)

def extract_year(file_stream):
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
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    df.to_csv(filename, index=False)
    logging.info(f"Saved cleaned data to {filename}")

def main(argv):
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
