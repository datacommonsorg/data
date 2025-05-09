import requests
import zipfile
import io
import os
import pandas as pd
from absl import logging

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
target_folder = os.path.join(_MODULE_DIR, "input_files")
input_statvar_file = os.path.join(_MODULE_DIR, 'statvars.csv')
os.makedirs(target_folder, exist_ok=True)


def download_data(series_id, non_working_indicators):
    url = f"https://api.worldbank.org/v2/en/indicator/{series_id}?downloadformat=csv"
    try:
        response = requests.get(url)
    except Exception as e:
        logging.info(f"Exception occurred while downloading : {url}")
    if response.status_code == 200:
        logging.info(f"downloding....{url}")
        file_like = io.BytesIO(response.content)
        if zipfile.is_zipfile(file_like):

            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                file_list = z.namelist()
                for filename in file_list:
                    if filename.endswith('.csv') and "Metadata" not in filename:
                        target_path = os.path.join(target_folder,
                                                   os.path.basename(filename))

                        with z.open(filename) as csv_file, open(
                                target_path, 'wb') as out_file:
                            out_file.write(csv_file.read())
                        break
        else:
            logging.info("indicator is not getting downloaded:", series_id)
            logging.info("indicator is not getting downloaded", series_id)
            non_working_indicators.append(series_id)
            with open("non_working.txt", "a") as file:
                file.write(series_id + "\n")

    else:
        logging.info("Failed to download data:", response.status_code,
                     series_id)


def main():
    non_working_indicators = []

    df = pd.read_csv(input_statvar_file)
    first_column_list = df.iloc[:, 0].tolist()
    for each_series_id in first_column_list:
        download_data(each_series_id, non_working_indicators)


if __name__ == "__main__":
    main()
