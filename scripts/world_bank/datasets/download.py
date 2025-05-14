import requests
import zipfile
import io
import os
import pandas as pd
from absl import logging
import json
from retry import retry

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_GCS_OUTPUT_DIR = os.path.join(_MODULE_DIR, 'gcs_output')
if not os.path.exists(_GCS_OUTPUT_DIR):
    os.makedirs(_GCS_OUTPUT_DIR)
target_folder = os.path.join(_GCS_OUTPUT_DIR, "input_files")
input_statvar_file = os.path.join(_MODULE_DIR, 'statvars.csv')
config_file = os.path.join(_GCS_OUTPUT_DIR, 'config.json')
if not os.path.exists(target_folder):
    os.makedirs(target_folder, exist_ok=True)


def create_config_for_series():
    """
    Creates a config.json file with URL and is_downloaded status for a given series ID.

    Args:
        series_id (str): The series ID to be included in the URL.
        base_url (str, optional): The base URL for the API. Defaults to "your_base_url_here/".
    """
    all_configs = []
    df = pd.read_csv(input_statvar_file)
    first_column_list = df.iloc[:, 0].tolist()
    for series_id in first_column_list:
        url = f"https://api.worldbank.org/v2/en/indicator/{series_id}?downloadformat=csv"
        config_data = {"URL": url, "is_downloaded": False}
        all_configs.append(config_data)
    try:
        with open(config_file, 'w') as f:
            json.dump(all_configs, f,
                      indent=4)  # Use indent for better readability
        logging.info(f"Config file '{config_file}' created successfully.")
    except Exception as e:
        logging.info(f"Error creating config file '{config_file}': {e}")


@retry(tries=3, delay=2, backoff=2)
def download_url(url):
    logging.info('# trying for url: %s', url)
    response = requests.get(url)
    response.raise_for_status(
    )  # Raise an exception for bad status codes (4xx or 5xx)
    return response


def process_config(config_file):
    """
    Reads a config.json file, fetches data from each URL, and updates
    the is_downloaded status based on the HTTP status code.

    Args:
        config_file_path (str): Path to the config.json file.
    """
    try:
        with open(config_file, 'r') as f:
            data = json.load(f)

        if not isinstance(data, list):
            logging.info(
                "Error: Config file should contain a list of dictionaries.")
            return

        updated_configs = []
        for item in data:
            if isinstance(item,
                          dict) and 'URL' in item and 'is_downloaded' in item:
                url = item['URL']
                is_downloaded = item['is_downloaded']

                if not is_downloaded:
                    try:
                        logging.info(f"Fetching data from: {url}")
                        response = download_url(url)
                        if response.status_code == 200:
                            download_data(response)
                            updated_configs.append({
                                'url': url,
                                'is_downloaded': True
                            })
                    except requests.exceptions.RequestException as e:
                        logging.info(f"Error fetching data from {url}: {e}")
                        """Ignoring this error; retry logic is in place and this script supports persitent volume mounts. Failed URLs will remain False in config and cause script failure at the end."""
                        updated_configs.append(
                            item
                        )  # Keep the original item with is_downloaded as False
                else:
                    updated_configs.append(
                        item)  # Keep already downloaded items as True
            else:
                logging.info("Warning: Invalid item format in config file:",
                             item)
                updated_configs.append(item)  # Keep invalid items as they are

        # Write the updated configurations back to the config.json file

    except FileNotFoundError:
        logging.info(f"Error: Config file '{config_file}' not found.")
    except json.JSONDecodeError:
        logging.info(f"Error: Could not decode JSON from '{config_file}'.")
    except Exception as e:
        logging.info(f"An unexpected error occurred: {e}")
    finally:
        try:
            with open(config_file, 'w') as f:
                json.dump(updated_configs, f, indent=4)
            logging.info("Config file updated with download status.")
        except Exception as e:
            logging.info(
                f"Error writing updated configurations to '{config_file}': {e}")


def download_data(response):
    file_like = io.BytesIO(response.content)
    if zipfile.is_zipfile(file_like):
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            file_list = z.namelist()
            for filename in file_list:
                if filename.endswith('.csv') and "Metadata" not in filename:
                    target_path = os.path.join(target_folder,
                                               os.path.basename(filename))

                    with z.open(filename) as csv_file, open(target_path,
                                                            'wb') as out_file:
                        out_file.write(csv_file.read())
                    break
    else:
        logging.info('Not a zip file')


def main():
    if not os.path.exists(config_file):
        create_config_for_series()
    process_config(config_file)
    try:
        with open(config_file, 'r') as config:
            data = json.load(config)
            for item in data:
                is_downloaded = item['is_downloaded']
                if not is_downloaded:
                    logging.fatal("all files were not downloaded successfully")
    except Exception as e:
        logging.fatal('Error while opening the config file')


if __name__ == "__main__":
    main()
