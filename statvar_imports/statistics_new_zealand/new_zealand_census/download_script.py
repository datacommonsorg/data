# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import requests
import zipfile
import io, os, config
from absl import app, logging
import pandas as pd
from retry import retry

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_INPUT_FILE_PATH = os.path.join(_MODULE_DIR, "input_files")


@retry(tries=3, delay=5, backoff=2)
def download_with_retry_method(url, headers=None):
    response = requests.get(url, stream=True)
    response.raise_for_status()
    return response

def download_files(urls, excel_file, output_path):
    """Downloads zip files from URLs, unzips them, and copies an Excel file to the output path.

    Args:
        urls: A list of URLs of zip files.
        excel_file: The path to the Excel file.
        output_path: The directory where all files will be saved.
    """
    try:
        os.makedirs(output_path, exist_ok=True)  

        for url in urls:
            try:
                response = download_with_retry_method(url)

                with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                    for file_info in zip_file.infolist():
                        file_name = os.path.basename(file_info.filename)
                        if not file_name or ("components-change" in file_name or "population-by-broad-age-group" in file_name):
                            continue
                        file_path = os.path.join(output_path, file_name)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        with zip_file.open(file_info) as source, open(file_path, "wb") as target:
                            target.write(source.read())

                logging.info(f"Zip file from {url} downloaded and unzipped.")

            except Exception as e:
                logging.fatal(f"An unexpected error occurred processing {url}: {e}")

        try:
            df = pd.read_excel(excel_file)
            processed_df = process_excel_data(df)
            new_excel_path = os.path.join(output_path, os.path.basename(excel_file))
            if processed_df is not None:
                processed_df.to_excel(new_excel_path, index=False)
            logging.info(f"Excel file copied to: {new_excel_path}")
        except Exception as e:
            logging.fatal(f"Error processing Excel file: {e}")

        logging.info("File processing complete.")

    except Exception as e:
        logging.fatal(f"A general error occurred: {e}")  


def process_excel_data(df):
    """
    Processes an Excel file to combine values based on single-column prefix rows.

    Args:
        df: The DataFrame to be processed.

    Returns:
        A pandas DataFrame with the processed data.
    """

    result = []
    current_prefix = None

    for index, row in df.iterrows():
        row_values = row.tolist()
        if pd.isna(row_values[1]) and pd.isna(row_values[2]) and pd.isna(row_values[3]) and not pd.isna(row_values[0]):
            current_prefix = row_values[0]
            result.append(row_values)
        elif current_prefix is not None:
            new_row = [f"{current_prefix}:{row_values[0]}"] + row_values[1:]
            result.append(new_row)
        else:
            result.append(row_values)

    return pd.DataFrame(result)

def main(argv):
    download_files(config.urls, config.excel_file, _INPUT_FILE_PATH)

if __name__ == "__main__":  
    app.run(main)
